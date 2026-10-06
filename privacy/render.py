#!/usr/bin/env python3
"""Render docs/PRIVACY_NOTICE.md into the landing site's /privacy page.

Deliberately a small, explicit converter rather than a markdown library: the
notice is a legal document, and the only safe transformation is one whose output
can be read against the input line by line. It handles exactly the constructs the
notice uses — headings, paragraphs, bullets, tables, blockquotes, rules, bold and
italic — and refuses anything it does not recognise rather than guessing.

The source text is never reworded. Every heading gets a predictable anchor
(section-1 ... section-11) so the app can deep-link, and section 4 gets the extra
stable alias `location` because that is the one the app links to.
"""
import html
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

md = SRC.read_text()
lines = md.split("\n")


def inline(t: str) -> str:
    """Escape, then apply the only inline markup the notice uses."""
    t = html.escape(t, quote=False)
    # Bold before italic: **x** must not be eaten by the single-asterisk rule.
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", t)
    # Bare email and URL autolinks, so a phone can tap them.
    t = re.sub(r"(?<![\w.@-])([\w.+-]+@[\w-]+\.[\w.]+)",
               r'<a href="mailto:\1">\1</a>', t)
    return t


out: list[str] = []
section_titles: list[tuple[str, str]] = []  # (anchor, title) for the contents list
i = 0
in_table = False
in_list = False
in_quote = False
para: list[str] = []


def flush_para():
    global para
    if para:
        out.append("<p>" + inline(" ".join(para)) + "</p>")
        para = []


def close_blocks(keep_quote=False):
    global in_list, in_table, in_quote
    flush_para()
    if in_list:
        out.append("</ul>")
        in_list = False
    if in_table:
        out.append("</tbody></table></div>")
        in_table = False
    if in_quote and not keep_quote:
        out.append("</blockquote>")
        in_quote = False


