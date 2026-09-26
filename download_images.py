#!/usr/bin/env python3
"""
Downloads all remote images from posts and pages to assets/images/posts/
and updates the Markdown files to use the local paths.
"""

import os
import re
import glob
import hashlib
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DEST_DIR = Path("assets/images/posts")
DEST_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://mealegroentupalabra.wordpress.com/"
}

def get_clean_filename(url):
    parsed = urllib.parse.urlparse(url)
    raw_name = os.path.basename(parsed.path)
    # Remove query string if any
    raw_name = raw_name.split("?")[0]
    if not raw_name or "." not in raw_name:
        h = hashlib.md5(url.encode()).hexdigest()[:10]
        raw_name = f"image_{h}.jpg"
    # Clean filename of unsafe characters
    clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', raw_name)
    return clean_name

def download_image(url, dest_path):
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True, "already_exists"

    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            if resp.status == 200:
                data = resp.read()
                dest_path.write_bytes(data)
                return True, "downloaded"
            else:
                return False, f"status_{resp.status}"
    except Exception as e:
        return False, str(e)

def main():
    md_files = glob.glob("content/posts/*.md") + glob.glob("content/pages/*.md")
    print(f"Scanning {len(md_files)} markdown files...")

    # Map url -> local filename
    url_to_local = {}
    used_filenames = {}

    for fpath in md_files:
        content = Path(fpath).read_text(encoding="utf-8")
        
        # Frontmatter image
        m_img = re.search(r'^image:\s*["\']?(https?://[^"\'\s\n]+)["\']?', content, re.MULTILINE)
        if m_img:
            u = m_img.group(1).strip()
            if u not in url_to_local:
                fn = get_clean_filename(u)
                if fn in used_filenames and used_filenames[fn] != u:
                    h = hashlib.md5(u.encode()).hexdigest()[:6]
                    base, ext = os.path.splitext(fn)
                    fn = f"{base}_{h}{ext}"
                used_filenames[fn] = u
                url_to_local[u] = fn

        # Body markdown images
        for m in re.finditer(r'!\[.*?\]\((https?://[^\)\s]+)\)', content):
            u = m.group(1).strip()
            if u not in url_to_local:
                fn = get_clean_filename(u)
                if fn in used_filenames and used_filenames[fn] != u:
                    h = hashlib.md5(u.encode()).hexdigest()[:6]
                    base, ext = os.path.splitext(fn)
                    fn = f"{base}_{h}{ext}"
                used_filenames[fn] = u
                url_to_local[u] = fn

        # Body html images
        for m in re.finditer(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', content):
            u = m.group(1).strip()
            if u not in url_to_local:
                fn = get_clean_filename(u)
                if fn in used_filenames and used_filenames[fn] != u:
                    h = hashlib.md5(u.encode()).hexdigest()[:6]
                    base, ext = os.path.splitext(fn)
                    fn = f"{base}_{h}{ext}"
                used_filenames[fn] = u
                url_to_local[u] = fn

    print(f"Found {len(url_to_local)} unique remote images to download.")

    # Concurrently download images
    download_results = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_url = {
            executor.submit(download_image, url, DEST_DIR / fn): (url, fn)
            for url, fn in url_to_local.items()
        }

        downloaded_count = 0
        exists_count = 0
        failed_count = 0

        for future in as_completed(future_to_url):
            url, fn = future_to_url[future]
            try:
                success, reason = future.result()
                if success:
                    if reason == "downloaded":
                        downloaded_count += 1
                    else:
                        exists_count += 1
                    download_results[url] = f"/assets/images/posts/{fn}"
                else:
                    failed_count += 1
                    print(f"Failed to download {url}: {reason}")
            except Exception as e:
                failed_count += 1
                print(f"Exception downloading {url}: {e}")

    print(f"\nDownload summary: {downloaded_count} downloaded, {exists_count} already existed, {failed_count} failed.")

    # Update markdown files
    updated_files = 0
    for fpath in md_files:
        p = Path(fpath)
        content = p.read_text(encoding="utf-8")
        orig_content = content

        for remote_url, local_url in download_results.items():
            if remote_url in content:
                content = content.replace(remote_url, local_url)

        if content != orig_content:
            p.write_text(content, encoding="utf-8")
            updated_files += 1

    print(f"Updated {updated_files} markdown files to use local image paths.")

if __name__ == "__main__":
    main()
