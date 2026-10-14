"""French UI and diagnostics catalog."""
MESSAGES = {
 'title':'Drive Manager','refresh':'Actualiser les connexions','mount':'Connecter','unmount':'Déconnecter',
 'open':'Ouvrir dans Dolphin','quit':"Quitter l’application",'oauth_open':"Ouvrir le navigateur d’autorisation",
 'oauth_port':"Une autre autorisation utilise le port 53682. Fermez-la ou annulez-la, puis réessayez.",
 'oauth_server':"Impossible de démarrer le serveur local d’autorisation.",
 'onedrive_error':"Impossible de configurer OneDrive. Vérifiez les autorisations Microsoft et le lecteur choisi.",
 'choose_drive':'Choisissez votre lecteur OneDrive','first_transfer':'Premier transfert','queued_label':'En attente',
 'uploading_label':'Envoi','transfers':'Transferts','uploading':'Envoi des modifications','queued':"En attente d’envoi",
 'transferring':'Transfert de fichiers','idle':'File vide · Connexion au cloud non vérifiée',
 'network_retry':'Erreur réseau · Nouvelle tentative de transfert','auth_required':"L’authentification requiert votre attention",
 'transfer_error':'Erreur de transfert · Des modifications restent en attente','monitor_unknown':'Impossible de vérifier la synchronisation',
 'unmonitored':'Montage local · Synchronisation non surveillée','provider_column':'Fournisseur','account':'Compte',
 'status':'État','access':'Accès','mode':'Mode des nouvelles connexions','mode_ro':'Lecture seule','mode_rw':'Lecture/écriture',
 'mounted_rw':'Monté (lecture/écriture)','sync_pending':'Modifications en cours ou en attente d’envoi',
 'sync_unknown':"Impossible de vérifier l’état des envois",'sync_clean':"File d’envoi vide",
 'uploads_pending':"Des modifications restent en attente. Attendez les envois ou reconnectez en lecture/écriture pour les récupérer.",
 'uploads_unknown':"Impossible de vérifier les modifications en attente. La déconnexion et la suppression sont bloquées.",
 'files_open':'Fermez les fichiers et les fenêtres Dolphin de ce lecteur avant de le déconnecter.',
 'needs_write_auth':"Ce compte a été autorisé en lecture. Activez la lecture/écriture dans ses paramètres pour autoriser cet accès.",
 'write_note':"La lecture/écriture modifie les fichiers du cloud. Google/Microsoft peut demander une autorisation dans votre navigateur.",
 'provider':'Fournisseur de la nouvelle connexion','email':'Adresse e-mail','password':'Mot de passe',
 'twofa':'Code à deux facteurs Internxt','internxt_error':"Échec de connexion à Internxt. Vérifiez les identifiants, le code à deux facteurs et la compatibilité de l’offre.",
 'wallet_error':'Déverrouillez ou créez le portefeuille KDE nommé kdewallet, puis réessayez.',
 'internxt_wait':'Connexion à Internxt. Déverrouillez KWallet si demandé.',
 'name_error':'Utilisez un nom unique commençant par une lettre, avec uniquement lettres, chiffres, tirets ou traits de soulignement.',
 'folder_error':'Choisissez un dossier vide et distinct dans votre dossier personnel, sans lien symbolique.',
 'browser_error':"Impossible d’ouvrir le navigateur. Vérifiez le navigateur par défaut et réessayez avec le bouton.",
 'add':'Nouvelle connexion','cancel_oauth':"Annuler l’autorisation",'name':'Nom du compte',
 'oauth_note':'Compte authentifié. Choisissez son nom et un dossier vide.',
 'auth_wait':'Terminez l’autorisation dans votre navigateur (10 minutes maximum).',
 'auth_error':"Impossible d’ajouter le compte. Vérifiez le nom unique et le dossier vide et distinct ; l’autorisation a peut-être été annulée.",
 'automount':'Monter ce compte à la connexion','settings':'Paramètres du compte','path':'Dossier de montage',
 'cache_size':'Taille cible du cache (GiB)','cache_age':'Conserver le cache inutilisé (heures)','choose':'Choisir un dossier',
 'prefs_note':'Appliqué au prochain montage. La taille du cache est une cible de nettoyage.',
 'prefs_error':"Impossible d’enregistrer. Choisissez un dossier vide dans votre dossier personnel, sans lien ni chevauchement entre comptes.",
 'note':'Comptes indépendants · Mode d’accès par compte','confirm':'Déconnecter ce compte ? Les fichiers ouverts peuvent cesser de fonctionner.',
 'disable_auto':'Désactiver aussi le montage à la connexion','delete':'Supprimer la connexion',
 'delete_own':'Supprimer {name} ? Son montage sera déconnecté et ses identifiants enregistrés supprimés. Les fichiers du cloud sont conservés.',
 'delete_external':'{name} appartient à la configuration Rclone existante. Sa suppression modifie cette configuration et affecte les autres outils. Les fichiers du cloud sont conservés.',
 'delete_error':'Suppression impossible : déconnectez d’abord les montages externes ou occupés. Vérifiez l’accès à la configuration.',
 'external_origin':'Connexion Rclone existante','app_origin':'Compte Drive Manager','error':'Échec de l’opération',
 'empty':'Aucune connexion trouvée','busy':'Traitement…','mounted':'Monté (lecture seule)',
 'external':'Montage/service externe','starting':'Démarrage / reconnexion','unmounted':'Démonté','failed':'Échec du montage',
 'capacity':'Espace','quota_refresh':'Actualiser l’espace','quota_loading':'Consultation de l’espace…',
 'quota_unknown':'Espace : non disponible','quota_used':'Utilisé','quota_free':'Disponible','quota_total':'Total',
 'quota_other':'Autres services','quota_trash':'Corbeille','quota_low':'Peu d’espace disponible',
 'notifications':'Notifications du bureau','notification_settings_error':'Impossible d’enregistrer le choix des notifications.',
 'uploads_done':'La file d’envoi observée est maintenant vide.',
 'notice_auth':'L’authentification requiert votre attention. Ouvrez l’application et réautorisez ce compte lorsque cela est sûr.',
 'notice_error':'Un transfert a échoué. Conservez la connexion et le cache tant que des modifications restent en attente.',
 'file_name':'Fichier','account_menu':'Compte','diagnostics':'Diagnostic','copy_report':'Copier le rapport','close_report':'Fermer',
 'upgrade_confirm':"Autoriser cette connexion à modifier vos fichiers du cloud ? Le navigateur s’ouvrira pour autoriser la lecture/écriture. Connectez-vous au MÊME compte. Annuler conserve le mode actuel.",
 'reauth':'Réautoriser le compte',
 'reauth_confirm':'Connectez-vous au MÊME compte que cette connexion. Son dossier, son cache et ses paramètres seront conservés. Elle doit être déconnectée et sans envoi en attente. Continuer ?',
 'reauth_error':"Impossible de renouveler l’autorisation. Utilisez un compte Google Drive, OneDrive ou Dropbox créé par cette application, déconnecté et sans identifiants OAuth personnalisés. La connexion initiale est conservée.",
 'reauth_identity':'Le lecteur OneDrive choisi est différent. La connexion initiale est conservée.',
 'language':'Langue','language_error':'Impossible d’enregistrer la langue. La langue précédente est conservée.'}

