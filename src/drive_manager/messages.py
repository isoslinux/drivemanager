"""English and Spanish UI messages; stable keys shared by every language."""

TEXT = {'en': {'title': 'Drive Manager',
        'refresh': 'Refresh connections',
        'mount': 'Connect',
        'unmount': 'Disconnect',
        'open': 'Open in Dolphin',
        'quit': 'Quit application',
        'oauth_open': 'Open authorization browser',
        'oauth_port': 'Another authorization is using port 53682. Close it or cancel it and retry.',
        'oauth_server': 'Could not start the local authorization server.',
        'onedrive_error': 'Could not configure OneDrive. Check Microsoft permissions and selected drive.',
        'choose_drive': 'Choose your OneDrive drive',
        'first_transfer': 'First transfer',
        'queued_label': 'Queued',
        'uploading_label': 'Uploading',
        'transfers': 'Transfers',
        'uploading': 'Uploading changes',
        'queued': 'Waiting to upload',
        'transferring': 'Transferring files',
        'idle': 'Queue empty · Cloud connectivity not checked',
        'network_retry': 'Network error · Retrying transfers',
        'auth_required': 'Authentication needs attention',
        'transfer_error': 'Transfer error · Changes remain pending',
        'monitor_unknown': 'Cannot verify synchronization',
        'unmonitored': 'Mounted locally · Synchronization not monitored',
        'provider_column': 'Provider',
        'account': 'Account',
        'status': 'Status',
        'access': 'Access',
        'mode': 'Mode for new connections',
        'mode_ro': 'Read only',
        'mode_rw': 'Read/write',
        'mounted_rw': 'Mounted (read/write)',
        'sync_pending': 'Changes uploading or pending',
        'sync_unknown': 'Upload status could not be verified',
        'sync_clean': 'Upload queue empty',
        'uploads_pending': 'Pending changes remain. Wait for uploads, or reconnect in read/write mode to '
                           'recover them.',
        'uploads_unknown': 'Cannot verify pending changes. Disconnect and deletion are blocked.',
        'files_open': 'Close files and Dolphin windows on this drive before disconnecting.',
        'needs_write_auth': 'This account was authorized for reading. Enable read/write in account settings '
                            'to authorize access.',
        'write_note': 'Read/write changes your cloud files. Google/Microsoft may ask you to authorize write '
                      'access in your browser.',
        'provider': 'Provider for new connection',
        'email': 'Email',
        'password': 'Password',
        'twofa': 'Internxt two-factor code',
        'internxt_error': 'Internxt login failed. Check credentials, two-factor code and plan compatibility.',
        'wallet_error': 'Unlock or create the KDE wallet named kdewallet, then retry.',
        'internxt_wait': 'Connecting to Internxt. Unlock KDE Wallet if requested.',
        'name_error': 'Use a unique name starting with a letter, with only letters, numbers, hyphens or '
                      'underscores.',
        'folder_error': 'Choose an empty, separate folder inside your home directory, without symlinks.',
        'browser_error': 'The browser could not be opened. Check your default browser and retry the button.',
        'add': 'New connection',
        'cancel_oauth': 'Cancel authorization',
        'name': 'Account name',
        'oauth_note': 'Account authenticated. Choose its name and an empty folder.',
        'auth_wait': 'Complete authorization in your browser (up to 10 minutes).',
        'auth_error': 'Could not add account. Check unique name and empty, separate home folder; '
                      'authorization may have been cancelled.',
        'automount': 'Mount this account at login',
        'settings': 'Account settings',
        'path': 'Mount folder',
        'cache_size': 'Cache target (GiB)',
        'cache_age': 'Keep unused cache (hours)',
        'choose': 'Choose folder',
        'prefs_note': 'Applies on next mount. Cache size is a cleanup target.',
        'prefs_error': 'Cannot save. Use an empty folder inside your home, without symlinks or account '
                       'overlap.',
        'note': 'Independent accounts · Choose access mode per account',
        'confirm': 'Disconnect this account? Open files may stop working.',
        'disable_auto': 'Also disable mounting at login',
        'delete': 'Delete connection',
        'delete_own': 'Delete {name}? Its managed mount will be disconnected and saved credentials removed. '
                      'Cloud files are preserved.',
        'delete_external': '{name} belongs to the existing Rclone configuration. Deleting it modifies that '
                           'configuration and affects other tools. Cloud files are preserved.',
        'delete_error': 'Cannot delete: disconnect external or busy mounts first. Check access to the '
                        'connection configuration.',
        'external_origin': 'Existing Rclone connection',
        'app_origin': 'Drive Manager account',
        'error': 'Operation failed',
        'empty': 'No connections found',
        'busy': 'Working…',
        'mounted': 'Mounted (read-only)',
        'external': 'External mount/service',
        'starting': 'Starting / reconnecting',
        'unmounted': 'Unmounted',
        'failed': 'Mount failed',
        'capacity': 'Storage',
        'quota_refresh': 'Refresh space',
        'quota_loading': 'Checking storage…',
        'quota_unknown': 'Storage: Not available',
        'quota_used': 'Used',
        'quota_free': 'Available',
        'quota_total': 'Total',
        'quota_other': 'Other services',
        'quota_trash': 'Trash',
        'quota_low': 'Low available space',
        'notifications': 'Desktop notifications',
        'notification_settings_error': 'Could not save notification preference.',
        'uploads_done': 'Observed upload queue is now empty.',
        'notice_auth': 'Authentication needs attention. Open the app and reauthorize this account when safe.',
        'notice_error': 'A transfer failed. Keep the connection and cache while changes remain pending.',
        'file_name': 'File',
        'account_menu': 'Account',
        'diagnostics': 'Diagnostics',
        'copy_report': 'Copy report',
        'close_report': 'Close',
        'upgrade_confirm': 'Allow this connection to modify your cloud files? Your browser will open to '
                           'authorize read/write access. Sign in with the SAME account. Cancelling keeps the '
                           'current mode.',
        'reauth': 'Reauthorize account',
        'reauth_confirm': 'Sign in with the SAME account as this connection. Its folder, cache and settings '
                          'will be kept. The connection must be disconnected, with no pending uploads. '
                          'Continue?',
        'reauth_error': 'Could not renew authorization. Use a disconnected Google Drive, OneDrive or Dropbox '
                        'connection created by this app, without custom OAuth credentials. The original '
                        'connection has been preserved.',
        'reauth_identity': 'The selected OneDrive belongs to another drive. The original connection has been '
                           'preserved.',
        'language': 'Language',
        'language_error': 'Could not save language preference. The previous language is kept.'},
 'es': {'title': 'Drive Manager',
        'refresh': 'Actualizar conexiones',
        'mount': 'Conectar',
        'unmount': 'Desconectar',
        'open': 'Abrir en Dolphin',
        'quit': 'Salir de la aplicación',
        'oauth_open': 'Abrir navegador para autorizar',
        'oauth_port': 'Otra autorización ocupa el puerto 53682. Ciérrala o cancélala y vuelve a intentarlo.',
        'oauth_server': 'No se pudo iniciar el servidor local de autorización.',
        'onedrive_error': 'No se pudo configurar OneDrive. Comprueba permisos de Microsoft y unidad elegida.',
        'choose_drive': 'Elige tu unidad de OneDrive',
        'first_transfer': 'Primera transferencia',
        'queued_label': 'En espera',
        'uploading_label': 'Subiendo',
        'transfers': 'Transferencias',
        'uploading': 'Subiendo cambios',
        'queued': 'Esperando subida',
        'transferring': 'Transfiriendo archivos',
        'idle': 'Cola vacía · Conectividad con la nube no comprobada',
        'network_retry': 'Error de red · Reintentando transferencias',
        'auth_required': 'La autenticación requiere atención',
        'transfer_error': 'Error de transferencia · Quedan cambios pendientes',
        'monitor_unknown': 'No se puede verificar la sincronización',
        'unmonitored': 'Montado localmente · Sin supervisión de sincronización',
        'provider_column': 'Proveedor',
        'account': 'Cuenta',
        'status': 'Estado',
        'access': 'Acceso',
        'mode': 'Modo de las nuevas conexiones',
        'mode_ro': 'Solo lectura',
        'mode_rw': 'Lectura/escritura',
        'mounted_rw': 'Montado (lectura/escritura)',
        'sync_pending': 'Cambios subiendo o pendientes',
        'sync_unknown': 'No se pudo verificar el estado de las subidas',
        'sync_clean': 'Cola de subidas vacía',
        'uploads_pending': 'Quedan cambios pendientes. Espera las subidas o vuelve a conectar en escritura '
                           'para recuperarlos.',
        'uploads_unknown': 'No se pueden verificar los cambios pendientes. Se bloquea desconectar y '
                           'eliminar.',
        'files_open': 'Cierra los archivos y ventanas de Dolphin de esta unidad antes de desconectar.',
        'needs_write_auth': 'Esta cuenta se autorizó para lectura. Activa lectura/escritura en los ajustes '
                            'de la cuenta para autorizar el acceso.',
        'write_note': 'Lectura/escritura modifica archivos de la nube. Las cuentas Google/Microsoft '
                      'autorizadas solo para lectura requieren una nueva autorización.',
        'provider': 'Proveedor de la nueva conexión',
        'email': 'Correo',
        'password': 'Contraseña',
        'twofa': 'Código de dos factores de Internxt',
        'internxt_error': 'Falló el acceso a Internxt. Comprueba credenciales, código de dos factores y '
                          'compatibilidad del plan.',
        'wallet_error': 'Desbloquea o crea la cartera KDE llamada kdewallet y vuelve a intentarlo.',
        'internxt_wait': 'Conectando a Internxt. Desbloquea KWallet si lo solicita.',
        'name_error': 'Usa un nombre único que empiece por una letra, solo con letras, números, guiones o '
                      'guiones bajos.',
        'folder_error': 'Elige una carpeta vacía e independiente dentro de tu directorio personal, sin '
                        'enlaces simbólicos.',
        'browser_error': 'No se pudo abrir el navegador. Comprueba el navegador predeterminado y reintenta '
                         'con el botón.',
        'add': 'Nueva conexión',
        'cancel_oauth': 'Cancelar autorización',
        'name': 'Nombre de la cuenta',
        'oauth_note': 'Cuenta autenticada. Elige su nombre y una carpeta vacía.',
        'auth_wait': 'Completa la autorización en el navegador (hasta 10 minutos).',
        'auth_error': 'No se pudo añadir. Comprueba nombre único y carpeta vacía e independiente; la '
                      'autorización puede haberse cancelado.',
        'automount': 'Montar esta cuenta al iniciar sesión',
        'settings': 'Ajustes de la cuenta',
        'path': 'Carpeta de montaje',
        'cache_size': 'Objetivo de caché (GiB)',
        'cache_age': 'Conservar caché sin uso (horas)',
        'choose': 'Elegir carpeta',
        'prefs_note': 'Se aplica al próximo montaje. El tamaño es un objetivo de limpieza.',
        'prefs_error': 'No se pudo guardar. Usa una carpeta vacía dentro de tu directorio personal, sin '
                       'enlaces ni solapamientos.',
        'note': 'Cuentas independientes · Modo de acceso por cuenta',
        'confirm': '¿Desconectar esta cuenta? Los archivos abiertos pueden dejar de funcionar.',
        'disable_auto': 'Desactivar también el montaje al iniciar sesión',
        'delete': 'Eliminar conexión',
        'delete_own': '¿Eliminar {name}? Se desconectará su montaje propio y se retirarán las credenciales '
                      'guardadas. Los archivos de la nube se conservan.',
        'delete_external': '{name} pertenece a la configuración existente de Rclone. Eliminarla modifica esa '
                           'configuración y afecta a otras herramientas. Los archivos de Google Drive se '
                           'conservan.',
        'delete_error': 'No se pudo eliminar: desmonta primero los montajes externos u ocupados y comprueba '
                        'el acceso a la configuración.',
        'external_origin': 'Conexión existente de Rclone',
        'app_origin': 'Cuenta de Drive Manager',
        'error': 'La operación ha fallado',
        'empty': 'No hay conexiones guardadas',
        'busy': 'Procesando…',
        'mounted': 'Montado (solo lectura)',
        'external': 'Montaje/servicio externo',
        'starting': 'Iniciando / reconectando',
        'unmounted': 'Desmontado',
        'failed': 'Montaje fallido',
        'capacity': 'Espacio',
        'quota_refresh': 'Actualizar espacio',
        'quota_loading': 'Consultando espacio…',
        'quota_unknown': 'Espacio: No disponible',
        'quota_used': 'Usado',
        'quota_free': 'Disponible',
        'quota_total': 'Total',
        'quota_other': 'Otros servicios',
        'quota_trash': 'Papelera',
        'quota_low': 'Poco espacio disponible',
        'notifications': 'Notificaciones de escritorio',
        'notification_settings_error': 'No se pudo guardar el ajuste de notificaciones.',
        'uploads_done': 'La cola de subidas observada ha quedado vacía.',
        'notice_auth': 'La autenticación requiere atención. Abre la aplicación y reautoriza esta cuenta '
                       'cuando sea seguro.',
        'notice_error': 'Falló una transferencia. Conserva la conexión y la caché mientras queden cambios '
                        'pendientes.',
        'file_name': 'Archivo',
        'account_menu': 'Cuenta',
        'diagnostics': 'Diagnóstico',
        'copy_report': 'Copiar informe',
        'close_report': 'Cerrar',
        'upgrade_confirm': '¿Permitir que esta conexión modifique tus archivos en la nube? Se abrirá el '
                           'navegador para autorizar lectura/escritura. Inicia sesión con la MISMA cuenta. '
                           'Cancelar conserva el modo actual.',
        'reauth': 'Reautorizar cuenta',
        'reauth_confirm': 'Inicia sesión con la MISMA cuenta de esta conexión. Se conservarán su carpeta, '
                          'caché y ajustes. Debe estar desconectada y sin subidas pendientes. ¿Continuar?',
        'reauth_error': 'No se pudo renovar la autorización. Usa una conexión Google Drive, OneDrive o Dropbox creada '
                        'por esta aplicación, desconectada y sin credenciales OAuth personalizadas. Se '
                        'conserva la conexión original.',
        'reauth_identity': 'La unidad OneDrive seleccionada es distinta. Se conserva la conexión original.',
        'language': 'Idioma',
        'language_error': 'No se pudo guardar el idioma. Se conserva el anterior.'}}

