# ⚡ 快速更新指南

这是日常开发和更新的快速参考指南。完整的部署说明请查看 [deployment.md](./deployment.md)。

## 🔄 更新代码到生产环境

### 步骤 1：修改代码
在本地进行你的开发工作。

### 步骤 2：提交到 GitHub
```bash
# 添加所有修改的文件
git add .

# 提交更改（使用有意义的提交信息）
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

### 步骤 3：自动部署
- 推送到 GitHub 后，**Vercel** 和 **Railway** 会自动检测到更改
- 大约 **1-2 分钟**后，新版本会自动部署到生产环境
- 你可以在相应的平台上查看部署状态

## 📝 Git 提交规范

使用语义化的提交信息：

```bash
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建/工具变更
```

示例：
```bash
git commit -m "feat: 添加用户头像上传功能"
git commit -m "fix: 修复 API 响应超时问题"
git commit -m "docs: 更新部署说明"
```

## 🚀 快速命令

### 查看状态
```bash
git status
```

### 查看提交历史
```bash
git log --oneline
```

### 撤销本地更改
```bash
# 撤销单个文件的更改
git checkout -- 文件名

# 撤销所有更改
git reset --hard HEAD
```

### 查看部署日志
- **Vercel**: 访问 [vercel.com/dashboard](https://vercel.com/dashboard) → 选择项目 → Deployments
- **Railway**: 访问 [railway.app/dashboard](https://railway.app/dashboard) → 选择项目 → Deployments

## 🔐 环境变量管理

### Vercel (前端)
1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择你的项目
3. 进入 Settings → Environment Variables
4. 添加或修改变量：`VITE_API_BASE_URL`

### Railway (后端)
1. 访问 [Railway Dashboard](https://railway.app/dashboard)
2. 选择你的项目
3. 进入 Variables 选项卡
4. 添加或修改变量：
   - `OPENROUTER_API_KEY`
   - `ALLOWED_ORIGINS`
   - 其他配置

## 🐛 常见问题

### 推送失败
```bash
# 如果推送失败，先拉取最新代码
git pull origin main

# 然后再推送
git push
```

### 部署失败
1. 查看部署日志找到错误原因
2. 修复问题后重新提交
3. 或者手动触发重新部署

### CORS 错误
确保 Railway 的 `ALLOWED_ORIGINS` 包含你的 Vercel 域名。

## 📞 获取帮助

- 📖 完整部署指南：[deployment.md](./deployment.md)
- 🔧 Vercel 文档：[vercel.com/docs](https://vercel.com/docs)
- 🚂 Railway 文档：[docs.railway.app](https://docs.railway.app)

---

**提示**：每次推送代码到 `main` 分支都会触发自动部署。如果不想触发部署，可以创建其他分支进行开发。