DIAGNOSTICS = {
 'title':'Diagnostic de Drive Manager','ok':'Correct','warning':'À vérifier','error':'Erreur',
 'rclone':'Rclone','fuse':'FUSE 3','device':'Périphérique FUSE','systemd_run':'systemd-run','systemd':'systemd utilisateur',
 'dolphin':'Dolphin','fuser':'Protection des fichiers ouverts','wallet':'KWallet (Internxt)',
 'connection':'Connexion sélectionnée','uploads':'Envois en attente','installed':'Disponible.',
 'missing_rclone':'Installez rclone (version 1.73 ou ultérieure).','old_rclone':'Mettez rclone à jour vers la version 1.73 ou ultérieure.',
 'missing_fuse':'Installez fuse3.','missing_systemd_run':'Installez systemd.',
 'missing_dolphin':'Installez dolphin pour ouvrir les dossiers.','missing_fuser':'Installez psmisc pour protéger les fichiers ouverts lors de la déconnexion.',
 'missing_wallet':'Installez kf6-kwallet pour utiliser Internxt.',
 'probe_failed':'Vérification impossible. Le composant peut être occupé ou le délai a été dépassé.',
 'manager_unavailable':'Impossible d’accéder à systemd utilisateur. Lancez l’application depuis votre session KDE, sans sudo.',
 'device_unavailable':'Impossible d’utiliser /dev/fuse. Vérifiez que FUSE est disponible dans cette session.',
 'no_selection':'Sélectionnez un compte pour vérifier son état local.','mounted':'Montage géré actif.',
 'external':'Montage externe : utilisez son outil d’origine pour le gérer.',
 'starting':'Le montage démarre ou est occupé. Attendez et actualisez le diagnostic.',
 'unmounted':'Compte déconnecté.','failed':'Le montage a échoué. Vérifiez les dépendances et reconnectez.',
 'unknown':'État non vérifié. Actualisez les connexions et réessayez.',
 'pending':'Des modifications restent en attente. Attendez les envois ; conservez la connexion et son cache.',
 'clean':'Aucune modification en attente détectée dans le cache d’écriture.',
 'unmonitored':'Montage externe : sa file d’envoi ne peut pas être vérifiée.',
 'footer':"Vérifications locales : accès Internet, autorisations OAuth et disponibilité du cloud non vérifiés.\nAucun jeton, mot de passe, e-mail, nom de compte, chemin personnel ou journal.\nAucune modification de configuration ni démarrage ou arrêt de service."}

