# Interface

The top toolbar contains **New connection**, **Refresh connections** and
**Diagnostics**, plus a manual **Check for updates** action. Provider and access mode for new connections are selected in a
compact row. Google Drive and OneDrive registration still opens the browser first.

Select an account and use **Connect**, **Disconnect** or **Open in Dolphin**.
The **Account** menu contains settings, reauthorization and connection removal.
Right-clicking a row selects that account before opening its menu. Unknown account
state keeps actions disabled until the query completes. Existing confirmations,
pending-upload protection and external-mount guards remain active.

**Transfers** expands or collapses the transfer table and progress bar. It starts
collapsed; folding it does not stop monitoring. A summary remains visible beside
the primary actions. Authorization controls appear only during authorization.

The language selector offers **Castellano, English, Français and Deutsch**.
Changing language immediately updates the main window, table headings, account
menu, tray actions, quota labels and future notifications/dialogs. The choice is
saved for the next launch. Account selection, access modes and action guards are
preserved, including while a background operation is busy.

The interface uses native Qt widgets. Platform-owned file pickers, Dolphin and
external browsers may follow their own desktop language. Application messages,
diagnostic reports and standard confirmation buttons use the selected language.

Implementation is in `app.py`; catalogs and persistence are in `i18n.py` and
`messages*.py`. `account_list.py` uses the mount-folder column as the flexible
account column and the filename column for transfers. Qt tests cover selection,
menus, OAuth controls, collapse behavior and language switching.
