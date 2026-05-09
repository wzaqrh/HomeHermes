---
name: xiaomi-ai-speaker-homeassistant-frequent-disconnect-fix
category: smart-home
description: 解决Home Assistant中小米小爱音箱频繁在idle和unavailable状态间切换的问题
---
# 小米小爱音箱Home Assistant频繁断开连接修复技能

## 触发条件
1.  Home Assistant中小米小爱音箱实体（如media_player.xiaomi_l05b_ee79_play_control）反复在`idle`和`unavailable`之间切换
2.  用户频繁收到设备状态变更告警
3.  设备多数情况下可自动恢复连接

## 临时恢复步骤
1.  **快速刷新实体**：调用`homeassistant.update_entity`服务，实体ID为`media_player.xiaomi_l05b_ee79_play_control`，通常10-30秒内恢复正常
2.  **手动唤醒设备**：调用`button.xiaomi_l05b_ee79_wake_up`实体触发设备唤醒重连

## 永久性修复方案
1.  **重启小爱音箱**：长按电源键关闭设备，等待30秒后重新插电开机，清除设备本地网络缓存
2.  **设置静态IP**：在路由器后台为小爱音箱分配固定IP地址，避免IP变动导致连接中断
3.  **重新加载小米Miio集成**：进入Home Assistant → 设置 → 设备与服务 → 小米Miio → 找到对应音箱后点击「重新加载」，清除集成缓存
4.  **配置自动恢复自动化**：创建Home Assistant自动化规则，当实体变为`unavailable`时自动执行`homeassistant.update_entity`或唤醒按钮操作

## 注意事项
1.  避免频繁调用`update_entity`服务，建议等待1-2分钟后再尝试多次操作
2.  确保小爱音箱与Home Assistant服务器处于同一Wi-Fi网络
3.  如果问题持续出现，检查小爱音箱固件版本是否为最新