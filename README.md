# 名侦探柯南 B站剧集数据自动更新

自动从 B站 与 conanpedia（柯南百科）抓取《名侦探柯南》剧集数据，生成 `data/conan_episodes.json`（按 B站拆分版编号）与 `data/conan_tv_original.json`（按日本原版编号）。

## 数据内容

### data/conan_episodes.json

按 B站剧集编号（拆分版编号）组织，每集包含：

| 字段 | 说明 |
|------|------|
| `bilibili_episode` | B站剧集编号（拆分版编号，如 "400"；特别篇为 "SP"） |
| `name` | 剧集名称 |
| `link` | B站观看链接 |
| `pub_date` | B站上线日期 |
| `characters` | 登场角色列表（`name` 角色名、`category` 常驻/案件/其他/黑影君、`status` 出场情况、`voice_actor` 声优） |
| `character_source` | 角色数据来源（conanpedia 页面链接） |

### data/conan_tv_original.json

按日本原版放送编号组织，每个原版 TV 编号一条记录（合并页如 TV100-101 会展开为多条），包含：

| 字段 | 说明 |
|------|------|
| `tv_episode` | 原版 TV 编号（如 "100"） |
| `tv_range` | 页面原始编号范围（如 "100-101"） |
| `split_range` | 对应的拆分版编号范围 |
| `bilibili_episodes` | 对应的 B站编号列表（一个原版集可能对应多个拆分版，如 TV219 → 235-238） |
| `name` | 剧集名称 |
| `characters` | 登场角色列表 |
| `character_source` | conanpedia 页面链接 |

## 编号说明

B站使用**拆分版编号**（版权编号），与日本原版编号存在偏差。conanpedia 每个剧集页面标注了「集数 xxx（拆分版 yyy）」，脚本据此精确映射。

例如：日本 TV369 = B站第 400 集 = 《幸运儿疑案》。

## 目录结构

```
├── data/
│   ├── conan_bilibili_base.json   # B站剧集基础数据
│   ├── conan_episodes.json        # 按 B站编号的最终合并数据
│   └── conan_tv_original.json     # 按原版编号的数据
├── scripts/
│   ├── fetch_bilibili.py          # 抓取 B站剧集列表
│   ├── fetch_characters.py        # 抓取 conanpedia 角色数据
│   ├── merge_update.py            # 合并生成 B站编号 JSON
│   └── build_original.py          # 生成原版编号 JSON
└── .github/workflows/auto_update.yml  # 定时自动更新
```

## 自动更新

GitHub Actions 每天 UTC 01:00（北京时间 09:00）自动运行：

1. 从 B站 PGC API 拉取最新剧集列表
2. 增量抓取 conanpedia 新增的剧集页面
3. 合并角色数据到 `conan_episodes.json`
4. 生成原版编号数据 `conan_tv_original.json`
5. 如有变化自动提交推送

可在 Actions 页面手动触发 `workflow_dispatch`。

### 保活机制

GitHub 会暂停连续 60 天无任何活动的仓库的 scheduled workflow。本工作流在数据无变化时也会每日更新 `.keepalive` 时间戳并提交一次心跳，确保仓库持续活跃，定时任务不会被暂停。`concurrency` 组防止推送触发形成递归堆积。

## 本地运行

```bash
pip install -r requirements.txt
python scripts/fetch_bilibili.py
python scripts/fetch_characters.py
python scripts/merge_update.py
python scripts/build_original.py
```

## 追番工具网站（conan-tracker）

`conan-tracker/` 是基于上述数据构建的柯南追番工具 Web 应用（Vue 3 + Vite），支持：

- B站拆分版 / 日本原版集数切换浏览
- 标记已看集数（localStorage 本地保存）
- 点击集数查看详细登场人物信息
- 主线剧情筛选
- 人物搜索筛选

### 本地开发

```bash
cd conan-tracker
npm install
npm run dev        # 前端开发服务器（默认代理 /api 到 Python 后端）
python3 server.py  # 可选：本地 API 后端（开发模式需要）
```

### 生产构建（纯静态，无需后端）

前端构建时通过 `scripts/build_static_data.py` 把 `data/` 下的 JSON 转换为静态数据，直接由前端读取，无需 Python 后端：

```bash
cd conan-tracker
npm run build       # 生成 dist/，含静态数据
npm run preview     # 本地预览构建产物
```

### 部署到 GitHub Pages

仓库已配置 `/.github/workflows/deploy_pages.yml`，推送 `main` 分支后自动构建并部署。首次部署前需在仓库 Settings → Pages 中，将 **Source** 设为 **GitHub Actions**。

访问地址：`https://<用户名>.github.io/<仓库名>/`

数据更新 workflow 也会在抓取新剧集后自动重建前端静态数据并提交，站点随之更新。

## 数据来源

- B站剧集信息：`https://api.bilibili.com/pgc/view/web/season?season_id=33378`
- 角色数据：`https://www.conanpedia.com/`（柯南百科）

## 已知限制

- conanpedia 对较新剧集的覆盖存在滞后，最新若干集可能暂无角色数据（`characters` 为 `null`）。
- 3 个 B站 SP 特别篇（无编号）暂无 conanpedia 页面，角色数据为空。
