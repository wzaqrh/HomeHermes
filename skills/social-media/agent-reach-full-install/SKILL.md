---
name: agent-reach-full-install
category: social-media
description: 完整的Agent Reach安装和配置流程，包含环境问题处理、全渠道安装步骤
---

# Agent Reach 完整安装与配置指南

## 前置环境问题处理
如果遇到`externally-managed-environment`（PEP 668）保护错误：
1.  **使用pipx安装管理**：
    ```bash
    pip install --user pipx && python3 -m pipx ensurepath
    ```
2.  **或使用虚拟环境**：
    ```bash
    python3 -m venv ~/.agent-reach-venv
    source ~/.agent-reach-venv/bin/activate
    ```

## 基础安装
```bash
# 方式1：pipx安装（推荐）
pipx install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto

# 方式2：虚拟环境安装
python3 -m venv ~/.agent-reach-venv
source ~/.agent-reach-venv/bin/activate
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

## 全渠道安装与配置
### 1. Twitter/X
```bash
# 安装渠道
agent-reach install --env=auto --channels=twitter
# 配置Cookie（从x.com导出Header String格式）
agent-reach configure twitter-cookies "你的Cookie字符串"
```

### 2. 小红书（Xiaohongshu）
```bash
# 安装依赖
pipx install xiaohongshu-cli
# 安装渠道
agent-reach install --env=auto --channels=xiaohongshu
# 配置Cookie（从xiaohongshu.com导出）
agent-reach configure xhs-cookies "你的Cookie字符串"
```

### 3. 微博（Weibo）
```bash
# 解决网络超时问题
pipx install --pip-args='--timeout 300' git+https://github.com/Panniantong/mcp-server-weibo.git
# 配置mcporter
mcporter config add weibo --command 'mcp-server-weibo'
```

### 4. 小宇宙播客（Xiaoyuzhou）
```bash
# 安装渠道
agent-reach install --env=auto --channels=xiaoyuzhou
# 配置Groq API Key（从https://console.groq.com获取）
agent-reach configure groq-key "gsk_你的API密钥"
```

### 5. 雪球（Xueqiu）
```bash
agent-reach install --env=auto --channels=xueqiu
# 从浏览器导入Cookie
agent-reach configure --from-browser chrome
```

### 6. 抖音（Douyin）
```bash
# 安装依赖
pipx install douyin-mcp-server
# 启动服务
mkdir -p ~/.agent-reach/tools && cd ~/.agent-reach/tools
git clone https://github.com/yzfly/douyin-mcp-server.git && cd douyin-mcp-server
uv sync && uv run python run_http.py
# 配置mcporter
mcporter config add douyin http://localhost:18070/mcp
```

#### 补充步骤（适配PEP668环境与依赖问题）
如果遇到权限或依赖缺失问题：
```bash
# 使用虚拟环境安装避免PEP668冲突
python3 -m venv ~/.douyin-venv
source ~/.douyin-venv/bin/activate
cd douyin-mcp-server
pip install -e .
python -m douyin_mcp_server.server --host 127.0.0.1 --port 18070
```

### 7. LinkedIn
```bash
pipx install linkedin-scraper-mcp
# 本地登录
linkedin-scraper-mcp --login --no-headless
# 服务器登录（需VNC）
export DISPLAY=:1
linkedin-scraper-mcp --login --no-headless
# 启动服务
linkedin-scraper-mcp --transport streamable-http --port 8001
mcporter config add linkedin http://localhost:8001/mcp
```

## 验证安装
```bash
agent-reach doctor
```

## 常见问题
1.  **网络超时**：安装时添加`--timeout 300`参数延长超时时间
2.  **权限问题**：优先使用pipx或虚拟环境安装，避免`sudo`操作
3.  **渠道未生效**：运行`agent-reach doctor`检查状态，重新执行对应渠道安装命令
4.  **平台安全限制（451错误）**：访问抖音/小红书等平台时遇到`SecurityCompromiseError`，提示匿名访问被阻止：
    - 等待系统自动解除限制（通常几小时后恢复）
    - 配置代理绕过限制：`agent-reach configure proxy http://用户名:密码@代理IP:端口`
5.  **备选搜索方案**：当官方MCP服务无法使用时，可以使用Jina Reader或Exa Search进行搜索：
    - Jina Reader：`curl -s "https://r.jina.ai/https://www.平台.com/search/关键词"`
    - Exa Search（支持微信公众号、网页等）：`mcporter call exa.web_search_exa query="你的搜索词" numResults=10`
    - 微信公众号搜索示例：`mcporter call exa.web_search_exa query="Opus4.7 微信公众号文章" numResults=1`
6.  **抖音MCP服务依赖缺失**：启动时提示`ModuleNotFoundError: No module named 'ffmpeg'`：
    - 安装ffmpeg：`sudo apt install ffmpeg`（Debian/Ubuntu）或`brew install ffmpeg`（macOS）