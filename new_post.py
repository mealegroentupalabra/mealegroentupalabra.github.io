#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra - Article Creator CLI
Easily create and publish new blog posts.
Usage:
  Interactive mode:
    python3 new_post.py

  Direct mode:
    python3 new_post.py "Título del Artículo" --category "Reflexiones" --tags "fe, gracia, oración" --summary "Resumen breve..."
"""

import os
import sys
import re
import argparse
from datetime import datetime
import json

POSTS_DIR = "content/posts"

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_existing_categories():
    categories = ["Reflexiones", "Planes de Lectura", "La Biblia en un Año"]
    if os.path.exists(POSTS_DIR):
        for f in os.listdir(POSTS_DIR):
            if f.endswith(".md"):
                try:
                    with open(os.path.join(POSTS_DIR, f), "r", encoding="utf-8") as file:
                        for line in file:
                            if line.startswith("category:"):
                                cat = line.split(":", 1)[1].strip().strip('"\'')
                                if cat and cat not in categories:
                                    categories.append(cat)
                                break
                except Exception:
                    pass
    return categories

def create_post(title, category="Reflexiones", tags=None, summary="", image="", content=""):
    os.makedirs(POSTS_DIR, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_prefix = now.strftime("%Y-%m-%d")
    slug = slugify(title)
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    if os.path.exists(filepath):
        print(f"\n⚠️  Aviso: Ya existe un archivo con este nombre: {filepath}")
        slug = f"{slug}-{now.strftime('%H%M%S')}"
        filename = f"{date_prefix}-{slug}.md"
        filepath = os.path.join(POSTS_DIR, filename)

    if not tags:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    if not content:
        content = f"""Escribe aquí el contenido de tu reflexión o estudio bíblico...

<div class="scripture-card">
  <blockquote>
    «Lámpara es a mis pies tu palabra, y lumbrera a mi camino.»
    <cite class="scripture-cite">Salmo 119:105</cite>
  </blockquote>
</div>

Puedes usar formato estándar de Markdown:
- **Texto en negrita**
- *Texto en cursiva*
- [Enlaces a recursos](https://bibleproject.com/)
- Listas y encabezados (## Subtítulo)
"""

    frontmatter = [
        "---",
        f'title: "{title.replace("\"", "\\\"")}"',
        f'date: {date_str}',
        f'slug: "{slug}"',
        f'category: "{category}"',
        f'categories: ["{category}"]',
        f'tags: {json.dumps(tags, ensure_ascii=False)}',
    ]

    if image:
        frontmatter.append(f'image: "{image}"')
    if summary:
        frontmatter.append(f'summary: "{summary.replace("\"", "\\\"")}"')

    frontmatter.append("---\n")

    full_text = "\n".join(frontmatter) + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n✅ ¡Artículo creado con éxito!")
    print(f"📄 Archivo: {filepath}")
    print(f"🔗 Slug: {slug}")
    return filepath

def interactive_mode():
    print("=" * 60)
    print(" 📖  Me Alegro En Tu Palabra — Publicar Nuevo Artículo")
    print("=" * 60)

    title = input("\n1. Título del artículo: ").strip()
    while not title:
        title = input("El título es obligatorio. Escribe un título: ").strip()

    existing_cats = get_existing_categories()
    print("\n2. Selecciona una categoría:")
    for idx, cat in enumerate(existing_cats[:8], 1):
        print(f"   [{idx}] {cat}")
    print(f"   [{len(existing_cats[:8]) + 1}] Otra categoría (escribir nueva)")

    cat_choice = input(f"Elige una opción (1-{len(existing_cats[:8]) + 1}) [por defecto: 1]: ").strip()
    if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(existing_cats[:8]):
        category = existing_cats[int(cat_choice) - 1]
    elif cat_choice == str(len(existing_cats[:8]) + 1):
        category = input("Escribe el nombre de la nueva categoría: ").strip() or "Reflexiones"
    else:
        category = existing_cats[0]

    tags_input = input("\n3. Etiquetas / Temas (separados por coma, ej: fe, oración, gracia): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    summary = input("\n4. Resumen breve para tarjetas y redes (opcional): ").strip()
    image = input("\n5. URL de imagen destacada (opcional, ej: assets/images/... o URL externa): ").strip()

    filepath = create_post(title, category, tags, summary, image)

    # Ask if user wants to rebuild site now
    rebuild = input("\n¿Deseas compilar el sitio ahora con el nuevo artículo? (S/n): ").strip().lower()
    if rebuild in ("", "s", "si", "y", "yes"):
        from build import SiteBuilder
        builder = SiteBuilder()
        builder.build()
        print("\n🚀 ¡Sitio compilado y listo para ver o subir a GitHub Pages!")

def main():
    parser = argparse.ArgumentParser(description="Crear un nuevo artículo para Me Alegro En Tu Palabra")
    parser.add_argument("title", nargs="?", help="Título del artículo")
    parser.add_argument("-c", "--category", default="Reflexiones", help="Categoría del artículo")
    parser.add_argument("-t", "--tags", default="", help="Etiquetas separadas por coma")
    parser.add_argument("-s", "--summary", default="", help="Resumen del artículo")
    parser.add_argument("-i", "--image", default="", help="Ruta o URL de la imagen destacada")
    parser.add_argument("--build", action="store_true", help="Compilar el sitio inmediatamente")

    args = parser.parse_args()

    if args.title:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        filepath = create_post(args.title, args.category, tags, args.summary, args.image)
        if args.build:
            from build import SiteBuilder
            builder = SiteBuilder()
            builder.build()
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
