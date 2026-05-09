---
name: bilibili-video-summary
description: "快速总结B站视频内容的完整流程，包含元数据提取、核心内容分析和结果保存。"
---

# B站视频内容总结技能

## 适用场景
需要快速提取、总结B站任意视频的核心内容、互动数据，并生成标准markdown总结文件的场景。

## 完整执行流程

### 1. 导航到目标视频页面
使用`browser_navigate`工具访问B站视频URL，格式如：`https://www.bilibili.com/video/BVxxxxxx/`

### 2. 提取基础元数据
通过`browser_console`执行JS脚本提取视频基础信息，示例脚本：
```javascript
(() => {
  const title = document.querySelector('h1.video-title')?.innerText || document.querySelector('.title-article')?.innerText || '未找到标题';
  const desc = document.querySelector('#v_desc')?.innerText || document.querySelector('.intro')?.innerText || document.querySelector('.video-desc')?.innerText || '未找到简介';
  const playCount = document.querySelector('.view-text')?.innerText || document.querySelector('.view-count')?.innerText || '未找到播放量';
  const dmCount = document.querySelector('.dm-text')?.innerText || document.querySelector('.dm-count')?.innerText || '未找到弹幕数';
  const pubDate = document.querySelector('.pubdate-text')?.innerText || document.querySelector('.publish-time')?.innerText || document.querySelector('.video-data .date')?.innerText || '未找到发布时间';
  const upName = document.querySelector('.up-name')?.innerText || document.querySelector('.owner-name')?.innerText || '未找到UP主';
  const tags = Array.from(document.querySelectorAll('.tag-item a')).map(a => a.innerText.trim());
  const likeCount = document.querySelector('.like-text')?.innerText || document.querySelector('.like-btn .count')?.innerText || '未找到点赞数';
  const coinCount = document.querySelector('.coin-text')?.innerText || document.querySelector('.coin-btn .count')?.innerText || '未找到投币数';
  return { title, desc, playCount, dmCount, pubDate, upName, tags, likeCount, coinCount };
})()
```

### 3. 视觉内容与互动分析
使用`browser_vision`工具，传入问题：`请总结这个B站视频的主要内容，包括讨论的主题、核心观点、关键信息点`，获取视频核心内容总结和页面互动细节。

### 4. 整理并保存结果
将提取的元数据和分析结果整理为标准markdown格式，使用`write_file`工具保存为`~/feushu/BV{视频号}-summary.md`文件，包含以下模块：
- 视频基本信息（标题、UP主、发布时间、播放数据、简介）
- 核心内容总结（主题、核心观点、关键信息点）
- 页面互动细节

## 示例输出格式
```markdown
# B站视频总结：{视频标题}
## 基本信息
- 视频标题：{title}
- UP主：{upName}
- 发布时间：{pubDate}
- 播放数据：{playCount}播放，{dmCount}弹幕，{likeCount}点赞，{coinCount}投币
## 核心内容总结
...
```

## 注意事项
- 若访问B站触发IP安全限制，参考`platform-ip-risk-mitigation`技能处理
- 优先使用内置浏览器`openclaw` profile
- 元数据提取脚本已更新为使用多个备选选择器，提升不同页面下的提取成功率
- 部分视频可能无法获取点赞、投币等数据，脚本会自动返回"未找到对应数据"作为占位符
- 发布时间可能无法从页面直接提取，可通过页面快照中的时间戳补充获取
- 若元数据提取失败，可补充使用`browser_snapshot`获取页面文本信息
