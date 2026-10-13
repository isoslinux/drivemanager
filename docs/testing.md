# Test plan

## Automated checks

From the repository root:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The suite uses temporary directories, synthetic credentials, simulated service
responses and offscreen Qt. Cloud access and active service changes are not part
of normal automated tests.

| Area | Important cases |
| --- | --- |
| Discovery | Supported file-backed providers, invalid metadata and conflicting names |
| Mount policy | Stable identity, empty folders, private snapshots and external ownership rejection |
| Settings | Type/range validation, symlinks, overlapping paths and atomic private writes |
| Accounts | Browser-first staging, cancellation, cleanup and independent account folders |
| OAuth | Valid local links, bounded parsing, no raw error output and real state length |
| Credential renewal | Same account/server, external and mounted rejection, dirty-cache races, failed/cancelled login, retained settings/cache, cleared session tokens and UI confirmation |
| Internxt | Encrypted staging, private Unix requests, two-factor continuation and wallet failures |
| New providers | Dropbox OAuth options and renewal, HTTPS URL validation, encrypted provider metadata, private credential requests, failure/cancellation cleanup and backend mount flags |
| OneDrive | Drive selection, read/write scopes and cancellation |
| Disconnect/removal | Explicit confirmation, external configuration scope and retained cloud files |
| Writable mounts | Queued uploads, unknown statistics, dirty metadata and open-file protection |
| Progress | Current versus historical errors, numeric validation and unknown monitoring state |
| Diagnostics | Missing tools, timeouts, unexpected output, privacy and clipboard contents |
| Notifications | Deduplication, recovery, multiple accounts, silence and preference rollback |
| Quotas | Shared storage, missing/invalid values, isolated refresh, cleanup and stale selections |
| Connectivity | Read-only root access, isolated token refresh, private permissions, cancellation/timeout, bounded diagnostic output, external encrypted configurations and stale selections |
| Updates | Numeric stable versions, safe URLs, response bounds, rate limits, manual browser actions and unchanged account controls |
| Languages | Complete keys/placeholders, private persistence, fallback, standard buttons and live switching |
| Qt | Selection, action guards, dialogs, collapsed transfers and unchanged controls during language switching |

Documentation links and Bash examples are also checked without executing the
installation commands. RPM builds validate packaging and include the source tests.

## Manual KDE acceptance

1. Install the RPM on Fedora 44 KDE and launch it without sudo.
2. Check all four languages, including tray actions, diagnostics, confirmations
   and restarting with a saved language preference.
3. Detect an existing Rclone connection and confirm its credentials remain unchanged.
4. Add separate Google Drive, OneDrive, Dropbox, Nextcloud, Proton Drive and compatible Internxt accounts. Check provider-specific setup in [PROVIDERS.md](PROVIDERS.md).
5. Assign independent empty mount folders; connect and open them in Dolphin.
6. Verify read-only mode, then explicitly authorize and enable read/write access.
7. Upload synthetic disposable files and inspect queued/active/completed state.
8. Confirm pending or unknown uploads block disconnect/removal; verify recovery
   preserves credentials and cache. Never use real important files for destructive tests.
9. Check notifications with KDE's Do Not Disturb mode both enabled and disabled.
10. Compare quota values with the provider and test missing quota support.
11. Verify optional login mounting and that quitting leaves mounts running.
12. Check external mounts remain untouched and removal of an external configuration
    requires separate explicit confirmation.

Do not automate real OAuth consent, mount teardown or deletion of existing user
connections without authorization. Native notifications and real cloud behavior
remain acceptance checks in the account owner's session.

For manual acceptance, select **Account → Check connection** on each provider,
including a disconnected account. Verify successful reads, rejected credentials,
a network outage, cancellation on quit and selection changes during a slow query.
Confirm the original configuration remains unchanged and no mounts are stopped.
An unavailable or slow check must not be displayed as upload completion.

Manually renew one disposable encrypted account for each supported credential
provider. Confirm wrong passwords and changed usernames preserve the old account,
2FA and mailbox passwords work, cached tokens do not mask failed login, and
mount folder/settings/cache remain unchanged. Check cancelled dialogs and wallet
failures. Do not change credentials for an important account merely for a test.
