# Diagnóstico local (1.10.0)

Pulsa **Diagnóstico**, incluso si todavía no tienes ninguna cuenta. La aplicación
consulta Rclone, FUSE 3, el acceso a `/dev/fuse`, systemd de usuario y la presencia
de Dolphin, systemd-run, fuser y kwallet-query. Los componentes ausentes muestran
el paquete que debes instalar. El mínimo de Rclone es 1.73.

Si hay una cuenta seleccionada, se comprueba su montaje local y la caché de
escritura. Los montajes externos no se consideran gestionados ni se afirma que
su cola de subidas esté vacía. Un estado de caché desconocido requiere atención.
No se prueba la conectividad con la nube ni la vigencia de los permisos OAuth.

**Copiar informe** copia exactamente el texto visible al portapapeles para poder
compartirlo. No lo envía automáticamente. El informe contiene mensajes fijos y
versiones numéricas verificadas; no incluye cuentas, correos, rutas personales,
nombres de archivos, tokens, contraseñas, salida bruta de comandos ni registros.

## Arquitectura y pruebas

- `diagnostics.py`: modelos inmutables, comprobaciones de lectura y catálogo ES/EN.
- `Probe`: comandos fijos, cuatro segundos de espera por comando y stderr descartado.
- `app.py`: ejecuta el diagnóstico en el trabajador existente y presenta una ventana
  de solo lectura; la copia requiere pulsar el botón.
- Las pruebas cubren componentes ausentes, versiones antiguas, espera agotada,
  respuestas inesperadas, datos secretos sintéticos, caché pendiente/desconocida,
  montajes externos, permisos FUSE y correspondencia entre informe visible y copia.

No se abre KWallet, no se instalan paquetes ni se modifican credenciales o servicios.
Una sesión restringida, contenedor o sandbox puede impedir usar FUSE o acceder al
bus de systemd; comprueba también desde la sesión KDE normal antes de concluir que
falla la instalación. La presencia de kwallet-query no comprueba si la cartera
está desbloqueada.
