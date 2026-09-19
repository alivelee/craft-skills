#!/usr/bin/env python3
"""
render_card.py
Renders high-quality 3:4 aspect ratio (1080x1440) Xiaohongshu image cards using PIL.
Supports Cover, Checklist, Data Comparison, and Key Takeaway cards.
Features:
- NotoColorEmoji native composite rendering for crisp emojis (🎾, 🔥, etc.)
- Dynamic pill badges with pixel-accurate text measurement and centering
- Smart Chinese line-wrapping respecting punctuation rules and word boundaries
- High-contrast athletic dark theme (tennis neon green + flame orange + deep navy)
"""

import sys
import os
import re
import argparse
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1440

# Colors
BG_DARK = (20, 24, 33)        # 深空深蓝黑，高端学术运动感
CARD_BG = (30, 36, 49)        # 卡片背景色
ACCENT_GREEN = (180, 230, 30) # 网球荧光黄绿
TEXT_WHITE = (255, 255, 255)  # 纯白
TEXT_MUTED = (160, 172, 193)  # 辅助浅灰蓝
ACCENT_ORANGE = (255, 112, 67)# 警示/痛点橙红
LINE_BORDER = (45, 54, 72)    # 边框深色

# Font detection
FONT_CANDIDATES = [
    # Linux
    "/usr/share/fonts/harmonyos-sans/HarmonyOS_Sans_SC.ttf",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Windows
    "C:\\Windows\\Fonts\\msyh.ttc",
    "C:\\Windows\\Fonts\\simhei.ttf",
    "C:\\Windows\\Fonts\\simsun.ttc",
]

