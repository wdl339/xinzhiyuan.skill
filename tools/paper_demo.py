#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None


ARXIV_API_URL = "https://export.arxiv.org/api/query"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a Xinzhiyuan-style paper rewrite demo from a local PDF "
            "or an arXiv title. Optionally generate the final article via an "
            "OpenAI-compatible API."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", help="Path to a local paper PDF")
    source.add_argument("--title", help="Paper title or a close title query for arXiv")

    parser.add_argument(
        "--work-dir",
        default="demo_outputs",
        help="Base output directory for prepared assets",
    )
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory used to store PDFs downloaded from arXiv",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=12,
        help="Maximum number of PDF pages to extract",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=24000,
        help="Maximum number of source characters to include in the rewrite prompt",
    )
    parser.add_argument(
        "--language",
        choices=["zh", "en"],
        default="zh",
        help="Output language for the rewrite prompt and optional article",
    )
    parser.add_argument(
        "--length",
        choices=["short", "standard", "long"],
        default="standard",
        help="Target article length profile",
    )
    parser.add_argument(
        "--generate-article",
        action="store_true",
        help="Generate the final article via an OpenAI-compatible API",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="Base URL for the OpenAI-compatible API",
    )
    parser.add_argument(
        "--openai-model",
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="Model name for the OpenAI-compatible API",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="API key for the OpenAI-compatible API",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "paper"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_prompt_template() -> str:
    template_path = Path(__file__).resolve().parent.parent / "prompts" / "demo_writer.md"
    return template_path.read_text(encoding="utf-8")


def search_arxiv(title_query: str) -> Dict[str, Any]:
    params = {
        "search_query": f'all:"{title_query}"',
        "start": 0,
        "max_results": 5,
    }
    response = requests.get(ARXIV_API_URL, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", namespace)
    if not entries:
        raise RuntimeError(f'No arXiv result found for title query: "{title_query}"')

    query_norm = normalize_text(title_query)
    best_match: Optional[Dict[str, Any]] = None

    for entry in entries:
        entry_title = get_xml_text(entry, "atom:title", namespace)
        summary = get_xml_text(entry, "atom:summary", namespace)
        abs_url = get_xml_text(entry, "atom:id", namespace)
        authors = [author.findtext("{http://www.w3.org/2005/Atom}name", default="") for author in entry.findall("atom:author", namespace)]
        pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"
        score = score_title_match(query_norm, normalize_text(entry_title))
        candidate = {
            "title": compact_whitespace(entry_title),
            "summary": compact_whitespace(summary),
            "authors": authors,
            "arxiv_abs_url": abs_url,
            "pdf_url": pdf_url,
            "score": score,
        }
        if best_match is None or candidate["score"] > best_match["score"]:
            best_match = candidate

    assert best_match is not None
    return best_match


def get_xml_text(entry: ET.Element, tag: str, namespace: Dict[str, str]) -> str:
    node = entry.find(tag, namespace)
    return node.text if node is not None and node.text else ""


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    return compact_whitespace(value)


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def score_title_match(query_norm: str, candidate_norm: str) -> float:
    if not candidate_norm:
        return 0.0
    if query_norm == candidate_norm:
        return 1000.0

    query_tokens = set(query_norm.split())
    candidate_tokens = set(candidate_norm.split())
    if not query_tokens:
        return 0.0

    overlap = len(query_tokens & candidate_tokens)
    coverage = overlap / max(len(query_tokens), 1)
    prefix_bonus = 0.5 if candidate_norm.startswith(query_norm[: min(20, len(query_norm))]) else 0.0
    return coverage + prefix_bonus


def download_file(url: str, target_path: Path) -> None:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    target_path.write_bytes(response.content)


def extract_pdf_text(pdf_path: Path, max_pages: int) -> str:
    if PdfReader is None:
        raise RuntimeError(
            "pypdf is required for PDF extraction. Install dependencies with "
            "`pip3 install -r requirements.txt`."
        )

    reader = PdfReader(str(pdf_path))
    chunks: List[str] = []
    for idx, page in enumerate(reader.pages):
        if idx >= max_pages:
            break
        page_text = page.extract_text() or ""
        if page_text.strip():
            chunks.append(page_text)

    if not chunks:
        raise RuntimeError(f"Could not extract text from PDF: {pdf_path}")

    return "\n\n".join(chunks)


def extract_section(text: str, start_patterns: List[str], end_patterns: List[str]) -> str:
    lowered = text.lower()
    start_idx = None
    for pattern in start_patterns:
        match = re.search(pattern, lowered, flags=re.MULTILINE)
        if match:
            start_idx = match.end()
            break
    if start_idx is None:
        return ""

    end_idx = len(text)
    search_space = lowered[start_idx:]
    for pattern in end_patterns:
        match = re.search(pattern, search_space, flags=re.MULTILINE)
        if match:
            end_idx = start_idx + match.start()
            break

    return text[start_idx:end_idx].strip()


def extract_abstract_from_pdf(text: str) -> str:
    return compact_whitespace(
        extract_section(
            text,
            [r"\babstract\b\s*[:\-]?\s*"],
            [
                r"\n\s*(?:1|i)\.?\s+introduction\b",
                r"\n\s*introduction\b",
                r"\n\s*keywords\b",
            ],
        )
    )


def extract_intro_excerpt(text: str) -> str:
    section = extract_section(
        text,
        [r"\n\s*(?:1|i)\.?\s+introduction\b", r"\n\s*introduction\b"],
        [
            r"\n\s*(?:2|ii)\.?\s+[a-z]",
            r"\n\s*related work\b",
            r"\n\s*background\b",
            r"\n\s*method\b",
        ],
    )
    return compact_whitespace(section)


def extract_conclusion_excerpt(text: str) -> str:
    section = extract_section(
        text,
        [r"\n\s*conclusion[s]?\b", r"\n\s*(?:7|8|9)\.?\s+conclusion[s]?\b"],
        [r"\n\s*reference[s]?\b", r"\n\s*acknowledg"],
    )
    return compact_whitespace(section)


def build_excerpt(full_text: str, abstract: str, intro: str, conclusion: str, max_chars: int) -> str:
    parts: List[str] = []
    if abstract:
        parts.append("## Abstract\n" + abstract)
    if intro:
        parts.append("## Introduction Excerpt\n" + intro[:6000])
    if conclusion:
        parts.append("## Conclusion Excerpt\n" + conclusion[:4000])

    remainder = full_text
    abstract_match = re.search(r"\babstract\b\s*[:\-]?\s*", remainder, flags=re.IGNORECASE)
    if abstract_match:
        remainder = remainder[abstract_match.start():]
    remainder = compact_whitespace(remainder)
    parts.append("## Body Excerpt\n" + remainder[: max_chars * 2])

    merged = "\n\n".join(part for part in parts if part)
    return merged[:max_chars]


def length_hint(length: str, language: str) -> str:
    if language == "zh":
        mapping = {
            "short": "300-500 字快讯",
            "standard": "1200-1800 字标准稿",
            "long": "2500 字以上长文",
        }
    else:
        mapping = {
            "short": "short brief",
            "standard": "standard article",
            "long": "long-form article",
        }
    return mapping[length]


def build_prompt(
    template: str,
    meta: Dict[str, Any],
    source_excerpt: str,
    language: str,
    length: str,
) -> str:
    rendered_meta = json.dumps(meta, ensure_ascii=False, indent=2)
    instruction = "Chinese" if language == "zh" else "English"
    parts = [
        template.strip(),
        "---",
        "Demo Task",
        "",
        f"Write the final article in {instruction}.",
        f"Target length: {length_hint(length, language)}.",
        "",
        "Paper metadata:",
        "```json",
        rendered_meta,
        "```",
        "",
        "Source excerpt:",
        "```text",
        source_excerpt,
        "```",
    ]
    return "\n".join(parts).strip() + "\n"


def call_openai_compatible_api(
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a careful Chinese AI journalist. Write in a "
                        "high-energy tech-media style, but never invent facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_meta_from_local_pdf(pdf_path: Path) -> Dict[str, Any]:
    return {
        "title": pdf_path.stem,
        "authors": [],
        "summary": "",
        "source": "local_pdf",
        "pdf_path": str(pdf_path.resolve()),
    }


def guess_title_from_pdf_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()[:20] if line.strip()]
    best_line = ""
    best_score = -1.0
    banned_fragments = [
        "provided proper attribution",
        "journalistic or scholarly works",
        "permission to reproduce",
        "copyright",
    ]

    for line in lines:
        compact = compact_whitespace(line)
        if len(compact) < 12:
            continue
        if len(compact) > 140:
            continue
        if "@" in compact:
            continue
        if re.search(r"\babstract\b", compact, flags=re.IGNORECASE):
            break
        lowered = compact.lower()
        if any(fragment in lowered for fragment in banned_fragments):
            continue

        words = re.findall(r"[A-Za-z][A-Za-z\-']*", compact)
        if not words:
            continue
        titlecase_words = sum(1 for word in words if word[:1].isupper())
        score = titlecase_words / len(words)
        if compact == compact.title():
            score += 0.5
        if 15 <= len(compact) <= 80:
            score += 0.3

        if score > best_score:
            best_score = score
            best_line = compact

    return best_line[:180]


def main() -> int:
    args = parse_args()
    template = read_prompt_template()

    work_root = Path(args.work_dir).resolve()
    download_root = Path(args.download_dir).resolve()
    ensure_dir(work_root)
    ensure_dir(download_root)

    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        meta = build_meta_from_local_pdf(pdf_path)
    else:
        meta = search_arxiv(args.title)
        paper_slug = slugify(meta["title"])
        pdf_path = download_root / f"{paper_slug}.pdf"
        download_file(meta["pdf_url"], pdf_path)
        meta["source"] = "arxiv_title_search"
        meta["pdf_path"] = str(pdf_path)

    full_text = extract_pdf_text(pdf_path, args.max_pages)
    if args.pdf:
        guessed_title = guess_title_from_pdf_text(full_text)
        if guessed_title:
            meta["title"] = guessed_title
    abstract = meta.get("summary") or extract_abstract_from_pdf(full_text)
    intro = extract_intro_excerpt(full_text)
    conclusion = extract_conclusion_excerpt(full_text)

    meta["abstract"] = abstract
    meta["extracted_pages"] = args.max_pages
    meta["language"] = args.language
    meta["length"] = args.length

    source_excerpt = build_excerpt(
        full_text=full_text,
        abstract=abstract,
        intro=intro,
        conclusion=conclusion,
        max_chars=args.max_chars,
    )

    output_slug = slugify(meta["title"])
    out_dir = work_root / output_slug
    ensure_dir(out_dir)

    prompt = build_prompt(
        template=template,
        meta=meta,
        source_excerpt=source_excerpt,
        language=args.language,
        length=args.length,
    )

    write_json(out_dir / "paper_meta.json", meta)
    write_text(out_dir / "source_excerpt.txt", source_excerpt)
    write_text(out_dir / "rewrite_prompt.md", prompt)

    if args.generate_article:
        if not args.openai_api_key:
            raise RuntimeError(
                "Missing API key. Set OPENAI_API_KEY or pass --openai-api-key "
                "to enable --generate-article."
            )
        article = call_openai_compatible_api(
            api_key=args.openai_api_key,
            base_url=args.openai_base_url,
            model=args.openai_model,
            prompt=prompt,
        )
        write_text(out_dir / "xinzhiyuan_article.md", article + "\n")

    summary = {
        "paper_title": meta["title"],
        "pdf_path": str(pdf_path),
        "output_dir": str(out_dir),
        "generated_article": bool(args.generate_article),
        "files": [
            str(out_dir / "paper_meta.json"),
            str(out_dir / "source_excerpt.txt"),
            str(out_dir / "rewrite_prompt.md"),
        ],
    }
    if args.generate_article:
        summary["files"].append(str(out_dir / "xinzhiyuan_article.md"))

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI error surface
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
