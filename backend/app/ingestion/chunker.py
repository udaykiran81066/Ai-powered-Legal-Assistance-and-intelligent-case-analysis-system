import re
from dataclasses import dataclass

# A new provision starts at a line like "420. Cheating and ..." or "66A. Punishment ..."
SECTION_RE = re.compile(r"^\s*(\d{1,3}[A-Z]{0,2})\.\s+(?=\S)", re.MULTILINE)
MIN_CHARS = 40


@dataclass
class Chunk:
    act: str
    section: str
    title: str
    page: int
    text: str


def _title(body: str) -> str:
    """Heading is the text up to the first '.—' / '.-' / newline-after-period."""
    first = body.strip().split("\n\n")[0].replace("\n", " ")
    m = re.match(r"(.{3,200}?)\s*[.—–-]{1,2}\s*(?=[A-Z(]|$)", first)
    return (m.group(1) if m else first[:120]).strip(" .—-")


def chunk_by_section(act: str, pages: list[tuple[int, str]]) -> list[Chunk]:
    """Split an act into one chunk per section.

    Pages are joined with offset tracking so a section that spans pages keeps
    the page where it starts. Section numbers must increase monotonically,
    which filters out numbered lists inside provisions.
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

    # Acts often print a table of contents (the same numbers, tiny bodies) before the
    # body. A sequence restart at 1-3 begins a new run; per section we later keep the
    # candidate with the longest body, which drops the TOC entries.
    starts, last = [], 0
    for m in SECTION_RE.finditer(full):
        n = num(m.group(1))
        if last < n <= last + 5 or (n <= 3 and last > 10):
            starts.append((m.start(), m.end(), m.group(1)))
            last = n
        elif n == last and m.group(1)[-1:].isalpha():
            starts.append((m.start(), m.end(), m.group(1)))

    best: dict[str, Chunk] = {}
    for i, (s, e, sec) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(full)
        body = full[e:end].strip()
        if len(body) < MIN_CHARS:
            continue
        chunk = Chunk(act, sec, _title(body), page_at(s), re.sub(r"[ 	]+", " ", body))
        if sec not in best or len(chunk.text) > len(best[sec].text):
            best[sec] = chunk
    chunks = list(best.values())
    return chunks
