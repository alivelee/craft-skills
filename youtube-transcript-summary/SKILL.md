---
name: "YouTube Transcript Summary"
description: "Download the transcript of a given YouTube link and summarize it. Handles tool installation, multiple fallback download methods, and produces structured summaries."
alwaysAllow: ["Bash"]
---

# YouTube Transcript Summary

When the user provides a YouTube URL (`youtube.com/watch`, `youtu.be`, `youtube.com/shorts`, `m.youtube.com`, `youtube.com/embed`, or a raw video ID), download its transcript and produce a comprehensive, structured summary in Simplified Chinese.

## Triggers

Use this skill when the user asks to:
- Summarize, resume, or extract content from a YouTube video
- Get a transcript from a YouTube link
- Document video content without rewatching it

## Step 0 — Environment Detection & Setup

Before processing, detect the execution environment to choose the correct transcript extraction strategy.

```bash
# Test 1: Can we run local Python?
python3 --version 2>/dev/null
PYTHON_AVAILABLE=$?

# Test 2: Is youtube-transcript-api installed?
python3 -c "import youtube_transcript_api" 2>/dev/null
LIB_AVAILABLE=$?
```

| Mode | Condition | Strategy |
|------|-----------|----------|
| **A — Python/CLI** | Python 3 available + library installed | `youtube-transcript-api` (full featured) |
| **B — WebFetch** | No Python OR sandboxed environment | Fetch YouTube page → extract transcript from embedded JSON |
| **C — Manual** | YouTube blocked at network level | Ask user to paste transcript text directly |

### Mode A setup (Python available, library missing)

If Python is available but `youtube-transcript-api` is not installed, install it:

```bash
pip3 install --user youtube-transcript-api
```

### Mode B setup (Sandboxed / no Python / WebFetch only)

Use `web_fetch` to extract the transcript embedded in the YouTube page HTML. YouTube embeds full caption track URLs in `ytInitialPlayerResponse` JSON inside the page source.

Steps:
1. `web_fetch` `https://www.youtube.com/watch?v=VIDEO_ID`
2. Extract `ytInitialPlayerResponse` JSON block from the HTML
3. Parse `captions.playerCaptionsTracklistRenderer.captionTracks[0].baseUrl`
4. `web_fetch` that URL to retrieve the transcript XML
5. Parse XML `<text>` elements into plain text

If the YouTube page itself is blocked, fall through to Mode C.

### Mode C setup (Network blocked)

Inform the user clearly in Simplified Chinese:

```
⚠️  当前环境无法访问 YouTube。

可选方案：
1. 在具备完整网络访问权限的 CLI 环境中运行此技能。
2. 将视频字幕文本直接粘贴到对话中。
3. 从 youtube.com/watch?v=VIDEO_ID 打开视频 → 点击“...” → “显示字幕” → 将字幕复制粘贴到这里。
```

## Progress Tracking (optional)

Throughout the workflow, display a visual progress gauge before each step, using Simplified Chinese labels:

```bash
echo "[███░░░░░░░░░░░░░░░░░] 14% - 步骤 1/7：验证链接"
echo "[██████░░░░░░░░░░░░░░] 29% - 步骤 2/7：检查可用性"
echo "[█████████░░░░░░░░░░░] 43% - 步骤 3/7：提取字幕"
echo "[████████████░░░░░░░░] 57% - 步骤 4/7：保存字幕"
echo "[███████████████░░░░░] 71% - 步骤 5/7：生成摘要"
echo "[██████████████████░░] 86% - 步骤 6/7：中英翻译"
echo "[████████████████████] 100% - 步骤 7/7：保存到 Obsidian"
```

Gauge format: 20 characters wide, `█` filled / `░` empty, include percentage and step label.

## Step 1 — Validate URL & Extract Video ID

Parse the 11-character video ID from any supported form:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- A bare `VIDEO_ID`

If the URL is invalid:

```
❌ YouTube 链接格式无效

请提供以下任一格式的有效 YouTube 链接：
- https://www.youtube.com/watch?v=VIDEO_ID
- https://youtu.be/VIDEO_ID
```

## Step 2 — Check Video & Transcript Availability

Verify the video exists and a transcript is accessible using the active mode.

**Mode A (Python):**

```python
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print(f"✅ 视频可访问：{video_id}")
    for transcript in transcript_list:
        lang_type = "[自动生成]" if transcript.is_generated else "[手动上传]"
        print(f"  - {transcript.language} ({transcript.language_code}) {lang_type}")
except TranscriptsDisabled:
    print("❌ 该视频已禁用字幕")
except NoTranscriptFound:
    print("❌ 未找到该视频的字幕")
except Exception as e:
    print(f"❌ 访问视频时出错：{e}")
```

**Mode B (WebFetch):**

Use `web_fetch` to load `https://www.youtube.com/watch?v=VIDEO_ID`. Search the HTML for `"captionTracks"` to confirm captions are available. If the page is inaccessible or no `captionTracks` key is found, fall through to Mode C.

## Step 3 — Extract the Transcript

Use the active mode to retrieve the transcript text.

