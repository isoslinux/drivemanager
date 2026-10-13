# Validation scope

## Current delivery: 1.18.0

The application, source archive and Fedora 44 noarch RPM are prepared locally.
Automated tests cover operation safety, account workflows, UI behavior, four
language catalogs and private preferences. See the release notes for the final
verified test count and download hashes.

Qt tests run with the offscreen platform. Screenshots use synthetic accounts and
quota/transfer data, not the user's cloud files. Language tests check immediate
changes, unchanged selection/action guards, persistence and standard dialog buttons.

Previous real Rclone probes checked local OAuth-link extraction and cancellation,
private Unix RC with synthetic encrypted configurations, synthetic local VFS
uploads and a local quota query. These probes did not authorize cloud accounts,
modify the user's existing credentials or stop active services.

## Limits

A successful unit test does not establish that a particular cloud plan supports
login, two-factor authentication, quota or every file operation. KDE tray behavior,
native platform dialogs, actual FUSE mounts and RPM installation need acceptance
in a normal desktop session. Sandbox restrictions can prevent FUSE or user-bus
access without indicating a broken installation.

A local mount, an empty queue or a quota response is not an independent integrity
check for each remote file. Dirty-cache protection retains local data and credentials
when the state is uncertain; it cannot prevent all races with external tools.

The project does not claim that cloud uploads, outage recovery or translation
wording have been independently accepted by native speakers on every provider.
Report issues with the safe diagnostic report rather than raw logs or credentials.

The 1.16.0 delivery adds synthetic Nextcloud, Dropbox and Proton registration tests,
including encrypted staging, cancellation and synchronous Dropbox upload flags.
The installed Rclone 1.74.3 option documentation was checked for Proton and WebDAV.
An attempted real Unix-socket configuration probe could not start its local RC
server in the restricted execution environment; that probe is not counted as passed.
The provider delivery passed 156 tests. Actual provider authorization and cloud file
operations have not been exercised in this delivery. Proton remains experimental.

The 1.17.0 delivery passes 169 automated tests, including manual connectivity checks
and per-account UI results. A real Rclone local-alias root check passed with a
synthetic configuration, preserving the source and removing the temporary copy.
This is not a verification of all six cloud providers with real credentials.

Version 1.17.1 explicitly sets stable FUSE device names. Regression tests simulate
Proton and Dropbox backend overrides, writable monitoring and rejection of foreign
mounts at the same path. Existing mounts are neither adopted nor restarted.
Actual FUSE remounting remains a manual acceptance step.

Version 1.18.0 passes 187 automated tests and includes encrypted credential renewal
for Nextcloud, Proton and Internxt. A real private Unix RC probe verified encrypted
configuration replacement, preserved backend options and removal of old tokens
with synthetic data. Root access was simulated in that probe. Live provider
password changes and two-factor behavior remain manual acceptance checks.
