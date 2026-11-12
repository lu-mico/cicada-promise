#!/bin/bash
# ch6 每日切片交付验收（tracks/ch6-daily.md §八 铁律的自动化版）
#
# 规则（21:30 切片后 22:00 查两条证据）：
#   ① git log 有无当日 commit      ② openclaw cron runs 有无当日「成功」条目
#   两条都缺 且 下一场切片文件也不存在 → 宿主进程级漏跑 → 立刻补跑 be2b1e10
#   当日条目为 error/interrupted     → 槽被宿主掐掉 → 与「零条目」同等处理：立刻补跑
#   有成功条目但 0 commit             → 选片规则/产出问题 → 只告警，不自动重跑
#   下一场文件已存在但无 commit      → 上一轮仍在写/提交失败 → 只告警，不自动重跑
#   一切正常                        → 打印 NO_REPLY（cron 静默抑制，不刷频道）
#
# ⚠️ R42（2026-11-10）：21:50 gateway 重启把 21:30 切片槽与 22:05 验收槽**同时掐掉**，
#    两条 cron runs 条目都写着 "cron: job interrupted by gateway restart"。
#    → **error 条目不算「槽跑过」**，必须与「零条目」同等处理 = 立刻补跑。
#    → 判据只看 **status=ok** 的条目；老脚本用 grep 数条目，error 条目会被算成「有条目」，
#      于是只告警不补跑 → 那晚的切片会静默丢失。本版改用 JSON 解析，error/interrupted 单独计数。
#
# 用法：bash tracks/verify_daily_slice.sh          （正常执行）
#       DRY_RUN=1 bash tracks/verify_daily_slice.sh （只体检不补跑）

set -u
REPO="/Users/lumico/.openclaw/workspace-yomi/projects/cicada-promise"
JOB="be2b1e10-33ef-47f4-bd25-026fef90fa86"
# 切片表顺序（tracks/ch6-daily.md §二）：表序第一个尚不存在的切片 = 下一场
ORDER="A1 B1 A2 B2 A3 B3"

cd "$REPO" 2>/dev/null || { echo "🔴 ch6 验收失败：进不了项目仓 $REPO"; exit 0; }

TODAY="$(TZ=Asia/Tokyo date +%F)"
NOW_HM="$(TZ=Asia/Tokyo date +%H%M)"

# 21:30 交付槽尚未触发时（<21:45），当日「0 commit」是常态，不是漏跑 → 不判不补
if [ "$NOW_HM" -lt 2145 ]; then
  echo "NO_REPLY"
  exit 0
fi

NEXT=""
for s in $ORDER; do
  if [ ! -f "manuscripts/ch6-$s.md" ]; then NEXT="$s"; break; fi
done

# 六场齐 → 本章切片已完稿
if [ -z "$NEXT" ]; then echo "NO_REPLY"; exit 0; fi

# 统计当日 cron runs 条目：**成功条目 / 被掐条目**（R42：error 不算「跑过」）
count_runs() {
  openclaw cron runs --id "$JOB" 2>/dev/null | python3 -c "
import sys, json
raw = sys.stdin.read()
i = raw.find('{')
ok = bad = 0
if i >= 0:
    try:
        d = json.loads(raw[i:])
    except Exception:
        d = {}
    today = '$TODAY'
    for e in d.get('entries', []):
        r = str(e.get('runAtIso') or '')
        if not r.startswith(today):
            continue
        if e.get('status') == 'ok':
            ok += 1
        else:
            bad += 1
print(ok, bad)
" 2>/dev/null || echo "0 0"
}

COMMITS=$(git log --since="$TODAY 00:00" --pretty=%s 2>/dev/null | grep -c "ch6 .*切片")
read -r RUNS_OK RUNS_BAD <<<"$(count_runs)"

# 当日已有切片 commit → 正常
if [ "$COMMITS" -ge 1 ]; then echo "NO_REPLY"; exit 0; fi

# 当日有**成功**条目 → 槽跑过了却 0 commit → 只告警，不自动重跑（防重复交付）
if [ "${RUNS_OK:-0}" -ge 1 ]; then
  echo "🔴 ch6 切片异常（$TODAY）：cron 有当日成功条目但 0 commit，下一场应是 $NEXT。→ 选片规则/限流/提交失败问题，需人工查；不要重复提交已存在的切片。"
  exit 0
fi

# 下一场文件已存在却没 commit → 上一轮还在写或提交失败，不自动重跑（避免同夜双交）
if [ -f "manuscripts/ch6-$NEXT.md" ]; then
  echo "🟡 ch6 切片待提交（$TODAY）：manuscripts/ch6-$NEXT.md 已存在但当日 0 commit。→ 上一轮可能仍在写/提交失败，请人工确认后再决定是否补跑。"
  exit 0
fi

# 槽被掐（error/interrupted）或零条目 → 宿主进程级漏跑 → 立刻补跑，不等下一个 21:30
if [ "${RUNS_BAD:-0}" -ge 1 ]; then
  SLOT_STATE="槽被宿主掐掉（$RUNS_BAD 条 interrupted/error 条目）"
else
  SLOT_STATE="零条目（宿主进程当时不在位）"
fi

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[DRY_RUN] $TODAY：git 0 commit + $SLOT_STATE + 下一场 $NEXT 文件不存在 → 判定为宿主进程级漏跑，实际执行会立刻补跑 $JOB。"
  exit 0
fi

( openclaw cron run "$JOB" >/tmp/ch6-backfill.log 2>&1 & )
sleep 10
read -r RUNS2_OK RUNS2_BAD <<<"$(count_runs)"
if [ "${RUNS2_OK:-0}" -ge 1 ]; then
  echo "🔴 ch6 切片漏跑（$TODAY）：git 0 commit + $SLOT_STATE → 已手动补跑 $JOB（补跑成功条目已出现），下一场 = $NEXT。"
else
  echo "🔴 ch6 切片漏跑（$TODAY）：git 0 commit + $SLOT_STATE → 自动补跑未生效，请手动执行：openclaw cron run $JOB。下一场 = $NEXT。"
fi
exit 0
