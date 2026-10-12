# Notificaciones de escritorio (1.12.0)

Drive Manager utiliza las notificaciones nativas de la bandeja de Qt, integradas
con KDE. Avisa cuando una cola de subidas que ha observado queda vacía, cuando
la autenticación requiere atención o cuando falla una transferencia.

Activa o desactiva **Notificaciones de escritorio** en la ventana o en el menú de
la bandeja. El ajuste global se guarda en `~/.config/drive-manager/notifications.json`
con permisos 0600 y sustitución atómica. Una preferencia ilegible desactiva los
avisos. Si no se puede guardar, se conserva la elección anterior.

Los avisos identifican la conexión y usan mensajes fijos. No contienen nombres
de archivos, rutas, credenciales, tokens ni el error bruto de Rclone. Pulsar un
aviso muestra la ventana principal. KDE puede silenciarlos en su modo No molestar.

## Límites y protección contra repeticiones

- Se supervisan todas las cuentas de la tabla mientras la aplicación está abierta,
  aunque esté oculta en la bandeja. No se crea un servicio de notificaciones separado.
- Solo se anuncia una cola vacía tras haber observado subidas pendientes en un
  montaje propio de lectura/escritura; no se confunden descargas, montajes externos
  o una desconexión con una subida completada.
- Estados desconocidos no anuncian finalización. Una cola vacía no es una prueba
  independiente de conectividad ni una verificación remota de cada archivo.
- Cada tipo de error se anuncia una vez por incidente, por cuenta, hasta observar
  recuperación. Un fallo de red transitorio no genera un aviso adicional.
- Los eventos ocurridos mientras los avisos están silenciados no se reproducen al
  volver a activarlos. El historial de deduplicación dura la sesión de la aplicación.
- No se montan, desmontan ni reautorizan cuentas como respuesta a un aviso. Si hay
  cambios pendientes, se mantienen los bloqueos existentes de caché y credenciales.

## Arquitectura y pruebas

`notifications.py` contiene el seguimiento de transiciones y la preferencia
privada; `app.py` consume los eventos en el hilo Qt mediante QSystemTrayIcon.
Las pruebas simulan colas, errores, recuperación, varias cuentas, silencio,
configuración dañada, enlaces simbólicos y fallo al guardar. La integración
visual nativa debe comprobarse desde una sesión KDE real.
