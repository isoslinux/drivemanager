# Provider and desktop acceptance guide

Use this checklist on a disposable account for each supported provider. Never
include account identifiers, credential files or raw cloud logs in public results.
Record provider, application/Rclone versions, desktop, operation and outcome.
A root read does not establish write integrity or recovery after an outage.

| Provider | Root read | Read-only mount | Write/readback | Reconnect | Outage recovery |
|---|---|---|---|---|---|
| Google Drive | Verify | Verify | Verify | Verify | Verify |
| OneDrive | Verify | Verify | Verify | Verify | Verify |
| Dropbox | Verify | Verify | Verify | Verify | Verify |
| Nextcloud | Verify | Verify | Verify | Verify | Verify |
| Internxt | Verify | Verify | Verify | Verify | Verify |
| Proton Drive (experimental) | Verify | Verify | Verify | Verify | Verify |

1. Configure the test account through its normal login flow. In Tools → Validate
   accounts, run a root read. Compare quota with the provider when supported.
2. Connect read-only and confirm that creating a disposable file is refused.
3. Disconnect, explicitly enable writing and reconnect. Wait for uploads to finish.
   Select Test writing and confirm the chosen account. Inspect the retained test
   file on the provider website. Success requires independent byte readback.
4. Close files and explicitly confirm Test reconnect. Reopen the retained file
   and verify content. Repeat independently for each configured account.
5. With disposable data only, exercise a temporary network outage. Check that
   pending writes are preserved and complete after recovery. Do not force-unmount
   a connection carrying important pending data.
6. For providers with refresh sessions or 2FA, run checks across several days
   and verify that the original credentials remain usable afterwards. Report
   results with provider/version and outcomes, without tokens or account names.

Mark unavailable scenarios as not tested. Unit tests and local-alias probes do
not count as real cloud/FUSE acceptance passes. These checklist cells are tasks,
not assertions that every provider has passed.

For KDE and GNOME, verify that the default file manager opens the selected mount
and all main-window controls work without a tray. Encrypted application accounts
still require KWallet; native GNOME Keyring migration is not implemented.
