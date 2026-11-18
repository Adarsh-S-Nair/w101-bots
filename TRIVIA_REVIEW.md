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
- Password prefixes and password length are no longer logged. The broader application still loads config from its existing environment/.env
  mechanism, but trivia no longer reads or types those credentials. No values were accessed.
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
Automatic credential typing has been removed entirely. An interactive terminal
prompts the operator to sign in manually and verify their intended account and
absence of pending challenges. Type READY only after doing so, then focus Chrome
within the five-second countdown. The bot first verifies that the Windows foreground process is chrome.exe, then
reads the address bar and requires
exactly `https://www.wizard101.com/game/trivia` (no query or fragment) and stops
if a login control is still visible. Account identity is operator-confirmed,
not independently machine-verified. Noninteractive runs stop, not guess.

To try on the existing Windows checkout/virtual environment after reviewing site
rules and these changes: run `python main.py --type trivia`. Sign in yourself,
return to the terminal, type READY, then click back into the Chrome trivia tab.
Keep the browser foreground and do not use the desktop during execution. Stop
with Ctrl+C or PyAutoGUI's corner fail-safe if the wrong window has focus. Any
human-verification or unknown UI stop requires manual review; rerunning is not
a checkpoint resume. No automatic verification bypass or retry loop exists.

The 12-question limit is retained as a bounded safety assumption. The script
stops if the layout/question flow differs; it does not guess or retry around a
site block. Already-completed quizzes currently cause a conservative stop if
the expected banner is absent, rather than assuming an unexplained page is safe.

No stealth capabilities were added. Site permission for unattended automation
has not been established. A live trial needs a supported Windows desktop,
review of site rules, and supervision for login or human-verification prompts.
