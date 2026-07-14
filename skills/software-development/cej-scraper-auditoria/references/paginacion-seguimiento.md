# Paginacion del seguimiento en detalleform.html

## Estructura observada

La tabla de seguimiento del expediente (dentro de `#collapseThree` o `#divResol`) usa paginacion con jQuery.

### Elementos de paginacion
```html
<li class="active"><a>Principal</a></li>
<li class="pointer-cursor"><a>1</a></li>
<li class="pointer-cursor"><a>2</a></li>
<li class="pointer-cursor"><a>3</a></li>
<li class="pointer-cursor"><a>></a></li>
<li class="pointer-cursor"><a>>></a></li>
```

Los `<a>` NO tienen href ni onclick — el evento se maneja via jQuery bindings.

### Como hacer click programaticamente
```python
from selenium.webdriver.common.by import By

# Click en pagina 2
link = driver.find_element(By.LINK_TEXT, "2")
driver.execute_script("arguments[0].click();", link)
time.sleep(4)

# Extraer items de esa pagina
items = driver.execute_script("""
    const container = document.querySelector('#collapseThree, #divResol');
    return Array.from(container.querySelectorAll('.row')).map(r => ({
        text: r.textContent.trim().substring(0, 250),
        nids: Array.from(r.querySelectorAll('a[href*="documentoD"]'))
              .map(a => a.href.split('nid=')[-1])
    })).filter(r => r.text.length > 30);
""")
```

### Lo que se encontro por pagina

| Pagina | Items | Documentos |
|--------|-------|------------|
| 1 (Principal) | 5 items | ~18 Descargar (notificaciones) |
| 2 | ~35 items | ~18 Descargar (notificaciones) |
| 3 | No probado | No probado |

### Items tipicos del seguimiento

**Pagina 1:**
- Item 1: NOTA - "EXPEDIENTE SE REMITE AL TRIBUNAL CONSTITUCIONAL"
- Item 2: AUTO (Resolucion CUATRO) - Concedio recurso de agravio constitucional ✅ **DESCARGAR**
- Item 3: NOTA - "EXP. A RELATORIA CON ESCRITO NRO.3087-2024"
- Item 4: ESCRITO - Recurso de agravio constitucional (folios 21)
- Item 5: SENTENCIA DE VISTA (Resolucion TRES) - Confirmo improcedente ✅ **DESCARGAR**

**Pagina 2:**
- Items con Resoluciones DOS, TRES, S/N
- Notas y escritos varios
- Algunos con boton DESCARGAR

### Pendiente
- Implementar loop: `for page in ['2', '3']: click() -> extract() -> accumulate nids`
- Combinar todos los nids de todas las paginas
- Descargar todo en paralelo al final
- Probar si la pagina 3 tiene mas documentos o llega al final
