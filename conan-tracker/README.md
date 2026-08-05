# 柯南追番工具

基于仓库自动更新数据的柯南追番 Web 应用（Vue 3 + Vite）。

## 功能

- B站拆分版 / 日本原版集数切换浏览
- 标记已看集数（localStorage 本地保存）
- 点击集数查看详细登场人物信息
- 主线剧情筛选
- 人物搜索筛选
- 分页浏览（每页条数可调、页码跳转）

## 目录结构

```
├── src/
│   ├── App.vue              # 主应用（全部功能）
│   ├── main.js
│   └── style.css
├── public/data/             # 静态数据（构建时由脚本生成）
│   ├── bilibili.json        # B站拆分版剧集
│   ├── original.json        # 日本原版剧集
│   └── characters.json      # 角色索引
├── scripts/build_static_data.py  # 从 ../data 生成静态数据
└── server.py                # 可选本地 API 后端（仅开发模式）
```

## 本地开发

```bash
npm install
python3 server.py    # 可选：启动 API 后端（开发模式用）
npm run dev
```

## 生产构建

纯静态，无需后端：

```bash
npm run build       # 自动生成静态数据并打包到 dist/
npm run preview     # 预览构建产物
```

部署到 GitHub Pages 见仓库根 README。
