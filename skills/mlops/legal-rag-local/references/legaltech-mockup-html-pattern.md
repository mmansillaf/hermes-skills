# Patrón: Mockups HTML para LegalTech MVP

## Estrategia

Construir 5 pantallas HTML autocontenidas con Tailwind CDN + vanilla JS, sin frameworks de build (no npm, no webpack, no React). Esto permite validar UX con stakeholders en horas, no semanas.

## Stack

```
HTML5 + Tailwind CSS CDN + Vanilla JS (ES6+)
Sin dependencias de build tools
Cada .html abre directo en el navegador
Navegación entre pantallas con <a href="...">
```

## Las 5 pantallas del MVP LegalTech

| # | Archivo | Funcionalidad | Complejidad |
|---|---------|--------------|:-----------:|
| 1 | `landing.html` | Hero, pricing 3 tiers, 6 features, testimonios, FAQ, dark/light, CTA | Media |
| 2 | `dashboard.html` | Layout 3-columnas: índice jerárquico + visor artículo + jurisprudencia. Buscador semántico con sugerencias, timeline de modificaciones | Alta |
| 3 | `chat.html` | Chat IA con streaming mock, citas badge clickeables, panel de fuentes, disclaimer legal modal, modo Abogado/Ciudadano, quick-ask buttons | Alta |
| 4 | `timemachine.html` | Slider de fechas 1991→2026 con versiones históricas reales de un artículo. Diff visual tachado/verde. Quick-jump por ley modificatoria | Media |
| 5 | `calculadora.html` | 13 delitos + 8 agravantes + 6 atenuantes + reincidencia + tentativa. Sistema de tercios automático con barras visuales | Media-Alta |

## Patrones CSS reutilizables

### Tailwind config inline (dark mode)
```html
<script>
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                gold: { 500: '#c9a84c', 400: '#d4b85c' }
            }
        }
    }
}
</script>
```

### Dark/light toggle (persiste en localStorage)
```js
function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', 
        document.documentElement.classList.contains('dark') ? 'dark' : 'light');
}
// Init
if (localStorage.getItem('theme') === 'dark') document.documentElement.classList.add('dark');
```

### Componentes compartidos (top bar de navegación)
```html
<header class="bg-surface dark:bg-slate-900 border-b h-14 flex items-center px-4 gap-4 sticky top-0 z-40">
    <a href="landing.html" class="flex items-center gap-2 font-bold text-lg">
        <span>⚖️</span> <span class="gradient-text">CP-Perú IA</span>
    </a>
    <div class="flex items-center gap-2 ml-auto">
        <a href="dashboard.html" class="btn-icon">📋</a>
        <a href="chat.html" class="btn-icon">💬</a>
        <a href="timemachine.html" class="btn-icon">🕰️</a>
        <a href="calculadora.html" class="btn-icon">🧮</a>
        <button onclick="toggleTheme()" class="btn-icon">🌓</button>
    </div>
</header>
```

## Datos mock

Usar datos realistas pero no reales:
- Nombres de abogados peruanos ficticios
- Artículos del CP reales (transcripción verificada de fuentes oficiales)
- Precios en soles (S/29/mes, S/99/mes)
- Testimonios en primera persona con formato "Dra. Nombre — Cargo"

## Transición a Next.js (Fase 3)

Los mockups sirven como spec visual. Cuando se migra a Next.js:
- Tailwind config se mueve a `tailwind.config.ts`
- JS vanilla → React hooks (`useState`, `useEffect`)
- `<a href>` → Next.js `<Link>` o `useRouter()`
- Datos mock → llamadas a API real (`fetch('/api/articulos')`)
- HTML plano → componentes React reutilizables

## Proyecto de referencia

`D:\PyCode\SkillEbookLegalWeb\mockups\` — 5 archivos HTML completos, 135KB total.
