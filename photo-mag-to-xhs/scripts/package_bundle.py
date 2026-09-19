#!/usr/bin/env python3
"""
package_bundle.py
Assembles and validates a complete Xiaohongshu release bundle for Photography Magazine summaries.
Includes text safety checks, image sequencing, post.txt formatting, and meta.json generation.
"""

import sys
import os
import shutil
import json
import argparse

PROHIBITED_WORDS = [
    "最权威", "天下第一", "100%", "绝对出片", "包教包会", "完全碾压", 
    "国家级大片", "唯一真理", "神作保底", "顶级神作"
]

def check_text_safety(text: str) -> list:
    hits = []
    for w in PROHIBITED_WORDS:
        if w in text:
            hits.append(w)
    return hits

def main():
    parser = argparse.ArgumentParser(description="Package Xiaohongshu Photography Release Bundle")
    parser.add_argument("--dir", required=True, help="Target output bundle directory")
    parser.add_argument("--title", required=True, help="Note title (<= 20 chars recommended)")
    parser.add_argument("--content-file", required=True, help="Path to markdown content file")
    parser.add_argument("--images", nargs="+", required=True, help="List of card image paths in order")
    parser.add_argument("--tags", nargs="*", default=["摄影", "摄影技巧", "摄影杂志", "大师构图", "审美提升"], help="Tags list")
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    with open(args.content_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Safety check
    violations = check_text_safety(args.title + " " + content)
    if violations:
        print(f"⚠️ [警告] 发现敏感/绝对化违禁词: {violations}，建议在发布前优化替换！")

    # Copy images sequentially
    copied_imgs = []
    for i, img_path in enumerate(args.images):
        ext = os.path.splitext(img_path)[1] or ".png"
        dest_name = f"slide_{i+1:02d}{ext}"
        dest_path = os.path.join(args.dir, dest_name)
        shutil.copyfile(img_path, dest_path)
        copied_imgs.append(dest_name)

    # Format tags and post
    tags_formatted = " ".join([f"#{t.lstrip('#')}" for t in args.tags])
    full_post = f"{args.title}\n\n{content}\n\n{tags_formatted}"
    
    post_txt_path = os.path.join(args.dir, "post.txt")
    with open(post_txt_path, "w", encoding="utf-8") as f:
        f.write(full_post)

    meta = {
        "title": args.title,
        "title_len": len(args.title),
        "content_len": len(content),
        "image_count": len(copied_imgs),
        "images": copied_imgs,
        "tags": args.tags,
        "violations": violations
    }
    with open(os.path.join(args.dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"✅ 小红书摄影图文交付包已打包完成: {args.dir}")
    print(f"   - 标题: {args.title} ({len(args.title)}字)")
    print(f"   - 图片数量: {len(copied_imgs)} 张 (已按发布顺序编号)")
    print(f"   - 发布正文文件: {post_txt_path}")

if __name__ == "__main__":
    main()
