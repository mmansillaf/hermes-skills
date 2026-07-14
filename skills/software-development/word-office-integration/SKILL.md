---
name: word-office-integration
description: "Integracion Hermes-Word: (A) CLI: leer/crear/modificar .docx via python-docx sin Word instalado. (B) IN-APP: panel de chat dentro de Word via Office Web Add-in + Office.js API + WebSocket a backend Hermes."
category: productivity
---

# Word / Office Integration for Hermes

Dos enfoques complementarios:

- **Enfoque A (CLI):** Manipular archivos .docx desde la terminal sin Word instalado — leer, crear, modificar, convertir.
- **Enfoque B (In-app):** Panel de chat dentro de Word via Office Web Add-in — lee y edita el documento activo en tiempo real.

Elige A para batch/headless, elige B para interaccion interactiva dentro de Word.

## Trigger
Cuando el usuario pide: leer/analizar/modificar/crear documentos Word, extraer texto de .docx, convertir entre docx y markdown, buscar documentos en OneDrive/SharePoint, integrar Hermes como panel de chat DENTRO de Word, crear un add-in para Word, leer/editar el documento activo en Word desde un panel lateral, investigar opciones de integracion Word-AI, MCP servers para Word, comparar enfoques de integracion Word+AI, consolidar proyecto Word-Hermes disperso, desplegar add-in en Windows desde Ubuntu, subir proyecto Word-Hermes a GitHub, activar GitHub Pages para documentacion, crear README profesional con badges, comparar Hermes con Copilot/Grammarly/ChatGPT.

## Entregables del Proyecto

El proyecto genera documentacion en **dos formatos siempre** (MD + HTML con diseno oscuro profesional) porque el usuario valora tener la version web renderizada. Entregables estandar:

- `README.md` con badges, tablas, diagrama ASCII, comparativa competitiva
- `docs/index.html` como landing page de GitHub Pages
- `docs/guia_instalacion_windows.md/.html` — guia paso a paso
- `research/informe_integracion.md/.html` — informe completo de investigacion
- `LICENSE` (MIT) y `requirements.txt`

### Competitive Landscape (para incluir en README)

| Solucion | Open Source | Custom LLM | Privacidad | Chat en Word | Precio |
|----------|:---:|:---:|:---:|:---:|---|
| Hermes Word Add-in | ✅ | ✅ | ✅ | ✅ | Gratis |
| Microsoft Copilot | ❌ | ❌ | ❌ | ✅ | $30/usr/mes |
| Grammarly | ❌ | ❌ | ❌ | ✅ | $12/usr/mes |
| ChatGPT | ❌ | ❌ | ❌ | ❌ | $20/usr/mes |

### GitHub Pages

Para proyectos de documentacion, activar GitHub Pages via API apuntando a `/docs`:

```bash
curl -X POST -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/{owner}/{repo}/pages \
  -d '{"source":{"branch":"main","path":"/docs"}}'
```

La URL resultante es `https://{owner}.github.io/{repo}/`. El build tarda ~1 minuto. La API puede reportar "errored" transitoriamente aunque el build real sea exitoso — verificar con `curl -I` a la URL final.

## Enfoque C: MCP Servers (Complementario - Headless)

Como tercera capa, integrar servidores MCP que manipulan .docx sin Word abierto. Hay 6 servidores activos analizados. Ver detalle completo en `references/mcp-servers-comparison.md`. Carga esa referencia cuando el usuario pregunte sobre MCP servers para Word o quiera comparar opciones.

Servidores destacados:
- **che-word-mcp** (Swift, macOS, 233 tools, byte-perfect round-trip, Track Changes programaticos) — mas potente
- **office-word-mcp-server** (Python, cross-platform, 50+ tools, PyPI) — mas popular (★1902) pero archivado
- **OfficeMCP** (Python+COM, Windows, suite completa) — requiere Office instalado

Ejemplo de configuracion MCP para Hermes:
```json
{
  "mcpServers": {
    "word-document-server": {
      "command": "uvx",
      "args": ["--from", "office-word-mcp-server", "word_mcp_server"]
    }
  }
}
```

## Proyecto Consolidado

El desarrollo del add-in vive en `~/hermes-word-addin/` con estructura limpia:

