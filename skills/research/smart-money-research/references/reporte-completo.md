# Smart Money — Informe Completo 2025-2026
## Versión actualizada tras auditoría (Jul 2026)

## Ubicación
El informe V1 de 50.7 KB / 993 líneas está en:
`D:\\PyCode\\hermes-skills\\SmartMoney\\INFORME_SMART_MONEY_COMPLETO.md`

## Resumen de Hallazgos de Auditoría (Jul 2026)

Tras investigación con 5 subagentes paralelos, se identificaron las siguientes brechas y correcciones:

### 🔴 Brechas Críticas en V1
1. **Falta Behavioral Finance** — El V1 describe QUÉ hace el Smart Money pero no POR QUÉ funciona. El motor causal son 8 sesgos conductuales (Barber & Odean, Kahneman & Tversky) que transfieren $50-100B/año del retail al institucional.
2. **Falta Alternative Data** — El V1 solo cubre order flow y on-chain. Pero los hedge funds top gastan $5-50M/año en alt data: satélites, tarjetas de crédito, scraping de empleos.
3. **Falta DeFi Microstructure** — El V1 cubre stablecoins pero ignora MEV ($800M-1.3B/año extraído en Ethereum/Solana), sandwich attacks, liquidations y flash loans.
4. **SMC Backtesting: FALSIFICADO** — El estudio más riguroso disponible (AaroNLaU0307, 2025) refuta el SMC como sistema: 0/210 configs sobreviven corrección, walk-forward OOS = -0.339 R negativo.
5. **Mappings Académicos INCORRECTOS** — La sección 4.4 del V1 mapea Kyle (1985) → Order Blocks, Cont (2010) → FVGs. Estos papers NO hablan de esos conceptos SMC.
6. **Falta CÓMO (solo QUÉ)** — El V1 describe los fenómenos pero no da workflows ejecutables, código, ni pasos prácticos.

### Resumen de 18 Secciones (V2 propuesto)
Ver `references/behavioral-finance-smart-money.md` y `references/alternative-data-hedge-funds.md` dentro de este skill para el contenido completo de las nuevas dimensiones.

### Auditoría completa
`D:\\PyCode\\hermes-skills\\SmartMoney\\AUDITORIA_SMART_MONEY.md` (16.2 KB)

### Plan de fortalecimiento
`D:\\PyCode\\hermes-skills\\SmartMoney\\PLAN_FORTALECIMIENTO.md` (8.3 KB)
