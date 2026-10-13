# Renew encrypted account credentials

Select a disconnected Nextcloud, Proton Drive or Internxt account, then choose
**Account → Renew credentials**. Confirm that you are renewing the same account
and server. Enter the same login name and the new password. For Nextcloud, enter
the same full HTTPS WebDAV URL and a new application password. For Proton, supply
a current two-factor code if required, and the mailbox password for two-password
accounts. Internxt asks for its two-factor code when Rclone requests one.

The connection name is fixed. Mount folder, access mode, automatic mounting,
cache settings and cached files are retained. The action does not change a
password at the cloud provider; it replaces the credentials stored by Drive Manager
after you change them at the provider. It does not automatically connect the drive.

The action is available only for encrypted accounts created by this application.
Google Drive, Dropbox and OneDrive continue to use browser **Reauthorize**.
Existing external encrypted configurations need their original configuration tools.
Custom bearer-token or OTP-secret configurations are not renewed by this workflow.

## Transaction and identity checks

A private temporary copy of the encrypted configuration is opened through a
private Unix RC channel using the existing KWallet encryption key. The key is not
created or replaced during renewal. Decrypted configuration fields are processed
only in memory and never written as a plaintext configuration or logged.

The configured login must match the previous login. Nextcloud also requires the
same WebDAV URL and `nextcloud` vendor. Email/Proton usernames are compared without
case; Nextcloud usernames are compared exactly. This checks the configured login
identity, not a universal provider account ID. Account aliases and URL changes
require separate connection setup rather than bypassing this check.

Non-credential backend settings are retained. Old passwords, one-time codes and
cached session credentials are removed from the temporary account before fresh
login, so a cached token cannot mask an incorrect replacement password. Internxt
regenerates its login-derived key data. Root-directory read access must succeed
before promotion. Write permission is not independently tested.

Renewal requires a disconnected account with no dirty upload cache. These guards
are checked before login and again before promotion. A source configuration changed
by another process is not overwritten. The validated stage is flushed and renamed
atomically; failed or cancelled attempts retain the original encrypted configuration
and pending local data. No active mounted Rclone instance is stopped.

## Validation

Regression tests cover confirmation, mounted accounts, dirty-cache races, source
changes, cancellation, failed login, account/server mismatches, custom credentials,
private encrypted staging, preserved settings and UI routing. A real Rclone probe
validates encrypted config/get-delete-create and removal of old cached tokens with
synthetic data. Root access in that probe is simulated; real login, password changes
and 2FA still require acceptance with disposable files in the owner's session.
