#!/usr/bin/env python3
"""
render_card.py
Renders high-quality 3:4 aspect ratio (1080x1440) Xiaohongshu image cards for Photography Magazine summaries.
Supported Card Types:
- cover: Gallery-style title cover with master insight & pill tags
- checklist: Step-by-step shooting formula & practical advice
- comparison: "Amateur Pitfalls vs Master Perspective" visual breakdown
"""

import sys
import os
import re
import argparse
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1440

# Colors (Gallery Darkroom Aesthetic)
BG_DARK = (18, 20, 26)         # 深邃哑光暗夜灰
CARD_BG = (28, 32, 42)         # 典雅暗房画廊卡片底色
ACCENT_GOLD = (245, 171, 53)   # 经典胶片琥珀金 (核心视觉强调)
ACCENT_RED = (255, 60, 75)     # 小红书/徕卡标杆红
ACCENT_CYAN = (78, 205, 196)   # 胶片冷调青 (辅助对比)
TEXT_WHITE = (255, 255, 255)   # 纯白
TEXT_MUTED = (165, 175, 195)   # 辅助冷灰字
LINE_BORDER = (45, 52, 68)     # 分割线与外边框

# Font Candidates
FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/harmonyos-sans/HarmonyOS_Sans_SC.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
    # Windows
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
    "C:\\Windows\\Fonts\\simsun.ttc",
]

EMOJI_FONT_CANDIDATES = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "C:\\Windows\\Fonts\\seguiemj.ttf",
]

def get_font(size: int, bold: bool = False):
    """Load system font with fallback."""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_emoji_img(char: str, target_size: int = 34):
    """Render emoji icon cleanly."""
    emoji_font_path = None
    for p in EMOJI_FONT_CANDIDATES:
        if os.path.exists(p):
            emoji_font_path = p
            break
    if not emoji_font_path:
        return None

    try:
        e_font = ImageFont.truetype(emoji_font_path, 109)
        temp = Image.new('RGBA', (140, 140), (0, 0, 0, 0))
        t_draw = ImageDraw.Draw(temp)
        t_draw.text((10, 10), char, font=e_font, embedded_color=True)
        bbox = temp.getbbox()
        if bbox:
            cropped = temp.crop(bbox)
            w, h = cropped.size
            scale = target_size / max(w, h)
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            return cropped.resize(new_size, Image.Resampling.LANCZOS)
    except Exception:
        pass
    return None

def wrap_text_by_width(text: str, font, max_width: int, max_lines: int = 6):
    """Wrap Chinese and mixed text avoiding punctuation at start of lines."""
    tokens = re.findall(r'[a-zA-Z0-9_\-\(\)\/]+|\s+|[\u4e00-\u9fff]|[，。？！、：；）》”’“‘（【】]|.', text)
    lines = []
    curr = ""
    PUNCT_NO_START = "，。？！、：；）》”’"
    for token in tokens:
        test_line = curr + token
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        if w > max_width:
            if token in PUNCT_NO_START and curr:
                curr += token
                lines.append(curr.strip())
                curr = ""
            else:
                if curr.strip():
                    lines.append(curr.strip())
                curr = token.lstrip()
        else:
            curr = test_line
    if curr.strip():
        lines.append(curr.strip())
    return lines[:max_lines]

def split_title(title: str, font, max_w: int = 940):
    """Split title semantically into 2 or 3 lines."""
    if "\n" in title:
        return [l.strip() for l in title.split("\n") if l.strip()]
    for punct in ["？", "?", "！", "!", "：", ":", "——", " "]:
        if punct in title:
            parts = title.split(punct, 1)
            left = parts[0] + (punct if punct not in [" ", ""] else "")
            right = parts[1].strip()
            if left and right:
                w_left = font.getbbox(left)[2] - font.getbbox(left)[0]
                w_right = font.getbbox(right)[2] - font.getbbox(right)[0]
                if w_left <= max_w and w_right <= max_w:
                    return [left, right]
    return wrap_text_by_width(title, font, max_w, max_lines=4)

