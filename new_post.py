#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra - Post Management & Creation Backend
Provides core functions for creating, editing, and listing blog posts,
as well as extracting dynamic taxonomies (categories and tags).
"""

import os
import sys
import re
import glob
import json
import yaml
from datetime import datetime
from pathlib import Path

POSTS_DIR = Path("content/posts")
POSTS_DIR.mkdir(parents=True, exist_ok=True)

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

def get_all_taxonomies():
    """Extract all categories and tags dynamically across all existing posts."""
    cat_counts = {}
    tag_counts = {}

    for fpath in POSTS_DIR.glob("*.md"):
        try:
            content = fpath.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1])
                if not fm:
                    continue
                
                # Categories
                post_cats = fm.get("categories", [])
                if isinstance(post_cats, str):
                    post_cats = [post_cats]
                cat = fm.get("category")
                if cat and cat not in post_cats:
                    post_cats.append(cat)
                
                for c in post_cats:
                    c = str(c).strip()
                    if c:
                        cat_counts[c] = cat_counts.get(c, 0) + 1

                # Tags
                post_tags = fm.get("tags", [])
                if isinstance(post_tags, str):
                    post_tags = [t.strip() for t in post_tags.split(",") if t.strip()]
                for t in post_tags:
                    t = str(t).strip()
                    if t:
                        tag_counts[t] = tag_counts.get(t, 0) + 1
        except Exception:
            pass

    # Sort categories by popularity, keeping top themes at top
    categories = sorted(cat_counts.items(), key=lambda x: -x[1])
    tags = sorted(tag_counts.items(), key=lambda x: -x[1])

    return {
        "categories": [{"name": c[0], "count": c[1]} for c in categories],
        "tags": [{"name": t[0], "count": t[1]} for t in tags]
    }

def get_all_posts():
    """List all existing posts with summary metadata for the editor drawer."""
    posts = []
    for fpath in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        try:
            content = fpath.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                title = fm.get("title", fpath.stem)
                slug = fm.get("slug", slugify(title))
                date_val = str(fm.get("date", ""))[:10]
                category = fm.get("category", "Reflexiones")
                categories = fm.get("categories", [category])
                if isinstance(categories, str):
                    categories = [categories]
                tags = fm.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]

                featured_val = fm.get("featured", False)
                is_featured = bool(featured_val) and str(featured_val).lower() not in ("false", "0", "no")

                posts.append({
                    "filename": fpath.name,
                    "title": title,
                    "slug": slug,
                    "date": date_val,
                    "category": category,
                    "categories": categories,
                    "tags": tags,
                    "image": fm.get("image", ""),
                    "summary": fm.get("summary", ""),
                    "featured": is_featured
                })
        except Exception:
            pass
    
    # Sort posts by date descending
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts

def get_post_by_file(filename):
    """Load full frontmatter and body content for an existing post."""
    clean_fn = os.path.basename(filename)
    fpath = POSTS_DIR / clean_fn
    if not fpath.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {clean_fn}")

    content = fpath.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) >= 3:
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].lstrip("\n")
        
        category = fm.get("category", "Reflexiones")
        categories = fm.get("categories", [category])
        if isinstance(categories, str):
            categories = [categories]
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        featured_val = fm.get("featured", False)
        is_featured = bool(featured_val) and str(featured_val).lower() not in ("false", "0", "no")

        return {
            "filename": clean_fn,
            "title": fm.get("title", ""),
            "slug": fm.get("slug", slugify(fm.get("title", clean_fn))),
            "date": str(fm.get("date", "")),
            "category": category,
            "categories": categories,
            "tags": tags,
            "image": fm.get("image", ""),
            "summary": fm.get("summary", ""),
            "featured": is_featured,
            "original_url": fm.get("original_url", ""),
            "content": body
        }
    return {
        "filename": clean_fn,
        "title": clean_fn,
        "slug": slugify(clean_fn),
        "date": "",
        "category": "Reflexiones",
        "categories": ["Reflexiones"],
        "tags": [],
        "image": "",
        "summary": "",
        "content": content
    }

def save_post_data(data):
    """
    Creates or updates a post markdown file.
    data fields:
      - filename (optional; if provided and exists, updates that file)
      - title (str, required)
      - categories (list or str, required)
      - tags (list or str)
      - summary (str)
      - image (str)
      - content (str)
      - slug (optional)
    """
    title = data.get("title", "").strip()
    if not title:
        raise ValueError("El título del artículo es obligatorio.")

    categories = data.get("categories", [])
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",") if c.strip()]
    if not categories:
        cat_single = data.get("category", "Reflexiones").strip()
        categories = [cat_single] if cat_single else ["Reflexiones"]

    primary_category = categories[0]

    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    summary = data.get("summary", "").strip()
    image = data.get("image", "").strip()
    content = data.get("content", "")

    filename = data.get("filename", "").strip()
    now = datetime.now()

    if filename and (POSTS_DIR / filename).exists():
        # Updating existing post
        fpath = POSTS_DIR / filename
        # Read existing date if available
        existing_fm = {}
        try:
            raw_c = fpath.read_text(encoding="utf-8")
            parts = raw_c.split("---", 2)
            if len(parts) >= 3:
                existing_fm = yaml.safe_load(parts[1]) or {}
        except Exception:
            pass

        date_str = str(existing_fm.get("date")) if existing_fm.get("date") else now.strftime("%Y-%m-%d %H:%M:%S")
        slug = existing_fm.get("slug") or data.get("slug") or slugify(title)
        is_new = False
    else:
        # Creating brand new post
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        date_prefix = now.strftime("%Y-%m-%d")
        slug = data.get("slug") or slugify(title)
        filename = f"{date_prefix}-{slug}.md"
        fpath = POSTS_DIR / filename
        if fpath.exists():
            slug = f"{slug}-{now.strftime('%H%M%S')}"
            filename = f"{date_prefix}-{slug}.md"
            fpath = POSTS_DIR / filename
        is_new = True

    featured = bool(data.get("featured", False))
    if featured:
        # If this post is set as featured, unmark any other post
        for other_path in POSTS_DIR.glob("*.md"):
            if other_path.name != filename:
                try:
                    c = other_path.read_text(encoding="utf-8")
                    if re.search(r'(?m)^featured:\s*(true|True|yes|1)', c):
                        new_c = re.sub(r'(?m)^featured:\s*(true|True|yes|1)\s*\n?', '', c)
                        other_path.write_text(new_c, encoding="utf-8")
                except Exception:
                    pass

    frontmatter = [
        "---",
        f'title: "{title.replace("\"", "\\\"")}"',
        f'date: {date_str}',
        f'slug: "{slug}"',
        f'category: "{primary_category}"',
        f'categories: {json.dumps(categories, ensure_ascii=False)}',
        f'tags: {json.dumps(tags, ensure_ascii=False)}',
    ]

    if featured:
        frontmatter.append("featured: true")

    if image:
        frontmatter.append(f'image: "{image}"')
    if summary:
        frontmatter.append(f'summary: "{summary.replace("\"", "\\\"")}"')

    original_url = data.get("original_url") or existing_fm.get("original_url")
    if original_url:
        frontmatter.append(f'original_url: "{original_url}"')

    frontmatter.append("---\n")
    full_text = "\n".join(frontmatter) + content.lstrip("\n")

    fpath.write_text(full_text, encoding="utf-8")

    return {
        "filepath": str(fpath),
        "filename": filename,
        "slug": slug,
        "is_new": is_new,
        "url": f"/posts/{slug}/"
    }

def interactive_mode():
    print("=" * 60)
    print(" 📖  Me Alegro En Tu Palabra — CLI de Artículos")
    print("=" * 60)
    title = input("\n1. Título del artículo: ").strip()
    while not title:
        title = input("El título es obligatorio: ").strip()

    tax = get_all_taxonomies()
    print("\n2. Categorías disponibles:")
    for idx, c in enumerate(tax["categories"][:10], 1):
        print(f"   [{idx}] {c['name']} ({c['count']})")
    print(f"   [{min(11, len(tax['categories']) + 1)}] Otra categoría")

    choice = input("Elige categoría principal (1-11) [1]: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= min(10, len(tax["categories"])):
        category = tax["categories"][int(choice) - 1]["name"]
    else:
        category = input("Nombre de categoría: ").strip() or "Reflexiones"

    tags_in = input("\n3. Etiquetas separadas por coma: ").strip()
    summary = input("\n4. Resumen breve (opcional): ").strip()
    image = input("\n5. URL de imagen (opcional): ").strip()

    res = save_post_data({
        "title": title,
        "categories": [category],
        "tags": tags_in,
        "summary": summary,
        "image": image,
        "content": "Escribe aquí tu contenido..."
    })

    print(f"\n✅ ¡Artículo guardado! {res['filepath']}")
    rebuild = input("¿Compilar sitio ahora? (S/n): ").strip().lower()
    if rebuild in ("", "s", "si", "y", "yes"):
        from build import SiteBuilder
        SiteBuilder().build()
        print("🚀 ¡Sitio compilado!")

if __name__ == "__main__":
    interactive_mode()
