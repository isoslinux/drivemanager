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

## 1.19.1: visible progress and cooperative cancellation

Connection checks, batch acceptance and browsing probes show a modeless activity
window with the account, current phase and elapsed seconds. Closing a running
activity requests cancellation; it stays visible until the worker returns.
The cancelling state disables repeated requests. No progress percentage is
invented. Batch checks report the current account before reading its root.

Browsing cancellation stops only the disposable probe process and skips further
measurements. Mount-status commands and private snapshot setup can take until
their existing bounded operation returns. Cancellation is cooperative, not an
immediate guarantee. A reconnect already started still attempts mounting;
pending uploads and real mounts are never forcibly stopped by cancellation.
Write-test files and pending data remain preserved as in 1.19.0.

All four language catalogs cover the activity window. Six regression tests cover
window close, elapsed time, translation, batch phase reporting and probe cleanup.

## 1.19.2: actionable browsing results

The browsing result explains incomplete measurements, slow enumeration, slow
filesystem-space queries, both slow queries or both queries under two seconds.
Two seconds is an advisory threshold, not a provider SLA or proof of a cause.
Missing results are never classified as fast. Slow root enumeration suggests
comparing connection checks, folder size and cache effects; slow space queries
suggest comparing the separate quota check without automatically changing mount
flags. If both probes are fast, compare Dolphin without previews and automatic
folder-size calculation where supported. No Dolphin settings are modified.

The existing ten-second limits, cancellation and privacy protections remain.
Only mounted-root queries are measured: file opening, nested folders, thumbnail
generation and upload completion are not validated. Warm caches can affect times.
Three regression tests cover threshold combinations, missing data and four
language catalogs.

## 1.19.3: selective import and desktop integration

Import review has account checkboxes, editable target folders and folder pickers.
The preview includes the imported access mode, login mounting and transfer limits.
Only checked accounts are applied; an empty selection disables application.
The source file is revalidated against the original review, while selected rows
may change only their mount folder. Unknown accounts, duplicate selections, unsafe
paths, current mounts and dirty caches remain rejected. Unselected preference
files are not written. A failure rolls back selected preference bytes.

Folder opening now uses `xdg-open` with an escaped absolute file URI. KDE can
resolve Dolphin and GNOME can resolve Files/Nautilus through the desktop default.
The RPM requires xdg-utils instead of Dolphin. No default associations are changed.
All account actions remain available in the main window. Without an available
tray, closing quits instead of hiding an inaccessible window. These paths are
covered by automated tests; a real GNOME graphical session has not been tested.
Encrypted application accounts still require KWallet; native GNOME Keyring
support is not included and existing encrypted accounts are not migrated.

See [ACCEPTANCE-1.19.3.md](ACCEPTANCE-1.19.3.md) for real account evidence.
