#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra — Importador de Artículos Individuales de WordPress
Permite importar cualquier artículo publicado en mealegroentupalabra.wordpress.com
o mealegroentupalabra.com y adaptarlo automáticamente a la arquitectura del blog:
- Descarga la imagen destacada y las imágenes internas.
- Optimiza automáticamente todas las imágenes a formato WebP (máx 1400px, calidad 82).
- Limpia y transforma bloques de Gutenberg a tarjetas bíblicas (.scripture-card).
- Genera el archivo Markdown en content/posts/YYYY-MM-DD-slug.md con frontmatter completo.
- Reconstruye el sitio estático automáticamente.

Uso:
  python3 import_post.py                             (Modo interactivo / selector de recientes)
  python3 import_post.py <url-o-slug>               (Importar URL o slug específico)
  python3 import_post.py --latest                    (Importar el artículo más reciente)
"""

import os
import re
import sys
import json
import html
import time
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import io

SITE_DOMAIN = "mealegroentupalabra.wordpress.com"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_DOMAIN}"
BASE_DIR = Path(__file__).resolve().parent
POSTS_DIR = BASE_DIR / "content" / "posts"
IMAGES_DIR = BASE_DIR / "assets" / "images" / "posts"
PUBLIC_IMAGES_DIR = BASE_DIR / "public" / "assets" / "images" / "posts"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml,image/webp,image/*,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://mealegroentupalabra.wordpress.com/"
}

# Regex to detect biblical citations (e.g. "Romanos 8:31-32", "1 Timoteo 6:6-10", "Salmos 23")
BIBLE_CITATION_PATTERN = re.compile(
    r'^\s*(?:(?:1|2|3|I|II|III|1º|2º)\s*)?'
    r'(?:G[eé]nesis|[EÉ]xodo|Lev[ií]tico|N[uú]meros|Deuteronomio|Josu[eé]|Jueces|Rut|'
    r'Samuel|Reyes|Cr[oó]nicas|Esdras|Nehem[ií]as|Ester|Job|Salmos?|Proverbios|Eclesiast[eé]s|'
    r'Cantares|Isa[ií]as|Jerem[ií]as|Lamentaciones|Ezequiel|Daniel|Oseas|Joel|Am[oó]s|Abd[ií]as|'
    r'Jon[aá]s|Miqueas|Nah[uú]m|Habacuc|Sofon[ií]as|Hageo|Zacar[ií]as|Malaqu[ií]as|Mateo|Marcos|'
    r'Lucas|Juan|Hechos|Romanos|Corintios|G[aá]latas|Efesios|Filipenses|Colosenses|'
    r'Tesalonicenses|Timoteo|Tito|Filem[oó]n|Hebreos|Santiago|Pedro|Judas|Apocalipsis)'
    r'\s+\d+(?::\d+(?:[–-]\d+)?)?'
    r'(?:\s*\((?:RVR60|NTV|TLA|NVI|DHH|LBLA|NBLA|BTX\d*|NBV|PDT|CST|BJ)\))?'
    r'\s*[\.,;]?\s*$',
    re.IGNORECASE
)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def clean_summary(text, max_len=180):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    plain = re.sub(r'\s+', ' ', plain).strip()
    if len(plain) > max_len:
        plain = plain[:max_len].rsplit(' ', 1)[0] + '...'
    return plain

def transform_url(url):
    """Transform internal WordPress links to local relative site paths."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    if 'mealegroentupalabra' not in domain:
        return url

    path = parsed.path.strip('/')
    if not path:
        return '/'

    if path == 'plan-de-lectura':
        return '/planes-de-lectura/'

    # Category links
    m_cat = re.match(r'^category/(?:la-biblia-en-un-ano/)?([^/]+)', path)
    if m_cat:
        cat_slug = m_cat.group(1)
        if cat_slug == 'la-biblia-en-un-ano':
            return '/la-biblia-en-un-ano/'
        return f'/categoria/{cat_slug}/'

    # Tag links
    m_tag = re.match(r'^tag/([^/]+)', path)
    if m_tag:
        return f'/etiqueta/{m_tag.group(1)}/'

    # Post links with date: YYYY/MM/DD/slug -> /posts/slug/
    m_post = re.match(r'^\d{4}/\d{2}/\d{2}/([^/]+)(?:/.*)?$', path)
    if m_post:
        return f'/posts/{m_post.group(1)}/'

    # Static pages
    if path in ['reflexiones', 'planes-de-lectura', 'la-biblia-en-un-ano', 'acerca-de', 'buscar', 'categorias', 'etiquetas']:
        return f'/{path}/'

    return f'/posts/{path}/'

