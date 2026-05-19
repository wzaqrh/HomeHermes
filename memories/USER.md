用户偏好：1. 安装Agent Reach时跳过了小宇宙播客转文字、雪球股票行情、LinkedIn职业社交渠道；2. 抖音搜索因安全限制暂时无法访问，需代理或等待后重试；3. 已完成Twitter/X、小红书、微博渠道的配置，抖音MCP服务已部署但暂时受限。
§
用户已为last30days-skill配置X/Twitter认证：AUTH_TOKEN=cdec84d65e3557460c00171418de2d0ad4b5ec44，CT0=***（完整值已保存到~/.config/last30days/.env）；用户需要搜索Ferrari ADUO相关的Twitter帖子，此前搜索无结果。
§
用户要求分析600276.SS的基本面，需要写入tradingagents目录或安装Python插件
§
用户使用 Obsidian 管理知识，vault 为 ~/MyDoc/brain-vault。偏好将 YouTube 总结自动保存到 brain-vault。已创建 notebooklm-to-brainvault 技能（NotebookLM + 本地 fallback 双路径）。
§
CLI power user, vault: ~/MyDoc/brain-vault (Obsidian). Pref: agent-to-agent JSON, cost-conscious (NotebookLM free > local AI), token protect ON, >10min no-transcript=skip (never description). Pipeline: youtubd→brain-vault/cron. Source skills from GitHub first.
§
用户要求：总结YouTube视频时如果抓不到字幕就直接失败，不能用视频description代替。description没有内容价值，宁可不存。
§
CLI power user, vault: ~/MyDoc/brain-vault (Obsidian). Pref: agent-to-agent (JSON), cost-conscious (NotebookLM free > local AI), token protect ON (>10min no-transcript=skip, never description). Pipeline: youtubd→summarize→brain-vault, cron, channels 1-5 weighted. PREFERS direct tool calls over manual. CRITICAL: source skills from GitHub first — never build wheels without search.
§
用户期望：遇到复杂问题时，先查阅已有的报告/记录/方案的参考资料，而不是盲目尝试各种方法。如果确实无法解决，直接报告"不会"或"做不到"，不要浪费步骤在错误的路径上反复试探。