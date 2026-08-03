#!/usr/bin/env python3
"""
diagnostic_reporter.py — Motor de informes científicos estructurados
Parte del skill scientific-statistical-engine

Genera informes científicos en formato .md y .txt con:
- Tablas de resultados con intervalos de confianza
- Tests de supuestos pre-modelo
- Métricas de diagnóstico post-modelo
- Autoevaluación con limitaciones documentadas
- Formato reproducible (seed, versión, fecha)

Uso:
    from diagnostic_reporter import Report, AssumptionTest, round_sig
"""

import numpy as np
from scipy import stats
from datetime import datetime
from typing import Optional, Union, List, Dict, Tuple
import textwrap


# =============================================================================
# UTILIDADES NUMÉRICAS
# =============================================================================

def round_sig(x: float, sig: int = 4) -> float:
    """Redondear a cifras significativas."""
    if x == 0 or not np.isfinite(x):
        return 0.0
    return round(x, sig - int(np.floor(np.log10(abs(x)))) - 1)


def format_ci(estimate: float, ci_low: float, ci_high: float, 
              sig: int = 4, pct: bool = False) -> str:
    """Formatear estimación con intervalo de confianza."""
    e = round_sig(estimate, sig)
    lo = round_sig(ci_low, sig)
    hi = round_sig(ci_high, sig)
    if pct:
        return f"{e*100:.2f}%  IC95% [{lo*100:.2f}%, {hi*100:.2f}%]"
    return f"{e}  IC95% [{lo}, {hi}]"


def format_pvalue(p: float) -> str:
    """Formatear p-valor con notación científica para valores pequeños."""
    if p < 0.0001:
        return f"{p:.2e}"
    return f"{p:.4f}"


def diagnostic_banner(title: str, width: int = 68) -> str:
    """Generar banner de diagnóstico."""
    return f"""
{'=' * width}
{title.upper()}
{'=' * width}
"""


# =============================================================================
# TESTS DE SUPUESTOS
# =============================================================================

class AssumptionTest:
    """
    Test de supuesto estadístico con resultado estructurado.
    
    Attributes:
        name: Nombre del test
        statistic: Valor del estadístico
        p_value: p-valor
        passed: True si pasa el supuesto (p > alpha por defecto)
        alpha: Nivel de significancia
        interpretation: Interpretación textual
        recommendation: Recomendación si no pasa
    """
    
    def __init__(self, name: str, statistic: float, p_value: float,
                 alpha: float = 0.05, passed: Optional[bool] = None,
                 interpretation: str = "", recommendation: str = ""):
        self.name = name
        self.statistic = round_sig(statistic)
        self.p_value = p_value
        self.alpha = alpha
        self.passed = passed if passed is not None else (p_value > alpha)
        self.interpretation = interpretation
        self.recommendation = recommendation
    
    def __str__(self) -> str:
        status = "✓ PASA" if self.passed else "✗ FALLA"
        return (f"  {status:>8s} | {self.name:35s} | "
                f"stat={self.statistic:.4f}  p={format_pvalue(self.p_value)}"
                f"{'  ⚠ ' + self.recommendation[:40] if not self.passed else ''}")


def test_normality(data: np.ndarray, alpha: float = 0.05) -> AssumptionTest:
    """Test de normalidad (Shapiro-Wilk). Recomendado para n < 5000."""
    if len(data) < 3:
        return AssumptionTest("Shapiro-Wilk (normalidad)", 0, 1, alpha,
                            passed=True, interpretation="n < 3, no testeable")
    if len(data) > 5000:
        # Usar Anderson-Darling para muestras grandes
        result = stats.anderson(data, dist='norm')
        stat = result.statistic
        # Anderson-Darling: rechaza si stat > critical_value
        crit_val = result.critical_values[2]  # 5% significance level
        p_val = _anderson_pvalue(stat)
        passed = stat < crit_val
        rec = "Usar tests no paramétricos (Mann-Whitney, Kruskal-Wallis)" if not passed else ""
        return AssumptionTest("Anderson-Darling (normalidad)", stat, p_val, alpha,
                            passed=passed,
                            interpretation=f"n={len(data)} > 5000, usando AD",
                            recommendation=rec)
    else:
        stat, p_val = stats.shapiro(data)
        passed = p_val > alpha
        rec = "Usar tests no paramétricos o transformar datos" if not passed else ""
        return AssumptionTest("Shapiro-Wilk (normalidad)", stat, p_val, alpha,
                            passed=passed,
                            interpretation=f"W={stat:.4f}",
                            recommendation=rec)