TEXT['en'].update({'updates': 'Check for updates',
 'update_checking': 'Checking updates…',
 'update_installed': 'Installed version',
 'update_latest': 'Latest stable version',
 'update_available': 'An update is available. Download the RPM and install it manually.',
 'update_current': 'You have the latest published stable version.',
 'update_ahead': 'Your installed version is newer than the latest published stable release.',
 'update_error': 'Could not check updates. Check your Internet connection and try again later.',
 'update_rate_limit': 'GitHub temporarily limited requests. Try again later.',
 'update_rpm_missing': 'No matching Fedora 44 RPM is available. Open the release page to view its '
                       'files.',
 'update_open_rpm': 'Download RPM',
 'update_open_release': 'Open release page',
 'update_open_error': 'Could not open the default browser.',
 'update_manual': 'Installation is manual. This check does not download or run software, change '
                  'credentials, or interrupt mounts and uploads.'})

TEXT['es'].update({'updates': 'Buscar actualizaciones',
 'update_checking': 'Buscando actualizaciones…',
 'update_installed': 'Versión instalada',
 'update_latest': 'Última versión estable',
 'update_available': 'Hay una actualización. Descarga el RPM e instálalo manualmente.',
 'update_current': 'Tienes la última versión estable publicada.',
 'update_ahead': 'La versión instalada es más reciente que la última entrega estable publicada.',
 'update_error': 'No se pudo comprobar. Revisa tu conexión a Internet y vuelve a intentarlo más '
                 'tarde.',
 'update_rate_limit': 'GitHub ha limitado temporalmente las consultas. Inténtalo más tarde.',
 'update_rpm_missing': 'No hay un RPM compatible con Fedora 44. Abre la página de la entrega para '
                       'ver sus archivos.',
 'update_open_rpm': 'Descargar RPM',
 'update_open_release': 'Abrir página de la entrega',
 'update_open_error': 'No se pudo abrir el navegador predeterminado.',
 'update_manual': 'La instalación es manual. Esta consulta no descarga ni ejecuta software, no '
                  'cambia credenciales ni interrumpe montajes o subidas.'})

