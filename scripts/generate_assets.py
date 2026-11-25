#!/usr/bin/env python3
"""Build the profile SVGs (hero, stats, languages) from live GitHub data.

Standard library only. Set GITHUB_TOKEN (the Actions token works) so the
GraphQL query can run. Edit the PROFILE block to change the banner text.
"""
import json
import os
import urllib.request
from collections import Counter

# ---- Edit me ---------------------------------------------------------------
PROFILE = {
    "name": "Jiya Elza Jabi",
    "title": "Full Stack and AI Developer",
    "tagline": "Turning my caffeinated ideas into code, one line at a time.",
    "location": "Bengaluru, India",
}
ACCENT = "#79fff8"  # main highlight colour
RAMP = ["#c2fffc", "#9efffa", "#79fff8", "#34f4ea", "#11d0c6", "#108e88"]
SKIP_LANGS = {"HTML", "CSS", "SCSS", "Jupyter Notebook"}
# ---------------------------------------------------------------------------

LOGIN = os.environ.get("GH_LOGIN", "jelza04")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SANS = "ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
BG, TEXT, SUB, MUTED, LINE = "#0b0b0c", "#ecebe7", "#a8a8ae", "#8a8a91", "#232327"


def api(url, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-assets"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def collect():
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
          totalCount
          nodes { languages(first: 20) { nodes { name } } }
        }
        contributionsCollection { contributionCalendar { totalContributions } }
      }
    }"""
    body = json.dumps({"query": query, "variables": {"login": LOGIN}}).encode()
    res = api("https://api.github.com/graphql", body)
    if "errors" in res:
        raise SystemExit(f"GraphQL error: {res['errors']}")
    user = res["data"]["user"]
    repos = user["repositories"]["nodes"]

    langs = Counter()
    for repo in repos:
        for name in {n["name"] for n in repo["languages"]["nodes"]} - SKIP_LANGS:
            langs[name] += 1

    return {
        "repos": user["repositories"]["totalCount"],
        "contributions": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "languages": langs,
    }


def svg(w, h, inner):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="auto">'
        f'<rect width="{w}" height="{h}" fill="{BG}"/>{inner}</svg>\n'
    )


def hline(y, x1, x2):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{LINE}"/>'


def hero_svg():
    p = {k: esc(v) for k, v in PROFILE.items()}
    return svg(800, 210, (
        f'<rect x="48" y="62" width="4" height="76" fill="{ACCENT}"/>'
        f'<text x="72" y="100" font-family="{SANS}" font-size="44" font-weight="700" fill="{TEXT}">{p["name"]}</text>'
        f'<text x="72" y="128" font-family="{SANS}" font-size="15" fill="{SUB}">{p["title"]}</text>'
        f'<text x="72" y="152" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{p["tagline"]}</text>'
        f'{hline(178, 48, 752)}'
        f'<text x="48" y="200" font-family="{SANS}" font-size="12" fill="{MUTED}">{p["location"]}</text>'
        f'<text x="752" y="200" text-anchor="end" font-family="{MONO}" font-size="11.5" fill="{MUTED}">github.com/{esc(LOGIN)}</text>'
    ))


def stats_svg(d):
    cells = [
        ("contributions, 12 mo", d["contributions"], ACCENT),
        ("public repos", d["repos"], TEXT),
    ]
    col = 592 / len(cells)
    parts = [hline(32, 44, 636)]
    for i, (label, value, colour) in enumerate(cells):
        cx = 44 + col * (i + 0.5)
        if i:
            x = 44 + col * i
            parts.append(f'<line x1="{x:.1f}" y1="52" x2="{x:.1f}" y2="118" stroke="{LINE}"/>')
        parts.append(f'<text x="{cx:.1f}" y="92" text-anchor="middle" font-family="{MONO}" font-size="32" font-weight="600" fill="{colour}">{value:,}</text>')
        parts.append(f'<text x="{cx:.1f}" y="114" text-anchor="middle" font-family="{SANS}" font-size="11.5" fill="{MUTED}">{label}</text>')
    return svg(680, 134, "".join(parts))


def languages_svg(d):
    rows = d["languages"].most_common(6)
    total = sum(c for _, c in rows) or 1
    parts = [
        hline(28, 44, 636),
        f'<text x="44" y="54" font-family="{SANS}" font-size="14" font-weight="600" fill="{TEXT}">Languages</text>',
        f'<text x="636" y="54" text-anchor="end" font-family="{SANS}" font-size="11" fill="{MUTED}">repos using each, of {d["repos"]}</text>',
    ]
    x, col = 44.0, 592 / 3
    for i, (name, count) in enumerate(rows):
        w = count / total * 592
        parts.append(f'<rect x="{x:.1f}" y="70" width="{max(w - 3, 1):.1f}" height="10" fill="{RAMP[i]}"/>')
        x += w
        lx, ly = 44 + (i % 3) * col, 112 + (i // 3) * 30
        parts.append(
            f'<circle cx="{lx + 4}" cy="{ly - 4.5}" r="4" fill="{RAMP[i]}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="{SANS}" font-size="13" fill="{TEXT}">{esc(name)}</text>'
            f'<text x="{lx + col - 24:.1f}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="10.5" fill="{MUTED}">{count} repos</text>'
        )
    return svg(680, 166, "".join(parts))


def main():
    out = os.path.join(ROOT, "assets")
    os.makedirs(out, exist_ok=True)
    files = {"hero.svg": hero_svg()}
    if TOKEN:
        data = collect()
        files.update({"stats.svg": stats_svg(data), "languages.svg": languages_svg(data)})
    else:
        print("No GITHUB_TOKEN set: only hero.svg was generated.")
    for name, content in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"wrote assets/{name}")


if __name__ == "__main__":
    main()
