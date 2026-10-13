# Check connection

Select an account, open the **Account** menu and choose **Check connection**.
The result appears below the account status, labelled **Last check**, together
with the time the cloud command took. Results belong to individual accounts and
are kept only for the current application session. Changing language updates the
result text immediately.

The check reads the remote root directory. It does not create a folder, upload a
file, mount or unmount a drive, change access mode or install dependencies. A
successful result proves root-directory read access at the time of the check;
it does not prove write access or completion of pending uploads.

## Results

- **Readable:** the root-directory query completed successfully.
- **Authentication:** recognized expired/invalid authorization or HTTP 401.
- **Permission:** recognized read-access denial or HTTP 403.
- **Network:** recognized DNS, connection or network timeout errors.
- **Request limit:** recognized provider throttling or HTTP 429.
- **Timed out:** the query exceeded 20 seconds. A slow provider or a large directory
  can cause this; it does not establish that the account is offline.
- **Wallet:** the application's encrypted configuration could not be unlocked.
- **External encrypted configuration:** its original authentication setup is needed.
- **Other failure:** the error could not be safely classified. Use local diagnostics
  to check dependencies and review the provider's requirements.

The messages deliberately omit the server's raw response. Classification is based
on known diagnostic patterns and is not a complete interpretation of every provider.
Proton root listings may be slow because Rclone fetches encrypted file metadata.
Checks run only on request; there is no automatic repeated cloud polling.

## Configuration and process safety

A separate worker leaves mount operations and transfer monitoring responsive.
The original configuration is copied into a temporary directory with permissions
0700 and a configuration file with permissions 0600. OAuth refresh can update this
copy without overwriting the original. Temporary files are removed on success,
failure, cancellation and timeout.

Application-owned encrypted configurations use the existing KWallet password
command. The check never creates or replaces the wallet key and does not assume
that an external encrypted file uses it. The wallet may need to be unlocked for
an explicit manual check. Secrets are never added to command arguments or reports.

Rclone output containing directory names is discarded. Its stderr is drained into
a bounded in-memory buffer and mapped to fixed messages; it is not logged or
saved. Timeouts and application quit terminate only the check's private process
group, not any mounted Rclone instance or active user service.

## Validation

Tests cover snapshot isolation, original credential preservation, private
permissions, cleanup, encrypted account handling, external configurations, safe
error classification, bounded execution, stale selection results and four live
language catalogs. A real Rclone check against a synthetic local alias validates
command compatibility and cleanup without using cloud accounts.
