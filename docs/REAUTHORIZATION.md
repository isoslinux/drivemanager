# Reautorizar cuentas (1.8.0)

Selecciona una conexión Google Drive o OneDrive creada por Drive Manager,
desconéctala y pulsa **Reautorizar cuenta**. Confirma e inicia sesión en el
navegador con la misma cuenta. No se desmontan unidades automáticamente.

Se conservan nombre, carpeta, caché, montaje automático, modo de acceso y opciones
del backend. Las credenciales nuevas se guardan en un archivo temporal privado y
sustituyen las anteriores de forma atómica únicamente al completar el proceso.
Cancelar, fallar o detectar un montaje concurrente conserva la conexión anterior.
OneDrive rechaza una unidad con un identificador o tipo distinto.

Google Drive requiere que el usuario elija la misma cuenta: esta versión no
comprueba automáticamente su identidad. No uses este botón para cambiar de cuenta;
crea una conexión independiente con otra carpeta.

Se bloquea la renovación con escrituras pendientes o caché de estado desconocido.
Internxt, conexiones externas y clientes OAuth personalizados no están incluidos
en esta entrega. No se modifica el rclone.conf existente ni se registran tokens.

## Pruebas

La suite usa credenciales sintéticas y servicios simulados. Verifica conservación
de ajustes y opciones, permisos 0600, cancelación, fallo, confirmación explícita,
rechazo de cuentas externas, montajes activos, subidas pendientes, montajes que
aparecen durante OAuth y selección de otra unidad OneDrive. La autenticación real
necesita una comprobación manual por el titular de la cuenta.
