---
name: debian-ubuntu-python-skill-install-fix
description: 修复 Debian/Ubuntu 12+ 系统上 Python 技能安装的常见问题
category: devops
---

# Debian/Ubuntu 12+ Python 技能安装修复

针对 Debian 12+ / Ubuntu 22.04+ 系统上安装 Python 技能或工具时遇到的常见问题的标准化修复方案：

## 常见问题 1：`externally-managed-environment` 错误
Debian 12+ 启用了系统包管理隔离，直接使用 `pip install` 会触发该错误，提示无法在系统包环境中安装第三方包。

### 修复方式：
为所有 `pip install` 命令添加 `--break-system-packages` 参数，绕过系统包管理限制，允许直接安装到全局 Python 环境。

## 常见问题 2：网络超时 / 依赖安装失败
国内网络环境下访问官方 PyPI 源会出现连接超时或下载缓慢的问题，导致依赖安装失败。

### 修复方式：
为所有 `pip install` 命令添加国内 PyPI 镜像源，例如阿里云镜像：
`-i https://mirrors.aliyun.com/pypi/simple/`

## 适用场景：
安装任何基于 Python 的 CLI 技能或工具时遇到上述问题时使用，尤其适用于国内网络环境。

## 示例：修复 qiaomu-anything-to-notebooklm 技能安装
1. 克隆技能仓库到本地：`git clone https://github.com/joeseesun/qiaomu-anything-to-notebooklm ~/.hermes/skills/qiaomu-anything-to-notebooklm`
2. 编辑 `install.sh` 文件，将所有 `pip3 install` 命令修改为带参数的版本：
   ```bash
   pip3 install --break-system-packages -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   ```
3. 重新运行安装脚本：`cd ~/.hermes/skills/qiaomu-anything-to-notebooklm && ./install.sh`

## 示例：修复 news-aggregator-skill 技能安装
1. 克隆技能仓库到本地：`git clone https://github.com/cclank/news-aggregator-skill ~/.hermes/skills/news-aggregator-skill`
2. 安装Python依赖并配置Playwright（使用国内镜像加速）：
   ```bash
   cd ~/.hermes/skills/news-aggregator-skill
   pip install --break-system-packages -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ python -m playwright install chromium
   ```

## 验证方式：
安装完成后，运行技能的测试命令或帮助指令，确认所有依赖已正确安装。