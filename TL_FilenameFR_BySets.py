# 2025-08-17 added ability to handle regex F-R
# 2025-08-17 added ability to handle multiple F-R from json file

import os
import sys
import re
from pathlib import Path
import json
import tkinter as tk
from tkinter import filedialog

filename_data = "TimelineFR_BySets_current_data.json"
folder_ignore_name = "HELP"

# Blacklisted file types
BLACKLISTED_EXTENSIONS = {".exe", ".dll", ".sys", ".bat"}

# Undo queue for optional rollback
undo_queue = []

def compile_rule(rule):
    if "regex" in rule and "case_sens" in rule:
        try:
            if rule["regex"] and rule["case_sens"]:
                compiled = re.compile(rule["find"])
                rule["find"] = compiled
            elif not rule["case_sens"]:
                compiled = re.compile(rule["find"], re.IGNORECASE)
                rule["find"] = compiled
            return rule

        except re.error as e:
            return {
                "error": f"Invalid find regex: {rule['find']}",
                "exception": str(e)
            }
    else:
        return {
            "error": "Missing 'case_sens' and 'regex' key in json data",
            "exception": ""
        }
    
def precompile_data_dict(raw_data):
    compiled_data = {}
    compile_errorlist = []
    for folder_name, rules in raw_data.items():
        if folder_name == folder_ignore_name:
            continue
        if len(rules) == 0:
            continue
        
        folder_rules = []
        for rule in rules:
            rule_compiled = compile_rule(rule)
            if "error" in rule_compiled:
                compile_errorlist.append(f"Rule compile error: {rule}")
            else:
                folder_rules.append(rule_compiled)
        compiled_data[folder_name] = folder_rules
    return compiled_data, compile_errorlist

def rename_files(root_str, precomp_fr_data):
    errorlist = []

    for folder_name, replacement_objs in precomp_fr_data.items():
        if folder_name == folder_ignore_name:
            continue
        if len(replacement_objs) == 0:
            continue
        folder_path = os.path.join(root_str, folder_name)
        if not os.path.exists(folder_path):
            continue
        print(f"Processing: {folder_path}")
        filenames = os.listdir(folder_path)
        num_files = len(filenames)

        renamed = 0
        unmodified = 0
        checked = 0
        error = 0

        for filename_ori in filenames:
            checked += 1
            src_path = os.path.join(folder_path, filename_ori)

            # Skip folders and blacklisted extensions
            if not os.path.isfile(src_path) or any(filename_ori.lower().endswith(ext) for ext in BLACKLISTED_EXTENSIONS):
                continue

            filename_new = filename_ori
            for rule in replacement_objs:

                try:
                    if rule["case_sens"] and not rule["regex"]:
                        if rule["find"] in filename_new:
                            filename_new = filename_new.replace(rule["find"], rule["replace"])
                    else:
                        filename_new = rule["find"].sub(rule["replace"], filename_new)

                except Exception as e:
                    errorlist.append(f"Rule error in {folder_name}: {e}")
                    continue

            if filename_new == filename_ori:
                unmodified += 1
            else:
                dst_path = os.path.join(folder_path, filename_new)
                suffix = 1
                while os.path.exists(dst_path):
                    base, ext = os.path.splitext(filename_new)
                    dst_path = os.path.join(folder_path, f"{base}_{suffix}{ext}")
                    suffix += 1

                try:
                    os.rename(src_path, dst_path)
                    undo_queue.append((dst_path, src_path))
                    renamed += 1
                except OSError as e:
                    errorlist.append(f"Error renaming {filename_ori}: {e}")
                    error += 1

            if checked % 10 == 0:
                print(f" → {checked} / {num_files}, {renamed} renamed, {unmodified} unmodified, {error} errors", end="\r")

        print(f" ✓ {checked} / {num_files}, {renamed} renamed, {unmodified} unmodified, {error} errors", end="\r")
        print("")

    if errorlist:
        print("\nERRORS:")
        for errstr in errorlist:
            print(errstr)

def undo_rename():
    print("\nUndoing previous renames...")
    while undo_queue:
        new_path, old_path = undo_queue.pop()
        try:
            os.rename(new_path, old_path)
            print(f"Restored: {os.path.basename(new_path)} → {os.path.basename(old_path)}")
        except Exception as e:
            print(f"Undo error: {e} ({new_path})")

def get_volume_root():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    backup_root = filedialog.askdirectory(
        title="Select Drive letter of Collection"
    )
    root.destroy()
    if backup_root and os.path.ismount(backup_root):
        return backup_root
    return None

if __name__ == "__main__":
    print(f"TIMELINE TOOL - rename filenames with find-replace")
    print(f"- using a prepared list of F-R strings")
    print(f"  placed at the top of the script")
    # can get vol root via .cmd script. easier.
    if len(sys.argv) == 2:
        root_str = Path(sys.argv[1])
    else:
        root_str = get_volume_root()

    dir_script_parent = str(Path(__file__).resolve().parent)
    filepath_data = os.path.join(dir_script_parent, filename_data)
    try:
        with open(filepath_data, "r", encoding="utf-8") as f:
            fr_data_raw = json.load(f)

    except json.JSONDecodeError as e:
        print(f"JSON load error: {e}")
        input("\nfix json file error then enter to quit.")
        sys.exit()


    # if adding regex to json, can precompile them before sending to next step. 
    precomp_fr_data, compile_errorlist = precompile_data_dict(fr_data_raw)
    if compile_errorlist:
        print(f"ERRORS in raw data file.")
        for err in compile_errorlist:
            print(err)
        input("\nfix data errors then enter to quit.")
        sys.exit()

    rename_files(root_str, precomp_fr_data)

    if undo_queue:
        choice = input("\nUndo changes? (enter any char or nothing to keep changes): ").strip().lower()
        if choice != "":
            undo_rename()