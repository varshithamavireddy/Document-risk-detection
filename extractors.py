import csv
import io
import json
from pathlib import Path
import pymupdf


def extract_document(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import pymupdf
        doc = pymupdf.open(stream=data, filetype="pdf")
        return "\n\n".join(f"[Page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc))
    if suffix == ".docx":
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()) + "\n" + "\n".join(
            " | ".join(cell.text for cell in row.cells) for table in doc.tables for row in table.rows
        )
    if suffix == ".xlsx":
        from openpyxl import load_workbook
        book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        parts = []
        for sheet in book.worksheets:
            parts.append(f"[Sheet: {sheet.title}]")
            for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
                values = [str(value) if value is not None else "" for value in row]
                if any(values):
                    parts.append(f"Row {row_num}: " + " | ".join(values))
        return "\n".join(parts)
    if suffix == ".pptx":
        from pptx import Presentation
        deck = Presentation(io.BytesIO(data))
        return "\n\n".join(
            f"[Slide {i}]\n" + "\n".join(shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False))
            for i, slide in enumerate(deck.slides, 1)
        )
    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8-sig", errors="replace")
    if suffix == ".json":
        return json.dumps(json.loads(data.decode("utf-8-sig")), ensure_ascii=False, indent=2)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(io.BytesIO(data)))
    raise ValueError(f"Unsupported file format: {suffix}")
