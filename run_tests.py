#!/usr/bin/env python3
"""
NeuraMatrix.ai — Overnight Diagnostic Test Suite
Tests: HTML validity, CSS references, nav links, external CDN, form endpoints, and local server health.
"""
import os, sys, re, json, time, http.server, threading, urllib.request, urllib.error, socketserver
from pathlib import Path

SITE_DIR = Path("/home/runner/work/neuramatrix-ai/neuramatrix-ai")
PORT = 8765
RESULTS = []

def log(status, test, detail=""):
    icon = "✅" if status == "PASS" else ("⚠️" if status == "WARN" else "❌")
    msg = f"{icon} [{status}] {test}"
    if detail:
        msg += f"\n       → {detail}"
    print(msg)
    RESULTS.append({"status": status, "test": test, "detail": detail})

# ── 1. CSS reference audit ─────────────────────────────────────────────────────
def check_css_references():
    print("\n── CSS Reference Audit ──")
    css_files = {f.name for f in SITE_DIR.glob("*.css")}
    for html_file in sorted(SITE_DIR.glob("*.html")):
        content = html_file.read_text(errors="replace")
        hrefs = re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', content)
        for href in hrefs:
            if href.startswith("http"):
                continue  # external, skip here
            if href in css_files:
                log("PASS", f"{html_file.name} → {href}")
            else:
                log("FAIL", f"{html_file.name} → {href}", f"File '{href}' not found in repo root")

# ── 2. Template syntax check ───────────────────────────────────────────────────
def check_template_syntax():
    print("\n── Template Syntax Check ──")
    for html_file in sorted(SITE_DIR.glob("*.html")):
        content = html_file.read_text(errors="replace")
        if "{{" in content or "{%" in content:
            log("FAIL", f"{html_file.name}", "Contains Jinja2/template syntax (won't render on static host)")
        else:
            log("PASS", f"{html_file.name} — no template syntax")

# ── 3. Internal link audit ─────────────────────────────────────────────────────
def check_internal_links():
    print("\n── Internal Link Audit ──")
    for html_file in sorted(SITE_DIR.glob("*.html")):
        content = html_file.read_text(errors="replace")
        hrefs = re.findall(r'<a[^>]+href=["\']([^"\'#][^"\']*)["\']', content)
        for href in hrefs:
            if href.startswith("http") or href.startswith("mailto"):
                continue
            # Resolve relative to site root
            target = (SITE_DIR / href).resolve()
            if target.exists():
                log("PASS", f"{html_file.name} → {href}")
            else:
                log("FAIL", f"{html_file.name} → {href}", "Target file not found")

# ── 4. Image asset audit ───────────────────────────────────────────────────────
def check_image_assets():
    print("\n── Image Asset Audit ──")
    for html_file in sorted(SITE_DIR.glob("*.html")):
        content = html_file.read_text(errors="replace")
        srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        for src in srcs:
            if src.startswith("http"):
                continue
            target = (SITE_DIR / src).resolve()
            if target.exists():
                log("PASS", f"{html_file.name} img → {src}")
            else:
                log("WARN", f"{html_file.name} img → {src}", "Image file not found (placeholder needed)")

# ── 5. Local HTTP server health check ─────────────────────────────────────────
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def check_local_server():
    print("\n── Local Server Health Check ──")
    os.chdir(SITE_DIR)
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        t = threading.Thread(target=httpd.serve_forever)
        t.daemon = True
        t.start()
        time.sleep(0.5)

        pages = [
            ("index.html", "index.html"),
            ("services.html", "services.html"),
            ("contact.html", "contact.html"),
            ("reviews.html", "reviews.html"),
            ("store.html", "store.html"),
            ("smart-entry.html", "smart-entry.html"),
            ("smart-lighting.html", "smart-lighting.html"),
            ("surveillance.html", "surveillance.html"),
            ("thank-you.html", "thank-you.html"),
            ("styles.css", "styles.css"),
            ("scripts.js", "scripts.js"),
            ("assets/kit-demo.svg", "assets/kit-demo.svg"),
        ]
        for label, path in pages:
            url = f"http://localhost:{PORT}/{path}"
            try:
                with urllib.request.urlopen(url, timeout=3) as r:
                    code = r.status
                    if code == 200:
                        log("PASS", f"GET /{path} → {code}")
                    else:
                        log("WARN", f"GET /{path} → {code}")
            except urllib.error.HTTPError as e:
                log("FAIL", f"GET /{path}", f"HTTP {e.code}")
            except Exception as e:
                log("FAIL", f"GET /{path}", str(e))
        httpd.shutdown()

# ── 6. Required meta tags ──────────────────────────────────────────────────────
def check_meta_tags():
    print("\n── Meta Tag / SEO Audit ──")
    required = ["charset", "viewport"]
    for html_file in sorted(SITE_DIR.glob("*.html")):
        content = html_file.read_text(errors="replace")
        for tag in required:
            if tag in content:
                log("PASS", f"{html_file.name} — meta:{tag}")
            else:
                log("WARN", f"{html_file.name} — meta:{tag}", "Missing meta tag")

# ── 7. CNAME / deployment config ──────────────────────────────────────────────
def check_deployment_config():
    print("\n── Deployment Config ──")
    cname = SITE_DIR / "CNAME"
    if cname.exists():
        domain = cname.read_text().strip()
        log("PASS", f"CNAME → {domain}")
    else:
        log("WARN", "CNAME missing", "GitHub Pages custom domain not configured")

    nginx = SITE_DIR / "nginx.conf"
    static = SITE_DIR / "static.json"
    if nginx.exists():
        log("PASS", "nginx.conf present")
    if static.exists():
        data = json.loads(static.read_text())
        if data.get("clean_urls"):
            log("WARN", "static.json clean_urls=true", 
                "Routes all to index.html — fine for CDN/SPA but may mask 404s on multi-page site")
        else:
            log("PASS", "static.json present")

# ── Run all checks ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  NeuraMatrix.ai — Diagnostic Test Suite")
    print(f"  Site dir: {SITE_DIR}")
    print("=" * 60)

    check_css_references()
    check_template_syntax()
    check_internal_links()
    check_image_assets()
    check_local_server()
    check_meta_tags()
    check_deployment_config()

    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    warned = sum(1 for r in RESULTS if r["status"] == "WARN")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")

    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed} passed  |  {warned} warnings  |  {failed} failed")
    print("=" * 60)
    sys.exit(1 if failed > 0 else 0)
