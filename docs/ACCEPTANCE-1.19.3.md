# Real-account acceptance: 1.19.3

The user reports Google Drive, Proton, OneDrive and Dropbox accounts. This
execution environment discovers only a configured Proton account. No credentials
were requested or copied into this report. A root read used a private temporary
configuration snapshot; original configuration SHA256 values were compared before
and after, without recording them. No services were stopped and no cloud files
were written or deleted.

| Provider | Root read | Cloud write/readback | Reconnect | Network outage |
|---|---|---|---|---|
| Google Drive | Pending: unavailable in this session | Pending | Pending | Pending |
| Proton Drive | Passed, approximately 9.23 seconds | Pending | Pending | Pending |
| OneDrive | Pending: unavailable in this session | Pending | Pending | Pending |
| Dropbox | Pending: unavailable in this session | Pending | Pending | Pending |
| Nextcloud | Pending: no account supplied | Pending | Pending | Pending |
| Internxt | Pending: no account supplied | Pending | Pending | Pending |

Open Tools → Validate accounts in the session where accounts are configured.
Read checks report each account independently. Select one disposable account
for Test writing and confirm the named account; the retained test file is checked
by independent direct readback. Close files and explicitly confirm Test reconnect.
For outage recovery, use disposable data and the Acceptance guide; avoid interrupting
important pending uploads. An automated unit test or local-alias probe does not
count as a real provider/FUSE acceptance pass.

KDE/ GNOME desktop acceptance: verify the default file manager opens the selected
mount and main-window controls remain usable with the tray unavailable. Install
KWallet for application-encrypted accounts; GNOME Keyring is not a replacement in
this version. A real GNOME session remains pending.
