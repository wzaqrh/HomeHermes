---
name: conda-pip-env-backup
description: 备份与复原Conda环境和pip依赖包到~/.hermes/environments_backup/，支持全量备份、单环境备份、以及从备份文件复原
version: "1.0.0"
tags: [conda, pip, backup, restore, environment, devops]
---

# Conda & pip 环境备份与复原

## 适用场景

- 定期备份本机的 conda 环境和 pip 依赖清单，防止重装系统或环境损坏后丢失
- 将某台机器上的 conda 环境迁移到另一台机器
- 在修改环境前创建快照，方便回滚
- 复原 conda 环境（从 YAML 文件重建）

## 目录结构约定

所有备份文件统一存放在 `~/.hermes/environments_backup/`，按时间戳组织：

```
~/.hermes/environments_backup/
├── latest/                          # 指向最近一次备份的软链接
├── 2026-05-10_21-00-00/             # 按时间戳的子目录
│   ├── conda/
│   │   ├── environment-base.yml     # base 环境的完整导出
│   │   ├── environment-MiroFish.yml # 各环境独立导出
│   │   └── environment-tradingagents.yml
│   └── pip/
│       ├── freeze-base.txt          # base 环境的 pip 包列表
│       ├── freeze-MiroFish.txt
│       └── freeze-tradingagents.txt
├── 2026-05-09_14-30-00/
│   └── ...
```

## 操作流程

### 一、全量备份所有 conda + pip 环境

```bash
# 设定备份目录
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$HOME/.hermes/environments_backup/$TIMESTAMP"
mkdir -p "$BACKUP_DIR/conda" "$BACKUP_DIR/pip"

# 遍历所有 conda 环境
for env in $(conda env list | grep -v "^#" | grep -v "^$" | awk '{print $1}' | grep -v "^$"); do
  echo ">>> Backing up conda env: $env"
  
  # conda 导出（含所有包 + 来源渠道）
  conda env export -n "$env" --no-builds > "$BACKUP_DIR/conda/environment-${env}.yml" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "  OK: conda/${env}.yml"
  else
    echo "  WARN: conda export failed for $env"
  fi
  
  # pip freeze（该环境下的 pip 包）
  conda run -n "$env" pip freeze > "$BACKUP_DIR/pip/freeze-${env}.txt" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "  OK: pip/${env}.txt"
  else
    echo "  WARN: pip freeze failed for $env"
  fi
done

# 更新 latest 软链接
ln -snf "$BACKUP_DIR" "$HOME/.hermes/environments_backup/latest"
echo ""
echo "=== 全量备份完成 ==="
echo "备份目录: $BACKUP_DIR"
ls -la "$BACKUP_DIR/conda/"
ls -la "$BACKUP_DIR/pip/"
```

### 二、备份单个 conda 环境

```bash
ENV_NAME="tradingagents"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$HOME/.hermes/environments_backup/$TIMESTAMP"
mkdir -p "$BACKUP_DIR/conda" "$BACKUP_DIR/pip"

conda env export -n "$ENV_NAME" --no-builds > "$BACKUP_DIR/conda/environment-${ENV_NAME}.yml"
conda run -n "$ENV_NAME" pip freeze > "$BACKUP_DIR/pip/freeze-${ENV_NAME}.txt"

ln -snf "$BACKUP_DIR" "$HOME/.hermes/environments_backup/latest"
echo "已备份 $ENV_NAME 到 $BACKUP_DIR"
```

### 三、仅导出 pip 依赖（不带 conda channel）

```bash
ENV_NAME="tradingagents"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$HOME/.hermes/environments_backup/$TIMESTAMP"
mkdir -p "$BACKUP_DIR/pip"

# 推荐: --exclude-editable 排除本地开发包, 避免安装时报错
conda run -n "$ENV_NAME" pip freeze --exclude-editable > "$BACKUP_DIR/pip/freeze-${ENV_NAME}.txt"

echo "已导出 $ENV_NAME 的 pip 依赖"
wc -l "$BACKUP_DIR/pip/freeze-${ENV_NAME}.txt"
```

### 四、从备份复原 conda 环境

```bash
# 从某个备份目录复原
BACKUP_DIR="$HOME/.hermes/environments_backup/latest"

# 列出可用环境
ls "$BACKUP_DIR/conda/" | sed 's/environment-//;s/\.yml//'

# 复原单个环境（例如 tradingagents）
ENV_NAME="tradingagents"
conda env create -f "$BACKUP_DIR/conda/environment-${ENV_NAME}.yml" -n "$ENV_NAME"

# 如果环境已存在，用 update 而非 create
conda env update -f "$BACKUP_DIR/conda/environment-${ENV_NAME}.yml" -n "$ENV_NAME"
```

