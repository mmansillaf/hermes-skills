# Windows Deployment Troubleshooting — Word Add-in

Common issues when deploying Hermes Word Add-in on Windows.

## 1. Panel en blanco (HTTPS)

**Sintoma:** El task pane carga en blanco o no muestra el frontend.

**Causa:** Word exige HTTPS para add-ins en produccion. Durante desarrollo con sideload, HTTP funciona pero puede fallar segun la version de Word.

**Diagnostico:**
1. Abrir http://localhost:8765 en el navegador
2. Si carga ahi pero no en Word → problema de HTTPS

**Solucion:** Usar ngrok para tunnel HTTPS:
```powershell
ngrok http 8765
# Actualizar manifest.xml con la URL de ngrok
```

## 2. Firewall bloquea el puerto

```powershell
netsh advfirewall firewall add rule name="Hermes Word" dir=in action=allow protocol=TCP localport=8765
```

## 3. Documentos grandes cuelgan al leer

Office.js `getOoxml()` tiene limite ~10MB. Para docs >50 paginas:
- Copiar y pegar solo la seccion relevante
- Alternativa: usar python-docx para extraccion en vez de Office.js

## 4. getOoxml() corrupcion

- No apto para round-trip sin validacion
- Usar getHtml() para docs que necesitan ida y vuelta
- Para operaciones criticas, usar che-word-mcp (byte-perfect)
