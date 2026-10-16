import re
from dataclasses import dataclass

# A new provision starts at a line like "420. Cheating and ..." or "66A. Punishment ...".
# Some PDFs print "3.Communication" with no space, and a heading may open with a quote
# (“, ‘, or the U+FFFD that PyMuPDF yields for them). The lookahead skips
# footnotes such as "4. See s. 75, infra." or "2. Subs. by Act ...".
SECTION_RE = re.compile(
    r"^\s*(\d{1,3}[A-Z]{0,2})\.[ \t]*(?=[A-Z\[“‘\"�])"
    r"(?!(?:See|Cf|Subs|Ins|Ibid|But see|The words|Vide)\b)",
    re.MULTILINE,
)
MIN_CHARS = 40


@dataclass
class Chunk:
    act: str
    section: str
    title: str
    page: int
    text: str


def _title(body: str) -> str:
    """Heading is the text up to the first '.-' / '.--' (the PDFs use an em dash)."""
    first = body.strip().split("\n\n")[0].replace("\n", " ")
    m = re.match(r"(.{3,200}?)\s*[.—–�-]{1,2}\s*(?=[A-Z(\[]|$)", first)
    return (m.group(1) if m else first[:120]).strip(" .—�-")


def chunk_by_section(act: str, pages: list[tuple[int, str]]) -> list[Chunk]:
    """Split an act into one chunk per section.

    Pages are joined with offset tracking so a section that spans pages keeps
    the page where it starts. Section numbers must run in sequence, which
    filters out numbered lists and footnotes inside provisions.
    """
    full, offsets = "", []
    for page_no, text in pages:
        offsets.append((len(full), page_no))
        full += text + "\n"

    def page_at(pos: int) -> int:
        page = offsets[0][1]
        for start, p in offsets:
            if start > pos:
                break
            page = p
        return page

    def num(sec: str) -> int:
        return int(re.match(r"\d+", sec).group())

    # Acts print a table of contents (same numbers, one-line bodies) before the body,
    # and may end with a numbered Statement of Objects. Split the matches into runs at
    # genuine restarts (a big drop in number followed by n+1), so stray numbered lines
    # inside a provision are skipped instead of derailing the sequence.
    matches = [(m.start(1), m.end(), m.group(1)) for m in SECTION_RE.finditer(full)]
    runs: list[list[tuple[int, int, str]]] = []
    top = max((num(m[2]) for m in matches), default=0)
    last = 0
    for i, (st, en, sec) in enumerate(matches):
        n = num(sec)
        nxt = num(matches[i + 1][2]) if i + 1 < len(matches) else None
        # A real restart (TOC -> body) happens only after reaching the end of the act;
        # a "1. 2. 3." list in the middle of a provision must not reset the run.
        restart = (
            n < last - 10 and last >= 0.8 * top and (nxt is None or nxt == n + 1)
        )
        if not runs or restart:
            runs.append([])
            last = 0
        # Only accept the next number; a gap is allowed when the following match
        # confirms it. A repeated number stays a candidate (longest body wins below).
        gap_ok = last + 1 < n <= last + 5 and nxt == n + 1
        if n == last + 1 or n == last or gap_ok:
            runs[-1].append((st, en, sec))
            last = n

    # Ignore short runs (e.g. a Statement of Objects) and keep, per section, the
    # candidate with the longest body, which drops the one-line TOC entries.
    biggest = max((len(r) for r in runs), default=0)
    starts = sorted(x for r in runs if len(r) >= biggest / 2 for x in r)
    best: dict[str, Chunk] = {}
    for i, (st, en, sec) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(full)
        body = full[en:end].strip()
        if len(body) < MIN_CHARS:
            continue
        chunk = Chunk(act, sec, _title(body), page_at(st), re.sub(r"[ \t]+", " ", body))
        if sec not in best or len(chunk.text) > len(best[sec].text):
            best[sec] = chunk
    return sorted(best.values(), key=lambda c: (num(c.section), c.section))
