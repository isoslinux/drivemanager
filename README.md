# Drive Manager 1.7.0 — progreso y estados de sincronización

Aplicación nativa Python 3 / PySide6 para Fedora 44 KDE Plasma. Gestiona Google Drive, Internxt y OneDrive como carpetas virtuales mediante Rclone, FUSE y systemd de usuario.

Permite varias cuentas con carpetas independientes, modos de lectura o lectura/escritura, caché configurable, montaje automático, bandeja del sistema y progreso de transferencias. Las operaciones de desconexión y eliminación protegen las subidas pendientes. Interfaz en español e inglés.

## Obtener el código

```bash
git clone https://github.com/isoslinux/drivemanager.git
cd drivemanager
```


## Uso desde el código

Instala las dependencias y ejecuta desde este directorio:

```bash
sudo dnf install python3 python3-pyside6 rclone fuse3 dolphin
PYTHONPATH=src python3 -m drive_manager.app
```

Estos comandos son para la instalación inicial; montar, desmontar y abrir carpetas se hace desde la interfaz. No se ejecutaron cambios de paquetes ni operaciones de montaje durante el desarrollo.

Selecciona una conexión y pulsa **Montar (solo lectura)**. El estado se actualiza cada cinco segundos. **Desmontar** solo está disponible para montajes propios y solicita confirmación. Cerrar la ventana la oculta cuando hay bandeja; **Salir de la aplicación** deja los montajes funcionando. Los servicios duran la sesión de usuario; no se habilita linger ni montaje automático.

La conexión debe existir en el archivo de configuración de Rclone y ser de tipo `drive`. Se requiere una versión con `listremotes --json`. Las conexiones de entorno, los alias/crypt y las configuraciones cifradas con contraseña interactiva quedan fuera del MVP. La versión 1.1.0 añade un asistente OAuth para cuentas nuevas, descrito más abajo.

## Protección de configuración y datos

No se edita el archivo original de Rclone. Al montar se crea una copia privada de su configuración en `~/.local/state/drive-manager/`, directorio 0700 y archivos 0600. La copia contiene credenciales de las conexiones del archivo original: no se debe compartir ni incluir en informes. Rclone puede actualizar sus tokens OAuth en esa copia sin tocar el original. La copia se conserva mientras pueda usarla el servicio; no se borra al cerrar la interfaz.

No hay logs de aplicación; stdout/stderr del servicio Rclone se descartan y los errores de procesos no muestran su contenido. Los montajes nuevos usan `--read-only --vfs-cache-mode=full` con caché privada de lectura, por lo que la aplicación no crea subidas pendientes. Ningún servicio externo se detiene ni se adopta. Una operación explícita de desmontaje detiene únicamente un servicio propio verificado. No hay desmontaje forzado, perezoso ni al salir.

Los puntos de montaje son `~/DriveManager/<identificador>`; los identificadores proceden del nombre de conexión. Los directorios deben estar vacíos y no ser enlaces simbólicos. Un bloqueo entre instancias serializa las operaciones de la aplicación. No puede impedir carreras con herramientas externas que monten simultáneamente.

**El estado mostrado es el estado local de FUSE/systemd, no una prueba de conectividad con Google.** Una conexión caída puede seguir apareciendo montada. Rclone administra sus reintentos de acceso; un servicio que falla no se reinicia automáticamente. Si hay un montaje obsoleto, el MVP bloquea otro montaje y no intenta forzarlo.

## Desarrollo y comprobaciones

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Consulta [arquitectura y fases](docs/architecture.md), [plan de pruebas](docs/testing.md) e [instalación y RPM](docs/install.md).

Entregado: núcleo probado con procesos simulados y arranque Qt sin pantalla. Pendiente: aceptación con Drive/FUSE real, bandeja en una sesión KDE e instalación del RPM. No se ha afirmado ni probado una subida o una reconexión real.

## Actualización 1.0.1: apertura de documentos

