# Validation scope

## Current delivery: 1.14.0

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