```
hermes-word-addin/
├── README.md              # Overview + setup instructions
├── .gitignore
├── src/
│   ├── backend_server.py  # Servidor Python (HTTP)
│   ├── frontend.html      # UI del add-in (HTML/CSS/JS + Office.js)
│   ├── manifest.xml       # Manifest para sideload en Word
│   └── convert_to_formats.py  # Conversion docx ↔ md
├── research/              # Investigacion y analisis
│   ├── informe_integracion.md/.html  # Informe completo (Abr 2026)
│   ├── feasibility_report.md         # Viabilidad tecnica
│   ├── protocol_spec.md              # Especificacion WS JSON
│   ├── architecture_diagrams.md      # Diagramas de arquitectura
│   └── word_integration_research.md  # Investigacion inicial python-docx
├── docs/                  # Documentacion adicional
└── scripts/               # Scripts de utilidad
```

## Deployment: Ubuntu → Windows

Cuando el usuario quiere desplegar en Windows desde Ubuntu:

1. El proyecto se sube a GitHub desde Ubuntu (requiere **classic token** con scope `repo`; los fine-grained NO funcionan)
2. En Windows: clonar el repo, instalar Python 3.8+, `pip install fastapi uvicorn websockets`
3. Backend: `python src/backend_server.py --port 8765` (nativo en Windows, no requiere WSL2)
4. Word: sideload del manifest.xml via Archivo > Opciones > Programador > Complementos
5. Alternativa WSL2: backend en WSL2, Word en Windows. Localhost se comparte automaticamente.

## Enfoque A: CLI file manipulation (sin Word instalado)

### Estrategia en Capas

```
Capa 1: python-docx (SIEMPRE - 90% de casos)
Capa 2: mammoth (docx -> markdown para procesar con LLM)
Capa 3: pandoc (si esta instalado - mejor conversion, preserva tablas)
Capa 4: Microsoft Graph API (documentos cloud OneDrive/SharePoint)
Capa 5: COM/pywin32 (solo Windows, solo si Word instalado)
```

## Enfoque B: Word Add-in Chat Panel (requiere Word abierto)

Integra Hermes como panel lateral de chat DENTRO de Word. Usa Office Web Add-ins (HTML/JS + Office.js) multiplataforma (Word 2016+ Windows/Mac/Online/iPad). Multiplataforma sin Word instalado.

```
┌─────────────────────────────────────────┐
│  WORD (Windows / Mac / Online)          │
│  ┌───────────────────────────────────┐  │
│  │  Task Pane (panel lateral)        │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  UI Chat (HTML/CSS/JS)      │  │  │
│  │  │  Historial + input + botones│  │  │
│  │  └─────────────────────────────┘  │  │
│  │           ↕ Office.js API         │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Documento activo           │  │  │
│  │  │  Leer: body.getOoxml()      │  │  │
│  │  │  Escribir: insertText()     │  │  │
│  │  │  Seleccion: getSelection()  │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│            ↕ HTTP/WebSocket              │
│  ┌───────────────────────────────────┐  │
│  │  Backend Hermes (localhost)       │  │
│  │  - Recibe OOXML/HTML del doc     │  │
│  │  - Procesa con LLM               │  │
│  │  - Devuelve respuesta/cambios    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Office.js APIs clave

```javascript
// Leer todo el documento como OOXML (XML completo)
await Word.run(async (context) => {
    const body = context.document.body;
    const ooxml = body.getOoxml();  // XML estructurado
    const html = body.getHtml();    // Alternativa HTML
    const text = body.text;         // Solo texto plano
    await context.sync();
    sendToHermes(ooxml.value);
});

// Insertar texto donde esta el cursor
await Word.run(async (context) => {
    const selection = context.document.getSelection();
    selection.insertText("Texto Hermes", Word.InsertLocation.replace);
    await context.sync();
});

// Insertar al final del documento
await Word.run(async (context) => {
    const body = context.document.body;
    body.insertText("\nNuevo contenido", Word.InsertLocation.end);
    await context.sync();
});

// Insertar al inicio
await Word.run(async (context) => {
    const body = context.document.body;
    body.insertText("Prefacio\n", Word.InsertLocation.start);
    await context.sync();
});
```

### Comunicacion con backend Hermes

```javascript
// Opcion 1: REST API
async function sendToHermesRest(documentContent) {
    const response = await fetch('http://localhost:8765/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            document: documentContent,
            message: userMessage
        })
    });
    return response.json();
}

