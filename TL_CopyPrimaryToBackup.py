# 20250813 untested draft

#!/usr/bin/env python3
import os
import sys
import shutil
import hashlib
import xxhash
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def get_backup_root():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    backup_root = filedialog.askdirectory(
        title="Select Drive letter of Backup Collection"
    )
    root.destroy()
    if backup_root and os.path.ismount(backup_root):
        return backup_root
    return None

def get_comparison_mode():
    print(f" COMPARISON MODE for files present in destination")
    print(f" - fast - by filesize (enter nothing)")
    print(f" - medium - by xxhash (enter any char)")
    print(f" - slow - by sha256 (enter any 2 chars)")
    user_input = input(" Enter response: ")
    if user_input == "":
        accuracy = "size"
    elif len(user_input) == 1:
        accuracy = "xxhash"
    else:
        accuracy = "sha256"
    return accuracy

def get_collection_files_shallow(root_path):
    """Get all files in collection directories (excluding root files and _* root dirs)"""
    root_path = Path(root_path)
    files_to_copy = []
    
    # Get all items in root
    for item in root_path.iterdir():
        if item.is_file():
            # Skip files in root
            continue
        elif item.is_dir() and item.name.startswith('_'):
            # Skip directories starting with underscore in root
            continue
        else:
            # This is a collection directory - get all files recursively
            
            for root_dir, _, files in item.iterdir():
                for file in files:
                    files_to_copy.append(os.path.join(root_dir, file))
    
    return files_to_copy

def move_file_preserving_structure(src_file, dest_root, relative_path):
    """Move file to destination while preserving directory structure"""
    dest_file = dest_root / relative_path
    
    # Create parent directories if they don't exist
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Move the file
    shutil.move(str(src_file), str(dest_file))
    print(f"Moved: {relative_path}")

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_xxhash(file_path):
    with open(file_path, 'rb') as f:
        return xxhash.xxh64(f.read()).hexdigest()

def are_files_same(src_file, sha256_src, dest_file, accuracy):
    if Path(src_file).stat().st_size != Path(dest_file).stat().st_size:
        return False
    if accuracy == "size": return True
    if compute_xxhash(src_file) != compute_xxhash(dest_file):
        return False
    if accuracy == "xxhash": return True # is xxhash fast enough
    if sha256_src != compute_sha256(dest_file):
        return False
    return True

# maybe useful for keeping older of identical pair
#def get_mtime(file_path):
#    return file_path.stat().st_mtime

def get_unique_filename(dest_path):
    base, ext = os.path.splitext(dest_path)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = f"{base}_diff_{counter}{ext}"
        counter += 1
    return dest_path

def copy_and_verify_file(src_file, dest_dir, relative_path, accuracy):
    try:
        dest_renamed = False
        dest_file = os.path.join(dest_dir, relative_path)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        sha256_src = compute_sha256(src_file)
        
        if os.path.exists(dest_file):

            isSame = are_files_same(src_file, sha256_src, dest_file, accuracy)
            if isSame:
                return True, "same"
            #rename non identical existing dest file
            dest_file_renamed = get_unique_filename(dest_file)
            shutil.move(dest_file, dest_file_renamed) 
            if not os.path.exists(dest_file_renamed):
               return False, f"Error: Move non-identical dest file failed, - SrcFile: {src_file}"
            dest_renamed = True        
            
        shutil.copy2(src_file, dest_file)

        isSame = are_files_same(src_file, sha256_src, dest_file, "sha256")
        if isSame:
            if dest_renamed:
                return True, "renamed"
            else:
                return True, "copied"
        else:
            os.remove(dest_file)
            return False, f"Error: Copy Verification failed, dest deleted - SrcFile: {src_file}"

    except (OSError, IOError) as e:
        if isinstance(e, OSError) and e.errno == 28:
            return False, f"Error: Disk full, current SrcFile: {src_file}"
        return False, f"Error: {str(e).split(':')[0]}, current SrcFile: {src_file}"


def main():
    if len(sys.argv) != 2:
        print("Error: Primary root path not provided")
        sys.exit(1)
    
    primary_root = Path(sys.argv[1])
    
    if not primary_root.exists():
        print(f"Error: Primary root path does not exist: {primary_root}")
        sys.exit(1)
    
    print(f"Selected Primary root: {primary_root}")
    
    # Get backup root from user
    backup_root_str = get_backup_root()
    if not backup_root_str:
        print("No backup root selected. Exiting.")
        sys.exit(1)
    
    backup_root = Path(backup_root_str)
    print(f"Selected Backup root: {backup_root}")
    
    if not backup_root.exists():
        print(f"Error: Backup root path does not exist: {backup_root}")
        sys.exit(1)

    # get the accuracy.
    accuracy = get_comparison_mode()
    print("  ")
    print(f"Selected accuracy: {accuracy}")
    print("  ")

    
    # Get valid primary files from both roots
    print("Scanning source collection...")
    primary_files_to_copy = get_collection_files_shallow(primary_root)
    print(f"Found {len(primary_files_to_copy)} files in primary collection")

    total_files = len(primary_files_to_copy)
    errors_list = []
    errors = 0
    checked = 0
    copied = 0
    renamed = 0
    same = 0

    print(f" → 0 / {total_files}, 0 copied, 0 dest-renamed, 0 same-{accuracy}, 0 errors", end="\r")
        
    for i, src in enumerate(primary_files_to_copy, 1):
        relative_path = os.path.relpath(src, primary_root)
        success, status_message = copy_and_verify_file(src, backup_root, relative_path, accuracy)

        if success:
            if status_message == "copied":
                copied += 1
            elif status_message == "renamed":
                renamed += 1
            elif status_message == "same":
                same += 1
        else:
            errors_list.append(status_message)
            errors += 1

        checked += 1
        if i % 10 == 0:
            print(f" → {checked} / {total_files}, {copied} copied, {renamed} dest-renamed, {same} same-{accuracy}, {errors} errors", end="\r")

    print(f" ✓ {checked} / {total_files}, {copied} copied, {renamed} dest-renamed, {same} same-{accuracy}, {errors} errors", end="\r")
    print("")

    if errors_list:
        print("\n  Errors:")
        for error in errors_list:
            print(error)


if __name__ == "__main__":
    print(f"COPY COLLECTION FILES TO BACKUP\n VERIFY COPIED FILES WITH SH256 HASHES")
    print(f" Failed copies are deleted.\n If a file is present in the destination:\n - Doesnt copy if both files same\n - renames non-same destination files with a suffix.")
    main()
    #input("Press Enter to exit...")