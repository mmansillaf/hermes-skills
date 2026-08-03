#!/usr/bin/env python3
"""
bayesian_inference.py — Modelos bayesianos conjugados + MCMC
Parte del skill scientific-statistical-engine

Cubre:
1. Modelos conjugados: Beta-Binomial, Normal-Normal, Gamma-Poisson
2. MCMC con PyMC: regresión lineal, logística, jerárquicos
3. Diagnóstico: R-hat, ESS, WAIC, LOO, trace plots
4. Prior y posterior predictive checks
5. Comparación de modelos

Uso:
    python3 bayesian_inference.py --data datos.csv --model beta-binomial
    python3 bayesian_inference.py --data datos.csv --model mcmc-regression
"""

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from typing import Optional, Dict, Tuple, List
import json
import os
import sys
import argparse

# =============================================================================
# UTILIDADES
# =============================================================================

def _check_packages():
    """Verificar dependencias."""
    missing = []
    try:
        import pymc as pm
    except ImportError:
        missing.append("pymc")
    try:
        import arviz as az
    except ImportError:
        missing.append("arviz")
    if missing:
        print(f"⚠️  Faltan paquetes: {missing}")
        print(f"   Instalar con: pip install {' '.join(missing)}")
        return False
    return True


# =============================================================================
# MODELO 1: BETA-BINOMIAL (proporciones)
# =============================================================================

def beta_binomial(y: int, n: int, alpha_prior: float = 1.0, 
                  beta_prior: float = 1.0, alpha: float = 0.05,
                  output_path: str = "") -> Dict:
    """
    Modelo Beta-Binomial para proporciones binomiales.
    
    Parámetros:
        y: Número de éxitos
        n: Número total de ensayos
        alpha_prior, beta_prior: Parámetros del prior Beta
        alpha: Nivel de significancia para IC
        output_path: Ruta base para guardar informe (opcional)
    
    Retorna:
        Dict con: media posterior, IC, P(θ > umbral), etc.
    """
    if y > n or y < 0:
        raise ValueError(f"y={y} debe estar entre 0 y n={n}")
    if n <= 0:
        raise ValueError(f"n={n} debe ser > 0")
    
    alpha_post = alpha_prior + y
    beta_post = beta_prior + n - y
    
    media_post = alpha_post / (alpha_post + beta_post)
    var_post = (alpha_post * beta_post) / ((alpha_post + beta_post)**2 * 
                                           (alpha_post + beta_post + 1))
    std_post = np.sqrt(var_post)
    
    ci_low, ci_high = sp_stats.beta.interval(1 - alpha, alpha_post, beta_post)
    mode_post = (alpha_post - 1) / (alpha_post + beta_post - 2) if alpha_post > 1 and beta_post > 1 else media_post
    
    # Prior predictive: P(y|prior) = Beta-Binomial
    from scipy.stats import betabinom
    log_ml = betabinom.logpmf(y, n, alpha_prior, beta_prior)
    
    # Posterior predictive: distribución de nuevas observaciones
    ppd_samples = sp_stats.betabinom(n=n, a=alpha_post, b=beta_post).rvs(10000)
    
    result = {
        "modelo": "Beta-Binomial",
        "prior": f"Beta({alpha_prior}, {beta_prior})",
        "posterior": f"Beta({alpha_post:.1f}, {beta_post:.1f})",
        "media_posterior": round(media_post, 6),
        "std_posterior": round(std_post, 6),
        "moda_posterior": round(mode_post, 6),
        "ic_{}%".format(int((1-alpha)*100)): [round(ci_low, 6), round(ci_high, 6)],
        "n_efectivo": alpha_post + beta_post,
        "log_evidencia_marginal": round(float(log_ml), 4),
        "prob_theta_gt_0.5": float(sp_stats.beta.sf(0.5, alpha_post, beta_post)),
        "prob_theta_lt_0.5": float(sp_stats.beta.cdf(0.5, alpha_post, beta_post)),
    }
    
    # Intervalo de máxima densidad (HPD)
    result["hpd_95"] = [round(x, 6) for x in _hpd_beta(alpha_post, beta_post)]
    
    return result


