---
name: bayesian-methodology
description: "Referencia teórica completa de métodos bayesianos: modelos conjugados, MCMC, diagnóstico, selección de modelos. Con fórmulas, ejemplos numéricos, y código Python."
---

# Bayesian Methodology — Referencia Teórica

## 1. Teorema de Bayes

P(θ|D) = P(D|θ) * P(θ) / P(D)

Donde:
- P(θ|D): Posterior (lo que sabemos después de los datos)
- P(D|θ): Likelihood (verosimilitud de los datos dado θ)
- P(θ): Prior (lo que sabíamos antes)
- P(D): Evidence (probabilidad marginal de los datos)

## 2. Modelos Conjugados

Un prior es conjugado si la posterior tiene la misma forma
familiar que el prior.

### 2.1 Beta-Binomial (proporciones/binario)

Prior:    θ ~ Beta(α, β)
Lik:      y ~ Binomial(n, θ)
Posterior: θ|y ~ Beta(α + y, β + n - y)

Media posterior: (α + y) / (α + β + n)
Varianza posterior: (α+y)(β+n-y) / [(α+β+n)²(α+β+n+1)]

Ejemplo numérico:
  Prior: Beta(2, 2) — vaga, centrada en 0.5
  Datos: y=30, n=50
  Posterior: Beta(32, 22)
  Media: 32/54 = 0.593
  IC 95%: [0.452, 0.723]

### 2.2 Normal-Normal (medias)

Prior:    μ ~ N(μ₀, σ₀²)
Lik:      y_i ~ N(μ, σ²) para i=1..n
Posterior: μ|y ~ N(μₙ, σₙ²)

μₙ = (μ₀/σ₀² + nȳ/σ²) / (1/σ₀² + n/σ²)
σₙ² = 1 / (1/σ₀² + n/σ²)

Interpretación: la media posterior es un promedio ponderado
entre el prior y los datos, ponderado por las precisiones (1/varianza).

### 2.3 Gamma-Poisson (tasas)

Prior:    λ ~ Gamma(α, β)
Lik:      y_i ~ Poisson(λ) para i=1..n
Posterior: λ|y ~ Gamma(α + Σy_i, β + n)

Media posterior: (α + Σy) / (β + n)

## 3. MCMC — Markov Chain Monte Carlo

Cuando no hay conjugación, muestreamos de la posterior con MCMC.

### 3.1 Metropolis-Hastings

Algoritmo:
1. Partir de θ⁰
2. Proponer θ* ~ q(θ*|θᵗ)  (distribución propuesta)
3. Calcular α = min(1, P(θ*|D)q(θᵗ|θ*) / [P(θᵗ|D)q(θ*|θᵗ)])
4. Aceptar θᵗ⁺¹ = θ* con prob α, si no θᵗ⁺¹ = θᵗ
5. Repetir

### 3.2 HMC — Hamiltonian Monte Carlo

Usa gradientes de la log-posterior para proponer saltos más
eficientes. NUTS (No-U-Turn Sampler) es una variante que
ajusta automáticamente la longitud de los saltos.

### 3.3 Diagnóstico de Convergencia

R-hat (Gelman-Rubin): compara varianza entre cadenas vs dentro.
  R-hat < 1.01 → convergencia aceptable
  R-hat > 1.05 → no convergió, más iteraciones

ESS (Effective Sample Size): número de muestras independientes
  equivalentes. ESS < 100 → autocorrelación alta, más iteraciones.

Trace plot: superposición de cadenas. Deben mezclarse bien.

Posterior predictive check: ¿los datos simulados del modelo
se parecen a los datos observados?

## 4. Selección de Modelos

WAIC (Watanabe-Akaike Information Criterion):
  WAIC = -2(lppd - p_WAIC)
  Menor WAIC → mejor modelo. Diferencia > 5 es significativa.

LOO-CV (Leave-One-Out Cross-Validation):
  Estima el poder predictivo fuera de muestra.
  PSIS (Pareto Smoothed Importance Sampling) para estabilidad.
  k_hat > 0.7 → observación influyente, revisar modelo.

Factor de Bayes:
  BF₁₂ = P(D|M₁) / P(D|M₂)
  BF > 10 → evidencia fuerte para M₁
  BF > 100 → evidencia decisiva

## 5. Modelos Jerárquicos (Multinivel)

Estructura:
  yᵢⱼ ~ N(θⱼ, σ²)          # Nivel 1: observaciones dentro de grupo
  θⱼ ~ N(μ, τ²)             # Nivel 2: grupos vienen de población
  μ ~ prior vago
  τ ~ Half-Cauchy(0, 5)     # Prior para varianza entre grupos

El shrinkage (contracción) depende de τ²:
  θ̂ⱼ_FH = (nⱼ/σ² * ȳⱼ + 1/τ² * μ) / (nⱼ/σ² + 1/τ²)

Cuando τ² → ∞: θ̂ⱼ = ȳⱼ (sin pooling, cada grupo independiente)
Cuando τ² → 0:  θ̂ⱼ = μ (pooling completo, todos iguales)

## 6. GLM Bayesianos

Regresión lineal:        y ~ N(Xβ, σ²)
Regresión logística:     y ~ Bernoulli(logit⁻¹(Xβ))
Regresión Poisson:       y ~ Poisson(exp(Xβ))

Priors típicos para β:
  β ~ Normal(0, 2.5)        — weakly informative
  β ~ Student-t(3, 0, 2.5) — colas pesadas (robusto a outliers)
  β ~ Laplace(0, 1)         — LASSO bayesiano (regularización L1)

## 7. Referencias

- Gelman, A., Carlin, J.B., Stern, H.S., et al. (2013).
  Bayesian Data Analysis, 3rd ed. Chapman & Hall/CRC.
- McElreath, R. (2020). Statistical Rethinking, 2nd ed. CRC Press.
- Kruschke, J.K. (2014). Doing Bayesian Data Analysis, 2nd ed.
  Academic Press.
- Carpenter, B., Gelman, A., Hoffman, M.D., et al. (2017).
  "Stan: A Probabilistic Programming Language." JSS.
- Vehtari, A., Gelman, A., Gabry, J. (2017).
  "Practical Bayesian model evaluation using leave-one-out
  cross-validation and WAIC." Statistics and Computing.
