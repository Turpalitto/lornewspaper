"""Figure extractor.

Extracts embedded images from PDF pages and associates them with captions.
"""

from __future__ import annotations

from typing import Any

from document_processing_service.extractors.base import BaseExtractor
from document_processing_service.models import ExtractedFigure

_CAPTION_PREFIXES = ("Figure", "Fig.", "Fig", "Figure S", "Fig. S")


class FigureExtractor(BaseExtractor):
    name = "figures"

    async def extract(  # noqa: PLR0913
        self,
        doc: Any,
        *,
        raw_pages: list[str] | None = None,
        **kwargs: Any,
    ) -> list[ExtractedFigure]:
        result: list[ExtractedFigure] = []
        try:
            for page_num, page in enumerate(doc):
                images = page.get_images(full=True)
                page_text = page.get_text()
                captions = self._find_captions(page_text)

                for img_idx, _img in enumerate(images):
                    caption = captions[img_idx] if img_idx < len(captions) else ""
                    result.append(ExtractedFigure(
                        caption=caption,
                        page_number=page_num + 1,
                        image_index=img_idx,
                    ))
        except Exception:
            pass
        return result

    @staticmethod
    def _find_captions(page_text: str) -> list[str]:
        captions: list[str] = []
        lines = page_text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            for prefix in _CAPTION_PREFIXES:
                if stripped.lower().startswith(prefix.lower()):
                    # Collect caption text until next empty line or figure keyword
                    caption_lines = [stripped]
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if not next_line:
                            break
                        if any(next_line.lower().startswith(p.lower()) for p in _CAPTION_PREFIXES):
                            break
                        caption_lines.append(next_line)
                    captions.append(" ".join(caption_lines))
                    break
        return captions