TEXT['en'].update({'username': 'Username', 'webdav_url': 'WebDAV URL (HTTPS)', 'app_password': 'Application password', 'optional_2fa': 'Two-factor code (optional)', 'mailbox_password': 'Mailbox password (optional)', 'nextcloud_note': 'Copy the WebDAV address from Nextcloud Files settings. Create an application password in Nextcloud security settings.', 'proton_note': 'Experimental Rclone support. Sign in to Proton Drive on the web at least once first. If enabled, enter a current two-factor code. Mailbox password is only needed for two-password accounts.', 'credentials_wait': 'Checking credentials securely…', 'credentials_error': 'Could not authenticate. Check credentials, two-factor code, server availability and Rclone compatibility.', 'webdav_url_error': 'Enter a valid HTTPS WebDAV URL without embedded credentials, query or fragment.'})

TEXT['es'].update({'username': 'Usuario', 'webdav_url': 'URL WebDAV (HTTPS)', 'app_password': 'Contraseña de aplicación', 'optional_2fa': 'Código de doble autenticación (opcional)', 'mailbox_password': 'Contraseña del buzón (opcional)', 'nextcloud_note': 'Copia la dirección WebDAV de los ajustes de Archivos de Nextcloud. Crea una contraseña de aplicación en los ajustes de seguridad de Nextcloud.', 'proton_note': 'Soporte experimental de Rclone. Inicia sesión primero en Proton Drive desde la web al menos una vez. Si usas doble autenticación, introduce un código actual. La contraseña del buzón solo se necesita para cuentas con dos contraseñas.', 'credentials_wait': 'Comprobando credenciales de forma segura…', 'credentials_error': 'No se pudo autenticar. Comprueba las credenciales, el código de doble autenticación, el servidor y la compatibilidad con Rclone.', 'webdav_url_error': 'Introduce una URL WebDAV HTTPS válida sin credenciales, consulta ni fragmento.'})

