# Confidence Floor Tuning

## Problem

False positives occur when adversarial queries get confidence >=0.75 despite having no real data. Root cause: `api_rest.py:607` has a floor that bumps confidence to 0.75 whenever there's ANY lexical overlap between query terms and results.

```python
# OLD - too aggressive
if has_real_overlap and weighted < 0.75 and (ratio >= 0.65 or db_ratio >= 0.90):
    weighted = 0.75  # FLOOR too high
```

## Solution

Lower the floor from 0.75 to 0.60:

```python
# NEW - less aggressive
if has_real_overlap and weighted < 0.60 and (ratio >= 0.65 or db_ratio >= 0.90):
    weighted = 0.60
```

## Results (Retest 27 preguntas)

| Query | Before | After |
|-------|--------|-------|
| DS 501-2028-SA presupuesto | 0.75 FAIL | 0.60 OK |
| decretos supremos 2019 | 0.75 FAIL | 0.60 OK |
| presupuesto general 2027 | 0.75 FAIL | 0.24 OK |
| normas 2010 medio ambiente | 0.75 FAIL | 0.60 OK |
| naves espaciales Peru | 0.75 FAIL | 0.24 OK |
| normas año 2020 | 0.76 FAIL | 0.72 STILL FP |

5/6 false positives corrected. The remaining one (normas 2020) requires temporal filter.

## Location in code
- `api_rest.py` line 607: the floor value
- `api_rest.py` line 609: exact ID boost (0.85, correct)
- `api_rest.py` line 1782: post-hoc negation range (0.75, different mechanism)