// Opcion 2: WebSocket (tiempo real, sesion persistente)
const ws = new WebSocket('ws://localhost:8765/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    addToChatHistory(data.response);
};
ws.send(JSON.stringify({ document: ooxml, message: userPrompt }));

// Opcion 3: Server-Sent Events para streaming
const eventSource = new EventSource('http://localhost:8765/stream');
```

### Estructura del proyecto add-in

El proyecto consolidado esta en `~/hermes-word-addin/`:

```
hermes-word-addin/
├── README.md              # Overview + setup instructions
├── .gitignore
├── src/
│   ├── backend_server.py  # Servidor Python (HTTP en :8765)
│   ├── frontend.html      # UI del add-in (HTML/CSS/JS + Office.js)
│   ├── manifest.xml       # Manifest para sideload en Word
│   └── convert_to_formats.py  # Conversion docx ↔ md
├── research/              # Investigacion y analisis
│   ├── informe_integracion.md/.html  # Informe completo
│   ├── feasibility_report.md
│   ├── protocol_spec.md
│   ├── architecture_diagrams.md
│   └── word_integration_research.md
├── docs/                  # Documentacion adicional
└── scripts/               # Scripts de utilidad
```

### Manifest XML minimo

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="TaskPaneApp">
  <Id>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>Hermes Agent</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName>Hermes Chat</DisplayName>
  <Description>AI chat panel for Word</Description>
  <Hosts>
    <Host Name="Document"/>
  </Hosts>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:3000/taskpane.html"/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
</OfficeApp>
```

### Backend Hermes: Implementacion Real (http.server + Multi-Proveedor)

El prototipo funcional usa `http.server` de stdlib (no FastAPI) porque es suficiente para HTTP simple y no requiere dependencias extra. Sirve frontend.html en `GET /` y expone `POST /chat`. Corre nativo en Windows sin WSL2.

**Multi-proveedor via variables de entorno.** El backend soporta 4 proveedores usando el mismo patron OpenAI-compatible. Se configura con:

| Variable | Proposito | Ejemplo |
|----------|-----------|---------|
| `LLM_PROVIDER` | deepseek \| openai \| anthropic \| openai-compatible | `deepseek` |
| `LLM_MODEL` | Override del modelo default | `gpt-4o` |
| `LLM_BASE_URL` | URL base para openai-compatible | `http://localhost:11434/v1/chat/completions` |
| `DEEPSEEK_API_KEY` | Key para DeepSeek | `sk-...` |
| `OPENAI_API_KEY` | Key para OpenAI | `sk-...` |
| `ANTHROPIC_API_KEY` | Key para Anthropic | `sk-ant-...` |
| `LLM_API_KEY` | Key generica para openai-compatible | `gsk_...` o `ollama` |

**Diferencias entre proveedores (PITFALLS):**
- **Anthropic** usa header `x-api-key` + `anthropic-version`, NO `Authorization: Bearer`. El body tiene `system` como campo separado, no como role en `messages`. La respuesta se parsea de `data['content'][0]['text']`, no de `choices[0].message.content`.
- **OpenAI-compatible** cubre Ollama, Groq, Together, vLLM, llama.cpp, y cualquier endpoint que implemente `/v1/chat/completions`. Ollama no requiere API key real (usar `ollama` como placeholder).

**Ejemplo: Ollama local (gratis, sin internet)**

```powershell
$env:LLM_PROVIDER="openai-compatible"
$env:LLM_BASE_URL="http://localhost:11434/v1/chat/completions"
$env:LLM_MODEL="llama3.1:8b"
$env:LLM_API_KEY="ollama"
```

**Ejemplo: Groq (gratis, 30 req/min)**

```powershell
$env:LLM_PROVIDER="openai-compatible"
$env:LLM_BASE_URL="https://api.groq.com/openai/v1/chat/completions"
$env:LLM_API_KEY="gsk_tu-key"
$env:LLM_MODEL="llama-3.1-8b-instant"
```

**Codigo del backend (version simplificada del patron):**

