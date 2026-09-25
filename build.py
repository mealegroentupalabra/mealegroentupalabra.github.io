#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra - Static Site Generator
Compiles Markdown posts, pages, and taxonomy into high-performance static HTML for GitHub Pages.
"""

import os
import sys
import re
import json
import shutil
import math
import http.server
import socketserver
from datetime import datetime
from pathlib import Path
import html
from bs4 import BeautifulSoup
import yaml
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt

# Initialize Markdown parser
md_parser = MarkdownIt("commonmark").enable("table").enable("strikethrough")

MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

def format_date_es(dt):
    if not dt:
        return ""
    return f"{dt.day} de {MESES_ES[dt.month]} de {dt.year}"

def format_date_rfc822(dt):
    if not dt:
        return ""
    # Example: Wed, 09 Sep 2026 18:00:38 +0000
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

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

def calculate_reading_time(text):
    if not text:
        return "1 min"
    words = len(re.findall(r'\w+', text))
    minutes = max(1, math.ceil(words / 200))
    return f"{minutes} min"

def strip_html(html_str):
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    return soup.get_text(" ", strip=True)

class SiteBuilder:
    def __init__(self, config_path="config.json", output_dir="public"):
        self.config_path = config_path
        self.output_dir = output_dir
        self.load_config()
        
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=True
        )
        self.jinja_env.globals.update({
            "site_title": self.config.get("site_title", "Me Alegro En Tu Palabra"),
            "site_tagline": self.config.get("site_tagline", ""),
            "site_description": self.config.get("site_description", ""),
            "site_url": self.config.get("site_url", ""),
            "base_path": self.config.get("base_path", ""),
            "author": self.config.get("author", {}),
            "nav": self.config.get("nav", []),
            "google_analytics": self.config.get("google_analytics", ""),
            "reftagger": self.config.get("reftagger", {"enabled": True, "bible_version": "RVR60", "round_corners": True}),
            "current_year": datetime.now().year,
        })

    def load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def parse_markdown_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_content = f.read()

        parts = raw_content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                print(f"Error parsing frontmatter in {filepath}: {e}")
                frontmatter = {}
            body = parts[2].strip()
        else:
            frontmatter = {}
            body = raw_content.strip()

        return frontmatter, body

    def transform_url(self, url):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if "mealegroentupalabra" not in domain:
            return url
        
        path = parsed.path.strip("/")
        base = self.config.get("base_path", "")
        
        if not path:
            return f"{base}/" if base else "/"
        
        if path == "plan-de-lectura":
            return f"{base}/planes-de-lectura/"
        
        m_cat = re.match(r"^category/(?:la-biblia-en-un-ano/)?([^/]+)", path)
        if m_cat:
            cat_slug = m_cat.group(1)
            if cat_slug == "la-biblia-en-un-ano":
                return f"{base}/la-biblia-en-un-ano/"
            return f"{base}/categoria/{cat_slug}/"

        m_tag = re.match(r"^tag/([^/]+)", path)
        if m_tag:
            return f"{base}/etiqueta/{m_tag.group(1)}/"

        m_post = re.match(r"^\d{4}/\d{2}/\d{2}/([^/]+)", path)
        if m_post:
            return f"{base}/posts/{m_post.group(1)}/"

        if path in ["reflexiones", "planes-de-lectura", "la-biblia-en-un-ano", "acerca-de", "buscar", "categorias", "etiquetas"]:
            return f"{base}/{path}/"

        return f"{base}/posts/{path}/"

    def render_content(self, body_text):
        if body_text.strip().startswith("<") and "</" in body_text:
            rendered = body_text
        else:
            rendered = md_parser.render(body_text)

        soup = BeautifulSoup(rendered, "html.parser")

        # Remove timeline bubbles and dots
        for bubble in soup.find_all("div", class_=lambda c: c and ("timeline-item__bubble" in c or "timeline-item__dot" in c)):
            bubble.decompose()

        # Unwrap timeline items
        for ul in soup.find_all("ul", class_=lambda c: c and "wp-block-jetpack-timeline" in c):
            ul.name = "div"
            ul["class"] = "reading-plan-flow"

        for li in soup.find_all("li", class_=lambda c: c and "wp-block-jetpack-timeline-item" in c):
            li.name = "div"
            if li.has_attr("style"):
                del li["style"]
            if li.has_attr("class"):
                del li["class"]

        for item in soup.find_all("div", class_="timeline-item"):
            item.unwrap()

        # Remove background-color:#eeeeee card backgrounds
        for el in soup.find_all(True):
            if el.has_attr("style") and ("background-color:#eee" in el["style"] or "background-color:#eeeeee" in el["style"]):
                new_style = re.sub(r"background-color:\s*#[a-fA-F0-9]+;?", "", el["style"]).strip()
                if new_style:
                    el["style"] = new_style
                else:
                    del el["style"]

        # Rewrite internal links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "mealegroentupalabra" in href and "/wp-content/uploads/" not in href:
                a["href"] = self.transform_url(href)

        return str(soup)

    def load_posts(self):
        posts = []
        posts_dir = Path("content/posts")
        if not posts_dir.exists():
            return posts

        for file_path in posts_dir.glob("*.md"):
            fm, body = self.parse_markdown_file(file_path)
            title = fm.get("title", file_path.stem)
            slug = fm.get("slug") or slugify(title)
            
            # Parse date
            raw_date = fm.get("date")
            dt = None
            if isinstance(raw_date, datetime):
                dt = raw_date
            elif isinstance(raw_date, str):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.strptime(raw_date[:19], fmt[:19])
                        break
                    except ValueError:
                        pass
            if not dt:
                # Fallback to filename prefix YYYY-MM-DD
                m = re.match(r"^(\d{4}-\d{2}-\d{2})", file_path.stem)
                if m:
                    dt = datetime.strptime(m.group(1), "%Y-%m-%d")
                else:
                    dt = datetime.now()

            category = fm.get("category", "Reflexiones")
            categories_list = fm.get("categories", [category])
            if not isinstance(categories_list, list):
                categories_list = [categories_list]

            raw_tags = fm.get("tags", [])
            if not isinstance(raw_tags, list):
                raw_tags = [t.strip() for t in str(raw_tags).split(",") if t.strip()]

            tags = [{"name": t, "slug": slugify(t)} for t in raw_tags if t]

            content_html = self.render_content(body)
            plain_text = strip_html(content_html)
            
            summary = fm.get("summary")
            if not summary:
                summary = plain_text[:180] + "..." if len(plain_text) > 180 else plain_text

            image = fm.get("image", "")

            reading_time = calculate_reading_time(plain_text)
            date_formatted = format_date_es(dt)
            date_rfc822 = format_date_rfc822(dt)
            date_iso = dt.strftime("%Y-%m-%d")

            url = f"{self.config.get('base_path', '')}/posts/{slug}/"

            posts.append({
                "title": title,
                "slug": slug,
                "url": url,
                "date": dt,
                "date_iso": date_iso,
                "date_formatted": date_formatted,
                "pub_date_rfc822": date_rfc822,
                "category": category,
                "category_slug": slugify(category),
                "categories": categories_list,
                "tags": tags,
                "image": image,
                "summary": summary,
                "content_html": content_html,
                "plain_text": plain_text,
                "reading_time": reading_time,
                "source_file": str(file_path)
            })

        # Sort posts by date descending
        posts.sort(key=lambda p: p["date"], reverse=True)
        return posts

    def load_pages(self):
        pages = []
        pages_dir = Path("content/pages")
        if not pages_dir.exists():
            return pages

        for file_path in pages_dir.glob("*.md"):
            fm, body = self.parse_markdown_file(file_path)
            title = fm.get("title", file_path.stem.capitalize())
            slug = fm.get("slug") or slugify(file_path.stem)
            content_html = self.render_content(body)
            plain_text = strip_html(content_html)
            summary = fm.get("summary") or (plain_text[:160] + "..." if len(plain_text) > 160 else plain_text)

            url = f"{self.config.get('base_path', '')}/{slug}/"

            pages.append({
                "title": title,
                "slug": slug,
                "url": url,
                "content_html": content_html,
                "summary": summary,
                "source_file": str(file_path)
            })

        return pages

    def build(self):
        print(f"Building site into '{self.output_dir}'...")
        out_dir = Path(self.output_dir)
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy assets
        if os.path.exists("assets"):
            shutil.copytree("assets", out_dir / "assets")
            print("Copied assets/")

        # Write .nojekyll
        (out_dir / ".nojekyll").write_text("", encoding="utf-8")

        # Load data
        posts = self.load_posts()
        pages = self.load_pages()
        print(f"Loaded {len(posts)} posts and {len(pages)} static pages.")

        # Build taxonomies
        categories_map = {}
        tags_map = {}

        for p in posts:
            cat_name = p["category"]
            cat_slug = p["category_slug"]
            if cat_slug not in categories_map:
                categories_map[cat_slug] = {"name": cat_name, "slug": cat_slug, "count": 0, "posts": []}
            categories_map[cat_slug]["count"] += 1
            categories_map[cat_slug]["posts"].append(p)

            for t in p["tags"]:
                t_slug = t["slug"]
                if t_slug not in tags_map:
                    tags_map[t_slug] = {"name": t["name"], "slug": t_slug, "count": 0, "posts": []}
                tags_map[t_slug]["count"] += 1
                tags_map[t_slug]["posts"].append(p)

        categories_list = sorted(categories_map.values(), key=lambda c: -c["count"])
        
        # Calculate tag cloud font sizes
        tags_list = sorted(tags_map.values(), key=lambda t: -t["count"])
        max_tag_count = max([t["count"] for t in tags_list]) if tags_list else 1
        min_tag_count = min([t["count"] for t in tags_list]) if tags_list else 1
        
        for t in tags_list:
            if max_tag_count > min_tag_count:
                weight = (t["count"] - min_tag_count) / (max_tag_count - min_tag_count)
            else:
                weight = 0.5
            t["font_size"] = round(0.78 + (weight * 0.7), 2)  # between 0.78rem and 1.48rem

        # Assign prev/next and related posts
        for i, post in enumerate(posts):
            post["next_post"] = posts[i - 1] if i > 0 else None
            post["prev_post"] = posts[i + 1] if i < len(posts) - 1 else None

            # Find up to 3 related posts (same category or overlapping tags)
            related = []
            for other in posts:
                if other["slug"] == post["slug"]:
                    continue
                score = 0
                if other["category"] == post["category"]:
                    score += 2
                tag_names = {t["name"] for t in post["tags"]}
                other_tags = {t["name"] for t in other["tags"]}
                score += len(tag_names.intersection(other_tags))
                if score > 0:
                    related.append((score, other))
            
            related.sort(key=lambda x: x[0], reverse=True)
            post["related_posts"] = [r[1] for r in related[:3]]

        # Generate Search Index JSON
        search_data = []
        for p in posts:
            search_data.append({
                "title": p["title"],
                "slug": p["slug"],
                "url": p["url"],
                "date": p["date_iso"],
                "date_formatted": p["date_formatted"],
                "category": p["category"],
                "category_slug": p["category_slug"],
                "tags": [t["name"] for t in p["tags"]],
                "summary": p["summary"],
                "content": p["plain_text"][:1200],  # first 1200 chars for deep search
                "reading_time": p["reading_time"]
            })
        
        (out_dir / "search.json").write_text(json.dumps(search_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Generated search.json index.")

        # Render Individual Posts
        post_tmpl = self.jinja_env.get_template("post.html")
        for p in posts:
            post_dir = out_dir / "posts" / p["slug"]
            post_dir.mkdir(parents=True, exist_ok=True)
            html_out = post_tmpl.render(
                post=p,
                canonical_url=f"{self.config.get('site_url')}{p['url']}",
                current_path=f"posts/{p['slug']}/",
                prev_post=p["prev_post"],
                next_post=p["next_post"],
                related_posts=p["related_posts"]
            )
            (post_dir / "index.html").write_text(html_out, encoding="utf-8")
        print(f"Rendered {len(posts)} post pages.")

        # Render Home Page with Pagination
        index_tmpl = self.jinja_env.get_template("index.html")
        per_page = self.config.get("posts_per_page", 12)
        total_posts = len(posts)
        total_pages = max(1, math.ceil(total_posts / per_page))

        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * per_page
            end_idx = start_idx + per_page
            page_posts = posts[start_idx:end_idx]

            featured_post = posts[0] if page_num == 1 and posts else None
            # If on page 1, we show featured post + remaining posts for the page
            grid_posts = page_posts[1:] if (page_num == 1 and featured_post) else page_posts

            prev_url = f"{self.config.get('base_path', '')}/" if page_num == 2 else f"{self.config.get('base_path', '')}/pagina/{page_num - 1}/"
            next_url = f"{self.config.get('base_path', '')}/pagina/{page_num + 1}/"

            html_out = index_tmpl.render(
                posts=grid_posts,
                featured_post=featured_post,
                page_num=page_num,
                total_pages=total_pages,
                total_posts=total_posts,
                has_prev=(page_num > 1),
                has_next=(page_num < total_pages),
                prev_page_url=prev_url,
                next_page_url=next_url,
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/" if page_num == 1 else f"{self.config.get('site_url')}{self.config.get('base_path', '')}/pagina/{page_num}/",
                current_path="" if page_num == 1 else f"pagina/{page_num}/"
            )

            if page_num == 1:
                (out_dir / "index.html").write_text(html_out, encoding="utf-8")
            else:
                p_dir = out_dir / "pagina" / str(page_num)
                p_dir.mkdir(parents=True, exist_ok=True)
                (p_dir / "index.html").write_text(html_out, encoding="utf-8")
        print(f"Rendered home and {total_pages} paginated pages.")

        # Render Category Archive Pages
        cat_tmpl = self.jinja_env.get_template("category.html")
        for cat in categories_list:
            c_dir = out_dir / "categoria" / cat["slug"]
            c_dir.mkdir(parents=True, exist_ok=True)
            html_out = cat_tmpl.render(
                category_name=cat["name"],
                category_slug=cat["slug"],
                posts=cat["posts"],
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/categoria/{cat['slug']}/",
                current_path=f"categoria/{cat['slug']}/"
            )
            (c_dir / "index.html").write_text(html_out, encoding="utf-8")

        # Render Categories Index Page (/categorias/)
        cats_idx_tmpl = self.jinja_env.get_template("categories_index.html")
        cats_dir = out_dir / "categorias"
        cats_dir.mkdir(parents=True, exist_ok=True)
        (cats_dir / "index.html").write_text(
            cats_idx_tmpl.render(
                categories=categories_list,
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/categorias/",
                current_path="categorias/"
            ),
            encoding="utf-8"
        )
        print("Rendered category archives.")

        # Render Tag Archive Pages
        tag_tmpl = self.jinja_env.get_template("tag.html")
        for tag in tags_list:
            t_dir = out_dir / "etiqueta" / tag["slug"]
            t_dir.mkdir(parents=True, exist_ok=True)
            html_out = tag_tmpl.render(
                tag_name=tag["name"],
                tag_slug=tag["slug"],
                posts=tag["posts"],
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/etiqueta/{tag['slug']}/",
                current_path=f"etiqueta/{tag['slug']}/"
            )
            (t_dir / "index.html").write_text(html_out, encoding="utf-8")

        # Render Tags Index Page (/etiquetas/)
        tags_idx_tmpl = self.jinja_env.get_template("tags_index.html")
        tags_dir = out_dir / "etiquetas"
        tags_dir.mkdir(parents=True, exist_ok=True)
        (tags_dir / "index.html").write_text(
            tags_idx_tmpl.render(
                tags=tags_list,
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/etiquetas/",
                current_path="etiquetas/"
            ),
            encoding="utf-8"
        )
        print("Rendered tag archives.")

        # Render Dedicated Search Page (/buscar/)
        search_tmpl = self.jinja_env.get_template("search.html")
        search_dir = out_dir / "buscar"
        search_dir.mkdir(parents=True, exist_ok=True)
        (search_dir / "index.html").write_text(
            search_tmpl.render(
                top_categories=categories_list[:8],
                top_tags=tags_list[:20],
                canonical_url=f"{self.config.get('site_url')}{self.config.get('base_path', '')}/buscar/",
                current_path="buscar/"
            ),
            encoding="utf-8"
        )
        print("Rendered dedicated search page.")

        # Render Static Pages (acerca-de, reflexiones, etc.)
        page_tmpl = self.jinja_env.get_template("page.html")
        for pg in pages:
            p_dir = out_dir / pg["slug"]
            p_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if this page matches a category name (e.g. reflexiones, planes-de-lectura, la-biblia-en-un-ano)
            matched_cat_slug = slugify(pg["title"])
            page_posts = categories_map.get(matched_cat_slug, {}).get("posts", [])
            
            html_out = page_tmpl.render(
                page=pg,
                page_posts=page_posts,
                canonical_url=f"{self.config.get('site_url')}{pg['url']}",
                current_path=f"{pg['slug']}/"
            )
            (p_dir / "index.html").write_text(html_out, encoding="utf-8")
        print(f"Rendered {len(pages)} static pages.")

        # Render RSS Feed
        feed_tmpl = self.jinja_env.get_template("feed.xml")
        feed_out = feed_tmpl.render(
            posts=posts,
            build_date=format_date_rfc822(datetime.now())
        )
        (out_dir / "feed.xml").write_text(feed_out, encoding="utf-8")
        print("Rendered feed.xml.")

        # Render Sitemap
        sitemap_tmpl = self.jinja_env.get_template("sitemap.xml")
        sitemap_out = sitemap_tmpl.render(
            posts=posts,
            static_pages=pages,
            categories=categories_list
        )
        (out_dir / "sitemap.xml").write_text(sitemap_out, encoding="utf-8")
        print("Rendered sitemap.xml.")

        # Render Robots.txt
        robots_content = f"""User-agent: *
Allow: /
Sitemap: {self.config.get('site_url')}{self.config.get('base_path', '')}/sitemap.xml
"""
        (out_dir / "robots.txt").write_text(robots_content, encoding="utf-8")
        print("Rendered robots.txt.")

        print(f"\nSite build completed successfully into '{self.output_dir}'!")

def serve(directory="public", port=8000):
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\nServing site at http://localhost:{port}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    builder = SiteBuilder()
    builder.build()

    if "--serve" in sys.argv:
        port = 8000
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        serve(directory="public", port=port)
