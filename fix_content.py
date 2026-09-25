#!/usr/bin/env python3
"""
Clean post content:
1. Strip Jetpack timeline cards and background-color:#eeeeee from reading plan posts.
2. Rewrite internal links pointing to mealegroentupalabra.wordpress.com / mealegroentupalabra.com to local URLs.
3. Remove old static wp-block-query Gutenberg blocks from static pages.
"""

import os
import glob
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def transform_url(url):
    parsed = urlparse(url)
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
    m_post = re.match(r'^\d{4}/\d{2}/\d{2}/([^/]+)', path)
    if m_post:
        return f'/posts/{m_post.group(1)}/'

    # Static pages
    if path in ['reflexiones', 'planes-de-lectura', 'la-biblia-en-un-ano', 'acerca-de', 'buscar', 'categorias', 'etiquetas']:
        return f'/{path}/'

    return f'/posts/{path}/'

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    parts = text.split('---', 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]
    body = parts[2]

    soup = BeautifulSoup(body, 'html.parser')

    # 1. Remove timeline bubbles & dots
    for bubble in soup.find_all('div', class_=lambda c: c and ('timeline-item__bubble' in c or 'timeline-item__dot' in c)):
        bubble.decompose()

    # 2. Unwrap timeline container & items
    for ul in soup.find_all('ul', class_=lambda c: c and 'wp-block-jetpack-timeline' in c):
        ul.name = 'div'
        ul['class'] = 'reading-plan-flow'

    for li in soup.find_all('li', class_=lambda c: c and 'wp-block-jetpack-timeline-item' in c):
        li.name = 'div'
        if li.has_attr('style'):
            del li['style']
        if li.has_attr('class'):
            del li['class']

    for item in soup.find_all('div', class_='timeline-item'):
        item.unwrap()

    # Clean any elements with background-color:#eeeeee or similar card backgrounds
    for el in soup.find_all(True):
        if el.has_attr('style'):
            style = el['style']
            if 'background-color:#eee' in style or 'background-color:#eeeeee' in style:
                # remove background-color from style
                new_style = re.sub(r'background-color:\s*#[a-fA-F0-9]+;?', '', style).strip()
                if new_style:
                    el['style'] = new_style
                else:
                    del el['style']

    # 3. Remove old Gutenberg query loops in pages
    for q in soup.find_all(class_=lambda c: c and 'wp-block-query' in c):
        q.decompose()

    # 4. Remove empty coblocks separators
    for hr in soup.find_all('hr', class_=lambda c: c and 'wp-block-coblocks-dynamic-separator' in c):
        hr.decompose()

    # 5. Rewrite internal links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'mealegroentupalabra' in href and '/wp-content/uploads/' not in href:
            new_href = transform_url(href)
            a['href'] = new_href

    cleaned_body = str(soup)
    new_text = f"---{frontmatter}---\n\n{cleaned_body.strip()}\n"

    if new_text != text:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_text)
        return True
    return False

def main():
    modified_posts = 0
    modified_pages = 0

    for f in glob.glob('content/posts/*.md'):
        if clean_file(f):
            modified_posts += 1

    for f in glob.glob('content/pages/*.md'):
        if clean_file(f):
            modified_pages += 1

    print(f"Updated {modified_posts} posts and {modified_pages} pages!")

if __name__ == "__main__":
    main()
