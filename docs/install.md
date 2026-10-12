# Instalación y construcción RPM para Fedora 44

## Instalar el RPM

Descarga `drive-manager-1.13.0-1.fc44.noarch.rpm` desde
[la última versión](https://github.com/isoslinux/drivemanager/releases/latest).
Ábrelo con Discover o instala desde la carpeta de descarga:

```bash
sudo dnf install ./drive-manager-1.13.0-1.fc44.noarch.rpm
```

El menú de KDE mostrará **Drive Manager**. Ejecuta la aplicación como usuario normal,
dentro de tu sesión gráfica, con el bus de systemd de usuario disponible. Añade las
cuentas desde la interfaz; no es necesario configurar previamente una cuenta Drive.
Las conexiones existentes también se detectan, sin modificar sus credenciales.

## Desde fuentes

```bash
git clone https://github.com/isoslinux/drivemanager.git
cd drivemanager
sudo dnf install python3 python3-pyside6 rclone fuse3 systemd dolphin psmisc kf6-kwallet
PYTHONPATH=src python3 -m drive_manager.app
```

Rclone debe ser 1.73 o posterior. Internxt utiliza la cartera KDE `kdewallet` mediante
KWallet; el acceso real depende del plan y la autenticación de la cuenta.

Para una instalación editable opcional, desde la raíz del repositorio:

```bash
sudo dnf install python3-pip python3-setuptools
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/drive-manager
```

## Construir el RPM

La receta `packaging/drive-manager.spec` no activa ni modifica servicios durante la
instalación. Estos comandos se ejecutan desde la raíz del repositorio y leen la
versión del proyecto para evitar empaquetar una versión antigua:

```bash
sudo dnf install rpm-build python3-devel python3-setuptools pyproject-rpm-macros desktop-file-utils
# Ejecutar dentro del repositorio drivemanager.
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

No empaquetes toda la carpeta personal ni una unidad montada. La lista explícita
incluye solo los archivos del proyecto y excluye credenciales, caché y productos
locales de construcción.

El RPM binario queda en `work/rpmbuild/RPMS/noarch/` y el de fuentes en
`work/rpmbuild/SRPMS/`. Si la construcción solicita dependencias adicionales,
instálalas y repite el proceso. Para comprobar una distribución en un entorno
limpio, utiliza Mock para Fedora 44.

## Validación

La versión 1.13.0 supera 125 pruebas automatizadas y se ha construido para Fedora
44. Las pruebas Qt se ejecutan sin pantalla:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Comprueba instalación, autorización y avisos de KDE en una sesión real. No se
incluyen cuentas ni tokens de prueba en el paquete.
