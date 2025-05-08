# HiDrive MSI Resigner

This Python script re-signs a given `.msi` installer for **IONOS HiDrive Next** by extracting its contents using the **WiX Toolset**, individually signing key binaries (EXEs and DLLs), and reassembling the installer. It is used to sign the msi delivered by the Nextcloud Customization Service (CS) with a valid IONOS certificate.
The resigning workflow is based on the client-building process used by the CS itself (https://github.com/nextcloud/client-building).

---

## 🛠 Features

* Decompiles the MSI using WiX `dark.exe`
* Finds and signs embedded binaries (.dll/.exe)
* Recompiles the installer using WiX `candle.exe` and `light.exe`
* Signs the final MSI using `signtool.exe`
* Verbose mode for debugging and inspection

---

## 🧾 Requirements

* **Python 3.6+**
* **WiX Toolset** installed and accessible via `--wix-path` or `WIX` environment variable
* **signtool.exe** from the Windows SDK
* A valid **code signing certificate (.pfx)**

Additionally, this script calls two helper scripts:

* `sign-file.py` — Script that wraps the actual signing process
* `fix-wxs.py` — Script that repairs `*.wxs` files post-extraction (e.g., path corrections)

---

## 📦 Usage

#### Minimal Example Usage

```bash
python resign-msi.py "path/to/installer.msi" \
  --cert-file "path/to/cert.pfx" \
  --cert-password "yourPassword" \
  --base-dir "path/to/temp" \
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
| `--app-name`      | App name used to identify and sign relevant files   |
| `--wix-path`      | Path to the WiX Toolset (or set `WIX` env variable) |
| `--v`             | Enable verbose output                               |

---

## 🔍 What Gets Signed

The script looks for the following files inside the MSI to re-sign:

### Exact matches:

* `NCContextMenu.dll`
* `NCOverlays.dll`
* `IONOS_HiDrive_Next.exe`
* `IONOS_HiDrive_Nextcmd.exe`
* `IONOS_HiDrive_Nextsync.dll`
* `IONOS_HiDrive_Next_csync.dll`

*(Dynamically derived from the app name)*

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
* No cleanup is performed
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

Sets `Advertise="no"` on `<Shortcut>` elements with `Id="Desktop"` and `Id="StartMenu"`.

* 🛠 Why: The compiliation with light fails otherwise.
* ✅ Result: Shortcuts are now always created correctly regardless of context.

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

Let me know if you'd like a single combined `README.md` that includes both `resign-msi.py` and `fix-wxs.py`.


