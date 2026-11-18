"""Synthetic UIA controls only; no browser, credentials, or network used."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from src.utils.trivia_auth import ChromeLogin, UnsafeLoginState, trusted_url, try_auto_login

class Control:
    def __init__(self, name, role, parent=None, password=False):
        self._parent = parent
        self.element_info = SimpleNamespace(name=name, control_type=role, runtime_id=[1])
        element = SimpleNamespace(CurrentIsPassword=password, CurrentIsKeyboardFocusable=True,
                                  CurrentHasKeyboardFocus=False)
        element.SetFocus = lambda: setattr(element, 'CurrentHasKeyboardFocus', True)
        self.element_info.element = element
        self.iface_value = SimpleNamespace(CurrentValue='', CurrentIsReadOnly=False, SetValue=Mock())
        self.iface_invoke = SimpleNamespace(Invoke=Mock())
    def parent(self): return self._parent
    def is_visible(self): return True
    def is_enabled(self): return True

class AutoLoginTests(unittest.TestCase):
    def setUp(self):
        self.doc = Control('Wizard101', 'Document')
        self.doc.iface_value.CurrentValue = 'https://www.wizard101.com/game/trivia'
        self.user = Control('Username', 'Edit', self.doc)
        self.password = Control('Password', 'Edit', self.doc, password=True)
        self.submit = Control('Login', 'Button', self.doc)
        self.account = Control('test-user', 'Text', self.doc)
        self.logout = Control('Logout', 'Hyperlink', self.doc)
        self.window = Mock()
        self.window.descendants.return_value = [self.doc, self.user, self.password, self.submit]
        self.submit.iface_invoke.Invoke.side_effect = lambda: setattr(
            self.window.descendants, 'return_value', [self.doc, self.account, self.logout])
        self.foreground = Mock(return_value=True)
        self.login = ChromeLogin(self.window, self.foreground, sleep=Mock())

    def test_verified_login(self):
        result = self.login.run('test-user', 'dummy-not-a-real-secret')
        self.assertTrue(result['authenticated'])
        self.password.iface_value.SetValue.assert_called_once_with('dummy-not-a-real-secret')
        self.submit.iface_invoke.Invoke.assert_called_once()

    def test_session_requires_positive_account_identity(self):
        self.window.descendants.return_value = [self.doc, self.logout]
        self.assertFalse(self.login.run('test-user','dummy')['authenticated'])
        self.password.iface_value.SetValue.assert_not_called()

    def test_existing_session_does_not_fill(self):
        self.window.descendants.return_value = [self.doc, self.account, self.logout]
        self.assertTrue(self.login.run('test-user','dummy')['authenticated'])
        self.password.iface_value.SetValue.assert_not_called()

    def test_wrong_origin_never_fills(self):
        self.doc.iface_value.CurrentValue = 'https://evil.test/login'
        self.assertFalse(self.login.run('test-user','dummy')['authenticated'])
        self.password.iface_value.SetValue.assert_not_called()

    def test_challenge_never_fills(self):
        self.window.descendants.return_value.append(Control("I'm not a robot", 'CheckBox', self.doc))
        result = self.login.run('test-user','dummy')
        self.assertEqual(result['reason'], 'human_verification')
        self.password.iface_value.SetValue.assert_not_called()

    def test_ambiguous_form_never_fills(self):
        self.window.descendants.return_value.append(Control('Password', 'Edit', self.doc, True))
        self.assertFalse(self.login.run('test-user','dummy')['authenticated'])
        self.user.iface_value.SetValue.assert_not_called()

    def test_password_must_be_password_control(self):
        self.password.element_info.element.CurrentIsPassword = False
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.user.iface_value.SetValue.assert_not_called()

    def test_focus_must_be_confirmed(self):
        self.password.element_info.element.SetFocus = lambda: None
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.password.iface_value.SetValue.assert_not_called()

    def test_origin_change_before_secret_stops(self):
        self.user.iface_value.SetValue.side_effect = lambda _: setattr(self.doc.iface_value, 'CurrentValue', 'https://evil.test')
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.password.iface_value.SetValue.assert_not_called()

    def test_readonly_password_never_fills(self):
        self.password.iface_value.CurrentIsReadOnly = True
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.user.iface_value.SetValue.assert_not_called()

    def test_foreground_loss_stops(self):
        self.foreground.return_value = False
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.user.iface_value.SetValue.assert_not_called()

    def test_different_frame_stops(self):
        other_doc = Control('Login iframe', 'Document')
        other_doc.iface_value.CurrentValue = self.doc.iface_value.CurrentValue
        other_doc.element_info.runtime_id = [2]
        self.password._parent = other_doc
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user','dummy')
        self.user.iface_value.SetValue.assert_not_called()

    def test_no_positive_result_never_claims_success(self):
        self.submit.iface_invoke.Invoke.side_effect = None
        result = self.login.run('test-user','dummy')
        self.assertFalse(result['authenticated'])
        self.assertEqual(result['reason'], 'sign_in_unconfirmed')
        self.submit.iface_invoke.Invoke.assert_called_once()

    def test_origin_allowlist(self):
        for url in ['http://www.wizard101.com', 'https://www.wizard101.com.evil.test',
                    'https://www.wizard101.com@evil.test', 'https://www.wizard101.com:8443']:
            self.assertFalse(trusted_url(url))

    def test_provider_errors_do_not_escape(self):
        with patch('src.utils.trivia_auth.sys.platform', 'win32'), patch(
            'src.utils.trivia_auth.is_chrome_foreground', side_effect=ValueError('dummy-secret')):
            result = try_auto_login('test-user', 'dummy-secret')
        self.assertNotIn('dummy-secret', str(result))
        self.assertFalse(result['authenticated'])


class CrossDocumentTests(unittest.TestCase):
    setUp = AutoLoginTests.setUp
    def test_cross_origin_captcha_stops_before_filling(self):
        google = Control('reCAPTCHA frame', 'Document')
        google.iface_value.CurrentValue = 'https://www.google.com/recaptcha/api2/anchor'
        challenge = Control("I'm not a robot", 'CheckBox', google)
        self.window.descendants.return_value += [google, challenge]
        result = self.login.run('test-user', 'dummy')
        self.assertEqual(result['reason'], 'human_verification')
        self.user.iface_value.SetValue.assert_not_called()
        self.password.iface_value.SetValue.assert_not_called()

    def test_account_and_logout_in_different_docs_not_authenticated(self):
        other = Control('other', 'Document')
        other.iface_value.CurrentValue = self.doc.iface_value.CurrentValue
        other.element_info.runtime_id = [2]
        self.logout._parent = other
        self.window.descendants.return_value = [self.doc, other, self.account, self.logout]
        self.assertFalse(self.login.run('test-user', 'dummy')['authenticated'])

    def test_document_changes_before_secret_stops(self):
        other = Control('other', 'Document')
        other.iface_value.CurrentValue = self.doc.iface_value.CurrentValue
        other.element_info.runtime_id = [2]
        self.user.iface_value.SetValue.side_effect = lambda _: setattr(self.password, '_parent', other)
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user', 'dummy')
        self.password.iface_value.SetValue.assert_not_called()
        self.submit.iface_invoke.Invoke.assert_not_called()

    def test_challenge_after_username_stops_before_secret(self):
        google = Control('reCAPTCHA frame', 'Document')
        google.iface_value.CurrentValue = 'https://www.google.com/recaptcha/api2/anchor'
        self.user.iface_value.SetValue.side_effect = lambda _: self.window.descendants.return_value.append(
            Control("I'm not a robot", 'CheckBox', google))
        with self.assertRaises(UnsafeLoginState): self.login.run('test-user', 'dummy')
        self.password.iface_value.SetValue.assert_not_called()
