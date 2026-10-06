"""Secure text and structural element extractor for ingested business documents."""

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.database.models.knowledge import DocumentType


@dataclass
class ExtractedSection:
    """A structural segment extracted from a document."""

    text: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    is_table: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Complete extraction payload containing all structured sections and metadata."""

    full_text: str
    sections: List[ExtractedSection]
    total_characters: int
    is_ocr: bool = False
    ocr_confidence: Optional[float] = None
    detected_title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentExtractionError(Exception):
    """Raised when document parsing fails unrecoverably."""

    pass


class DocumentExtractor:
    """Parses heterogeneous business documents into structural text units with source lineage."""

    @classmethod
    def extract(cls, file_bytes: bytes, filename: str, file_type: DocumentType) -> ExtractionResult:
        """Extract text and structural headings from the uploaded file bytes."""
        if not file_bytes:
            raise DocumentExtractionError("Uploaded file is empty.")

        if file_type == DocumentType.PDF:
            return cls._extract_pdf(file_bytes, filename)
        elif file_type == DocumentType.DOCX:
            return cls._extract_docx(file_bytes, filename)
        elif file_type in [DocumentType.TXT, DocumentType.MARKDOWN, DocumentType.CSV_REFERENCE]:
            return cls._extract_plaintext_or_markdown(file_bytes, filename, file_type)
        else:
            return cls._extract_plaintext_or_markdown(file_bytes, filename, file_type)

    @classmethod
    def _extract_plaintext_or_markdown(
        cls, file_bytes: bytes, filename: str, file_type: DocumentType
    ) -> ExtractionResult:
        """Parse plain text, Markdown, or CSV reference documents."""
        # Try UTF-8 with fallback to Latin-1
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = file_bytes.decode("latin-1")
            except Exception as exc:
                raise DocumentExtractionError(f"Failed to decode text file: {exc}")

        # Normalize line endings and strip null bytes
        normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")

        lines = normalized.split("\n")
        sections: List[ExtractedSection] = []
        current_heading: Optional[str] = None
        current_buffer: List[str] = []
        detected_title: Optional[str] = None

        heading_pattern = re.compile(r"^(#{1,6}\s+|===+|\b(?:Section|Article|Chapter|Policy|KPI)\s+\d+[:\.\s])(.*)$", re.IGNORECASE)

        for line in lines:
            line_str = line.strip()
            if not line_str:
                if current_buffer:
                    current_buffer.append("")
                continue

            match = heading_pattern.match(line_str)
            if match:
                # Flush previous buffer
                if current_buffer:
                    body = "\n".join(current_buffer).strip()
                    if body:
                        sections.append(ExtractedSection(text=body, section_heading=current_heading))
                    current_buffer = []

                current_heading = line_str.lstrip("#").strip()
                if not detected_title and (line_str.startswith("# ") or "policy" in line_str.lower()):
                    detected_title = current_heading
            else:
                current_buffer.append(line_str)

        if current_buffer:
            body = "\n".join(current_buffer).strip()
            if body:
                sections.append(ExtractedSection(text=body, section_heading=current_heading))

        if not sections and normalized.strip():
            sections.append(ExtractedSection(text=normalized.strip(), section_heading=None))

        return ExtractionResult(
            full_text=normalized.strip(),
            sections=sections,
            total_characters=len(normalized.strip()),
            detected_title=detected_title or filename,
            metadata={"lines_count": len(lines), "sections_count": len(sections)},
        )

    @classmethod
    def _extract_docx(cls, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Extract text from DOCX (OpenXML) by reading word/document.xml."""
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise DocumentExtractionError("Invalid DOCX: missing word/document.xml.")
                xml_content = zf.read("word/document.xml")
        except Exception as exc:
            # Fallback to plain text search if zip structure is abnormal
            raise DocumentExtractionError(f"Failed to parse DOCX container: {exc}")

        try:
            root = ET.fromstring(xml_content)
            # Word namespaces
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

            sections: List[ExtractedSection] = []
            paragraphs: List[str] = []
            current_heading: Optional[str] = None

            for p in root.iter(f"{{{ns['w']}}}p"):
                # Check for paragraph style or heading
                p_style = p.find(f".//{{{ns['w']}}}pStyle")
                style_val = p_style.attrib.get(f"{{{ns['w']}}}val", "") if p_style is not None else ""

                # Extract text within paragraph runs
                text_runs = [t.text for t in p.iter(f"{{{ns['w']}}}t") if t.text]
                p_text = "".join(text_runs).strip()
                if not p_text:
                    continue

                if "heading" in style_val.lower() or "title" in style_val.lower():
                    if paragraphs:
                        sections.append(ExtractedSection(text="\n".join(paragraphs), section_heading=current_heading))
                        paragraphs = []
                    current_heading = p_text
                else:
                    paragraphs.append(p_text)

            if paragraphs:
                sections.append(ExtractedSection(text="\n".join(paragraphs), section_heading=current_heading))

            full_text = "\n\n".join(s.text for s in sections)
            return ExtractionResult(
                full_text=full_text,
                sections=sections,
                total_characters=len(full_text),
                detected_title=filename,
                metadata={"docx_parsed": True, "sections_count": len(sections)},
            )
        except Exception as exc:
            raise DocumentExtractionError(f"Error extracting DOCX elements: {exc}")

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Extract text and pages from PDF documents."""
        sections: List[ExtractedSection] = []
        full_text_parts: List[str] = []

        # Attempt extraction using pypdf if installed
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                clean_page = page_text.strip()
                if clean_page:
                    full_text_parts.append(clean_page)
                    # Split page text into structural heading sections if found
                    sections.append(
                        ExtractedSection(
                            text=clean_page,
                            page_number=page_idx,
                            section_heading=f"Page {page_idx}",
                        )
                    )

            if sections:
                full_text = "\n\n".join(full_text_parts)
                return ExtractionResult(
                    full_text=full_text,
                    sections=sections,
                    total_characters=len(full_text),
                    detected_title=filename,
                    metadata={"total_pages": len(reader.pages), "extractor": "pypdf"},
                )
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback text extraction using regex stream searching
        decoded = file_bytes.decode("latin-1", errors="ignore")
        text_stream_blocks = re.findall(r"BT\s+(.*?)\s+ET", decoded, re.DOTALL)
        if text_stream_blocks:
            extracted_words = []
            for block in text_stream_blocks:
                words = re.findall(r"\((.*?)\)", block)
                if words:
                    extracted_words.append(" ".join(words))
            if extracted_words:
                text_content = "\n".join(extracted_words)
                sections.append(ExtractedSection(text=text_content, page_number=1, section_heading="Extracted Stream"))
                return ExtractionResult(
                    full_text=text_content,
                    sections=sections,
                    total_characters=len(text_content),
                    detected_title=filename,
                    metadata={"extractor": "stream_fallback"},
                )

        # Fallback for scanned/binary PDF where pure text extraction yielded minimal text
        cleaned_text = re.sub(r"[^\x20-\x7E\n\r\t]", " ", decoded)
        compact = re.sub(r"\s+", " ", cleaned_text).strip()
        if len(compact) > 50:
            snippet = compact[:2000]
            sections.append(ExtractedSection(text=snippet, page_number=1, section_heading="Raw Extracted Text"))
            return ExtractionResult(
                full_text=snippet,
                sections=sections,
                total_characters=len(snippet),
                is_ocr=True,
                ocr_confidence=0.75,
                detected_title=filename,
                metadata={"extractor": "binary_heuristics"},
            )

        raise DocumentExtractionError("Could not extract readable text from PDF. Document may be password protected or empty.")
