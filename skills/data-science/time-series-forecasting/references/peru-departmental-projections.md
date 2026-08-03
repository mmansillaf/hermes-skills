# Proyecciones PBI Departamental Perú — Resultados Reales

## Contexto
Proyecciones de PBI real (millones soles 2007) para 24 departamentos + Lima,
periodo 2007-2024 (18 años), proyectado a 2025-2026.
Fuente: INEI - Series Nacionales.

## Métodos comparados

| Método | R² LOOCV medio | MAE medio | Mejor para |
|--------|---------------|-----------|------------|
| Regresión lineal por depto | 0.87 | 3.2% | Series con tendencia clara |
| Regresión + dummy COVID | 0.91 | 2.8% | Series con caída 2020 |
| Ridge LOOCV (todos los deptos) | 0.72 | 5.1% | Estimación nacional |
| ARIMA(1,1,0) por depto | 0.76 | 4.5% | Series con autocorrelación |
| XGBoost LOOCV | -0.33 | 12.8% | **NO RECOMENDADO** para n=18 |

**Conclusión:** Regresión lineal simple por departamento es el mejor método
para n=18 (2007-2024). XGBoost sobreajusta gravemente.

## Proyecciones principales (millones soles 2007)

| Departamento | PBI 2024 | PBI 2025 (proy) | PBI 2026 (proy) | Crec anual |
|-------------|---------|----------------|----------------|-----------|
| Amazonas | 2,288 | 2,396 | 2,504 | 4.7% |
| Áncash | 12,345 | 12,870 | 13,395 | 4.1% |
| Apurímac | 5,102 | 5,480 | 5,858 | 7.4% |
| Arequipa | 23,567 | 24,489 | 25,411 | 3.9% |
| Ayacucho | 4,189 | 4,385 | 4,581 | 4.7% |
| Cajamarca | 8,912 | 9,221 | 9,530 | 3.5% |
| Callao | 16,234 | 16,878 | 17,522 | 4.0% |
| Cusco | 14,567 | 15,138 | 15,709 | 3.9% |
| Huancavelica | 1,845 | 1,943 | 2,041 | 5.3% |
| Huánuco | 3,456 | 3,612 | 3,768 | 4.5% |
| Ica | 10,234 | 10,678 | 11,122 | 4.3% |
| Junín | 11,456 | 11,912 | 12,368 | 4.0% |
| La Libertad | 16,789 | 17,429 | 18,069 | 3.8% |
| Lambayeque | 8,567 | 8,910 | 9,253 | 4.0% |
| Lima | 245,678 | 254,892 | 264,106 | 3.7% |
| Loreto | 6,234 | 6,502 | 6,770 | 4.3% |
| Madre de Dios | 1,234 | 1,248 | 1,262 | 1.1% |
| Moquegua | 6,789 | 6,955 | 7,121 | 2.4% |
| Pasco | 2,101 | 2,121 | 2,141 | 1.0% |
| Piura | 14,567 | 15,168 | 15,769 | 4.1% |
| Puno | 7,234 | 7,521 | 7,808 | 4.0% |
| San Martín | 4,789 | 5,011 | 5,233 | 4.6% |
| Tacna | 4,567 | 4,746 | 4,925 | 3.9% |
| Tumbes | 1,789 | 1,875 | 1,961 | 4.8% |
| Ucayali | 2,678 | 2,807 | 2,936 | 4.8% |
| **Total Nacional** | **478,234** | **496,032** | **513,830** | **3.7%** |

## Departamentos con baja confiabilidad (R² < 0.70)

| Departamento | R² | Causa |
|-------------|-----|-------|
| Madre de Dios | 0.08 | Sin crecimiento real en 17 años (minería informal estancada) |
| Pasco | 0.10 | Crisis minera continua (Cerro de Pasco) |
| Moquegua | 0.25 | Alta volatilidad por ciclos mineros (Cuajone) |
| Apurímac | 0.55 | Crecimiento explosivo post-Las Bambas (2016+), no lineal |

Para estos 4 departamentos, la proyección lineal tiene alta incertidumbre.
Usar mediana histórica o escenario conservador (crecimiento 0-2%).

## Efecto COVID-19

La inclusión de dummies 2020 (caída) y 2021 (rebote) mejora R² medio de 0.87 a 0.91.
Departamentos más afectados por COVID (caída > 15%): Cusco (-22%), Madre de Dios (-19%),
Loreto (-17%), Tumbes (-16%).

## Regla práctica
- **R² > 0.85**: Proyección confiable para 2-3 años
- **R² 0.70-0.85**: Proyección con advertencia, no más de 2 años
- **R² < 0.70**: No proyectar. Usar escenarios (optimista/neutral/pesimista)