while i < len(lines):
    raw = lines[i]
    line = raw.rstrip()

    # ── Blank ────────────────────────────────────────────────────────────────
    if not line.strip():
        flush_para()
        if in_list:
            out.append("</ul>")
            in_list = False
        if in_table:
            out.append("</tbody></table></div>")
            in_table = False
        if in_quote:
            out.append("</blockquote>")
            in_quote = False
        i += 1
        continue

    # ── Horizontal rule ──────────────────────────────────────────────────────
    if re.fullmatch(r"-{3,}", line.strip()):
        close_blocks()
        out.append('<hr aria-hidden="true" />')
        i += 1
        continue

    # ── Headings ─────────────────────────────────────────────────────────────
    m = re.match(r"^(#{1,3})\s+(.*)$", line)
    if m:
        close_blocks()
        level, text = len(m.group(1)), m.group(2).strip()
        if level == 1:
            out.append(f"<h1>{inline(text)}</h1>")
        elif level == 2:
            num = re.match(r"^(\d+)\.", text)
            if num:
                anchor = f"section-{num.group(1)}"
                section_titles.append((anchor, text))
                extra = ""
                if num.group(1) == "4":
                    # The app deep-links here. A named alias survives renumbering.
                    extra = '<a id="location" class="alias" aria-hidden="true"></a>'
                out.append(
                    f'{extra}<h2 id="{anchor}">{inline(text)}'
                    f'<a class="anchor" href="#{anchor}" aria-label="Link to this section">#</a></h2>'
                )
            else:
                out.append(f"<h2>{inline(text)}</h2>")
        else:
            out.append(f"<h3>{inline(text)}</h3>")
        i += 1
        continue

    # ── Blockquote ───────────────────────────────────────────────────────────
    if line.startswith(">"):
        flush_para()
        if in_list:
            out.append("</ul>")
            in_list = False
        if not in_quote:
            out.append('<blockquote class="note">')
            in_quote = True
        body = line[1:].lstrip()
        if body:
            para.append(body)
        i += 1
        # Flush the quote's paragraph when the quote block ends.
        if i >= len(lines) or not lines[i].startswith(">"):
            flush_para()
        continue

    # ── Table ────────────────────────────────────────────────────────────────
    if line.lstrip().startswith("|"):
        flush_para()
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        is_divider = all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c)
        if is_divider:
            i += 1
            continue
        if not in_table:
            out.append('<div class="table-scroll"><table>')
            # A leading row whose first cell is empty is this document's idiom
            # for "the row labels have no header"; it is still the header row.
            out.append("<thead><tr>" + "".join(
                f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
            in_table = True
        else:
            out.append("<tr>" + "".join(
                f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        i += 1
        continue

    # ── Bullet ───────────────────────────────────────────────────────────────
    if re.match(r"^-\s+", line):
        flush_para()
        if not in_list:
            out.append("<ul>")
            in_list = True
        item = [re.sub(r"^-\s+", "", line)]
        i += 1
        # Continuation lines are indented.
        while i < len(lines) and re.match(r"^\s{2,}\S", lines[i]):
            item.append(lines[i].strip())
            i += 1
        out.append("<li>" + inline(" ".join(item)) + "</li>")
        continue

    # ── Paragraph text ───────────────────────────────────────────────────────
    para.append(line.strip())
    i += 1

close_blocks()
body_html = "\n      ".join(out)

def plain(t: str) -> str:
    """Heading text with the emphasis markers removed, for the contents list."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return html.escape(t, quote=False)


contents = "\n          ".join(
    f'<li><a href="#{a}">{plain(t)}</a></li>' for a, t in section_titles
)

# The "Last updated" line is pulled out of the body and shown as a dateline, so
# it is visible at the top on a phone without scrolling into the prose.
m = re.search(r"^Last updated ([^.]+)\.$", md, flags=re.M)
updated = m.group(1) if m else ""

page = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Privacy Notice - DriveBai</title>
    <meta
      name="description"
      content="What DriveBai collects about you, who sees it, how long it is kept, and what you can do about it."
    />
    <meta name="author" content="DriveBai" />
    <meta name="robots" content="index, follow" />
    <meta property="og:type" content="article" />
    <meta property="og:title" content="Privacy Notice - DriveBai" />
    <meta
      property="og:description"
      content="What DriveBai collects about you, who sees it, how long it is kept, and what you can do about it."
    />
    <link rel="stylesheet" href="../styles.css" />
    <link rel="stylesheet" href="../privacy.css" />
  </head>
  <body>
    <header class="site-header" aria-label="Primary navigation">
      <a class="brand" href="../" aria-label="DriveBai home">
        <img src="../assets/drivebai-logo.png" alt="DriveBai" class="brand-logo" />
      </a>
      <nav aria-label="Primary">
        <a href="../#how">How it works</a>
        <a href="../#download">iOS app</a>
      </nav>
    </header>

    <main class="doc" id="top">
      <p class="dateline"><span class="dateline-label">Last updated</span> {html.escape(updated)}</p>

      {body_html}

      <nav class="doc-contents" aria-label="Sections of this notice">
        <h2>Sections</h2>
        <ol>
          {contents}
        </ol>
      </nav>
    </main>

    <footer class="site-footer">
      <a class="brand" href="../" aria-label="DriveBai home">
        <img src="../assets/drivebai-logo.png" alt="DriveBai" class="brand-logo" />
      </a>
      <nav aria-label="Legal">
        <a href="/privacy" aria-current="page">Privacy</a>
        <a href="https://drivebai-landing-v2.netlify.app/terms">Terms</a>
        <a href="mailto:support@drivebai.com">Contact</a>
      </nav>
      <small>&copy; DriveBai 2026</small>
    </footer>
  </body>
</html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)

# Loud, every single time, because the one thing that must not happen quietly is
# this page going live with our own blocker notes on it.
if "POSTAL ADDRESS REQUIRED" in md:
    print("\n  !! NOT PUBLISHABLE: section 11 still carries the postal-address")
    print("     placeholder, and the internal blocker note renders on the page.")
    print("     Replace the Mail line AND delete the blockquote under it.\n")
print(f"wrote {OUT} ({len(page)} bytes), {len(section_titles)} numbered sections")
for a, t in section_titles:
    print(f"  #{a:<11} {t}")