def _anderson_pvalue(stat: float) -> float:
    """Aproximación del p-valor para Anderson-Darling."""
    # Ajuste empírico basado en tabla de Stephens (1974)
    if stat < 0.2:
        return 0.85
    elif stat < 0.3:
        return 0.75 - (stat - 0.2) / 0.1 * 0.3
    elif stat < 0.4:
        return 0.45 - (stat - 0.3) / 0.1 * 0.2
    elif stat < 0.6:
        return 0.25 - (stat - 0.4) / 0.2 * 0.15
    elif stat < 0.8:
        return 0.10 - (stat - 0.6) / 0.2 * 0.07
    else:
        return 0.03 - (stat - 0.8) / 0.5 * 0.025


def test_homoscedasticity(*groups: np.ndarray, alpha: float = 0.05
                          ) -> AssumptionTest:
    """Test de homocedasticidad (Levene). Robusto a no-normalidad."""
    if len(groups) < 2:
        return AssumptionTest("Levene (homocedasticidad)", 0, 1, alpha,
                            passed=True, interpretation="< 2 grupos")
    stat, p_val = stats.levene(*groups)
    passed = p_val > alpha
    rec = "Usar Welch ANOVA o regresión robusta" if not passed else ""
    return AssumptionTest("Levene (homocedasticidad)", stat, p_val, alpha,
                        passed=passed, recommendation=rec)


def test_independence(x: np.ndarray, y: np.ndarray, alpha: float = 0.05
                      ) -> AssumptionTest:
    """Test de independencia (Durbin-Watson para residuos)."""
    from statsmodels.stats.stattools import durbin_watson
    dw = durbin_watson(np.asarray(y))
    # DW ≈ 2 indica no autocorrelación
    passed = 1.5 < dw < 2.5
    rec = ""
    if dw < 1.0:
        rec = "Autocorrelación positiva severa. Usar modelos con AR."
    elif dw > 3.0:
        rec = "Autocorrelación negativa severa. Revisar especificación."
    elif not passed:
        rec = "Autocorrelación moderada. Considerar HAC errors."
    return AssumptionTest("Durbin-Watson (independencia)", dw, 0.5, alpha,
                        passed=passed,
                        interpretation=f"DW={dw:.3f} (ideal: 1.5-2.5)",
                        recommendation=rec)


def run_assumption_battery(data: np.ndarray, groups: Optional[list] = None,
                           residuals: Optional[np.ndarray] = None,
                           alpha: float = 0.05) -> List[AssumptionTest]:
    """Ejecutar batería completa de tests de supuestos."""
    tests = []
    
    # Normalidad
    if len(data) >= 3:
        tests.append(test_normality(data, alpha))
    
    # Homocedasticidad
    if groups and len(groups) >= 2:
        tests.append(test_homoscedasticity(*groups, alpha=alpha))
    
    # Independencia
    if residuals is not None and len(residuals) >= 4:
        tests.append(test_independence(np.arange(len(residuals)), residuals, alpha))
    
    return tests


# =============================================================================
# MOTOR DE INFORMES
# =============================================================================

