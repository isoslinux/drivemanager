# Reauthorization and access modes

Select an application-created Google Drive or OneDrive connection, disconnect it,
and choose **Account → Reauthorize account**. Confirm and sign in with the same
account. No mounts are automatically stopped to perform authorization.

Name, folder, cache, login mounting, access mode and backend options are preserved.
New credentials are staged privately and atomically replace the old configuration
only after successful authorization. Cancellation, failure or a concurrent mount
preserves the previous connection. OneDrive rejects a different drive identifier
or drive type.

Google requires the user to choose the same account; identity is not independently
verified in this workflow. To use another account, create an independent connection
with its own folder. Pending writes or unknown cache state block reauthorization.
Internxt, external configurations and custom OAuth clients are not supported by
this renewal workflow.

## Enable read/write on an existing account

Disconnect the account, open settings, enable **Read/write**, and save. If permissions
are missing, the application asks for confirmation and opens the browser to authorize
write access to the same account. A duplicate connection is not required.

Cancellation or failed OAuth preserves the previous mode. Permissions are checked
before credentials are promoted. The mount mode remains unchanged until preferences
are successfully saved. If preference saving fails after authorization, the new
credentials remain available but the old mode is retained; resolve the mount or
folder problem and save again.

Returning to read-only prevents mount writes but does not revoke granted OAuth
permissions. External configurations retain their original credentials; use their
original tool if additional permissions are required.

Tests cover preserved options/preferences, private permissions, cancellation,
failures, explicit confirmation, external/active accounts, dirty caches, concurrent
mounts, incorrect OneDrive identity and write-scope upgrades.