### Method A: youtube-transcript-api (preferred)

```python
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "VIDEO_ID"

try:
    # Prefer English; fall back to any available language or auto-translation
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
    text = " ".join(entry["text"] for entry in transcript)
    print("✅ 字幕提取成功")
    print(f"📊 字幕长度：{len(text)} 字符")
except Exception as e:
    print(f"❌ 提取字幕时出错：{e}")
```

If English is unavailable, list available transcripts and either use the original language or its auto-generated English translation. Note the language in your summary.

### Method B: yt-dlp (fallback for auto-generated captions)

```bash
which yt-dlp >/dev/null 2>&1 || pip3 install --user yt-dlp
yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en.*,.*" \
  --sub-format vtt -o "/tmp/yt-%(id)s.%(ext)s" "VIDEO_URL"
```

Convert the downloaded `.vtt` to plain text (strip timestamps and dedupe repeated caption lines).

### Method C: Web page scrape (last resort)

Fetch the watch page HTML, extract `captionTracks` from the embedded player JSON, then fetch the base URL of the first caption track and parse the XML.

### Method D: Manual paste

If all extraction methods fail, ask the user to paste the transcript text directly and proceed to summarization.

### Transcript cleanup

- Remove `[Music]`, `[Applause]`, and similar auto-generated noise markers
- Preserve punctuation and formatting where available
- Combine segments into coherent paragraphs when it improves readability

## Step 4 — Save Transcript

Save the full transcript to the session data folder so the user can access it:

```
data/transcript_{VIDEO_ID}.txt
```

## Step 5 — Summarize

Apply the **STAR + R-I-S-E** framework to the transcript and produce a comprehensive, structured summary in Simplified Chinese.

### Summarization prompt

Use the following prompt when generating the summary. Replace `{TRANSCRIPT}` with the extracted transcript text and, when available, `{TITLE}`, `{CHANNEL}`, `{DURATION}`, `{URL}`, `{PUBLISHED}`, and `{LANGUAGE}` with the corresponding metadata.

```markdown
You are an expert content summarizer. Your task is to read the provided YouTube transcript and produce a comprehensive, well-structured Markdown summary in Simplified Chinese that captures the full substance of the video.

Apply the **STAR + R-I-S-E** framework where relevant:
- **STAR** — Situation, Task, Action, Result（用于叙事、教程、流程或故事类内容）
- **R-I-S-E** — Reasoning, Insights, Synthesis, Evaluation（用于分析、论证或教育类内容）

Instructions:
1. Be faithful to the transcript. Do not invent facts, quotes, speakers, or external context.
2. Identify the core topic, central argument, and key supporting points.
3. Preserve important examples, data, statistics, case studies, and direct quotes when they add value.
4. Explain technical terms, acronyms, and domain-specific concepts in a **概念与术语** section.
5. Extract actionable insights, practical takeaways, and recommendations in a **核心洞察** section.
6. List any books, papers, tools, links, or resources explicitly mentioned in a **提及资源** section.
7. Synthesize the overall message and implications in a **总结** section.
8. 如果字幕原文不是中文，请用简体中文输出摘要，并在开头注明原始语言。

Output format (Markdown in Simplified Chinese):
- Use the structure below, with clear headings, subheadings, bullet points, and bold labels.
- Use `###` for topic-level sections and `####` for subtopics.
- Keep the summary detailed and reference-rich rather than brief.

# [视频标题]

