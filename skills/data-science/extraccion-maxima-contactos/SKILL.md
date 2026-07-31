---
name: extraccion-maxima-contactos
description: Metodologia completa para extraccion masiva de contactos (email, telefono, nombre, cargo) desde fuentes web, OSINT, Active Directory, Office 365, breach databases, y fuentes peruanas. Abarca Google Dorks, scraping, APIs, verificacion, y tecnicas de bypass.
---

# Extraccion Maxima de Contactos

Metodologia integral para extraer la maxima cantidad de datos de contacto por cualquier medio tecnico disponible: OSINT pasivo, scraping web, enumeracion de directorios corporativos (AD/O365), breach databases, fuentes gubernamentales, y tecnicas avanzadas de generacion/verificacion.

## Fases de ejecucion (orden optimo)

### Fase 0: OSINT Pasivo (legal, sin trafico al objetivo)
- theHarvester: `-d dominio.com -b all -l 1000`
- crt.sh: `curl -s "https://crt.sh/?q=%.dominio.com&output=json" | jq -r '.[].name_value'`
- Google Dorks (ver catalogo en `references/google-dorks.md`)
- Shodan / Censys / Wayback Machine CDX API
- GitHub dorking: `site:github.com "dominio.com" (password OR api_key OR smtp)`

### Fase 1: Scraping Web (datos publicos)
- peru_contact_scraper (539 dorks, 3 backends, ubicado en D:\PyCode\ScraperDorksContancs\peru_contact_scraper\)
- Google Maps scraper para negocios B2B
- vCard/VCARD + CardDAV discovery
- Calendar .ics scraping (listas de asistentes)
- npm/PyPI maintainer emails

### Fase 2: Verificacion Activa
- GetCredentialType (O365): `curl -d '{"Username":"usuario@dominio.com"}' https://login.microsoftonline.com/common/GetCredentialType`
- SMTP RCPT TO / VRFY / EXPN
- WHOIS historico + reverso (WhoisXML, DomainTools)
- 10 APIs gratuitas: Hunter.io, Snov.io, Clearbit, FindThatEmail, etc.
- Email pattern generation + verificacion masiva

### Fase 3: Breaches y Leaks
- h8mail contra todos los servicios (DeHashed, IntelX, HIBP, SnusBase)
- HaveIBeenPwned API v3 (Stealer Logs — nuevo Julio 2026)
- Pastebin/psbdmp search de dominios objetivo
- SSL certificate email extraction via crt.sh

### Fase 4: AD/O365 (requiere autorizacion)
- LDAP anonymous bind: `ldapsearch -x -H ldap://DC_IP -b "DC=dominio,DC=com" "(objectClass=*)" mail telephoneNumber`
- Kerbrute user enum + AS-REP roasting
- ADWS bypass (SOAPHound, ADWSHound) — evade monitoreo LDAP
- ROADtools/Graph API post-auth
- BloodHound/SharpHound + AzureHound

### Fase 5: Correlacion y Enriquecimiento
- Cruzar emails de TODAS las fuentes
- user-scanner (verificacion en 290+ sitios)
- Sherlock (redes sociales)
- Apollo.io / Lusha / ContactOut para enriquecimiento
- HaveIBeenPwned individual
- Exportar CSV unificado con source_file y confidence_score

## Herramientas imprescindibles

| Herramienta | Instalacion | Uso |
|---|---|---|
| theHarvester | `apt install theharvester` | OSINT pasivo multi-fuente |
| h8mail | `pip3 install h8mail` | Consulta unificada de breaches |
| user-scanner | git clone + pip | Verificacion en 290+ sitios |
| ldapsearch | `apt install ldap-utils` | LDAP enumeration |
| Kerbrute | GitHub releases | Kerberos user enum |
| ROADtools | `pip install roadtools` | Azure AD enumeration |
| msmailprobe2 | git clone + go build | Exchange/O365 enumeration |
| ExifTool | `apt install exiftool` | Metadatos 400+ formatos |
| Sherlock | git clone + pip | Username search 400+ redes |
| peru_contact_scraper | D:\PyCode\ScraperDorksContancs\ | 539 dorks para Peru |

## Bypass de defensas

- **Monitoreo LDAP:** Usar ADWS (TCP/9389) con SOAPHound/ADWSHound
- **Logs de auditoria Windows:** LDAP Ping sobre UDP con ldapnomnom
- **Deteccion de auth fallida:** Kerberos pre-auth con Kerbrute (no cuenta como login)
- **Rate limiting O365:** Delays aleatorios + rotacion de User-Agent + proxies
- **Bloqueo de IP:** Proxies residenciales (Bright Data $10/GB, IPRoyal $7/GB)
- **MFA:** Device Code phishing, PRT cookie theft (ROADtools)
- **CAPTCHA:** 2captcha + delays gaussianos + rotacion de fingerprints

## Fuentes peruanas (ver references/peru-fuentes.md)

- OSCE/SEACE: 50-100K contratistas con RUC, telefono, email
- Colegios profesionales: CAL (80K+), CIP, CMP, Notarios
- apis.net.pe: API de RUC/DNI masivo
- SUNAT RUC, SUNARP, JNE hojas de vida
- Indecopi SPC, Marcas, Barreras Burocraticas
- Paginas Amarillas Peru (200K+)

## Consideraciones legales (Peru)
- Ley 29733: Proteccion de Datos Personales
- Ley 30096: Delitos Informaticos (Art. 2, 3, 6)
- Ley 27806: Transparencia — datos de funcionarios publicos SON publicos
- Legal: OSINT pasivo, APIs publicas, registros oficiales, WHOIS
- Ilegal: acceso no autorizado, compra/venta de datos robados, suplantacion
- Zona gris: email pattern brute-force, scraping de redes sociales, bypass de CAPTCHAs

## Ver tambien
- `references/google-dorks.md`: Catalogo completo de Google Dorks
- `references/peru-fuentes.md`: Fuentes peruanas detalladas con URLs y volumenes
- `references/tecnicas-osadas.md`: 12 categorias de tecnicas avanzadas (breaches, HubSpot, npm, .ics, etc.)