### 五、仅复原 pip 依赖（在已有环境中）

```bash
ENV_NAME="tradingagents"
BACKUP_DIR="$HOME/.hermes/environments_backup/latest"

conda run -n "$ENV_NAME" pip install -r "$BACKUP_DIR/pip/freeze-${ENV_NAME}.txt"
```

### 六、列出所有历史备份

```bash
ls -lt ~/.hermes/environments_backup/ | head -20
```

## 注意事项 / 常见问题

1. **`--no-builds` 参数**：导出时建议加上 `--no-builds`，避免跨平台 build hash 不匹配导致复原失败。如果非常在意精确复现（同架构同OS），可以不加此参数同时导出 `--explicit` 版本。
2. **pip 包版本冲突**：pip freeze 包含精确版本号，复原时如果某些包的新版已不兼容，可能安装失败。建议在复原前先查看 `freeze-*.txt` 中的关键包版本。
3. **base 环境**：base 环境也可以通过 conda env export 导出，但复原时一般用 `conda env update` 而不用 `conda env create`，因为 base 是系统根环境不能覆盖创建。
4. **--exclude-editable**：如果当前环境有通过 `pip install -e .` 安装的本地开发包，freeze 会包含 `-e` 路径指向，这些路径在其他机器上不存在。建议用 `--exclude-editable` 过滤掉，或手动编辑 freeze 文件。
5. **大型环境**：如果环境很大（200+ 包），conda env export 可能耗时较长，耐心等待。
6. **跨平台迁移**：Linux → macOS 或 Windows 的跨平台迁移时，部分包（如 torch、tensorflow）的安装方式不同，建议先复原 conda 环境，然后手动处理平台特定的包。
7. **恢复前确认**：恢复操作前建议先用 `conda env list` 确认环境是否已存在，避免冲突。
8. **软链接 latest**：每次备份自动更新 `latest` 指向最近一次备份，方便脚本化和快速引用。

## 快捷脚本

### 一键备份脚本

将以下内容保存到 `~/.hermes/scripts/backup-env.sh`：

```bash
#!/bin/bash
# 全量备份所有 conda 环境 + pip 依赖
set -euo pipefail

BACKUP_ROOT="$HOME/.hermes/environments_backup"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR/conda" "$BACKUP_DIR/pip"

echo "[$(date '+%H:%M:%S')] 开始备份 conda 环境..."

conda env list | grep -v "^#" | grep -v "^$" | awk '{print $1}' | grep -v "^$" | while read -r env; do
  echo "  -> 备份环境: $env"
  conda env export -n "$env" --no-builds > "$BACKUP_DIR/conda/environment-${env}.yml" 2>/dev/null || echo "  [WARN] conda export $env 失败"
  conda run -n "$env" pip freeze --exclude-editable > "$BACKUP_DIR/pip/freeze-${env}.txt" 2>/dev/null || echo "  [WARN] pip freeze $env 失败"
done

ln -snf "$BACKUP_DIR" "$BACKUP_ROOT/latest"
echo "[$(date '+%H:%M:%S')] 备份完成: $BACKUP_DIR"
echo "  文件统计:"
echo "    conda: $(ls $BACKUP_DIR/conda/ 2>/dev/null | wc -l) 个文件"
echo "    pip:   $(ls $BACKUP_DIR/pip/ 2>/dev/null | wc -l) 个文件"
```

### 对比备份差异

```bash
# 对比最近两次备份的 conda 环境差异
DIFF_TOOL="diff --color=always"
BACKUPS=($(ls -t ~/.hermes/environments_backup/ | grep -v latest | head -2))
if [ ${#BACKUPS[@]} -ge 2 ]; then
  for f in ~/.hermes/environments_backup/${BACKUPS[1]}/conda/*.yml; do
    fname=$(basename "$f")
    newf="$HOME/.hermes/environments_backup/${BACKUPS[0]}/conda/$fname"
    if [ -f "$newf" ]; then
      echo "=== $fname ==="
      diff <(grep -E "^  - " "$f" | sort) <(grep -E "^  - " "$newf" | sort) | $DIFF_TOOL || true
    fi
  done
fi
```
