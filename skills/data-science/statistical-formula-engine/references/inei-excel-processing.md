# Procesamiento de Excel del INEI — Patrones descubiertos

Este archivo documenta los patrones estructurales y quirks encontrados al procesar
cuadros estadísticos del INEI en formato Excel (.xlsx). El usuario (abogado peruano
investigando inclusión financiera territorial con CMAC) trabaja regularmente con
datos del INEI, SBS, BCRP.

## Estructura típica de un cuadro INEI

```
Filas 0-4:   Título del cuadro (celdas combinadas, NaN en columnas datos)
             Ej: "PERÚ: Producto Bruto Interno por Años, según Departamentos"
             "Valores a precios constantes de 2007 (Miles de soles)"
Fila 5:      Año del PBI base de referencia (ej: "2023") — fila fantasma, ignorar
Fila 6:      HEADER real — nombres de columnas: "Departamentos", "2007", "2008", ..., "2024E/"
Fila 7:      Fila vacía (separador) — ignorar
Fila 8+:     DATOS — un departamento por fila
             Últimas filas: agregados (Valor Agregado Bruto, Derechos de Importación,
             Producto Bruto Interno), luego "Fuente: ...", "Nota: ..."
```

**Comando de lectura estándar:**
```python
df = pd.read_excel('archivo.xlsx', sheet_name='Cuadro1', skiprows=6)
# skiprows=6 elimina título + header anidado
```

## Problemas comunes y soluciones

### 1. Columnas con nombres "Unnamed"

Los headers anidados del INEI producen columnas como "Unnamed: 1", "Unnamed: 2", etc.
La fila de header real suele estar en la fila 6 (0-indexed tras skiprows).

**Solución:** renombrar manualmente con los años como nombres de columna:
```python
anos = list(range(2007, 2025))  # ajustar según el archivo
df.columns = ['Departamento'] + anos
```

### 2. Departamentos con tildes

INEI usa nombres con acentos: "Áncash", "Apurímac", "Huánuco", "Junín".
El filtrado con `.str.contains()` o comparación directa falla si el patrón no tiene acento.

**Solución:** normalizar con unicodedata antes de comparar:
```python
import unicodedata
def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()

deptos_buscados = ['Ancash', 'Apurimac', 'Huanuco', 'Junin']  # sin acentos
mask = df['Departamento'].apply(lambda x: any(d in norm(x) for d in deptos_buscados))
```

### 3. Filas de agregados y notas

Las filas finales incluyen "Valor Agregado Bruto", "Derechos de Importación",
"Producto Bruto Interno", "Fuente: ...", "Nota: ...".

**Solución:** filtrar explícitamente:
```python
excluir = ['fuente', 'valor agregado', 'derechos', 'impuestos',
           'producto bruto', 'con informacion', 'nota']
mask = df['Departamento'].apply(lambda x: not any(e in norm(x) for e in excluir))
```

### 4. Notación de estimación INEI

| Sufijo | Significado |
|--------|-------------|
| Sin marca | Cifra definitiva |
| `P/` | Cifra preliminar |
| `E/` | Cifra estimada |

Ejemplo en columnas: "2022P/", "2023P/", "2024E/"
Los sufijos aparecen como parte del nombre de columna. Al renombrar con enteros,
se pierden — documentar en el reporte qué años son P/ o E/.

### 5. Lima desagregado en 3 filas

INEI separa Lima en 3 registros distintos:
- `Provincia de Lima` — Lima centro (aprox. 36% del PBI)
- `Región Lima` — provincias de Lima excepto Lima centro
- `Prov. Const. del Callao` — Callao como entidad separada

Al calcular totales o promedios, decidir si:
- Sumar los 3 (para PBI de Lima metropolitana)
- Usar solo "Provincia de Lima" (para Lima centro)
- Excluir los 3 y trabajar solo con provincias (para análisis territorial sin Lima)

### 6. Valores numéricos con separador de miles

Los valores en el Excel de INEI usan punto como separador de miles (1,234,567).
pandas.read_excel() los lee correctamente como float si el Excel está bien formateado.
Si vienen como string, limpiar con:
```python
df['columna'] = df['columna'].str.replace(',', '').astype(float)
```

## Estructura típica de cuadros INEI (PBI departamental)

El archivo `PBI_departamentos_2007_2024.xlsx` contiene 6 hojas con esta estructura:

| Hoja | Contenido | Unidad | Columnas | 
|------|-----------|--------|----------|
| Cuadro1 | PBI real (precios constantes 2007) | Miles S/ | 2007..2024E |
| Cuadro2 | Participación VAB en PBI real | % | 2007..2024E |
| Cuadro3 | Variación % índice volumen físico | % | 2007..2024E |
| Cuadro4 | PBI nominal (precios corrientes) | Miles S/ | 2007..2024E |
| Cuadro5 | Participación VAB en PBI nominal | % | 2007..2024E |
| Cuadro6 | Variación % índice de precios | % | 2007..2024E |

El usuario tiene este archivo en `D:\Descargas\UPN-Investigacion\PBI_departamentos_2007_2024.xlsx`
y el venv en `D:\Descargas\UPN-Investigacion\venv_stats_ml\`.

## Script de extracción probado

```python
import pandas as pd, unicodedata

def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode().lower()

def leer_pbi_inei(ruta, hoja='Cuadro1'):
    """Lee PBI departamental INEI. Retorna DataFrame con 24 deptos."""
    df = pd.read_excel(ruta, sheet_name=hoja, skiprows=6)
    df = df[df.iloc[:,0].notna()]

    deptos = ['Amazonas','Ancash','Apurimac','Arequipa','Ayacucho','Cajamarca',
              'Cusco','Huancavelica','Huanuco','Ica','Junin','La Libertad',
              'Lambayeque','Loreto','Madre de Dios','Moquegua','Pasco','Piura',
              'Puno','San Martin','Tacna','Tumbes','Ucayali']
    excluir = ['fuente','valor agregado','derechos','impuestos',
               'producto bruto','con informacion','nota']

    mask = df.iloc[:,0].apply(
        lambda x: any(d in norm(x) for d in [norm(d2) for d2 in deptos])
                  and not any(e in norm(x) for e in excluir))
    data = df[mask].copy()
    anos = list(range(2007, 2025))
    data.columns = ['Departamento'] + anos[:data.shape[1]-1]
    return data
```

## Notas adicionales

- Los datos se actualizan anualmente (noviembre). El archivo más reciente tiene info
  hasta "15 de Noviembre del 2025".
- Los valores son en miles de soles. Para millones, dividir entre 1,000.
- La fila "Producto Bruto Interno" al final del cuadro es el PBI nacional total
  (incluye Valor Agregado Bruto + Impuestos a los Productos + Derechos de Importación).
