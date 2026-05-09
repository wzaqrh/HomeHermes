---
name: scrapling-xiaohongshu-recursive-scrape
description: 使用Scrapling工具递归爬取小红书内容，支持绕过IP风控和登录限制
author: Hermes Agent
created: 2026-05-08
dependencies: scrapling, Chrome with remote debugging
---

## 技能说明
使用Scrapling工具递归爬取小红书内容，支持绕过IP风控和登录限制

## 前置条件
1.  已安装Scrapling工具
2.  已登录小红书账号的Chrome浏览器（或使用远程调试端口连接已登录会话）
3.  可选：使用代理IP绕过IP限制

## 使用流程
1.  **启动Chrome远程调试会话**
   ```bash
   google-chrome --remote-debugging-port=9222 --user-data-dir="~/.chrome/xhs-session"
   ```
2.  **手动登录小红书账号**
   在打开的Chrome浏览器中访问https://www.xiaohongshu.com并完成登录
3.  **运行递归爬取脚本**
   ```bash
   python3 ~/scrapling-xhs-recursive.py
   ```

## 关键参数与优化
- 使用`remote_debugging_port=9222`参数连接已登录的浏览器会话
- 使用`wait_until="networkidle"`等待页面完全加载
- 递归深度默认设置为5层，可通过修改`MAX_DEPTH`参数调整
- 随机选择链接避免触发反爬机制
- 自动去重已访问的URL

## 常见问题
1.  **IP限制问题**：切换代理网络或使用住宅IP
2.  **页面内容为空**：确保已正确登录小红书账号
3.  **反爬拦截**：增加请求间隔时间，使用更真实的浏览器指纹

## 示例输出
```
Found 23 initial links
Starting with random link: https://www.xiaohongshu.com/explore/xxx
[0] Scraping: https://www.xiaohongshu.com/explore/xxx
Saved: xhs-depth-0-xxx.html -> https://www.xiaohongshu.com/explore/xxx
Page length: 12345
Found 15 sub links, choosing random: https://www.xiaohongshu.com/explore/yyy
[1] Scraping: https://www.xiaohongshu.com/explore/yyy
...
```