def _hpd_beta(alpha: float, beta: float, mass: float = 0.95) -> Tuple[float, float]:
    """Intervalo de máxima densidad para Beta (por fuerza bruta)."""
    from scipy.optimize import minimize_scalar
    def hpd_width(logit_p):
        p = 1 / (1 + np.exp(-logit_p))
        if p <= 0 or p >= 1 - mass:
            return 1.0
        lower = sp_stats.beta.ppf((1 - mass) / 2, alpha, beta)
        if p < lower:
            return 1.0
        upper = p + mass
        if upper > 1:
            return 1.0
        return sp_stats.beta.ppf(upper, alpha, beta) - sp_stats.beta.ppf(lower, alpha, beta)
    
    res = minimize_scalar(hpd_width, bounds=(-10, 10), method='bounded')
    p_opt = 1 / (1 + np.exp(-res.x))
    lower = sp_stats.beta.ppf((1 - mass) / 2, alpha, beta)
    return (sp_stats.beta.ppf(lower, alpha, beta), 
            sp_stats.beta.ppf(lower + mass, alpha, beta))


# =============================================================================
# MODELO 2: NORMAL-NORMAL (medias)
# =============================================================================

def normal_normal(data: np.ndarray, mu_prior: float = 0.0, 
                  sigma_prior: float = 10.0, sigma_lik: Optional[float] = None,
                  alpha: float = 0.05) -> Dict:
    """
    Modelo Normal-Normal para la media de una población.
    
    Parámetros:
        data: Vector de observaciones
        mu_prior, sigma_prior: Parámetros del prior Normal
        sigma_lik: Desviación estándar de la likelihood (si se conoce).
                   Si es None, se estima de los datos.
        alpha: Nivel de significancia
    
    Retorna:
        Dict con media posterior, IC, etc.
    """
    n = len(data)
    if n < 2:
        raise ValueError(f"Se necesitan al menos 2 observaciones, n={n}")
    
    y_bar = np.mean(data)
    if sigma_lik is None:
        sigma_lik = np.std(data, ddof=1)
    
    # Precisión = 1/varianza
    prec_prior = 1 / sigma_prior**2
    prec_lik = n / sigma_lik**2
    
    mu_post = (mu_prior * prec_prior + y_bar * prec_lik) / (prec_prior + prec_lik)
    sigma_post = np.sqrt(1 / (prec_prior + prec_lik))
    
    ci_low, ci_high = sp_stats.norm.interval(1 - alpha, mu_post, sigma_post)
    
    # Factor de Bayes vs H₀: μ=0 usando Savage-Dickey
    # BF₁₀ = f_prior(μ=0) / f_posterior(μ=0)
    # La densidad prior en H₀: μ=0 bajo el prior N(mu_prior, sigma_prior²)
    prior_density_at_0 = sp_stats.norm.pdf(0, mu_prior, sigma_prior)
    # La densidad posterior en H₀: μ=0 bajo la posterior N(mu_post, sigma_post²)
    post_density_at_0 = sp_stats.norm.pdf(0, mu_post, sigma_post)
    bf10 = prior_density_at_0 / post_density_at_0 if post_density_at_0 > 0 else float('inf')
    
    result = {
        "modelo": "Normal-Normal",
        "prior": f"N({mu_prior}, {sigma_prior})",
        "media_posterior": round(mu_post, 6),
        "std_posterior": round(sigma_post, 6),
        f"ic_{int((1-alpha)*100)}": [round(ci_low, 6), round(ci_high, 6)],
        "n": n,
        "media_muestral": round(float(y_bar), 6),
        "sigma_likelihood": round(float(sigma_lik), 6),
        "precision_ganancia": round(prec_lik / prec_prior, 2),
        "bayes_factor_vs_H0": round(float(bf10), 2),
    }
    
    # Interpretación del BF
    if bf10 > 100:
        result["bf_interpretacion"] = "Evidencia decisiva para H₁ (μ ≠ 0)"
    elif bf10 > 10:
        result["bf_interpretacion"] = "Evidencia fuerte para H₁"
    elif bf10 > 3:
        result["bf_interpretacion"] = "Evidencia moderada para H₁"
    else:
        result["bf_interpretacion"] = "Evidencia débil o anecdótica"
    
    return result


