"""Semantic, structural, and heading-aware chunking engine for knowledge documents."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.knowledge.extractor import ExtractedSection


@dataclass
class GeneratedChunk:
    """A semantic chunk generated from document sections."""

    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentChunker:
    """Splits extracted document sections into contextually coherent, bounded semantic chunks."""

    def __init__(
        self,
        target_chunk_tokens: int = 350,
        min_chunk_tokens: int = 5,
        max_chunk_tokens: int = 600,
        overlap_tokens: int = 50,
    ) -> None:
        self.target_chunk_tokens = target_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def estimate_tokens(self, text: str) -> int:
        """Approximates token count based on whitespace word boundaries (~1.3 tokens per word)."""
        words = len(text.split())
        return max(1, int(words * 1.3))

    def chunk_sections(self, sections: List[ExtractedSection]) -> List[GeneratedChunk]:
        """Convert a list of extracted sections into indexed chunks."""
        chunks: List[GeneratedChunk] = []
        chunk_idx = 0

        for sec in sections:
            sec_text = sec.text.strip()
            if not sec_text:
                continue

            sec_tokens = self.estimate_tokens(sec_text)

            # If section fits within target token bounds, keep as a single clean chunk
            if sec_tokens <= self.max_chunk_tokens:
                if sec_tokens >= self.min_chunk_tokens or not chunks:
                    chunk_idx += 1
                    chunks.append(
                        GeneratedChunk(
                            chunk_index=chunk_idx,
                            content=sec_text,
                            token_count=sec_tokens,
                            page_number=sec.page_number,
                            section_heading=sec.section_heading,
                            metadata={"section_is_table": sec.is_table},
                        )
                    )
                else:
                    # Append short snippet to previous chunk if exists
                    if chunks:
                        prev = chunks[-1]
                        prev.content = f"{prev.content}\n\n{sec_text}"
                        prev.token_count = self.estimate_tokens(prev.content)
            else:
                # Split large section by paragraphs or sentences with overlap
                sub_chunks = self._split_large_text(
                    text=sec_text,
                    page_number=sec.page_number,
                    section_heading=sec.section_heading,
                    start_index=chunk_idx + 1,
                )
                for sc in sub_chunks:
                    chunk_idx += 1
                    sc.chunk_index = chunk_idx
                    chunks.append(sc)

        if not chunks and sections:
            # Fallback for any content
            full_fallback = "\n\n".join(s.text for s in sections).strip()
            if full_fallback:
                chunks.append(
                    GeneratedChunk(
                        chunk_index=1,
                        content=full_fallback[:2000],
                        token_count=self.estimate_tokens(full_fallback[:2000]),
                        page_number=sections[0].page_number,
                        section_heading=sections[0].section_heading,
                    )
                )

        return chunks

    def _split_large_text(
        self,
        text: str,
        page_number: Optional[int],
        section_heading: Optional[str],
        start_index: int,
    ) -> List[GeneratedChunk]:
        """Split text across paragraph and sentence boundaries with token overlap."""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        results: List[GeneratedChunk] = []
        current_paragraphs: List[str] = []
        current_tokens = 0
        current_idx = start_index

        for p in paragraphs:
            p_tokens = self.estimate_tokens(p)

            if current_tokens + p_tokens > self.target_chunk_tokens and current_paragraphs:
                # Form chunk
                content = "\n\n".join(current_paragraphs).strip()
                results.append(
                    GeneratedChunk(
                        chunk_index=current_idx,
                        content=content,
                        token_count=current_tokens,
                        page_number=page_number,
                        section_heading=section_heading,
                    )
                )
                current_idx += 1

                # Keep overlap if paragraph allows
                if len(current_paragraphs) > 1 and self.estimate_tokens(current_paragraphs[-1]) <= self.overlap_tokens:
                    current_paragraphs = [current_paragraphs[-1], p]
                    current_tokens = self.estimate_tokens(current_paragraphs[0]) + p_tokens
                else:
                    current_paragraphs = [p]
                    current_tokens = p_tokens
            else:
                current_paragraphs.append(p)
                current_tokens += p_tokens

        if current_paragraphs:
            content = "\n\n".join(current_paragraphs).strip()
            results.append(
                GeneratedChunk(
                    chunk_index=current_idx,
                    content=content,
                    token_count=self.estimate_tokens(content),
                    page_number=page_number,
                    section_heading=section_heading,
                )
            )

        return results
