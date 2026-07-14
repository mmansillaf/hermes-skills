# .venv CUDA Bloat Cleanup — VPS sin GPU

## Problema

`sentence-transformers` (dependencia para embeddings) instala `torch` con CUDA por defecto. En una VPS sin GPU (VMware SVGA, Contabo VPS), esto deja ~3.4G de librerías inútiles:

```
nvidia/   (CUDA libs)    2.7G  ← basura sin GPU
triton/   (CUDA kernel)  641M  ← basura sin GPU
torch/    (CUDA overhead) 954M  ← parcialmente utilizable
Total:                    ~4.3G innecesarios
```

## Diagnóstico

```bash
# Verificar tamaño del .venv
du -sh /opt/elperuano/.venv/

# Verificar qué paquetes ocupan más
du -sh /opt/elperuano/.venv/lib/python3.1*/site-packages/nvidia/ \
      /opt/elperuano/.venv/lib/python3.1*/site-packages/triton/ \
      /opt/elperuano/.venv/lib/python3.1*/site-packages/torch/

# Verificar si hay GPU
lspci | grep -i 'vga\|nvidia'
nvidia-smi  # si no existe, no hay GPU
```

## Solución: recrear .venv con torch CPU-only

```bash
cd /opt/elperuano

# 1. Eliminar .venv inflado
rm -rf .venv

# 2. Instalar python3-venv si no existe
sudo apt-get install -y python3-venv

# 3. Crear venv limpio
python3 -m venv .venv
source .venv/bin/activate

# 4. Instalar torch CPU-only ANTES que cualquier otra dependencia
pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch

# 5. Instalar el resto (sentence-transformers NO reinstalará torch CUDA)
pip install --no-cache-dir sentence-transformers transformers \
    qdrant-client neo4j groq fastapi uvicorn pydantic \
    python-dotenv beautifulsoup4 lxml tqdm markdownify \
    pandas numpy scipy click rich PyMuPDF pdfplumber pyyaml \
    pytest pytest-asyncio requests

# 6. Verificar
python3 -c 'import torch; print("Torch", torch.__version__, "CUDA:", torch.cuda.is_available())'
# Debe imprimir: Torch X.X.X+cpu CUDA: False
```

## Resultado

| Métrica | Antes | Después |
|---------|-------|---------|
| .venv tamaño | 5.5G | ~1.5G |
| Torch CUDA | True | False |
| Disco total usado | 99% (358MB libre) | 84% (~5GB libre) |

## Pitfall: orden de instalación

El orden importa. Si se instala `sentence-transformers` primero, pip resuelve la dependencia `torch` con la versión CUDA. Instalar `torch` CPU-only manualmente ANTES de `sentence-transformers` para que pip vea la dependencia satisfecha y no intente reinstalar.

## Limpieza adicional

```bash
# Snap versions viejas (pueden ocupar 500M-1G)
snap list --all | grep disabled
sudo snap remove --revision OLD_REV PACKAGE_NAME

# HuggingFace cache
rm -rf ~/.cache/huggingface/

# Apt cache
sudo apt clean
sudo apt autoremove -y
```
