用户使用 Obsidian 管理知识，vault 为 ~/MyDoc/brain-vault。偏好将 YouTube 总结自动保存到 brain-vault。已创建 notebooklm-to-brainvault 技能（NotebookLM + 本地 fallback 双路径）。
§
用户要求：总结YouTube视频时如果抓不到字幕就直接失败，不能用视频description代替。description没有内容价值，宁可不存。
§
用户期望：遇到复杂问题时，先查阅已有的报告/记录/方案的参考资料，而不是盲目尝试各种方法。如果确实无法解决，直接报告"不会"或"做不到"，不要浪费步骤在错误的路径上反复试探。
§
CLI power user. Wants honest "做不到" over random workarounds when things fail. Prefers testing proper existing commands before ad-hoc code. Prefers agent-tool execution over Python subprocess for multi-step workflows (NotebookLM). Wants skill features with proper --output/--todolist params. clear naming: "本地订阅频道" != YouTube "订阅". Follow skill docs precisely, don't guess. process_video.py needs sleep(2) after add_source before generate. Shared notebook pattern for batch NotebookLM: create once → add source → sleep → generate → wait → download → delete source → repeat.
§
用户偏好：希望遇到问题时报"做不到"而不是在错误路径上浪费时间。重视CLI命令的参数设计（--output/--todolist等应有默认值且可配置）。接受长时间后台任务。偏好可配置化（.env文件）而非硬编码。