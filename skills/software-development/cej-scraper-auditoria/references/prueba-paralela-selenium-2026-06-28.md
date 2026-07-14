# Prueba de paralelismo con Selenium puro — 28-Jun-2026

## Contexto

Se reemplazo `undetected_chromedriver` por `selenium.webdriver.Chrome` estandar para eliminar race conditions con 2+ spiders.

## Entorno

- Chrome 149.0.7827.196
- Chromedriver: /home/usuario/.local/share/undetected_chromedriver/undetected_chromedriver (reutilizado pero NO parcheado)
- Selenium 4.45.0
- Scrapy 2.16.0
- Ubuntu 24.04.4 LTS
- 2captcha API key activa ($1.99 saldo)

## Prueba single-instance (4 expedientes)

Comando: `PJ_INPUT_FILE='input/prueba_3_exp.xlsx' PJ_SPIDER_ID='selenium_test' python3 -m scrapy crawl poder_opt`

| Expediente | Docs | PDFs | Tamaño |
|---|---|---|---|
| 00020-2021-0-1801-JR-LA-07 | 12 | 4 | 427KB + 619KB + 177KB + 135KB |
| 00026-2021-0-1801-JR-LA-08 | 2 | 0 | (solo seguimiento) |
| 00017-2021-0-1801-JR-FC-14 | 5 | 1 | 108KB |
| 00021-2021-0-1801-JR-FC-14 | 6 | 1 | 114KB |

Resultado: `finish_reason: finished`, consumo RAM ~97MB.

## Prueba paralela (2 spiders simultaneos, 2 expedientes c/u)

**Spider A** (run_A_parallel.py: offset=0, limit=2):
- `finish_reason: finished`
- 2/2 expedientes procesados
- Memoria max: 105MB

**Spider B** (run_B_parallel.py: offset=2, limit=2, lanzado 8s despues):
- `finish_reason: finished`
- 2/2 expedientes procesados, 1 PDF descargado
- Memoria max: 101MB

**Conclusion:** Selenium puro permite 2 spiders simultaneos sin race conditions. El Chromedriver del sistema no se parchea, por lo que no hay conflicto de binary.

## Contraste con undetected_chromedriver

En pruebas anteriores con `undetected_chromedriver`, siempre uno de los dos spiders fallaba con:
```
chrome_dead → ConnectionRefusedError → HTTPConnection failed
```

Razon: undetected_chromedriver descarga y parchea UN solo binary de ChromeDriver en `~/.local/share/undetected_chromedriver/`. Cuando 2 spiders se inicializan casi al mismo tiempo, ambos intentan escribir en el mismo archivo → binary corrupto.