TEXT['en'].update({'check_connection': 'Check connection', 'connection_checking': 'Checking root-folder read access…', 'connection_ok': 'Root folder readable. Write access and upload completion were not checked.', 'connection_auth': 'Authentication failed. Renew authorization or check your credentials.', 'connection_permission': 'Read permission denied. Check the account’s server permissions.', 'connection_network': 'Network request failed. Check connectivity and server availability.', 'connection_rate': 'Provider request limit reached. Wait before checking again.', 'connection_timeout': 'Check timed out. The provider may be slow; this does not prove it is offline.', 'connection_error': 'Could not check access. Review provider compatibility and account setup.', 'connection_wallet': 'Could not unlock the private configuration. Check KDE Wallet.', 'connection_locked': 'Existing encrypted configurations require their original authentication setup.', 'connection_cancelled': 'Check cancelled.', 'connection_elapsed': '{seconds:.1f} s'})

TEXT['es'].update({'check_connection': 'Comprobar conexión', 'connection_checking': 'Comprobando acceso de lectura a la carpeta raíz…', 'connection_ok': 'Carpeta raíz accesible. No se ha comprobado escritura ni finalización de subidas.', 'connection_auth': 'Falló la autenticación. Renueva la autorización o revisa tus credenciales.', 'connection_permission': 'Lectura denegada. Revisa los permisos de la cuenta en el servidor.', 'connection_network': 'Falló la solicitud de red. Revisa la conexión y la disponibilidad del servidor.', 'connection_rate': 'Se alcanzó el límite de consultas del proveedor. Espera antes de comprobar de nuevo.', 'connection_timeout': 'La comprobación agotó el tiempo. El proveedor puede estar lento; no confirma que esté desconectado.', 'connection_error': 'No se pudo comprobar el acceso. Revisa la compatibilidad y la configuración de la cuenta.', 'connection_wallet': 'No se pudo desbloquear la configuración privada. Comprueba KWallet.', 'connection_locked': 'Las configuraciones cifradas externas necesitan su método de autenticación original.', 'connection_cancelled': 'Comprobación cancelada.', 'connection_elapsed': '{seconds:.1f} s'})