def draw_header_badge(img: Image.Image, draw: ImageDraw.ImageDraw, text="摄影杂志 · 视觉精读", icon_char="📷"):
    """Draw top branding badge with photography icon."""
    font_badge = get_font(28, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    cam_icon = get_emoji_img(icon_char, 30)
    icon_w = cam_icon.width if cam_icon else 0
    gap = 10 if cam_icon else 0

    pad_left = 18
    pad_right = 22
    pad_y = 12

    total_w = pad_left + icon_w + gap + tw + pad_right
    total_h = max(30, th) + pad_y * 2
    x0, y0 = 70, 70
    x1, y1 = x0 + total_w, y0 + total_h
    radius = total_h // 2

    # Draw pill badge
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=(34, 39, 52), outline=ACCENT_GOLD, width=2)

    # Paste icon
    if cam_icon:
        ix = x0 + pad_left
        iy = y0 + (total_h - cam_icon.height) // 2
        img.paste(cam_icon, (ix, iy), cam_icon)
        tx = ix + icon_w + gap
    else:
        tx = x0 + pad_left

    ty = y0 + (total_h - th) // 2 - bbox[1]
    draw.text((tx, ty), text, font=font_badge, fill=ACCENT_GOLD)

def draw_footer(draw, text="收藏实践 · 翻完一本好杂志"):
    """Draw bottom footer bar."""
    font_foot = get_font(26)
    draw.line([(70, HEIGHT - 110), (WIDTH - 70, HEIGHT - 110)], fill=LINE_BORDER, width=2)
    draw.text((70, HEIGHT - 85), text, font=font_foot, fill=TEXT_MUTED)
    draw.text((WIDTH - 280, HEIGHT - 85), "@摄影美学精读", font=font_foot, fill=ACCENT_GOLD)

