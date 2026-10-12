# Application languages

The project documentation and development terminology are English. The application
supports four complete catalogs: `es` (Castellano), `en` (English), `fr` (Français)
and `de` (Deutsch).

Use the main-window language selector. Changes apply immediately without restarting
or changing mount state. A saved preference in
`~/.config/drive-manager/language.json` overrides the system locale. The file is
written atomically with 0600 permissions; its application folder uses 0700.
Unsupported locales fall back to English. Invalid preferences fall back to the
system selection without rewriting the invalid file. A save failure keeps the old
language and restores the selector.

## Catalog maintenance

- `src/drive_manager/messages.py`: English and Spanish UI strings.
- `src/drive_manager/messages_fr.py`: French UI and diagnostics.
- `src/drive_manager/messages_de.py`: German UI and diagnostics.
- `src/drive_manager/diagnostics.py`: English/Spanish diagnostic catalog.
- `src/drive_manager/i18n.py`: catalog assembly, preference and Qt button integration.

Keep every key present in all four languages and preserve interpolation fields
such as `{name}`. Do not concatenate translated fragments when sentence structure
matters. Do not translate provider brands, account names, paths, remote identifiers
or technical units. Never put tokens or raw process errors into translations.

Qt's installed `qtbase` catalogs are loaded when available. Built-in translations
cover standard confirmation buttons even without those optional resources.
Platform-owned dialogs and external applications may retain the desktop language.
The application uses Python catalogs rather than requiring compiled `.qm` resources
for its own messages.

Run the full suite with `QT_QPA_PLATFORM=offscreen`. Language tests check key parity,
placeholder parity, diagnostics, private persistence, fallback, symlink rejection,
standard buttons, immediate switching, preserved selection/action guards and rollback.
Review wording and layouts in every language before expanding a catalog.
