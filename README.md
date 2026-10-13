# Drive Manager

A native desktop application for Fedora 44 KDE Plasma that manages Google Drive,
Internxt, OneDrive, Nextcloud, Dropbox and Proton Drive (experimental) as virtual folders using Python 3, PySide6, Rclone, FUSE and
user systemd services. Each account has its own connection, folder and settings.

The project documentation is in English. The application provides a persistent,
live language selector: **Castellano, English, Français and Deutsch**.

## Download and install

Download the `noarch.rpm` from [GitHub Releases](https://github.com/isoslinux/drivemanager/releases/latest)
and open it with Discover, or install/update it from your download folder:

```bash
sudo dnf install ./drive-manager-1.19.0-1.fc44.noarch.rpm
```

Launch **Drive Manager** from the KDE application menu, as your normal user.
Authenticate accounts separately on each computer. Credentials, caches and cloud
files are never included in this repository or the release package.

## Using the application

- Choose a provider and access mode, then select **New connection**. Google Drive
  OneDrive and Dropbox open an external browser; Internxt, Nextcloud and Proton Drive
  use credentials and KWallet. See [provider setup and limitations](docs/PROVIDERS.md).
- Select an account and use **Connect**, **Disconnect** or **Open in Dolphin**.
- The **Account** menu contains **Check connection**, settings, browser reauthorization,
  encrypted credential renewal and connection removal.
  A manual check verifies root-folder read access without changing the original credentials.
- Configure mount folder, cache targets, access mode and mounting at login per account.
- Expand **Transfers** to inspect progress. Desktop notifications can be muted.
- **Tools** contains the setup guide, live validation, browsing measurements and portable settings.
- Per-account settings include independent upload/download limits; local cache space and pending files appear in the main window.
- **Diagnostics** checks dependencies and local state with a copyable safe report.
- Select an account to query its storage quota. **Refresh space** requests fresh data.
- Select a language near the top of the window. Changes apply immediately and persist.
- **Check for updates** compares the installed version with the latest stable GitHub release.
  Downloading and installing the RPM remain manual.

Closing the window hides it when a tray is available. **Quit application** leaves
mounts running until the user session ends. Mounting at login is optional; linger
is never enabled. Changing language does not disconnect or reauthorize accounts.

## Run from source

```bash
git clone https://github.com/isoslinux/drivemanager.git
cd drivemanager
sudo dnf install python3 python3-pyside6 rclone fuse3 systemd dolphin psmisc kf6-kwallet
PYTHONPATH=src python3 -m drive_manager.app
```

Rclone 1.73 or later and a graphical session with user systemd are required.
Do not run the application with sudo.

## Configuration and data protection

Existing Rclone connections are discovered without changing their credentials.
Their mounts use private configuration snapshots; new accounts use independent
private files. These files contain secrets and must not be shared. Tokens and raw
OAuth output are never logged or included in user-facing error messages.

Read/write access changes cloud files and must be enabled explicitly. Disconnecting
and removing connections require confirmation and are blocked when uploads remain
pending or their state is unknown. Removing an external connection additionally
requires approval to modify the original Rclone configuration. Connection removal
does not delete cloud files or local mount folders. External mounts are never stopped.

Caches may contain local document copies. They use private permissions but are
not encrypted by this application. Mounts are never forced or lazily unmounted.
Other tools can still race with local mount operations.

A local mount or empty upload queue does not independently prove cloud connectivity.
Quota availability depends on the provider. Encrypted credential connections need an
active managed mount for quota queries; background queries never unlock KWallet.

## Documentation and tests

- [Installation and RPM building](docs/install.md)
- [Architecture](docs/architecture.md)
- [Interface](docs/INTERFACE.md)
- [Reauthorization and access modes](docs/REAUTHORIZATION.md)
- [Diagnostics](docs/DIAGNOSTICS.md)
- [Notifications](docs/NOTIFICATIONS.md)
- [Storage quotas](docs/STORAGE.md)
- [Languages and translation maintenance](translations/README.md)
- [The six-area improvement bundle](docs/BUNDLE.md)
- [Encrypted credential renewal](docs/CREDENTIALS.md)
- [Connection checks](docs/CONNECTIVITY.md)
- [Update checks](docs/UPDATES.md)
- [Test plan](docs/testing.md) and [validation scope](docs/validation.md)

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Automated tests use synthetic credentials, simulated services and offscreen Qt.
Native KDE notifications, real OAuth, cloud access and FUSE acceptance are checked
in the account owner's desktop session. See the validation document for the scope.

## Release history

| Version | Main change |
| --- | --- |
| 1.19.0 | Live validation, browsing diagnostics, speed limits, cache warnings, setup and portable preferences |
| 1.18.0 | Renew encrypted credentials for the same Nextcloud, Proton and Internxt account |
| 1.17.1 | Stable mount identities for backend option overrides |
| 1.17.0 | Manual connection checks with safe errors and private snapshots |
| 1.16.0 | Nextcloud, Dropbox and experimental Proton Drive connections |
| 1.15.0 | Manual update checks with safe release/RPM links |
| 1.14.0 | English project documentation and four selectable application languages |
| 1.13.0 | Account quotas and low-space warnings |
| 1.12.0 | Deduplicated desktop notifications and persistent mute controls |
| 1.11.0 | Simplified interface, account menu and collapsible transfers |
| 1.10.0 | Safe local diagnostics and copyable reports |
| 1.9.0 | Authorize write access from existing account settings |
| 1.8.0 | Reauthorize managed Google Drive and OneDrive accounts |
| 1.7.0 | Transfer progress and synchronization states |
| 1.6.0 | Explicit read/write mode with pending-upload protection |
| 1.5.0 | OneDrive browser authorization |
| 1.4.0 | Encrypted Internxt configurations and KWallet |
| 1.3.0 | Confirmed disconnect and connection removal |
| 1.2.0 | Browser-first Google Drive registration |
| 1.1.0–1.1.2 | Multiple accounts, login mounting and browser authorization fixes |
| 1.0.0–1.0.2 | Read-only MVP, private read cache and account settings |
