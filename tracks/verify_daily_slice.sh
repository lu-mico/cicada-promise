#!/bin/bash
# ch5 每日切片交付验收（tracks/ch5-daily.md §八 铁律的自动化版）
#
# 规则（21:30 切片后 22:00 查两条证据）：
#   ① git log 有无当日 commit      ② openclaw cron runs 有无当日条目
#   两条都缺 且 下一场切片文件也不存在 → 宿主进程级漏跑 → 立刻补跑 be2b1e10
#   有条目但 0 commit                → 选片规则/产出问题 → 只告警，不自动重跑
#   下一场文件已存在但无 commit      → 上一轮仍在写/提交失败 → 只告警，不自动重跑
#   一切正常                        → 打印 NO_REPLY（cron 静默抑制，不刷频道）
#
# 用法：bash tracks/verify_daily_slice.sh          （正常执行）
#       DRY_RUN=1 bash tracks/verify_daily_slice.sh （只体检不补跑）

set -u
REPO="/Users/lumico/.openclaw/workspace-yomi/projects/cicada-promise"
JOB="be2b1e10-33ef-47f4-bd25-026fef90fa86"
# 切片表顺序（tracks/ch5-daily.md §二）：表序第一个尚不存在的切片 = 下一场
ORDER="B1 A1 B2 A2 B3 A3"

cd "$REPO" 2>/dev/null || { echo "🔴 ch5 验收失败：进不了项目仓 $REPO"; exit 0; }

TODAY="$(TZ=Asia/Tokyo date +%F)"
NOW_HM="$(TZ=Asia/Tokyo date +%H%M)"

# 21:30 交付槽尚未触发时（<21:45），当日「0 commit」是常态，不是漏跑 → 不判不补
if [ "$NOW_HM" -lt 2145 ]; then
  echo "NO_REPLY"
  exit 0
fi

NEXT=""
for s in $ORDER; do
  if [ ! -f "manuscripts/ch5-$s.md" ]; then NEXT="$s"; break; fi
done

# 六场齐 → 本章切片已完稿
if [ -z "$NEXT" ]; then echo "NO_REPLY"; exit 0; fi

COMMITS=$(git log --since="$TODAY 00:00" --pretty=%s 2>/dev/null | grep -c "ch5 .*切片")
RUNS=$(openclaw cron runs --id "$JOB" 2>/dev/null | grep -c "\"runAtIso\": \"$TODAY")

# 当日已有切片 commit → 正常
if [ "$COMMITS" -ge 1 ]; then echo "NO_REPLY"; exit 0; fi

if [ "$RUNS" -ge 1 ]; then
  echo "🔴 ch5 切片异常（$TODAY）：cron 有当日条目（$RUNS）但 0 commit，下一场应是 $NEXT。→ 选片规则/限流/提交失败问题，需人工查；不要重复提交已存在的切片。"
  exit 0
fi

# 下一场文件已存在却没 commit → 上一轮还在写或提交失败，不自动重跑（避免同夜双交）
if [ -f "manuscripts/ch5-$NEXT.md" ]; then
  echo "🟡 ch5 切片待提交（$TODAY）：manuscripts/ch5-$NEXT.md 已存在但当日 0 commit。→ 上一轮可能仍在写/提交失败，请人工确认后再决定是否补跑。"
  exit 0
fi

# 两条都缺 且 下一场文件不存在 → 宿主进程级漏跑 → 立刻补跑，不等下一个 21:30
if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[DRY_RUN] $TODAY：git 0 commit + cron 0 条目 + 下一场 $NEXT 文件不存在 → 判定为宿主进程级漏跑，实际执行会立刻补跑 $JOB。"
  exit 0
fi

( openclaw cron run "$JOB" >/tmp/ch5-backfill.log 2>&1 & )
sleep 10
RUNS2=$(openclaw cron runs --id "$JOB" 2>/dev/null | grep -c "\"runAtIso\": \"$TODAY")
if [ "$RUNS2" -ge 1 ]; then
  echo "🔴 ch5 切片漏跑（$TODAY）：git 0 commit + cron 0 条目 → 已手动补跑 $JOB（补跑条目已出现），下一场 = $NEXT。"
else
  echo "🔴 ch5 切片漏跑（$TODAY）：git 0 commit + cron 0 条目 → 自动补跑未生效，请手动执行：openclaw cron run $JOB。下一场 = $NEXT。"
fi
exit 0