TEXT['en']['connection_last']='Last check'

TEXT['es']['connection_last']='Última comprobación'

TEXT['en'].update({'renew_credentials': 'Renew credentials', 'credential_confirm': 'Use the SAME account and server. The connection must be disconnected with no pending uploads. Folder, settings and cache will be retained. Replace its credentials?', 'credential_identity': 'The username or Nextcloud server differs from the original connection. Original credentials were retained.', 'credential_custom': 'Custom bearer-token or OTP-secret configurations require their original setup. Original credentials were retained.', 'credential_renew_error': 'Could not renew credentials. Use an encrypted connection created by this application, disconnected and with a clean upload cache. Original credentials were retained.'})

TEXT['es'].update({'renew_credentials': 'Renovar credenciales', 'credential_confirm': 'Usa la MISMA cuenta y servidor. La conexión debe estar desmontada y sin subidas pendientes. Se conservarán carpeta, ajustes y caché. ¿Sustituir sus credenciales?', 'credential_identity': 'El usuario o el servidor Nextcloud no coincide con la conexión original. Se conservaron las credenciales anteriores.', 'credential_custom': 'Las configuraciones con token bearer o secreto OTP personalizado requieren su método original. Se conservaron las credenciales anteriores.', 'credential_renew_error': 'No se pudieron renovar las credenciales. Usa una conexión cifrada creada por esta aplicación, desmontada y sin cambios pendientes en caché. Se conservaron las credenciales anteriores.'})

