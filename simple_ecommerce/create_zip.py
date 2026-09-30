#!/usr/bin/env python
"""
Packaging utility to generate simple_ecommerce_store.zip.
Excludes virtual environments, cache folders, and temp files to produce a clean, portable zip.
"""
import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_OUTPUT_PATH = os.path.join(BASE_DIR, 'simple_ecommerce_store.zip')

EXCLUDE_DIRS = {'venv', '.venv', '__pycache__', '.git', '.idea', '.vscode'}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.pyd'}

def create_zip():
    print(f"Creating ZIP archive from: {BASE_DIR}")
    file_count = 0

    with zipfile.ZipFile(ZIP_OUTPUT_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Modify dirs in-place to exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                # Don't include the zip file itself or python bytecode
                if file == 'simple_ecommerce_store.zip' or os.path.splitext(file)[1] in EXCLUDE_EXTS:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR)
                zipf.write(full_path, arcname=os.path.join('simple_ecommerce', rel_path))
                file_count += 1

    file_size_kb = os.path.getsize(ZIP_OUTPUT_PATH) / 1024
    print(f"Successfully created {ZIP_OUTPUT_PATH}")
    print(f"Total files packed: {file_count}")
    print(f"Archive size: {file_size_kb:.1f} KB")

if __name__ == '__main__':
    create_zip()
