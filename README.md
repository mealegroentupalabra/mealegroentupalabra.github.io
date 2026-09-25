# Me Alegro En Tu Palabra — Blog para GitHub Pages

Sitio web estático moderno, elegante y optimizado para **GitHub Pages**, diseñado para el blog cristiano y reflexiones bíblicas **Me Alegro En Tu Palabra** (*«Descubre el tesoro de Dios para ti»*).

Este proyecto incluye la **migración completa de los 293 artículos y páginas** desde `mealegroentupalabra.wordpress.com`, preservando el logo oficial, enlaces, categorías y etiquetas temáticas.

---

## 🌟 Características Principales

1. **Diseño Editorial Elegante y Optimizado:**
   - Tipografía editorial clásica y legible: cabeceras con *Newsreader* (serif) y lectura descansada con *Plus Jakarta Sans*.
   - Paleta de colores cálida y solemne (Azul bíblico `#1a365d`, acentos dorados/ámbar `#b45309`, fondos apergaminados y modo oscuro automático/manual).
   - Componentes especiales para pasajes bíblicos (`.scripture-card`) con citas destacadas.
   - Cálculo automático de tiempo de lectura (ej. `⏱️ 4 min`).
   - Barra superior de progreso de lectura interactiva.
   - Botones rápidos para compartir en redes: WhatsApp, Telegram, X (Twitter), Facebook y copia de enlace.
   - Tarjeta de autor con biografía y enlaces a redes de Alejandro Morales.

2. **Búsqueda Instantánea Inteligente:**
   - Buscador rápido con modal global (atajo de teclado `⌘K` / `Ctrl+K` o tecla `/`).
   - Página dedicada de búsqueda en `/buscar/`.
   - **Búsqueda contextual por taxonomía**: busca por título, texto completo, **categorías** y **etiquetas** simultáneamente, resaltando coincidencias.
   - Filtros dinámicos en vivo por categoría y temas frecuentes.

3. **Organización por Categorías y Etiquetas:**
   - Página índice de categorías (`/categorias/`) y archivos individuales (`/categoria/<nombre>/`).
   - Directorio de etiquetas con nube ponderada (`/etiquetas/`) y archivos individuales (`/etiqueta/<nombre>/`).
   - Páginas dedicadas para las series principales:
     - [Reflexiones](/reflexiones/)
     - [Planes de Lectura](/planes-de-lectura/)
     - [La Biblia en un Año](/la-biblia-en-un-ano/)
     - [Acerca de](/acerca-de/)

4. **Publicación Sencilla de Nuevos Artículos (3 Métodos):**
   - **Editor Visual en el Navegador**: Escribe en un formulario con vista previa en vivo y publica con 1 clic.
   - **Asistente por Terminal**: Ejecuta `python3 new_post.py` y responde las preguntas interactivas.
   - **Markdown Directo**: Crea un archivo `.md` en `content/posts/` con formato estándar.

5. **Métricas y Analítica:**
   - Integración nativa con **Google Analytics (GA4)** mediante `config.json`.
   - Seguimiento automático de visitas, búsquedas internas, temas explorados y artículos compartidos.

6. **Automatización en GitHub Pages:**
   - Flujo de trabajo en `.github/workflows/deploy.yml` que compila y publica automáticamente en cada `git push`.
   - Generación de RSS 2.0 (`feed.xml`), `sitemap.xml`, `robots.txt` y metadatos OpenGraph / Twitter Cards para compartir en WhatsApp y redes sociales.

---

## 🚀 Inicio Rápido (Local)