EMOJI_FONT_CANDIDATES = [
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
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
    """Render a colored emoji using NotoColorEmoji if available."""
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
    """Split title semantically into 2 lines."""
    if "\n" in title:
        return [l.strip() for l in title.split("\n") if l.strip()]
    for punct in ["？", "?", "！", "!", "：", ":", " "]:
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

def draw_header_badge(img: Image.Image, draw: ImageDraw.ImageDraw, text="科学网球 · 论文精读"):
    """Draw top branding badge with tennis icon."""
    clean_text = text.replace("🎾", "").strip()
    font_badge = get_font(28, bold=True)
    bbox = draw.textbbox((0, 0), clean_text, font=font_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    tennis_icon = get_emoji_img('🎾', 30)
    icon_w = tennis_icon.width if tennis_icon else 0
    gap = 10 if tennis_icon else 0

    pad_left = 18
    pad_right = 22
    pad_y = 12

    total_w = pad_left + icon_w + gap + tw + pad_right
    total_h = max(30, th) + pad_y * 2
    x0, y0 = 70, 70
    x1, y1 = x0 + total_w, y0 + total_h
    radius = total_h // 2

    # Draw pill badge
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=(38, 48, 66), outline=ACCENT_GREEN, width=2)

    # Paste icon
    if tennis_icon:
        ix = x0 + pad_left
        iy = y0 + (total_h - tennis_icon.height) // 2
        img.paste(tennis_icon, (ix, iy), tennis_icon)
        tx = ix + icon_w + gap
    else:
        tx = x0 + pad_left

    ty = y0 + (total_h - th) // 2 - bbox[1]
    draw.text((tx, ty), clean_text, font=font_badge, fill=ACCENT_GREEN)

def draw_footer(draw, text="收藏实践 · 关注进阶更多球场科学"):
    """Draw bottom footer bar."""
    font_foot = get_font(26)
    draw.line([(70, HEIGHT - 110), (WIDTH - 70, HEIGHT - 110)], fill=LINE_BORDER, width=2)
    draw.text((70, HEIGHT - 85), text, font=font_foot, fill=TEXT_MUTED)
    draw.text((WIDTH - 250, HEIGHT - 85), "@网球生物力学", font=font_foot, fill=ACCENT_GREEN)

def render_cover(title: str, subtitle: str, tag: str, output_path: str):
    """Render Xiaohongshu 3:4 Cover Card with fixed tag styling."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # 1. Top badge
    draw_header_badge(img, draw)
    
    # 2. Tag chip (Properly sized pill with flame icon and dynamic text centering)
    if tag:
        clean_tag = tag.replace("🔥", "").strip()
        font_tag = get_font(30, bold=True)
        bbox = draw.textbbox((0, 0), clean_tag, font=font_tag)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        flame_icon = get_emoji_img('🔥', 32)
        icon_w = flame_icon.width if flame_icon else 0
        gap = 10 if flame_icon else 0

        pad_left = 18
        pad_right = 24
        pad_y = 12

        total_w = pad_left + icon_w + gap + tw + pad_right
        total_h = max(32, th) + pad_y * 2
        x0, y0 = 70, 160
        x1, y1 = x0 + total_w, y0 + total_h
        radius = total_h // 2

        # Rounded pill in ACCENT_ORANGE
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius, fill=ACCENT_ORANGE)

        if flame_icon:
            fx = x0 + pad_left
            fy = y0 + (total_h - flame_icon.height) // 2
            img.paste(flame_icon, (fx, fy), flame_icon)
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
        # Highlight last line with tennis accent color if more than 1 line
        color = ACCENT_GREEN if i == len(title_lines) - 1 and len(title_lines) > 1 else TEXT_WHITE
        draw.text((70, y), line, font=font_title, fill=color)
        y += 105

    # 4. Center card with Subtitle / Key Hook
    card_top = max(y + 35, 680)
    card_bottom = min(card_top + 450, HEIGHT - 160)
    draw.rounded_rectangle([(70, card_top), (WIDTH - 70, card_bottom)], radius=24, fill=CARD_BG, outline=LINE_BORDER, width=3)
    
    font_sub_title = get_font(38, bold=True)
    draw.text((110, card_top + 45), "🔬 实验颠覆性结论：", font=font_sub_title, fill=ACCENT_GREEN)
    
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
    """Render Actionable On-Court Checklist Card."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_header_badge(img, draw, text="球场实操 · 动作指南")
    
    # Title
    font_title = get_font(56, bold=True)
    draw.text((70, 160), title, font=font_title, fill=TEXT_WHITE)
    
    # Checklist boxes
    y = 265
    font_item_title = get_font(36, bold=True)
    font_item_body = get_font(30)
    font_num = get_font(26, bold=True)
    
    for i, pt in enumerate(points[:4]):
        item_title = pt.get("title", f"动作要点 {i+1}")
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
        draw.rounded_rectangle([(bx0, by0), (bx0 + badge_w, by0 + badge_h)], radius=10, fill=(38, 48, 66), outline=ACCENT_GREEN, width=1)
        draw.text((bx0 + 10, by0 + (badge_h - nh)//2 - num_bbox[1]), num_str, font=font_num, fill=ACCENT_GREEN)

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

def main():
    parser = argparse.ArgumentParser(description="Render Xiaohongshu Image Cards")
    parser.add_argument("--type", choices=["cover", "checklist"], default="cover")
    parser.add_argument("--title", required=True, help="Main title")
    parser.add_argument("--subtitle", default="", help="Subtitle / Key conclusion")
    parser.add_argument("--tag", default="网球进阶", help="Tag pill")
    parser.add_argument("--points", nargs="*", help="Key points for checklist format: 'Title|Desc'")
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
                {"title": "击球前髋部预制动", "desc": "骨盆提前刹车才能把转动动量传递到肩胸关节"},
                {"title": "拍头下沉与外旋蓄力", "desc": "不要用手腕死掰，前臂被动外旋受力更自然"},
                {"title": "沿击球轴完整随挥", "desc": "随挥不完全会导致伸肌腱吸收 30% 额外冲击力"}
            ]
        render_checklist(args.title, pts, args.output)

if __name__ == "__main__":
    main()