Se añade caché de lectura en `~/.cache/drive-manager-readonly-v1/<identificador-de-cuenta>/`, aislada por cuenta de cualquier caché usada para subir archivos. Directorios 0700 y servicio con UMask 0077. Puede contener copias locales de tus documentos; no está cifrada por la aplicación. El montaje sigue siendo de solo lectura y no crea subidas.

Objetivo de tamaño: 2 GiB por cuenta; caducidad: 24 horas desde el último acceso; objetivo de espacio libre: 512 MiB. Son objetivos de limpieza de Rclone, no límites estrictos: los archivos abiertos y el intervalo de limpieza pueden hacer que se superen. Usa 8 MiB de búfer en memoria por archivo y 16 MiB de lectura anticipada en disco. No descarga todo Drive; conserva los fragmentos consultados. Rclone comprueba si el contenido remoto cambió.

Para aplicar la actualización: cierra la aplicación desde la bandeja, instala el RPM 1.0.1, abre Drive Manager, cierra los documentos, desmonta con confirmación y vuelve a montar. Instalar el RPM no reinicia ni detiene servicios. Los montajes antiguos siguen sin caché hasta que los vuelvas a montar.

Prueba el mismo PDF dos veces, cerrando Okular entre aperturas. La primera todavía depende de la red y el tamaño; la segunda debería aprovechar los datos descargados. No se ha medido todavía el rendimiento real de esta actualización en tu Drive.

