#!/usr/bin/env python3
"""
extract_magazine.py
Photography Magazine & Article Extractor
Extracts text and identifies critical photography concepts:
Composition rules, lighting setups, camera settings/focal lengths, aesthetic theories, and practical shooting checklists.
"""

import sys
import os
import re
import json
import subprocess

def extract_raw_text(pdf_path: str) -> str:
    """Extract raw text from PDF using pdftotext or python library fallback."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Magazine PDF file not found: {pdf_path}")
    
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

    # 3. Fallback to PyPDF2 if installed
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except ImportError:
        pass

    raise RuntimeError(
        "pdftotext is not installed or failed, and no python pdf library was found.\n"
        "Please install poppler-utils:\n"
        "  macOS: brew install poppler\n"
        "  Ubuntu/Debian: sudo apt-get install poppler-utils\n"
        "  Python fallback: pip install pypdf"
    )

def parse_magazine_sections(text: str) -> dict:
    """Parse common photography magazine sections and techniques from text."""
    
    # Heuristics for photography terminology
    composition_keywords = ["构图", "三分法", "引导线", "框架", "留白", "负空间", "对称", "视线", "前景", "透视", "视角", "composition", "framing", "leading lines", "rule of thirds"]
    lighting_keywords = ["光影", "自然光", "侧光", "逆光", "顺光", "伦勃朗光", "顶光", "黄金时刻", "蓝调时刻", "明暗对比", "漫反射", "硬光", "柔光", "lighting", "shadow", "golden hour"]
    gear_keywords = ["焦段", "镜头", "光圈", "快门", "感光度", "ISO", "f/", "mm", "景深", "色温", "黑白", "胶片", "测光", "aperture", "shutter", "focal length"]
    
    found_compositions = []
    found_lighting = []
    found_gear = []

    for line in text.split("\n"):
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 10:
            continue
        if any(k in line_clean for k in composition_keywords) and len(found_compositions) < 6:
            found_compositions.append(line_clean)
        if any(k in line_clean for k in lighting_keywords) and len(found_lighting) < 6:
            found_lighting.append(line_clean)
        if any(k in line_clean for k in gear_keywords) and len(found_gear) < 6:
            found_gear.append(line_clean)

    # Master quotes heuristic (looking for quotation marks or colon dialogue)
    quote_matches = re.findall(r'[“"「]([^”"」]{15,120})[”"」]', text)
    notable_quotes = [q.strip() for q in quote_matches[:5]]

    sections = {
        "title_and_header": text.strip().split("\n")[0][:100] if text.strip() else "",
        "key_composition_insights": found_compositions,
        "key_lighting_insights": found_lighting,
        "camera_and_settings_insights": found_gear,
        "master_quotes": notable_quotes,
        "raw_sample": text[:3000]
    }
    return sections

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 extract_magazine.py <path-to-pdf-or-txt> [--json | --output <out_path>]")
        sys.exit(0)
        
    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    if input_path.lower().endswith(".pdf"):
        raw_text = extract_raw_text(input_path)
    else:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

    parsed = parse_magazine_sections(raw_text)
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
            print(f"Extracted magazine content saved to: {out_file}")
            return

    # Default output
    if out_format == "json":
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    else:
        print(f"=== Extracted Magazine Content ({len(raw_text)} chars) ===")
        print(f"标题/头条: {parsed['title_and_header']}")
        print(f"\n【构图要素采样】({len(parsed['key_composition_insights'])}条):")
        for c in parsed['key_composition_insights'][:3]:
            print(f"  • {c[:90]}")
        print(f"\n【光影要素采样】({len(parsed['key_lighting_insights'])}条):")
        for l in parsed['key_lighting_insights'][:3]:
            print(f"  • {l[:90]}")
        print(f"\n【参数与焦段采样】({len(parsed['camera_and_settings_insights'])}条):")
        for g in parsed['camera_and_settings_insights'][:3]:
            print(f"  • {g[:90]}")
        if parsed['master_quotes']:
            print(f"\n【大师金句采样】:")
            for q in parsed['master_quotes'][:3]:
                print(f"  “{q}”")

if __name__ == "__main__":
    main()
