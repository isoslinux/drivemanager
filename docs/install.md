# Fedora 44 installation and RPM building

## Install the RPM

Download `drive-manager-1.19.9-1.fc44.noarch.rpm` from
[the latest release](https://github.com/isoslinux/drivemanager/releases/latest).
Open it with Discover or install/update it from the download folder:

```bash
sudo dnf install ./drive-manager-1.19.9-1.fc44.noarch.rpm
```

Launch **Drive Manager** from the KDE menu as your normal user, in a graphical
session with user systemd available. Add accounts through the interface. A
preconfigured Google Drive connection is not required; existing connections can
also be discovered without changing their credentials.

The language selector provides Spanish, English, French and German. The first
launch follows a supported system locale, otherwise English. Your saved choice
overrides the system locale and applies without restarting.

## Run from source

```bash
git clone https://github.com/isoslinux/drivemanager.git
cd drivemanager
sudo dnf install python3 python3-pyside6 rclone fuse3 systemd dolphin psmisc kf6-kwallet
PYTHONPATH=src python3 -m drive_manager.app
```

Rclone 1.73 or later is required. Internxt, Nextcloud and Proton Drive use the KDE wallet named `kdewallet`;
account access also depends on the provider's plan and authentication requirements.
Do not run the application with sudo.

For an optional editable installation, from the repository root:

```bash
sudo dnf install python3-pip python3-setuptools
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/drive-manager
```

## Build the RPM

`packaging/drive-manager.spec` does not activate or modify services during
installation. Run the following from the repository root. The source version is
read from project metadata to avoid packaging an older release:

```bash
sudo dnf install rpm-build python3-devel python3-setuptools pyproject-rpm-macros desktop-file-utils
test -f pyproject.toml && test -f packaging/drive-manager.spec || exit 1
dm_version=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
mkdir -p work/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
tar --exclude=__pycache__ --exclude='*.pyc' \
    --transform="s,^,drive-manager-${dm_version}/," \
    -czf "work/rpmbuild/SOURCES/drive-manager-${dm_version}.tar.gz" \
    pyproject.toml LICENSE README.md src tests docs packaging translations
cp packaging/drive-manager.spec work/rpmbuild/SPECS/
rpmbuild --define "_topdir $PWD/work/rpmbuild" -ba work/rpmbuild/SPECS/drive-manager.spec
```

Never archive an entire home directory or a mounted cloud drive. The explicit
source list excludes credentials, caches and local build products.

Binary RPMs are written to `work/rpmbuild/RPMS/noarch/`; source RPMs are written to
`work/rpmbuild/SRPMS/`. Install any additional requested build dependencies and
repeat the build. Use Mock for a clean Fedora 44 distribution build.

## Validation

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Check installation, real authorization, FUSE and desktop notifications from a
normal KDE session. No real test accounts or tokens are included in the package.

## GNOME integration

The app opens folders with the desktop default through xdg-utils. No Dolphin
installation is required. Without a tray, closing exits; all controls are in the
main window. Application-encrypted accounts still use KWallet and require
kf6-kwallet even under GNOME. GNOME Keyring migration is not implemented.
A live GNOME session should complete the acceptance steps before deployment.