TEXT['en'].update({'tools': 'Tools', 'setup_guide': 'Setup guide', 'export_settings': 'Export settings', 'import_settings': 'Import settings', 'setup_steps': '1. Check local dependencies. This guide does not install software.\n2. Choose a provider and create your account in read-only mode.\n3. Assign an empty folder, connect and open it in Dolphin. Enable writing only when needed.', 'setup_finish': 'Finish guide', 'export_done': 'Exported settings for {count} accounts. No credentials or cache contents were included.', 'import_note': 'Review every folder, access mode, login-mount flag and speed limit. Accounts must already exist on this computer. Save applies these preferences only to disconnected accounts with no pending local changes. Enabled read/write and login mounting take effect on the next connection/login.', 'portable_error': 'Could not process this settings file. Check its format, matching account names/providers, empty separate folders, write authorization and file permissions. No credentials are imported.', 'portable_busy': 'Disconnect the affected accounts and finish pending uploads before importing settings.', 'upload_limit': 'Upload limit', 'download_limit': 'Download limit', 'unlimited': 'Unlimited', 'cache_health': 'Local cache: disk free {free} · Pending local files {pending}', 'cache_low': 'Low local disk space. Keep pending files and free space outside the upload cache.', 'cache_unknown': 'Local cache state could not be verified.', 'cloud_slow': 'Slow cloud response; previews, folder counting or speed limits can add delays.', 'validate_all': 'Validate accounts', 'validation_note': 'Read checks contact configured accounts only. Unchecked providers need an account. Writing and reconnect tests require separate confirmation. A successful read does not validate uploads, 2FA, renewal or outage recovery.', 'validation_read': 'Root read', 'validation_time': 'Response time', 'validation_unchecked': 'Not checked / no account result', 'validation_write': 'Test writing', 'validation_reconnect': 'Test reconnect', 'validation_guide': 'Acceptance guide', 'validation_confirm': 'Explicit test confirmation required.', 'validation_write_confirm': 'Create a small disposable test file in this account and verify its contents directly from the cloud? The file will remain so you can inspect or delete it yourself. The account must be managed, mounted read/write and have an empty upload queue.', 'validation_reconnect_confirm': 'Disconnect and reconnect this selected managed account? Pending uploads or open files will block the operation. Other accounts are not restarted.', 'validation_write_requires': 'Mount this managed account in read/write mode and finish pending uploads first.', 'validation_write_ok': 'Test contents verified directly from the cloud. The disposable test file remains.', 'validation_timeout': 'The test did not complete in time. Keep the test file and pending cache; inspect Transfers.', 'validation_error': 'Could not verify the test. Review access, upload state and local diagnostics. Keep pending data.', 'validation_finished': 'Read checks finished. Review each account; cancelled and missing accounts remain unverified.', 'validation_file': 'Disposable test file', 'validation_reconnect_ok': 'Managed mount reconnected. File integrity and outage recovery are separate checks.', 'acceptance_steps': 'For each provider:\n1. Configure a disposable account and run the root-read check.\n2. Mount read-only and confirm that writing is denied.\n3. Explicitly enable read/write and use Test writing; inspect the retained test file in the provider web app.\n4. Close files and use Test reconnect; verify the file again.\n5. Manually exercise required 2FA and credential renewal with the same account.\n6. Test an outage with disposable data; verify pending uploads block disconnect and recover after connectivity returns.\n7. Compare quota with the provider.\nThese owner-operated checks are not automatically marked as passed.'})