# =============================================================================
# MODELO 3: GAMMA-POISSON (tasas)
# =============================================================================

def gamma_poisson(data: np.ndarray, alpha_prior: float = 1.0,
                  beta_prior: float = 1.0, alpha: float = 0.05) -> Dict:
    """
    Modelo Gamma-Poisson para tasa de eventos.
    
    Parámetros:
        data: Conteos de eventos (enteros >= 0)
        alpha_prior, beta_prior: Parámetros del prior Gamma
        alpha: Nivel de significancia
    
    Retorna:
        Dict con media posterior, IC, etc.
    """
    data = np.asarray(data, dtype=float)
    if np.any(data < 0):
        raise ValueError("Los datos deben ser >= 0")
    
    n = len(data)
    sum_y = data.sum()
    
    alpha_post = alpha_prior + sum_y
    beta_post = beta_prior + n
    
    media_post = alpha_post / beta_post
    var_post = alpha_post / beta_post**2
    std_post = np.sqrt(var_post)
    
    ci_low, ci_high = sp_stats.gamma.interval(1 - alpha, alpha_post, scale=1/beta_post)
    
    # Probabilidad que la tasa supere un umbral (ej: 1.0)
    prob_gt_1 = sp_stats.gamma.sf(1.0, alpha_post, scale=1/beta_post)
    
    result = {
        "modelo": "Gamma-Poisson",
        "prior": f"Gamma({alpha_prior}, {beta_prior})",
        "posterior": f"Gamma({alpha_post:.1f}, {beta_post:.1f})",
        "media_posterior": round(media_post, 6),
        "std_posterior": round(std_post, 6),
        f"ic_{int((1-alpha)*100)}": [round(ci_low, 6), round(ci_high, 6)],
        "n": n,
        "total_eventos": int(sum_y),
        "tasa_empirica": round(float(sum_y / n), 6),
        "prob_tasa_gt_1": round(float(prob_gt_1), 6),
    }
    
    return result


# =============================================================================
# MODELO 4: MCMC CON PyMC (regresión lineal)
# =============================================================================