### 1. Iniciar el servidor local y editor visual
Ejecuta en tu terminal:
```bash
python3 serve.py
```
Abre en tu navegador:
- **Ver el blog:** [http://localhost:8000/](http://localhost:8000/)
- **Editor visual de artículos:** [http://localhost:8000/editor/](http://localhost:8000/editor/)

---

## ✍️ Cómo Publicar Nuevos Artículos

Tienes tres opciones sencillas:

### Opción A: Desde el Editor Visual (Recomendado)
1. Con el servidor corriendo (`python3 serve.py`), entra a [http://localhost:8000/editor/](http://localhost:8000/editor/).
2. Escribe el título, selecciona la categoría, ingresa las etiquetas y redacta tu contenido con vista previa instantánea.
3. Puedes hacer clic en **"📖 Cita Bíblica"** para insertar un bloque formateado para versículos.
4. Haz clic en **"Publicar Artículo"**. El artículo se guardará en `content/posts/` y el sitio se actualizará inmediatamente.

### Opción B: Mediante el Asistente Interactivo en Terminal
Ejecuta:
```bash
python3 new_post.py
```
El asistente te guiará preguntándote el título, categoría y etiquetas. Al terminar, compilará el blog de inmediato.

O también puedes pasar los datos directamente en un solo comando:
```bash
python3 new_post.py "La Fidelidad de Dios" -c "Reflexiones" -t "fidelidad, gracia, promesa" --build
```

### Opción C: Creando un archivo Markdown manualmente
Crea un archivo en `content/posts/YYYY-MM-DD-mi-titulo.md`:
```markdown
---
title: "La Fidelidad de Dios"
date: 2026-09-25 10:00:00
category: "Reflexiones"
categories: ["Reflexiones"]
tags: ["fidelidad", "gracia", "promesa"]
image: "https://ejemplo.com/imagen.jpg"
summary: "Breve resumen para la tarjeta y redes sociales..."
---

Escribe aquí tu reflexión en Markdown...

<div class="scripture-card">
  <blockquote>
    «El Señor es mi pastor; nada me faltará.»
    <cite class="scripture-cite">Salmo 23:1</cite>
  </blockquote>
</div>

Continúa con tus párrafos...
```
Luego ejecuta:
```bash
python3 build.py
```

---

## 🌐 Cómo Desplegar en GitHub Pages

Para publicar tu blog en GitHub Pages:

### Paso 1: Inicializar el repositorio Git y subirlo a GitHub
```bash
git init
git add .
git commit -m "Inicializar blog Me Alegro En Tu Palabra con artículos migrados"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

### Paso 2: Activar GitHub Pages en el repositorio
1. En GitHub, ve a tu repositorio &rarr; **Settings** &rarr; pestaña **Pages**.
2. En la sección **Build and deployment** &rarr; **Source**, selecciona:
   - **GitHub Actions**
3. ¡Listo! El archivo `.github/workflows/deploy.yml` se ejecutará de forma automática y tu sitio estará en línea en:
   `https://TU_USUARIO.github.io/TU_REPOSITORIO/` (o en tu dominio personalizado).

> **Nota para subdirectorios:** Si tu repositorio no es la página de usuario raíz (ej. si la URL es `https://usuario.github.io/maetp`), abre `config.json` y cambia `"base_path": ""` por `"base_path": "/maetp"`, luego ejecuta `python3 build.py` y sube los cambios.

---

## ⚙️ Configuración (`config.json`)

Edita el archivo `config.json` para personalizar los ajustes globales del blog:

```json
{
  "site_title": "Me Alegro En Tu Palabra",
  "site_tagline": "Descubre el tesoro de Dios para ti",
  "site_description": "Reflexiones bíblicas, planes de lectura y estudio de las Escrituras para descubrir la gloria de Dios en Jesucristo.",
  "site_url": "https://alemormez.github.io",
  "base_path": "",
  "posts_per_page": 12,
  "google_analytics": "G-XXXXXXXXXX",
  "author": {
    "name": "Alejandro Morales",
    "bio": "Yo me alegro en la Palabra de Dios porque en ella puedo ver la gloria de Dios en la faz de Jesucristo.",
    "avatar": "assets/images/logo.png",
    "social": {
      "youtube": "https://www.youtube.com/c/AlejandroMorales",
      "twitter": "https://twitter.com/alemormez",
      "facebook": "https://www.facebook.com/mealegroentupalabra",
      "instagram": "https://instagram.com/alejandromoralesmeza",
      "linktree": "https://linktr.ee/alemormez"
    }
  }
}
```

### Configuración de Google Analytics (GA4)
1. Ve a [Google Analytics](https://analytics.google.com/) y crea una propiedad Web para tu blog.
2. Copia tu **ID de Medición** (formato `G-XXXXXXXXXX`).
3. Pégalo en el campo `"google_analytics"` de `config.json`.
4. Recompila con `python3 build.py` y sube el commit. Las estadísticas comenzarán a registrarse inmediatamente.

---

## 📁 Estructura del Proyecto

```
maetp/
├── .github/
│   └── workflows/
│       └── deploy.yml        # Automatización de despliegue en GitHub Pages
├── assets/
│   ├── css/
│   │   └── style.css         # Estilos elegantes, modo oscuro, responsive
│   ├── js/
│   │   ├── main.js           # Tema, menú móvil, compartir, lectura
│   │   └── search.js         # Buscador instantáneo con taxonomía
│   └── images/
│       ├── logo.png          # Logo oficial de Me Alegro En Tu Palabra
│       ├── favicon.png       # Favicon e iconos para navegadores y móviles
│       └── ...
├── content/
│   ├── posts/                # 293 artículos migrados en Markdown
│   └── pages/                # Páginas estáticas (acerca-de, reflexiones...)
├── templates/                # Plantillas Jinja2 HTML modulares
│   ├── base.html
│   ├── index.html
│   ├── post.html
│   ├── page.html
│   ├── category.html
│   ├── tag.html
│   ├── search.html
│   ├── feed.xml
│   └── sitemap.xml
├── public/                   # Sitio web 100% estático generado
├── config.json               # Configuración global del sitio
├── build.py                  # Compilador ultra-rápido (< 5 segundos)
├── serve.py                  # Servidor local con editor web en /editor/
├── new_post.py               # Generador de artículos por terminal
└── migrate_wordpress.py      # Script de migración desde WordPress
```

---

## 📄 Licencia y Créditos
- Contenido por **Alejandro Morales** bajo licencia [Creative Commons Atribución-NoComercial 4.0 Internacional (CC BY-NC 4.0)](http://creativecommons.org/licenses/by-nc/4.0/).
- Recursos y referencias bíblicas conectadas con: [Proyecto Biblia](https://bibleproject.com/) y [Study Light](https://studylight.org/).
