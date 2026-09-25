#!/usr/bin/env python3
"""
Me Alegro En Tu Palabra - Local Server & Visual Editor
Serves the generated blog and provides a web-based editor at http://localhost:8000/editor/
"""

import os
import sys
import json
import urllib.parse
import http.server
import socketserver
from datetime import datetime
from pathlib import Path
from build import SiteBuilder, slugify

PORT = 8000
POSTS_DIR = "content/posts"

EDITOR_HTML = """<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Editor de Artículos — Me Alegro En Tu Palabra</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/style.css">
  <style>
    body { background-color: var(--bg-body); padding-bottom: 5rem; }
    .editor-container { max-width: 1000px; margin: 2rem auto; padding: 0 1.5rem; }
    .editor-card { background: var(--bg-surface); border: 1px solid var(--border-light); border-radius: var(--radius-lg); padding: 2rem; box-shadow: var(--shadow-md); }
    .form-group { margin-bottom: 1.25rem; }
    .form-label { display: block; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.4rem; color: var(--text-main); }
    .form-control { width: 100%; padding: 0.75rem 1rem; border: 1px solid var(--border-light); border-radius: var(--radius-md); font-family: inherit; font-size: 1rem; background: var(--bg-surface); color: var(--text-main); transition: border-color 0.15s ease; }
    .form-control:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }
    .editor-split { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem; }
    .textarea-editor { min-height: 420px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.92rem; line-height: 1.6; resize: vertical; }
    .preview-box { min-height: 420px; border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 1.5rem; background: var(--bg-surface); overflow-y: auto; max-height: 600px; }
    .btn-publish { background: var(--primary); color: #ffffff; border: none; border-radius: var(--radius-md); padding: 0.85rem 1.75rem; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s ease, transform 0.1s ease; display: inline-flex; align-items: center; gap: 0.5rem; }
    .btn-publish:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .editor-toolbar { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .tool-btn { background: var(--bg-subtle); border: 1px solid var(--border-light); padding: 0.35rem 0.65rem; border-radius: 4px; font-size: 0.82rem; cursor: pointer; color: var(--text-main); }
    .tool-btn:hover { background: var(--border-light); }
  </style>
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="site-brand">
        <img src="/assets/images/logo.png" alt="Logo" class="site-logo" width="40" height="40">
        <div class="brand-text">
          <span class="brand-title">Me Alegro En Tu Palabra</span>
          <span class="brand-tagline">Editor de Publicaciones</span>
        </div>
      </a>
      <div>
        <a href="/" class="nav-link" target="_blank">&larr; Ver Sitio Web</a>
      </div>
    </div>
  </header>

  <div class="editor-container">
    <div class="editor-card">
      <h1 style="font-family: var(--font-serif); font-size: 2rem; margin-bottom: 0.5rem;">Publicar Nuevo Artículo</h1>
      <p style="color: var(--text-muted); font-size: 0.92rem; margin-bottom: 1.5rem;">
        Escribe tu artículo en formato Markdown o HTML. Al presionar "Publicar", el archivo se creará y el sitio se compilará automáticamente.
      </p>

      <form id="postForm">
        <div class="form-group">
          <label class="form-label" for="title">Título del Artículo *</label>
          <input type="text" id="title" class="form-control" placeholder="Ej: La Paz que Sobrepasa Todo Entendimiento" required>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div class="form-group">
            <label class="form-label" for="category">Categoría *</label>
            <select id="category" class="form-control">
              <option value="Reflexiones">Reflexiones</option>
              <option value="Planes de Lectura">Planes de Lectura</option>
              <option value="La Biblia en un Año">La Biblia en un Año</option>
              <option value="Génesis">Génesis</option>
              <option value="Isaías">Isaías</option>
              <option value="Jeremías">Jeremías</option>
              <option value="Ezequiel">Ezequiel</option>
              <option value="__new__">+ Otra categoría personalizada...</option>
            </select>
            <input type="text" id="newCategory" class="form-control" placeholder="Escribe la nueva categoría" style="display: none; margin-top: 0.5rem;">
          </div>

          <div class="form-group">
            <label class="form-label" for="tags">Etiquetas (separadas por coma)</label>
            <input type="text" id="tags" class="form-control" placeholder="Ej: paz, confianza, fe, oración">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="image">URL de Imagen Destacada (opcional)</label>
          <input type="text" id="image" class="form-control" placeholder="Ej: https://... o /assets/images/...">
        </div>

        <div class="form-group">
          <label class="form-label" for="summary">Resumen / Descripción breve</label>
          <input type="text" id="summary" class="form-control" placeholder="Breve introducción para tarjetas y redes sociales...">
        </div>

        <div class="form-group">
          <label class="form-label">Contenido del Artículo (Markdown)</label>
          <div class="editor-toolbar">
            <button type="button" class="tool-btn" onclick="insertSyntax('**', '**')"><strong>B</strong> Negrita</button>
            <button type="button" class="tool-btn" onclick="insertSyntax('*', '*')"><em>I</em> Cursiva</button>
            <button type="button" class="tool-btn" onclick="insertSyntax('## ', '')">H2 Título</button>
            <button type="button" class="tool-btn" onclick="insertSyntax('### ', '')">H3 Subtítulo</button>
            <button type="button" class="tool-btn" onclick="insertScripture()">📖 Cita Bíblica</button>
            <button type="button" class="tool-btn" onclick="insertSyntax('- ', '')">Lista</button>
            <button type="button" class="tool-btn" onclick="insertSyntax('[Enlace](', ')')">🔗 Enlace</button>
          </div>

          <div class="editor-split">
            <div>
              <textarea id="content" class="form-control textarea-editor" placeholder="Escribe aquí tu reflexión..." required></textarea>
            </div>
            <div>
              <div class="preview-box post-content" id="previewBox">
                <p style="color: var(--text-light); font-style: italic;">La vista previa aparecerá aquí en tiempo real...</p>
              </div>
            </div>
          </div>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 2rem;">
          <span id="statusMsg" style="font-weight: 600; font-size: 0.95rem;"></span>
          <button type="submit" class="btn-publish" id="publishBtn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
            <span>Publicar Artículo</span>
          </button>
        </div>
      </form>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    const textarea = document.getElementById('content');
    const preview = document.getElementById('previewBox');
    const categorySelect = document.getElementById('category');
    const newCategoryInput = document.getElementById('newCategory');

    categorySelect.addEventListener('change', () => {
      if (categorySelect.value === '__new__') {
        newCategoryInput.style.display = 'block';
        newCategoryInput.focus();
      } else {
        newCategoryInput.style.display = 'none';
      }
    });

    textarea.addEventListener('input', () => {
      const md = textarea.value;
      if (window.marked) {
        preview.innerHTML = marked.parse(md);
      } else {
        preview.innerText = md;
      }
    });

    function insertSyntax(before, after) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const sel = textarea.value.substring(start, end);
      textarea.value = textarea.value.substring(0, start) + before + sel + after + textarea.value.substring(end);
      textarea.focus();
      textarea.dispatchEvent(new Event('input'));
    }

    function insertScripture() {
      const snippet = `\\n<div class="scripture-card">\\n  <blockquote>\\n    «Versículo bíblico aquí...»\\n    <cite class="scripture-cite">Libro Capítulo:Versículo</cite>\\n  </blockquote>\\n</div>\\n`;
      insertSyntax(snippet, '');
    }

    document.getElementById('postForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('publishBtn');
      const statusMsg = document.getElementById('statusMsg');
      
      btn.disabled = true;
      statusMsg.style.color = 'var(--primary)';
      statusMsg.textContent = '⏳ Publicando y recompilando el sitio...';

      let cat = categorySelect.value;
      if (cat === '__new__') {
        cat = newCategoryInput.value.trim() || 'Reflexiones';
      }

      const payload = {
        title: document.getElementById('title').value.trim(),
        category: cat,
        tags: document.getElementById('tags').value.trim(),
        summary: document.getElementById('summary').value.trim(),
        image: document.getElementById('image').value.trim(),
        content: textarea.value
      };

      try {
        const resp = await fetch('/api/new-post', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.success) {
          statusMsg.style.color = '#16a34a';
          statusMsg.innerHTML = `✓ ¡Artículo publicado! <a href="${res.url}" target="_blank" style="text-decoration: underline;">Ver artículo</a>`;
          setTimeout(() => {
            window.open(res.url, '_blank');
          }, 800);
        } else {
          statusMsg.style.color = '#dc2626';
          statusMsg.textContent = 'Error: ' + res.error;
        }
      } catch (err) {
        statusMsg.style.color = '#dc2626';
        statusMsg.textContent = 'Error de conexión con el servidor local.';
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""

class BlogRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path).path
        if url_path == "/editor" or url_path == "/editor/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(EDITOR_HTML.encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        url_path = urllib.parse.urlparse(self.path).path
        if url_path == "/api/new-post":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(post_data)
                title = data.get("title", "").strip()
                if not title:
                    raise ValueError("El título es obligatorio")

                from new_post import create_post
                filepath = create_post(
                    title=title,
                    category=data.get("category", "Reflexiones"),
                    tags=data.get("tags", ""),
                    summary=data.get("summary", ""),
                    image=data.get("image", ""),
                    content=data.get("content", "")
                )

                # Rebuild site
                builder = SiteBuilder()
                builder.build()

                slug = slugify(title)
                url = f"/posts/{slug}/"

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "url": url, "file": filepath}).encode("utf-8"))
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

    with socketserver.TCPServer(("", port), BlogRequestHandler) as httpd:
        print("\n" + "=" * 60)
        print(f" 📖  Me Alegro En Tu Palabra — Servidor Local")
        print("=" * 60)
        print(f" • Blog en vivo:     http://localhost:{port}/")
        print(f" • Editor visual:    http://localhost:{port}/editor/")
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
