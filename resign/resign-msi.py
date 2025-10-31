import subprocess
import argparse
import os
from pathlib import Path
import sys

import xml.etree.ElementTree as ET
import fnmatch

def check_and_resolve_path(path):
    try:
        print(f"🔍 Checking path: {path.resolve(strict=False)}")
        resolved_path = path.resolve(strict=True)
        return resolved_path
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return None

def match_filename(name, pattern, wildcard):
    if wildcard:
        if name and fnmatch.fnmatch(name.lower(), pattern):
            return True
    else:
        if name and name.lower() == pattern.lower():
            return True
    return False

def read_wxs(wxs_file, filename, wildcard=False, first=True):
    try:
        tree = ET.parse(wxs_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading WXS file: {e}", file=sys.stderr)
        return 2

    ns = {'wix': 'http://schemas.microsoft.com/wix/2006/wi'}
    ET.register_namespace('', ns['wix'])

    matches = []
    for file_elem in root.findall(".//wix:File", ns):
        name = file_elem.attrib.get("Name")
        if match_filename(name, filename, wildcard):
            source = file_elem.attrib.get("Source")
            if source:
                matches.append(source)

    if matches:
        if first:
            return matches[0]
        else:
            return matches
    else:
        return None
    
def read_wildcard_name(wxs_file, filename, first=True):
    try:
        tree = ET.parse(wxs_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading WXS file: {e}", file=sys.stderr)
        return 2

    ns = {'wix': 'http://schemas.microsoft.com/wix/2006/wi'}
    ET.register_namespace('', ns['wix'])

    matches = []
    for file_elem in root.findall(".//wix:File", ns):
        name = file_elem.attrib.get("Name")
        if match_filename(name, filename, True):
            matches.append(name)

    if matches:
        if first:
            return matches[0]
        else:
            return matches
    else:
        return None

def rename_file(src, dst):
    """
    Rename a file from src to dst.
    :param src: Original file path
    :param dst: New file path
    """
    try:
        os.rename(src, dst)
        # print(f"✅ Renamed:\n  from: {src}\n  to:   {dst}")
    except FileNotFoundError:
        print(f"❌ File not found: {src}")
    except FileExistsError:
        print(f"❌ Destination file already exists: {dst}")
    except PermissionError:
        print(f"❌ Permission denied when renaming: {src}")
    except Exception as e:
        print(f"❌ Error renaming file: {e}")


def run_command(command, description, verbose=False):
    print(f"🔧 {description}...")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        if verbose:
            print("📥 STDERR:\n" + result.stderr.strip())
            print("📤 STDOUT:\n" + result.stdout.strip())
        sys.exit(result.returncode)
    else:
        print(f"✅ Success: {description}")
        if verbose:
            print(result.stdout.strip())


def preserve_msi_languages(src_msi, dst_msi):
    """
    Copy language transform sub-storages and SIS Template from the original MSI
    into the resigned MSI so that Windows Installer can find the correct language
    transform on non-English systems (prevents error 1624).
    Requires: pip install pywin32
    """
    try:
        import pythoncom
        import win32com.storagecon as sc
    except ImportError:
        print("❌ pywin32 is required for multilingual MSI support: pip install pywin32")
        sys.exit(1)

    # --- Copy Summary Information Stream Template (language ID list) ---
    try:
        import msilib  # built-in on Python < 3.13
        src_db = msilib.OpenDatabase(str(src_msi), msilib.MSIDBOPEN_READONLY)
        template = src_db.GetSummaryInformation(0).GetProperty(7)  # PID_TEMPLATE = 7
        del src_db

        dst_db = msilib.OpenDatabase(str(dst_msi), msilib.MSIDBOPEN_TRANSACT)
        dst_si = dst_db.GetSummaryInformation(1)
        dst_si.SetProperty(7, template)
        dst_si.Persist()
        dst_db.Commit()
        del dst_db
    except ImportError:
        # Python 3.13+ fallback via PowerShell COM
        ps = (
            f'$i=New-Object -ComObject WindowsInstaller.Installer;'
            f'$t=$i.OpenDatabase("{src_msi}",0).SummaryInformation(0).Property(7);'
            f'$d=$i.OpenDatabase("{dst_msi}",1);'
            f'$si=$d.SummaryInformation(1);'
            f'$si.Property(7)=$t;$si.Persist();$d.Commit()'
        )
        r = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"⚠️ Could not copy SIS Template: {r.stderr.strip()}")
        template = "(set via PowerShell)"

    print(f"✅ Copied SIS Template: {template}")

    # --- Copy language transform sub-storages (OLE compound document sub-storages) ---
    src_stg = pythoncom.StgOpenStorage(
        str(src_msi), None, sc.STGM_READ | sc.STGM_SHARE_DENY_WRITE
    )
    dst_stg = pythoncom.StgOpenStorage(
        str(dst_msi), None,
        sc.STGM_READWRITE | sc.STGM_SHARE_EXCLUSIVE | sc.STGM_TRANSACTED
    )

    copied = []
    for stat in src_stg.EnumElements():
        name = stat[0]
        try:
            src_sub = src_stg.OpenStorage(name, None, sc.STGM_READ | sc.STGM_SHARE_EXCLUSIVE)
        except Exception:
            continue  # It's a stream, not a sub-storage — skip
        dst_sub = dst_stg.CreateStorage(
            name,
            sc.STGM_CREATE | sc.STGM_WRITE | sc.STGM_SHARE_EXCLUSIVE,
            0, 0
        )
        src_sub.CopyTo(None, None, dst_sub)
        copied.append(name)

    if copied:
        dst_stg.Commit(0)
        print(f"✅ Copied {len(copied)} language transform(s): {', '.join(copied)}")
    else:
        print("⚠️  No language transforms found in original MSI")


def sign_file(file_path, sign_tool, cert_file, cert_password, app_name):
    sign_result = subprocess.run([
        "python", "sign-file.py",
        file_path,
        "--signtool", sign_tool,
        "--cert-file", cert_file,
        "--cert-password", cert_password,
        "--app-name", app_name
    ], capture_output=True, text=True)
    
    if sign_result.returncode == 0:
        print(f"[OK] ({__file__}) Successfully signed {file_path.name}")
    else:
        print(f"[ERR] ({__file__}) Signing failed for {file_path.name}")
        print(f"[ERR] ({__file__}) STDOUT:\n" + sign_result.stdout.strip())
        print(f"[ERR] ({__file__}) STDERR:\n" + sign_result.stderr.strip())
    return sign_result.returncode

#----------------------------   
#--- Begin ------------------
#----------------------------   

parser = argparse.ArgumentParser(
    description="Resigns the given HiDrive Next .msi file with given certificate using WIX Toolset and SignTool."
)
parser.add_argument("input_msi", help="Path to the .msi file to sign anew")


parser.add_argument("--cert-file", required=True, help="Path to the certificate file")
parser.add_argument("--cert-password", required=True, help="Password for the certificate file")
parser.add_argument(
    "--base-dir", default=".",
    help="Base directory where temporary files are created and the .msi is extracted to (default: current directory)"
)
parser.add_argument(
    "--sign-tool", default="C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.26100.0\\x64\\signtool.exe",
    help="Path to the windows signtool.exe", required=False
)
parser.add_argument(
    "--app-name", default="STRATO HiDrive Next",
    help="Name of app (default: STRATO HiDrive Next)", required=False
)
parser.add_argument(
    "--wix-path", 
    help="Path to WIX Toolset (default: extracted from PATH)", required=False
)

parser.add_argument(
    "--v",  # or use "--verbose" for clarity
    help="Enable verbose output",
    action="store_true"
)

args = parser.parse_args()

# TODO check if fullpath or only filename, combine base-dir if filename

start_msi = Path(args.input_msi)
sign_tool = Path(args.sign_tool)
app_name = str(args.app_name)
app_name_sanitized = app_name.replace(" ", "_")
base_dir = Path(args.base_dir)
cert_file = Path(args.cert_file)

# Check and resolve all paths
start_msi = check_and_resolve_path(start_msi)
if start_msi is None:
    sys.exit(1)
sign_tool = check_and_resolve_path(sign_tool)
if sign_tool is None:
    sys.exit(1)
cert_file = check_and_resolve_path(cert_file)
if cert_file is None:
    sys.exit(1)
base_dir = check_and_resolve_path(base_dir)
if base_dir is None:
    sys.exit(1)


wxs_name = "temp"
wxs_file = base_dir / (wxs_name +".wxs")

extracted_dir = base_dir / "extracted"
if args.v:
    print("🔍 Verbose mode is ON")
    
print(f"🔧 Beginn to resign {start_msi}")

if args.wix_path:
    wix_path = Path(args.wix_path)
else:
    wix_path = os.environ.get("WIX")
    if wix_path:
        print(f"🔧 WIX path is: {wix_path}")
    else:
        print("❌ WIX environment variable not set.")
wix_path = Path(wix_path)
wix_path = check_and_resolve_path(wix_path)
if wix_path is None:
    sys.exit(1)

#----------------------------   
#--- Decompiling-------------
#----------------------------   
dark = wix_path / "bin" / "dark.exe"

run_command([
    str(dark), str(start_msi),
    "-x", str(extracted_dir),
    "-o", str(wxs_file)
], f"Decompiling {start_msi} to WXS and binary files", args.v)

#----------------------------   
#--- Signing ----------------
#----------------------------   
print(f"🔧 Start signing extracted files...")
exact_file_names = [
    "NCContextMenu.dll",
    "NCOverlays.dll",
    app_name_sanitized + ".exe",
    app_name_sanitized + "cmd.exe",
    app_name_sanitized + "sync.dll",
    app_name_sanitized + "_csync.dll",
]

fuzzy_file_names = [
    "qt6keychain*.dll",
    "libcrypto-3*.dll", 
    "libssl-3*.dll", 
    "zlib1*.dll", 
]

for file_name in exact_file_names:
    
    print(f"\t🔍 Looking for: {file_name}")

    search_result = read_wxs(wxs_file, file_name, first=True)

    if search_result is None:
        print("\t❌ No match found.")
        continue        
    else:
        source_path = Path(search_result)
        print(f"\t🎯 Found: {source_path}, {file_name}")  
        
    renamed_file_path = source_path.parent / file_name    
    rename_file(source_path, renamed_file_path)

    sign_res = sign_file(renamed_file_path, sign_tool, str(cert_file), args.cert_password, app_name)
    if sign_res != 0:
        sys.exit(sign_res)
    
    rename_file(renamed_file_path, source_path)
    
for file_name in fuzzy_file_names:
    
    print(f"\t🔍 Looking for: {file_name}")
    search_result = read_wxs(wxs_file, file_name, first=True, wildcard=True)
    
    if search_result is None:
        print("\t❌ No match found.")
        continue
    else:
        source_path = Path(search_result)
        name = read_wildcard_name(wxs_file, file_name, True)
        if name is not None:
            print(f"\t🎯 Found: {source_path}, {name}")  
        else:
            print(f"\t❌ No match found.")
            continue
            

    renamed_file_path = source_path.parent / name    
    rename_file(source_path, renamed_file_path)

    sign_res = sign_file(renamed_file_path, sign_tool, str(cert_file), args.cert_password, app_name)
    if sign_res != 0:
        sys.exit(sign_res)
    rename_file(renamed_file_path, source_path)

#----------------------------   
#--- Recompiling-------------
#----------------------------  
print(f"🔧 Start repairing .wxs file...")
    
wixobj_file = base_dir / (wxs_name +".wixobj")
msi_file = base_dir / start_msi.name.replace(".msi", "_resigned.msi")

fix_result = subprocess.run([
    "python", "fix-wxs.py",
    wxs_file,
    "--extracted-path", str(extracted_dir),
], capture_output=True, text=True)

if fix_result.returncode == 0:
    print(f"[OK] ({__file__}) Successfully repaired {wxs_file.name}")
else:
    print(f"[ERR] ({__file__}) Repair failed for {wxs_file.name}")
    print(f"[ERR] ({__file__}) STDOUT:\n" + fix_result.stdout.strip())
    print(f"[ERR] ({__file__}) STDERR:\n" + fix_result.stderr.strip())
    sys.exit(fix_result.returncode)

candle = wix_path / "bin" / "candle.exe"

# Step 1: Compile .wxs to .wixobj using candle.exe
run_command(
    [str(candle), 
    "-ext", "WixUtilExtension",
    "-dcodepage=1252",
    "-o", wixobj_file,
     str(wxs_file),
    ]
    , "Compiling WXS to WIXOBJ", args.v)

# Step 2: Link .wixobj to .msi using light.exe
light = wix_path / "bin" / "light.exe"

run_command([
    str(light), str(wixobj_file),
    "-ext", "WixUtilExtension",
    "-ext", "WixUIExtension",
    "-sval",
    "-o", str(msi_file)
], "Linking WIXOBJ to MSI", args.v)

# Preserve language transforms from the original MSI
print(f"🔧 Preserving language transforms from original MSI...")
preserve_msi_languages(start_msi, msi_file)

# Signing the new .msi file
print(f"🔧 Start signing new .msi file...")

sign_res = sign_file(
    msi_file,
    sign_tool,
    str(cert_file),
    args.cert_password,
    app_name
)

if sign_res != 0:
    sys.exit(sign_res)

print(f"\n🎉 Installer built successfully: {msi_file}")
sys.exit(0)  # Explicit success