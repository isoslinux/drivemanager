# Espacio por cuenta (1.13.0)

Al seleccionar una conexión se consulta su cuota en segundo plano y se muestran
los valores disponibles: usado, libre, total, otros servicios y papelera. La barra
representa la ocupación del total indicado por el proveedor. Cuando existe el dato
libre, se calcula a partir de total menos libre; si no existe, utiliza el usado y
otros servicios informados, sin inventar una cantidad libre ni sumar dos veces
la papelera. Los tamaños se muestran en unidades binarias (GiB, MiB, etc.).

En Google la cuota puede incluir otros servicios, como Gmail y Fotos. Se muestran
por separado cuando Rclone los facilita. La cuenta queda marcada con poco espacio
cuando queda un 10 % o menos del total informado, o cuando el libre es cero. El
aviso de escritorio respeta el ajuste global y no se repite hasta observar una
recuperación. No detiene subidas ni elimina datos.

Los resultados se conservan en memoria cinco minutos. **Actualizar espacio**
fuerza una nueva consulta. Las transferencias y acciones siguen funcionando
mientras se consulta la cuota. Una respuesta de una cuenta que ya no está seleccionada
no sustituye los datos visibles de la nueva selección.

Si no hay soporte, faltan datos o falla la consulta se muestra **No disponible**.
No significa espacio ilimitado ni libre cero. No se cuentan todos los archivos
como alternativa: eso sería lento y no equivale a consultar la cuota.

## Credenciales y limitaciones

Las consultas de configuraciones sin cifrar utilizan una copia temporal privada
con permisos 0600 en una carpeta 0700. Una posible renovación OAuth queda en esa
copia; la configuración original se conserva y la copia se elimina al terminar.
No se abre el navegador, se registran tokens ni se cambia ningún servicio.

Las cuentas cifradas creadas por la aplicación (Internxt) se consultan a través del
socket privado de su montaje activo. Si no están montadas, se muestra No disponible,
sin abrir KWallet en segundo plano. Las configuraciones externas cifradas y los
archivos de configuración enlazados no se consultan en esta entrega.

La consulta no verifica las subidas ni la integridad de archivos. Los datos dependen
del proveedor y pueden actualizarse con retraso.

## Arquitectura y pruebas

`quota.py` valida campos numéricos y consulta `rclone about --json` o
`operations/about` sobre un socket privado. La interfaz usa un trabajador separado,
una caché en memoria y controles Qt. Cada comando de consulta tiene un tiempo
máximo de doce segundos; la conexión RC tiene un límite de diez segundos.

Las pruebas cubren cuotas compartidas, campos ausentes, valores inválidos,
conservación de configuración original, limpieza temporal, timeout configurado,
cuentas cifradas desconectadas y cambios de selección en Qt. Se ha verificado
además una consulta real a un backend local sintético, sin cuentas de nube ni montajes.

Referencias oficiales: [rclone about](https://rclone.org/commands/rclone_about/) y
[operations/about](https://rclone.org/rc/#operations-about).
