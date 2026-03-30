# 🚀 Infinite Canvas 部署指南

本指南将帮助你将 Infinite Canvas 项目部署到云端并实现持续更新。

## 📋 部署前准备

### 已完成 ✅
- [x] 创建 .gitignore 文件
- [x] 初始化 Git 仓库
- [x] 提交初始代码

### 待完成 📝
- [ ] 在 GitHub 创建远程仓库
- [ ] 推送代码到 GitHub
- [ ] 部署后端到 Railway
- [ ] 部署前端到 Vercel
- [ ] 配置环境变量和 CORS

---

## 第一步：在 GitHub 创建仓库

### 1. 访问 GitHub
1. 打开 [GitHub](https://github.com)
2. 点击右上角的 "+" → "New repository"

### 2. 填写仓库信息
- **Repository name**: `infinite-canvas`
- **Description**: `Visual AI canvas studio with React Flow and FastAPI`
- **Visibility**: Private（私有）或 Public（公开）
- **不要勾选** "Add a README file"
- **不要勾选** "Add .gitignore"

### 3. 创建仓库
点击 "Create repository" 按钮

### 4. 关联本地仓库
创建完成后，GitHub 会显示一个快速设置页面。复制你的仓库 URL（类似 `https://github.com/你的用户名/infinite-canvas.git`）

然后在本地执行：
```bash
# 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/infinite-canvas.git

# 推送代码到 GitHub
git branch -M main
git push -u origin main
```

---

## 第二步：部署后端到 Railway

### 1. 注册 Railway
1. 访问 [Railway.app](https://railway.app)
2. 点击 "Login" 并使用 GitHub 账号登录
3. 授权 Railway 访问你的 GitHub 仓库

### 2. 创建新项目
1. 登录后点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 找到并选择 `infinite-canvas` 仓库
4. 点击 "Import"

### 3. 配置后端
Railway 会自动检测项目，但我们需要手动配置：

#### 3.1 添加服务配置
点击项目中的 "New Service" → 选择 "Empty Service"，然后：

**Root Directory**: `backend`

**Build Command**:
```bash
pip install poetry && poetry install
```

**Start Command**:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 3.2 设置环境变量
在 Railway 项目的 "Variables" 选项卡中添加以下环境变量：

```bash
# 必需的环境变量
OPENROUTER_API_KEY=你的OpenRouter_API密钥
APP_ENV=production
DEFAULT_PROVIDER=openrouter

# CORS 设置（稍后填写 Vercel 前端 URL）
ALLOWED_ORIGINS=https://你的前端域名.vercel.app
```

### 4. 部署
1. 点击 "Deploy" 按钮
2. 等待部署完成（约 2-3 分钟）
3. 部署成功后，你会看到一个 URL，类似 `https://your-app.railway.app`
4. **复制这个 URL**，后面会用到

### 5. 验证后端部署
访问 `https://your-app.railway.app/docs`，你应该看到 FastAPI 的文档页面。

---

## 第三步：部署前端到 Vercel

### 1. 注册 Vercel
1. 访问 [Vercel](https://vercel.com)
2. 点击 "Sign Up" 并使用 GitHub 账号登录
3. 授权 Vercel 访问你的 GitHub 仓库

### 2. 导入项目
1. 点击 "Add New" → "Project"
2. 找到并选择 `infinite-canvas` 仓库
3. 点击 "Import"

### 3. 配置前端
在 Vercel 的项目配置页面：

#### 3.1 构建设置
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

#### 3.2 设置环境变量
在 "Environment Variables" 部分添加：

```bash
# 后端 API 地址（使用 Railway 提供的 URL）
VITE_API_BASE_URL=https://your-app.railway.app
```

### 4. 部署
1. 点击 "Deploy" 按钮
2. 等待部署完成（约 1-2 分钟）
3. 部署成功后，你会看到一个 URL，类似 `https://your-app.vercel.app`

### 5. 更新 CORS 设置
现在你有了前端 URL，需要回到 Railway 更新 CORS 设置：

1. 打开 Railway 项目
2. 进入 "Variables" 选项卡
3. 修改 `ALLOWED_ORIGINS` 为：
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
4. Railway 会自动重新部署

---

## 第四步：测试部署

### 1. 访问前端
打开浏览器访问你的 Vercel 前端 URL

### 2. 测试功能
- [ ] 页面正常加载
- [ ] 可以创建/编辑节点
- [ ] 文件上传功能正常
- [ ] AI 生成功能正常（需要有效的 API 密钥）

### 3. 检查控制台
按 F12 打开浏览器开发者工具，检查是否有错误信息。

---

## 🔄 持续更新工作流

### 日常开发流程

#### 1. 本地开发
```bash
# 在项目根目录
cd frontend
npm run dev

# 在另一个终端
cd backend
poetry run uvicorn app.main:app --reload
```

#### 2. 提交代码
```bash
# 添加修改的文件
git add .

# 提交更改（使用有意义的提交信息）
git commit -m "feat: 添加新功能"
# 或
git commit -m "fix: 修复 bug"
# 或
git commit -m "docs: 更新文档"

# 推送到 GitHub
git push
```

#### 3. 自动部署
- 推送到 GitHub 后，Vercel 和 Railway 会自动检测到更改
- 大约 1-2 分钟后，新版本会自动部署到生产环境

### Git 提交规范

使用语义化的提交信息：

```bash
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建/工具变更
```

### 分支管理（可选）

如果你想要更复杂的工作流：

```bash
# 创建功能分支
git checkout -b feature/新功能名称

# 开发完成后合并到 main
git checkout main
git merge feature/新功能名称
git push
```

---

## 🔧 环境变量说明

### 后端环境变量（Railway）

```bash
# API 密钥
OPENROUTER_API_KEY=你的密钥
OPENAI_API_KEY=可选的 OpenAI 密钥

# 应用配置
APP_ENV=production
DEFAULT_PROVIDER=openrouter

# CORS 配置
ALLOWED_ORIGINS=https://your-app.vercel.app

# 文件上传限制
UPLOAD_MAX_MB=20
```

### 前端环境变量（Vercel）

```bash
# 后端 API 地址
VITE_API_BASE_URL=https://your-app.railway.app
```

---

## 💰 成本预估

| 服务 | 免费额度 | 预计月费 |
|------|---------|---------|
| Vercel | 100GB 带宽/月 | ¥0（免费） |
| Railway | $5 免费额度/月 | ¥0-¥30（超出后） |
| GitHub | 私有仓库 | ¥0（免费） |
| **总计** | | **¥0-¥30/月** |

---

## 🐛 常见问题

### 1. CORS 错误
**问题**: 前端无法访问后端 API

**解决**: 
- 确保 Railway 的 `ALLOWED_ORIGINS` 包含你的 Vercel 域名
- 等待 Railway 重新部署完成

### 2. API 密钥无效
**问题**: AI 生成功能不工作

**解决**:
- 检查 Railway 环境变量中的 `OPENROUTER_API_KEY`
- 确保 API 密钥有效且有足够的额度

### 3. 部署失败
**问题**: Railway 或 Vercel 部署失败

**解决**:
- 查看部署日志
- 检查构建命令是否正确
- 确保所有依赖都在 package.json 或 pyproject.toml 中

### 4. 文件上传失败
**问题**: 上传文件时出错

**解决**:
- 检查文件大小是否超过限制（默认 20MB）
- 确保 Railway 有足够的存储空间

---

## 📞 获取帮助

如果遇到问题：
1. 查看 Railway 和 Vercel 的部署日志
2. 检查浏览器控制台的错误信息
3. 访问 [FastAPI 文档](https://fastapi.tiangolo.com/)
4. 访问 [Vite 文档](https://vitejs.dev/)

---

## 🎉 完成！

恭喜你完成了项目部署！现在你可以：
- 访问你的在线应用
- 持续开发和更新
- 与他人分享你的项目

记住：每次推送到 GitHub，代码会自动部署到生产环境。🚀
