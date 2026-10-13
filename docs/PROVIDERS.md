# Cloud providers

Drive Manager supports Google Drive, Internxt, OneDrive, Nextcloud, Dropbox and
Proton Drive. Each account has an independent configuration and mount folder.
Read-only is the default; read/write must be selected explicitly.

## Dropbox

Choose **Dropbox**, then **New connection**. The application opens an external
browser for Rclone OAuth. Complete authorization with the account you want, then
choose a connection name and an empty mount folder. Repeat for additional accounts.
No Google or Microsoft scopes are sent to Dropbox.

Mounted Dropbox connections explicitly use synchronous batch commits so an upload
is not reported complete before Dropbox confirms it. Reauthorization is available
for disconnected application-created accounts with a clean cache. Select the same
account during renewal; custom OAuth clients are outside this workflow.

## Nextcloud

Choose **Nextcloud / WebDAV**, then **New connection**. Supply a connection name,
the complete HTTPS WebDAV URL, your Nextcloud username and an application password.
Copy the URL from the Files settings in your Nextcloud web interface; it commonly
looks like `https://cloud.example/remote.php/dav/files/username/`. Do not include
credentials, query parameters or fragments in the URL. Create a dedicated app
password in the Nextcloud security settings, especially when 2FA is enabled.

Rclone uses its `webdav` backend with `vendor=nextcloud`. Existing file-backed
WebDAV connections are also detected and labelled **Nextcloud / WebDAV** because
Rclone metadata discovery does not identify the particular WebDAV server vendor.
Server permissions may restrict writes even when read/write mounting is selected.

## Proton Drive (experimental)

Choose **Proton Drive (beta)**, then **New connection**. Supply your username and
login password. If your account uses 2FA, supply a current code. For an account
configured with two passwords, also supply its mailbox password. Never share your
passwords or recovery data in issue reports.

Before first registration, sign in to Proton Drive on the web at least once so
Proton generates the account's encryption keys. Proton registration uses credentials
rather than Google-style browser OAuth. Rclone's backend is beta and may not work
with every account. Its metadata cache is disabled for mounts, as Rclone recommends;
this can increase network requests. Concurrent changes from other clients are not
promised to appear instantly. Existing upload drafts are not forcibly replaced.

## Credential handling and validation

Nextcloud and Proton configurations are encrypted **before** any credentials are
submitted. The encryption key remains in KDE's `kdewallet`. Credentials travel to
Rclone over a private Unix socket, never in command arguments or logs. Registration
checks root-directory access before committing the staged account. A failure or
cancellation deletes its staged encrypted file. It does not modify an existing
Rclone configuration or stop existing services.

Quota queries for encrypted accounts require an active managed mount and backend
support. Encrypted application accounts offer **Renew credentials** while disconnected
and with a clean upload cache; see [credential renewal](CREDENTIALS.md). Browser
reauthorization remains separate. Account removal remains subject
to the existing pending-upload protections and explicit confirmation.

Automated tests use synthetic credentials and mocks. A standalone real Rclone probe is prepared locally, but its Unix RC server could
not start in the restricted execution environment. Actual login,
mounting, uploading, quota and two-factor behavior still require acceptance with
the account owner's disposable files.

References: [Rclone Dropbox](https://rclone.org/dropbox/),
[Rclone WebDAV / Nextcloud](https://rclone.org/webdav/#nextcloud),
[Rclone Proton Drive](https://rclone.org/protondrive/).
