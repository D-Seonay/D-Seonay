#!/usr/bin/env python3
"""Generate the README's SVG assets (dark + light pairs, plus the link pills).

    python3 tools/build-assets.py

Edit PHRASES, LINKS or the palettes below, then re-run. Every SVG is
self-contained: no external fonts, no scripts, so GitHub's image proxy
renders it as-is. Motion is SMIL and is swapped for a static frame under
prefers-reduced-motion.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

FONT = "ui-monospace,'SF Mono',SFMono-Regular,'JetBrains Mono',Menlo,Consolas,'Liberation Mono',monospace"
ADV = 0.6  # monospace advance in em; textLength pins every line to this grid

PALETTES = {
    "dark": {"fg": "#fafafa", "muted": "#a1a1aa", "faint": "#71717a", "line": "#3f3f46"},
    "light": {"fg": "#09090b", "muted": "#52525b", "faint": "#71717a", "line": "#d4d4d8"},
}

# Link pills are a single filled variant that reads on both themes: GitHub can't
# theme-swap an image wrapped in our own link (see the note in README.md).
PILL = {"bg": "#18181b", "fg": "#fafafa", "faint": "#a1a1aa", "line": "#3f3f46"}

W = 840

PHRASES = [
    "Building smart & impactful solutions",
    "React, Next.js, TypeScript, Node.js",
    "Open to freelance & full-time roles",
]

LINKS = [  # (file stem, key, value)
    ("link-mail", "mail", "matheodelaunay04@gmail.com"),
    ("link-linkedin", "linkedin", "in/matheo-delaunay"),
    ("link-web", "web", "seonay.com"),
]

# figlet "standard", kerned with a one-column gap
GLYPHS = {
    "S": [" ____  ", "/ ___| ", "\\___ \\ ", " ___) |", "|____/ "],
    "E": [" _____ ", "| ____|", "|  _|  ", "| |___ ", "|_____|"],
    "O": ["  ___  ", " / _ \\ ", "| | | |", "| |_| |", " \\___/ "],
    "N": [" _   _ ", "| \\ | |", "|  \\| |", "| |\\  |", "|_| \\_|"],
    "A": ["    _    ", "   / \\   ", "  / _ \\  ", " / ___ \\ ", "/_/   \\_\\"],
    "Y": ["__   __", "\\ \\ / /", " \\ V / ", "  | |  ", "  |_|  "],
}


def _trim(rows):
    w = max(map(len, rows))
    rows = [r.ljust(w) for r in rows]
    left = min(len(r) - len(r.lstrip()) for r in rows)
    right = min(len(r) - len(r.rstrip()) for r in rows)
    return [r[left : w - right] for r in rows]


def wordmark(word, gap=1):
    rows = _trim(GLYPHS[word[0]])
    for ch in word[1:]:
        glyph = _trim(GLYPHS[ch])
        k = min((len(a) - len(a.rstrip())) + (len(b) - len(b.lstrip())) for a, b in zip(rows, glyph)) - gap
        if k < 0:
            rows, k = [r + " " * -k for r in rows], 0
        out = []
        for a, b in zip(rows, glyph):
            seam = "".join(y if x == " " else x for x, y in zip(a[len(a) - k :], b[:k])) if k else ""
            out.append(a[: len(a) - k] + seam + b[k:])
        rows = out
    w = max(map(len, rows))
    return [r.ljust(w) for r in rows]


def nb(s):
    """Non-breaking spaces survive every renderer's whitespace collapsing."""
    return escape(s).replace(" ", "\u00a0")


def text(x, y, s, size, fill, anchor="start", extra=""):
    length = f' textLength="{len(s) * size * ADV:.2f}" lengthAdjust="spacing"' if anchor == "start" else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}"{a}{length}{extra}>{nb(s)}</text>'


def svg(w, h, title, body, style=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t" font-family="{FONT}">\n'
        f"<title id=\"t\">{escape(title)}</title>\n"
        + (f"<style>{style}</style>\n" if style else "")
        + body
        + "\n</svg>\n"
    )


MOTION_CSS = (
    ".still{display:none}"
    "@media (prefers-reduced-motion: reduce){.motion{display:none}.still{display:inline}}"
)


def typing_timeline():
    """One loop through every phrase: type, hold, erase, pause."""
    TYPE, HOLD, ERASE, PAUSE = 0.055, 2.4, 0.022, 0.45
    events = []  # (time, phrase index, visible chars)
    t = 0.0
    for i, p in enumerate(PHRASES):
        events.append((t, i, 0))
        for n in range(1, len(p) + 1):
            t += TYPE
            events.append((t, i, n))
        t += HOLD
        for n in range(len(p) - 1, -1, -1):
            events.append((t, i, n))
            t += ERASE
        t += PAUSE
    return events, t


