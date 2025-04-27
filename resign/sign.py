import subprocess
import argparse
import sys
from pathlib import Path

# Setup CLI argument parsing
parser = argparse.ArgumentParser(description="Sign a file using signtool.")
parser.add_argument("file", help="Path to the file to sign")
parser.add_argument("--signtool", required=True, help="Full path to signtool.exe")
parser.add_argument("--timestamp-url", required=True, help="Timestamp server URL (e.g. http://timestamp.digicert.com)")
parser.add_argument("--timestamp-alg", required=True, help="Timestamp digest algorithm (e.g. sha256)")
parser.add_argument("--file-digest-alg", required=True, help="File digest algorithm (e.g. sha256)")
parser.add_argument("--cert-file", required=True, help="Path to the certificate file (.pfx)")
parser.add_argument("--cert-password", required=True, help="Password for the certificate file")
parser.add_argument("--app-name", required=True, help="Application name for the /d parameter")

args = parser.parse_args()

sign_file = Path(args.file)

# Build the signtool command
cmd = [
    args.signtool,
    "sign",
    # "/debug",
    # "/v",
    "/tr", args.timestamp_url,
    "/td", args.timestamp_alg,
    "/fd", args.file_digest_alg,
    "/f", args.cert_file,
    "/p", args.cert_password,
    "/d", args.app_name,
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
    sys.exit(result.returncode)  # Propagate the failure
else:
    print(f"[OK] ({__file__}) Successfully signed {sign_file.name}")
    sys.exit(0)  # Explicit success

# Print output
# print(result.stdout)
# if result.stderr:
#     print("ERROR:", result.stderr, file=sys.stderr)

# Exit with the same return code as signtool
sys.exit(result.returncode)
