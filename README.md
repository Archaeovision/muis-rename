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

- Python 3.9+ (kui kasutada lähtekoodi)
- Internetiühendus (MuIS API jaoks)
- [ExifTool](https://exiftool.org/) (kui soovid EXIF-i uuendamist)
- `requests` moodul Pythonis (paigalda `pip install requests`)
- `pyinstaller` kui soov ise kompileerida lähtekoodi

---

## ⚙️ Kasutamine

### 1. Tööriista käivitamine kasutades lähtekoodi

```bash
python3.9 muis-rename.py
```
### 2. Tööriista käivitamine käsurealt

```bash
muis-rename
```
### Lähtekoodi kompileerimine
```bash
pyinstaller --onefile --name muis-rename muis-rename-osx.py
```

## Parameetrid
```
  -h, --help      Näitab abiteksti
  -t, --test      Lülitab sisse kuivkäivituse režiim (faile ei nimetata ümber kui luuakse logi).
  -e, --exiftool  Luba IPTC metaandmete kirjutamine Exiftooli abil.
  -c, --check     Kontrolli MuIS ID põhjal seotud failinimesid MuISi Digihoidlas
```

## 📁 Sisendfailide eeldused

Failinimed peavad sisaldama MuIS ID-d ja vajadusel järjenumbreid, näiteks:

- 123456.jpg
- 123456_1.jpg
- 123456_1_1.jpg

Tööriist eraldab ID ja säilitab ülejäänud suffixi.

## 🛡 Kaitsemehhanismid
Faili ei nimetata ümber, kui sihtfail juba eksisteerib.

Failid, mis algavad punktiga (.DS_Store, jms), jäetakse vahele.

Küsitakse kinnitust enne töö alustamist

## 📄 Logimine
Logifail luuakse igal käivitamisel töökausta: `failide_logi_YYYYMMDD_HHMMSS.txt`
Sinna salvestatakse info iga töödeldud faili kohta.

## 🧪 EXIF/IPTC andmete täitmine (valikuline)
Kui kasutad -e lippu ja süsteemis on *exiftool*, täidetakse järgmised IPTC-väljad:

- Source: MuIS ID
- ObjectName: Pealkiri (kui olemas)

