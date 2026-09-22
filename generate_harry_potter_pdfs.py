from pathlib import Path
import textwrap


OUTPUT_DIR = Path(__file__).parent / "data"
MIN_BYTES = 250 * 1024

FOCUS_AREAS = [
    "friendship and loyalty",
    "identity and belonging",
    "the cost of prejudice",
    "choice versus destiny",
    "grief and memory",
    "the ethics of power",
    "mentorship and responsibility",
    "school as a changing community",
    "courage under pressure",
    "family, inheritance, and self-definition",
    "secrecy and revelation",
    "humor as resilience",
    "rules, institutions, and justice",
    "language, names, and reputation",
    "the meaning of home",
    "sacrifice and reciprocal care",
    "fear and the imagination",
    "growing older and moral agency",
    "objects as carriers of memory",
    "the relationship between knowledge and power",
    "leadership and collective action",
    "outsiders and chosen communities",
    "ambition and its consequences",
    "love as an active practice",
    "the limits of prophecy",
    "tradition and reform",
    "adventure and ordinary life",
    "the role of teachers",
    "truth, rumor, and public narrative",
    "resistance to authoritarianism",
    "sports, competition, and identity",
    "the emotional geography of familiar places",
    "the tension between innocence and experience",
    "repair after conflict",
    "moral luck and accountability",
    "friendship across difference",
    "the symbolism of light and darkness",
    "the dangers of dehumanizing labels",
    "knowledge passed between generations",
    "the private self and the public role",
    "the value of imperfect heroes",
    "community rituals and shared memory",
    "the pressure of exceptional expectations",
    "how stories teach empathy",
    "the relationship between fear and control",
    "the possibility of second chances",
    "how settings shape character",
    "the narrative function of mystery",
    "the balance of wonder and danger",
    "what makes an ending feel earned",
]


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


ANGLES = [
    "character motivation",
    "setting and atmosphere",
    "conflict and consequence",
    "dialogue and silence",
    "symbols and recurring objects",
    "the growth of trust",
    "the role of rules",
    "private choices versus public roles",
    "the effect of memory",
    "the difference between knowledge and wisdom",
]

QUESTIONS = [
    "What changes when the reader sees the same event from another character's perspective?",
    "Which apparently ordinary detail becomes emotionally important later?",
    "How does the setting pressure the characters to reveal their values?",
    "What does the story suggest about responsibility after a mistake?",
    "Where does a character confuse confidence with certainty?",
    "How does a relationship change without being announced directly?",
    "Which institution benefits from the way the problem is described?",
    "What does a character protect, and what does that protection cost?",
    "How does humor alter the emotional meaning of a dangerous moment?",
    "What would be lost if the mystery were solved immediately?",
]


def paragraph(topic: str, index: int) -> str:
    angle = ANGLES[(index - 1) % len(ANGLES)]
    question = QUESTIONS[(index - 1) % len(QUESTIONS)]
    return (
        f"Section {index} studies {topic} through {angle}. {question} "
        "An original reading can begin with the contrast between what a character believes at the start of a scene "
        "and what the reader understands by its end. The novels often make that contrast visible through movement, "
        "interrupted conversations, withheld information, or an object whose meaning changes with context. Rather than "
        "treating magic as decoration, this approach asks what the fantastic element makes easier to see about ordinary "
        "human behavior. A promise can become a burden, a rule can protect one person while excluding another, and a "
        "private fear can become a public conflict. The most revealing evidence is often relational: who speaks first, "
        "who is believed, who gets another chance, and who performs bravery for an audience. This page therefore reads "
        "the story as a sequence of choices with consequences, while leaving room for disagreement among readers."
    )


def make_pages(topic: str, book_number: int) -> list[str]:
    title = f"Harry Potter Stories: An Original Critical Guide {book_number:02d}"
    subtitle = f"A thematic study of {topic}"
    blocks = [title, subtitle, "Original commentary; no source text reproduced."]
    for index in range(1, 211):
        blocks.append(paragraph(topic, index))
    pages = []
    for block in blocks:
        lines = []
        for line in textwrap.wrap(block, width=86):
            lines.append(line)
        pages.append(lines)
    return pages


def build_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    for page_lines in pages:
        commands = [b"BT", b"/F1 10 Tf", b"50 760 Td", b"13 TL"]
        for line in page_lines:
            commands.append(f"({escape_pdf_text(line)}) Tj T*".encode("ascii"))
        commands.append(b"ET")
        stream = b"\n".join(commands)
        content_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_ids.append(content_id)

    pages_id = len(objects) + 1
    page_objects = []
    for content_id in page_ids:
        page_objects.append(
            add_object(
                b"<< /Type /Page /Parent "
                + str(pages_id).encode("ascii")
                + b" 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 "
                + str(font_id).encode("ascii")
                + b" 0 R >> >> /Contents "
                + str(content_id).encode("ascii")
                + b" 0 R >>"
            )
        )

    kids = b"[" + b" ".join(f"{page_id} 0 R".encode("ascii") for page_id in page_objects) + b"]"
    objects.insert(pages_id - 1, b"<< /Type /Pages /Kids " + kids + b" /Count " + str(len(page_objects)).encode("ascii") + b" >>")
    catalog_id = add_object(b"<< /Type /Catalog /Pages " + str(pages_id).encode("ascii") + b" 0 R >>")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root "
        + str(catalog_id).encode("ascii")
        + b" 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return bytes(output)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for number, topic in enumerate(FOCUS_AREAS, start=1):
        pdf = build_pdf(make_pages(topic, number))
        if len(pdf) < MIN_BYTES:
            raise RuntimeError(f"Generated file {number} is only {len(pdf)} bytes")
        (OUTPUT_DIR / f"harry_potter_guide_{number:02d}.pdf").write_bytes(pdf)
    print(f"Created {len(FOCUS_AREAS)} PDFs in {OUTPUT_DIR}")
    print(f"Smallest file: {min(path.stat().st_size for path in OUTPUT_DIR.glob('*.pdf'))} bytes")


if __name__ == "__main__":
    main()