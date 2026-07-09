"""Generate minimal valid PDFs for testing (no external dependencies)."""

import zlib


def _gen_pdf_text(text: str) -> bytes:
    content = _encode_content(text, 612, 792)
    return _build_pdf(content)


def make_minimal_pdf(
    title: str = "Test Article Title",
    body: str | None = None,
) -> bytes:
    text_lines = body or _default_body()
    return _gen_pdf_text(text_lines)


def _default_body() -> str:
    return (
        "Abstract\n"
        "This is a test abstract for the paper.\n"
        "\n"
        "Introduction\n"
        "This is the introduction section.\n"
        "Some introductory text.\n"
        "\n"
        "2. Methods\n"
        "The methods section describes methodology.\n"
        "\n"
        "2.1 Statistical Analysis\n"
        "We used statistical methods.\n"
        "\n"
        "Results\n"
        "Our results show significant findings.\n"
        "\n"
        "Discussion\n"
        "We discuss the implications.\n"
        "\n"
        "References\n"
        "[1] Author A, Author B. Paper title. Journal. 2023.\n"
        "[2] Author C. Another paper. Science. 2024.\n"
    )


def make_pdf_with_tables() -> bytes:
    text = (
        "Abstract\n"
        "Table test abstract.\n"
        "\n"
        "Results\n"
        "The results are shown in the table below.\n"
        "\n"
        "| Header1 | Header2 | Header3 |\n"
        "|---------|---------|---------|\n"
        "| Cell A  | Cell B  | Cell C  |\n"
        "| Cell D  | Cell E  | Cell F  |\n"
        "\n"
        "Discussion\n"
        "Some discussion.\n"
    )
    return _gen_pdf_text(text)


def make_encrypted_pdf() -> bytes:
    content = _encode_content("", 612, 792)
    return _build_pdf(content, encrypt=True)


# --- raw PDF builder ---------------------------------------------------------


def _encode_content(text: str, pw: float, ph: float) -> bytes:
    lines = []
    y = int(ph) - 50
    for line_text in text.split("\n"):
        safe = line_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        lines.append(f"BT /F1 11 Tf 50 {y} Td ({safe}) Tj ET")
        y -= 14
    return ("\n".join(lines)).encode("latin-1", errors="replace")


def _build_pdf(content: str | bytes, encrypt: bool = False) -> bytes:
    encrypt_dict = b""
    encrypt_ref = b""

    if encrypt:
        encrypt_ref = b"/Encrypt 4 0 R "
        encrypt_dict = (
            b"4 0 obj\n"
            b"<< /Filter /Standard /V 1 /R 2 /O (\x00\x00\x00\x00) /U (\x00\x00\x00\x00) "
            b"/P -4 /Length 40 >>\nendobj\n"
        )

    stream_data = content if isinstance(content, bytes) else content.encode("latin-1", errors="replace")
    compressed = zlib.compress(stream_data)
    stream_len = len(compressed)
    n_objs = 5 + (1 if encrypt else 0)
    xref_size = n_objs + 1  # +1 for free entry 0

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page " + encrypt_ref + b"/Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 5 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica >> >> >> >>\n"
        b"endobj\n"
        + encrypt_dict +
        b"5 0 obj\n"
        b"<< /Length " + str(stream_len).encode() + b" /Filter /FlateDecode >>\n"
        b"stream\n" + compressed + b"\nendstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 " + str(xref_size).encode() + b"\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        + ((b"0000000196 00000 n \n") if encrypt else b"") +
        b"0000000266 00000 n \n"
        b"0000000315 00000 n \n"
        b"trailer\n"
        b"<< /Size " + str(xref_size).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n"
        b"318\n"
        b"%%%%EOF\n"
    )
    return pdf