def download_and_optimize_image(remote_url, dt):
    """
    Downloads an image from WordPress, resizes to max 1400px, converts to WebP,
    and saves it in assets/images/posts/YYYY/MM/.
    Returns the local web path (e.g. /assets/images/posts/2026/09/image.webp).
    """
    if not remote_url or not remote_url.startswith("http"):
        return remote_url

    # Strip query parameters (like ?w=768) to download the original full resolution
    clean_remote_url = remote_url.split("?")[0]
    parsed = urllib.parse.urlparse(clean_remote_url)
    raw_name = os.path.basename(parsed.path)
    stem = os.path.splitext(raw_name)[0]
    if not stem:
        stem = f"image_{hashlib.md5(remote_url.encode()).hexdigest()[:8]}"

    clean_stem = re.sub(r'[^a-zA-Z0-9._-]', '_', stem)
    webp_filename = f"{clean_stem}.webp"

    year_str = dt.strftime("%Y")
    month_str = dt.strftime("%m")

    dest_dir = IMAGES_DIR / year_str / month_str
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / webp_filename

    # If already downloaded and valid WebP, reuse it
    if dest_file.exists() and dest_file.stat().st_size > 0:
        local_web_path = f"/assets/images/posts/{year_str}/{month_str}/{webp_filename}"
        return local_web_path

    # Download
    req = urllib.request.Request(clean_remote_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            image_data = resp.read()
    except Exception as e:
        # Fallback to URL with query if stripped failed
        try:
            req = urllib.request.Request(remote_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                image_data = resp.read()
        except Exception as e2:
            print(f"  [Advertencia] No se pudo descargar la imagen {remote_url}: {e2}")
            return remote_url

    # Convert to WebP and resize
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img = ImageOps.exif_transpose(img)
            w, h = img.size
            max_w = 1400
            if w > max_w:
                new_h = int(h * (max_w / w))
                img = img.resize((max_w, new_h), Image.Resampling.LANCZOS)

            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(dest_file, 'WEBP', quality=85, method=6)
            else:
                img.convert('RGB').save(dest_file, 'WEBP', quality=82, method=6)

        # Also copy immediately to public/
        pub_dir = PUBLIC_IMAGES_DIR / year_str / month_str
        pub_dir.mkdir(parents=True, exist_ok=True)
        (pub_dir / webp_filename).write_bytes(dest_file.read_bytes())

        local_web_path = f"/assets/images/posts/{year_str}/{month_str}/{webp_filename}"
        return local_web_path
    except Exception as e:
        print(f"  [Advertencia] Error al procesar imagen a WebP ({remote_url}): {e}")
        return remote_url

def clean_and_transform_post_content(raw_html, dt):
    """
    Cleans WordPress Gutenberg blocks, converts pullquotes into Scripture cards,
    downloads and converts inline images to WebP, and rewrites internal links.
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove WordPress tracking pixels and comments
    for pixel in soup.find_all("img", src=re.compile(r"pixel\.wp\.com")):
        pixel.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, type(soup)) and "wp:" in text):
        comment.extract()

    # 2. Convert Gutenberg pullquotes to scripture-card
    for figure in soup.find_all("figure", class_=lambda c: c and "wp-block-pullquote" in c):
        bq = figure.find("blockquote")
        if bq:
            figure.name = "div"
            figure["class"] = ["scripture-card"]
            if figure.has_attr("style"):
                del figure["style"]
            cite = bq.find("cite")
            if cite and cite.has_attr("class"):
                del cite["class"]

    # 2b. Auto-detect and format Bible citations in all blockquotes
    for bq in soup.find_all("blockquote"):
        existing_cite = bq.find("cite")
        if existing_cite:
            if existing_cite.has_attr("class"):
                del existing_cite["class"]
        else:
            # Check last child paragraph
            paras = bq.find_all("p")
            if paras and BIBLE_CITATION_PATTERN.match(paras[-1].get_text(strip=True)):
                target_p = paras[-1]
                target_p.name = "cite"
                if target_p.has_attr("class"):
                    del target_p["class"]
            else:
                # Check next sibling element (sometimes reference is in a <p> right below blockquote)
                nxt = bq.find_next_sibling()
                if nxt and nxt.name == "p" and BIBLE_CITATION_PATTERN.match(nxt.get_text(strip=True)):
                    nxt.name = "cite"
                    if nxt.has_attr("class"):
                        del nxt["class"]
                    bq.append(nxt)

    # 3. Process and download all inline images to WebP
    for img in soup.find_all("img"):
        # Remove all WordPress metadata and tracking attributes (e.g. data-permalink, data-orig-file, data-large-file, data-attachment-id)
        for attr in list(img.attrs.keys()):
            if attr.startswith("data-"):
                del img[attr]

        src = img.get("src", "")
        if src.startswith("http"):
            local_webp = download_and_optimize_image(src, dt)
            img["src"] = local_webp
            if img.has_attr("srcset"):
                # Simplify srcset to local WebP
                img["srcset"] = f"{local_webp} 768w"

        # If wrapped in an <a> tag pointing to WordPress attachment/media or the image itself, unwrap it
        parent = img.parent
        if parent and parent.name == "a":
            href = parent.get("href", "")
            if "wordpress.com" in href or "wp-content" in href or href == src:
                parent.unwrap()

    # 4. Remove timeline bubbles & unwrap timeline items if reading plan
    for hr in soup.find_all("hr", class_=lambda c: c and "wp-block-coblocks-dynamic-separator" in c):
        hr.decompose()

    for bubble in soup.find_all("div", class_=lambda c: c and ("timeline-item__bubble" in c or "timeline-item__dot" in c)):
        bubble.decompose()

    for ul in soup.find_all("ul", class_=lambda c: c and "wp-block-jetpack-timeline" in c):
        ul.name = "div"
        ul["class"] = ["reading-plan-flow"]

    for li in soup.find_all("li", class_=lambda c: c and "wp-block-jetpack-timeline-item" in c):
        li.name = "div"
        if li.has_attr("style"):
            del li["style"]
        if li.has_attr("class"):
            del li["class"]

    for item in soup.find_all("div", class_="timeline-item"):
        item.unwrap()

    # 5. Clean inline styles and empty paragraphs
    for el in soup.find_all(True):
        for attr in list(el.attrs.keys()):
            if attr.startswith("data-"):
                del el[attr]

        if el.has_attr("style"):
            style = el["style"]
            if "wp--preset" in style or "background-color:#eee" in style or "background-color:#eeeeee" in style:
                new_style = re.sub(r'background-color:\s*#[a-fA-F0-9]+;?', '', style)
                new_style = re.sub(r'var\(--wp--preset[^\)]+\)', '', new_style).strip()
                if new_style and new_style != ";":
                    el["style"] = new_style
                else:
                    del el["style"]

        if el.has_attr("class"):
            classes = [c for c in el["class"] if not c.startswith("wp-container-") and not c.startswith("wp-elements-")]
            if classes:
                el["class"] = classes
            else:
                del el["class"]

    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()

    # 6. Rewrite internal links
    for a in soup.find_all("a", href=True):
        a["href"] = transform_url(a["href"])

    return str(soup)

def parse_identifier(input_str):
    """Extracts slug or ID from URL or input string."""
    input_str = input_str.strip()
    if not input_str:
        return None

    # Check if URL
    if input_str.startswith("http://") or input_str.startswith("https://") or "mealegroentupalabra" in input_str:
        parsed = urllib.parse.urlparse(input_str)
        path = parsed.path.strip("/")
        # Path format: 2026/09/29/aprende-a-vivir-contento/
        parts = [p for p in path.split("/") if p]
        if parts:
            return parts[-1]

    # Clean slug
    return slugify(input_str)

def get_existing_slugs():
    """Returns a set of slugs that already exist in content/posts/."""
    slugs = set()
    for f in POSTS_DIR.glob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r'^slug:\s*["\']?([^"\'\s\n]+)["\']?', content, re.MULTILINE)
            if m:
                slugs.add(m.group(1))
            else:
                # slug from filename YYYY-MM-DD-slug
                parts = f.stem.split("-", 3)
                if len(parts) >= 4:
                    slugs.add(parts[3])
                else:
                    slugs.add(f.stem)
        except Exception:
            pass
    return slugs

def import_post_by_slug_or_url(identifier, rebuild=True):
    """
    Imports a post from mealegroentupalabra.wordpress.com by slug or URL.
    Returns dict with details or raises Exception.
    """
    slug = parse_identifier(identifier)
    if not slug:
        raise ValueError(f"No se pudo determinar el slug o identificador de: {identifier}")

    print(f"\n[1/4] Consultando la API de WordPress para '{slug}'...")
    url = f"{API_BASE}/posts/slug:{slug}"
    try:
        p = fetch_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try searching by query
            search_url = f"{API_BASE}/posts?search={urllib.parse.quote(slug)}&number=1"
            sdata = fetch_json(search_url)
            posts = sdata.get("posts", [])
            if posts:
                p = posts[0]
            else:
                raise ValueError(f"No se encontró el artículo '{slug}' en {SITE_DOMAIN} (Error 404)")
        else:
            raise e

    title = html.unescape(p.get("title", "Sin título")).strip()
    date_str = p.get("date", "")
    try:
        dt = datetime.fromisoformat(date_str)
    except Exception:
        dt = datetime.now()

    date_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
    date_prefix = dt.strftime("%Y-%m-%d")
    post_slug = p.get("slug") or slugify(title)

    print(f"  • Título: {title}")
    print(f"  • Fecha:  {date_formatted}")
    print(f"  • Slug:   {post_slug}")

    # Process featured image
    print(f"[2/4] Procesando y optimizando imagen destacada...")
    featured_img_remote = p.get("featured_image", "")
    featured_img_local = ""
    if featured_img_remote:
        featured_img_local = download_and_optimize_image(featured_img_remote, dt)
        print(f"  • Imagen destacada guardada: {featured_img_local}")

    # Process content and inline images
    print(f"[3/4] Procesando contenido e imágenes internas a WebP...")
    raw_content = p.get("content", "")
    content = clean_and_transform_post_content(raw_content, dt)

    categories = list(p.get("categories", {}).keys())
    tags = list(p.get("tags", {}).keys())
    excerpt = p.get("excerpt", "")
    summary = clean_summary(excerpt or raw_content)

    # Build Frontmatter
    frontmatter = [
        "---",
        f'title: "{title.replace("\"", "\\\"")}"',
        f'date: {date_formatted}',
        f'slug: "{post_slug}"',
    ]

    if categories:
        frontmatter.append(f'category: "{categories[0]}"')
        frontmatter.append(f'categories: {json.dumps(categories, ensure_ascii=False)}')
    else:
        frontmatter.append('category: "Reflexiones"')
        frontmatter.append('categories: ["Reflexiones"]')

    if tags:
        frontmatter.append(f'tags: {json.dumps(tags, ensure_ascii=False)}')
    else:
        frontmatter.append('tags: []')

    if featured_img_local:
        frontmatter.append(f'image: "{featured_img_local}"')

    frontmatter.append(f'summary: "{summary.replace("\"", "\\\"")}"')
    frontmatter.append(f'original_url: "{p.get("URL", "")}"')
    frontmatter.append("---\n")

    filename = f"{date_prefix}-{post_slug}.md"
    filepath = POSTS_DIR / filename
    filepath.write_text("\n".join(frontmatter) + content, encoding="utf-8")
    print(f"  • Archivo Markdown creado: content/posts/{filename}")

    # Rebuild site
    if rebuild:
        print(f"[4/4] Recompilando el sitio...")
        from build import SiteBuilder
        builder = SiteBuilder()
        builder.build()

    post_url = f"/posts/{post_slug}/"
    print("\n" + "=" * 60)
    print(f"✅ ¡Artículo importado con éxito!")
    print(f" • Título:     {title}")
    print(f" • Archivo:    content/posts/{filename}")
    print(f" • URL local:  {post_url}")
    print("=" * 60)

    return {
        "success": True,
        "title": title,
        "slug": post_slug,
        "filename": filename,
        "url": post_url,
        "date": date_formatted,
        "categories": categories,
        "tags": tags,
        "image": featured_img_local,
        "summary": summary
    }

def interactive_mode():
    print("=" * 60)
    print(" 📖  Me Alegro En Tu Palabra — Importador de Artículos")
    print("=" * 60)
    print("Consultando los artículos más recientes en WordPress...")
    
    try:
        data = fetch_json(f"{API_BASE}/posts?number=6")
        posts = data.get("posts", [])
    except Exception as e:
        print(f"Error al conectar con WordPress: {e}")
        posts = []

    existing_slugs = get_existing_slugs()

    if posts:
        print("\nÚltimos artículos publicados en tu sitio original:")
        for idx, p in enumerate(posts, 1):
            title = html.unescape(p.get("title", "Sin título"))
            p_slug = p.get("slug", "")
            p_date = p.get("date", "")[:10]
            status = " [Ya importado]" if p_slug in existing_slugs else " ⭐ [NUEVO]"
            print(f"  [{idx}] {title} ({p_date}){status}")

    print("\nOpciones:")
    print("  • Escribe el número del artículo (ej. 1)")
    print("  • O pega la URL completa del artículo")
    print("  • O escribe el slug")
    print("  • O escribe 'q' para cancelar")

    choice = input("\nIngresa tu opción: ").strip()
    if not choice or choice.lower() == 'q':
        print("Operación cancelada.")
        return

    if choice.isdigit() and 1 <= int(choice) <= len(posts):
        selected_post = posts[int(choice) - 1]
        import_post_by_slug_or_url(selected_post.get("slug"))
    else:
        import_post_by_slug_or_url(choice)

def sync_new_posts(limit=20, rebuild=True):
    """
    Checks the latest posts in WordPress and automatically imports
    any post that does not exist in content/posts/.
    Returns list of newly imported posts.
    """
    print(f"\n[Sincronización] Consultando los últimos {limit} artículos en WordPress...")
    try:
        data = fetch_json(f"{API_BASE}/posts?number={limit}")
        posts = data.get("posts", [])
    except Exception as e:
        print(f"[Error de conexión con WordPress]: {e}")
        return []

    existing_slugs = get_existing_slugs()
    new_posts = [p for p in posts if p.get("slug") and p.get("slug") not in existing_slugs]

    if not new_posts:
        print("✅ No hay nuevas publicaciones en WordPress. El sitio está al día.")
        return []

    print(f"⭐ Se encontraron {len(new_posts)} publicaciones nuevas para importar.")
    # Process from oldest to newest among the new ones
    new_posts.reverse()
    imported = []

    for idx, p in enumerate(new_posts, 1):
        slug = p.get("slug")
        title = html.unescape(p.get("title", ""))
        print(f"\n({idx}/{len(new_posts)}) Importando: '{title}' ({slug})...")
        try:
            res = import_post_by_slug_or_url(slug, rebuild=False)
            imported.append(res)
        except Exception as e:
            print(f"  [Error al importar '{slug}']: {e}")

    if imported and rebuild:
        print(f"\n[Reconstrucción] Compilando el sitio con los {len(imported)} nuevos artículos...")
        from build import SiteBuilder
        builder = SiteBuilder()
        builder.build()
        print(f"✅ ¡Sincronización completada! {len(imported)} artículos importados y sitio compilado.")

    return imported

def watch_wordpress(interval_minutes=15):
    """
    Runs a polling loop checking for new WordPress posts every N minutes.
    """
    print("=" * 60)
    print(f" 👀 Me Alegro En Tu Palabra — Monitor Automático de WordPress")
    print(f" Comprobando publicaciones cada {interval_minutes} minutos...")
    print(" Presiona Ctrl+C para detener el monitor.")
    print("=" * 60)

    sync_new_posts()

    while True:
        try:
            time.sleep(interval_minutes * 60)
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Comprobando nuevas publicaciones en WordPress...")
            sync_new_posts()
        except KeyboardInterrupt:
            print("\nMonitor detenido.")
            break

def import_latest():
    print("Buscando el artículo más reciente no importado...")
    data = fetch_json(f"{API_BASE}/posts?number=10")
    posts = data.get("posts", [])
    existing_slugs = get_existing_slugs()

    for p in posts:
        slug = p.get("slug")
        if slug and slug not in existing_slugs:
            title = html.unescape(p.get("title"))
            print(f"Encontrado nuevo artículo: '{title}' ({slug})")
            return import_post_by_slug_or_url(slug)

    print("Todos los artículos recientes de WordPress ya se encuentran importados.")
    return None

if __name__ == "__main__":
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg in ("--latest", "-l"):
            import_latest()
        elif arg in ("--sync", "--auto", "-s", "-a"):
            sync_new_posts()
        elif arg in ("--watch", "-w"):
            interval = 15
            if len(sys.argv) > 2 and sys.argv[2].isdigit():
                interval = int(sys.argv[2])
            watch_wordpress(interval)
        elif arg in ("--help", "-h"):
            print(__doc__)
        else:
            import_post_by_slug_or_url(arg)
    else:
        interactive_mode()
