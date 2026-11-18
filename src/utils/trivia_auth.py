"""Fail-closed Windows UIA login using existing local environment credentials.

Never uses pixel coordinates, global typing, credential clipboard, password reads,
or pywinauto's logging set_edit_text wrapper. No Chrome flags are changed.
"""
import sys
import time
from urllib.parse import urlparse
from src.utils.foreground_browser import is_chrome_foreground


def trusted_url(value):
    parsed = urlparse(value)
    return parsed.scheme == 'https' and parsed.netloc == 'www.wizard101.com'


def label(control):
    return control.element_info.name.strip().strip('*').strip().rstrip(':').casefold()


class UnsafeLoginState(Exception):
    pass


class ChromeLogin:
    def __init__(self, window, foreground_matches, sleep=time.sleep):
        self.window = window
        self.foreground_matches = foreground_matches
        self.sleep = sleep

    def document(self, control):
        for _ in range(32):
            if control.element_info.control_type == 'Document':
                if not trusted_url(control.iface_value.CurrentValue):
                    raise UnsafeLoginState()
                return control
            control = control.parent()
            if control is None:
                break
        raise UnsafeLoginState()

    def guard(self, control):
        if not self.foreground_matches() or not control.is_visible() or not control.is_enabled():
            raise UnsafeLoginState()
        self.document(control)

    def controls(self):
        if not self.foreground_matches():
            raise UnsafeLoginState()
        controls = []
        for item in self.window.descendants():
            if item.is_visible() and item.is_enabled():
                try:
                    self.document(item)
                except Exception:
                    continue
                controls.append(item)
        return controls

    def challenge_visible(self, controls):
        # Only inspect control labels, never textbox values.
        phrases = ("i'm not a robot", 'verify you are human', 'verify that you are human',
                   'unusual traffic', 'access denied', 'security check')
        # Challenges may live in a cross-origin iframe. Inspect visible labels only
        # across this window, while credential controls still require trusted origin.
        return any(any(p in label(c) for p in phrases)
                   for c in self.window.descendants() if c.is_visible())

    def signed_in(self, controls, username):
        # Account identity and logout must be positive signals in the SAME document.
        accounts, logouts = set(), set()
        for control in controls:
            document_id = tuple(self.document(control).element_info.runtime_id)
            if (control.element_info.control_type == 'Text'
                    and control.element_info.name.strip() == username):
                accounts.add(document_id)
            if (control.element_info.control_type in ('Button', 'Hyperlink')
                    and label(control) in ('logout', 'log out', 'sign out')):
                logouts.add(document_id)
        return bool(accounts & logouts)

    def guard_form(self, controls, expected_document):
        if self.challenge_visible([]):
            raise UnsafeLoginState()
        for control in controls:
            self.guard(control)
            if tuple(self.document(control).element_info.runtime_id) != expected_document:
                raise UnsafeLoginState()

    def enter(self, control, value, password):
        self.guard(control)
        element = control.element_info.element
        if bool(element.CurrentIsPassword) != password or not element.CurrentIsKeyboardFocusable:
            raise UnsafeLoginState()
        pattern = control.iface_value
        if pattern.CurrentIsReadOnly:
            raise UnsafeLoginState()
        element.SetFocus()
        self.guard(control)
        if not element.CurrentHasKeyboardFocus:
            raise UnsafeLoginState()
        # Call the UIA pattern directly: set_edit_text/type_keys can log the value.
        pattern.SetValue(value)

    def run(self, username, password):
        if not username:
            return {'authenticated': False, 'reason': 'missing_local_username'}
        controls = self.controls()
        if self.challenge_visible(controls):
            return {'authenticated': False, 'reason': 'human_verification'}
        if self.signed_in(controls, username):
            return {'authenticated': True, 'reason': 'existing_verified_session'}
        if not password:
            return {'authenticated': False, 'reason': 'missing_local_password'}
        edits = [c for c in controls if c.element_info.control_type == 'Edit']
        users = [c for c in edits if label(c) == 'username']
        passwords = [c for c in edits if label(c) == 'password']
        submits = [c for c in controls if c.element_info.control_type in ('Button', 'Hyperlink')
                   and label(c) == 'login']
        if len(users) != 1 or len(passwords) != 1 or len(submits) != 1:
            return {'authenticated': False, 'reason': 'ambiguous_or_unavailable_controls'}
        user, secret, submit = users[0], passwords[0], submits[0]
        # Require all controls in exactly the same trusted document, not sibling frames.
        docs = [self.document(c).element_info.runtime_id for c in (user, secret, submit)]
        if docs[0] != docs[1] or docs[0] != docs[2]:
            raise UnsafeLoginState()
        # Validate all capabilities before filling either field.
        if bool(user.element_info.element.CurrentIsPassword) or not secret.element_info.element.CurrentIsPassword:
            raise UnsafeLoginState()
        if user.iface_value.CurrentIsReadOnly or secret.iface_value.CurrentIsReadOnly:
            raise UnsafeLoginState()
        invoke = submit.iface_invoke
        expected_document = tuple(docs[0])
        self.guard_form((user, secret, submit), expected_document)
        self.enter(user, username, False)
        self.guard_form((user, secret, submit), expected_document)
        self.enter(secret, password, True)
        self.guard_form((user, secret, submit), expected_document)
        invoke.Invoke()  # One attempt only. No retries after errors or challenges.
        for _ in range(20):
            self.sleep(0.5)
            controls = self.controls()
            if self.challenge_visible(controls):
                return {'authenticated': False, 'reason': 'human_verification'}
            if self.signed_in(controls, username):
                return {'authenticated': True, 'reason': 'verified_account_and_logout'}
        return {'authenticated': False, 'reason': 'sign_in_unconfirmed'}


def try_auto_login(username, password):
    """Return only non-secret status. Never propagate provider exception strings."""
    try:
        if sys.platform != 'win32' or not is_chrome_foreground():
            return {'authenticated': False, 'reason': 'chrome_not_foreground'}
        import ctypes
        from ctypes import wintypes
        from pywinauto import Desktop
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetForegroundWindow.restype = wintypes.HWND
        handle = user32.GetForegroundWindow()
        window = Desktop(backend='uia').window(handle=handle).wrapper_object()
        return ChromeLogin(window, lambda: is_chrome_foreground() and
                           user32.GetForegroundWindow() == handle).run(username, password)
    except Exception:
        # UIA errors may include a supplied value. Never log/return the exception.
        return {'authenticated': False, 'reason': 'safe_ui_access_unavailable'}
