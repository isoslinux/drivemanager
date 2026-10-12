Name:           drive-manager
Version:        1.10.0
Release:        1%{?dist}
Summary:        Google Drive desktop mount manager for KDE
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
PySide6 interface for discovering existing Google Drive connections and managing
read-only FUSE mounts through transient systemd user services.

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
