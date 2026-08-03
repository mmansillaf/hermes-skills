# Plan: [Nombre de la Feature]

## Arquitectura General

```
[Cliente] ──> [Frontend] ──> [Backend] ──> [Base de Datos]
                              │
                              └──> [Servicios Externos]
```

## Data Model

### Tabla: [nombre]
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK |
| [campo] | [tipo] | [notas] |

## API Contracts

```
POST   /api/v1/[recurso]      # [descripcion]
GET    /api/v1/[recurso]      # [descripcion]
```

## Librerias y Justificacion

| Libreria | Proposito | Alternativa |
|----------|-----------|-------------|
| [lib] | [uso] | [alt] |

## Constitucion Check

- [ ] Lenguaje y framework segun constitucion
- [ ] Sin dependencias externas obligatorias no autorizadas
- [ ] i18n desde el inicio
- [ ] Multi-tenant / seguridad

## Opciones de Hosting

| Opcion | Costo/mes | Ideal si... |
|--------|-----------|-------------|
| [opcion] | ~$X | [caso de uso] |
