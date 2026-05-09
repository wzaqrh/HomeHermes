---
name: last30days-xiaohongshu-setup
version: "1.0.0"
description: "配置last30days技能以支持小红书（Xiaohongshu）内容搜索"
argument-hint: 'last30days-xiaohongshu-setup'
allowed-tools: Bash, Read, Write, terminal
homepage: https://github.com/mvanhorn/last30days-skill
repository: https://github.com/mvanhorn/last30days-skill
author: hermes-agent
license: MIT
user-invocable: true
metadata:
  hermes:
    emoji: "📰"
    tags:
      - research
      - xiaohongshu
      - social-media
      - setup
    requires:
      env:
        - XIAOHONGSHU_API_BASE
      bins:
        - python3.12+
        - docker
    primaryEnv: XIAOHONGSHU_API_BASE
    files:
      - "scripts/*"
    homepage: https://github.com/mvanhorn/last30days-skill
---

# last30days 小红书集成配置技能

## 概述
last30days技能已经内置小红书（Xiaohongshu）内容搜索支持，但需要额外部署`xiaohongshu-mcp`服务才能正常工作。本技能记录完整的配置流程和故障排查方法。

## 前置条件
1. 已成功安装并配置`last30days`技能
2. 系统已安装Docker（推荐）或可以使用浏览器插件
3. 拥有小红书账号（可选，但推荐登录以获取更好的搜索结果）

## 部署xiaohongshu-mcp服务
有两种主流部署方式：

### 方式1：Docker部署（推荐，完整功能）
1. **克隆项目仓库**
   ```bash
   git clone https://github.com/xpzouying/xiaohongshu-mcp.git ~/xiaohongshu-mcp
   ```

2. **创建数据目录**
   ```bash
   mkdir -p ~/xiaohongshu-mcp/data
   ```

3. **下载Docker配置文件**
   ```bash
   cd ~/xiaohongshu-mcp && wget https://raw.githubusercontent.com/xpzouying/xiaohongshu-mcp/main/docker/docker-compose.yml
   ```

4. **启动服务**
   ```bash
   cd ~/xiaohongshu-mcp && sudo docker compose up -d
   ```
   *注意：需要sudo权限以访问Docker守护进程，输入系统密码完成授权*

5. **验证服务状态**
   ```bash
   curl http://localhost:18060/health
   ```
   正常响应：`{"success": true}`

### 方式2：浏览器插件部署（简单快速）
适合不希望配置Docker环境的用户：
1. 访问[x-mcp插件仓库](https://github.com/xpzouying/x-mcp)
2. 下载并安装对应浏览器（Chrome/Edge）的插件
3. 插件会自动在本地启动服务，默认地址为`http://localhost:18060`

## 配置last30days技能
1. **编辑环境配置文件**
   ```bash
   nano ~/.config/last30days/.env
   ```

2. **添加小红书API配置**
   在文件末尾添加：
   ```
   XIAOHONGSHU_API_BASE=http://localhost:18060
   ```

3. **保存并退出编辑器**

## 测试小红书搜索
运行以下命令验证配置是否成功：
```bash
cd ~/.hermes/skills/research/last30days && python3.12 scripts/last30days.py "gpt5.5" --emit=compact --lookback-days=30 --search=xiaohongshu
```

## 常见故障排查
1. **Docker权限错误**
   - 错误信息：`permission denied while trying to connect to the docker API`
   - 解决方案：使用sudo命令，或配置当前用户的Docker用户组

2. **服务无法启动**
   - 查看日志：`cd ~/xiaohongshu-mcp && docker compose logs -f`
   - 检查端口是否被占用：`ss -tlnp | grep :18060`

3. **搜索无结果**
   - 检查小红书登录状态：`curl http://localhost:18060/api/v1/login/status`
   - 重新登录：使用项目提供的登录工具完成账号授权

4. **IP风控限制**
   - 小红书会触发IP安全限制，建议使用代理服务器或VPN
   - 参考`social-platform-content-scraping-and-ip-mitigation`技能处理IP限制问题

## 使用示例
完成配置后，你可以使用以下命令搜索小红书内容：
```bash
last30days "GPT-5.5 最新动态" --search=xiaohongshu --lookback-days=7
```

该技能会自动调用last30days的内置小红书搜索功能，返回指定时间范围内的舆情数据、用户评论和互动统计。