MESSAGES.update({'updates': 'Rechercher des mises à jour',
 'update_checking': 'Recherche de mises à jour…',
 'update_installed': 'Version installée',
 'update_latest': 'Dernière version stable',
 'update_available': 'Une mise à jour est disponible. Téléchargez le RPM et installez-le '
                     'manuellement.',
 'update_current': 'Vous utilisez la dernière version stable publiée.',
 'update_ahead': 'La version installée est plus récente que la dernière version stable publiée.',
 'update_error': 'Impossible de vérifier les mises à jour. Vérifiez votre connexion Internet et '
                 'réessayez plus tard.',
 'update_rate_limit': 'GitHub limite temporairement les requêtes. Réessayez plus tard.',
 'update_rpm_missing': 'Aucun RPM compatible avec Fedora 44 n’est disponible. Ouvrez la page de la '
                       'version pour consulter ses fichiers.',
 'update_open_rpm': 'Télécharger le RPM',
 'update_open_release': 'Ouvrir la page de la version',
 'update_open_error': 'Impossible d’ouvrir le navigateur par défaut.',
 'update_manual': 'L’installation est manuelle. Cette vérification ne télécharge ni n’exécute de '
                  'logiciel, ne change pas les identifiants et n’interrompt pas les montages ou '
                  'les envois.'})

MESSAGES.update({'username': 'Nom d’utilisateur', 'webdav_url': 'URL WebDAV (HTTPS)', 'app_password': 'Mot de passe d’application', 'optional_2fa': 'Code de double authentification (facultatif)', 'mailbox_password': 'Mot de passe de la boîte mail (facultatif)', 'nextcloud_note': 'Copiez l’adresse WebDAV des paramètres Fichiers de Nextcloud. Créez un mot de passe d’application dans les paramètres de sécurité de Nextcloud.', 'proton_note': 'Prise en charge expérimentale de Rclone. Connectez-vous d’abord à Proton Drive sur le Web au moins une fois. Si nécessaire, saisissez un code de double authentification actuel. Le mot de passe de la boîte mail concerne uniquement les comptes à deux mots de passe.', 'credentials_wait': 'Vérification sécurisée des identifiants…', 'credentials_error': 'Échec de l’authentification. Vérifiez les identifiants, le code, la disponibilité du serveur et la compatibilité avec Rclone.', 'webdav_url_error': 'Saisissez une URL WebDAV HTTPS valide sans identifiants, paramètres ni fragment.'})

MESSAGES.update({'check_connection': 'Vérifier la connexion', 'connection_checking': 'Vérification de la lecture du dossier racine…', 'connection_ok': 'Dossier racine accessible. Écriture et fin des envois non vérifiées.', 'connection_auth': 'Échec de l’authentification. Renouvelez l’autorisation ou vérifiez vos identifiants.', 'connection_permission': 'Lecture refusée. Vérifiez les droits du compte sur le serveur.', 'connection_network': 'Échec de la requête réseau. Vérifiez la connexion et la disponibilité du serveur.', 'connection_rate': 'Limite de requêtes atteinte. Attendez avant de réessayer.', 'connection_timeout': 'Délai de vérification dépassé. Le fournisseur peut être lent ; cela ne prouve pas qu’il est hors ligne.', 'connection_error': 'Accès non vérifié. Vérifiez la compatibilité et la configuration du compte.', 'connection_wallet': 'Impossible de déverrouiller la configuration privée. Vérifiez KDE Wallet.', 'connection_locked': 'Les configurations externes chiffrées nécessitent leur méthode d’authentification d’origine.', 'connection_cancelled': 'Vérification annulée.', 'connection_elapsed': '{seconds:.1f} s'})

