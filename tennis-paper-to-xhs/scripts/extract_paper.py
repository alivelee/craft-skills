#!/usr/bin/env python3
"""
extract_paper.py
Academic Paper Text & Section Extractor for Sports Science & Tennis Papers
Extracts text and identifies critical sections (Abstract, Methodology, Results, Discussion, Practical Applications).
"""

import sys
import os
import re
import json
import subprocess

def extract_raw_text(pdf_path: str) -> str:
    """Extract raw text from PDF using pdftotext or python library fallback."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # 1. Try pdftotext (fast and layout-aware)
    try:
        cmd = ["pdftotext", "-layout", pdf_path, "-"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 2. Fallback to pypdf if installed
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except ImportError:
        pass

    # 3. Fallback to pypdf2 if installed
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except ImportError:
        pass

    raise RuntimeError(
        "pdftotext is not installed or failed, and no python pdf library was found.\n"
        "Please install poppler-utils:\n"
        "  Ubuntu/Debian: sudo apt-get install poppler-utils\n"
        "  macOS: brew install poppler\n"
        "  Python fallback: pip install pypdf"
    )

def parse_sections(text: str) -> dict:
    """Parse common academic sections from paper text."""
    lines = text.split("\n")
    
    # Common section header patterns
    patterns = {
        "abstract": re.compile(r"^\s*(abstract|summary)\b", re.I),
        "introduction": re.compile(r"^\s*(1\.?\s*)?introduction\b", re.I),
        "methods": re.compile(r"^\s*([1-9]\.?\s*)?(methods|methodology|materials and methods|experimental)\b", re.I),
        "results": re.compile(r"^\s*([1-9]\.?\s*)?(results|findings)\b", re.I),
        "discussion": re.compile(r"^\s*([1-9]\.?\s*)?(discussion)\b", re.I),
        "practical": re.compile(r"^\s*([1-9]\.?\s*)?(practical applications|coaching implications|conclusions?)\b", re.I),
    }
    
    sections = {
        "title_and_header": "",
        "abstract": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "practical_applications": "",
        "raw_sample": text[:3000]
    }
    
    # Simple heuristic to extract abstract
    abs_match = re.search(r"(?i)\babstract\b[\s\:\.\-]+(.*?)(?=\b(?:introduction|keywords|1\.|\n\s*\n\s*[A-Z\s]{4,})\b)", text, re.DOTALL)
    if abs_match:
        sections["abstract"] = abs_match.group(1).strip()[:4000]
    
    # Practical applications / Conclusion heuristic
    conc_match = re.search(r"(?i)\b(?:practical applications|coaching implications|conclusions?)\b[\s\:\.\-]+(.*?)(?=\b(?:references|acknowledg|appendix)\b|$)", text, re.DOTALL)
    if conc_match:
        sections["practical_applications"] = conc_match.group(1).strip()[:4000]
        
    return sections

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 extract_paper.py <path-to-pdf> [--json | --output <out_path>]")
        sys.exit(0)
        
    pdf_path = sys.argv[1]
    raw_text = extract_raw_text(pdf_path)
    parsed = parse_sections(raw_text)
    
    out_format = "json" if "--json" in sys.argv else "text"
    
    if "--output" in sys.argv:
        out_idx = sys.argv.index("--output") + 1
        if out_idx < len(sys.argv):
            out_file = sys.argv[out_idx]
            with open(out_file, "w", encoding="utf-8") as f:
                if out_format == "json":
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                else:
                    f.write(raw_text)
            print(f"Extracted content saved to: {out_file}")
            return

    # Default output stdout
    if out_format == "json":
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    else:
        print(f"=== Extracted Raw Text ({len(raw_text)} chars) ===")
        print(raw_text[:2000] + "\n\n...[truncated]...")

if __name__ == "__main__":
    main()
