# Batch de 15 preguntas — script de referencia

## Script probado que funciona (bash, subprocess secuencial)

Archivo: `scripts/bateria_15.sh`

Funciona pero es lento (~36 min para 15 queries) porque cada subprocess recarga
el modelo Sentence-Transformer desde HuggingFace.

## Script alternativo más rápido (Python, modelo compartido)

Archivo: `scripts/bateria_15_directa.py`

Llama `run_console_query()` directo — el modelo se carga UNA vez.
Pero tiene un bug: `contextlib.redirect_stdout` es incompatible con el async generator
del synthesizer. El fix es usar `sys.stdout = open(os.devnull, 'w')` en vez de redirect_stdout.

## Distribución de niveles

Diseñar baterías con 3 niveles de dificultad:

| Nivel | Tipo | Ejemplo |
|---|---|---|
| simple | Factual/definición | "¿Qué es el proceso de amparo?" |
| medio | Doctrinal/interpretativo | "¿Cuáles son los requisitos de procedencia del recurso de casación?" |
| complejo | Análisis multi-parte | "Análisis comparativo: criterios de admisibilidad del amparo en materia previsional vs laboral" |

## Métricas por nivel (batería jun 2026)

| Nivel | Promedio chars/respuesta | Promedio tiempo |
|---|---|---|
| simple | 4,795 | ~140s |
| medio | 6,009 | ~147s |
| complejo | 6,822 | ~145s |

Las complejas producen ~42% más texto que las simples, con tiempo similar.
