# Spurs Daily · 热刺每日新闻聚合

一个静态网站，每天自动抓取托特纳姆热刺相关中英文新闻，用 GitHub Actions 定时更新，托管在 GitHub Pages 上。

## 功能

- 📰 **中英文混合新闻流**：聚合 BBC Sport、Sky Sports、Guardian、热刺官网、Google News 中文等多个来源
- 🏷️ **分类筛选**：转会 / 赛况 / 训练 / 伤病 / 评论 / 综合
- 🔍 **站内搜索**：按标题和摘要关键词过滤
- ★ **收藏功能**：重要新闻标星，存在浏览器本地
- 📊 **英超积分榜侧边栏**：实时排名（可选配置 API key 拉真实数据）
- 📡 **RSS 订阅**：输出 `feed.xml`，可订阅到 RSS 阅读器
- 📱 **响应式布局**：手机端也能看

## 部署步骤

### 1. Fork 本仓库

点击右上角 Fork，把项目复制到你自己的 GitHub 账号下。

### 2. 开启 GitHub Pages

1. 进入你仓库的 **Settings → Pages**
2. **Source** 选择 `Deploy from a branch`
3. **Branch** 选择 `main`，目录选 `/ (root)`
4. 点 **Save**

等 1 分钟，你的网站就上线了，地址是：
`https://<你的用户名>.github.io/tottenham-news-dashboard/`

### 3. 触发第一次更新

仓库刚 fork 下来时 `data/news.json` 是空的，需要手动跑一次脚本：

1. 进入仓库的 **Actions** 标签页
2. 左边选 **Daily Tottenham News**
3. 点右边 **Run workflow → Run workflow**

跑完后，`data/news.json` 和 `feed.xml` 就会生成，页面就能看到新闻了。

之后每天早上北京时间 8:00 会自动更新一次。

### 4.（可选）配置真实积分榜数据

默认积分榜是示意数据。要拉真实的英超积分榜：

1. 去 [football-data.org](https://www.football-data.org/) 注册一个免费账号
2. 拿到你的 API Token
3. 进入仓库 **Settings → Secrets and variables → Actions**
4. 新建一个 Secret：
   - Name: `FOOTBALL_DATA_API_KEY`
   - Value: 你的 Token

免费 tier 每月有 10 次请求额度，每天跑一次刚好够用。

## 本地开发

```bash
# 安装依赖
pip install feedparser requests

# 手动跑一次新闻抓取
python src/fetch_news.py

# 跑积分榜
python src/fetch_standings.py

# 生成 RSS
python src/generate_rss.py

# 用本地服务器打开页面（直接双击 index.html 也能看，但 fetch json 可能有跨域问题）
# 推荐：
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 项目结构

```
tottenham-news-dashboard/
├── .github/workflows/
│   └── daily_news.yml      # GitHub Actions 定时任务
├── src/
│   ├── fetch_news.py       # 新闻 RSS 抓取
│   ├── fetch_standings.py  # 积分榜抓取
│   └── generate_rss.py      # RSS feed 生成
├── data/
│   ├── news.json           # 新闻数据（自动生成）
│   └── standings.json       # 积分榜数据（自动生成）
├── index.html               # 主页面
├── style.css                # 样式
├── app.js                   # 前端交互
├── feed.xml                 # RSS 输出（自动生成）
└── README.md
```

## 自定义

- **加新闻源**：编辑 `src/fetch_news.py` 里的 `ENGLISH_FEEDS` 和 `CHINESE_FEEDS`
- **改更新时间**：编辑 `.github/workflows/daily_news.yml` 里的 `cron`（注意是 UTC 时间）
- **改配色**：编辑 `style.css` 顶部的 CSS 变量

## 免责声明

本项目是个人非官方项目，与托特纳姆热刺足球俱乐部无关。所有新闻版权归原媒体所有。
