"""Multimodal figure and vision extraction utilities."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from docurag.cache import disk_cache, with_retry
from docurag.config import get_settings
from docurag.schemas import FigureData, FigureDescription

logger = logging.getLogger(__name__)


def _is_fakes() -> bool:
    if os.getenv("DOCURAG_FAKES") in ("1", "true", "True"):
        return True
    try:
        return get_settings().DOCURAG_FAKES
    except Exception:
        return False


def extract_figures(
    path: Union[Path, str],
    page_number: Optional[int] = None,
    document_id: Optional[str] = None,
) -> List[FigureData]:
    """Extract embedded figures and charts from a document page.

    Args:
        path: Path to the document.
        page_number: Specific page number to inspect, or None for all pages.

    Returns:
        List of FigureData objects representing extracted figure metadata.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        if _is_fakes():
            return [
                FigureData(
                    figure_id="fig_sample_1",
                    image_path="storage/figs/fig_sample_1.png",
                    page=page_number or 1,
                    bbox=[50.0, 100.0, 450.0, 350.0],
                    caption="Simulated architectural diagram",
                )
            ]
        raise FileNotFoundError(f"Document not found: {path}")

    import fitz

    settings = get_settings()
    settings.ensure_dirs()
    doc_id = document_id or path_obj.stem
    out_dir = settings.figs_dir / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(path_obj))
    xref_page_counts: Dict[int, int] = {}
    try:
        for page in doc:
            seen_on_page = {img[0] for img in page.get_images(full=True)}
            for xref in seen_on_page:
                xref_page_counts[xref] = xref_page_counts.get(xref, 0) + 1

        pages = [page_number] if page_number is not None else list(range(1, doc.page_count + 1))
        figures: List[FigureData] = []
        for pnum in pages:
            page = doc[pnum - 1]
            figure_idx = 0
            for image_info in page.get_images(full=True):
                xref = image_info[0]
                width = int(image_info[2] or 0)
                height = int(image_info[3] or 0)
                if min(width, height) < settings.MIN_IMG_PX:
                    continue
                ratio = width / max(height, 1)
                if ratio > 8.0 or ratio < 0.125:
                    continue
                if doc.page_count > 2 and xref_page_counts.get(xref, 0) / doc.page_count > 0.5:
                    continue

                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                figure_idx += 1
                figure_id = f"{doc_id}_p{pnum}_fig{figure_idx}"
                image_path = out_dir / f"fig_p{pnum}_{figure_idx}.png"
                pix.save(str(image_path))
                rects = page.get_image_rects(xref)
                bbox = [float(v) for v in rects[0]] if rects else None
                figures.append(
                    FigureData(
                        figure_id=figure_id,
                        image_path=str(image_path),
                        page=pnum,
                        bbox=bbox,
                        caption=f"Embedded figure on page {pnum}",
                    )
                )
        return figures
    finally:
        doc.close()


def _strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def describe_figure(image_path: Union[Path, str]) -> FigureDescription:
    """Analyze a figure image with multimodal LLM and produce structured description.

    Args:
        image_path: Path to the image file on disk.

    Returns:
        FigureDescription model instance.
    """
    return _describe_figure_cached(str(image_path))


@disk_cache(namespace="figure_descriptions")
@with_retry(tries=2, base=0.2)
def _describe_figure_cached(image_path: str) -> FigureDescription:
    if _is_fakes():
        return FigureDescription(
            type="bar_chart",
            title="Simulated Metric Comparison",
            caption="Comparison of performance benchmarks across versions.",
            key_values=[{"label": "v1.0", "value": "120", "unit": "ms"}],
            relationships="",
            visible_text="Performance benchmarks v1.0",
        )

    try:
        from google import genai

        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            return FigureDescription(type="other", caption="Vision description unavailable.")
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = (
            "You are indexing a figure from a document so it can be found by text search. "
            "Describe the image and return ONLY valid JSON with this shape:\n"
            "{\n"
            "  \"type\": \"bar_chart|line_chart|pie_chart|table|diagram|photo|scanned_text|other\",\n"
            "  \"title\": \"<title if visible, else empty>\",\n"
            "  \"caption\": \"<2-3 sentence description of what the figure shows>\",\n"
            "  \"key_values\": [{\"label\": \"<x/category/series>\", \"value\": \"<number or text>\", \"unit\": \"<unit or empty>\"}],\n"
            "  \"relationships\": \"<for diagrams/flowcharts: A -> B -> C; else empty>\",\n"
            "  \"visible_text\": \"<all legible text in the image>\"\n"
            "}\n"
            "Read numbers exactly as shown. If a value is unreadable, omit it. Do not guess."
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt, __import__("google.genai.types", fromlist=["Part"]).Part.from_bytes(data=Path(image_path).read_bytes(), mime_type="image/png" if str(image_path).lower().endswith(".png") else "image/jpeg")],
        )
        raw = getattr(response, "text", "") or ""
        data = json.loads(_strip_json_fence(raw))

        # Hardening: Ensure all required fields exist before validation
        # to avoid Pydantic validation errors on partial LLM responses.
        defaults = {
            "type": "other",
            "title": "",
            "caption": "No description provided.",
            "key_values": [],
            "relationships": "",
            "visible_text": ""
        }
        for field, default_val in defaults.items():
            if field not in data or data[field] is None:
                data[field] = default_val

        return FigureDescription.model_validate(data)
    except Exception as exc:
        logger.warning("Figure description failed for %s: %s", image_path, exc)
        return FigureDescription(type="other", caption=f"Figure at {Path(image_path).name}")


def transcribe_page(image_path: Union[Path, str]) -> str:
    """Full-page multimodal vision transcription fallback when OCR confidence is low.

    Args:
        image_path: Path to the rendered page image.

    Returns:
        Transcribed plain text.
    """
    if _is_fakes():
        return "Simulated multimodal vision transcription for scanned page."

    try:
        from google import genai
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            return ""

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = "Transcribe all text from this page exactly as it appears. Preserve layout where possible."

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt, __import__("google.genai.types", fromlist=["Part"]).Part.from_bytes(data=Path(image_path).read_bytes(), mime_type="image/png" if str(image_path).lower().endswith(".png") else "image/jpeg")],
        )
        return getattr(response, "text", "") or ""
    except Exception as exc:
        logger.warning("Vision transcription failed for %s: %s", image_path, exc)
        return ""
