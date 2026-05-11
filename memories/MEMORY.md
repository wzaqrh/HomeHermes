User preferences and installed skills:
1. Prefers CLI-based installation and management of AI skills
2. Requested installation of two GitHub-hosted AI skills: qiaomu-anything-to-notebooklm (multi-source content to NotebookLM) and last30days-skill (30-day topic research across social platforms)
3. last30days-skill has been successfully installed, configured, and synced across local Claude/agent/codex environments with proper file permissions
§
小爱音箱Home Assistant控制规则：1. 让小爱说/播报：调用text.set_value到text.xiaomi_l05b_ee79_play_text，data.value为播报内容；2. 让小爱执行指令：调用text.set_value到text.xiaomi_l05b_ee79_execute_text_directive，data.value为中文指令；3. 调整音量到X%：调用media_player.volume_set到media_player.xiaomi_l05b_ee79_play_control，volume_level=X/100
§
已创建xiaoai-ha本地技能，用于通过Home Assistant控制小爱音箱，技能路径为~/.hermes/skills/smart-home/xiaoai-ha/，支持播报文本、执行指令、调整音量、唤醒设备、播放音乐等功能，已完成测试验证。
§
notebooklm-to-brainvault 技能已创建：YouTube/网页 → NotebookLM → brain-vault。生成失败时 fallback 到本地字幕+AI总结 CLI。仅生成阶段有配额限制。
§
用户当前网络访问（东方财富/百度）均失败，无法获取实时行情数据，后续查询A股相关股票需提前确认网络状态
§
用户Home Assistant中连接的小米小爱音箱设备名为hermes1，对应实体ID：1. 播放控制实体：media_player.xiaomi_l05b_ee79_play_control；2. 文本播报实体：text.xiaomi_l05b_ee79_play_text；3. 指令执行实体：text.xiaomi_l05b_ee79_execute_text_directive；4. 唤醒按钮实体：button.xiaomi_l05b_ee79_wake_up。该设备频繁出现连接不稳定问题，会在`idle`和`unavailable`状态之间反复切换，用户会收到Home Assistant的状态变更告警，且设备通常会自动恢复连接。
§
youtubd 技能已完善：manage.py（add/remove/fetch/new/mark/loadlist/stats）、database.json（分类+历史订阅）、todolist.txt（纯URL供loadlist导入）。已关注：读书-魏知超、经济-宏观洞察/BossEconomics、科技-最佳拍档。用户要求：字幕抓不到就直接失败，不用description替代。
§
用户偏好与环境：1. 偏好用curl/bash命令测试MCP工具；2. 已配置Chrome MCP服务器地址为http://127.0.0.1:12306/mcp（streamable http方式）；3. 运行Linux环境，已安装node/npm和全局包mcp-chrome-bridge；4. 已安装Chrome MCP插件并完成基础配置。
§
mcp-chrome技能使用注意事项：1. 无需手动执行mcp-chrome-bridge start，服务器已随插件自动运行；2. 验证服务器状态：访问http://127.0.0.1:12306/ping返回pong即正常；3. 常见错误Invalid MCP request or session.：需重新连接Chrome插件（断开后再点击连接）；4. 正确请求头为Content-Type: application/json，工具方法名如get_windows_and_tabs、chrome_navigate；5. 错误命令：mcp-chrome-bridge start 官方不存在