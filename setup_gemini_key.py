"""
setup_gemini_key.py - Secure Local Gemini API Key Configuration Tool
SHA Interface Interiors - AI-Powered Lead Management System

Prompts the user to enter their Google Gemini API key securely in a local terminal
using masked/hidden input (getpass). The key is written directly to the local .env
file (ignored by git) and never displayed on screen, logged, or transmitted anywhere.
"""

import sys
import os
import getpass

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def setup_key():
    print("=" * 65)
    print("   SHA INTERFACE INTERIORS - SECURE GEMINI API KEY SETUP")
    print("=" * 65)
    print("\nThis utility securely saves your Google Gemini API key into your local .env file.")
    print("• Your key is typed invisibly (input is masked and will not appear on screen).")
    print("• The .env file is strictly ignored by git and will never be pushed.")
    print("• Never share or commit your API key.\n")

    try:
        raw_key = getpass.getpass("Enter your Gemini API key (hidden): ").strip()
    except Exception:
        # Fallback if getpass is unsupported in rare pseudo-terminals
        raw_key = input("Enter your Gemini API key: ").strip()

    if not raw_key:
        print("\n[INFO] No key entered. Operation cancelled.")
        return

    if len(raw_key) < 15:
        print("\n[WARNING] The entered key appears shorter than typical Gemini keys (~39 chars).")
        confirm = input("Save anyway? (y/n): ").strip().lower()
        if confirm != "y":
            print("[INFO] Cancelled.")
            return

    # Path to .env
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")

    # Read existing lines if .env exists
    lines = []
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    # Replace or append GEMINI_API_KEY
    key_written = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("GEMINI_API_KEY="):
            new_lines.append(f"GEMINI_API_KEY={raw_key}\n")
            key_written = True
        else:
            new_lines.append(line)

    if not key_written:
        new_lines.append(f"GEMINI_API_KEY={raw_key}\n")

    # Ensure other default settings exist
    content_str = "".join(new_lines)
    if "GEMINI_MODEL=" not in content_str:
        new_lines.append("GEMINI_MODEL=gemini-1.5-flash\n")
    if "STUDIO_TIMEZONE=" not in content_str:
        new_lines.append("STUDIO_TIMEZONE=Asia/Kolkata\n")
    if "STUDIO_PRIMARY_CITIES=" not in content_str:
        new_lines.append("STUDIO_PRIMARY_CITIES=Bangalore,Hyderabad\n")

    # Write securely
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Set environment variable for current runtime
    os.environ["GEMINI_API_KEY"] = raw_key

    print("\n[SUCCESS] API key saved securely into .env file.")
    print("Testing connection with Google Gemini API...")

    import ai_service
    status = ai_service.verify_connection()
    if status.get("connected"):
        print(f"-> [VERIFIED] Gemini API connected successfully!")
        print(f"-> Model: {status.get('model')}")
        print("-> Your CRM AI Assistant is now operating with Gemini AI capabilities.")
    else:
        print(f"-> [STATUS] Key saved, but API check returned: {status.get('error')}")
        print("-> Note: The CRM will continue operating seamlessly on the built-in local engine.")
    print("=" * 65)


if __name__ == "__main__":
    setup_key()
