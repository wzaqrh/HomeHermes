# database.json Schema Reference

Location: `~/.hermes/skills/media/youtubd/database.json`

## Structure

```json
{
  "categories": {
    "<分类名>": {
      "channels": {
        "<channel_id (UC...)>": {
          "name": "频道显示名",
          "url": "频道链接",
          "added": "YYYY-MM-DD"
        }
      }
    }
  },
  "history": [
    {
      "id": "视频11位ID",
      "title": "视频标题",
      "url": "https://www.youtube.com/watch?v=ID",
      "channel_name": "频道名",
      "channel_id": "UC...",
      "category": "分类名（对应 categories 中的key）",
      "fetched_at": "YYYY-MM-DD",
      "duration": 1234,
      "view_count": 50000,
      "upload_date": "20260315",
      "processed": true,
      "note": "处理备注"
    }
  ]
}
```

## history 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | YouTube 视频ID (11字符) |
| title | string | 标题 |
| url | string | 完整URL |
| channel_name | string | 频道显示名 |
| channel_id | string | UCxxx 格式 |
| category | string | 来自 categories 的key |
| fetched_at | string | 拉取日期 YYYY-MM-DD |
| duration | int | 时长（秒） |
| view_count | int | 播放量 |
| upload_date | string | 上传日期 YYYYMMDD（可能为空） |
| processed | bool | 是否已处理 |
| note | string | 处理备注 |

## 数据来源标识

- `category: "导入"` — 通过 loadlist 从外部 txt 文件导入
- 其他 category — 通过 fetch 从订阅频道拉取