**频道：** [频道名称]
**时长：** [时长]
**链接：** [https://youtube.com/watch?v=VIDEO_ID]
**发布日期：** [日期，若可获取]
**字幕语言：** [原始语言，例如 英语]

---

## 📊 内容概览

[用 2-4 段话概括视频目的、核心论点与关键收获。]

---

## 📝 详细摘要

### [主题 1]
[包含示例、数据与引用的全面说明。]

#### [子主题 1.1]
[详细拆解。]

### [主题 2]
[继续深入分析。]

---

## 💡 核心洞察

- **洞察 1：** [解释及其重要性。]
- **洞察 2：** [解释及其重要性。]

---

## 📚 概念与术语

- **术语 1：** [定义及视频中的上下文。]
- **术语 2：** [定义及视频中的上下文。]

---

## 🔗 提及资源

- [资源 1 — 标题、作者、链接（若视频中有提供）]
- [资源 2 — 标题、作者、链接（若视频中有提供）]

---

## 📌 总结

[最终综合、整体评价，以及观众应记住的最重要内容。]
```

### Model execution

1. Load the full transcript text into the model context.
2. Invoke the summarization prompt above.
3. Ensure the final output follows the Markdown structure exactly and is written in Simplified Chinese.
4. If the transcript exceeds the model context window, split it into logical chunks, summarize each chunk, and merge the partial summaries into the final structure.

## Step 6 — Translate Transcript to Chinese-English Bilingual

After generating the summary, translate the full original transcript into a **Chinese-English bilingual对照文本**.

### Translation rules

1. **Preserve structure.** Keep paragraph or sentence boundaries aligned with the original transcript.
2. **Bilingual layout.** For each segment, output the original text followed immediately by its translation:
   - If the original is **English**, present **English first, then 简体中文翻译**.
   - If the original is **Chinese**, present **中文原文 first, then English translation**.
   - For other languages, present **original language first, then 简体中文 and English**.
3. **Be faithful.** Do not add, omit, or rewrite the meaning. Keep the translation natural and accurate.
4. **Preserve placeholders.** Keep timestamps, speaker labels, and formatting markers exactly as they appear in the original transcript.
5. **Save the bilingual file** to the session data folder for reference:
   ```
   data/transcript_{VIDEO_ID}_bilingual.txt
   ```

### Example bilingual format

```text
Welcome to today's lecture on machine learning.
欢迎来到今天的机器学习讲座。

Machine learning is a subset of artificial intelligence.
机器学习是人工智能的一个子集。
```

## Step 7 — Auto-Save to Obsidian Vault

Once the summary and bilingual transcript are ready, **automatically save 摘要 + 原始字幕 + 中英对照字幕** to the user's Obsidian vault. Do not ask for confirmation before writing; proceed directly after detecting or receiving the vault path.

### Detect the vault root

Check common locations in order:
- `~/Documents/Obsidian Vault`
- `~/Obsidian`
- Any folder whose name contains `Obsidian` under `~/Documents`
- If the vault cannot be auto-detected, ask the user for the absolute path once and then proceed.

### Determine the category folder

Based on the video's main topic and content, choose or create an appropriate folder. Common folders (create if missing):
- `01-Inbox/` — when the topic is unclear or mixed
- `Tech/` — programming, software, AI, hardware, engineering
- `Business/` — entrepreneurship, investing, management, marketing
- `Science/` — physics, biology, medicine, research
- `Philosophy/` — philosophy, psychology, self-improvement
- `History/` — history, biography, culture
- `Language/` — language learning, translation, linguistics
- `Life/` — lifestyle, travel, cooking, hobbies
- `Notes/` — general notes and miscellaneous

Inspect existing folders in the vault and prefer matching them by name or topic. If no clear match exists, place the note in `01-Inbox/` and optionally suggest a better folder.

### File name format

```
{Category Folder}/{YYYY-MM-DD}-{Video Title}-{VIDEO_ID}.md
```

Sanitize the file name: replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` with `-`, and trim spaces.

### Note structure

```markdown
---
date: {YYYY-MM-DD}
source: https://youtube.com/watch?v={VIDEO_ID}
channel: {CHANNEL}
duration: {DURATION}
language: {原始语言}
tags: [youtube, {category}, {auto-detected topic tags}]
---

# {视频标题}

{完整的中文摘要，遵循 STAR + R-I-S-E 结构}

---

## 🎬 原始字幕

```text
{完整原始字幕文本}
```

---

## 🌐 中英对照字幕

```text
{完整中英对照字幕文本}
```
```

### After saving

Report the saved file path to the user in Simplified Chinese:

```
✅ 已自动保存到 Obsidian vault：
{完整文件路径}

内容包含：
- 中文摘要
- 原始字幕
- 中英对照字幕
```

Suggested file names in the session data folder:
- Summary only: `summary-{VIDEO_ID}-{YYYY-MM-DD}.md`
- Summary + transcript: `summary-{VIDEO_ID}-{YYYY-MM-DD}.md`
- Transcript only: `transcript-{VIDEO_ID}-{YYYY-MM-DD}.txt`
- Bilingual transcript: `transcript-{VIDEO_ID}-{YYYY-MM-DD}-bilingual.txt`

## Long Transcripts

For transcripts longer than the model context window:
1. Split the transcript into logical chunks
2. Summarize each chunk with `call_llm`
3. Combine the partial summaries into the final structured output in Simplified Chinese

## Error Handling

| Error | Likely Cause | Action |
|-------|-------------|--------|
| Invalid YouTube URL format | URL is not a recognized pattern | 显示有效链接格式，并请用户提供正确链接 |
| Video not found or private | Video removed, private, or wrong URL | 告知用户，并请提供公开视频链接 |
| Transcripts disabled | Creator disabled transcripts | 告知用户；建议手动转录 |
| No transcript found | No auto-generated or manual transcript | 告知用户；建议更换视频或使用音频转录 |
| `youtube-transcript-api` not installed | Python dependency missing | 使用 `pip3 install --user youtube-transcript-api` 安装 |
| YouTube blocked | Sandboxed environment | 切换到模式 B（WebFetch）；如仍被阻止，切换到模式 C |
| Network error / timeout | Connectivity issue or rate-limiting | 重试一次；若仍然失败，请用户稍后再试 |
| Transcript in unexpected language | Video in a language not requested | 报告检测到的语言；继续使用可用字幕生成中文摘要 |

Never fabricate a summary without a real transcript.

## Notes

- Auto-generated transcripts lack punctuation and may contain errors — interpret sensibly.
- If the user provides multiple links, process them one at a time and summarize each separately.
- Always preserve the YAML frontmatter of this SKILL.md file.
- All user-facing output from this skill should be in Simplified Chinese.