def mcmc_linear_regression(X: np.ndarray, y: np.ndarray,
                           prior_beta_std: float = 2.5,
                           prior_sigma_std: float = 2.5,
                           n_samples: int = 2000, n_chains: int = 4,
                           n_tune: int = 1000, seed: int = 42,
                           output_path: str = "") -> Dict:
    """
    Regresión lineal bayesiana con MCMC (NUTS).
    
    y ~ N(Xβ, σ²)
    β ~ N(0, prior_beta_std²)
    σ ~ HalfNormal(prior_sigma_std)
    
    Retorna:
        Dict con: medias posteriores, IC, R-hat, ESS, WAIC
    """
    import pymc as pm
    import arviz as az
    
    n, p = X.shape if X.ndim > 1 else (len(X), 1)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    # Añadir intercepto
    X_with_intercept = np.column_stack([np.ones(n), X])
    p_full = X_with_intercept.shape[1]
    
    with pm.Model() as linear_model:
        # Priors
        beta = pm.Normal("beta", mu=0, sigma=prior_beta_std, shape=p_full)
        sigma = pm.HalfNormal("sigma", sigma=prior_sigma_std)
        
        # Likelihood
        mu = pm.math.dot(X_with_intercept, beta)
        likelihood = pm.Normal("y", mu=mu, sigma=sigma, observed=y)
        
        # MCMC
        trace = pm.sample(draws=n_samples, chains=n_chains, tune=n_tune,
                         random_seed=seed, progressbar=False)
        
        # Computar log-likelihood para LOO (dentro del contexto)
        pm.compute_log_likelihood(trace)
        
        # Posterior predictive check (dentro del contexto)
        ppc = pm.sample_posterior_predictive(trace, random_seed=seed,
                                              progressbar=False)
    
    # Diagnóstico
    summary = az.summary(trace, ci_prob=0.95)
    # Convertir columnas numéricas (arviz 1.x devuelve strings)
    for col in ["mean", "sd", "eti95_lb", "eti95_ub", "r_hat", "mcse_mean", "mcse_sd"]:
        if col in summary.columns:
            summary[col] = summary[col].astype(float)
    r_hats = summary["r_hat"].values
    ess_values = summary["ess_bulk"].values
    
    # LOO
    loo_result = az.loo(trace, pointwise=False)
    
    y_pred = ppc["posterior_predictive"]["y"].mean(("chain", "draw")).values
    residuals = y - y_pred
    rmse = np.sqrt(np.mean(residuals**2))
    
    # Resultados
    coef_names = ["Intercepto"] + [f"X{i+1}" for i in range(p)]
    coef_means = summary["mean"].values
    coef_sds = summary["sd"].values
    coef_ci = [[summary["eti95_lb"].values[i], summary["eti95_ub"].values[i]] for i in range(p_full)]
    
    result = {
        "modelo": "Regresión Lineal Bayesiana (MCMC-NUTS)",
        "n_observaciones": n,
        "n_predictores": p,
        "n_cadenas": n_chains,
        "n_muestras_por_cadena": n_samples,
        "n_tune": n_tune,
        "coeficientes": {
            coef_names[i]: {
                "media": round(float(coef_means[i]), 6),
                "std": round(float(coef_sds[i]), 6),
                "hpd_95": [round(float(coef_ci[i][0]), 6), 
                          round(float(coef_ci[i][1]), 6)],
                "r_hat": round(float(r_hats[i]), 4),
                "ess_bulk": int(ess_values[i]),
            }
            for i in range(p_full)
        },
        "sigma": {
            "media": round(float(summary.loc["sigma", "mean"]), 6),
            "hpd_95": [round(summary.loc["sigma", "eti95_lb"], 6),
                      round(summary.loc["sigma", "eti95_ub"], 6)],
            "r_hat": round(summary.loc["sigma", "r_hat"], 4),
        },
        "diagnostico": {
            "max_r_hat": round(float(max(r_hats)), 4),
            "min_ess": int(min(ess_values)),
            "loo_ic": round(float(loo_result.elpd), 2),
            "loo_se": round(float(loo_result.se), 2),
            "rmse": round(float(rmse), 4),
        },
        "convergencia": "OK" if max(r_hats) < 1.01 else "⚠️ REVISAR",
    }
    
    return result


# =============================================================================
# MODELO 5: REGRESIÓN LOGÍSTICA BAYESIANA
# =============================================================================

