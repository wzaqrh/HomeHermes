---
name: xiaoai-ha
description: 通过Home Assistant控制小米小爱音箱的技能，支持播报文本、执行指令、调整音量、唤醒设备等操作
category: smart-home
keywords: homeassistant, xiaomi, ai-speaker, automation
---

# 小爱音箱Home Assistant控制技能

## 技能用途
当用户通过自然语言指令控制小爱音箱时，自动调用Home Assistant服务执行对应操作，支持播报文本、执行指令、调整音量、唤醒设备、播放音乐等功能。

## 使用规则
### 1. 文本播报
当用户说以下任意指令时：
- "让小爱说 {内容}"
- "让音箱播报 {内容}"
- "播报 {内容}"
自动调用Home Assistant服务：
```
domain: text
service: set_value
entity_id: text.xiaomi_l05b_ee79_play_text
data:
  value: {用户指定的内容}
```

### 2. 执行小爱指令
当用户说以下任意指令时：
- "让小爱执行 {指令}"
- "让小爱帮我 {指令}"
自动调用Home Assistant服务：
```
domain: text
service: set_value
entity_id: text.xiaomi_l05b_ee79_execute_text_directive
data:
  value: {用户指定的指令}
```

### 3. 调整音箱音量
当用户说以下任意指令时：
- "把小爱音量调到 {X}%"
- "把音箱音量调到 {X}%"
自动调用Home Assistant服务：
```
domain: media_player
service: volume_set
entity_id: media_player.xiaomi_l05b_ee79_play_control
data:
  volume_level: {X} / 100
```
示例："把小爱音量调到40%" → volume_level: 0.4

### 4. 唤醒小爱音箱
当用户说"唤醒小爱"时，自动调用Home Assistant服务：
```
domain: button
service: press
entity_id: button.xiaomi_l05b_ee79_wake_up
```

### 5. 播放音乐
当用户说"播放音乐"时，优先执行以下操作：
1. 调用Home Assistant服务：
```
domain: text
service: set_value
entity_id: text.xiaomi_l05b_ee79_execute_text_directive
data:
  value: 播放音乐
```
2. 如果第一步失败，回退调用：
```
domain: button
service: press
entity_id: button.xiaomi_l05b_ee79_play_music
```

### 6. 暂停/停止播放
当用户说以下任意指令时：
- "暂停播放"
- "停止播放"
- "停止播放音乐"
自动调用Home Assistant服务：
```
domain: text
service: set_value
entity_id: text.xiaomi_l05b_ee79_execute_text_directive
data:
  value: {用户指定的停止/暂停指令}
```
或者直接调用媒体播放器服务：
```
domain: media_player
service: media_pause / media_stop
entity_id: media_player.xiaomi_l05b_ee79_play_control
```

### 7. 恢复播放
当用户说"继续播放"或"恢复播放"时，自动调用Home Assistant服务：
```
domain: media_player
service: media_play
entity_id: media_player.xiaomi_l05b_ee79_play_control
```

### 8. 特定音箱实例：hermes1
针对名为`hermes1`的小爱音箱，其对应的Home Assistant实体ID为：
- 文本播报实体：`text.xiaomi_l05b_ee79_play_text`
- 媒体控制/音量实体：`media_player.xiaomi_l05b_ee79_play_control`
- 执行指令实体：`text.xiaomi_l05b_ee79_execute_text_directive`
- 唤醒按钮实体：`button.xiaomi_l05b_ee79_wake_up`
- 播放音乐按钮实体：`button.xiaomi_l05b_ee79_play_music`

播放完成后，实体状态会自动更新为：
- 文本播报实体重置为空字符串
- 媒体控制实体进入`idle`状态

### 测试方法
可以通过以下指令测试技能是否正常工作：
1. 文本播报：`让小爱说：skill 创建成功`
2. 播放音乐：`播放音乐`
3. 停止播放：`停止播放`
4. 验证状态：确认音箱状态从`playing`切换为`idle`或`paused`，已通过实际测试验证所有指令均可正常执行

### 常见问题排查：播放控制实体反复变为`unavailable`
当小爱音箱的播放控制实体频繁从`idle`切换为`unavailable`时，可按以下步骤排查修复：
1.  **快速恢复连接**：执行Home Assistant服务`homeassistant.update_entity`刷新实体状态，通常10-30秒即可恢复。
2.  **设备端排查**：
    - 确认小爱音箱已连接到Wi-Fi网络，信号强度正常
    - 长按电源键关闭音箱，等待30秒后重新插电开机，清除设备本地网络缓存
3.  **Home Assistant集成修复**：
    - 进入`设置 > 设备与服务 > 小米Miio`，找到对应音箱实体并点击「重新加载」，清除集成缓存
4.  **永久性解决**：
    - 在路由器后台为小爱音箱分配静态IP地址，避免IP变动导致连接中断
    - 创建Home Assistant自动化规则，当实体变为`unavailable`时自动执行刷新或唤醒操作，实现自动恢复