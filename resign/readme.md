# HiDrive MSI Resigner

This Python script re-signs a given `.msi` installer for **IONOS HiDrive Next** or **STRATO HiDrive Next** by extracting its contents using the **WiX Toolset**, individually signing key binaries (EXEs and DLLs), and reassembling the installer. It is used to sign the MSI delivered by the Nextcloud Customization Service (CS) with a valid certificate.

The branding (IONOS vs. STRATO) is controlled entirely by the `--app-name` argument — no separate branch or script copy is needed.

The resigning workflow is based on the client-building process used by the CS itself (https://github.com/nextcloud/client-building).

---

## 🛠 Features

* Decompiles the MSI using WiX `dark.exe`
* Finds and signs embedded binaries (.dll/.exe)
* Recompiles the installer using WiX `candle.exe` and `light.exe`
* **Supports IONOS and STRATO branding** — binary names and shortcut targets are derived dynamically from `--app-name`
* **Preserves multilingual MSI support** by copying language transform sub-storages and the SIS Template from the original MSI into the resigned one (prevents Windows Installer error 1624 on non-English systems)
* Signs the final MSI using `signtool.exe`
* Verbose mode for debugging and inspection

---

## 🧾 Requirements

* **Python 3.6+**
* **WiX Toolset** installed and accessible via `--wix-path` or `WIX` environment variable
* **signtool.exe** from the Windows SDK
* A valid **code signing certificate (.pfx)**
* **pywin32** for multilingual MSI support (language transform preservation):
  ```
  pip install pywin32
  ```
  > On Python < 3.13, `msilib` (built-in) is used for the Summary Information Stream. On Python 3.13+, the script falls back to a PowerShell COM call automatically.

Additionally, this script calls two helper scripts:

* `sign-file.py` — Script that wraps the actual signing process
* `fix-wxs.py` — Script that repairs `*.wxs` files post-extraction (e.g., path corrections)

---

## 📦 Usage

### Minimal Example Usage

#### IONOS (default)

```bash
python resign-msi.py "path/to/installer.msi" \
  --cert-file "path/to/cert.pfx" \
  --cert-password "yourPassword" \
  --base-dir "path/to/temp"
```

#### STRATO

```bash
python resign-msi.py "path/to/installer.msi" \
  --cert-file "path/to/cert.pfx" \
  --cert-password "yourPassword" \
  --base-dir "path/to/temp" \
  --app-name "STRATO HiDrive Next"
```

#### Full Example Usage

```bash
python resign-msi.py "path/to/installer.msi" \
  --cert-file "path/to/cert.pfx" \
  --cert-password "yourPassword" \
  --wix-path "C:\Program Files (x86)\WiX Toolset v3.11" \
  --sign-tool "C:\Program Files (x86)\Windows Kits\10\bin\...\signtool.exe" \
  --base-dir "path/to/temp" \
  --app-name "IONOS HiDrive Next" \
  --v
```

---

## 🧩 Options

| Argument          | Description                                         |
| ----------------- | --------------------------------------------------- |
| `input_msi`       | Path to the MSI installer to be resigned            |
| `--cert-file`     | Path to the `.pfx` certificate file                 |
| `--cert-password` | Password for the certificate                        |
| `--base-dir`      | Temporary working directory (default: current dir)  |
| `--sign-tool`     | Path to `signtool.exe` (optional if in PATH)        |
| `--app-name`      | App name controlling branding: `"IONOS HiDrive Next"` (default) or `"STRATO HiDrive Next"`. Determines signed binary names and shortcut targets. |
| `--wix-path`      | Path to the WiX Toolset (or set `WIX` env variable) |
| `--v`             | Enable verbose output                               |

---

## 🔍 What Gets Signed

The script looks for the following files inside the MSI to re-sign:

### Exact matches:

* `NCContextMenu.dll`
* `NCOverlays.dll`
* `<AppName>.exe` — e.g. `IONOS_HiDrive_Next.exe` / `STRATO_HiDrive_Next.exe`
* `<AppName>cmd.exe`
* `<AppName>sync.dll`
* `<AppName>_csync.dll`

The `<AppName>` prefix is derived from `--app-name` with spaces replaced by underscores. Passing `"STRATO HiDrive Next"` automatically resolves to `STRATO_HiDrive_Next.*`.

### Wildcard matches:

* `qt6keychain*.dll`
* `libcrypto-3*.dll`
* `libssl-3*.dll`
* `zlib1*.dll`

---

## 🚧 Notes

* Ensure `sign-file.py` and `fix-wxs.py` are in the same directory or accessible via PATH.
* The script handles temporary file renaming needed for signing binaries embedded under different names.
* All output files (including the new MSI) will be placed in the specified `--base-dir`.
* No cleanup is performed.
* Language transforms are copied from the **original MSI** after relinking, before final signing. Without this step, Windows Installer cannot find the correct language transform on non-English systems and raises error 1624.
* WiX `light.exe` is invoked with `-sval` (suppress validation) to avoid false validation failures when relinking a decompiled MSI.
---

## ✅ Example Output

```
🔧 Beginn to resign installer.msi
🔧 Decompiling installer...
✅ Success: Decompiling installer.msi to WXS and binary files
🔧 Start signing extracted files...
🎯 Found: extracted\bin\IONOS_HiDrive_Next.exe
✅ Successfully signed IONOS_HiDrive_Next.exe
...
🎉 Installer built successfully: installer_resigned.msi
```

---

# fix-wxs.py
## 🛠 What `fix-wxs.py` Repairs — and Why

While re-signing the .msi using the WiX Toolset, we first decompile the installer using dark.exe. However, dark.exe only extracts what is physically stored in the .msi file. This causes several issues with UI-related elements, especially when the installer was originally built using built-in WiX UI dialogs.

These dialogs are pulled in at compile time from WixUIExtension.dll and are not embedded directly in the MSI. As a result, the .wxs output from dark.exe is incomplete and won't compile or function correctly without some manual repairs.

---

## ✅ What the Script Fixes (Specifically)

### 1. **Fixes broken shortcuts**

Sets `Advertise="no"` on `<Shortcut>` elements with `Id="Desktop"` and `Id="StartMenu"`, and sets the `Target` attribute to `[INSTALLDIR]<AppName>.exe` derived from `--app-name`.

* 🛠 Why: The compilation with light fails otherwise, and the shortcut target must match the actual exe name for the selected branding.
* ✅ Result: Shortcuts are now always created correctly regardless of context, for both IONOS and STRATO branding.

---

### 2. **Restores UI assets**

Adds `<WixVariable>` entries for:

* `WixUIBannerBmp`
* `WixUIDialogBmp`

These point to `WixUI_Bmp_Banner` and `WixUI_Bmp_Dialog` binaries in the extracted MSI files.

* ✅ Result: Banner and background images show up correctly again in the UI.

---

### 3. **Rebuilds missing UI behavior (Skipping License Page)**

Adds:

* `<UIRef>`s to include common UI elements like `WixUI_FeatureTree` and `WixUI_ErrorProgressText`

* `<Publish>` entries for:

  * Skipping the license page by jumping from `WelcomeDlg` → `CustomizeDlg`
  * Launching the app from `ExitDialog → Finish`

---

## 🧪 Output

The modified `.wxs` file is saved in-place. It is now fully compatible with `candle.exe` and `light.exe`, making it possible to **rebuild and resign** the MSI correctly.

---