MESSAGES['connection_last']='Dernière vérification'

MESSAGES.update({'renew_credentials': 'Renouveler les identifiants', 'credential_confirm': 'Utilisez le MÊME compte et serveur. La connexion doit être démontée et sans envoi en attente. Dossier, paramètres et cache seront conservés. Remplacer les identifiants ?', 'credential_identity': 'Le nom d’utilisateur ou le serveur Nextcloud diffère de la connexion initiale. Les identifiants précédents sont conservés.', 'credential_custom': 'Les configurations avec jeton bearer ou secret OTP personnalisé nécessitent leur méthode initiale. Les identifiants précédents sont conservés.', 'credential_renew_error': 'Impossible de renouveler les identifiants. Utilisez une connexion chiffrée créée par cette application, démontée et sans envoi en attente. Les identifiants précédents sont conservés.'})

MESSAGES.update({'tools': 'Outils', 'setup_guide': 'Guide de démarrage', 'export_settings': 'Exporter les paramètres', 'import_settings': 'Importer les paramètres', 'setup_steps': '1. Vérifiez les dépendances locales. Ce guide n’installe aucun logiciel.\n2. Choisissez un fournisseur et créez le compte en lecture seule.\n3. Choisissez un dossier vide, connectez-le et ouvrez-le dans Dolphin. Activez l’écriture seulement si nécessaire.', 'setup_finish': 'Terminer le guide', 'export_done': 'Paramètres de {count} comptes exportés. Aucun identifiant ni contenu du cache inclus.', 'import_note': 'Vérifiez dossiers, accès, montage à la connexion et limites de débit. Les comptes doivent déjà exister ici. Enregistrer applique les paramètres aux comptes démontés sans modifications locales en attente. Écriture et montage automatique prennent effet à la prochaine connexion.', 'portable_error': 'Fichier non traité. Vérifiez format, comptes/fournisseurs correspondants, dossiers vides séparés, autorisation d’écriture et droits du fichier. Aucun identifiant importé.', 'portable_busy': 'Démontez les comptes concernés et terminez les envois avant l’importation.', 'upload_limit': 'Limite d’envoi', 'download_limit': 'Limite de téléchargement', 'unlimited': 'Illimité', 'cache_health': 'Cache local : disque libre {free} · Fichiers locaux en attente {pending}', 'cache_low': 'Espace disque local faible. Conservez les fichiers en attente et libérez de l’espace hors du cache d’envoi.', 'cache_unknown': 'État du cache local non vérifié.', 'cloud_slow': 'Réponse lente du fournisseur ; aperçus, comptage et limites de débit peuvent ajouter des délais.', 'validate_all': 'Valider les comptes', 'validation_note': 'Les lectures vérifient uniquement les comptes configurés. Les fournisseurs sans résultat nécessitent un compte. Écriture et reconnexion demandent une confirmation séparée. Une lecture réussie ne valide pas les envois, la 2FA, le renouvellement ou la reprise après panne.', 'validation_read': 'Lecture racine', 'validation_time': 'Temps de réponse', 'validation_unchecked': 'Non vérifié / aucun résultat', 'validation_write': 'Tester l’écriture', 'validation_reconnect': 'Tester la reconnexion', 'validation_guide': 'Guide de validation', 'validation_confirm': 'Confirmation explicite nécessaire.', 'validation_write_confirm': 'Créer un petit fichier de test et vérifier son contenu directement depuis le cloud ? Le fichier reste disponible pour inspection ou suppression manuelle. Le compte doit être monté par l’application en lecture/écriture, sans envoi en attente.', 'validation_reconnect_confirm': 'Démonter et reconnecter ce compte sélectionné ? Les envois en attente ou fichiers ouverts bloquent l’opération. Les autres comptes ne redémarrent pas.', 'validation_write_requires': 'Montez ce compte avec l’application en lecture/écriture et terminez les envois.', 'validation_write_ok': 'Contenu du test vérifié directement depuis le cloud. Le fichier de test est conservé.', 'validation_timeout': 'Test non terminé dans le délai. Conservez le fichier et le cache en attente ; consultez Transferts.', 'validation_error': 'Test non vérifié. Vérifiez accès, envois et diagnostic local. Conservez les données en attente.', 'validation_finished': 'Lectures terminées. Vérifiez chaque compte ; les comptes absents ou annulés restent non vérifiés.', 'validation_file': 'Fichier de test', 'validation_reconnect_ok': 'Montage reconnecté. L’intégrité et la reprise après panne restent des vérifications séparées.', 'acceptance_steps': 'Pour chaque fournisseur :\n1. Configurez un compte de test et vérifiez la lecture racine.\n2. Montez en lecture seule et vérifiez le refus d’écriture.\n3. Activez explicitement l’écriture et testez-la ; inspectez le fichier conservé sur le site du fournisseur.\n4. Fermez les fichiers, testez la reconnexion et relisez le fichier.\n5. Vérifiez manuellement la 2FA et le renouvellement avec le même compte.\n6. Simulez une panne avec des données jetables ; vérifiez la protection des envois et leur reprise.\n7. Comparez le quota au fournisseur.\nCes vérifications du titulaire ne sont pas automatiquement déclarées réussies.'})

