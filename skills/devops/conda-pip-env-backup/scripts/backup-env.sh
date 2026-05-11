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
