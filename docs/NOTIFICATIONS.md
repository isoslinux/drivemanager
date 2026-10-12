# Desktop notifications

Drive Manager uses Qt tray notifications integrated with KDE. It announces an
observed upload queue becoming empty, authentication requiring attention and
transfer failures. Messages follow the selected application language.

Enable or disable **Desktop notifications** in the window or tray menu. The global
preference is saved atomically in `~/.config/drive-manager/notifications.json` with
0600 permissions. An unreadable preference disables alerts; a failed save preserves
the previous choice. Clicking a notification displays the main window.

Messages identify the connection and use fixed text. They never include filenames,
paths, credentials, tokens or Rclone's raw error. KDE may suppress notifications
with Do Not Disturb or its application notification settings.

## Event policy

- All accounts in the table are monitored while the application runs, including
  while hidden in the tray. No separate notification service is created.
- Queue-empty alerts require previously observed pending uploads on an owned
  read/write mount. Downloads, external mounts and disconnects are not completion.
- Unknown state never announces completion. An empty queue does not independently
  verify connectivity or integrity of every remote file.
- Each error type is announced once per account/incident until recovery is observed.
  Transient network retry does not produce an additional alert.
- Muted events are consumed and are not replayed when alerts are enabled again.
  Deduplication history lasts for the application session.
- Alerts never mount, disconnect, reauthorize or delete accounts. Existing cache
  and credential protection remains in effect.

Low-space alerts also respect the global preference; see [storage](STORAGE.md).
`notifications.py` tracks transitions and private preferences; `app.py` presents
messages on the Qt thread. Tests simulate queues, errors, recovery, multiple
accounts, mute behavior, corrupted preferences, symlinks and failed-save rollback.
Native notification presentation requires a normal KDE-session acceptance check.
