# create a JSONL file with a JOURNAL entry for each file in the TIMELINE set

# 20250815 untrested draft
# 20250814 created from copy of cleanup script

#!/usr/bin/env python3
import os
import sys
import re
import json
import mimetypes
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

def get_dt_patterns():
    re1 = re.compile(r"^(?<date>\d{4}-\d{2}-\d{2})[ _](?<time_fn>\d{2}([-_]\d{2})?([-_]\d{2})?(\.\d{3,6})?)(?<utc_offset>[\+-]\d{4})? "),
    re2 = re.compile(r"^(?<date>\d{4}-\d{2}-\d{2}) "),
    re3 = re.compile(r"^(?<date>\d{4}(-\d{2})?) "),
    return [re1, re2, re3]

def get_collection_files(root_path):
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
            for root_dir, _, files in os.walk(item):
                for file in files:
                    files_to_copy.append(os.path.join(root_dir, file))
    return files_to_copy

def extract_datetime_values(file_path, patterns):
    # patterns are precompiled in main() before any loop
    parentpath, filename = os.path.split(file_path)
    filename_base, ext = os.path.splitext(filename)
    match_substr = ""
    pattern_used = None
    for pattern in patterns:
        match = pattern.match(filename)
        if match:
            match_str = match.group()
            match_len = len(match_str)
            remainder = filename_base[match_len:]
            named_parts = match.groupdict()   
            date = named_parts.get('date')
            time = named_parts.get('time')
            utc_offset = named_parts.get('utc_offset')
            return date, time, utc_offset, remainder, ext

    return "", "", "", "", ext

def extract_location(remainder):
    # the timeline filenames are a mess and most need fixing.
    # if the file has " - " then assume before is location
    # otherwise return the string as the description.
    str_parts = remainder.split(' - ', 1)
    if len(str_parts) == 2:
        return str_parts[0], str_parts[1]
    return "", remainder
    
def detect_mimetype(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type: return ""
    return mime_type
    
def trysave_string_to_utf8_file_ret_bool(file_output, file_string):
    try:
        with open(file_output, 'w', encoding='utf-8') as f:
            f.write(file_string)
        return True
    except Exception as e:
        print('ERROR: save file exception: ', e)
        return False

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
    
    # Get collection files from both roots
    print("Scanning primary collection...")
    primary_files = get_collection_files(primary_root)
    num_primary_files = len(primary_files)
    print(f" Primary collection: {num_primary_files} files.")

    # match ok 2008-04-13_15-42 TH Chiang Mai Songkran water fight drummer - RENAME.mp4
    # match fail 2008-04-12_12-17-56+0700 TH Chiang Mai_RENAME.jpg
    # rename files in backup difft from primary if match
    checked = 0
    extracted = 0
    errors = 0
    errors_list = []
    entries_list = []
    datetime_patterns = get_dt_patterns()

    print(f" → 0 / {num_primary_files}, 0 extracted, 0 errors", end="\r")

    for pri_file_path in primary_files:

        checked += 1
        date, time, utc_offset, remainder, ext = extract_datetime_values(pri_file_path, datetime_patterns)
        if date == "":
            errors += 1
            continue
        location, description = extract_location(remainder)
        mime_type = detect_mimetype(pri_file_path)

        # can use IM to extract camera data
        device_type = ""
        device_code = ""

        dict_entry = {
            "date": date,
            "time": time,
            "utc_offset": utc_offset,
            "location": location,
            "description": description,
            "format": mime_type,
            "device_type": device_type,
            "device_code": device_code,
            "tags": ["timeline", "file"]
        }

        entry_str = json.dumps(dict_entry)
        entries_list.append(entry_str)
        extracted += 1

        if checked % 10 == 0:
            print(f" → {checked} / {num_primary_files}, {extracted} extracted, {errors} errors", end="\r")

    print(f" ✓ {checked} / {num_primary_files}, {extracted} extracted, {errors} errors", end="\r")
    print("")

    if entries_list:
        # save to root level file.
        entries_sorted = sorted(entries_list)
        file_string = '\n'.join(entries_sorted)

        filename = f"_ScriptGeneratedJournalEntries.jsonl" # 
        file_output = os.path.join(primary_root, filename)
        saved = trysave_string_to_utf8_file_ret_bool(file_output, file_string)
        if saved == False:
            errors_list.append(f'Filesave error: {filename}')
    else:
        print(f"NO ENTRIES EXTRACTED. No file saved.")

    if errors_list:
        print(f"  ERRORS: {len(errors_list)}")
        for err_str in errors_list:
            print(err_str)




if __name__ == "__main__":
    print("COLLECTION TOOL: Generate JOURNAL entries from timeline files")
    main()