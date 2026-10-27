#!/usr/bin/env python3
"""
英超积分榜抓取脚本
- 若配置了 FOOTBALL_DATA_API_KEY 环境变量，从 football-data.org 拉取真实数据
- 否则使用内置示意数据，保证页面不会空白
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


# 内置示意数据（仅在未配置 API key 时使用）
# 真实部署时建议在 GitHub Secrets 里配 FOOTBALL_DATA_API_KEY
FALLBACK_STANDINGS = {
    "competition": "Premier League",
    "season": "2026/27",
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "note": "示意数据 — 在 GitHub Secrets 配置 FOOTBALL_DATA_API_KEY 后自动拉取真实积分榜",
    "table": [
        {"position": 1, "team": "Arsenal", "played": 10, "won": 7, "draw": 2, "lost": 1, "gf": 22, "ga": 10, "gd": 12, "points": 23},
        {"position": 2, "team": "Liverpool", "played": 10, "won": 7, "draw": 1, "lost": 2, "gf": 20, "ga": 11, "gd": 9, "points": 22},
        {"position": 3, "team": "Man City", "played": 10, "won": 6, "draw": 3, "lost": 1, "gf": 19, "ga": 10, "gd": 9, "points": 21},
        {"position": 4, "team": "Chelsea", "played": 10, "won": 6, "draw": 2, "lost": 2, "gf": 18, "ga": 12, "gd": 6, "points": 20},
        {"position": 5, "team": "Newcastle", "played": 10, "won": 5, "draw": 3, "lost": 2, "gf": 17, "ga": 12, "gd": 5, "points": 18},
        {"position": 6, "team": "Aston Villa", "played": 10, "won": 5, "draw": 2, "lost": 3, "gf": 16, "ga": 13, "gd": 3, "points": 17},
        {"position": 7, "team": "Tottenham Hotspur", "played": 10, "won": 4, "draw": 3, "lost": 3, "gf": 15, "ga": 14, "gd": 1, "points": 15},
        {"position": 8, "team": "Man United", "played": 10, "won": 4, "draw": 2, "lost": 4, "gf": 14, "ga": 15, "gd": -1, "points": 14},
        {"position": 9, "team": "Brighton", "played": 10, "won": 3, "draw": 4, "lost": 3, "gf": 13, "ga": 13, "gd": 0, "points": 13},
        {"position": 10, "team": "West Ham", "played": 10, "won": 3, "draw": 3, "lost": 4, "gf": 12, "ga": 14, "gd": -2, "points": 12},
    ],
}


def fetch_real_standings(api_key: str) -> dict:
    """从 football-data.org v4 拉取英超积分榜"""
    url = "https://api.football-data.org/v4/competitions/PL/standings"
    headers = {"X-Auth-Token": api_key}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    table = []
    for row in data.get("standings", [{}])[0].get("table", []):
        table.append({
            "position": row.get("position"),
            "team": row.get("team", {}).get("name", ""),
            "played": row.get("playedGames"),
            "won": row.get("won"),
            "draw": row.get("draw"),
            "lost": row.get("lost"),
            "gf": row.get("goalsFor"),
            "ga": row.get("goalsAgainst"),
            "gd": row.get("goalDifference"),
            "points": row.get("points"),
        })

    return {
        "competition": data.get("competition", {}).get("name", "Premier League"),
        "season": str(data.get("season", {}).get("startDate", ""))[:4] + "/" + str(data.get("season", {}).get("endDate", ""))[2:4],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "note": "",
        "table": table,
    }


def main():
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "standings.json"

    if api_key:
        try:
            print("[INFO] 检测到 FOOTBALL_DATA_API_KEY，拉取真实积分榜...")
            payload = fetch_real_standings(api_key)
        except Exception as e:
            print(f"[WARN] 拉取真实积分榜失败: {e}，使用兜底数据")
            payload = FALLBACK_STANDINGS
    else:
        print("[INFO] 未配置 FOOTBALL_DATA_API_KEY，使用示意数据")
        payload = FALLBACK_STANDINGS

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已写入 {out_file}，共 {len(payload['table'])} 支球队")


if __name__ == "__main__":
    main()
