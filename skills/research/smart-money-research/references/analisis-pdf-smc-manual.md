# Análisis de un Manual SMC/ICT (110 páginas, por @chart.wzrd / @curiwesfx)
## Lecciones para la investigación e implementación de señales

## Naturaleza del documento
- Manual de trading SMC/ICT completo, NO investigación académica
- Incluye capítulos de psicología (I), estructura (II), liquidez (III), order blocks (IV), entradas (V), casos de estudio (VI)
- Contenido protegido (Google Drive con lista de compradores)

## Reglas codificables del manual

### Order Block (4 reglas, página 63)
1. Debe barrer liquidez de algún High/Low o EQH/EQL
2. Obligatoriamente debe hacer BOS de un punto débil (Weak High/Low)
3. Debe crear IRL ANTES de ser mitigado
4. No debe estar mitigado (tocado múltiples veces invalida)

### Tipos de liquidez detectables
- ERL: External Range Liquidity (fuera del TR actual)
- IRL: Internal Range Liquidity (dentro del TR actual)
- ARL: Asia Session Range Liquidity
- BSL: Buy Side Liquidity (stops de compradores)
- SSL: Sell Side Liquidity (stops de vendedores)
- EQH/EQL: Equal Highs/Lows

### Estructura de mercado
- BOS: Break of Structure (continuación de tendencia)
- CHoCH/CDC: Cambio de Carácter (posible reversión)
- TR PT: Trading Range Pro-Trend (a favor de tendencia)
- TR CT: Trading Range Counter-Trend (contra tendencia)
- Premium/Discount/Equilibrium

### Modelos de entrada
- RE: Risk Entry (sin confirmación, más riesgo)
- CE: Confirmation Entry (esperar CDC en POI)
- DCE: Double Confirmation Entry (doble BOS a favor)

## Contradicciones internas clave
- "8/10 trades deben ser de continuación" (pág 95) vs SMC vendido como detector de reversiones
- "Reversals kill traders" (pág 95) — si las reversiones son peligrosas, el SMC añade poco valor

## Vacíos críticos
- CERO backtesting: no hay win rate, Sharpe, profit factor, número de trades
- Lenguaje pseudocientífico: "IPDA" no existe en academia ni en documentación de exchanges
- Sin comparación contra benchmark (buy/hold, SMA crossover, random entry)
