# Auditoría del Informe Smart Money — Julio 2026

## Resumen de hallazgos

### ✅ Fortalezas (5)
1. Estructura de 3 canales (13F / Order Flow / On-Chain)
2. 13 papers arXiv con IDs verificables
3. Crítica honesta del SMC (sección 4.6)
4. Datos IIF detallados mes por mes
5. Advertencias finales claras

### 🔴 Debilidades críticas (5)
1. **QUÉ vs CÓMO**: Describe Smart Money pero no cómo actuar
2. **Brecha 13F**: 45 días de lag no resuelta
3. **Mappings SMC→Academia forzados** (Kyle 1985 no habla de Order Blocks)
4. **Cero backtesting** en 993 líneas
5. **Costo herramientas ignorado** (no menciona alternativas gratuitas)

### ✅ Debilidades resueltas (Jul 2026)
7. ~~Behavioral Finance ausente~~ → ✅ **RESUELTO**: Dimensión 8 expandida con tabla de 8 sesgos, datos duros, papers (Barber & Odean, Kahneman & Tversky, Thaler), mecanismos de explotación, y evidencia contraria. Referencia completa en `references/behavioral-finance-smart-money.md`.

### 🟠 Debilidades significativas (4 pendientes)
6. No explora cómo compite el retail (ventajas asimétricas)
8. DeFi microstructure ignorada (MEV, flash loans)
9. Alternative Data no cubierta
10. Numeración "10.7" duplicada

### 🟡 Zonas grises (3)
- Debate EMH: si el mercado es eficiente (Fama), no hay Smart Money
- Order flow institucional no es replicable por retail (Kang usó 2.7M obs.)
- Stablecoins como canal: GENIUS Act + MiCA pueden cerrarlo en 2027

### 🆕 Perspectivas no cubiertas (4)
- Alternative Data (satellite, credit cards, job postings)
- Reinforcement Learning compitiendo contra retail
- Smart Money Index práctico (combinar 3 fuentes en score)
- Conexión con LegalTech (litigation finance como Smart Money)
