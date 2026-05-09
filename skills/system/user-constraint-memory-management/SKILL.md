---
name: user-constraint-memory-management
description: 标准化管理用户约束和记忆条目的流程，用于处理用户的约束变更请求
version: "0.1.0"
---

# 用户约束与记忆管理流程

## 适用场景
当用户提出变更现有约束、添加新规则或修改之前的要求时，使用此流程来更新系统记忆。

## 标准步骤

1. **识别约束变更类型**：确定用户是要添加新约束、移除现有约束还是修改现有约束
2. **定位目标记忆条目**：使用memory工具的搜索功能（或直接匹配已知条目）找到需要更新的记忆内容
3. **执行记忆更新操作**：
   - 使用`memory(action='replace', target='user', old_text='旧内容', content='新内容')`来替换现有条目
   - 使用`memory(action='remove', target='user', old_text='旧内容')`来删除条目
   - 使用`memory(action='add', target='user', content='新内容')`来添加新条目
4. **验证更新结果**：检查memory返回的结果，确认条目已成功更新
5. **反馈用户**：向用户确认约束已成功变更

## 常见示例

### 移除现有约束
```bash
# 移除"不许安装任何Python插件"约束
memory(action='replace', target='user', old_text='用户偏好与约束：1. 禁止安装任何Python插件，仅允许写入~/feushu目录；2. 偏好CLI工具，股票分析优先使用tradingagents-runner技能；3. 要求严格匹配分析参数：ticker、analysts、depth、provider、language、date；4. 多次要求分析600276.SS（恒瑞医药）和300760.SZ（迈瑞医疗），偏好浅分析+基本面+技术面维度。', content='用户偏好与约束：1. 偏好CLI工具，股票分析优先使用tradingagents-runner技能；2. 要求严格匹配分析参数：ticker、analysts、depth、provider、language、date；3. 多次要求分析600276.SS（恒瑞医药）和300760.SZ（迈瑞医疗），偏好浅分析+基本面+技术面维度。')
```

### 替换特定约束条目
```bash
# 替换用户的分析需求
memory(action='replace', target='user', old_text='用户要求分析600276.SS的基本面，需要写入tradingagents目录或安装Python插件', content='用户要求分析600276.SS的基本面，无额外限制')
```

## 注意事项
- 匹配旧文本时需要使用唯一且完整的子字符串，避免匹配到多个条目
- 当替换用户偏好总结时，需要保留所有未变更的内容，仅修改需要调整的部分
- 如果不确定旧文本的准确内容，可以先列出所有用户记忆条目再进行匹配