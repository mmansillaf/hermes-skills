Script de descarga de documentos CEJ con valor legal.
Usa undetected_chromedriver + CDP + ddddocr + requests.

NOTA IMPORTANTE (Junio 2026):
- El filtro PRE-desarga por contexto HTML padre NO es confiable.
  Los bloques HTML contienen resoluciones Y cedulas mezcladas.
- Mejor estrategia: descargar TODO, luego clasificar por contenido del PDF.
- El script undetected_chromedriver funciona para captcha + navegacion,
  pero las descargas a documentoD.html via requests son bloqueadas por Radware.
- Para descargar, usar el Chrome del usuario via remote-debugging:9225,
  con page_load_strategy='none' + CDP Runtime.evaluate + Network.getAllCookies.

Ubicacion: /home/usuario/Escritorio/PyCode/poder_judicial_results/download_cej_important.py
Ejecutar: source ~/cej-scraper/bin/activate && python3 download_cej_important.py
