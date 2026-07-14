# Project Audit Checklist — Document vs Data Consistency

Use this when reviewing an ML project that has both a methodology document
(Word/PDF) and a dataset (Excel/CSV). Detects gaps between what's described
and what's actually available.

## Phase 1: Extract Claims from Document

- [ ] List every variable name mentioned (including derived/engineered)
- [ ] List every transformation promised (ratios, scaling, encoding, PCA)
- [ ] Note the stated number of observations (rows) and features (columns)
- [ ] Note the model type (supervised/unsupervised) and stated evaluation metrics
- [ ] Note any preprocessing steps described (outlier treatment, imputation, scaling)

## Phase 2: Inspect the Dataset

For **every sheet** in the Excel:

- [ ] Count rows and columns
- [ ] Identify all column names (case-sensitive, typo check)
- [ ] Count nulls per column (especially >10% = red flag)
- [ ] Count exact duplicate rows
- [ ] Run describe() on numeric columns
- [ ] Run value_counts() on categorical/ID columns
- [ ] Calculate correlation matrix for numeric columns
- [ ] Detect outliers per numeric column (IQR method)

## Phase 3: Cross-Reference

- [ ] Every variable in the document → exists in the data? (exact name match)
- [ ] Every derived variable promised → exists as a column? (ratios, per_capita, etc.)
- [ ] Row count matches? (document number ≈ data rows)
- [ ] Outliers mentioned? → quantified in data?
- [ ] Multicolinealidad discussed? → correlation matrix confirms or contradicts?

## Phase 4: Model Readiness

- [ ] Is the data in the correct sheet for modeling? (data inicial vs data final)
- [ ] If the document promises feature engineering that isn't in the data,
      the data is NOT ready — the engineering step must be executed first.
- [ ] If one department/region dominates as outlier in all variables,
      it will distort K-Means (treat with winsorization or separate cluster).
- [ ] If r > 0.9 between predictors, the feature set has redundancy
      (use PCA or drop correlated variables).

## Phase 5: Deliverable Formats (user preferences)

When the audit is complete, the user expects:

- **Archivos de texto**: Guardar el informe como `.md` (markdown con tablas) y `.txt` (plano, ancho fijo). Ambos en la carpeta del proyecto.
- **Documento Word auditado**: CREAR un nuevo `.docx` (con sufijo `- AUDITADO`) que contenga el texto original del documento con observaciones **intercaladas en color**:
  - 🔴 Rojo = Crítico (bloqueante, inconsistencia documentada)
  - 🟠 Naranja/Alto = Requiere atención antes de continuar
  - 🔵 Azul = Mejora/sugerencia
  - 🟢 Verde = Bien (validado, correcto)
  - Gris = Nota metodológica
- **No modificar el original**: El Word auditado es una copia con anotaciones. El archivo original se conserva intacto.

### Procedimiento para Word auditado

```python
from docx import Document
from docx.shared import Pt, RGBColor

doc = Document()
ROJO = RGBColor(0xCC, 0x00, 0x00)
NARANJA = RGBColor(0xE6, 0x7E, 0x22)
AZUL = RGBColor(0x1F, 0x5B, 0xB6)
VERDE = RGBColor(0x1B, 0x7A, 0x2B)

def add_obs(doc, text, color, bold_title=""):
    p = doc.add_paragraph()
    run = p.add_run(f"📌 [{bold_title}] " if bold_title else "📌 ")
    run.bold = True
    run.font.color.rgb = color
    run.font.size = Pt(10)
    run2 = p.add_run(text)
    run2.font.color.rgb = color
    run2.font.size = Pt(10)
```

## Phase 6: Outlier Dominance — The Lima Pattern

When a dataset has one observation that dominates ALL numeric columns
(10-30x the mean of others), standard IQR outlier detection undercounts
because the outlier inflates the IQR itself. Use this instead:

```python
# 1. Separate the dominant observation
dominant_mask = df['dept'].str.contains('Lima', case=False)
resto_mask = ~dominant_mask

# 2. Compare each column
for col in numeric_cols:
    dom_val = df.loc[dominant_mask, col].values[0]
    resto_mean = df.loc[resto_mask, col].mean()
    ratio = dom_val / resto_mean
    print(f"{col}: {ratio:.1f}x el promedio del resto")
    # ratio > 5x → dominio extremo
    # ratio > 2x → dominio significativo

# 3. Simulate derived variables (ratios) to show the "should-be" state
df_r = df.copy()
df_r['ratio_var'] = (df['absolute_var'] / df['denominator']) * scale
# Re-run the comparison to show improvement
```

### ⚠️ Pitfall: IQR with a dominant outlier

Standard IQR may flag 0-2 outliers when the dominant observation is so
large it inflates Q3 and the IQR, making everything else look "in range."
Always supplement with the mean-ratio method above.

## Common Findings (from past audits)

| Finding | Severity | Action |
|---|---|---|
| Variables derivadas descritas pero no implementadas | 🔴 Blocking | Ejecutar feature engineering antes de modelar |
| Multicolinealidad no mencionada (r>0.9) | 🟡 Warning | Reducir dimensionalidad o seleccionar variables |
| Outlier que domina todas las variables | 🟡 Warning | Winsorize, tratar aparte, o usar modelo robusto |
| Conteo de filas no coincide entre doc y data | 🟡 Warning | Identificar hoja correcta o documentar discrepancia |
| Métricas de supervisado usadas para clustering | 🔴 Error | Cambiar a silhouette, Davies-Bouldin, inertia |