class Report:
    """
    Generador de informes científicos estructurados.
    
    Uso:
        r = Report(title="Análisis Bayesiano")
        r.add_section("Datos", "n=100, media=52.3...")
        r.add_table("Resultados", headers=["Parámetro", "Media", "IC95%"],
                    rows=[["mu", "52.3", "[50.1, 54.5]"]])
        r.add_assumption_tests(tests)
        r.add_self_evaluation(fortalezas=[...], limitaciones=[...])
        r.save("/ruta/informe")
    """
    
    def __init__(self, title: str, author: str = "Hermes Agent",
                 model: str = "", seed: int = 42):
        self.title = title
        self.author = author
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.model = model
        self.seed = seed
        self.sections: List[Dict] = []
        self._n_tests_passed = 0
        self._n_tests_total = 0
    
    def add_section(self, name: str, content: str, level: int = 2):
        """Añadir sección de texto."""
        self.sections.append({"type": "section", "name": name, 
                             "content": content, "level": level})
    
    def add_table(self, name: str, headers: List[str], rows: List[List],
                  caption: str = ""):
        """Añadir tabla con resultados."""
        # Calcular anchos de columna
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        col_widths = [min(w + 2, 60) for w in col_widths]
        
        # Construir tabla
        header_line = " │ ".join(h.center(w) for h, w in zip(headers, col_widths))
        sep = "─┼─".join("─" * w for w in col_widths)
        
        table_lines = [
            f"─── {name} {caption}",
            f"  {header_line}",
            f"  {sep}",
        ]
        for row in rows:
            row_line = " │ ".join(str(c).ljust(w) for c, w in zip(row, col_widths))
            table_lines.append(f"  {row_line}")
        
        self.sections.append({"type": "table", "name": name,
                             "text": "\n".join(table_lines)})
    
    def add_assumption_tests(self, tests: List[AssumptionTest]):
        """Añadir batería de tests de supuestos."""
        lines = ["─── BATERÍA DE SUPUESTOS"]
        for t in tests:
            lines.append(str(t))
            self._n_tests_total += 1
            if t.passed:
                self._n_tests_passed += 1
        
        pct_pass = self._n_tests_passed / max(self._n_tests_total, 1) * 100
        lines.append(f"\n  Supuestos superados: {self._n_tests_passed}/{self._n_tests_total} ({pct_pass:.0f}%)")
        
        if pct_pass < 100:
            lines.append("  ⚠ Algunos supuestos no se cumplen. Las conclusiones deben")
            lines.append("     interpretarse con cautela. Ver recomendaciones arriba.")
        
        self.sections.append({"type": "assumptions", "text": "\n".join(lines)})
    
    def add_self_evaluation(self, fortalezas: List[str], limitaciones: List[str],
                           riesgos: Optional[List[str]] = None,
                           errores_propios: Optional[List[str]] = None):
        """Añadir sección de autoevaluación."""
        lines = ["─── AUTOEVALUACIÓN", ""]
        
        lines.append("  FORTALEZAS:")
        for f in fortalezas:
            lines.append(f"    ✓ {f}")
        
        lines.append("")
        lines.append("  LIMITACIONES:")
        for l in limitaciones:
            lines.append(f"    ✗ {l}")
        
        if riesgos:
            lines.append("")
            lines.append("  RIESGOS DE INTERPRETACIÓN:")
            for r in riesgos:
                lines.append(f"    ⚠ {r}")
        
        if errores_propios:
            lines.append("")
            lines.append("  ERRORES PROPIOS CORREGIDOS:")
            for e in errores_propios:
                lines.append(f"    • {e}")
        
        self.sections.append({"type": "self_eval", "text": "\n".join(lines)})
    
    def add_code_block(self, language: str, code: str):
        """Añadir bloque de código."""
        self.sections.append({"type": "code", "language": language, "code": code})
    
    def _render_header(self) -> str:
        w = 68
        return f"""
{'═' * w}
{self.title}
{'═' * w}
Autor: {self.author}  |  Fecha: {self.date}  |  Seed: {self.seed}
Modelo: {self.model}
{'─' * w}
"""
    
    def _render_section(self, sec: Dict, md: bool = True) -> str:
        if sec["type"] == "section":
            if md:
                prefix = "#" * sec.get("level", 2)
                return f"\n{prefix} {sec['name']}\n\n{sec['content']}\n"
            return f"\n─── {sec['name']} ───\n\n{sec['content']}\n"
        
        elif sec["type"] == "table":
            return f"\n{sec['text']}\n"
        
        elif sec["type"] == "assumptions":
            return f"\n{sec['text']}\n"
        
        elif sec["type"] == "self_eval":
            return f"\n{sec['text']}\n"
        
        elif sec["type"] == "code":
            if md:
                return f"\n```{sec['language']}\n{sec['code']}\n```\n"
            return f"\n[CÓDIGO {sec['language']}]\n{sec['code']}\n[/CÓDIGO]\n"
        
        return ""
    
    def render_markdown(self) -> str:
        """Renderizar informe en Markdown."""
        parts = [self._render_header()]
        for sec in self.sections:
            parts.append(self._render_section(sec, md=True))
        parts.append(f"\n{'─' * 68}\nFin del informe — {self.date}\n")
        return "\n".join(parts)
    
    def render_text(self) -> str:
        """Renderizar informe en texto plano."""
        parts = [self._render_header().replace('═', '=').replace('─', '-')]
        for sec in self.sections:
            t = self._render_section(sec, md=False)
            t = t.replace('─', '-').replace('═', '=')
            parts.append(t)
        parts.append(f"\n{'-' * 68}\nFin del informe — {self.date}\n")
        return "\n".join(parts)
    
    def save(self, base_path: str):
        """Guardar informe en formato dual (.md + .txt)."""
        md_path = base_path + ".md"
        txt_path = base_path + ".txt"
        
        with open(md_path, 'w') as f:
            f.write(self.render_markdown())
        
        with open(txt_path, 'w') as f:
            f.write(self.render_text())
        
        return {"md": md_path, "txt": txt_path}
    
    def get_summary_stats(self) -> Dict:
        """Obtener estadísticas resumen del informe."""
        return {
            "n_sections": len(self.sections),
            "n_tests_passed": self._n_tests_passed,
            "n_tests_total": self._n_tests_total,
            "pct_tests_passed": (self._n_tests_passed / 
                                max(self._n_tests_total, 1) * 100),
        }


