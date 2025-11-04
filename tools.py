import wikipedia
import requests
import json
import textwrap
import os
from datetime import datetime
from typing import Optional


def web_search_tool(query: str, max_results: int = 5) -> str:
    """Perform a lightweight web search using DuckDuckGo Instant Answer API (no API key required).

    Returns a short, human-readable summary of the top results (text + url when available).
    Falls back to Wikipedia search if DuckDuckGo returns little data.
    """
    try:
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1,
        }
        r = requests.get("https://api.duckduckgo.com/", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        results = []
        # Instant answer abstract
        abstract = data.get("Abstract") or data.get("Heading")
        if abstract:
            results.append(f"InstantAnswer: {abstract}")

        # Related topics may contain useful snippets
        related = data.get("RelatedTopics", [])
        for item in related:
            if isinstance(item, dict):
                text = item.get("Text") or item.get("Result")
                first_url = item.get("FirstURL")
                if text:
                    if first_url:
                        results.append(f"{text} — {first_url}")
                    else:
                        results.append(text)
            if len(results) >= max_results:
                break

        if results:
            return "\n\n".join(results)

        # Fallback: use wikipedia search
        titles = wikipedia.search(query, results=max_results)
        if titles:
            out = []
            for t in titles:
                try:
                    s = wikipedia.summary(t, sentences=2)
                    out.append(f"{t}: {s}")
                except Exception:
                    out.append(t)
            return "\n\n".join(out)

        return "No web search results found."
    except Exception as e:
        return f"Web search tool error: {e}"


def search_tool(query: str, results: int = 3, sentences: int = 3) -> str:
    """Perform a simple search using the wikipedia package and return short summaries for top results."""
    try:
        titles = wikipedia.search(query, results=results)
        if not titles:
            return "No search results found."

        summaries = []
        for t in titles:
            try:
                s = wikipedia.summary(t, sentences=sentences)
                summaries.append(f"{t}: {s}")
            except Exception as e:
                summaries.append(f"{t}: (summary error: {e})")

        return "\n\n".join(summaries)
    except Exception as e:
        return f"Search tool error: {e}"


def wiki_tool(title: str, sentences: int = 5) -> str:
    """Fetch a Wikipedia summary for a given title."""
    try:
        return wikipedia.summary(title, sentences=sentences)
    except Exception as e:
        return f"Wiki tool error for '{title}': {e}"


def save_tool(content: str, filename: Optional[str] = None, as_pdf: bool = True) -> str:
    """Save content to a PDF file (preferred) or fallback to text file.

    Returns a user-friendly path message on success or an error message on failure.
    """
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if filename is None:
            ext = "pdf" if as_pdf else "txt"
            filename = f"research_snapshot_{ts}.{ext}"

        # Attempt to write PDF using fpdf
        if as_pdf:
            try:
                from fpdf import FPDF

                def try_write_pdf(text, out_name):
                    pdf = FPDF(unit="mm", format="A4")
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)

                    # Break content into paragraphs and wrap lines
                    for paragraph in text.split("\n\n"):
                        paragraph = paragraph.strip()
                        if not paragraph:
                            continue
                        lines = textwrap.wrap(paragraph, width=95)
                        for line in lines:
                            pdf.cell(0, 6, txt=line, ln=1)
                        pdf.ln(4)

                    pdf.output(out_name)

                # First attempt: write as-is
                try_write_pdf(content, filename)
                return f"Saved to {filename}"
            except Exception as e:
                # If PDF writing fails (common cause: latin-1 encoding error),
                # attempt simple Unicode normalization and punctuation replacement
                err_str = str(e)
                try:
                    import unicodedata

                    def normalize_common(text: str) -> str:
                        # replace common smart punctuation with ASCII equivalents
                        replacements = {
                            '\u2013': '-',  # en dash
                            '\u2014': ' - ',  # em dash
                            '\u2018': "'",  # left single quote
                            '\u2019': "'",  # right single quote
                            '\u201c': '"',  # left double quote
                            '\u201d': '"',  # right double quote
                            '\u2026': '...',  # ellipsis
                            '\u2010': '-',
                        }
                        for k, v in replacements.items():
                            text = text.replace(k, v)
                        # decompose other unicode characters and strip combining marks
                        text = unicodedata.normalize('NFKD', text)
                        # keep characters that are encodable in latin-1 after normalization
                        try:
                            text.encode('latin-1')
                            return text
                        except Exception:
                            # fallback: remove characters that can't be encoded
                            return text.encode('latin-1', 'ignore').decode('latin-1')

                    safe_content = normalize_common(content)
                    try:
                        # retry PDF write with normalized content
                        from fpdf import FPDF

                        pdf = FPDF(unit="mm", format="A4")
                        pdf.set_auto_page_break(auto=True, margin=15)
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for paragraph in safe_content.split("\n\n"):
                            paragraph = paragraph.strip()
                            if not paragraph:
                                continue
                            lines = textwrap.wrap(paragraph, width=95)
                            for line in lines:
                                pdf.cell(0, 6, txt=line, ln=1)
                            pdf.ln(4)
                        pdf.output(filename)
                        return f"Saved to {filename} (normalized unicode characters)"
                    except Exception as e2:
                        # give up and write a text fallback including both errors
                        fallback_name = filename.rsplit('.', 1)[0] + '.txt'
                        with open(fallback_name, 'w', encoding='utf-8') as f:
                            f.write(f"PDF save failed: {err_str}\nRetry with normalization failed: {e2}\n\nOriginal content below:\n\n")
                            f.write(content)
                        return f"PDF save failed ({err_str}). Normalization retry failed ({e2}). Saved text fallback to {fallback_name}"
                except Exception:
                    fallback_name = filename.rsplit('.', 1)[0] + '.txt'
                    with open(fallback_name, 'w', encoding='utf-8') as f:
                        f.write(f"PDF save failed: {e}\n\nOriginal content below:\n\n")
                        f.write(content)
                    return f"PDF save failed ({e}). Saved text fallback to {fallback_name}"

        # Non-PDF fallback: write text
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Saved to {filename}"
    except Exception as e:
        return f"Save tool error: {e}"
