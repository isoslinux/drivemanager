# Interfaz simplificada (1.11.0)

La barra superior reúne **Nueva conexión**, **Actualizar conexiones** y
**Diagnóstico**. El proveedor y el modo de las nuevas conexiones se eligen en
una fila compacta; crear Google Drive o OneDrive sigue abriendo el navegador.

Selecciona una cuenta y utiliza **Conectar**, **Desconectar** o **Abrir en Dolphin**.
El botón **Cuenta** ofrece **Ajustes**, **Reautorizar** y **Eliminar conexión**.
También puedes abrir este menú con el botón derecho sobre una fila: primero se
selecciona esa cuenta. Si su estado aún es desconocido, sus acciones permanecen
bloqueadas hasta completar la consulta. Se conservan las confirmaciones de
eliminación y desconexión y la protección de subidas pendientes y montajes externos.

**Transferencias** permite desplegar o plegar la tabla y la barra de progreso.
Se abre plegado; plegarlo no detiene el seguimiento. El estado resumido de las
subidas permanece junto a las acciones principales.

Los botones de cancelar y abrir el navegador aparecen durante la autorización
y se ocultan al finalizar. No se han cambiado credenciales, configuraciones de
Rclone ni unidades systemd como parte de esta reorganización visual.

## Implementación y comprobación

La distribución se implementa en `app.py` con widgets nativos Qt y acciones de
menú que reutilizan los controladores existentes. `account_list.py` permite elegir
la columna que ocupa el ancho disponible: carpeta para cuentas, archivo para
transferencias. Los estados locales ya consultados permiten actualizar los
controles al seleccionar otra fila, antes de la siguiente consulta periódica.

Las pruebas Qt comprueban selección de cuenta, bloqueo de acciones externas,
plegado, controles OAuth y conservación de las acciones previas. Las capturas
se han revisado con cuatro cuentas sintéticas, sin montar unidades reales.
