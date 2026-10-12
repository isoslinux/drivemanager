# Account storage quotas

Selecting a connection starts a background quota query. Available fields are
shown separately: used, free, total, other services and trash. Sizes use binary
units such as GiB and MiB. The capacity bar uses total minus free when available;
otherwise it uses reported used/other storage without inventing a free value or
adding trash twice.

Google quotas may include services such as Gmail and Photos. Other-service usage
is displayed separately when reported by Rclone. Low space means 10% or less of
reported total remaining, or a known free value of zero. Desktop alerts respect
the global preference and do not repeat until recovery is observed. No uploads
are stopped and no data is deleted.

Results are retained in memory for five minutes. **Refresh space** requests fresh
data. Transfers and actions remain responsive during the separate quota query.
An old selection's response cannot replace the newly selected account's display.
Labels and warnings use the selected application language.

Missing support, unavailable fields or a failed query produce **Not available**.
Unknown values do not mean unlimited storage or zero free space. The application
does not traverse every file as a substitute for provider quota information.

## Credentials and limits

Unencrypted configurations are queried through temporary private copies (0600
files in 0700 directories). Possible OAuth refresh remains in that copy, leaving
the source untouched. Temporary copies are removed afterwards. No browser is
opened and no tokens or raw errors are logged.

Encrypted application-created accounts (Internxt) use the private socket of an
active managed mount. If disconnected, quota is unavailable and KWallet is not
opened in the background. External encrypted configurations and linked source
configuration files are not queried in this delivery.

Quota queries are not upload-integrity checks. Provider information may lag.
`quota.py` validates numeric fields and calls `rclone about --json` or private
`operations/about`; the UI uses a separate worker and memory cache. Quota subprocesses
have a twelve-second limit and RC connections use ten seconds.

Tests cover shared quotas, absent/invalid values, preserved source configuration,
temporary cleanup, process bounds, disconnected encrypted accounts and Qt selection
changes. A real synthetic local-backend query was also checked without cloud accounts
or mounts.

References: [rclone about](https://rclone.org/commands/rclone_about/) and
[operations/about](https://rclone.org/rc/#operations-about).