MESSAGES.update({'browse_measure': 'Mesurer la navigation', 'browse_result': 'Liste du dossier : {listing} · Espace disque : {space}', 'browse_note': 'Lectures limitées à 10 secondes chacune. — signifie indisponible ou délai dépassé. Aperçus et comptage ne sont pas mesurés. Si la liste est rapide mais Dolphin lent, comparez sans aperçus ni calcul de taille des dossiers.'})

DIAGNOSTICS.update({'wallet': 'KWallet (comptes chiffrés)', 'missing_wallet': 'Installez kf6-kwallet pour Internxt, Nextcloud et Proton Drive.'})

MESSAGES.update({'operation_cancel': 'Annuler la vérification', 'operation_cancelling': 'Annulation… En attente de la fin sécurisée de l’opération. Une reconnexion déjà commencée tentera le montage.', 'operation_elapsed': 'Temps écoulé : {seconds} s', 'operation_status': 'Vérification du montage…', 'operation_listing': 'Lecture du dossier…', 'operation_space': 'Consultation de l’espace du système de fichiers…', 'operation_finished': 'Opération terminée. Consultez le résultat détaillé.'})

MESSAGES['operation_close']='Fermer'

MESSAGES.update({'browse_incomplete': 'Mesure incomplète : une requête a échoué ou dépassé sa limite. Vérifiez le montage et la connexion, puis réessayez. Cela ne prouve pas une déconnexion du cloud.', 'browse_both_slow': 'Les deux requêtes ont pris au moins 2 secondes. Comparez avec une vérification de connexion, examinez les envois en attente et réessayez plus tard. Évitez les actualisations répétées pendant une requête.', 'browse_listing_slow': 'La lecture du dossier a pris au moins 2 secondes. Comparez avec une vérification de connexion. Taille du dossier, cache ou latence distante peuvent contribuer ; ces durées ne les distinguent pas.', 'browse_space_slow': 'La requête d’espace a pris au moins 2 secondes et la lecture du dossier était plus rapide. Les requêtes d’espace ou de quota peuvent contribuer. Comparez séparément la vérification du quota ; ne modifiez pas le montage sur ce seul résultat.', 'browse_fast': 'Les deux requêtes ont pris moins de 2 secondes. Si Dolphin se bloque encore, comparez sans aperçu ni calcul automatique de taille des dossiers, si votre version le propose. Essayez un petit dossier. Une racine rapide ne garantit pas des fichiers ou sous-dossiers rapides.', 'browse_scope': 'Conseils avec un seuil de 2 secondes et une limite de 10 secondes par requête. Seule la racine montée est mesurée, pas Dolphin, les miniatures, les contenus ni la fin des envois. Le cache peut accélérer le résultat. Aucun réglage Dolphin, identifiant ou montage modifié.'})

MESSAGES.update({'open': 'Ouvrir le dossier', 'import_select_note': 'Choisissez les comptes à importer et modifiez leurs dossiers. Les comptes décochés restent inchangés. Enregistrer applique le mode, montage à la connexion et limites affichés uniquement aux comptes déconnectés avec cache propre et dossiers vides sûrs.'})

MESSAGES.update({'import_mode': 'Accès importé', 'import_apply': 'Appliquer la sélection', 'import_cancel': 'Annuler'})

DIAGNOSTICS.update({'dolphin': 'Gestionnaire de fichiers par défaut', 'missing_dolphin': 'Installez xdg-utils et configurez un gestionnaire de fichiers par défaut.'})
