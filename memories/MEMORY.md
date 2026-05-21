User preferences and installed skills:
1. Prefers CLI-based installation and management of AI skills
2. Requested installation of two GitHub-hosted AI skills: qiaomu-anything-to-notebooklm (multi-source content to NotebookLM) and last30days-skill (30-day topic research across social platforms)
3. last30days-skill has been successfully installed, configured, and synced across local Claude/agent/codex environments with proper file permissions
§
小爱音箱Home Assistant控制规则：1. 让小爱说/播报：调用text.set_value到text.xiaomi_l05b_ee79_play_text，data.value为播报内容；2. 让小爱执行指令：调用text.set_value到text.xiaomi_l05b_ee79_execute_text_directive，data.value为中文指令；3. 调整音量到X%：调用media_player.volume_set到media_player.xiaomi_l05b_ee79_play_control，volume_level=X/100
§
notebooklm-to-brainvault: process_video.py脚本封装完整流程。source add后必须sleep（SOURCE_ADD_SLEEP默认1200s/20min）。generate支持16次重试（15/30/60min步进）后改ask。部分视频NotebookLM无法处理（"no data"），直接跳过。多个视频用共享notebook（--notebook）。已移除本地字幕fallback。
§
用户Home Assistant中连接的小米小爱音箱设备名为hermes1，对应实体ID：1. 播放控制实体：media_player.xiaomi_l05b_ee79_play_control；2. 文本播报实体：text.xiaomi_l05b_ee79_play_text；3. 指令执行实体：text.xiaomi_l05b_ee79_execute_text_directive；4. 唤醒按钮实体：button.xiaomi_l05b_ee79_wake_up。该设备频繁出现连接不稳定问题，会在`idle`和`unavailable`状态之间反复切换，用户会收到Home Assistant的状态变更告警，且设备通常会自动恢复连接。
§
youtubd重构：subscribe.json（本地订阅+权重1-5）、history.json（map<videoId,info>）、todolist.txt（累计追加）、cron_task.json。manage.py新增：gethistory/listplaylists/importplaylist（--output参数）/flush（--todolist参数）。flush改为逐条调process_video.py（notebooklm-to-brainvault技能的独立脚本），不再硬编码notebooklm subprocess。cron每日10点加权随机抽N个。强制覆盖：新进程kill旧flush/cron。NotebookLM必须串行禁用delegate_task，耐心等待用sleep+process wait（15/30/60min步进最多16次，之后ask）。等待时不处理N+1。字幕抓不到直接失败不用description。
§
mcp-chrome bridge singleton MCP server: edited `dist/mcp/mcp-server.js` to always create fresh Server (removed singleton guard). After bridge restart, extension may not auto-connect — user clicks Connect in popup (sends CONNECT_NATIVE, not just ENSURE_NATIVE). CDP port 9222 bound but returns 404 on all endpoints. Prefer Hermes native MCP client via mcp_servers in config.yaml over manual curl.