```python
PROVIDER = os.environ.get('LLM_PROVIDER', 'deepseek')

PROVIDER_CONFIG = {
    'deepseek': {
        'url': 'https://api.deepseek.com/v1/chat/completions',
        'model': os.environ.get('LLM_MODEL', 'deepseek-chat'),
        'api_key': os.environ.get('DEEPSEEK_API_KEY', ''),
        'auth_header': 'Bearer {key}',
        'parse_response': lambda data: data['choices'][0]['message']['content'],
    },
    'anthropic': {
        'url': 'https://api.anthropic.com/v1/messages',
        'model': os.environ.get('LLM_MODEL', 'claude-sonnet-4-20250514'),
        'api_key': os.environ.get('ANTHROPIC_API_KEY', ''),
        # ⚠️ Anthropic NO usa Authorization: Bearer
        'extra_headers': lambda: {
            'x-api-key': os.environ.get('ANTHROPIC_API_KEY', ''),
            'anthropic-version': '2023-06-01',
        },
        # ⚠️ Anthropic: system es campo separado, no role en messages
        'body': lambda model, messages: {
            'model': model,
            'system': messages[0]['content'] if messages[0]['role'] == 'system' else '',
            'messages': [m for m in messages if m['role'] != 'system'],
            'max_tokens': 2000,
        },
        # ⚠️ Anthropic: respuesta en content[0].text, no choices[0].message
        'parse_response': lambda data: data['content'][0]['text'],
    },
    'openai-compatible': {
        'url': os.environ.get('LLM_BASE_URL', 'http://localhost:8080/v1/chat/completions'),
        'model': os.environ.get('LLM_MODEL', 'llama-3.1-8b-instruct'),
        'api_key': os.environ.get('LLM_API_KEY', ''),
        'auth_header': 'Bearer {key}',
        'parse_response': lambda data: data['choices'][0]['message']['content'],
    },
}

def call_llm(prompt, document_text=''):
    cfg = PROVIDER_CONFIG.get(PROVIDER)
    if not cfg or not cfg['api_key']:
        return local_analysis(prompt, document_text)
    # ... HTTP request usando urllib con los headers y body del provider
```

**Sin API key → modo local.** Si no hay key configurada, el backend devuelve analisis basico del documento (conteo de palabras, lineas, caracteres, primeras lineas). Util para testing sin depender de APIs externas.

**Health check incluye info del provider.** `GET /health` devuelve:
```json
{
  "status": "ok",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "has_api_key": true
}
```

### Opciones de implementacion

| Opcion | Dificultad | Tiempo | Notas |
|--------|-----------|--------|-------|
| Add-in HTML/JS + llamada directa a API LLM | Baja | 2-3 dias | Sin backend Hermes, el add-in llama a OpenAI/DeepSeek directo |
| Add-in HTML/JS + REST API a Hermes local | Media | 3-4 dias | Hermes expone endpoints REST en localhost |
| Add-in HTML/JS + WebSocket a Hermes local | Media | 4-5 dias | Comunicacion bidireccional, sesion persistente |
| VSTO (.NET, solo Windows) | Alta | 1-2 semanas | Mas poderoso pero solo Windows, requiere Visual Studio |

### Proyectos open source existentes (todos basicos)

- Lenand2/chatgpt-office-addin: solo UI HTML + llamada fetch a OpenAI, no usa Office.js
- jgramlange/office-addin-chatgpt: taskpane.html + JS simple, no lee/escribe documento
- No existe un proyecto open source completo que lea+edite el documento activo via Office.js

### Pitfalls del Enfoque B

- **HTTPS requerido para desarrollo**: Office solo carga add-ins desde HTTPS (incluso localhost). Usar certificado autofirmado o ngrok.
- **Office.js es asincrono**: Modelo request/context.sync() - no es async/await normal. Curva de aprendizaje.
- **OOXML es complejo**: getOoxml() devuelve XML enorme con namespaces. Parsearlo del lado Hermes requiere logica dedicada. Alternativa: getHtml() es mas simple.
- **Limite de tamano en getOoxml()**: Documentos muy grandes pueden exceder limites. Considerar envio por secciones.
- **El add-in solo funciona con Word abierto**: No es headless. El usuario debe tener el documento abierto en Word.
- **Sideload del manifest**: En desarrollo se carga el manifest manualmente (Shared Folder o npm run start con yo office).
- **El add-in requiere hosting web**: No es un archivo local. Necesita un servidor (puede ser localhost) sirviendo los archivos HTML/JS.

