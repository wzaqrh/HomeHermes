#!/usr/bin/env python3
"""
NotebookLM → Brain-Vault 自动处理脚本

根据 SKILL.md 实现完整流程：
  创建 notebook → 添加源 → 生成报告（含耐心等待重试）→ 下载 → 清理
  失败时按 token 保护规则决定是否 fallback 到本地字幕

用法:
  python3 scripts/process_video.py <video_url> [--notebook <id>] [--force-local]

选项:
  --notebook <id>   使用已有 notebook（不新建），默认每视频新建
  --force-local     跳过 NotebookLM，直接走本地字幕 fallback
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VAULT_DIR = Path.home() / "MyDoc" / "brain-vault"
ENV_PATH = SKILL_DIR / "assets" / ".env"

# ─── 配置 ────────────────────────────────────

# 读取 .env
TOKEN_PROTECTION = True
TOKEN_THRESHOLD = 600  # 10 分钟
SOURCE_ADD_SLEEP = 300  # 添加源后等待 5 分钟
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k == "TOKEN_PROTECTION":
                    TOKEN_PROTECTION = v.lower() == "true"
                elif k == "TOKEN_PROTECTION_THRESHOLD":
                    TOKEN_THRESHOLD = int(v)
                elif k == "SOURCE_ADD_SLEEP":
                    SOURCE_ADD_SLEEP = int(v)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def extract_vid(text):
    text = text.strip()
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/|live/|watch\?v=)([a-zA-Z0-9_-]{11})', text)
    if m:
        return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', text):
        return text
    return None


def run(cmd, timeout=60):
    """运行 shell 命令，返回 (stdout, stderr, returncode)"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"TIMEOUT after {timeout}s", -1


def get_video_meta(video_url):
    """通过 yt-dlp 获取视频元数据"""
    r = subprocess.run(
        ["yt-dlp", "--dump-json", video_url],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip())
    except:
        return None


def get_duration(meta):
    """获取视频时长（秒）"""
    return meta.get("duration", 0) if meta else 0


def make_filename(video_id, meta):
    """生成 brain-vault 文件名"""
    channel = meta.get("channel", "unknown") if meta else "unknown"
    title = meta.get("title", video_id) if meta else video_id
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:40]
    return f"{channel}_{safe_title}_总结.md".replace(" ", "_")


# ─── NotebookLM 操作 ─────────────────────────

def nb_create(name):
    """创建 Notebook，返回 notebook_id"""
    log(f"📓 创建 notebook: {name}")
    out, err, code = run(["notebooklm", "create", name], timeout=30)
    if code != 0:
        log(f"  ❌ create 失败: {err[:200]}")
        return None
    for line in out.split("\n"):
        if "Created notebook:" in line:
            nb_id = line.split(":")[1].strip().split()[0]
            log(f"  ✅ {nb_id}")
            return nb_id
    log(f"  ⚠️  未找到 notebook ID，尝试从输出解析")
    log(f"  输出: {out[:200]}")
    return None


def nb_add_source(video_url, nb_id):
    """添加视频源到 notebook"""
    log(f"  📎 添加源")
    out, err, code = run(["notebooklm", "source", "add", video_url, "-n", nb_id], timeout=30)
    if code != 0 or "Added source" not in out:
        log(f"  ❌ 添加源失败: {err[:200]}")
        return False
    log(f"  ✅ 源已添加")
    return True


def nb_generate(nb_id):
    """生成报告，返回 (成功?, artifact_id)"""
    log(f"  🏗️  生成报告...")
    out, err, code = run(["notebooklm", "generate", "report", "-n", nb_id], timeout=300)
    combined = out + err

    if "completed" in combined.lower() or "briefing document" in combined.lower():
        # 提取 artifact_id
        aid = ""
        for line in out.split("\n"):
            if "artifact wait" in line or "completed" in line:
                for p in line.strip().split():
                    if "-" in p and len(p) > 20:
                        aid = p
                        break
        if not aid:
            out2, _, _ = run(["notebooklm", "artifact", "list", "-n", nb_id], timeout=30)
            for line in out2.split("\n"):
                if "briefing-doc" in line or "report" in line.lower():
                    aid = line.strip().split()[0]
                    break
        if aid:
            log(f"  ✅ 生成完成 (artifact: {aid[:16]}...)")
            return True, aid
        else:
            log(f"  ⚠️  生成完成但未找到 artifact_id")
            return False, None

    if "quota" in combined.lower() or "rate limited" in combined.lower():
        log(f"  ⏳ 配额限制")
        return False, "QUOTA"

    log(f"  ⚠️  生成失败: {combined[:200]}")
    return False, None


