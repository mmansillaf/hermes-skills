# Google Colab — Evaluación para El Peruano RAG

**Fecha:** 01-may-2026

## ¿Sirve para este proyecto?

| Uso | Viabilidad | Detalle |
|-----|-----------|---------|
| Demo interactiva | ✅ Excelente | Notebook compartible, sin instalación |
| Procesamiento GPU | ✅ Útil | Embeddings más rápido que CPU |
| Prototipado | ✅ Bueno | Probar nuevos modelos sin instalar |
| API producción | ❌ No | Se duerme, sin IP fija |
| Reemplazar VPS | ❌ No | Sin Docker, sin endpoints |
| Almacenamiento | ❌ No | Disco efímero |

## Planes

| | Free | Pro ($10/mes) | Pro+ ($50/mes) |
|---|---|---|---|
| RAM | 12 GB | 25 GB | 50 GB |
| GPU | T4 | V100/P100 | A100 |
| Runtime máx | 12h | 24h | 24h + bg |
| Idle timeout | ~30 min | ~90 min | Background |

## Caso de uso ideal: Demo para abogados

```python
# Notebook: "Consulta normas peruanas con IA"
# Celda 1: Instalar dependencias
!pip install requests

# Celda 2: Configurar (API key oculta con getpass)
import requests
API = "https://tu-api.com"

# Celda 3: Consulta interactiva
pregunta = input("Tu pregunta: ")  # @param {type:"string"}
resp = requests.post(f"{API}/query", json={"question": pregunta})
print(resp.json()["answer"])
```

**Ventajas:**
- El abogado no instala nada (solo abre un link)
- La API key está oculta (getpass o secrets de Colab)
- Puede hacer múltiples consultas
- Se puede compartir como "Abrir en Colab"

## Lo que NO puede hacer Colab

- Ejecutar Docker (Qdrant, Neo4j)
- Mantener un endpoint REST 24/7
- Almacenar datos permanentemente (sin Google Drive)
- Tener IP fija para whitelisting

## Conclusión

Colab es herramienta de **demo y prototipado**, no de producción. Complementa al VPS de Contabo ($5.50/mes), no lo reemplaza.
