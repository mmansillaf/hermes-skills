# Cloudflare Access vs FastAPI JWT — Autenticación para El Peruano RAG

**Fecha:** 01-may-2026

## Comparativa

| Aspecto | Cloudflare Access | FastAPI + JWT propio |
|---------|-------------------|---------------------|
| Usuarios gratis | 50 | **Ilimitado** |
| Usuarios de pago | $7/usuario/mes | $0 |
| Login Google/GitHub | ✅ Nativo | ✅ python-social-auth |
| Código necesario | 0 líneas | ~80 líneas |
| Planes de suscripción | ❌ No | ✅ Stripe |
| Rate limiting | Workers KV | FastAPI middleware |
| Panel admin | Cloudflare Dashboard | Construir propio |

## Recomendación: FastAPI + JWT

Para 500-1000 usuarios, Cloudflare Access de pago costaría $3,500-$7,000/mes. FastAPI + JWT es gratis e ilimitado.

### Código mínimo (~80 líneas)

```python
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "your-secret"
pwd_context = CryptContext(schemes=["bcrypt"])

# Modelo de usuario
class User:
    email: str
    plan: str  # "free", "pro", "enterprise"
    daily_queries: int = 0

# Login con email/password
@app.post("/auth/login")
async def login(email: str, password: str):
    user = db.get_user(email)
    if not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(401)
    token = jwt.encode({"sub": email, "plan": user.plan}, SECRET_KEY)
    return {"access_token": token}

# Login con Google OAuth (opcional)
@app.get("/auth/google")
async def google_login(code: str):
    # Intercambiar code por token con Google
    user_info = google_verify(code)
    user = db.get_or_create_user(user_info["email"])
    token = jwt.encode({"sub": user.email, "plan": user.plan}, SECRET_KEY)
    return {"access_token": token}

# Middleware de autenticación
async def get_current_user(authorization: str = Header(None)):
    try:
        payload = jwt.decode(authorization.split()[1], SECRET_KEY)
        return {"email": payload["sub"], "plan": payload["plan"]}
    except:
        raise HTTPException(401)

# Endpoint protegido con rate limiting
@app.post("/query")
async def query(req: QueryRequest, user = Depends(get_current_user)):
    if user["plan"] == "free" and user_daily_count(user["email"]) >= 10:
        raise HTTPException(429, "Límite diario: 10 consultas")
    result = process_query(req.question)
    increment_user_count(user["email"])
    return result
```

## Planes de suscripción sugeridos

| Plan | Consultas/día | Precio | Implementación |
|------|--------------|--------|---------------|
| Free | 10 | $0 | Registro automático |
| Pro | 100 | $10/mes | Stripe Checkout |
| Enterprise | API key ilimitada | $30/mes | Stripe + panel admin |
