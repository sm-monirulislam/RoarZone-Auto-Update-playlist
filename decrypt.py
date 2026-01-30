import zipfile
import os
import sys

ZIP_FILE = "RoarZone_main.zip"      # ZIP file name
EXTRACT_DIR = "main"       # Extract destination folder

# Read password from GitHub Secrets
password = os.environ.get("ZIP_PASSWORD")

if not password:
    print("❌ ERROR: ZIP_PASSWORD is missing in GitHub Secrets!")
    sys.exit(1)

# Check ZIP exists
if not os.path.exists(ZIP_FILE):
    print(f"❌ ERROR: {ZIP_FILE} not found!")
    sys.exit(1)

print("🔐 Trying to unlock ZIP...")

try:
    with zipfile.ZipFile(ZIP_FILE, "r") as z:
        z.extractall(
            path=EXTRACT_DIR,
            pwd=password.encode("utf-8")
        )

    print("✅ ZIP extracted successfully!")
    print(f"📂 Extracted to: {EXTRACT_DIR}/")

except RuntimeError as e:
    print("❌ WRONG PASSWORD or ZIP is corrupted!")
    print(e)
    sys.exit(1)

except zipfile.BadZipFile:
    print("❌ ZIP file is invalid or corrupted!")
    sys.exit(1)

except Exception as e:
    print("❌ Unexpected error during ZIP extraction:")
    print(e)
    sys.exit(1)
