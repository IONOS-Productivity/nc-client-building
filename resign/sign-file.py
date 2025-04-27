import subprocess
import argparse
import os
import sys
from pathlib import Path


# CLI argument setup
parser = argparse.ArgumentParser(description="Signs a single file using sign.py.")
parser.add_argument("file_path", help="Path to the file to sign")
parser.add_argument("--signtool", required=True, help="Path to signtool.exe")
parser.add_argument("--cert-file", required=True)
parser.add_argument("--cert-password", required=True)
parser.add_argument("--app-name", required=True, help="Application name for the /d parameter")

timestamp_url = "http://timestamp.digicert.com"
timestamp_alg = "sha256"
file_digest_alg = "sha256"

args = parser.parse_args()

# Loop over files and call sign.py
print(f"Signing: {args.file_path}")
result = subprocess.run([
    sys.executable,  # ensures we're calling with the current Python interpreter
    "./sign.py",
    str(args.file_path),
    "--signtool", args.signtool,
    "--timestamp-url", timestamp_url,
    "--timestamp-alg", timestamp_alg,
    "--file-digest-alg", file_digest_alg,
    "--cert-file", args.cert_file,
    "--cert-password", args.cert_password,
    "--app-name", args.app_name
])
path = Path(args.file_path)

if result.returncode != 0:
    print(f"[ERR] ({__file__}) Signing failed for {path.name}")
    print(f"[ERR] ({__file__}) STDOUT:\n" + result.stdout.strip())
    print(f"[ERR] ({__file__}) STDERR:\n" + result.stderr.strip())
    sys.exit(result.returncode)  # Propagate the failure
else:
    print(f"[OK] ({__file__}) Successfully signed {path.name}")
    sys.exit(0)  # Explicit success

