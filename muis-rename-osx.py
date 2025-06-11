#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""File renamer with logging, dry-run option, sorted files, dot-file exclusion, and conditional EXIF updates"""

__version__ = "1.1"

import requests
import sys
import os
import os.path
import datetime
import argparse
import subprocess  # To execute exiftool commands

# Clear the terminal screen
os.system('clear')  # Use 'cls' on Windows

# Color class for terminal output
class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Function to replace umlauts in text
def replace_umlauts(text):
    replacements = {
        'Ä': 'A', 'ä': 'a',
        'Ü': 'U', 'ü': 'u',
        'Ö': 'O', 'ö': 'o',
        'Õ': 'O', 'õ': 'o',
        'Å': 'A', 'å': 'a',
        'Æ': 'AE', 'æ': 'ae',
        'Ø': 'O', 'ø': 'o',
    }
    for umlaut, replacement in replacements.items():
        text = text.replace(umlaut, replacement)
    return text

# Argument parser for command-line options
parser = argparse.ArgumentParser(description="Failide ümbernimetamine koos logimise, kuivkäivituse ja valikuliste EXIF-i uuendustega.")
parser.add_argument("-t", "--test", action="store_true", help="Lülita sisse kuivkäivituse režiim (faile ei nimetata ümber kui luuakse logi).")
parser.add_argument("-e", "--exiftool", action="store_true", help="Luba IPTC metaandmete kirjutamine Exiftooli abil.")

args = parser.parse_args()

# Get directory name from user
dirName = input("Kaust kus asuvad failid: ").strip()  # Remove leading/trailing whitespace
dirName = dirName.strip('"').strip("'")  # Remove any enclosing quotes
dirName = dirName.rstrip()  # Remove trailing slashes or newlines

# Check if directory exists
if not os.path.isdir(dirName):
    print(f"Directory '{dirName}' does not exist.")
    sys.exit()

# Prepare log file in the target directory
log_file_path = os.path.join(dirName, f"failide_logi_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
log_file_name = os.path.basename(log_file_path)  # Extract the log file name
with open(log_file_path, 'w', encoding='utf-8') as log_file:
    log_file.write(f"Failide logi - {datetime.datetime.now()}\n")
    log_file.write(f"Kaust - {log_file_path}\n")
    log_file.write("=" * 50 + "\n")

# List and sort directory contents
dirContent = sorted(os.listdir(dirName))

# Counter for processed files
i = 0

# Process each file in the directory
for fileNameIn in dirContent:
    # Skip the log file itself and files starting with a dot
    if fileNameIn == log_file_name or fileNameIn.startswith('.'):
        continue

    i += 1
    fileNameArr = fileNameIn.split(".")
    fileExt = fileNameArr[-1]  # Get file extension
    fileBase = fileNameArr[0]  # Get file base name

    # Split the base name by "_" to extract parts
    fileBaseArr = fileBase.split("_")  # Adjust to support "-" if needed
    muisid = fileBaseArr[0]
    if len(fileBaseArr) > 1:
        seq = fileBaseArr[-1]
    else:
        seq = ""

    # Display file info
    print(f"[ {i} ]")
    print(f"Algfail: {color.YELLOW}{fileNameIn}{color.END}")
    print(f"MuISi ID failist: {color.YELLOW}{muisid}{color.END}")
    print(f"MuISi link: {color.GREEN}https://www.muis.ee/museaalview/{muisid}{color.END}")

    # Fetch metadata from MuIS
    link = f"https://www.muis.ee/rdf/object/{muisid}"
    try:
        r = requests.get(link)
        r.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching MuIS ID {muisid}: {e}"
        print(f"{color.RED}{error_msg}{color.END}")
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{error_msg}\n")
        continue

    # Parse XML response
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(r.text.encode('utf-8'))
    except ET.ParseError as e:
        error_msg = f"Error parsing XML for MuIS ID {muisid}: {e}"
        print(f"{color.RED}{error_msg}{color.END}")
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{error_msg}\n")
        continue

    # Extract object ID and label
    objectId = None
    labelTitle = None
    for thing in root.findall('{http://www.cidoc-crm.org/cidoc-crm/}E18_Physical_Thing'):
        object = thing.find('{http://purl.org/dc/terms/}identifier')
        if object is not None:
            objectId = object.text
        label = thing.find('{http://www.w3.org/2000/01/rdf-schema#}label')
        if label is not None and label.attrib.get('{http://www.w3.org/XML/1998/namespace}lang') == 'et':
            labelTitle = label.text

    if not objectId:
        error_msg = f"Ei leidud sellist MuISi ID: {muisid}."
        print(f"{color.RED}{error_msg}{color.END}")
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{error_msg}\n")
        continue

    print(f"Museaali number: {objectId}")
    if labelTitle:
        print(f"MuIS Label Title: {labelTitle}")

    # Replace umlauts in the object ID
    sanitizedObjectId = replace_umlauts(objectId)

    # Generate new file name
    fileName = sanitizedObjectId.replace(" ", "").replace(":", "_").replace("/", "-")
    if seq:
        seq = f"_{seq}"
    else:
        seq = ""

    fileNameFinal = f"{fileName}{seq}.{fileExt}"
    print(f"Faili nimi: {fileNameFinal}")

    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[ {i} ]\n")
        log_file.write(f"Algfail: {fileNameIn}\n")
        log_file.write(f"MuISi ID: {muisid}\n")
        log_file.write(f"MuISi link: https://www.muis.ee/museaalview/{muisid}\n")
        log_file.write(f"Museaali number: {objectId}\n")
        if labelTitle:
            log_file.write(f"MuIS nimetus: {labelTitle}\n")
        log_file.write(f"Digihoidla fail: {fileNameFinal}\n\n")

    # Update EXIF data with MuIS ID and Label Title (only if -e/--exiftool is passed)
    if args.exiftool:
        try:
            exiftool_cmd = [
                "exiftool",
                f"-IPTC:Source=MuIS ID: {muisid}",
            ]
            if labelTitle:
                exiftool_cmd.append(f"-IPTC:ObjectName={labelTitle}")
            exiftool_cmd.append(os.path.join(dirName, fileNameIn))

            subprocess.run(exiftool_cmd, check=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"Error updating EXIF data for {fileNameIn}: {e}"
            print(f"{color.RED}{error_msg}{color.END}")
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{error_msg}\n")

    # Rename the file (only if not in dry-run mode)
    if not args.test:
        try:
            os.rename(os.path.join(dirName, fileNameIn), os.path.join(dirName, fileNameFinal))
        except OSError as e:
            error_msg = f"Error renaming file {fileNameIn} to {fileNameFinal}: {e}"
            print(f"{color.RED}{error_msg}{color.END}")
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"{error_msg}\n")
            continue

# Summary
summary_msg = f"Kokku töödeldi {i} faili"
print("-----------------")
print(f"{summary_msg}")
with open(log_file_path, 'a', encoding='utf-8') as log_file:
    log_file.write("=" * 50 + "\n")
    log_file.write(f"{summary_msg}\n")
input("Klõpsa Enter väljumiseks...")
