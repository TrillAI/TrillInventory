# Trill Inventory 1.16 — Live viewing & editing

## Connect once
1. Install the update over the existing app. Do not uninstall if you want to keep local inventory.
2. Connect the phone and viewing device to the same trusted private Wi-Fi network.
3. On the phone, tap **Connect a viewing device** on the home screen, or **Menu → Browser access → Start hosting**.
4. Scan the QR code using the viewing device's camera. It opens the dashboard and supplies the pairing credential automatically. On a computer without a QR scanner, open the displayed address and enter the **six-digit connection code**.
5. After successful validation, that browser saves a strong credential. It reconnects without another code at the same address, including after restarting the phone server.
6. Close the phone's Browser access panel to start scanning. Keep Trill in the foreground. Hosting keeps the screen awake, but switching apps, locking the phone, Wi-Fi changes and Android power management can interrupt it.

Codes and QR pairing links expire after 10 minutes. Tap **New 10-minute code / QR** to renew them. Pairing is rate-limited after repeated attempts. Up to 32 browsers can be remembered.

Browser storage must be allowed. Clearing website data, using private browsing, changing browsers or a change to the phone's IP address may require pairing again. A stable router-assigned phone IP avoids address changes.

## Live dashboard
- **Inventory:** search, low-stock filter, list/grid layout, product pictures when available, and edit stock/prices. Edits set the total stock count, not an increment.
- **Insights:** category stock bars, recorded additions across seven rolling 24-hour periods, and a 24-hour activity wave. Charts use the latest 100 history entries; they are not sales or profit reports.
- **Activity:** the latest recorded additions.
- **Live scan:** the most recent accepted scan, barcode, identity if known, picture if available, count and price. A nonmodal notification appears on new scans in other tabs. Unknown barcodes stay labeled unknown until identified/saved. Notifications do not interrupt an open editor.

The old five-second polling delay is replaced by long-poll change notifications. Accepted scans publish immediately; other changes are checked every half-second while hosting. Latency still depends on Wi-Fi, browser scheduling and the phone. Up to four viewers receive live notifications simultaneously; extra viewers can use manual Refresh.

## Cigarette stock
On an identified cigarette's details page, use **Set up pack / carton details**. Confirm whether its exact barcode represents one pack or one carton, the printed packs-per-carton count, and optionally cigarettes per pack. Existing stock and prices are **not** silently converted.

For pack-based records, **Select 1 carton** sets the pending addition to the confirmed number of packs. The page shows full-carton equivalents and loose packs. Carton records show pack equivalents. Pack and carton barcodes remain separate; there is no inferred SKU link. Fast scan always adds exactly **one saved inventory unit** per accepted scan.

Identification and photo coverage depend on public databases; brand/variant, menthol, length and pack/carton mismatches still require package verification. No guessed local shelf prices are introduced.

## Security and reconnecting
This is private-LAN **HTTP, not encrypted HTTPS**. Any paired device can view and edit inventory. Do not use untrusted/public Wi-Fi or forward port 8765 to the internet. QR links and codes are credentials; do not share screenshots of them.

- **Stop hosting** shuts down access but preserves trusted-device credentials.
- **Forget all remembered devices** on the phone revokes all saved browser credentials and rotates the pairing code/QR.
- **Forget this browser** removes the credential from that browser. To revoke copies of that credential, use the phone's all-device revocation.
- If disconnected, keep Trill open, check Wi-Fi and reopen the current address. The browser retries live connections. Refresh before repeating an edit that timed out.

Animations can be disabled in phone settings or using **Motion on/off** in the dashboard. System reduced-motion preferences are also respected. The decorative, no-fail platform-running loop never covers the live camera.

Validation: automated JS, Chromium touch/browser, native Java socket and QR pixel-decode tests. No physical Android camera, Wi-Fi or OS QR-scanner testing was performed.