def render_cover(title: str, subtitle: str, tag: str, output_path: str):
    """Render Xiaohongshu 3:4 Cover Card for Photography Magazine."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # 1. Top badge
    draw_header_badge(img, draw, text="摄影杂志 · 视觉精读", icon_char="📷")
    
    # 2. Tag chip (Properly sized pill with flame/film icon)
    if tag:
        clean_tag = tag.replace("🔥", "").replace("🎞️", "").strip()
        font_tag = get_font(30, bold=True)
        bbox = draw.textbbox((0, 0), clean_tag, font=font_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        film_icon = get_emoji_img('🎞️', 32)
        icon_w = film_icon.width if film_icon else 0
        gap = 10 if film_icon else 0

        pad_left = 18
        pad_right = 24
        pad_y = 12

        total_w = pad_left + icon_w + gap + tw + pad_right
        total_h = max(32, th) + pad_y * 2
        x0, y0 = 70, 160
        x1, y1 = x0 + total_w, y0 + total_h
        radius = total_h // 2

        # Rounded pill in ACCENT_RED
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=ACCENT_RED)

        if film_icon:
            fx = x0 + pad_left
            fy = y0 + (total_h - film_icon.height) // 2
            img.paste(film_icon, (fx, fy), film_icon)
            tx = fx + icon_w + gap
        else:
            tx = x0 + pad_left

        ty = y0 + (total_h - th) // 2 - bbox[1]
        draw.text((tx, ty), clean_tag, font=font_tag, fill=TEXT_WHITE)

    # 3. Main Title (Large, wrapped semantically)
    font_title = get_font(72, bold=True)
    title_lines = split_title(title, font_title, WIDTH - 140)
        
    y = 280
    for i, line in enumerate(title_lines):
        # Highlight last line with amber accent color if more than 1 line
        color = ACCENT_GOLD if i == len(title_lines) - 1 and len(title_lines) > 1 else TEXT_WHITE
        draw.text((70, y), line, font=font_title, fill=color)
        y += 105

    # 4. Center card with Subtitle / Master Insight
    card_top = max(y + 35, 680)
    card_bottom = min(card_top + 450, HEIGHT - 160)
    draw.rounded_rectangle([(70, card_top), (WIDTH - 70, card_bottom)], radius=24, fill=CARD_BG, outline=LINE_BORDER, width=3)
    
    font_sub_title = get_font(38, bold=True)
    draw.text((110, card_top + 45), "💡 顶级杂志大师洞察：", font=font_sub_title, fill=ACCENT_GOLD)
    
    font_sub = get_font(34)
    available_w = WIDTH - 140 - 80
    sub_lines = wrap_text_by_width(subtitle, font_sub, available_w, max_lines=6)
        
    sy = card_top + 115
    for sline in sub_lines:
        draw.text((110, sy), sline, font=font_sub, fill=TEXT_WHITE)
        sy += 58
        
    draw_footer(draw)
    img.save(output_path, quality=95)
    print(f"Cover card saved to: {output_path}")

def render_checklist(title: str, points: list, output_path: str):
    """Render Actionable Photography Shooting / Composition Checklist Card."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_badge(img, draw, text="实操拆解 · 拍摄配方", icon_char="📐")
    
    # Title
    font_title = get_font(56, bold=True)
    draw.text((70, 160), title, font=font_title, fill=TEXT_WHITE)
    
    # Checklist boxes
    y = 265
    font_item_title = get_font(36, bold=True)
    font_item_body = get_font(30)
    font_num = get_font(26, bold=True)
    
    for i, pt in enumerate(points[:4]):
        item_title = pt.get("title", f"拍摄要点 {i+1}")
        item_desc = pt.get("desc", "")
        
        # Draw item card
        card_h = 225
        draw.rounded_rectangle([(70, y), (WIDTH - 70, y + card_h)], radius=20, fill=CARD_BG, outline=LINE_BORDER, width=2)
        
        # Step number pill badge
        num_str = f"0{i+1}"
        num_bbox = draw.textbbox((0, 0), num_str, font=font_num)
        nw = num_bbox[2] - num_bbox[0]
        nh = num_bbox[3] - num_bbox[1]
        badge_w = nw + 20
        badge_h = 40
        bx0, by0 = 105, y + 26
        draw.rounded_rectangle([(bx0, by0), (bx0 + badge_w, by0 + badge_h)], radius=10, fill=(38, 44, 58), outline=ACCENT_GOLD, width=1)
        draw.text((bx0 + 10, by0 + (badge_h - nh)//2 - num_bbox[1]), num_str, font=font_num, fill=ACCENT_GOLD)

        # Title of box
        draw.text((bx0 + badge_w + 16, y + 26), item_title, font=font_item_title, fill=TEXT_WHITE)
        
        # Body wrap
        available_w = WIDTH - 140 - 70
        blines = wrap_text_by_width(item_desc, font_item_body, available_w, max_lines=2)
            
        by = y + 88
        for bl in blines:
            draw.text((105, by), bl, font=font_item_body, fill=TEXT_MUTED)
            by += 46
            
        y += 255
        
    draw_footer(draw)
    img.save(output_path, quality=95)
    print(f"Checklist card saved to: {output_path}")

def render_comparison(title: str, amateur: dict, master: dict, output_path: str):
    """Render Amateur Pitfalls vs Master Vision Comparison Card."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_badge(img, draw, text="避坑对照 · 认知跃迁", icon_char="🔍")
    
    # Title
    font_title = get_font(54, bold=True)
    draw.text((70, 160), title, font=font_title, fill=TEXT_WHITE)
    
    # Box 1: Amateur Pitfall
    y1 = 265
    box_h = 430
    draw.rounded_rectangle([(70, y1), (WIDTH - 70, y1 + box_h)], radius=22, fill=(35, 26, 30), outline=ACCENT_RED, width=2)
    
    font_tag = get_font(26, bold=True)
    tag1_text = "新手常见盲区"
    t1_bbox = draw.textbbox((0, 0), tag1_text, font=font_tag)
    t1_w = t1_bbox[2] - t1_bbox[0]
    t1_h = t1_bbox[3] - t1_bbox[1]
    draw.rounded_rectangle([(105, y1 + 26), (105 + t1_w + 32, y1 + 26 + t1_h + 20)], radius=10, fill=ACCENT_RED)
    draw.text((121, y1 + 36 - t1_bbox[1]), tag1_text, font=font_tag, fill=TEXT_WHITE)
    
    font_item_title = get_font(36, bold=True)
    draw.text((105, y1 + 95), amateur.get("title", "盲目依赖大光圈虚化"), font=font_item_title, fill=TEXT_WHITE)
    
    font_item_body = get_font(30)
    amateur_desc = amateur.get("desc", "只顾把背景完全虚化，忽略了环境叙事与主体互动，导致照片毫无张力与记忆点。")
    alines = wrap_text_by_width(amateur_desc, font_item_body, WIDTH - 210, max_lines=4)
    ay = y1 + 160
    for al in alines:
        draw.text((105, ay), al, font=font_item_body, fill=(230, 190, 195))
        ay += 46

    # Box 2: Master Perspective
    y2 = y1 + box_h + 35
    draw.rounded_rectangle([(70, y2), (WIDTH - 70, y2 + box_h)], radius=22, fill=(28, 36, 44), outline=ACCENT_GOLD, width=2)
    
    tag2_text = "杂志大师解法"
    t2_bbox = draw.textbbox((0, 0), tag2_text, font=font_tag)
    t2_w = t2_bbox[2] - t2_bbox[0]
    t2_h = t2_bbox[3] - t2_bbox[1]
    draw.rounded_rectangle([(105, y2 + 26), (105 + t2_w + 32, y2 + 26 + t2_h + 20)], radius=10, fill=ACCENT_GOLD)
    draw.text((121, y2 + 36 - t2_bbox[1]), tag2_text, font=font_tag, fill=(18, 20, 26))
    
    draw.text((105, y2 + 95), master.get("title", "收小光圈，构建多层叙事"), font=font_item_title, fill=TEXT_WHITE)
    
    master_desc = master.get("desc", "收光圈至 f/5.6~f/8，利用前景框架与景深层级交代环境，用光影反差自然引导视觉焦点。")
    mlines = wrap_text_by_width(master_desc, font_item_body, WIDTH - 210, max_lines=4)
    my = y2 + 160
    for ml in mlines:
        draw.text((105, my), ml, font=font_item_body, fill=TEXT_MUTED)
        my += 46
        
    draw_footer(draw)
    img.save(output_path, quality=95)
    print(f"Comparison card saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Render Xiaohongshu Photography Cards")
    parser.add_argument("--type", choices=["cover", "checklist", "comparison"], default="cover")
    parser.add_argument("--title", required=True, help="Main title")
    parser.add_argument("--subtitle", default="", help="Subtitle / Key conclusion")
    parser.add_argument("--tag", default="构图进阶", help="Tag pill")
    parser.add_argument("--points", nargs="*", help="Key points for checklist format: 'Title|Desc'")
    parser.add_argument("--amateur-title", default="死记硬背九宫格构图", help="Amateur title for comparison")
    parser.add_argument("--amateur-desc", default="把主体机械放在交叉点，画面呆板没有张力与呼吸感。", help="Amateur desc")
    parser.add_argument("--master-title", default="用视线引导与负空间建立张力", help="Master title for comparison")
    parser.add_argument("--master-desc", default="根据被摄体朝向留出视觉呼吸感，利用光线明暗对比自然牵引目光。", help="Master desc")
    parser.add_argument("--output", default="card.png", help="Output file path")
    args = parser.parse_args()

    if args.type == "cover":
        render_cover(args.title, args.subtitle, args.tag, args.output)
    elif args.type == "checklist":
        pts = []
        if args.points:
            for p in args.points:
                parts = p.split("|", 1)
                pts.append({"title": parts[0], "desc": parts[1] if len(parts) > 1 else ""})
        else:
            pts = [
                {"title": "焦段视角与透视选择", "desc": "35mm交代人与环境关系，50mm呈现真实纪实视角，85mm提炼几何关系"},
                {"title": "光影雕刻：寻找侧逆光", "desc": "避开正午直射光，利用侧逆光在边缘勾勒高光轮廓，增强立体雕刻感"},
                {"title": "极简减法与框架借景", "desc": "先做减法剔除杂物，利用门窗、阴影或树枝形成自然画框引导视线"},
                {"title": "快门时机：决定性瞬间", "desc": "提前预判主体行进路线，设置快门优先或连拍，在肢体张力最强一瞬按下"}
            ]
        render_checklist(args.title, pts, args.output)
    elif args.type == "comparison":
        amateur = {"title": args.amateur_title, "desc": args.amateur_desc}
        master = {"title": args.master_title, "desc": args.master_desc}
        render_comparison(args.title, amateur, master, args.output)

if __name__ == "__main__":
    main()
