# 6 Estrategias Cuantitativas de Gamma Exposure (GEX)

## Estrategia 1: The Gamma Pin (Venta de Premium)
- **Condición:** SPY/QQQ en GEX positivo, precio dentro de 0.5% del Call Wall, VIX bajo, sin eventos macro
- **Lógica:** Dealers compran caídas y venden alzas mecánicamente. El precio queda "clavado" (pinned).
- **Trade:** Iron condors o short strangles centrados en el Call Wall.
- **Stop:** Si precio rompe el Call Wall con volumen >1.5× media.

## Estrategia 2: The Gamma Flip Breakout
- **Condición:** Precio acercándose al Gamma Flip desde arriba, GEX negativo construyéndose debajo
- **Lógica:** Cruzar el flip cambia el régimen de estabilización a amplificación.
- **Trade:** Put spreads o short shares debajo del flip. El flip es la línea en la arena.
- **Stop:** Si precio vuelve por encima del flip + 0.5 ATR.

## Estrategia 3: The TSLA Gamma Squeeze
- **Condición:** TSLA en GEX negativo, precio acercándose al Call Wall desde abajo, momentum fuerte
- **Lógica:** Romper el Call Wall en gamma negativo fuerza a dealers a comprar → loop de retroalimentación.
- **Trade:** Calls ligeramente OTM cuando el precio rompe el Call Wall con volumen.
- **Target:** 5-10% de movimiento (común en TSLA).

## Estrategia 4: Post-FOMC Vanna Rally
- **Condición:** Día FOMC, VEX positivo alto en SPY, VIX esperado caer post-anuncio
- **Lógica:** Caída de IV desencadena ajustes vanna-driven. Los dealers crean oferta mecánica 1-3 días.
- **Trade:** SPY calls 30-60 min post-statement (después de que la reacción inicial se asiente).

## Estrategia 5: 0DTE Charm Drift
- **Condición:** Día de expiración 0DTE, OI concentrado en pocos strikes, CHEX fuertemente direccional
- **Lógica:** El decay delta-driven (charm) fuerza un drift direccional que persiste por la tarde.
- **Trade:** A la 1 PM ET: CHEX negativo total = drift alcista (calls). CHEX positivo = drift bajista (puts).

## Estrategia 6: Expiry Friday Pin
- **Condición:** Viernes de expiración mensual/semanal, GEX positivo, precio cerca de max pain
- **Lógica:** Opciones expirando convergen a max pain a medida que el hedging gamma se intensifica.
- **Trade:** Iron butterflies centrados en max pain al apertura. Cerrar antes de las 3 PM ET.

---

**Fuente:** Conceptos_v2/sm5.txt — investigación de subagente sobre estrategias cuantitativas GEX (Jul 2026).
