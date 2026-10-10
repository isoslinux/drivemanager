# Instalación y preparación RPM para Fedora 44

## Desde fuentes

```bash
sudo dnf install python3 python3-pyside6 rclone fuse3 dolphin kf6-kwallet
PYTHONPATH=src python3 -m drive_manager.app
```

Para instalación de desarrollo opcional:

```bash
sudo dnf install python3-pip python3-setuptools
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/drive-manager
```

Rclone debe tener una conexión Drive ya autorizada. Se pueden añadir cuentas mediante OAuth en el navegador desde el asistente. No se ejecuta como root. Se necesita la sesión gráfica y el bus de systemd de usuario. El entorno cifrado con contraseña interactiva no está soportado; no se solicita ni almacena la contraseña.

## Construir RPM

Receta: `packaging/drive-manager.spec`. No incluye scripts de activación ni modifica servicios durante instalación/desinstalación. Desde la raíz del repositorio:

```bash
sudo dnf install rpm-build python3-devel python3-setuptools pyproject-rpm-macros desktop-file-utils
cd drivemanager
# Verificar que estamos en el proyecto antes de empaquetar.
test -f pyproject.toml && test -f packaging/drive-manager.spec || exit 1
mkdir -p work/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
tar --exclude=__pycache__ --exclude='*.pyc' \
    --transform='s,^,drive-manager-1.7.0/,' \
    -czf work/rpmbuild/SOURCES/drive-manager-1.7.0.tar.gz \
    pyproject.toml LICENSE README.md src tests docs packaging translations
cp packaging/drive-manager.spec work/rpmbuild/SPECS/
rpmbuild --define "_topdir $PWD/work/rpmbuild" -ba work/rpmbuild/SPECS/drive-manager.spec
```

Si `%generate_buildrequires` solicita dependencias adicionales, instalarlas y repetir la construcción. Para una compilación reproducible de distribución, usar Mock con un entorno Fedora 44 y revisar el SRPM.

Después de construir:

```bash
sudo dnf install work/rpmbuild/RPMS/noarch/drive-manager-1.7.0-1.fc44.noarch.rpm
```

El menú de KDE mostrará Drive Manager. No se requiere terminal para las operaciones de montaje.

## Estado de validación

Se verificaron pruebas Python, arranque Qt sin pantalla y formato del lanzador en Fedora 44. El RPM se construyó correctamente tras instalar las herramientas de construcción. La construcción ejecutó las pruebas del núcleo; la prueba Qt se verificó por separado en modo offscreen. La instalación y aceptación con Google Drive real siguen pendientes.

Fuentes de paquetes: [PySide6 en Fedora](https://packages.fedoraproject.org/pkgs/python-pyside6/python3-pyside6/) y [Rclone en Fedora](https://packages.fedoraproject.org/pkgs/rclone/rclone/).

Internxt requiere Rclone >= 1.73 y KWallet (`kf6-kwallet`). Configura la cartera KDE `kdewallet` antes del alta. La integración real con tu cuenta depende de tu plan.
