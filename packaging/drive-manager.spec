Name:           drive-manager
Version:        1.18.0
Release:        1%{?dist}
Summary:        Multi-account cloud drive desktop manager for KDE
License:        MIT
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  pyproject-rpm-macros
BuildRequires:  desktop-file-utils
Requires:       python3-pyside6
Requires:       rclone >= 1.73
Requires:       fuse3
Requires:       psmisc
Requires:       systemd
Requires:       dolphin
Requires:       kf6-kwallet

%description
Native PySide6 interface for Google Drive, Internxt, OneDrive, Nextcloud, Dropbox and Proton Drive connections,
with explicit read/write modes and transient user systemd mounts. Includes
Spanish, English, French and German application languages.

%prep
%autosetup

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files drive_manager
install -Dpm644 packaging/drive-manager.desktop %{buildroot}%{_datadir}/applications/drive-manager.desktop

%check
QT_QPA_PLATFORM=offscreen PYTHONPATH=src %{python3} -m unittest discover -s tests
 desktop-file-validate %{buildroot}%{_datadir}/applications/drive-manager.desktop

%files -f %{pyproject_files}
%license LICENSE
%doc README.md docs
%{_bindir}/drive-manager
%{_datadir}/applications/drive-manager.desktop

%changelog
* Wed Oct 14 2026 Drive Manager contributors - 1.18.0-1
- Add transactional encrypted credential renewal with identity and upload guards
- Preserve account preferences and require fresh root-read authentication

* Wed Oct 14 2026 Drive Manager contributors - 1.17.1-1
- Set stable FUSE device names when backend options modify remote identities
- Keep existing ownership checks and pending-upload protections

* Tue Oct 13 2026 Drive Manager contributors - 1.17.0-1
- Add bounded manual connection checks with private configuration snapshots
- Add safe per-account results in all four application languages

* Tue Oct 13 2026 Drive Manager contributors - 1.16.0-1
- Add Nextcloud, Dropbox and experimental Proton Drive registration
- Preserve encrypted credentials and pending-upload protections

* Tue Oct 13 2026 Drive Manager contributors - 1.15.0-1
- Add manual stable-release checks with safe browser links

* Tue Oct 13 2026 Drive Manager contributors - 1.14.0-1
- Add four live application languages and English project documentation

* Tue Oct 13 2026 Drive Manager contributors - 1.13.0-1
- Add asynchronous per-account quotas and low-space warnings

* Mon Oct 12 2026 Drive Manager contributors - 1.12.0-1
- Add deduplicated native notifications with persistent mute preference

* Mon Oct 12 2026 Drive Manager contributors - 1.11.0-1
- Simplify main actions, add account menu and collapsible transfers

* Mon Oct 12 2026 Drive Manager contributors - 1.10.0-1
- Add safe read-only diagnostics and copyable ES/EN reports

* Sat Oct 10 2026 Drive Manager contributors - 1.7.0-1
- Show live transfer progress and precise synchronization states
- Keep periodic polling responsive and serialize requested actions

* Sat Oct 10 2026 Drive Manager contributors - 1.6.0-1
- Add account table and opt-in writable mounts with upload and cache protection
- Request write OAuth scopes only for new writable registrations

* Sat Oct 10 2026 Drive Manager contributors - 1.5.0-1
- Enable OneDrive browser OAuth with read scopes and explicit drive selection

* Sat Oct 10 2026 Drive Manager contributors - 1.4.0-1
- Add Internxt with encrypted Rclone config, KDE Wallet and private Unix login
- Add provider registry; reserve OneDrive for a future release

* Sat Oct 10 2026 Drive Manager contributors - 1.3.0-1
- Add disconnect and confirmed connection removal with explicit external scope

* Sat Oct 10 2026 Drive Manager contributors - 1.2.0-1
- Start browser OAuth directly; choose account name and folder after authentication

* Sat Oct 10 2026 Drive Manager contributors - 1.1.2-1
- Accept real Rclone OAuth state length; verify actual link and cancellation

* Sat Oct 10 2026 Drive Manager contributors - 1.1.1-1
- Open OAuth browser through Qt with retry button and persistent safe errors

* Sat Oct 10 2026 Drive Manager contributors - 1.1.0-1
- Add independent Google accounts with browser OAuth and per-account login mounts

* Sat Oct 10 2026 Drive Manager contributors - 1.0.2-1
- Add private atomic per-account preferences and settings dialog

* Fri Oct 09 2026 Drive Manager contributors - 1.0.1-1
- Add isolated private read cache; preserve read-only mounts and legacy ownership

* Fri Oct 09 2026 Drive Manager contributors - 1.0.0-1
- Initial read-only MVP
