# Diagnosing CEJ Form Validation Failures

Methodology for determining WHY CEJ rejects captcha-solved forms, distilled from
production debugging where the success rate dropped from 72% to 10% due to wrong
event dispatching.

## Step 1: Capture pre-submit state

Take a screenshot AND save the HTML BEFORE clicking "consultarExpedientes":

```python
driver.save_screenshot(f'{exp_dir}/intento{intento}_pre_submit.png')
with open(f'{exp_dir}/intento{intento}_pre_submit.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)
```

## Step 2: Submit and capture post-fail state

After clicking "consultarExpedientes", wait for results. If `#command` doesn't
appear within 20s, capture the failure state:

```python
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#command'))
    )
except:
    driver.save_screenshot(f'{exp_dir}/intento{intento}_post_fail.png')
    with open(f'{exp_dir}/intento{intento}_post_fail.html', 'w') as f:
        f.write(driver.page_source)
```

## Step 3: Analyze the pre-submit HTML

Check if form fields actually contain values:

```bash
grep -oP 'id="cod_[^"]*"[^>]*value="[^"]*"' pre_submit.html
```

If you see `value=""` on fields that should be filled, an event handler is
CLEARING them. This happened with `blur` event — CEJ's blur handler runs validation
that resets invalid-seeming fields.

## Step 4: Analyze the post-fail HTML for errors

CEJ shows validation errors in `msjError` elements with red color:

```bash
grep -oP 'class="msjError[^"]*"[^>]*>[^<]+' post_fail.html
grep -oP 'style="color: rgb\(255, 0, 0\)[^"]*"[^>]*>[^<]+' post_fail.html
```

Example findings from production:
- `id="distritoJudicialError" style="display: inline;">Seleccione un distrito Judicial` — cod_distprov validation failed
- `id="cod_expedienteError" style="color: rgb(255, 0, 0);">` — expediente code validation failed
- `class="msjError"> (*)` — required field markers showing

## Step 5: Test event combinations

The form fields have `onkeyup="saltoCajaTexto(event,this,N,'nextField')"` handlers
and CEJ's validation is sensitive to which events are fired. Test combinations:

| Events fired | Result | Notes |
|-------------|--------|-------|
| None (just execute_script) | 33% success | Silent rejection |
| input + change | **72% success** | Production verified |
| input + change + keyup | 10% success | saltoCajaTexto corrupts |
| input + change + keyup + blur | 0% success | Fields cleared to "" |

## Step 6: Test with multiple expedientes

A critical mistake in the debugging session: the test input file
(filtro_100_200.xlsx) has expediente 00060-2021-0-1801-JR-DC-03 as its first entry.
This expediente does NOT exist in CEJ and fails 100% of the time regardless of
event configuration. This made it look like ALL fixes were failing when the real
success rate on valid expedientes was 72%.

Always test diagnostics with at least 5 UNIQUE expedientes from the actual
production input, not a test file that may have broken entries.