def nb_wait_artifact(aid, nb_id, timeout=300):
    """等待 artifact 完成"""
    out, err, code = run(["notebooklm", "artifact", "wait", aid, "-n", nb_id], timeout=timeout)
    return code == 0


def nb_download(filepath, nb_id):
    """下载报告到文件"""
    out, err, code = run(["notebooklm", "download", "report", str(filepath), "-n", nb_id], timeout=30)
    if code == 0 and filepath.exists() and filepath.stat().st_size > 100:
        log(f"  ✅ 已下载: {filepath.name}")
        return True
    log(f"  ❌ 下载失败: {err[:200]}")
    return False


def nb_ask(nb_id, question="请从视频内容生成结构化中文摘要，含核心观点、关键论述和金句摘录。"):
    """使用 ask 作为 fallback"""
    log(f"  🔄 改用 ask...")
    out, err, code = run(["notebooklm", "ask", question, "-n", nb_id], timeout=120)
    if out.strip():
        return out
    return None


def nb_delete(nb_id):
    """删除 notebook"""
    run(["notebooklm", "delete", "-n", nb_id, "-y"], timeout=15)


# ─── 本地字幕 Fallback ───────────────────────

def local_transcript_fallback(video_url, video_id, meta, output_path):
    """尝试本地字幕转录 + AI 总结"""
    duration = get_duration(meta)
    log(f"  📝 尝试本地字幕 fallback")

    # Token 保护检查
    if TOKEN_PROTECTION and duration > TOKEN_THRESHOLD:
        log(f"  ⛔ token保护: {duration//60}min > {TOKEN_THRESHOLD//60}min，跳过")
        return False

    # 获取字幕
    try:
        r = subprocess.run(
            ["yt-dlp", "--write-auto-sub", "--sub-lang", "zh-Hans,en",
             "--skip-download", "-o", f"/tmp/nb_fallback_{video_id}", video_url],
            capture_output=True, text=True, timeout=60
        )
        # 找字幕文件
        import glob
        subs = glob.glob(f"/tmp/nb_fallback_{video_id}*.vtt") + \
               glob.glob(f"/tmp/nb_fallback_{video_id}*.srt") + \
               glob.glob(f"/tmp/nb_fallback_{video_id}*.ass")
        if not subs:
            log(f"  ❌ 无可用字幕")
            return False

        # 简单提取字幕文本
        transcript = ""
        with open(subs[0]) as f:
            text = f.read()
            # 去除时间戳等 VTT 格式
            text = re.sub(r'^\d{2}:\d{2}.*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            transcript = text.strip()

        if not transcript:
            log(f"  ❌ 字幕内容为空")
            return False

        # 用本地 AI 总结（用 notebooklm ask 替代本地 LLM）
        # 创建一个临时 notebook 来总结字幕
        nb_name = f"local-{video_id}"
        nb_id = nb_create(nb_name)
        if not nb_id:
            log(f"  ❌ 无法创建 notebook 做本地总结")
            return False

        # 把字幕文本写入临时文件并添加为源
        tmp_file = f"/tmp/nb_transcript_{video_id}.txt"
        with open(tmp_file, "w") as f:
            f.write(transcript)

        out, err, code = run(["notebooklm", "source", "add", tmp_file, "-n", nb_id], timeout=30)
        if code != 0 or "Added source" not in out:
            log(f"  ❌ 添加字幕源失败")
            nb_delete(nb_id)
            return False

        # 用 ask 总结
        result = nb_ask(nb_id)
        if result:
            with open(output_path, "w") as f:
                f.write(result)
            log(f"  ✅ 本地 fallback 完成 -> {output_path.name}")
            nb_delete(nb_id)
            return True

        nb_delete(nb_id)
        return False

    except Exception as e:
        log(f"  ❌ fallback 出错: {e}")
        return False


# ─── 主流程 ──────────────────────────────────

def process_video(video_url, shared_nb_id=None, force_local=False):
    """处理单个视频的完整流程"""
    video_id = extract_vid(video_url)
    if not video_id:
        log(f"❌ 无效的视频 URL: {video_url}")
        return False

    meta = get_video_meta(video_url)
    duration = get_duration(meta)
    duration_min = duration // 60
    title = meta.get("title", video_id) if meta else video_id
    channel = meta.get("channel", "unknown") if meta else "unknown"

    log(f"\n▶ [{video_id}] {title[:50]}")
    log(f"   频道: {channel}  |  时长: {duration_min}min")

    output_path = VAULT_DIR / make_filename(video_id, meta)
    if output_path.exists() and output_path.stat().st_size > 100:
        log(f"  ⏭ 已存在，跳过")
        return True

    # 检查 youtubd history.json 是否已处理过
    youtubd_history = SKILL_DIR.parent / "media" / "youtubd" / "history.json"
    if youtubd_history.exists():
        try:
            with open(youtubd_history) as f:
                hist = json.load(f)
            if video_id in hist and hist[video_id].get("processed"):
                log(f"  ⏭ history.json 中已标记为 processed，跳过")
                return True
        except:
            pass

    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    # 强制走本地
    if force_local:
        return local_transcript_fallback(video_url, video_id, meta, output_path)

    # ─── NotebookLM 主路径 ───
    using_shared = False
    if shared_nb_id:
        nb_id = shared_nb_id
        using_shared = True
        log(f"  📓 使用共享 notebook: {nb_id}")
    else:
        nb_id = nb_create(f"nb-{video_id}")
        if not nb_id:
            log(f"  ⚠️  创建 notebook 失败，尝试本地 fallback")
            return local_transcript_fallback(video_url, video_id, meta, output_path)

    # 添加源
    if not nb_add_source(video_url, nb_id):
        if not using_shared:
            nb_delete(nb_id)
        return local_transcript_fallback(video_url, video_id, meta, output_path)

    # 等待 NotebookLM 处理源，否则 generate 可能失败
    sleep_sec = SOURCE_ADD_SLEEP
    if sleep_sec >= 60:
        log(f"  ⏳ 等待 {sleep_sec//60} 分钟让 NotebookLM 充分处理源...")
    else:
        log(f"  ⏳ 等待 {sleep_sec} 秒让 NotebookLM 处理源...")
    time.sleep(sleep_sec)

    # 生成报告（耐心等待模式）
    generated = False
    for attempt in range(1, 17):
        success, aid = nb_generate(nb_id)
        if success and aid:
            # 等待完成并下载
            if nb_wait_artifact(aid, nb_id):
                if nb_download(output_path, nb_id):
                    generated = True
                    break
            else:
                log(f"  ⚠️  artifact wait 超时")

        elif aid == "QUOTA":
            # 配额限制，按步进等待
            wait_times = {1: 900, 2: 1800}  # 15min, 30min
            wait = wait_times.get(attempt, 3600)  # 之后每次 60min
            log(f"  ⏳ 配额限制，等待 {wait//60}min...")
            time.sleep(wait)
        else:
            log(f"  ⚠️  失败，10秒后重试...")
            time.sleep(10)

    if not generated:
        # 改用 ask
        log(f"  🔄 generate 用满16次，改用 ask...")
        result = nb_ask(nb_id)
        if result:
            with open(output_path, "w") as f:
                f.write(result)
            log(f"  ✅ ask -> {output_path.name}")
            generated = True
        else:
            log(f"  ❌ ask 也失败，尝试本地 fallback")
            generated = local_transcript_fallback(video_url, video_id, meta, output_path)

    if not using_shared:
        nb_delete(nb_id)

    return generated


# ─── 入口 ────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NotebookLM → Brain-Vault 视频处理")
    parser.add_argument("url", help="YouTube 视频 URL 或 video ID")
    parser.add_argument("--notebook", help="使用已有 notebook（不新建）")
    parser.add_argument("--force-local", action="store_true", help="强制走本地字幕 fallback")
    args = parser.parse_args()

    success = process_video(args.url, shared_nb_id=args.notebook, force_local=args.force_local)
    sys.exit(0 if success else 1)
