# Next.js App Router + FastAPI Integration Pattern

## Architecture

```
Frontend (Next.js 15, port 3000)  →  rewrites proxy  →  Backend (FastAPI, port 8000)
   src/lib/api.ts                      next.config.ts       app/main.py
   src/app/page.tsx (Home)                                  app/routers/articulos.py
   src/app/dashboard/page.tsx                                app/routers/busqueda.py
   src/app/chat/page.tsx                                     app/routers/consulta.py
   src/components/Sidebar.tsx
   src/lib/theme.tsx
```

## Step 1: API Proxy (next.config.ts)

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

## Step 2: Type-safe API Client (src/lib/api.ts)

```typescript
const API_BASE = ""; // Uses Next.js rewrites proxy — no localhost:8000 needed

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${res.statusText}`);
  return res.json();
}

// Typed interfaces for all API responses
export interface ArticuloCompleto { id, numero, titulo, libro, texto, incisos, vigencia, modificaciones, ... }
export interface SearchResult { score, article_id, numero, titulo, ... }
export interface ConsultaResponse { respuesta, fuentes, confidence }
```

## Step 3: Dark Mode ThemeProvider (src/lib/theme.tsx)

```tsx
"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type Theme = "light" | "dark";
const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({ theme: "light", toggle: () => {} });

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const saved = localStorage.getItem("theme") as Theme | null;
    const prefers = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initial = saved || (prefers ? "dark" : "light");
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
  }, []);

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
  };

  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
```

## Step 4: Layout with Sidebar (src/app/layout.tsx)

```tsx
import { ThemeProvider } from "@/lib/theme";
import { Sidebar } from "@/components/Sidebar";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="h-full bg-white dark:bg-slate-950 antialiased">
        <ThemeProvider>
          <div className="flex h-full">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

## Step 5: Sidebar with Active State (src/components/Sidebar.tsx)

```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/lib/theme";
import { BookOpen, MessageCircle, Scale } from "lucide-react";

const navItems = [
  { href: "/", label: "Inicio", icon: Scale },
  { href: "/dashboard", label: "Código Penal", icon: BookOpen },
  { href: "/chat", label: "Chat IA", icon: MessageCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r flex flex-col shrink-0">
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700" : "text-slate-600 hover:bg-slate-100"
              }`}>
              <Icon size={18} /> {item.label}
            </Link>
          );
        })}
      </nav>
      <button onClick={toggle} className="p-3 text-sm text-slate-500">
        {theme === "dark" ? "☀️ Modo Claro" : "🌙 Modo Oscuro"}
      </button>
    </aside>
  );
}
```

## Pitfalls

### useSearchParams requires Suspense boundary

**Symptom:** Next.js build fails with `⨯ useSearchParams() should be wrapped in a suspense boundary at page "/dashboard"`.

**Cause:** `useSearchParams()` triggers client-side rendering that Next.js can't statically prerender.

**Fix:** Split the page into a wrapper with Suspense:

```tsx
// /dashboard/page.tsx
"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function DashboardContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");
  // ... rest of component
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Cargando...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
```

### Tailwind v4 dark mode requires explicit custom variant

**Symptom:** `dark:` classes don't work in Tailwind v4 with `@import "tailwindcss"`.

**Fix:** Add to `globals.css`:
```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
```

### /mnt/d/ filesystem slowness with Next.js

**Symptom:** `npx next build` takes 5-10x longer than normal.

**Cause:** Windows filesystem mounted via 9p/drvfs has poor I/O for node_modules.

**Workaround:** Accept the slowness for builds. Dev server with turbopack is faster. For production builds, consider running on native Linux filesystem or using WSL2's native ext4 for node_modules.

## Dependencies

```bash
npm install lucide-react clsx tailwind-merge

# For chat streaming (next phase):
# npm install ai @ai-sdk/react
```

## Project Reference

`D:\PyCode\SkillEbookLegalWeb\mvp\frontend\` — Complete Next.js 15 frontend with 3 pages (Home, Dashboard, Chat), sidebar, dark mode, API proxy, and typed client library.
