#!/usr/bin/env bash
# Bina laman dan terbitkan kandungan dist/ ke cabang gh-pages.
#
# Kenapa skrip ini wujud: `astro build` MEMADAM folder dist/ sepenuhnya,
# termasuk .git jika repositori deploy disimpan di dalamnya. Jadi repositori
# deploy disimpan di luar (DEPLOY_DIR) dan hanya disegerakkan setiap kali.
#
# Guna:  ./scripts/deploy.sh "mesej commit"

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${DEPLOY_DIR:-/home/ubuntu/.hadiahkorporat-deploy}"
REMOTE="https://github.com/maryamstore6/hadiahkorporat.git"
BRANCH="gh-pages"
BASE_URL="https://maryamstore6.github.io/hadiahkorporat"
MESEJ="${1:-Deploy: katalog hadiah korporat}"

cd "$REPO_DIR"

echo "▸ Bina laman…"
npx astro build

echo "▸ Jana sitemap + robots…"
python3 - "$BASE_URL" <<'PY'
import os, sys, datetime
base, dist = sys.argv[1], "dist"
urls = []
for root, _dirs, files in os.walk(dist):
    for f in files:
        if f.endswith(".html"):
            rel = os.path.relpath(os.path.join(root, f), dist).replace("index.html", "").replace("\\", "/")
            if rel != "404.html":
                urls.append(f"{base}/{rel}")
urls.sort()
today = datetime.date.today().isoformat()
with open(f"{dist}/sitemap.xml", "w") as fh:
    fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    fh.write("\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls))
    fh.write("\n</urlset>")
with open(f"{dist}/robots.txt", "w") as fh:
    fh.write(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
open(f"{dist}/.nojekyll", "w").write("")
print(f"   {len(urls)} URL dalam sitemap")
PY

echo "▸ Segerak ke repositori deploy ($DEPLOY_DIR)…"
mkdir -p "$DEPLOY_DIR"
# Kosongkan tetapi kekalkan .git
find "$DEPLOY_DIR" -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +
cp -a dist/. "$DEPLOY_DIR"/

cd "$DEPLOY_DIR"
if [ ! -d .git ]; then
  git init -q
  git config user.name "Hermes Agent"
  git config user.email "agent@hadiahkorporat.my"
  git remote add origin "$REMOTE"
fi
git add -A
git commit -q -m "$MESEJ" || echo "   (tiada perubahan)"
git push -f origin "HEAD:$BRANCH"
echo "✓ Terbit. Laman: $BASE_URL/"
