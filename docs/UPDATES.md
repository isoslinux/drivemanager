# Manual update checks

Select **Check for updates** in the top toolbar. Drive Manager requests the latest
published stable release from the project's public GitHub API endpoint and shows
the installed and available versions. The request is made only when you press the
button; no GitHub account, access token or cloud credentials are needed.

An available update offers **Download RPM** when a matching uploaded Fedora 44
noarch package is present, and **Open release page** for release information.
Both actions open the default browser only after you click them. Installation
remains manual through Discover or `dnf`. The application does not download, execute,
install, restart or change services as part of the version check.

Equal versions report that the installed stable version is current. A newer
installed version is reported separately; no downgrade RPM is offered. Missing RPM
assets leave the release-page action available. Preview/draft releases, malformed
versions and unexpected repository URLs are rejected.

## Responsiveness and privacy

A separate worker handles the public HTTP request. Account actions, quota queries
and transfer monitoring remain independent. Polling stays active while the result
dialog is open. Duplicate clicks cannot start overlapping requests. Labels use the
selected Spanish, English, French or German application language.

The request contains normal public API headers and the application version in its
User-Agent, without credentials or account metadata. HTTPS verification is enabled;
API redirects are rejected, response size is limited to 512 KiB, and network socket
operations have a ten-second timeout. Network and API errors use fixed translated
messages rather than raw response bodies. Rate limits advise trying again later.

Release and download links must belong to the project's repository and match the
validated version and RPM filename. Remote HTML, release notes and API error text
are never rendered as application messages. Browser downloads follow GitHub's
normal download flow; package installation is the user's separate action.

## Validation

`updates.py` validates numeric stable versions, publication flags, asset names and
URLs. Tests cover version ordering, drafts/previews, invalid metadata, missing or
wrong packages, redirects, request bounds, timeouts, HTTP failures and rate limits.
Qt tests verify that a manual background check preserves account controls and that
opening the RPM requires an explicit button click. Dialog layouts are reviewed in
all four languages with synthetic future-version data.

Published public release metadata was also parsed for older, equal and newer
installed versions. This validates metadata handling, not a package installation.

Reference: [GitHub release API](https://docs.github.com/en/rest/releases/releases#get-the-latest-release).
