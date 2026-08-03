# LinkedIn OAuth — Creación de App Developer

## ⚠️ Regla crítica

El navegador automatizado NO puede iniciar sesión en LinkedIn. El usuario debe seguir estos pasos en su propio navegador. El agente solo da las instrucciones y recibe los códigos.

## Paso a paso para crear la App

### 1. Ir a la página de creación

Abrir en navegador propio:
```
https://www.linkedin.com/developers/apps/new
```

### 2. Llenar el formulario "Create an app"

| Campo | Qué poner | Ejemplo |
|-------|-----------|---------|
| **App name** | Nombre descriptivo | `HermesLinkedInMCP` |
| **LinkedIn Page** | URL de una página de empresa de LinkedIn | Crear página temporal si no hay: `https://www.linkedin.com/company/<nombre>` |

Para crear página temporal:
1. Clic en icono "Yo" → "Crear una página de empresa"
2. Elegir "Empresa pequeña" (la más simple)
3. Poner nombre, handle (e.g. `/company/hermes-mcp-local`)
4. Publicar con datos mínimos

### 3. Aceptar términos

Marcar:
- "I have read and agree to these terms"
- Verificar que la página de LinkedIn seleccionada existe (no usar "Developer Portal" — es de LinkedIn y rechaza)

Hacer clic en **"Create app"**.

### 4. Ir a la pestaña Auth

Una vez creada la app, navegar a la pestaña **Auth** (autenticación).

Copiar:
- **Client ID** — se ve como `86...abc` (string de ~14 caracteres alfanuméricos)
- **Client Secret** — se ve como `WPL_...` (string largo que empieza con `WPL_`)

### 5. Configurar OAuth 2.0

En **OAuth 2.0 settings**:

1. **Authorized Redirect URLs** → agregar:
   ```
   http://localhost:3000/callback
   ```
2. Hacer clic en **Add** y luego **Update** (guardar cambios).

### 6. Habilitar productos

Ir a la pestaña **Products** (o desde Auth, revisar si ya están habilitados).

Para linkedin-mcp-server se necesita como mínimo:
- **Sign In with LinkedIn** (para obtener token de usuario)
- **Share on LinkedIn** (para publicar contenido)

Habilitar:
1. Buscar "Sign In with LinkedIn" → **Request access**
2. Buscar "Share on LinkedIn" → **Request access**

> Algunos productos requieren verificación de app o pasar por un review. Para uso personal/local no suele ser necesario — con los productos básicos basta.

### 7. Entregar credenciales al agente

Pegar estos dos valores en el chat con Hermes:
- `Client ID: <el código>`
- `Client Secret: <el código>`

## Lo que hará el agente después

1. Escribir las credenciales en `config.yaml` bajo `mcp_servers.linkedin`
2. El usuario reinicia Hermes (`hermes` en terminal)
3. Ejecutar autenticación OAuth: aceptar en navegador el permiso de LinkedIn
4. El server MCP queda conectado

## Posibles problemas

| Problema | Solución |
|----------|----------|
| "LinkedIn Page not found" al crear app | Crear página de empresa temporal desde el perfil |
| OAuth redirect mismatch | Asegurarse que `http://localhost:3000/callback` está EXACTAMENTE así (con http, no https) |
| Producto no disponible | Usar "Sign In with LinkedIn" como mínimo — no requiere review |
| 403 al publicar | El token puede no tener scope suficiente → regenerar OAuth |
| Client Secret no visible | LinkedIn oculta el secret después de salir de la página — copiar antes de cerrar |
