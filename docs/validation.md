# Validación de la primera entrega

Fecha: 9 de octubre de 2026.

Entorno de ejecución: Fedora 44 KDE Plasma, Python 3.14.8 y PySide6 6.11.2.

- 19 pruebas automatizadas aprobadas: núcleo con procesos simulados y prueba Qt offscreen.
- Formato JSON de descubrimiento contrastado con Rclone instalado y un archivo ficticio sin credenciales.
- Lanzador verificado con desktop-file-validate.
- No se consultaron archivos de credenciales del usuario, ni se montaron unidades ni se detuvieron servicios.
- RPM y SRPM construidos correctamente tras instalar herramientas. Instalación pendiente.
- Pendiente: aceptación real con cuenta Drive de prueba, FUSE, systemd de usuario y bandeja KDE.

Las pruebas simuladas verifican las decisiones y los argumentos emitidos, no demuestran el funcionamiento extremo a extremo contra Google Drive. El MVP limita el montaje a solo lectura y muestra el estado local, sin certificar conectividad remota.

Actualización 1.0.1: caché de lectura verificada con pruebas simuladas, sin detener servicios. Rendimiento real de PDF pendiente de comprobación por el usuario.

Versión 1.0.2: 27 pruebas (núcleo, preferencias y diálogo Qt). No se modificaron preferencias del usuario ni se detuvieron montajes activos. Aceptación real de ajustes pendiente.

Versión 1.1.0 (10 de octubre de 2026): 36 pruebas. Registro OAuth y automontaje simulados; autorización Google y sesión KDE real pendientes de aceptación.

## Corrección 1.1.1

Apertura OAuth explícita mediante Qt y botón para reintentar. Extracción de enlace local desde salida temporal de Rclone sin logs ni presentación de tokens; búfer acotado y errores persistentes. 40 pruebas aprobadas. No se han detenido servicios ni realizado consentimiento Google real durante esta corrección.

## Corrección 1.1.2

Se corrige la longitud mínima del estado OAuth: Rclone real emite 22 caracteres para 128 bits. 41 pruebas aprobadas y prueba de enlace/cancelación con Rclone 1.74.3 real, sin abrir navegador ni conceder acceso a Google. El callback recibió el enlace y se limpiaron los temporales.

## Versión 1.2.0

El botón de nueva conexión inicia OAuth directamente. `begin_authorization()` genera una identidad temporal y devuelve las credenciales privadas preparadas. El formulario de nombre/carpeta aparece después; guardar promueve y renombra la conexión sin repetir OAuth. Cancelar descarta el temporal. 43 pruebas aprobadas, incluyendo la secuencia Qt y el registro en dos fases. No se detienen servicios activos.

## Versión 1.3.0

`disconnect()` conserva credenciales y puede desactivar el inicio automático bajo confirmación. `remove_connection()` aplica el bloqueo de operaciones, solicita alcance explícito para conexiones externas y verifica desmontaje antes de eliminar metadatos. La UI identifica origen y confirma la operación. No se borran archivos de Drive ni carpetas locales. 51 pruebas aprobadas con archivos temporales y procesos simulados; ninguna conexión real se eliminó durante el desarrollo.

## Versión 1.4.0

`providers.py` define proveedores y flujos: Google Drive por navegador, Internxt por credenciales y OneDrive reservado. `internxt.py` configura Rclone por RC en socket Unix privado y maneja 2FA. `wallet.py` guarda una clave común en KWallet sin argumentos secretos. Las configuraciones Internxt se cifran antes de introducir credenciales; `Accounts` descubre sus nombres mediante metadatos privados y `Manager` añade password-command al montaje. Los nombres Internxt se fijan antes de autenticarse y no se renombra texto cifrado.

59 pruebas aprobadas y prueba adicional con Rclone real del cifrado y canal Unix usando datos sintéticos, sin cuenta Internxt real. Pendiente aceptación de KWallet, login, 2FA y navegación con un plan compatible. No se modificaron credenciales ni servicios activos del usuario.

## Versión 1.5.0

OneDrive se activa en `providers.py`. `onedrive.py` ejecuta la máquina de estados no interactiva de Rclone, separa JSON de stdout y avisos de stderr en memoria, envía el enlace OAuth validado a Qt y procesa únicamente la elección de unidades `config_driveid`. Se limita a OneDrive personal/business, con scopes de lectura; SharePoint queda fuera. `begin_authorization()` despacha por proveedor y conserva el flujo Google anterior.

65 pruebas aprobadas y comprobación real del enlace OAuth de OneDrive/cancelación con Rclone 1.74.3, sin consentimiento ni cuenta Microsoft real. Pendiente aceptación del login, selección de unidad y apertura de documentos de la cuenta del usuario.

## Versión 1.6.0

`Preferences.writable` mantiene compatibilidad con versiones anteriores (false por defecto). El alta solicita scopes de escritura solo cuando se selecciona ese modo; no se sustituyen tokens de perfiles existentes de lectura. `account_list.py` presenta una tabla nativa con selección de cuenta.

`transfers.py` valida estadísticas de uploads por socket Unix privado y metadatos persistentes Dirty. La escritura usa caché propia y unidades con descripción diferenciada. `stop_managed()` exige cola limpia, caché limpia y ausencia de archivos abiertos, desmonta FUSE sin force/lazy y revisa la caché después. Eliminar y pasar a lectura se bloquean con datos pendientes, conservando credenciales y caché para reconectar. No se usa inUse como contador de archivos abiertos: es el contador de referencias VFS de Rclone; se utiliza fuser y el desmontaje normal.

79 pruebas aprobadas y prueba real de VFS con subida de datos sintéticos a backend local, comprobando cola, Dirty, finalización y contenido. Pendiente aceptación FUSE y escritura en nubes reales. No se modificaron servicios activos ni credenciales del usuario durante el desarrollo.

## Versión 1.7.0

`Progress` y `Transfer` son DTO inmutables construidos en memoria a partir de vfs/stats y core/stats, con validación de números y estados. No se persisten nombres de archivos ni errores originales. `Status` incorpora el progreso para el controlador Qt. La interfaz presenta las transferencias activas y actualiza la tabla/bandeja sin afirmar conectividad a partir de un montaje local o cola vacía. El sondeo es silencioso y las acciones durante un sondeo se serializan.

87 pruebas aprobadas, incluyendo estados/errores históricos, nombres sin caracteres de control, porcentaje/velocidad/ETA no disponibles, fallo de monitor y presentación Qt. Prueba adicional con Rclone real y backend local verifica estado pendiente y finalización. No se modifican datos de cuentas reales ni se detienen servicios activos durante el desarrollo.