# =============================================================================
# VALIDACIÓN
# =============================================================================

if __name__ == "__main__":
    # Demo del motor de informes
    np.random.seed(42)
    data = np.random.normal(5.2, 1.5, 100)
    group_a = np.random.normal(5.0, 1.5, 50)
    group_b = np.random.normal(5.5, 1.5, 50)
    
    r = Report(title="Demo: Motor de Informes Científicos",
               model="Test de validación")
    
    r.add_section("Datos simulados", 
                  f"n={len(data)}, media={data.mean():.2f}, std={data.std():.2f}")
    
    tests = run_assumption_battery(data, [group_a, group_b])
    r.add_assumption_tests(tests)
    
    r.add_table("Estadísticos descriptivos",
                ["Variable", "n", "Media", "DE", "Min", "Max"],
                [["Grupo A", "50", f"{group_a.mean():.2f}", f"{group_a.std():.2f}",
                  f"{group_a.min():.2f}", f"{group_a.max():.2f}"],
                 ["Grupo B", "50", f"{group_b.mean():.2f}", f"{group_b.std():.2f}",
                  f"{group_b.min():.2f}", f"{group_b.max():.2f}"]])
    
    # Test t
    t_stat, t_p = stats.ttest_ind(group_a, group_b)
    r.add_section("Test de hipótesis",
                  f"t-test independiente (dos colas): t={t_stat:.3f}, p={t_p:.4f}\n"
                  f"Diferencia de medias: {group_b.mean()-group_a.mean():.3f}\n"
                  f"IC95% diferencia: {stats.ttest_ind(group_a, group_b, alternative='two-sided')}")
    
    r.add_self_evaluation(
        fortalezas=["Motor de informes funcional", "Tests de supuestos integrados",
                    "Formato dual .md + .txt", "Reproducibilidad (seed fija)"],
        limitaciones=["Demo con datos simulados", "Solo tests básicos implementados"],
        riesgos=["Los datos simulados no representan casos reales"]
    )
    
    paths = r.save("/mnt/d/descargas/Statistical_Skill_Dev/demo_reporter")
    print(f"✅ Informe guardado en:")
    print(f"   {paths['md']}")
    print(f"   {paths['txt']}")
    print(f"\nResumen: {r.get_summary_stats()}")
