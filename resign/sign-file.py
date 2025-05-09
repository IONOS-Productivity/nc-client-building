import subprocess
import argparse
import os
import sys
from pathlib import Path


def sign(file, signtool, timestamp_url, timestamp_alg
         , file_digest_alg, cert_file, cert_password, app_name):
    args = parser.parse_args()

    sign_file = Path(file)

    # Build the signtool command
    cmd = [
        signtool,
        "sign",
        # "/debug",
        # "/v",
        "/tr", timestamp_url,
        "/td", timestamp_alg,
        "/fd", file_digest_alg,
        "/f", cert_file,
        "/p", cert_password,
        "/d", app_name,
        sign_file
    ]

    # Execute the command
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[ERR] ({__file__}) Signing failed for {sign_file.name}")
        print(f"[ERR] ({__file__}) STDOUT:\n" + result.stdout.strip())
        print(f"[ERR] ({__file__}) STDERR:\n" + result.stderr.strip())
        return result
    else:
        print(f"[OK] ({__file__}) Successfully signed {sign_file.name}")
        return result # Explicit success
    
    
    
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

result = sign(args.file_path, args.signtool, timestamp_url, timestamp_alg
         , file_digest_alg, args.cert_file, args.cert_password, args.app_name)

path = Path(args.file_path)

if result.returncode != 0:
    print(f"[ERR] ({__file__}) Signing failed for {path.name}")
    print(f"[ERR] ({__file__}) STDOUT:\n" + result.stdout.strip())
    print(f"[ERR] ({__file__}) STDERR:\n" + result.stderr.strip())
    sys.exit(result.returncode)  # Propagate the failure
else:
    print(f"[OK] ({__file__}) Successfully signed {path.name}")
    sys.exit(0)  # Explicit success