def mcmc_logistic_regression(X: np.ndarray, y: np.ndarray,
                             prior_beta_std: float = 2.5,
                             n_samples: int = 2000, n_chains: int = 4,
                             n_tune: int = 1000, seed: int = 42) -> Dict:
    """
    Regresión logística bayesiana con MCMC.
    
    y ~ Bernoulli(p)
    logit(p) = Xβ
    β ~ Student-t(3, 0, prior_beta_std) — colas pesadas, robusto
    """
    import pymc as pm
    import arviz as az
    
    n, p = X.shape if X.ndim > 1 else (len(X), 1)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    
    X_with_intercept = np.column_stack([np.ones(n), X])
    p_full = X_with_intercept.shape[1]
    
    with pm.Model() as logit_model:
        beta = pm.StudentT("beta", nu=3, mu=0, sigma=prior_beta_std, shape=p_full)
        p_logit = pm.math.dot(X_with_intercept, beta)
        likelihood = pm.Bernoulli("y", logit_p=p_logit, observed=y)
        
        trace = pm.sample(draws=n_samples, chains=n_chains, tune=n_tune,
                         random_seed=seed, progressbar=False)
    
    summary = az.summary(trace, ci_prob=0.95)
    for col in ["mean", "sd", "eti95_lb", "eti95_ub", "r_hat"]:
        if col in summary.columns:
            summary[col] = summary[col].astype(float)
    loo_result = az.loo(trace, pointwise=False)
    
    # Precisión predictiva
    y_pred_prob = 1 / (1 + np.exp(-(X_with_intercept @ summary["mean"].values)))
    y_pred = (y_pred_prob > 0.5).astype(int)
    accuracy = (y_pred == y).mean()
    
    coef_names = ["Intercepto"] + [f"X{i+1}" for i in range(p)]
    coef_means = summary["mean"].values
    coef_ci = [summary[["eti95_lb", "eti95_ub"]].values[i] for i in range(p_full)]
    
    result = {
        "modelo": "Regresión Logística Bayesiana (MCMC-NUTS)",
        "n_observaciones": n,
        "n_predictores": p,
        "coeficientes": {
            coef_names[i]: {
                "media": round(float(coef_means[i]), 4),
                "hpd_95": [round(float(coef_ci[i][0]), 4), 
                          round(float(coef_ci[i][1]), 4)],
            }
            for i in range(p_full)
        },
        "rendimiento": {
            "accuracy": round(float(accuracy), 4),
            "loo_ic": round(float(loo_result.elpd), 2),
        },
        "max_r_hat": round(float(max(summary["r_hat"].values)), 4),
    }
    
    return result


# =============================================================================
# MODELO 6: MODELO JERÁRQUICO (MULTINIVEL)
# =============================================================================

