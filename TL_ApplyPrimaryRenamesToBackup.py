# TIMELINE TOOL - rename filenames with find-replace
# - using a prepared list of F-R strings
#   placed at the top of the script

#!/usr/bin/env python3
import os
import sys
import re
import shutil
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def get_dt_patterns():

    re1 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2}[-_]\d{2}\.\d{3,6}[\+-]\d{4} "),
    re2 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2}[-_]\d{2}\.\d{3,6} "),
    re3 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2}[-_]\d{2}[\+-]\d{4} "),
    re4 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2}[-_]\d{2} "),
    re5 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2}[\+-]\d{4} "),
    re6 = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}[-_]\d{2} ")
    
    return [re1, re2, re3, re4, re5, re6,]

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

def get_collection_files_shallow(root_path):
    """Get all files in collection directories (excluding root files and _* root dirs)"""
    root_path = Path(root_path)
    files_to_copy = []
    for item in root_path.iterdir():
        if item.is_file():
            continue
        elif item.is_dir() and item.name.startswith('_'):
            continue
        elif item.is_dir() and item.name.startswith('System Volume'):
            continue
        else:
            for root_dir, _, files in item.iterdir():
                for file in files:
                    files_to_copy.append(os.path.join(root_dir, file))
    return files_to_copy

def get_unique_filename(dest_path):
    base, ext = os.path.splitext(dest_path)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = f"{base}_{counter}{ext}"
        counter += 1
    return dest_path

# last thing TODO
def calc_filename_substr(file_path, patterns):
    # patterns are precompiled in main() before any loop
    parentpath, filename = os.path.split(file_path)
    match_substr = ""
    pattern_used = None
    for pattern in patterns:
        match_result = pattern.match(filename)
        if match_result:
            pattern_used = pattern
            match_substr = match_result.group()
            break
    print(f" try match - filename: {filename}")
    print(f" - with pattern: {pattern_used}")
    print(f" - match_substr: {match_substr}")
    return parentpath, filename, match_substr

def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def isIdentical(mbpath, pri_file_path):
    return compute_sha256(mbpath) == compute_sha256(pri_file_path)


def main():
    if len(sys.argv) != 2:
        print("Error: Primary root path not provided")
        sys.exit(1)
    
    primary_root_str = sys.argv[1] + "\\"
    primary_root = Path(primary_root_str)
    
    if not primary_root.exists():
        print(f"Error: Primary root path does not exist: {primary_root}")
        sys.exit(1)
    
    print(f"Primary SD card root: {primary_root}")
    
    # Get backup root from user
    backup_root_str = get_backup_root()
    if not backup_root_str:
        print("No backup root selected. Exiting.")
        sys.exit(1)
    
    backup_root = Path(backup_root_str)
    print(f"Backup SD card root: {backup_root}")
    
    if not backup_root.exists():
        print(f"Error: Backup root path does not exist: {backup_root}")
        sys.exit(1)

    # Get collection files from both roots
    print("Scanning primary collection...")
    primary_files = get_collection_files_shallow(primary_root)
    num_primary_files = len(primary_files)
    print(f" Primary collection: {num_primary_files} files.")

    # Get collection files from both roots
    print("Scanning backup collection...")
    backup_files = get_collection_files_shallow(backup_root)
    num_backup_files = len(backup_files)
    print(f" Backup collection: {num_backup_files} files.")

    # match ok 2008-04-13_15-42 TH Chiang Mai Songkran water fight drummer - RENAME.mp4
    # match fail 2008-04-12_12-17-56+0700 TH Chiang Mai_RENAME.jpg
    datetime_patterns = get_dt_patterns()
    # rename files in backup difft from primary if match
    checked = 0
    count_same = 0
    count_undet = 0
    count_renamed = 0
    errors = 0
    errors_list = []

    #print(f" → 0 / {num_primary_files}, 0 same, 0 undetermined, 0 renamed, 0 errors", end="\r")

    for pri_file_path in primary_files:

        checked += 1
        relative_path = os.path.relpath(pri_file_path, primary_root)
        backup_eq_path = backup_root / relative_path

        #if backup_eq_path in backup_files:
        if backup_eq_path.exists():
            count_same += 1
            continue # filename exists in backup

        # ONLY RENAMED FILES FROM HERE
        print(f"   ")
        print(f" primary file: {pri_file_path}")
        print(f" relative_path: {relative_path}")
        print(f" backup_eq_path: {backup_eq_path}")

        parentpath, filename, f_substr = calc_filename_substr(pri_file_path, datetime_patterns)

        if f_substr == "":
            count_undet += 1
            continue # insufficient filename

        b_parentpath, filename = os.path.split(backup_eq_path)
        backup_path_substr = os.path.join(b_parentpath, f_substr)
        print(f" backup_path_substr: {backup_path_substr}")
        
        # check how many files have that filename prefix. 
        matching_paths = [bpath for bpath in backup_files if bpath.startswith(backup_path_substr)]
        print(f" num matching: {len(matching_paths)}")
        # possible theres multiple dt matches
        ident_matching_paths = [mbpath for mbpath in matching_paths if isIdentical(mbpath, pri_file_path)]
        print(f" num identical file: {len(ident_matching_paths)}")
        
        # only proceed if theres one otherwise its too messy
        if len(ident_matching_paths) == 1:
            #rename with primary
            backup_old_path = ident_matching_paths[0]
            os.rename(backup_old_path, backup_eq_path)
            if backup_eq_path.exists():
                count_renamed += 1
                print(f" Renamed: {backup_old_path} with {filename}")
            else:
                msg = f"Error: Backup file not renamed: {backup_old_path}"
                errors_list.append(msg)
                errors += 1
        else:
            msg = f"Error: No exact file match: {backup_eq_path}"
            errors_list.append(msg)
            errors += 1
                
        #if checked % 10 == 0:
        #    print(f" → {checked} / {num_primary_files}, {count_same} same, {count_undet} undetermined, {count_renamed} renamed, {errors} errors", end="\r")

    #print(f" ✓ {checked} / {num_primary_files}, {count_same} same, {count_undet} undetermined, {count_renamed} renamed, {errors} errors", end="\r")
    print("")
    print(f"\nOperation complete. Renamed {count_renamed} backup files after primary.")

if __name__ == "__main__":
    print("COLLECTION TOOL: Propagate primary file renames to backup")
    print("- if unique match found by datetime prefix is identical file")
    main()