def hero(p):
    rows = wordmark("SEONAY")
    cols = len(rows[0])
    wm_size = W / (cols * ADV)
    wm_lead = wm_size * 1.13

    head_y = 16
    wm_y0 = head_y + 50
    type_size = 18
    cw = type_size * ADV
    type_y = wm_y0 + wm_lead * (len(rows) - 1) + 60
    H = round(type_y + 30)

    header = "\n".join(
        [
            text(0, head_y, "SEONAY(1)", 13, p["muted"]),
            f'<text x="{W / 2}" y="{head_y}" font-size="13" fill="{p["faint"]}" text-anchor="middle">{nb("Full-Stack Developer Manual")}</text>',
            f'<text x="{W}" y="{head_y}" font-size="13" fill="{p["muted"]}" text-anchor="end">SEONAY(1)</text>',
        ]
    )

    def wm(animated):
        out = []
        for i, r in enumerate(rows):
            # rows print top to bottom, like terminal output
            anim = f'<set attributeName="opacity" to="0" dur="{0.35 + i * 0.07:.2f}s"/>' if animated else ""
            out.append(
                f'<text x="0" y="{wm_y0 + i * wm_lead:.2f}" font-size="{wm_size:.2f}" fill="{p["fg"]}" '
                f'textLength="{W}" lengthAdjust="spacing" xml:space="preserve">{nb(r)}{anim}</text>'
            )
        return "\n".join(out)

    prompt = text(0, type_y, ">", type_size, p["faint"])
    x0 = 2 * cw
    cur_h = type_size * 1.15
    cur_y = type_y - type_size * 0.88

    # static frame: first phrase, cursor at rest
    still = "\n".join(
        [
            wm(False),
            prompt,
            text(x0, type_y, PHRASES[0], type_size, p["fg"]),
            f'<rect x="{x0 + len(PHRASES[0]) * cw + 2:.2f}" y="{cur_y:.2f}" width="{cw:.2f}" height="{cur_h:.2f}" fill="{p["fg"]}"/>',
        ]
    )

    events, T = typing_timeline()
    begin = 0.35 + len(rows) * 0.07 + 0.25

    def key(t):
        return f"{t / T:.5f}"

    clips, lines = [], []
    for i, phrase in enumerate(PHRASES):
        ev = [(t, n) for t, j, n in events if j == i]
        # phrase is hidden outside its own slot
        kt, vals = ["0"], ["0"]
        for t, n in ev:
            if t == 0:
                vals[0] = f"{n * cw:.2f}"
                continue
            kt.append(key(t))
            vals.append(f"{n * cw:.2f}")
        # base width = fully typed first phrase, so non-SMIL renderers still read well
        base = len(phrase) * cw if i == 0 else 0
        clips.append(
            f'<clipPath id="c{i}"><rect x="{x0 - 1:.2f}" y="{type_y - type_size:.2f}" width="{base:.2f}" height="{type_size * 1.5:.2f}">'
            f'<set attributeName="width" to="0" dur="{begin:.2f}s"/>'
            f'<animate attributeName="width" begin="{begin:.2f}s" dur="{T:.3f}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{";".join(kt)}" values="{";".join(vals)}"/>'
            f"</rect></clipPath>"
        )
        lines.append(f'<g clip-path="url(#c{i})">{text(x0, type_y, phrase, type_size, p["fg"])}</g>')

    kt, vals = [], []
    for t, _, n in events:
        k = key(t)
        if kt and kt[-1] == k:
            vals[-1] = f"{x0 + n * cw + 2:.2f}"
            continue
        kt.append(k)
        vals.append(f"{x0 + n * cw + 2:.2f}")
    cursor = (
        f'<rect x="{x0 + len(PHRASES[0]) * cw + 2:.2f}" y="{cur_y:.2f}" width="{cw:.2f}" height="{cur_h:.2f}" fill="{p["fg"]}">'
        f'<set attributeName="x" to="{x0 + 2:.2f}" dur="{begin:.2f}s"/>'
        f'<animate attributeName="x" begin="{begin:.2f}s" dur="{T:.3f}s" repeatCount="indefinite" '
        f'calcMode="discrete" keyTimes="{";".join(kt)}" values="{";".join(vals)}"/>'
        f'<animate attributeName="opacity" values="1;0" dur="1.06s" calcMode="discrete" repeatCount="indefinite"/>'
        f"</rect>"
    )

    motion = "\n".join([f"<defs>{''.join(clips)}</defs>", wm(True), prompt, *lines, cursor])
    body = f'{header}\n<g class="motion">\n{motion}\n</g>\n<g class="still">\n{still}\n</g>'
    title = "SEONAY — Full-Stack Developer. " + " / ".join(PHRASES)
    return svg(W, H, title, body, MOTION_CSS)


def pill(key, value, p=PILL):
    size, pad, h = 13, 14, 34
    cw = size * ADV
    w = round(pad * 2 + (len(key) + 2 + len(value)) * cw)
    y = h / 2 + size * 0.35
    body = "\n".join(
        [
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="7" fill="{p["bg"]}" stroke="{p["line"]}"/>',
            text(pad, y, key, size, p["faint"]),
            text(pad + (len(key) + 2) * cw, y, value, size, p["fg"]),
        ]
    )
    return svg(w, h, f"{key}: {value}", body)


def footer(p):
    h, y = 22, 15
    body = "\n".join(
        [
            text(0, y, "Nantes, France", 13, p["muted"]),
            f'<text x="{W / 2}" y="{y}" font-size="13" fill="{p["faint"]}" text-anchor="middle">{nb("Crafted with precision, caffeine & clean commits")}</text>',
            f'<text x="{W}" y="{y}" font-size="13" fill="{p["muted"]}" text-anchor="end">SEONAY(1)</text>',
        ]
    )
    return svg(W, h, "Nantes, France. Crafted with precision, caffeine & clean commits.", body)


def main():
    OUT.mkdir(exist_ok=True)
    for mode, p in PALETTES.items():
        (OUT / f"hero-{mode}.svg").write_text(hero(p), encoding="utf-8")
        (OUT / f"footer-{mode}.svg").write_text(footer(p), encoding="utf-8")
    for stem, key, value in LINKS:
        (OUT / f"{stem}.svg").write_text(pill(key, value), encoding="utf-8")
    for f in sorted(OUT.glob("*.svg")):
        print(f"{f.stat().st_size:>6}  {f.relative_to(OUT.parent)}")


if __name__ == "__main__":
    main()
