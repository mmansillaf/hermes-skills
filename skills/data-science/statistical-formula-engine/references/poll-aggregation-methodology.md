# Poll Aggregation Methodology (Small-n, Multi-Source)

Metodologia para combinar multiples encuestas de opinion en un
pronostico unico con incertidumbre calibrada, especialmente
util cuando el numero de encuestas independientes es pequeno
(n < 30 polls).

## Contexto tipico

- 10-30 encuestas de distintas encuestadoras
- Cada una con 800-2,000 entrevistas
- Periodo de 2-6 meses antes de la eleccion
- 2-5 candidatos principales
- Objetivo: pronosticar resultado + incertidumbre

## Errores comunes (vistos en la practica)

### ❌ Tratar cada entrevista como observacion independiente

Beta-Binomial con n=19,513 entrevistas produce IC artificialmente
angostos. Las entrevistas NO son independientes porque estan
agrupadas en encuestas (clusters).

```
Incorrecto:  IC = f(19,513 entrevistas)  → demasiado angosto
Correcto:    IC = f(15 encuestas)         → realista
```

### ❌ Ignorar el diseno de efecto (DEFF)

El DEFF (Design Effect) mide cuanto se infla la varianza por
el diseno de muestreo conglomerado. En encuestas electorales,
DEFF tipico = 2-4 (para muestreo polietapico). Pero cuando
CADA ENCUESTA es un cluster, el DEFF efectivo es mucho mayor.

```
DEFF_efectivo = N_total_entrevistas / N_encuestas
Ejemplo: 19,513 / 15 = 1,308x
```

### ❌ Presentar un modelo como "base" y otros como "alternativos"

Cuando 4 especificaciones distintas dan resultados diferentes
(Keiko 51%, Keiko 49%, Keiko ventaja, Roberto ventaja),
ninguna es la "base". Usar Bayesian Model Averaging (BMA).

## Metodologia correcta (4 pasos)

### Paso 1: Estimar house effects

Cada encuestadora tiene un sesgo sistematico. Estimar como la
desviacion de cada una respecto al promedio general.

```python
dif_promedio = df['diferencia'].mean()
house_effects = {}
for enc in df['encuestadora'].unique():
    sub = df[df['encuestadora'] == enc]
    house_effects[enc] = sub['diferencia'].mean() - dif_promedio

# Corregir diferencias
df['dif_corregida'] = df['diferencia']
for enc, he in house_effects.items():
    df.loc[df['encuestadora'] == enc, 'dif_corregida'] -= he
```

Precaucion: Con solo 2-5 encuestas por encuestadora, la estimacion
del house effect tiene alta varianza. Atenuar hacia cero.

### Paso 2: Bootstrap a nivel de encuesta

Remuestrear las ENCUESTAS (no los individuos) con reemplazo.

```python
N_BOOT = 10000
boot_means = np.zeros(N_BOOT)
for b in range(N_BOOT):
    idx = np.random.choice(len(df), size=len(df), replace=True)
    sample = df.iloc[idx]
    weights = sample['n'].values / sample['n'].values.sum()
    boot_means[b] = np.average(sample['dif_corregida'], weights=weights)

media = boot_means.mean()
ic_95 = np.percentile(boot_means, [2.5, 97.5])
prob_victoria = (boot_means > 0).mean()
```

### Paso 3: Propagar incertidumbre de parametros secundarios

No tratar el voto blanco/nulo o la participacion como valores
fijos. Modelarlos como distribuciones.

```python
# B+N historico como distribucion normal
bn_historico = np.array([6.30, 6.15, 6.51])  # datos de 3 elecciones
bn_mean = bn_historico.mean()
bn_std = bn_historico.std()
bn_sample = np.random.normal(bn_mean / 100, bn_std / 100)

# Participacion como distribucion
part_mean, part_std = 0.75, 0.03
part_sample = np.random.normal(part_mean, part_std)
```

### Paso 4: Bayesian Model Averaging (BMA)

Promediar 4+ modelos con distintas especificaciones, usando
pesos basados en verosimilitud o pesos iguales (cuando no
hay suficiente data para estimar verosimilitudes).

```python
# Modelos con distintas ventanas temporales/filtros
modelos = {
    'ultimas_3_sem': boot_ultimas_3_sem,
    'todos': boot_todos,
    'verificados': boot_verificados,
    'sesgo_historico': boot_con_sesgo,
}
# Ponderacion igual (default cuando no hay data para mas)
pesos = [0.25, 0.25, 0.25, 0.25]

# BMA: combinar distribuciones
bma_samples = np.concatenate([
    np.random.choice(modelos[m], int(N_BOOT * pesos[i]))
    for i, m in enumerate(modelos)
])
```

## Interpretacion de resultados

| Escenario | P(victoria candidato A) | Que significa |
|---|---|---|
| > 95% | Favorito solido | Muy probable, pero no seguro |
| 80-95% | Favorito claro | Ventaja significativa |
| 60-80% | Favorito moderado | Ventaja, pero posible sorpresa |
| 40-60% | Carrera reñida | Cualquiera puede ganar |
| 20-40% | Desfavorecido moderado | Remontada posible |
| 5-20% | Desfavorecido claro | Necesita evento extraordinario |
| < 5% | Desfavorecido solido | Muy improbable |

## Autoevaluacion (auditar tu propio modelo)

Despues de construir el pronostico, hacer estas preguntas:

1. **Robustez**: Si cambio un supuesto (ventana temporal, ponderacion),
   ¿cambia drasticamente el resultado? → Si la respuesta es SI,
   el modelo no es robusto. Reportar el rango, no un valor puntual.

2. **Overconfidence**: Mis IC 95% son realistas? → Verificar con
   simulacion: si el IC dice [48%, 52%] pero al cambiar la
   especificacion el resultado salta a [45%, 55%], tus IC estan
   subestimados.

3. **Sesgo del investigador**: ¿Estoy presentando el modelo que
   "prefiero" como el principal? → Usar BMA para evitar esto.

4. **Trazabilidad**: ¿Puedo verificar cada encuesta contra su
   ficha tecnica original? → Si no, documentar como limitacion.

5. **Nivel de precision**: Con n < 30 encuestas, NO reportar
   decimales (51.11% es espurio). Reportar enteros (51%).

## Referencias

- Gelman et al. (2014): Bayesian Data Analysis (3rd ed.) — Capitulo de
  modelos jerarquicos para encuestas
- Jackman (2009): Bayesian Analysis for the Social Sciences — Pooling
  de encuestas electorales
- FiveThirtyEight (2024): Pollster Ratings — Metodologia de house effects
- Mercer et al. (2018): "A unified method for measuring polling accuracy"
  (AAPOR)
