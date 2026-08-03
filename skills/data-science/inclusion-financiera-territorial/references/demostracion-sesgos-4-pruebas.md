# Demostración Matemática de 4 Sesgos en Modelos de Inclusión Financiera

**Script de referencia:** `_demostracion_sesgos.py`

## Prueba 1: Variables Proxy Discriminatorias

5 de 6 variables correlacionan r>0.5 con ruralidad. La más crítica: `Sin_internet` (r=0.94).

**Consecuencia:** El modelo usa "falta de internet" como proxy de "ruralidad", no como medición real de conectividad.

## Prueba 2: Sesgo Geográfico del IVCD

IVCD urbano: +0.098 vs IVCD rural: -0.251 (diferencia 0.35, p=0.0000). **Ningún distrito rural recibe GO.**

## Prueba 3: Error Desigual del ML

Error en urbano: 0.040 vs Error en rural: 0.492 (12.2x más). 14 falsos NO-GO en rural, 0 en urbano.

## Prueba 4: Feedback Loop

55.7% de rurales con CMAC no mejora en 5 periodos. La desigualdad se replica exactamente.

## Código de reproducción

```python
# Reproducir las 4 pruebas con datos sintéticos realistas
# Ver Papers/_demostracion_sesgos.py
```
