# Local diagnostics

Select **Diagnostics**, even when no accounts are configured. The application
checks Rclone, FUSE 3, `/dev/fuse`, user systemd and the presence of systemd-run,
Dolphin, fuser and kwallet-query. Missing components show the relevant package.
The minimum Rclone version is 1.73.

A selected account adds local mount and write-cache checks. External mounts are
not treated as managed, and their queue is not claimed empty. Unknown cache state
requires attention. Diagnostics do not test cloud connectivity or OAuth validity.

**Copy report** copies exactly the visible report to the clipboard. It is never
sent automatically. Reports contain fixed messages and validated numeric versions,
without account names, emails, personal paths, filenames, credentials, raw command
output or logs. Reports use the selected application language.

`diagnostics.py` contains immutable models and read-only checks; `Probe` uses fixed
commands, a four-second timeout per probe and discarded stderr. `app.py` runs checks
in the existing worker and shows a read-only dialog. Tests cover missing programs,
old versions, timeouts, unexpected output, synthetic secrets, pending/unknown cache,
external mounts, FUSE access and visible-report/clipboard equality.

Diagnostics never open KWallet, install packages or change services. A restricted
session or sandbox may deny FUSE/user-bus access; also check from a normal KDE session
before concluding that installation failed. The presence of kwallet-query does not
establish that the wallet is unlocked.
