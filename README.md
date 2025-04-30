# Failide ümbernimetamise tööriist MuISi digihoidla jaoks

See on käsurea tööriist, mis võimaldab **failide ümbernimetamist MuIS-i metaandmete alusel**, logimise, kuivkäivituse ja valikulise EXIF-andmete uuendamisega. Tööriist on kirjutatud Pythonis ja toetab EXIFTool'i kasutamist IPTC-väljade täitmiseks.

## 🎯 Eesmärk

- Ümber nimetada faile MuIS-i ID alusel.
- Küsida metaandmeid automaatselt MuIS-i RDF-liidesest.
- Salvestada tegevused logifaili.
- Soovi korral uuendada EXIF-andmeid IPTC-väljades.
- Võimalus testida "kuivkäivituse" režiimis ilma reaalse ümbernimetamiseta.

---

## 🛠 Nõuded

- Python 3.9+
- Internetiühendus (MuIS API jaoks)
- [ExifTool](https://exiftool.org/) (kui soovid EXIF-i uuendamist)
- `requests` moodul Pythonis (paigalda `pip install requests`)

---

## ⚙️ Kasutamine

### 1. Tööriista käivitamine

```bash
python3 renamer.py
