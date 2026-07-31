# Extraer Correos de PDFs → CSV (Jul 2026)

> Reference para el skill `bypass-paywall`. Patrón de post-procesamiento de PDFs descargados de Scribd u otras fuentes.

## Objetivo

Procesar un directorio de PDFs, extraer emails + nombres + teléfonos, generar dos CSVs:
1. `contacts.csv` — columnas: name, email, phone
2. `emails_only.csv` — solo emails, uno por línea, sin cabecera

## Dependencias

```bash
pip install PyMuPDF --break-system-packages  # PDF text extraction
```

## Extractor inline (no depende de file_processor.py)

El `file_processor.py` del proyecto `ScraperDorksContancs` tiene un bug: falta `Optional` en los imports (`NameError: name 'Optional' is not defined`). Usar extractor inline:

```python
import fitz  # PyMuPDF
import re, csv

class ContactExtractor:
    def __init__(self):
        self.email_pattern = re.compile(
            r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
            r"@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+"
            r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?",
            re.VERBOSE
        )
        self.phone_patterns = {
            'peru_mobile': re.compile(r'\+51\s?9\d{8}\b'),
            'peru_landline': re.compile(r'\+51\s?(?:\d{2}|\d{1})\s?\d{3,4}\s?\d{4}\b'),
            'peru_short': re.compile(r'\b9\d{8}\b'),
            'generic': re.compile(r'\b(?:\d{2,3}[-.\s]?){2,3}\d{4}\b'),
            'intl': re.compile(r'\+(?:[1-9]\d{0,2})\s?\d{4,14}\b'),
        }
        self.name_patterns = [
            re.compile(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,4}\b'),
            re.compile(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b'),
        ]

    def extract_from_pdf(self, filepath):
        doc = fitz.open(str(filepath))
        all_text = ""
        for page_num in range(min(len(doc), 50)):  # limit 50 pages for speed
            page = doc.load_page(page_num)
            all_text += page.get_text() + "\n"
        doc.close()
        return self._extract(all_text)

    def _extract(self, text):
        contacts = []
        seen = set()
        for match in self.email_pattern.finditer(text):
            email = match.group().lower().strip()
            if email in seen or len(email) > 254: continue
            if any(x in email for x in ['example.com', 'test.com', 'yourdomain']): continue
            seen.add(email)

            # Find nearby phone (300 chars around email)
            start = max(0, match.start() - 300)
            end = min(len(text), match.end() + 300)
            context = text[start:end]
            phone = ""
            for pattern in self.phone_patterns.values():
                phones = pattern.findall(context)
                if phones: phone = phones[0]; break

            # Find name (before email)
            before = text[max(0, match.start()-150):match.start()]
            name = ""
            for pattern in self.name_patterns:
                names = pattern.findall(before)
                if names: name = names[-1]; break

            contacts.append({'name': name, 'email': email, 'phone': phone})
        return contacts
```

## Uso

```python
extractor = ContactExtractor()
all_contacts = []
seen_emails = set()

for pdf in Path(OUTPUT_DIR).glob("*.pdf"):
    contacts = extractor.extract_from_pdf(pdf)
    for c in contacts:
        if c['email'] and c['email'] not in seen_emails:
            seen_emails.add(c['email'])
            all_contacts.append(c)

# contacts.csv
with open("contacts.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "email", "phone"])
    writer.writeheader()
    writer.writerows(all_contacts)

# emails_only.csv (sin cabecera)
with open("emails_only.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    for c in all_contacts:
        if c['email']: writer.writerow([c['email']])
```

## Resultados de prueba real (Jul 2026)

31 PDFs de directorios peruanos (Scribd) → 1064 correos únicos:

| Métrica | Valor |
|---------|-------|
| PDFs procesados | 31 |
| Raw contacts (con duplicados) | 1085 |
| Unique emails | 1064 |
| Con nombre | 312 (29%) |
| Con teléfono | 821 (77%) |
| PDFs sin correos | 14 (docs legales, brochures, mapas) |

**Top PDFs por correos:**
- Concesionarios-Postales-Vigentes: 489
- Empresas-as-Del-Estado-de-Mexico-2004: 144
- DIRECTORIO-PROCURADURIAS-ANTICORRUPCION: 132
- directorio-loretooec: 128

## Pitfalls

- **PDFs escaneados/imagen**: PyMuPDF extrae texto nativo. PDFs que son imágenes escaneadas devuelven 0 texto. Necesitarían OCR (Tesseract + pdf2image).
- **Límite 50 páginas**: balance velocidad vs exhaustividad. Directorios suelen tener emails en primeras páginas.
- **Falsos positivos de teléfono**: números de DNI/RUC pueden matchear como teléfonos genéricos. Priorizar patrones peruanos específicos (`+51 9...`, `9\d{8}`).
- **Nombres solo mayúsculas iniciales**: el regex de nombres solo captura `Nombre Apellido`. Si el PDF tiene nombres en MAYÚSCULAS, no los captura.
- **encoding utf-8-sig**: BOM para compatibilidad Excel en Windows.

## Template completo

Script completo en: `/mnt/d/PyCode/SkillScribidDown/extract_contacts.py`