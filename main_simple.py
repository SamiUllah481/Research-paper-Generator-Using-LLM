from dotenv import load_dotenv
import os
import json
import argparse
from typing import List

from google import genai
from pydantic import BaseModel

from tools import search_tool, wiki_tool, save_tool, web_search_tool

load_dotenv()


class ResearchResponse(BaseModel):
    topic: str
    abstract: str
    introduction: str
    literature_review: str
    methodology: str
    analysis_and_findings: str
    discussion: str
    future_research: str
    conclusion: str
    sources: List[str]
    tools_used: List[str]


# Initialize the Google GenAI client lazily when needed
def get_genai_client():
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


SYSTEM_PROMPT = """
You are an expert academic researcher tasked with generating a comprehensive research paper.
Create a detailed academic paper following standard research paper structure and academic writing conventions.
Format your response in this JSON structure exactly (keys must match):
{
    "topic": "",
    "abstract": "",
    "introduction": "",
    "literature_review": "",
    "methodology": "",
    "analysis_and_findings": "",
    "discussion": "",
    "future_research": "",
    "conclusion": "",
    "sources": [],
    "tools_used": []
}

Please produce long, academic-quality content for each section (use the earlier conversation guidance for approximate target lengths).
"""


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```json"):
        t = t[len("```json"):]
    if t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def generate_research(query: str, model: str = "gemini-2.5-flash") -> ResearchResponse:
    # Run tools proactively and attach outputs to the prompt
    tool_outputs = {}
    try:
        ws = web_search_tool(query, max_results=5)
        tool_outputs["web_search"] = ws

        wp = search_tool(query, results=5, sentences=3)
        tool_outputs["wikipedia_search"] = wp

        try:
            wsum = wiki_tool(query, sentences=5)
        except Exception:
            wsum = ""
        tool_outputs["wikipedia_summary"] = wsum

        # Save a snapshot of tool outputs (helps debugging and gives the model
        # explicit external evidence to cite). This is a small snapshot.
        combined = f"Query: {query}\n\nWEB SEARCH:\n{ws}\n\nWIKIPEDIA SEARCH:\n{wp}\n\nWIKIPEDIA SUMMARY:\n{wsum}\n"
        tool_snapshot_msg = save_tool(combined)
        tool_outputs["tool_snapshot_saved"] = tool_snapshot_msg
    except Exception as e:
        tool_outputs["tool_error"] = str(e)

    tools_block = json.dumps(tool_outputs, ensure_ascii=False, indent=2)

    final_prompt = (
        f"{SYSTEM_PROMPT}\n\nUser query: {query}\n\nTool outputs (JSON):\n{tools_block}\n\n"
        "Using the above tool outputs where relevant, produce the full research paper as a single JSON object following the schema exactly."
    )

    client = get_genai_client()
    final_resp = client.models.generate_content(model=model, contents=final_prompt)
    # Extract text from response (handle different shapes)
    try:
        final_text = final_resp.text
    except Exception:
        try:
            final_text = final_resp.candidates[0].content.parts[0].text
        except Exception:
            final_text = str(final_resp)

    final_text = _strip_code_fences(final_text)

    # Try to parse JSON
    try:
        data = json.loads(final_text)
        return ResearchResponse(**data)
    except Exception:
        # Best-effort extraction using regex when JSON is malformed
        import re

        def extract_string(key: str) -> str:
            pattern = r'"' + re.escape(key) + r'"\s*:\s*"([\s\S]*?)"\s*(,|})'
            m = re.search(pattern, final_text)
            return m.group(1).strip() if m else ""

        def extract_list(key: str) -> List[str]:
            pattern = r'"' + re.escape(key) + r'"\s*:\s*\[([\s\S]*?)\]'
            m = re.search(pattern, final_text)
            if not m:
                return []
            inner = m.group(1)
            items = re.findall(r'"([\s\S]*?)"', inner)
            return [it.strip() for it in items]

        parsed = {
            "topic": extract_string("topic"),
            "abstract": extract_string("abstract"),
            "introduction": extract_string("introduction"),
            "literature_review": extract_string("literature_review"),
            "methodology": extract_string("methodology"),
            "analysis_and_findings": extract_string("analysis_and_findings"),
            "discussion": extract_string("discussion"),
            "future_research": extract_string("future_research"),
            "conclusion": extract_string("conclusion"),
            "sources": extract_list("sources"),
            "tools_used": extract_list("tools_used"),
        }
        return ResearchResponse(**parsed)


def build_paper_text(result: ResearchResponse) -> str:
    lines = []
    lines.append(result.topic.upper())
    lines.append('\nABSTRACT\n')
    lines.append(result.abstract)
    lines.append('\nINTRODUCTION\n')
    lines.append(result.introduction)
    lines.append('\nLITERATURE REVIEW\n')
    lines.append(result.literature_review)
    lines.append('\nMETHODOLOGY\n')
    lines.append(result.methodology)
    lines.append('\nANALYSIS AND FINDINGS\n')
    lines.append(result.analysis_and_findings)
    lines.append('\nDISCUSSION\n')
    lines.append(result.discussion)
    lines.append('\nFUTURE RESEARCH\n')
    lines.append(result.future_research)
    lines.append('\nCONCLUSION\n')
    lines.append(result.conclusion)
    lines.append('\nREFERENCES\n')
    for i, s in enumerate(result.sources, 1):
        lines.append(f'[{i}] {s}')
    lines.append('\nRESEARCH METHODOLOGY & TOOLS\n')
    for t in result.tools_used:
        lines.append(f'• {t}')
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a research paper using Google GenAI")
    parser.add_argument("--query", "-q", help="Research query / topic", required=False)
    parser.add_argument("--model", "-m", default="gemini-2.5-flash", help="GenAI model to use")
    parser.add_argument("--out", "-o", help="Output filename (PDF). If omitted a timestamped file will be used")
    args = parser.parse_args()

    query = args.query
    if not query:
        # Prompt interactively if running in a TTY
        try:
            query = input("Enter research topic or question: ")
        except Exception:
            print("No query provided. Use --query to provide a topic.")
            return

    try:
        # Minimal CLI output per user request
        print("Generating research paper (this may take a minute)...")
        result = generate_research(query, args.model)

        paper_text = build_paper_text(result)

        # Determine output filename
        out_filename = args.out
        if out_filename:
            if not os.path.splitext(out_filename)[1]:
                out_filename = out_filename + ".pdf"
        else:
            from datetime import datetime

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_filename = f"research_output_{ts}.pdf"

        save_msg = save_tool(paper_text, filename=out_filename)
        print(save_msg)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