Detalles: [caché VFS de Rclone](https://rclone.org/commands/rclone_mount/#vfs-file-caching).

## Actualización 1.0.2: ajustes por cuenta

Con la cuenta desmontada, pulsa **Ajustes de la cuenta** para elegir la carpeta de montaje, el objetivo de caché (1–1024 GiB) y la conservación sin uso (1–8760 horas). La carpeta puede ser nueva, pero debe estar vacía dentro de tu directorio personal, sin enlaces simbólicos ni solapamientos con otras rutas configuradas. No se admite montar dentro de `.config`, `.cache` o `.local`. El selector permite elegir una carpeta; también puedes escribir una ruta nueva.

Los ajustes se guardan por cuenta en `~/.config/drive-manager/accounts/<identificador>.json`, permisos 0600, mediante reemplazo atómico. No contienen tokens y no editan Rclone. La identidad del servicio y la ubicación de caché se conservan aunque cambies la carpeta de montaje. No se mueven ni borran datos de las carpetas antiguas.

Los cambios se aplican al siguiente montaje. No se pueden editar los ajustes de una cuenta montada, iniciando o gestionada por otra herramienta; el backend lo comprueba de nuevo al guardar. Cancelar el diálogo no escribe nada. Se mantienen los valores anteriores de 2 GiB y 24 horas cuando no existen preferencias.

Instala el RPM 1.0.2, abre la aplicación, desmonta con confirmación y entra en Ajustes de la cuenta. Si reduces el tamaño de caché, la limpieza de Rclone se aplica al montar y no elimina archivos abiertos de inmediato.

## Versión 1.1.0: conectar varias cuentas Google

1. Pulsa **Añadir cuenta Google**.
2. Escribe un nombre único, por ejemplo `personal`, `trabajo`, `familia` o `archivo` (letras ASCII, números, guion o guion bajo; empieza por una letra).
3. Asigna una carpeta vacía distinta dentro de tu directorio personal: por ejemplo `~/Drives/Personal`, `~/Drives/Trabajo`, `~/Drives/Familia` y `~/Drives/Archivo`. En el campo introduce la ruta absoluta, sin `~`; puedes escribir una carpeta nueva o elegir una existente.
4. Si quieres, marca **Montar esta cuenta al iniciar sesión**.
5. Acepta y completa OAuth en el navegador externo. **Elige la cuenta Google correcta en el navegador**, usando «Usar otra cuenta» cuando sea necesario.
6. Vuelve a la aplicación: la conexión aparecerá en la lista. Selecciónala, pulsa **Montar** y después **Abrir en Dolphin**. Repite para las otras cuentas.

No hay límite de cuatro cuentas. Cada conexión tiene un archivo privado independiente (0600) en `~/.config/drive-manager/connections/`, caché aislada y carpeta elegida. Los permisos OAuth nuevos son `drive.readonly` y el montaje sigue siendo solo lectura. No se escribe ni cambia la configuración Rclone original. Los archivos propios contienen tokens: no compartirlos. El asistente utiliza Rclone y no solicita contraseñas Google dentro de la aplicación.

Durante OAuth se puede pulsar **Cancelar autorización**; hay un plazo máximo de diez minutos. Un fallo o cancelación elimina el archivo temporal y no registra una cuenta utilizable. Cancelar después de conceder acceso puede dejar la autorización concedida en Google; se puede revocar desde la cuenta Google. La salida de Rclone se descarta, los tokens no se pasan por argumentos ni se muestran en errores. El asistente está dirigido a unidades personales de Google Drive; no selecciona unidades compartidas.

Los nombres nuevos deben ser distintos de todas las conexiones Rclone existentes. Si más adelante otra herramienta crea una conexión con el mismo nombre, la aplicación informa de un conflicto en lugar de elegir credenciales arbitrariamente. El asistente no detecta si has autorizado dos nombres diferentes con la misma cuenta Google: debes elegir correctamente la cuenta en el navegador.

### Montaje al iniciar sesión

Se configura por cuenta desde **Ajustes de la cuenta**, con la cuenta desmontada, o al añadirla. La aplicación crea únicamente su lanzador `~/.config/autostart/drive-manager-automount.desktop` y lo elimina cuando ninguna cuenta lo necesita. No reemplaza un lanzador ajeno ni detiene montajes al desmarcar la opción. En KDE, el lanzador inicia los montajes seleccionados mediante systemd de usuario al entrar en la sesión gráfica. No hace falta mantener abierta la ventana de Drive Manager y no se activa linger.

El montaje manual sigue disponible. La automatización omite las cuentas que ya tienen un montaje/servicio activo. Si falla por falta de red al iniciar sesión, consulta la cuenta en la interfaz y monta manualmente; todavía no hay reintentos automáticos de inicio. El montaje automático se aplica al próximo inicio de sesión, no empieza a montar al guardar la casilla.

### Validación

36 pruebas automatizadas aprobadas, incluidas cuatro cuentas simuladas y Qt offscreen. La autorización real y el inicio de sesión automático quedan pendientes de aceptación en tu escritorio. No se ejecutaron OAuth ni paradas de servicios durante el desarrollo.

Fuentes: [creación de conexiones en Rclone](https://rclone.org/commands/rclone_config_create/) y [OAuth en navegador](https://rclone.org/commands/rclone_authorize/).

## Corrección 1.1.1: navegador de autorización

El enlace local de OAuth se obtiene de la salida de Rclone y se abre mediante Qt en el navegador predeterminado de la sesión. Durante OAuth aparece **Abrir navegador para autorizar**, que permite reintentar con el mismo enlace mientras la sesión esté activa. Se admiten únicamente enlaces `http://127.0.0.1:53682/auth` con el estado emitido por Rclone. El enlace no se guarda ni se registra.

La salida del proceso OAuth ahora se procesa exclusivamente en memoria en un búfer acotado, sin presentar líneas originales ni tokens. El resto de procesos conserva su política anterior. Las variables de entorno RCLONE_* no se heredan durante el alta, para no incorporar configuraciones de log o credenciales externas. El archivo original de Rclone no cambia.

Los errores del asistente permanecen visibles hasta una nueva acción o cambio de cuenta. Se distinguen nombres inválidos/repetidos, carpetas no válidas y servidor local/puerto ocupado. Si el puerto 53682 está ocupado no se detiene el proceso que lo usa.

40 pruebas aprobadas, incluido envío del enlace a Qt y reintento del botón. La apertura y consentimiento en un navegador real deben comprobarse al instalar esta corrección.

## Corrección 1.1.2: botón de navegador desactivado

Reproducción con Rclone 1.74.3: el estado OAuth tiene 128 bits, que se codifican como 22 caracteres. El filtro de 1.1.1 exigía 32 caracteres y descartaba el enlace. Se corrige para admitir el formato real conservando la restricción al servidor local de Rclone.

41 pruebas automatizadas aprobadas. Además se ejecutó una comprobación con Rclone real: se recibió el enlace en el callback y se canceló antes de abrir navegador o consentir en Google. Se comprobó la eliminación del archivo temporal. Ningún servicio de montaje activo fue detenido. La autorización completa en Google aún requiere aceptación en la sesión del usuario.

## Versión 1.2.0: conexión sencilla

Pulsa **Nueva conexión de Google Drive**: empieza OAuth y se abre directamente el navegador, sin pedir antes nombre ni carpeta. Elige la cuenta Google que quieras y autoriza el acceso de solo lectura. Después aparece un formulario con un nombre y carpeta nuevos propuestos; puedes cambiarlos por `personal`, `trabajo`, etc., y asignar una carpeta distinta a cada cuenta. Guarda y la conexión queda seleccionada para montar y abrir en Dolphin.

La autenticación se mantiene en un archivo temporal privado hasta guardar los detalles. Cancelar ese formulario descarta el archivo; no se registra una conexión. El permiso ya concedido en Google no se revoca automáticamente al cancelar. Sigue disponible el botón para reabrir el navegador mientras OAuth espera. El montaje automático es opcional en el formulario posterior.

43 pruebas aprobadas, incluyendo inicio de autenticación antes de los detalles, registro sin segundo OAuth, renombrado de la conexión temporal y limpieza tras cancelación. La aceptación completa con tus cuentas reales sigue pendiente. No se cambian cuentas ni montajes existentes.

## Versión 1.3.0: Desconectar y Eliminar conexión

Selecciona una cuenta en la lista:

- **Desconectar** desmonta únicamente el servicio propio, pide confirmación y conserva la conexión. El diálogo permite marcar **Desactivar también el montaje al iniciar sesión**. Si no lo marcas, el ajuste anterior se conserva. No se fuerza el desmontaje.
- **Eliminar conexión** pide confirmación y, si hay un montaje propio, lo detiene y comprueba que desapareció antes de retirar credenciales. Para cuentas añadidas por la app se elimina su archivo de conexión. Para conexiones existentes, el diálogo avisa explícitamente de que se editará Rclone y se afectará a otras herramientas; usa únicamente `rclone config delete <nombre>`.

Se retiran las preferencias de la cuenta y la copia privada de configuración de montaje, y se actualiza el lanzador automático. La conexión desaparece de la lista. Las carpetas y la caché de lectura se conservan: eliminar una conexión no elimina documentos locales ni remotos. No se revoca automáticamente el consentimiento OAuth en Google.

Los montajes y servicios externos activos no se detienen ni se adoptan. La eliminación se bloquea hasta desmontarlos desde la herramienta que los inició; si el servicio propio sigue ocupado tras solicitar stop, se conservan las credenciales. La interfaz muestra el origen «Cuenta de Drive Manager» o «Conexión existente de Rclone».

51 pruebas aprobadas. Incluyen confirmación, aislamiento de cuentas, conservación de archivos, bloqueo de montajes externos, orden stop/retirada de credenciales, fallo de desmontaje y desactivación opcional del montaje automático. Durante el desarrollo no se han eliminado conexiones reales del usuario.

## Versión 1.4.0: proveedores Google Drive e Internxt

Elige el **Proveedor de la nueva conexión** y pulsa **Nueva conexión**:

- **Google Drive** conserva el flujo directo de navegador. Después de autorizar se elige nombre y carpeta.
- **Internxt** pide nombre único, correo y contraseña (campo oculto). Si solicita 2FA, introduce el código en el diálogo posterior. Después elige la carpeta y los ajustes de montaje. El nombre se fija antes del acceso para mantener la configuración cifrada; para otras cuentas usa nombres diferentes, como `internxt_personal`.
- **OneDrive** aparece como próximo proveedor, desactivado. Todavía no se implementa ni se descubren sus conexiones.

Internxt utiliza la integración nativa de Rclone 1.73 o superior, no WebDAV. La compatibilidad depende del plan de Internxt. Consulta [documentación del backend](https://rclone.org/internxt/). Las conexiones existentes sin cifrado de tipo internxt también se descubren y su configuración original se conserva al montar.

### Cartera KDE y cifrado

Para registrar Internxt se necesita KWallet operativo con cartera `kdewallet` y carpeta `Passwords`. Si no tienes cartera, créala o actívala mediante el gestor de carteras KDE. Si aparece una solicitud de acceso de `kwallet-query`, autoriza el acceso de la aplicación. No compartas tus claves ni contraseñas en el chat.

La configuración privada de Internxt se cifra usando el formato nativo de Rclone. La clave de cifrado aleatoria se guarda como `drive-manager-rclone-key` en KWallet; la contraseña de Internxt no se almacena en las preferencias. La aplicación nunca sustituye una clave existente cuando falla su lectura y no usa una configuración sin cifrar como alternativa. Conserva la cartera: perder su clave impide descifrar las conexiones Internxt guardadas.

El alta se realiza por un socket Unix local dentro de un directorio temporal privado 0700, socket 0600. Correo, contraseña y 2FA viajan por ese canal, no por argumentos de procesos. Rclone escribe contraseña, token y datos de cifrado propios de Internxt únicamente en la configuración cifrada. No hay servidor TCP de registro ni salida de logs. La clave se obtiene de KWallet mediante `--password-command` al montar, por lo que la cartera debe estar accesible también para el montaje automático.

Las cuentas comparten la clave de cifrado de la aplicación, pero conservan archivos de configuración, preferencias, carpetas y cachés independientes. Eliminar una cuenta elimina su configuración y metadatos; se conserva la clave común de KWallet para no afectar a otras cuentas. Los documentos de la caché de lectura no se cifran localmente por esta función.

El montaje continúa siendo **solo lectura** para ambos proveedores. Internxt conserva los botones Conectar, Desconectar, Eliminar, Abrir en Dolphin, caché y montaje automático. Cancelar o fallar en el registro descarta la configuración temporal. La cancelación puede tardar hasta el límite de la solicitud HTTP local en curso (45 segundos).

### Verificación

59 pruebas automatizadas aprobadas. Incluyen configuración cifrada, metadatos por cuenta, llamada de KWallet sin claves en argumentos, no sobrescritura de claves, canal privado, 2FA, cancelación y mantenimiento de Google Drive. Comprobación adicional con Rclone real: escritura de un dato sintético por RC Unix a una configuración cifrada y ausencia del dato en texto claro. **La cartera real y el acceso real a una cuenta Internxt aún deben probarse en tu sesión**; durante el desarrollo no se usaron tus credenciales.

## Versión 1.5.0: OneDrive disponible

Selecciona **OneDrive** en el proveedor y pulsa **Nueva conexión**. Se abre el navegador para iniciar sesión en Microsoft y autorizar acceso de lectura. Si Microsoft devuelve una sola unidad se selecciona automáticamente; si devuelve varias, la interfaz te pide elegir. Después asigna un nombre y una carpeta vacía independiente, guarda y monta desde la aplicación.

Se admiten OneDrive personal y empresarial en la región global estándar. El asistente no configura SharePoint ni nubes gubernamentales/China. Algunas cuentas de trabajo necesitan consentimiento del administrador; la aplicación no elude las políticas de Microsoft. Consulta [documentación de OneDrive en Rclone](https://rclone.org/onedrive/).

Se solicitan `Files.Read Files.Read.All offline_access`, sin permisos de escritura ni Sites.Read.All. Cada cuenta utiliza un archivo privado 0600 con tokens OAuth, como Google Drive. No se cambia la configuración original de Rclone y no se usa la cartera Internxt para estas cuentas. Se detectan también conexiones OneDrive existentes de tipo `onedrive`.

La interfaz conserva Desconectar, Eliminar, Abrir en Dolphin, carpetas independientes, caché y montaje automático. Todos los montajes continúan en solo lectura. No se registran tokens ni la salida de los pasos OAuth; los únicos datos presentados durante la elección son los nombres/tipos de unidades. Una selección cancelada o configuración incompleta descarta el temporal.

65 pruebas aprobadas, con elección de unidad única/múltiple, cancelación, scopes de lectura, validación de la configuración y encaminamiento de la interfaz. Además se comprobó con Rclone real la entrega del enlace OAuth de OneDrive y la limpieza al cancelar, sin login ni consentimiento Microsoft. La aceptación completa contra tu cuenta real sigue pendiente.

## Versión 1.6.0: lista de cuentas y modo lectura/escritura

La pantalla principal muestra una tabla con cuenta, proveedor, carpeta, modo y estado. Selecciona una fila para Conectar, Desconectar, Eliminar, abrir Dolphin o editar sus ajustes. Los estados se consultan en segundo plano; los montajes externos aparecen con acceso desconocido y no se controlan como propios.

### Elegir acceso

- Para una **nueva conexión**, selecciona proveedor y el **Modo de las nuevas conexiones** antes de pulsar Nueva conexión. Por defecto es solo lectura. Google y Microsoft piden permisos de escritura únicamente si elegiste Lectura/escritura; el flujo de navegador sigue siendo directo.
- Para **Internxt ya conectado**, desconecta y marca Lectura/escritura en Ajustes de la cuenta. Su autenticación actual permite ese acceso; no se necesita otro OAuth.
- Para **Google Drive/OneDrive creados anteriormente en solo lectura**, sus tokens no conceden escritura. Añade de nuevo la cuenta con Nueva conexión en modo Lectura/escritura, usando un nombre y carpeta independientes, o elimina primero la conexión antigua y vuelve a crearla. La aplicación no reemplaza sus credenciales de forma silenciosa. Si una conexión existente ya dispone de permisos de escritura, puedes activar el modo desde Ajustes con la cuenta desconectada.

Tras conectar, puedes crear, modificar, mover y eliminar archivos desde Dolphin u otras aplicaciones. Estas operaciones sí modifican los archivos de la nube. El modo de montaje no se cambia mientras la unidad está activa. Volver a solo lectura no revoca permisos OAuth; cambia el acceso del montaje.

### Protección de subidas

Los montajes con escritura usan VFS full y una caché duradera separada por cuenta en `~/.cache/drive-manager-write-v1/`. La caché de solo lectura anterior se conserva separada. No se borra caché al desconectar, eliminar una conexión o salir. La interfaz muestra si hay cambios subiendo o pendientes, si la cola está vacía o si no puede verificarla.

Antes de Desconectar o Eliminar una unidad con escritura, se comprueba la cola VFS mediante un socket Unix privado y los metadatos Dirty de la caché. Si hay subidas, errores o no se puede comprobar el estado, se bloquea la operación. También se comprueba que no existan procesos con archivos/carpetas abiertos. Cierra los documentos y las ventanas de Dolphin de esa unidad antes de desconectar.

El desmontaje FUSE es normal, nunca forzado ni perezoso. Si una última escritura coincide con el desmontaje, se vuelve a revisar la caché después: las credenciales se conservan y la eliminación queda bloqueada si aparecen cambios pendientes. En ese caso reconecta en escritura y espera a que se suban. Tampoco se permite cambiar a solo lectura ni eliminar una conexión desconectada que conserve metadatos Dirty.

La unidad de escritura no tiene un plazo de systemd que termine forzando SIGKILL al desconectar. Cerrar la interfaz deja el montaje activo, como antes. Apagar el ordenador, cerrar la sesión o detener Rclone desde otras herramientas queda fuera del control de la interfaz; la caché conserva los datos pendientes para recuperarlos al montar de nuevo la misma cuenta en escritura. El mecanismo de protección no sustituye la espera a que se complete la sincronización.

Los límites de caché siguen siendo objetivos de limpieza, no cuotas estrictas, y los archivos abiertos/pendientes pueden superar el objetivo. La aplicación no revoca permisos ni limpia credenciales originales al cambiar modo. Los documentos locales en caché no están cifrados por la aplicación.

### Verificación

79 pruebas automatizadas aprobadas. Cubren compatibilidad con preferencias antiguas, permisos OAuth de lectura/escritura, caché separada, rechazo de escritura con autorización antigua de lectura, bloqueo por cola pendiente/errores/estado desconocido/archivos abiertos, comprobación posterior al desmontaje, recuperación y protección de credenciales al eliminar.

Prueba adicional con Rclone real y un backend local de prueba servido mediante WebDAV: una escritura quedó en cola, se persistió Dirty, se completó la subida y se verificaron contenido y limpieza. No se escribieron archivos en tus cuentas reales. La escritura real sobre Google Drive, Microsoft o Internxt y el desmontaje FUSE real quedan pendientes de aceptación en tu sesión.

Fuente: [estadísticas VFS de Rclone](https://rclone.org/rc/#vfs-stats-stats-for-a-vfs).

## Versión 1.7.0: progreso de transferencias

Selecciona una cuenta en la tabla para ver sus transferencias activas: archivo, porcentaje, velocidad en KiB/s y tiempo estimado cuando Rclone lo proporciona. La barra corresponde a la primera transferencia activa; no es un porcentaje global de todos los archivos. Se muestran hasta 50 transferencias activas y no se guarda un historial de nombres de archivos. Los datos se consultan aproximadamente cada dos segundos en segundo plano.

La tabla y la bandeja distinguen: **Subiendo cambios**, **Esperando subida**, **Transfiriendo archivos**, **Cola vacía**, **Error de transferencia**, **Error de red/reintentos**, **Autenticación requiere atención** y **No se puede verificar sincronización**. Se muestran también cantidades en espera y subiendo. Los mensajes se derivan de la cola y errores actuales de caché: un error histórico de Rclone no convierte una cola limpia en un fallo permanente. No se muestran cadenas de errores originales que puedan incluir secretos.

**Montado no equivale a conectado a la nube.** Una cola vacía no certifica conectividad ni que un archivo todavía abierto esté subido. El estado dice expresamente que la conectividad no se ha comprobado. Los fallos de autenticación o red se clasifican cuando existe evidencia de errores de transferencia actuales; no se fuerzan pruebas ni cambios en la nube para obtener un icono verde.

Los montajes nuevos de lectura y escritura tienen el canal privado de supervisión. Los montajes antiguos de solo lectura siguen funcionando, pero pueden aparecer sin supervisión hasta desconectarlos y volverlos a conectar. No es necesario interrumpir montajes activos para instalar. La supervisión no cambia las protecciones de subidas ni permite forzar un desmontaje.

El refresco periódico ya no desactiva los botones; si se solicita una operación durante una consulta de estado, se ejecuta al acabar esa consulta con las comprobaciones del backend. No se ejecutan mutaciones en paralelo.

87 pruebas aprobadas, incluyendo datos de porcentaje/velocidad/ETA, valores desconocidos y no finitos, clasificación de fallos sin exponer secretos, errores históricos y presentación Qt del porcentaje. Comprobación con Rclone real sobre un backend local sintético: los estados pasaron de pendiente/subiendo a cola vacía al completar la escritura. La visualización con transferencias reales de tus proveedores queda pendiente de aceptación.

Fuente: [estadísticas de transferencias de Rclone](https://rclone.org/rc/#core-stats-returns-stats-about-current-transfers).

## Versión 1.8.0

Reautorizar cuentas Google Drive y OneDrive conservando carpeta y ajustes.
Consulta [las garantías y limitaciones](docs/REAUTHORIZATION.md).

## Versión 1.9.0

Activa lectura/escritura en los ajustes de una cuenta existente. Si faltan permisos,
se solicita autorización mediante navegador sin duplicar la conexión.

## Versión 1.10.0

Botón **Diagnóstico** para comprobar dependencias y el estado local de la cuenta.
Informe ES/EN que se puede copiar sin credenciales ni datos personales.
[Detalles](docs/DIAGNOSTICS.md).

## Versión 1.11.0

Interfaz simplificada con tres acciones principales, menú Cuenta y transferencias
desplegables. [Guía](docs/INTERFACE.md).

## Versión 1.12.0

Notificaciones de escritorio con silencio persistente y deduplicación por cuenta.
[Detalles](docs/NOTIFICATIONS.md).
