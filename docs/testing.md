# Plan de pruebas y resultados

## Automatizadas

Las pruebas de `tests/test_core.py` usan un ejecutor falso y directorios temporales. No consultan cuentas reales ni montan ni detienen unidades. Cubren:

- Filtrado de Google Drive guardado en archivo y rechazo de metadatos inválidos.
- Decodificación de espacios de mountinfo.
- Duplicados y servicios activos externos; no se emite `stop`.
- Confirmación obligatoria y parada únicamente de servicio propio.
- Argumentos de solo lectura, caché de lectura, aislamiento y permisos y supresión del diario.
- Nombres peligrosos, identidades independientes y rutas no vacías.
- Copia de configuración 0600; el original no cambia al actualizar la copia.
- Errores de proceso sin exposición de secretos.

`tests/test_ui.py` comprueba el arranque Qt, selección de conexión y botones con backend simulado. Para ejecutarlo sin pantalla, usa `QT_QPA_PLATFORM=offscreen`.

## Aceptación manual pendiente

Realizar en una sesión KDE de prueba, con una cuenta de prueba ya configurada y sin servicios activos ajenos:

1. Comparar contenido del archivo Rclone original antes y después del montaje.
2. Abrir la aplicación desde el lanzador, seleccionar una cuenta y montar. Confirmar unidad de usuario y punto FUSE.
3. Abrir Dolphin, leer un archivo y comprobar que no se admite escritura.
4. Cancelar el diálogo de desmontaje: la unidad sigue activa. Aceptar: desaparece el montaje.
5. Abrir dos instancias y montar a la vez: se crea una sola unidad.
6. Preparar un montaje externo antes de abrir la aplicación: no permite detenerlo.
7. Cortar y restablecer la red: documentar errores de lectura y recuperación de Rclone; la interfaz no se bloquea. El estado local no equivale a estado de red.
8. Probar varias cuentas, nombres con espacios, falta de Dolphin/FUSE y sesión sin bus systemd.
9. Comprobar bandeja, ocultar/restaurar, salida sin desmontaje y textos ES/EN.
10. Construir e instalar RPM en Fedora 44 limpio; repetir el flujo desde el lanzador.

Las pruebas reales no se ejecutan automáticamente sobre la sesión del usuario. No se alteran conexiones existentes ni se detienen servicios para ejecutar esta suite.

## Pruebas 1.0.1

19 pruebas aprobadas, incluida Qt offscreen. Añadidas: caché distinta por cuenta y persistencia de datos entre llamadas; rechazo de ruta simbólica; desmontaje confirmado de servicios full; bloqueo de propiedad sobre servicios con caché que no son solo lectura. Se verifica compatibilidad con el desmontaje de servicios off anteriores.

Aceptación de rendimiento pendiente: abrir el mismo PDF dos veces en Okular, cerrar el visor entre aperturas y comparar tiempos. Validar que el montaje continúa rechazando escrituras y que el cambio remoto se refleja en nuevas lecturas. No se promete funcionamiento sin conexión por tener datos parciales en caché.

## Pruebas 1.0.2

27 pruebas aprobadas. Se añaden valores por defecto, persistencia por cuenta y permisos, rechazo de valores fuera de rango/rutas peligrosas, enlaces, solapamientos y carpetas no vacías; bloqueo de edición de una cuenta activa sin emitir stop; parámetros personalizados en la invocación de montaje; y configuración corrupta sin sobrescritura. La prueba Qt ejercita el diálogo completo de guardar, los valores enviados al backend y el bloqueo del botón mientras la cuenta está montada.

Aceptación manual: desmontar una cuenta, guardar una carpeta nueva y valores de caché, reiniciar la aplicación y comprobar persistencia; montar y abrir Dolphin en la carpeta elegida; comprobar que otra cuenta mantiene sus ajustes. Cancelar el diálogo y verificar que no cambió nada. No se ha ejecutado este flujo sobre cuentas reales durante el desarrollo.

## Versión 1.1.0

36 pruebas aprobadas. Nuevas pruebas: cuatro cuentas/configuraciones y carpetas independientes; duplicado de nombre y solapamiento bloqueados antes de OAuth; cancelación antes de iniciar proceso; permisos privados y alcance de solo lectura; fallo de OAuth sin preferencias; lanzador creado/eliminado sin stop; lanzador ajeno conservado con rollback; inicio automático solo de cuentas seleccionadas desmontadas.

Aceptación real pendiente: autorizar las cuatro cuentas desde el navegador, verificando identidad antes de aceptar; comprobar sus contenidos en cuatro carpetas; cancelar una autorización y comprobar que no aparece conexión; cerrar sesión y volver a entrar con dos cuentas marcadas y dos desmarcadas. Los tests simulan OAuth y systemd: no certifican un consentimiento real de Google.

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
