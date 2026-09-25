#!/usr/bin/env python3
"""
Migrate posts and pages from mealegroentupalabra.wordpress.com via its public REST API.
Saves posts to content/posts/ and pages to content/pages/ with YAML frontmatter.
"""

import os
import re
import json
import time
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup
import html

SITE_DOMAIN = "mealegroentupalabra.wordpress.com"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{SITE_DOMAIN}"

POSTS_DIR = "content/posts"
PAGES_DIR = "content/pages"

os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(PAGES_DIR, exist_ok=True)

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

def clean_html_content(raw_html):
    """
    Cleans WordPress Gutenberg blocks and formats pullquotes/blockquotes nicely.
    """
    if not raw_html:
        return ""
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Remove WordPress tracking pixels and comments
    for pixel in soup.find_all("img", src=re.compile(r"pixel\.wp\.com")):
        pixel.decompose()
        
    for comment in soup.find_all(string=lambda text: isinstance(text, type(soup)) and "wp:" in text):
        comment.extract()

    # Convert Gutenberg pullquotes to standard blockquotes with custom class
    for figure in soup.find_all("figure", class_=lambda c: c and "wp-block-pullquote" in c):
        bq = figure.find("blockquote")
        if bq:
            # Add scripture-quote class
            figure.name = "div"
            figure["class"] = "scripture-card"
            if figure.has_attr("style"):
                del figure["style"]
            cite = bq.find("cite")
            if cite:
                cite["class"] = "scripture-cite"

    # Clean empty paragraphs
    for p in soup.find_all("p"):
        if not p.get_text(strip=True) and not p.find("img"):
            p.decompose()

    # Clean inline styles from wp blocks
    for el in soup.find_all(True):
        if el.has_attr("style") and "wp--preset" in str(el["style"]):
            del el["style"]
        if el.has_attr("class"):
            # keep only meaningful classes
            classes = [c for c in el["class"] if not c.startswith("wp-container-") and not c.startswith("wp-elements-")]
            if classes:
                el["class"] = classes
            else:
                del el["class"]

    return str(soup)

def clean_summary(text, max_len=180):
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    plain = soup.get_text(" ", strip=True)
    plain = re.sub(r'\s+', ' ', plain).strip()
    if len(plain) > max_len:
        plain = plain[:max_len].rsplit(' ', 1)[0] + '...'
    return plain

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Migration Script)'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def migrate_posts():
    print("--- Migrating Posts ---")
    offset = 0
    total_migrated = 0
    
    while True:
        url = f"{API_BASE}/posts?number=100&offset={offset}"
        try:
            data = fetch_json(url)
            posts = data.get("posts", [])
            if not posts:
                break

            for p in posts:
                title = html.unescape(p.get("title", "Sin título")).strip()
                date_str = p.get("date", "")
                dt = datetime.fromisoformat(date_str)
                date_formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
                date_prefix = dt.strftime("%Y-%m-%d")
                
                slug = p.get("slug") or slugify(title)
                filename = f"{date_prefix}-{slug}.md"
                filepath = os.path.join(POSTS_DIR, filename)

                categories = list(p.get("categories", {}).keys())
                tags = list(p.get("tags", {}).keys())
                featured_image = p.get("featured_image", "")
                excerpt = p.get("excerpt", "")
                summary = clean_summary(excerpt or p.get("content", ""))

                content = clean_html_content(p.get("content", ""))

                frontmatter = [
                    "---",
                    f'title: "{title.replace("\"", "\\\"")}"',
                    f'date: {date_formatted}',
                    f'slug: "{slug}"',
                ]

                if categories:
                    frontmatter.append(f'category: "{categories[0]}"')
                    frontmatter.append(f'categories: {json.dumps(categories, ensure_ascii=False)}')
                else:
                    frontmatter.append('category: "General"')
                    frontmatter.append('categories: ["General"]')

                if tags:
                    frontmatter.append(f'tags: {json.dumps(tags, ensure_ascii=False)}')
                else:
                    frontmatter.append('tags: []')

                if featured_image:
                    frontmatter.append(f'image: "{featured_image}"')

                frontmatter.append(f'summary: "{summary.replace("\"", "\\\"")}"')
                frontmatter.append(f'original_url: "{p.get("URL", "")}"')
                frontmatter.append("---\n")

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(frontmatter))
                    f.write(content)

                total_migrated += 1

            offset += len(posts)
            print(f"Migrated {total_migrated}/{data.get('found', 0)} posts...")
            if offset >= data.get("found", 0):
                break
            time.sleep(0.3)
        except Exception as e:
            print(f"Error fetching batch at offset {offset}: {e}")
            break

    print(f"Finished migrating {total_migrated} posts!")

def migrate_pages():
    print("--- Migrating Pages ---")
    url = f"{API_BASE}/posts?type=page&number=20"
    data = fetch_json(url)
    pages = data.get("posts", [])
    
    for p in pages:
        title = html.unescape(p.get("title", "")).strip()
        slug = p.get("slug", "")
        content = clean_html_content(p.get("content", ""))
        
        filepath = os.path.join(PAGES_DIR, f"{slug}.md")
        frontmatter = [
            "---",
            f'title: "{title}"',
            f'slug: "{slug}"',
            f'date: {p.get("date", "")}',
            "---\n"
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(frontmatter))
            f.write(content)
        print(f"Migrated page: {title} ({slug})")

if __name__ == "__main__":
    migrate_pages()
    migrate_posts()
