// ===== Spurs Daily 前端交互逻辑 =====

let allNews = [];
let currentCategory = "all";
let currentKeyword = "";
let starredIds = new Set(JSON.parse(localStorage.getItem("spurs_starred") || "[]"));

const CATEGORY_LABELS = {
  all: "全部",
  transfer: "转会",
  match: "赛况",
  training: "训练",
  injury: "伤病",
  opinion: "评论",
  general: "综合",
  starred: "我的收藏",
};

// ---------- 工具函数 ----------
function timeAgo(isoStr) {
  const now = new Date();
  const t = new Date(isoStr);
  const diff = (now - t) / 1000; // 秒

  if (diff < 60) return "刚刚";
  if (diff < 3600) return Math.floor(diff / 60) + " 分钟前";
  if (diff < 86400) return Math.floor(diff / 3600) + " 小时前";
  if (diff < 86400 * 7) return Math.floor(diff / 86400) + " 天前";
  return t.toLocaleDateString("zh-CN");
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// ---------- 数据加载 ----------
async function loadData() {
  try {
    const [newsRes, standingsRes] = await Promise.all([
      fetch("data/news.json"),
      fetch("data/standings.json"),
    ]);
    const newsData = await newsRes.json();
    const standingsData = await standingsRes.json();

    allNews = newsData.items || [];
    document.getElementById("updatedAt").textContent = timeAgo(newsData.updated_at);
    renderStandings(standingsData);
    renderNews();
  } catch (e) {
    console.error("加载数据失败:", e);
    document.getElementById("statusBar").textContent =
      "数据加载失败 — 请确认 data/news.json 已生成";
  }
}

// ---------- 渲染新闻 ----------
function getFilteredNews() {
  return allNews.filter((item) => {
    // 分类过滤
    if (currentCategory === "starred") {
      if (!starredIds.has(item.id)) return false;
    } else if (currentCategory !== "all") {
      if (item.category !== currentCategory) return false;
    }
    // 关键词过滤
    if (currentKeyword) {
      const kw = currentKeyword.toLowerCase();
      const haystack = (item.title + " " + item.summary).toLowerCase();
      if (!haystack.includes(kw)) return false;
    }
    return true;
  });
}

function renderNews() {
  const list = getFilteredNews();
  const container = document.getElementById("newsList");
  const empty = document.getElementById("emptyState");
  const statusBar = document.getElementById("statusBar");

  statusBar.textContent = `共 ${list.length} 条新闻 · 更新于 ${document.getElementById("updatedAt").textContent}`;

  if (list.length === 0) {
    container.innerHTML = "";
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  container.innerHTML = list
    .map((item) => {
      const starClass = starredIds.has(item.id) ? "star-btn starred" : "star-btn";
      return `
      <article class="news-card">
        <div class="news-meta">
          <span class="news-source">${escapeHtml(item.source)}</span>
          <span class="lang-tag ${item.lang}">${item.lang === "zh" ? "中" : "EN"}</span>
          <span class="cat-tag">${CATEGORY_LABELS[item.category] || "综合"}</span>
          <span class="news-time">${timeAgo(item.published)}</span>
        </div>
        <h3 class="news-title">
          <a href="${escapeHtml(item.link)}" target="_blank" rel="noopener">
            ${escapeHtml(item.title)}
          </a>
        </h3>
        ${item.summary ? `<p class="news-summary">${escapeHtml(item.summary)}</p>` : ""}
        <div class="news-actions">
          <button class="${starClass}" data-id="${item.id}" title="收藏">★</button>
          <a class="read-more" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">阅读原文 →</a>
        </div>
      </article>
    `;
    })
    .join("");

  // 绑定标星按钮
  container.querySelectorAll(".star-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      if (starredIds.has(id)) {
        starredIds.delete(id);
      } else {
        starredIds.add(id);
      }
      localStorage.setItem("spurs_starred", JSON.stringify([...starredIds]));
      renderNews();
    });
  });
}

// ---------- 渲染积分榜 ----------
function renderStandings(data) {
  const container = document.getElementById("standingsTable");
  const note = document.getElementById("standingsNote");

  if (data.note) {
    note.textContent = data.note;
  }

  const rows = data.table || [];
  container.innerHTML = `
    <div class="standings-row head">
      <span>#</span><span>球队</span><span>场</span><span>胜</span><span>分</span><span>净</span>
    </div>
    ${rows
      .map((r) => {
        const isSpurs = /tottenham|spurs|热刺/i.test(r.team);
        return `
        <div class="standings-row ${isSpurs ? "spurs" : ""}">
          <span>${r.position}</span>
          <span>${escapeHtml(r.team)}</span>
          <span>${r.played}</span>
          <span>${r.won}</span>
          <span>${r.points}</span>
          <span>${r.gd > 0 ? "+" + r.gd : r.gd}</span>
        </div>
      `;
      })
      .join("")}
  `;
}

// ---------- 事件绑定 ----------
function bindEvents() {
  // 分类按钮
  document.querySelectorAll(".cat-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".cat-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentCategory = btn.dataset.cat;
      renderNews();
    });
  });

  // 搜索框
  document.getElementById("searchBox").addEventListener("input", (e) => {
    currentKeyword = e.target.value.trim();
    renderNews();
  });
}

// ---------- 启动 ----------
document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadData();
});
