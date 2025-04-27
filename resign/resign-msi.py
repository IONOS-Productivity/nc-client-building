import subprocess
import argparse
import os
from pathlib import Path
import sys

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
    "--app-name", default="IONOS HiDrive Next",
    help="Name of app (default: IONOS HiDrive Next)", required=False
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

start_msi = Path(args.input_msi)
sign_tool = Path(args.sign_tool)
app_name = str(args.app_name)
app_name_sanitized = app_name.replace(" ", "_")
base_dir = Path(args.base_dir)

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

#----------------------------   
#--- Decompiling-------------
#----------------------------   
dark = Path(wix_path) / "bin" / "dark.exe"

run_command([
    str(dark), str(start_msi),
    "-x", str(extracted_dir),
    "-o", str(wxs_file)
], f"Decompiling {start_msi} to WXS and binary files", args.v)

#----------------------------   
#--- Signing ----------------
#----------------------------   
print(f"🔧 Start signing extracted files...")
file_names = [
    "NCContextMenu.dll",
    "NCOverlays.dll",
    app_name_sanitized + ".exe",
    app_name_sanitized + "cmd.exe",
    app_name_sanitized + "sync.dll",
    app_name_sanitized + "_csync.dll",
    # "qt6keychain%DLL_SUFFIX%.dll",
    # "%LIBCRYPTO_DLL_FILENAME%",
    # "%LIBSSL_DLL_FILENAME%",
    # "zlib1%DLL_SUFFIX%.dll",
]

for file_name in file_names:
    
    print(f"\t🔍 Looking for: {file_name}")
    search_result = subprocess.run(
        ["python", "read_wsx.py", wxs_file, file_name, "--first"],
        capture_output=True,
        text=True
    )

    if search_result.returncode == 0:
        source_path = Path(search_result.stdout.strip())
        print(f"\t🎯 Found: {source_path}")
    elif search_result.returncode == 1:
        print("\t❌ No match found.")
    else:
        print(f"\t💥 Error:\n{search_result.stderr.strip()}")
        
    renamed_file_path = source_path.parent / file_name    
    rename_file(source_path, renamed_file_path)

    sign_file(renamed_file_path, sign_tool, args.cert_file, args.cert_password, app_name)
    
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

candle = Path(wix_path) / "bin" / "candle.exe"

# Step 1: Compile .wxs to .wixobj using candle.exe
run_command(
    [str(candle), 
    "-ext", "WixUtilExtension",
    "-dcodepage=1252",
    "-o", wixobj_file,
     str(wxs_file),
    ]
    , "Compiling WXS to WIXOBJ", args.v)

# Step 2: Link .wixobj to .msi usi
# ng light.exe
light = Path(wix_path) / "bin" / "light.exe"

run_command([
    str(light), str(wixobj_file),
    "-ext", "WixUtilExtension",
    "-ext", "WixUIExtension",
    "-o", str(msi_file)
], "Linking WIXOBJ to MSI", args.v)

print(f"🔧 Start signing new .msi file...")

sign_file(
    msi_file,
    sign_tool,
    args.cert_file,
    args.cert_password,
    app_name
)

print(f"\n🎉 Installer built successfully: {msi_file}")
sys.exit(0)  # Explicit success