## Dependencias

**Enfoque A (CLI):**
**Enfoque A (CLI):**
```bash
pip install python-docx mammoth docx2txt
# Opcionales:
# pip install msal requests  # para Graph API
# pip install pywin32        # solo Windows + Word
# sudo apt install pandoc    # conversion mejorada
```

**Enfoque B (Word Add-in):**
```bash
# Backend Hermes (Python)
pip install fastapi uvicorn websockets

# Desarrollo del add-in (Node.js)
npm install -g yo generator-office
yo office  # Wizard para crear el proyecto add-in

# HTTPS local (certificado autofirmado)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Alternativa: ngrok para tunnel HTTPS publico
# ngrok http https://localhost:3000
```

## Flujos Principales

### 1. Leer documento .docx

```python
from docx import Document
import mammoth

def read_docx(path):
    """Leer .docx y retornar contenido como Markdown y datos estructurados"""
    doc = Document(path)
    
    # Estructura completa (parrafos, tablas, formato)
    paragraphs = []
    for p in doc.paragraphs:
        paragraphs.append({
            'text': p.text,
            'style': p.style.name if p.style else 'Normal',
            'runs': [{'text': r.text, 'bold': r.bold, 'italic': r.italic} for r in p.runs]
        })
    
    tables = []
    for t in doc.tables:
        tables.append([[cell.text for cell in row.cells] for row in t.rows])
    
    # Conversion a Markdown (para que el LLM lo procese)
    with open(path, 'rb') as f:
        md_result = mammoth.convert_to_markdown(f)
    
    return {
        'markdown': md_result.value,
        'paragraphs': paragraphs,
        'tables': tables,
        'sections': len(doc.sections)
    }
```

### 2. Crear .docx desde Markdown

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor
import re

def markdown_to_docx(md_text, output_path, template_path=None):
    """Convierte Markdown a .docx usando python-docx"""
    doc = Document(template_path) if template_path else Document()
    
    lines = md_text.split('\n')
    for line in lines:
        line = line.rstrip()
        
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif re.match(r'^\d+\.\s', line):
            doc.add_paragraph(re.sub(r'^\d+\.\s', '', line), style='List Number')
        elif line.strip() == '---':
            p = doc.add_paragraph()
            p.add_run('_' * 60)
        elif line.strip() == '':
            pass
        else:
            doc.add_paragraph(line)
    
    doc.save(output_path)
    print(f"Creado: {output_path}")
```

### 3. Modificar documento existente

```python
from docx import Document
from docx.shared import Inches

def modify_docx(path, output_path, changes):
    """
    Modifica un .docx. changes es un dict:
    {
        'replace_text': {'viejo': 'nuevo'},
        'add_paragraphs': ['parrafo1', 'parrafo2'],
        'add_table': [['Col1', 'Col2'], ['dato1', 'dato2']],
        'add_image': '/path/to/image.png',
        'remove_paragraphs_matching': 'texto a buscar'
    }
    """
    doc = Document(path)
    
    if 'replace_text' in changes:
        for old, new in changes['replace_text'].items():
            for p in doc.paragraphs:
                if old in p.text:
                    p.text = p.text.replace(old, new)
    
    if 'add_paragraphs' in changes:
        for text in changes['add_paragraphs']:
            doc.add_paragraph(text)
    
    if 'add_table' in changes:
        data = changes['add_table']
        table = doc.add_table(rows=len(data), cols=len(data[0]))
        table.style = 'Light Grid Accent 1'
        for i, row_data in enumerate(data):
            for j, cell_text in enumerate(row_data):
                table.cell(i, j).text = cell_text
    
    if 'add_image' in changes:
        doc.add_picture(changes['add_image'], width=Inches(5.0))
    
    if 'remove_paragraphs_matching' in changes:
        target = changes['remove_paragraphs_matching']
        for p in doc.paragraphs:
            if target.lower() in p.text.lower():
                p._element.getparent().remove(p._element)
    
    doc.save(output_path)
    print(f"Modificado: {output_path}")
