#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""File renamer with logging, dry-run option, MuIS integration, EXIF tool support, and MuIS file name checker"""

import requests
import sys
import os
import os.path
import datetime
import argparse
import subprocess
import xml.etree.ElementTree as ET

# Terminal color output
class color:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
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

# Fetch filenames from MuIS OAIService
def get_muis_file_names(muis_id):
    url = f"https://www.muis.ee/OAIService/OAIService?verb=GetRecord&metadataPrefix=lido&identifier=oai:muis.ee:{muis_id}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        root = ET.fromstring(r.text.encode("utf-8"))
        ns = {"lido": "http://www.lido-schema.org"}
        file_names = [
            replace_umlauts(el.text)
            for el in root.findall(".//lido:resourceDescription[@lido:type='failinimi']", ns)
            if el.text
        ]
        return list(set(file_names))
    except Exception as e:
        return []

# Argument parser
parser = argparse.ArgumentParser(
    description="Failide ümbernimetamine koos logimise, kuivkäivituse ja valikuliste EXIF-i uuendustega.")
parser.add_argument("-t", "--test", action="store_true",
                    help="Lülita sisse kuivkäivituse režiim (faile ei nimetata ümber kui luuakse logi).")
parser.add_argument("-e", "--exiftool", action="store_true",
                    help="Luba IPTC metaandmete kirjutamine Exiftooli abil.")
parser.add_argument("-c", "--check", action="store_true",
                    help="Kontrolli MuIS ID põhjal seotud failinimesid.")
args = parser.parse_args()

# Get directory from user
dirName = input("Kaust kus asuvad failid (võid kausta lohistada siia): ").strip()
dirName = dirName.replace('\\', '')
dirName = dirName.strip('"').strip("'").strip()
dirName = os.path.expanduser(dirName)
dirName = os.path.abspath(dirName)

# Validate directory
if not os.path.isdir(dirName):
    print(f"Directory '{dirName}' does not exist.")
    sys.exit()

# Prepare log file
log_file_path = os.path.join(
    dirName, f"failide_logi_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
log_file_name = os.path.basename(log_file_path)
log_file = open(log_file_path, 'w', encoding='utf-8')
log_file.write(f"Failide logi - {datetime.datetime.now()}\n")
log_file.write(f"Kaust - {log_file_path}\n")
log_file.write("=" * 50 + "\n")

# List and sort directory contents
dirContent = sorted(os.listdir(dirName))

# Check mode: list filenames from MuIS API and exit
if args.check:
    checked_ids = set()
    counter = 0
    for fileNameIn in dirContent:
        if fileNameIn.startswith('.'):
            continue
        baseName = os.path.splitext(fileNameIn)[0]
        if '_pisipilt' in baseName:
            continue
        base = os.path.splitext(fileNameIn)[0]
        muis_id = base.split("_")[0]
        counter += 1
        if muis_id not in checked_ids:
            checked_ids.add(muis_id)
            names = get_muis_file_names(muis_id)
            for name in names:
                base = os.path.splitext(name)[0]
                if '_pisipilt' in base:
                    continue
                log_file.write(f"{name}\n")
                print(f"\rFaile: {counter}", end='', flush=True)
    print()  # newline after counter
    log_file.close()
    sys.exit()

# Ask confirmation only if not in test mode
if not args.test:
    confirmation = input("Kas oled teinud koopia oma failidest? Kas jätkame? (jah/ei): ").strip().lower()
    if confirmation != "jah":
        print("Katkestatud kasutaja poolt.")
        log_file.close()
        sys.exit()

# Process files
i = 0
for fileNameIn in dirContent:
    baseName = os.path.splitext(fileNameIn)[0]
    if fileNameIn == log_file_name or fileNameIn.startswith('.') or '_pisipilt' in baseName:
        continue

    i += 1
    fileNameArr = fileNameIn.split(".")
    if len(fileNameArr) < 2:
        continue
    fileExt = fileNameArr[-1]
    fileBase = ".".join(fileNameArr[:-1])

    fileBaseArr = fileBase.split("_")
    muisid = fileBaseArr[0]
    seq = "_".join(fileBaseArr[1:]) if len(fileBaseArr) > 1 else ""

    log_file.write(f"[ {i} ]\n")
    log_file.write(f"Algfail: {fileNameIn}\n")
    log_file.write(f"MuISi ID: {muisid}\n")
    log_file.write(f"MuISi link: https://www.muis.ee/museaalview/{muisid}\n")

    # Fetch metadata
    link = f"https://www.muis.ee/rdf/object/{muisid}"
    try:
        r = requests.get(link)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        log_file.write(f"Error fetching MuIS ID {muisid}: {e}\n\n")
        continue

    try:
        root = ET.fromstring(r.text.encode('utf-8'))
    except ET.ParseError as e:
        log_file.write(f"Error parsing XML for MuIS ID {muisid}: {e}\n\n")
        continue

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
        log_file.write(f"Ei leidud sellist MuISi ID: {muisid}.\n\n")
        continue

    log_file.write(f"Museaali number: {objectId}\n")
    if labelTitle:
        log_file.write(f"MuIS nimetus: {labelTitle}\n")

    sanitizedObjectId = replace_umlauts(objectId)
    cleanSeq = f"_{seq}" if seq else ""
    fileNameFinal = f"{sanitizedObjectId.replace(' ', '').replace(':', '_').replace('/', '-')}{cleanSeq}.{fileExt}"
    log_file.write(f"Digihoidla fail: {fileNameFinal}\n")
    

    # Check MuIS for existing filename
    muis_filenames = get_muis_file_names(muisid)

    if args.test:
        print(f"[TEST] {fileNameIn} → {fileNameFinal}")

    if fileNameFinal in muis_filenames:
        print(f"\r{color.RED}⚠ Fail '{fileNameFinal}' on juba MuIS-is olemas!{color.END}", flush=True)
        log_file.write(f"⚠ Fail '{fileNameFinal}' on juba MuIS-is olemas – kirjutati üle.\n")

    # Write EXIF
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
            log_file.write(f"Error updating EXIF data for {fileNameIn}: {e}\n")

    # Rename file
    if not args.test:
        src_path = os.path.join(dirName, fileNameIn)
        dest_path = os.path.join(dirName, fileNameFinal)
        try:
            os.rename(src_path, dest_path)
            log_file.write(f"Fail ümber nimetatud: {fileNameIn} → {fileNameFinal}\n")
        except OSError as e:
            log_file.write(f"Error renaming file {fileNameIn} to {fileNameFinal}: {e}\n")
            continue

    log_file.write("\n")

# Summary
log_file.write("=" * 50 + "\n")
log_file.write(f"Kokku töödeldi {i} faili\n")
log_file.close()

input("Valmis. Klõpsa Enter väljumiseks...")
