from typing import Optional, Literal, Union
from pydantic import BaseModel, Field

"""
Indexing conventions used across all location models:

- line, row, col, paragraph, run are 1-based indices (human-facing)
- start_char and end_char follow Python regex semantics:
  - start_char is 0-based and inclusive
  - end_char is 0-based and exclusive
- "line" refers to newline-delimited lines, not visual word wrapping
- DOCX page numbers are intentionally avoided (rendering-dependent)
"""


class TextLocation(BaseModel):
    doc_type: Literal["text"] = "text"
    start_char: int
    end_char: int
    line: Optional[int] = None  # newline-delimited line number (not word-wrap line)


class XlsxLocation(BaseModel):
    doc_type: Literal["xlsx"] = "xlsx"
    sheet: str
    row: int
    col: int
    cell: Optional[str] = None  # e.g. "B12" (optional convenience)


class DocxLocation(BaseModel):
    doc_type: Literal["docx"] = "docx"
    paragraph: Optional[int] = None
    run: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None


SensitiveLocation = Union[TextLocation, XlsxLocation, DocxLocation]


class SensitiveData(BaseModel):
    content: str = Field(..., description="The exact matched sensitive string")
    domain: str = Field(..., description="e.g. PII, SECRETS, FINANCIAL")
    data_category: str = Field(..., description="e.g. NRIC, Credit Card PAN")
    location: SensitiveLocation = Field(..., discriminator="doc_type")


# * Example usage
if __name__ == "__main__":
    sd = SensitiveData(
        content="1234-5678-9012-3456",
        domain="FINANCIAL",
        data_category="Credit Card PAN",
        location=XlsxLocation(
            sheet="Sheet1",
            row=10,
            col=2,
            cell="B10",
        ),
    )
    print("doc_type:", sd.location.doc_type)
    print(sd.model_dump())
    print("---\n")

    sd2 = SensitiveData(
        content="S1234567D",
        domain="PII",
        data_category="NRIC",
        location=TextLocation(
            start_char=100,
            end_char=109,
            line=5,
        ),
    )
    print("doc_type:", sd2.location.doc_type)
    print(sd2.model_dump())
    print("---\n")
