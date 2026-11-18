# Trivia reliability update

This is an offline-reviewed working copy, not a live-validated bot. No account
login, quiz submission, reward claim, credential transfer, GitHub push, or local
Windows changes were performed while developing this update.

## Changes

- Run tracking is finalized on every exit, including initialization errors and interrupts.
- Failed runs persist to disk; only successful runs advance the 20-hour eligibility clock. Legacy successful-only timestamps are migrated.
- Page errors and missing visual elements no longer count as completed quizzes.
- Questions and answers match conservatively (case, whitespace, Unicode), not by
  80% word overlap. Unknown or ambiguous questions stop the run.
- A matched answer is required before submission; unchanged questions and failed
  transitions stop the run.
- Reward-flow failure propagates all the way to the run result. A visible return
  to the quiz flow is distinguished from independently verified currency credit.
- An unconfirmed reward screen stops with `needs_human`; no CAPTCHA solver,
  fingerprint spoofing, proxy switching, or safeguard bypass was added.
- Password prefixes and password length are no longer logged. Automatic sign-in uses the existing local environment/.env credentials through
  field-bound Windows UI Automation. No real credential values were accessed during development.
- Failed clipboard copy cannot accidentally reuse old clipboard content.

## Verification

Run without desktop packages or credentials:

```sh
python -m unittest discover tests/offline -v
python -m compileall -q src/automation/trivia_automation.py src/utils/trivia_matching.py
```

The offline suite loads the actual class through AST while excluding imports
that open a display, load credentials, or write run history. It mocks all desktop
and network effects. This checks logic, not live recognition accuracy.

The existing `python run_tests.py` suite requires missing desktop packages in
this Linux workspace and is blocked at `pyautogui`. Its positioning tests also
reference old methods absent from the upstream class. It is not a passing full
suite. Upstream requirements.txt is empty; dependency installation has not been
invented or silently changed.

## Remaining live limitations

The current Windows implementation uses the installed Chrome executable and its
normal default profile, then drives pixels/clipboard with PyAutoGUI. Display
scaling, zoom, focus, and updated site layout may invalidate its templates.
Automatic sign-in now uses a conservative Windows UI Automation adapter on the
installed Chrome browser and existing normal profile. It obtains credentials
from the existing local config only at runtime; it does not transfer them to a
service, clipboard, source file, or log. The agent did not read the local .env.

Install the optional accessibility adapter in the existing Windows venv:

```sh
python -m pip install -r requirements-trivia-auth.txt
python main.py --type trivia --custom-only
```

The adapter requires Chrome foreground, trusted HTTPS document origin, exactly
one visible/enabled username field, password-protected password field and login
control in the same document, writeable ValuePatterns, and confirmed field focus.
It calls SetValue directly (pywinauto's convenience set_edit_text logs values and
is deliberately not used). It submits once and waits for both the expected
account name and a logout control before declaring authentication successful.
It stops automatic attempts for human verification, missing accessibility
support, ambiguous controls, changed origin/focus or unconfirmed success. No
Chrome flags/security settings or fingerprint behavior are changed.

Windows Chrome UIA behavior is NOT live-validated here. In particular, password
ValuePattern support and the site's accessible signed-in signals may be absent;
that causes manual fallback, not unsafe keyboard entry. This is a tested adapter,
not a guarantee of unattended login in the user's installed browser.

Manual fallback: sign in and verify the intended account/no pending challenges,
return to the terminal, type READY, and focus the Chrome trivia tab within five
seconds. The script verifies the foreground process and exact
`https://www.wizard101.com/game/trivia` address before continuing. In this fallback,
account identity is operator-confirmed, not independently machine-verified.
Noninteractive runs without verified auto-login stop. Keep Chrome foreground and
do not use the desktop during execution. Stop with Ctrl+C or PyAutoGUI's corner
fail-safe if the wrong window has focus. Human-verification or unknown UI stops
require review; rerunning is not a checkpoint resume. No verification bypass or
retry loop exists. `--custom-only` avoids unrelated game-launcher validation.

Adapter API references: [pywinauto UIA wrapper](https://pywinauto.readthedocs.io/en/latest/code/pywinauto.controls.uiawrapper.html),
[Microsoft IUIAutomationElement](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nn-uiautomationclient-iuiautomationelement).

The 12-question limit is retained as a bounded safety assumption. The script
stops if the layout/question flow differs; it does not guess or retry around a
site block. Already-completed quizzes currently cause a conservative stop if
the expected banner is absent, rather than assuming an unexplained page is safe.

No stealth capabilities were added. Site permission for unattended automation
has not been established. A live trial needs a supported Windows desktop, review of site rules, and
supervision for any automatic-login fallback or human-verification prompts.
