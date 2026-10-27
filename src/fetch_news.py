#!/usr/bin/env python3
"""
Tottenham Hotspur 每日新闻聚合脚本
从多个中英文 RSS 源抓取热刺相关新闻，去重、分类后输出到 data/news.json
"""

import json
import re
import hashlib
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    import feedparser
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser


# ---------- 新闻源配置 ----------
# 优先用 Google News RSS（动态搜索，最可靠）
# 英文源
ENGLISH_FEEDS = [
    {
        # Google News 英文：近 30 天 Tottenham Hotspur
        "url": "https://news.google.com/rss/search?q=Tottenham+Hotspur+when:30d&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News EN",
        "lang": "en",
    },
    {
        # Google News 英文：Spurs transfer
        "url": "https://news.google.com/rss/search?q=Tottenham+Spurs+transfer+when:30d&hl=en-US&gl=US&ceid=US:en",
        "source": "Transfer News",
        "lang": "en",
    },
    {
        # BBC Sport Tottenham
        "url": "https://feeds.bbci.co.uk/sport/football/teams/tottenhamhotspur/rss.xml",
        "source": "BBC Sport",
        "lang": "en",
    },
    {
        # Guardian Tottenham
        "url": "https://www.theguardian.com/football/tottenham-hotspur/rss",
        "source": "The Guardian",
        "lang": "en",
    },
]

# 中文源
CHINESE_FEEDS = [
    {
        # Google News 中文：近 30 天 热刺
        "url": "https://news.google.com/rss/search?q=%E7%83%AD%E5%88%BA+when:30d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source": "Google News 中文",
        "lang": "zh",
    },
    {
        # Google News 中文：热刺转会
        "url": "https://news.google.com/rss/search?q=%E7%83%AD%E5%88%BA+%E8%BD%AC%E4%BC%9A+when:30d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source": "转会动态",
        "lang": "zh",
    },
    {
        # Google News 中文：孙兴慜
        "url": "https://news.google.com/rss/search?q=%E5%AD%99%E5%85%B4%E6%85%92+when:30d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "source": "孙兴慜",
        "lang": "zh",
    },
]

ALL_FEEDS = ENGLISH_FEEDS + CHINESE_FEEDS


# ---------- 分类关键词 ----------
CATEGORY_KEYWORDS = {
    "transfer": [
        "transfer", "sign", "bid", "agree", "deal", "loan", "buy", "sell",
        "转会", "签约", "报价", "加盟", "离队", "引进",
    ],
    "match": [
        "vs", "v ", "match", "fixture", "result", "win", "lose", "draw",
        "score", "goal", "premier league", "carabao", "fa cup",
        "对阵", "比赛", "战报", "比分", "进球", "英超", "足总杯", "联赛杯",
    ],
    "training": [
        "training", "train", "session", "pre-season", "preseason",
        "训练", "集训", "备战",
    ],
    "injury": [
        "injury", "injured", "surgery", "recover", "fitness", "doubt",
        "伤病", "受伤", "恢复", "缺阵",
    ],
    "opinion": [
        "opinion", "analysis", "column", "editorial", "review",
        "评论", "分析", "观点", "前瞻",
    ],
}


def classify(title: str, summary: str) -> str:
    """根据标题和摘要关键词判断分类"""
    text = (title + " " + summary).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return cat
    return "general"


def parse_time(entry) -> str:
    """统一输出 ISO 格式时间字符串"""
    # 优先用 published_parsed / updated_parsed
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            dt = datetime(*t[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    # 兜底：直接解析 published 字符串
    pub = entry.get("published", "")
    if pub:
        try:
            dt = parsedate_to_datetime(pub)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def make_id(title: str, link: str) -> str:
    """生成新闻唯一 ID 用于去重"""
    raw = (title + "|" + link).encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:12]


def clean_html(text: str) -> str:
    """去除 HTML 标签"""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_one_feed(feed_cfg: dict) -> list:
    """抓取单个 RSS 源，返回新闻列表"""
    items = []
    try:
        d = feedparser.parse(feed_cfg["url"])
        for entry in d.entries[:30]:  # 每个源最多取 30 条
            title = clean_html(getattr(entry, "title", ""))
            link = getattr(entry, "link", "")
            summary = clean_html(getattr(entry, "summary", getattr(entry, "description", "")))
            if not title or not link:
                continue
            items.append({
                "id": make_id(title, link),
                "title": title,
                "link": link,
                "summary": summary[:300],  # 摘要截断
                "published": parse_time(entry),
                "source": feed_cfg["source"],
                "lang": feed_cfg["lang"],
                "category": classify(title, summary),
                "starred": False,  # 前端 localStorage 里存用户标星，这里默认 False
            })
    except Exception as e:
        print(f"[WARN] 抓取 {feed_cfg['source']} 失败: {e}")
    return items


def deduplicate(news_list: list) -> list:
    """按标题相似度去重，保留最新的一条"""
    seen = {}
    for item in news_list:
        # 用标题前 40 字符做粗去重
        key = item["title"][:40].lower().strip()
        if key not in seen:
            seen[key] = item
        else:
            # 如果已有，比较时间保留更新的
            old = seen[key]
            if item["published"] > old["published"]:
                seen[key] = item
    return list(seen.values())


def main():
    all_news = []
    for feed in ALL_FEEDS:
        print(f"[INFO] 抓取 {feed['source']} ...")
        all_news.extend(fetch_one_feed(feed))

    print(f"[INFO] 原始抓取 {len(all_news)} 条")

    all_news = deduplicate(all_news)
    print(f"[INFO] 去重后 {len(all_news)} 条")

    # 按时间倒序
    all_news.sort(key=lambda x: x["published"], reverse=True)

    # 只保留最近 30 天
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent = []
    for item in all_news:
        try:
            pub = datetime.fromisoformat(item["published"])
            if pub >= cutoff:
                recent.append(item)
        except Exception:
            recent.append(item)  # 时间解析失败就保留

    # 最多保留 100 条
    recent = recent[:100]

    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "news.json"

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(recent),
        "items": recent,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已写入 {out_file}，共 {len(recent)} 条新闻")


if __name__ == "__main__":
    main()