```

### 4. Extraer solo texto (rapido)

```python
import docx2txt

def extract_text(path):
    """Extrae todo el texto de un .docx, incluyendo OCR basico de imagenes"""
    return docx2txt.process(path)
```

### 5. Conversion con pandoc (si disponible)

```python
import subprocess
import os

def pandoc_convert(input_path, output_path, from_fmt=None, to_fmt=None):
    """Convierte documentos usando pandoc si esta instalado"""
    if not os.path.exists(input_path):
        return None
    
    cmd = ['pandoc', input_path, '-o', output_path]
    if from_fmt: cmd.extend(['-f', from_fmt])
    if to_fmt: cmd.extend(['-t', to_fmt])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return output_path
    return None

# pandoc_convert('doc.docx', 'doc.md', 'docx', 'markdown')
# pandoc_convert('doc.md', 'doc.docx', 'markdown', 'docx')
```

### 6. Documentos avanzados (headers, footers, secciones, margenes)

```python
from docx import Document
from docx.shared import Inches, Pt, Cm

def create_professional_docx(output_path, title, content_md, author="Hermes Agent"):
    """Crea documento profesional con headers, footers y formato"""
    doc = Document()
    
    doc.core_properties.author = author
    
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    
    header = section.header
    header.paragraphs[0].text = title
    
    footer = section.footer
    footer.paragraphs[0].text = "Generado por Hermes Agent"
    
    doc.add_heading(title, level=1)
    
    lines = content_md.split('\n')
    for line in lines:
        line = line.rstrip()
        if line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('- '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line.strip():
            doc.add_paragraph(line)
    
    doc.save(output_path)
    print(f"Documento profesional creado: {output_path}")
```

## Pitfalls

- **mammoth aplana tablas**: Si necesitas preservar tablas en conversion docx->markdown, usa pandoc. Si pandoc no esta, extrae las tablas separadamente con python-docx.
- **pip install bloqueado en sistema**: Usa venv: `python -m venv .venv-word && source .venv-word/bin/activate && pip install python-docx mammoth`
- **Archivos .doc legacy**: python-docx no soporta .doc (solo .docx). Convierte con LibreOffice: `libreoffice --headless --convert-to docx archivo.doc`
- **COM/pywin32 fragil**: Si usas COM en Windows, siempre usa `try/finally` para garantizar `word.Quit()`. Puede dejar procesos zombie.
- **Graph API requiere app registration**: No funciona out-of-the-box. Necesita configuracion previa en Azure AD.
- **GitHub tokens**: Los fine-grained tokens NO funcionan con la API REST para crear repos (HTTP 404 en /user/repos). Para operaciones de escritura via API se necesita **classic token** con scope `repo`. Alternativa: crear el repo manualmente en GitHub y pushear con token en URL.
- **Windows sin WSL2**: El backend Python corre nativo en Windows. No necesita WSL2. Solo requiere Python 3.8+ y `pip install fastapi uvicorn websockets`.
- **Sideload en Windows**: La ruta del manifest debe ser accesible desde Windows. Si el proyecto esta en WSL2, usar `\\wsl$\Ubuntu\home\usuario\hermes-word-addin\src\manifest.xml`.
- **Consolidar investigación dispersa**: Si hay multiples carpetas con research del mismo tema, consolidar en `~/hermes-word-addin/` con estructura src/research/docs/scripts. Borrar duplicados y archivos temporales (.docx de prueba, .venv, test scripts).
- **Git push pierde tracking tras set-url**: Cuando usas `git remote set-url` con token embebido para push y luego lo limpias, el upstream tracking se pierde. Solucion: `git push --set-upstream origin main` en el mismo comando con token, o usar `git remote set-url` solo para push y restaurar inmediatamente.
- **GitHub Pages API "errored" transitorio**: Al activar Pages via API, el status puede mostrar "errored" durante el primer minuto aunque el build sea exitoso. Verificar con `curl -I` a la URL final. El status se corrige solo.

## Verificacion

```python
from docx import Document
import os
doc = Document()
doc.add_paragraph("Test Hermes Word Integration")
doc.save("/tmp/hermes_test.docx")
print("OK" if os.path.exists("/tmp/hermes_test.docx") else "FAIL")
```
