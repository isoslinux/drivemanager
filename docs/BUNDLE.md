# 1.19 improvement bundle

This delivery groups six areas into one version. It does not claim that every
provider/account has passed all real-world acceptance scenarios.

## Live acceptance panel

Open **Tools → Validate accounts**. **Validate accounts** reads the root folders
of configured accounts using isolated credential snapshots. Results and response
times are shown per account. Providers without a result remain explicitly
unverified; accounts must be configured separately with their normal login flows.

**Test writing** requires separate confirmation, a managed read/write mount,
a known empty upload queue and clean local upload metadata. It creates a uniquely
named `DriveManager-test-<random>.txt`, waits for the queue and reads that exact
file directly through Rclone with an independent private configuration snapshot.
Only an exact byte comparison is reported as success. The test file remains for
inspection or manual deletion; no cloud deletion is automated. Cancelled or failed
tests retain local data and report the test filename when it was created.

**Test reconnect** also requires confirmation. It calls the existing guarded
unmount/mount operations for the selected managed account only, then waits for
mount readiness. Pending uploads, open files and external mounts remain protected.
A successful reconnect does not independently prove integrity of every cloud file
or complete outage recovery. A cancellation before starting does not stop a mount;
once the disconnect/reconnect operation has started, mounting is still attempted.

The **Acceptance guide** covers all six providers: read-only enforcement,
write/readback, reconnect, required 2FA, renewal, network-outage recovery and quota
comparison. These owner-operated steps are not automatically marked as passed.
Use disposable accounts/data when exercising outages or password changes.

## Browsing diagnostics

**Tools → Measure browsing** times directory enumeration and filesystem-space
queries separately. Each runs in a separate bounded process with a 10-second
limit. No filenames, file contents or personal paths are included in the result.
A missing duration means unavailable or timed out. Only a mounted account can be
measured. The checks do not measure Dolphin thumbnail generation, nested folder
counting or every remote API request.

A successful connection check taking at least five seconds carries a slow-response
advisory. This includes initialization/login time and is not a diagnosis of the
provider's underlying cause. Configured speed limits may also slow HTTP metadata
queries. Compare Dolphin with previews and folder-size counting disabled before
concluding that a fast root listing explains all browsing behavior.

## Per-account transfer speed

In **Account → Settings**, set independent upload/download limits in KiB/s.
Zero means unlimited; 1024 KiB/s is 1 MiB/s, approximately 8 Mbit/s. Existing
preference files default to unlimited. Changes require the account to be disconnected
and take effect on the next mount, through Rclone's `--bwlimit=UP:DOWN`. The app
never signals or restarts an active process to apply them. Other accounts keep
independent limits. There is no scheduling/timetable UI in this delivery.

## Local cache warnings

The main window shows free space on the local cache filesystem and the number of
dirty local files for the selected account. Metadata is inspected without reading
cached document contents. Results refresh about every 30 seconds, in a separate
worker; changing selection requests a new result. Unknown or malformed metadata
is not treated as a clean cache.

Free space below 1 GiB produces a local warning and a deduplicated native
notification when notifications are enabled. Quota warnings refer to cloud space;
this warning refers to local disk space. Pending data is never automatically
deleted or evicted by the application. The cache size setting remains a Rclone
cache target, not a guaranteed hard limit. Cache contents are not application-encrypted.

## Initial setup guide

**Tools → Setup guide** offers dependency checks, provider selection and a route
into the existing read-only account registration flow. It explains empty-folder
assignment and when to enable writing. On a new installation with no accounts,
a setup banner is shown until the guide is explicitly finished. Finishing stores
only a private completion flag. The guide remains available from Tools.

The guide does not install packages, enable linger, stop services or authorize
accounts automatically. Missing dependencies must be installed through the normal
Fedora workflow; OAuth and credential entry remain interactive.

## Portable preferences

**Tools → Export settings** writes a private JSON file containing provider/name,
relative mount folder, cache targets, access mode, automatic-login mounting and
speed limits. It contains no OAuth tokens, passwords, server login credentials,
KWallet keys or cache/document contents. Connection names and folder names are
still personal preferences; share the file deliberately.

**Tools → Import settings** requires matching accounts already configured on the
new computer. Relative folders are rebased to the current home. A preview shows
all effective folders, access modes, automount choices and speed limits. Save is
explicit consent to apply those choices. Active accounts, dirty upload caches,
unavailable write authorization, invalid types, unsafe paths, overlapping or
nonempty mount folders and unknown fields are rejected. No account is automatically
registered or mounted during import.

The import file is revalidated against the reviewed values before application.
The app holds its operation lock, snapshots existing preferences, writes them
privately and updates only its own login launcher. A failure restores previous
preference bytes. The process cannot prevent every race with external programs.
Batch folder swaps that conflict with currently stored paths are rejected rather
than temporarily removing account preferences.

The portable format is version 1, limited to 100 accounts and 1 MiB. Account names
must follow the application's portable naming rules. JSON exports cannot overwrite
application/runtime files under `.config`, `.cache` or `.local`. Symlinks are rejected.
External encrypted account authentication is not transferred.

## Validation evidence

Automated tests cover limits, migration, source preservation, private export files,
strict import parsing, changed previews, active/dirty account rejection, rollback,
cache corruption, cancellation and explicitly confirmed live-test operations.
Offscreen Qt checks cover setup, validation, speed controls and all four catalogs.

A real Rclone synthetic local-alias probe passed independent test-file readback,
bandwidth-flag parsing, browsing measurements and snapshot cleanup. It does not
exercise cloud uploads or FUSE. A read-only check of the configured Proton account
also passed in approximately 4.6 seconds, preserving source configuration bytes.
Other real providers, password flows, live FUSE uploads and service reconnects
remain account-owner acceptance scenarios in the new panel.

References: [Rclone bandwidth limits](https://rclone.org/docs/#bwlimit-bwtimetable),
[Rclone mount and VFS](https://rclone.org/commands/rclone_mount/).
