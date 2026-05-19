User preferences and installed skills:
1. Prefers CLI-based installation and management of AI skills
2. Requested installation of two GitHub-hosted AI skills: qiaomu-anything-to-notebooklm (multi-source content to NotebookLM) and last30days-skill (30-day topic research across social platforms)
3. last30days-skill has been successfully installed, configured, and synced across local Claude/agent/codex environments with proper file permissions
§
小爱音箱Home Assistant控制规则：1. 让小爱说/播报：调用text.set_value到text.xiaomi_l05b_ee79_play_text，data.value为播报内容；2. 让小爱执行指令：调用text.set_value到text.xiaomi_l05b_ee79_execute_text_directive，data.value为中文指令；3. 调整音量到X%：调用media_player.volume_set到media_player.xiaomi_l05b_ee79_play_control，volume_level=X/100
§
已创建xiaoai-ha本地技能，用于通过Home Assistant控制小爱音箱，技能路径为~/.hermes/skills/smart-home/xiaoai-ha/，支持播报文本、执行指令、调整音量、唤醒设备、播放音乐等功能，已完成测试验证。
§
notebooklm-to-brainvault 技能：YouTube/网页 → NotebookLM → brain-vault。token保护模式ON（.env配置），>10min视频NotebookLM失败则跳过。NotebookLM CLI需用-n显式指定notebook（use上下文会漂移）。generate report瞬态失败可重试。本地字幕fallback仅对≤10min视频执行。
§
用户Home Assistant中连接的小米小爱音箱设备名为hermes1，对应实体ID：1. 播放控制实体：media_player.xiaomi_l05b_ee79_play_control；2. 文本播报实体：text.xiaomi_l05b_ee79_play_text；3. 指令执行实体：text.xiaomi_l05b_ee79_execute_text_directive；4. 唤醒按钮实体：button.xiaomi_l05b_ee79_wake_up。该设备频繁出现连接不稳定问题，会在`idle`和`unavailable`状态之间反复切换，用户会收到Home Assistant的状态变更告警，且设备通常会自动恢复连接。
§
youtubd重构：subscribe.json（订阅+权重1-5、fetch_limit=100）、history.json（map<videoId,info>）、todolist.txt（累计追加）、cron_task.json（up_list=[] 或[{name,weight}]）。manage.py命令：subscribe/unsubscribe/weight/fetch/new/mark/cron/loadlist/flush/stats。cron每日10点加权随机抽N个。强制覆盖：新进程kill旧flush/cron。NotebookLM必须串行禁用delegate_task，耐心等待用sleep+process wait（15/30/60min步进最多16次，之后ask）。等待时不处理N+1。已关注13+频道。字幕抓不到直接失败不用description。
§
mcp-chrome bridge singleton MCP server: edited `dist/mcp/mcp-server.js` to always create fresh Server (removed singleton guard). After bridge restart, extension may not auto-connect — user clicks Connect in popup (sends CONNECT_NATIVE, not just ENSURE_NATIVE). CDP port 9222 bound but returns 404 on all endpoints. Prefer Hermes native MCP client via mcp_servers in config.yaml over manual curl.