TEXT['es'].update({'tools': 'Herramientas', 'setup_guide': 'Asistente inicial', 'export_settings': 'Exportar ajustes', 'import_settings': 'Importar ajustes', 'setup_steps': '1. Comprueba las dependencias locales. El asistente no instala programas.\n2. Elige un proveedor y crea la cuenta en modo de solo lectura.\n3. Asigna una carpeta vacía, conecta y ábrela en Dolphin. Activa escritura solo cuando la necesites.', 'setup_finish': 'Finalizar asistente', 'export_done': 'Ajustes de {count} cuentas exportados. No se incluyeron credenciales ni contenidos de caché.', 'import_note': 'Revisa cada carpeta, modo de acceso, montaje al iniciar sesión y límite de velocidad. Las cuentas ya deben existir en este ordenador. Guardar aplica los ajustes solo a cuentas desmontadas y sin cambios locales pendientes. Escritura y montaje automático se aplicarán en la siguiente conexión o inicio de sesión.', 'portable_error': 'No se pudo procesar el archivo. Revisa formato, nombres y proveedores coincidentes, carpetas vacías separadas, autorización de escritura y permisos del archivo. No se importan credenciales.', 'portable_busy': 'Desmonta las cuentas afectadas y termina las subidas pendientes antes de importar ajustes.', 'upload_limit': 'Límite de subida', 'download_limit': 'Límite de bajada', 'unlimited': 'Sin límite', 'cache_health': 'Caché local: disco libre {free} · Archivos locales pendientes {pending}', 'cache_low': 'Poco espacio en el disco local. Conserva los archivos pendientes y libera espacio fuera de la caché de subida.', 'cache_unknown': 'No se pudo comprobar el estado de la caché local.', 'cloud_slow': 'Respuesta lenta de la nube; vistas previas, recuentos y límites de velocidad pueden añadir demoras.', 'validate_all': 'Validar cuentas', 'validation_note': 'La lectura comprueba solo las cuentas configuradas. Los proveedores sin resultado necesitan una cuenta. Las pruebas de escritura y reconexión requieren confirmación independiente. Leer correctamente no valida subidas, doble autenticación, renovación ni recuperación tras cortes.', 'validation_read': 'Lectura raíz', 'validation_time': 'Tiempo de respuesta', 'validation_unchecked': 'Sin comprobar / sin resultado de cuenta', 'validation_write': 'Probar escritura', 'validation_reconnect': 'Probar reconexión', 'validation_guide': 'Guía de validación', 'validation_confirm': 'La prueba requiere confirmación explícita.', 'validation_write_confirm': '¿Crear un pequeño archivo de prueba en esta cuenta y verificar su contenido directamente desde la nube? El archivo se conservará para que puedas inspeccionarlo o borrarlo. La cuenta debe ser un montaje propio en lectura/escritura y sin subidas pendientes.', 'validation_reconnect_confirm': '¿Desmontar y volver a conectar esta cuenta seleccionada? Las subidas pendientes o los archivos abiertos bloquearán la operación. Las demás cuentas no se reiniciarán.', 'validation_write_requires': 'Conecta esta cuenta como montaje propio en lectura/escritura y termina primero las subidas pendientes.', 'validation_write_ok': 'Contenido de prueba verificado directamente desde la nube. El archivo de prueba se conserva.', 'validation_timeout': 'La prueba no terminó a tiempo. Conserva el archivo y la caché pendiente; revisa Transferencias.', 'validation_error': 'No se pudo verificar la prueba. Revisa acceso, estado de las subidas y diagnóstico local. Conserva los datos pendientes.', 'validation_finished': 'Comprobaciones de lectura terminadas. Revisa cada cuenta; las canceladas y las ausentes quedan sin verificar.', 'validation_file': 'Archivo de prueba', 'validation_reconnect_ok': 'Montaje propio reconectado. La integridad de archivos y la recuperación tras cortes son pruebas separadas.', 'acceptance_steps': 'Para cada proveedor:\n1. Configura una cuenta de prueba y comprueba la lectura raíz.\n2. Conecta en solo lectura y confirma que no permite escribir.\n3. Activa lectura/escritura explícitamente y pulsa Probar escritura; inspecciona el archivo conservado desde la web del proveedor.\n4. Cierra los archivos y pulsa Probar reconexión; comprueba de nuevo el archivo.\n5. Prueba manualmente doble autenticación y renovación de credenciales con la misma cuenta.\n6. Prueba un corte con datos desechables; verifica que las subidas pendientes bloquean desmontar y se recuperan al volver la red.\n7. Compara la cuota con el proveedor.\nEstas comprobaciones del titular no se marcan automáticamente como superadas.'})

TEXT['en'].update({'browse_measure': 'Measure browsing', 'browse_result': 'Folder listing: {listing} · Space query: {space}', 'browse_note': 'These read-only checks are limited to 10 seconds each. — means unavailable or timed out. They do not measure previews or folder-content counting. A fast listing with slow Dolphin suggests extra file-manager queries; disable previews and folder-size counting to compare.'})

TEXT['es'].update({'browse_measure': 'Medir navegación', 'browse_result': 'Listado de carpeta: {listing} · Consulta de espacio: {space}', 'browse_note': 'Estas lecturas tienen un límite de 10 segundos cada una. — indica que no se pudo medir o agotó el tiempo. No miden vistas previas ni recuentos internos. Si el listado es rápido y Dolphin sigue lento, prueba sin vistas previas ni cálculo de tamaño de carpetas.'})