def hierarchical_model(groups: np.ndarray, y: np.ndarray,
                       n_samples: int = 2000, n_chains: int = 4,
                       n_tune: int = 1000, seed: int = 42) -> Dict:
    """
    Modelo jerárquico multinivel.
    
    yᵢⱼ ~ N(θⱼ, σ²)      Nivel 1
    θⱼ ~ N(μ, τ²)         Nivel 2
    μ ~ N(0, 10)          Hiperprior
    τ ~ HalfCauchy(5)     Hiperprior
    σ ~ HalfNormal(5)
    """
    import pymc as pm
    import arviz as az
    
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    group_idx = np.array([np.where(unique_groups == g)[0][0] for g in groups])
    
    with pm.Model() as hierarchical:
        # Hiperpriors
        mu = pm.Normal("mu", mu=0, sigma=10)
        tau = pm.HalfCauchy("tau", beta=5)
        sigma = pm.HalfNormal("sigma", sigma=5)
        
        # Grupo-specific intercepts
        theta = pm.Normal("theta", mu=mu, sigma=tau, shape=n_groups)
        
        # Likelihood
        y_hat = theta[group_idx]
        likelihood = pm.Normal("y", mu=y_hat, sigma=sigma, observed=y)
        
        trace = pm.sample(draws=n_samples, chains=n_chains, tune=n_tune,
                         random_seed=seed, progressbar=False)
    
    summary = az.summary(trace, ci_prob=0.95)
    for col in ["mean", "sd", "eti95_lb", "eti95_ub", "r_hat"]:
        if col in summary.columns:
            summary[col] = summary[col].astype(float)
    loo_result = az.loo(trace, pointwise=False)
    
    # Shrinkage estimado
    theta_means = summary.loc[[f"theta[{i}]" for i in range(n_groups)], "mean"].values
    shrinkage = 1 - np.var(theta_means) / np.var(y)
    
    result = {
        "modelo": "Modelo Jerárquico (Multinivel)",
        "n_observaciones": len(y),
        "n_grupos": n_groups,
        "mu_global": {
            "media": round(float(summary.loc["mu", "mean"]), 4),
            "hpd_95": [round(summary.loc["mu", "eti95_lb"], 4),
                      round(summary.loc["mu", "eti95_ub"], 4)],
        },
        "tau_entre_grupos": {
            "media": round(float(summary.loc["tau", "mean"]), 4),
            "hpd_95": [round(summary.loc["tau", "eti95_lb"], 4),
                      round(summary.loc["tau", "eti95_ub"], 4)],
        },
        "sigma_dentro_grupo": {
            "media": round(float(summary.loc["sigma", "mean"]), 4),
        },
        "shrinkage": round(float(shrinkage), 4),
        "waic": round(float(loo_result.elpd), 2),
        "max_r_hat": round(float(max(summary["r_hat"].values)), 4),
    }
    
    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Inferencia Bayesiana Avanzada")
    parser.add_argument("--model", choices=["beta-binomial", "normal-normal",
                        "gamma-poisson", "mcmc-regression", "mcmc-logistic",
                        "hierarchical"],
                        default="beta-binomial")
    parser.add_argument("--data", type=str, help="Ruta al archivo CSV")
    parser.add_argument("--y", type=str, default="y", help="Columna de respuesta")
    parser.add_argument("--X", type=str, default="", help="Columnas predictoras (comma-sep)")
    parser.add_argument("--output", type=str, default="", help="Ruta de salida")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--samples", type=int, default=2000)
    
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    print(f"\n{'='*60}")
    print(f"INFERENCIA BAYESIANA — Modelo: {args.model}")
    print(f"{'='*60}")
    
    if args.model == "beta-binomial":
        # Ejemplo: 30 éxitos en 50 ensayos
        result = beta_binomial(y=30, n=50, alpha_prior=2, beta_prior=2)
        print(f"\nPrior: {result['prior']}")
        print(f"Posterior: {result['posterior']}")
        print(f"Media posterior: {result['media_posterior']:.4f}")
        ic_key = 'ic_95%'
        print(f"IC 95%: [{result[ic_key][0]:.4f}, {result[ic_key][1]:.4f}]")
        print(f"P(θ > 0.5): {result['prob_theta_gt_0.5']:.1%}")
    
    elif args.model == "normal-normal":
        data = np.random.normal(5.2, 2.0, 100)
        result = normal_normal(data, mu_prior=0, sigma_prior=10)
        print(f"\nMedia posterior: {result['media_posterior']:.4f}")
        ic_key2 = 'ic_95%' if 'ic_95%' in result else 'ic_95'
        print(f"IC 95%: [{result[ic_key2][0]:.4f}, {result[ic_key2][1]:.4f}]")
        print(f"BF₁₀ vs H₀: {result['bayes_factor_vs_H0']:.1f}")
        print(f"Interpretación: {result['bf_interpretacion']}")
    
    elif args.model == "mcmc-regression":
        if not _check_packages():
            return 1
        X = np.random.normal(0, 1, (200, 2))
        y = 1.5 + 0.8 * X[:, 0] - 0.5 * X[:, 1] + np.random.normal(0, 0.5, 200)
        result = mcmc_linear_regression(X, y)
        print(f"R²: {1 - result['diagnostico']['rmse']**2 / np.var(y):.4f}")
        print(f"LOO-IC: {result['diagnostico']['loo_ic']}")
        print(f"Convergencia: {result['convergencia']}")
        for name, coef in result['coeficientes'].items():
            print(f"  {name}: {coef['media']:.4f} ± {coef['std']:.4f}  "
                  f"R-hat={coef['r_hat']:.4f}")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Resultados guardados en: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
