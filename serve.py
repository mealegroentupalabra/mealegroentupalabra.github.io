#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra - Local Server & Studio Editor
Serves the generated blog and provides a full-featured web-based studio editor at http://localhost:8000/editor/
"""

import os
import sys
import re
import json
import base64
import urllib.parse
import http.server
import socketserver
from datetime import datetime
from pathlib import Path
from build import SiteBuilder, slugify

PORT = 8000
POSTS_DIR = "content/posts"

def get_editor_html():
    editor_path = Path("templates/editor.html")
    if editor_path.exists():
        return editor_path.read_text(encoding="utf-8")
    return "<h1>Error: No se encontró templates/editor.html</h1>"

class BlogRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        url_path = parsed.path
        if url_path in ("/editor", "/editor/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return
        if url_path.startswith("/api/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return
        super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        url_path = parsed.path

        # Visual Editor
        if url_path in ("/editor", "/editor/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_editor_html().encode("utf-8"))
            return

        # API: Taxonomies (All categories and tags)
        if url_path == "/api/taxonomies":
            from new_post import get_all_taxonomies
            data = get_all_taxonomies()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # API: List all posts
        if url_path == "/api/posts":
            from new_post import get_all_posts
            posts = get_all_posts()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(posts, ensure_ascii=False).encode("utf-8"))
            return

        # API: Get single post by filename
        if url_path == "/api/post":
            from new_post import get_post_by_file
            query = urllib.parse.parse_qs(parsed.query)
            filename = query.get("file", [""])[0]
            try:
                post = get_post_by_file(filename)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(post, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        url_path = parsed.path

        # API: Save or update post
        if url_path in ("/api/save-post", "/api/new-post"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(post_data)
                from new_post import save_post_data
                res = save_post_data(data)

                # Rebuild site
                builder = SiteBuilder()
                builder.build()

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "url": res["url"],
                    "filename": res["filename"],
                    "is_new": res["is_new"]
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: Upload featured or inline image
        if url_path == "/api/upload-image":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(post_data)
                filename = data.get("filename", "imagen.jpg")
                base64_str = data.get("data", "")
                if not base64_str:
                    raise ValueError("No se enviaron datos de imagen.")

                image_bytes = base64.b64decode(base64_str)

                clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                if not clean_name or "." not in clean_name:
                    clean_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

                now = datetime.now()
                year_str = now.strftime('%Y')
                month_str = now.strftime('%m')

                dest_dir = Path(f"assets/images/posts/{year_str}/{month_str}")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / clean_name

                # Avoid accidental overwrite
                if dest_file.exists():
                    base_n, ext_n = os.path.splitext(clean_name)
                    clean_name = f"{base_n}_{now.strftime('%H%M%S')}{ext_n}"
                    dest_file = dest_dir / clean_name

                dest_file.write_bytes(image_bytes)

                # Also write immediately to public/ so it can be previewed/served without full rebuild
                public_file = Path(f"public/assets/images/posts/{year_str}/{month_str}") / clean_name
                public_file.parent.mkdir(parents=True, exist_ok=True)
                public_file.write_bytes(image_bytes)

                url = f"/assets/images/posts/{year_str}/{month_str}/{clean_name}"
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "url": url}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

def run_server(port=PORT):
    # Ensure site is built before serving
    builder = SiteBuilder()
    builder.build()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), BlogRequestHandler) as httpd:
        print("\n" + "=" * 60)
        print(f" 📖  Me Alegro En Tu Palabra — Servidor & Estudio Editorial")
        print("=" * 60)
        print(f" • Blog en vivo:     http://localhost:{port}/")
        print(f" • Estudio de Edición: http://localhost:{port}/editor/")
        print("=" * 60)
        print("Presiona Ctrl+C para detener el servidor.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")

if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
