#!/usr/bin/env bash
# bob_e2e.sh — 一键端到端验证 Ledger CLI（含登录、导入/新增/列表/统计/出图、导出、预算、提醒、登出）
# 适用环境：Git Bash / WSL / macOS / Linux
# 使用方法：
#   chmod +x tests/bob_e2e.sh
#   ./tests/bob_e2e.sh
set -euo pipefail

# ====== 可按需修改的参数 ======
DB_URL="sqlite:///./ledger.db"
USERNAME="alice"
PASSWORD="123456"
EMAIL="a@b.com"
MONTH="2025-01"
CSV_PATH="data/sample_records.csv"
REPORTS_DIR="reports"
PY="python"                # 或 python3 / py -m 的 python
CLI_MOD="-m ledger.api.cli"

# ====== 辅助函数 ======
title() { echo -e "\n==================== $* ====================\n"; }
step()  { echo -e "→ $*"; }
save()  { # 将上一条命令输出同时写入文件
  local outfile="$1"; shift
  "$@" | tee "$outfile"
}

mkdir -p "$REPORTS_DIR"

# ====== 0) 环境信息（可选） ======
title "0) 环境与依赖检查"
step "Python 版本"
$PY -V
step "确保 reports 目录存在：$REPORTS_DIR"
echo "OK" > "$REPORTS_DIR/.keep"

# ====== 1) 初始化数据库 ======
title "1) init-db"
save "$REPORTS_DIR/01_init_db.txt" \
  $PY $CLI_MOD init-db --db "$DB_URL"

# ====== 2) 注册与登录 ======
title "2) register / login / whoami"
# 注册（已注册会报错也无妨；你可按需忽略错误）
set +e
$PY $CLI_MOD register --db "$DB_URL" --username "$USERNAME" --password "$PASSWORD" --email "$EMAIL" \
  | tee "$REPORTS_DIR/02_register.txt"
set -e

save "$REPORTS_DIR/03_login.txt" \
  $PY $CLI_MOD login --db "$DB_URL" --username "$USERNAME" --password "$PASSWORD"

save "$REPORTS_DIR/04_whoami.txt" \
  $PY $CLI_MOD whoami

# ====== 3) 导入 CSV ======
title "3) import-csv"
if [[ -f "$CSV_PATH" ]]; then
  save "$REPORTS_DIR/05_import_csv.txt" \
    $PY $CLI_MOD import-csv --db "$DB_URL" --path "$CSV_PATH"
else
  echo "⚠️  未找到 CSV：$CSV_PATH，跳过导入"
fi

# ====== 4) 新增两笔记录 ======
title "4) add records"
save "$REPORTS_DIR/06_add_expense.txt" \
  $PY $CLI_MOD add --db "$DB_URL" --type EXPENSE --category coffee --amount 18.5 --date "$MONTH-10" --note "latte"
save "$REPORTS_DIR/07_add_income.txt" \
  $PY $CLI_MOD add --db "$DB_URL" --type INCOME  --category bonus  --amount 300  --date "$MONTH-15" --note "Q1"

# ====== 5) 列出当月记录 ======
title "5) list"
save "$REPORTS_DIR/08_list_${MONTH}.txt" \
  $PY $CLI_MOD list --db "$DB_URL" --month "$MONTH"

# ====== 6) 统计与出图 ======
title "6) stats + plot"
save "$REPORTS_DIR/09_stats_${MONTH}.txt" \
  $PY $CLI_MOD stats --db "$DB_URL" --month "$MONTH"
# 出图
save "$REPORTS_DIR/10_stats_plot_${MONTH}.txt" \
  $PY $CLI_MOD stats --db "$DB_URL" --month "$MONTH" --plot --reports-dir "$REPORTS_DIR"

# ====== 7) 导出 CSV ======
title "7) export-csv"
EXPORT_FILE="$REPORTS_DIR/export_${MONTH}.csv"
save "$REPORTS_DIR/11_export_${MONTH}.txt" \
  $PY $CLI_MOD export-csv --db "$DB_URL" --path "$EXPORT_FILE" --month "$MONTH"
echo "---- 导出文件预览 ----" | tee -a "$REPORTS_DIR/11_export_${MONTH}.txt"
head -n 20 "$EXPORT_FILE" | tee -a "$REPORTS_DIR/11_export_${MONTH}.txt"

# ====== 8) 预算（设置/列表/进度） ======
title "8) budget set/list/progress"
save "$REPORTS_DIR/12_budget_set.txt" \
  $PY $CLI_MOD budget set --db "$DB_URL" --category food --limit 500
save "$REPORTS_DIR/13_budget_list.txt" \
  $PY $CLI_MOD budget list --db "$DB_URL"
save "$REPORTS_DIR/14_budget_progress_${MONTH}.txt" \
  $PY $CLI_MOD budget progress --db "$DB_URL" --month "$MONTH"

# ====== 9) 提醒（设置/列表/触发） ======
title "9) reminder set/list/emit"
save "$REPORTS_DIR/15_reminder_set.txt" \
  $PY $CLI_MOD reminder set --db "$DB_URL" --time 09:00 --message "记账一下"
save "$REPORTS_DIR/16_reminder_list.txt" \
  $PY $CLI_MOD reminder list --db "$DB_URL"
save "$REPORTS_DIR/17_reminder_emit.txt" \
  $PY $CLI_MOD reminder emit --db "$DB_URL"

# ====== 10) 登出与验证 ======
title "10) logout / whoami"
save "$REPORTS_DIR/18_logout.txt" \
  $PY $CLI_MOD logout
save "$REPORTS_DIR/19_whoami_after_logout.txt" \
  $PY $CLI_MOD whoami

title "完成 ✅  所有输出已保存到：$REPORTS_DIR/"
