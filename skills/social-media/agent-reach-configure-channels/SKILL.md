---
name: agent-reach-configure-channels
description: 配置Agent Reach的可选社交媒体渠道，解决安装和配置过程中的常见问题
---

## 技能概述
配置Agent Reach的可选社交媒体渠道，解决安装和配置过程中的常见问题

## 适用场景
当需要为Agent Reach安装和配置以下可选渠道时：
- Twitter/X 推文
- 小红书笔记
- 微博动态与热搜
- 小宇宙播客转文字
- 抖音短视频
- LinkedIn 职业社交

## 前置条件
1.  已经安装基础版Agent Reach
2.  系统已经安装pipx和python3虚拟环境
3.  有对应平台的账号Cookie或API密钥

## 安装步骤

### 1. 处理PEP 668保护机制
如果遇到`externally-managed-environment`错误，使用以下方式安装：
```bash
# 使用pipx安装（推荐）
pipx install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto

# 或者使用虚拟环境
python3 -m venv ~/.agent-reach-venv
source ~/.agent-reach-venv/bin/activate
pip install https://github.com/Panniantong/agent-reach/archive/main.zip
agent-reach install --env=auto
```

### 2. 安装单个渠道示例（以抖音为例）
```bash
# 安装依赖
pipx install --pip-args='--timeout 300' douyin-mcp-server

# 启动服务
nohup python3 -m douyin_mcp_server.server --transport streamable-http --host 127.0.0.1 --port 18070 > ~/.agent-reach/douyin-mcp-server.log 2>&1 &

# 注册到mcporter
mcporter config add douyin http://localhost:18070/mcp
```

## 常见问题解决

### 问题1：安装超时
```bash
# 增加pip安装超时时间
pipx install --pip-args='--timeout 300' 包名
```

### 问题2：模块未找到错误
```bash
# 手动克隆仓库并在虚拟环境中安装
git clone https://github.com/yzfly/douyin-mcp-server.git /tmp/douyin-mcp-server
cd /tmp/douyin-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -e .
python -m douyin_mcp_server.server --host 127.0.0.1 --port 18070
```

### 问题3：抖音访问被安全限制
```bash
# 配置代理
agent-reach configure proxy http://用户名:密码@代理IP:端口

# 或者等待系统自动解封（通常几分钟到几小时）
```

### 问题4：Cookie字符串转义
当终端无法正确解析包含特殊字符的Cookie字符串时，使用单引号包裹：
```bash
agent-reach configure twitter-cookies 'auth_token=xxx;gt=xxx;...'
```

## 渠道配置命令汇总

| 渠道名称 | 配置命令 |
|---------|---------|
| Twitter | agent-reach configure twitter-cookies "Cookie字符串" |
| 小红书 | agent-reach configure xhs-cookies "Cookie字符串" |
| 微博 | agent-reach install --env=auto --channels=weibo |
| 抖音 | 参考上面的抖音安装步骤 |
| LinkedIn | 参考官方文档的LinkedIn配置步骤 |
| 小宇宙 | agent-reach install --env=auto --channels=xiaoyuzhou |