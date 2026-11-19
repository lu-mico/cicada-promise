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
YESTERDAY="$(TZ=Asia/Tokyo date -v-1d +%F)"
NOW_HM="$(TZ=Asia/Tokyo date +%H%M)"

# ⚠️ R50（2026-11-14 01:09，Mico 验收脚本先撞上同型 bug）：**证据窗口按「切片槽日」算，不按「脚本运行日」算**。
#    旧逻辑把「当日」＝脚本运行当天：验收一旦跨过午夜（01:09 补验 21:30 那场），
#    日历当天自然没有当日 commit → 假 FAIL／假漏跑；反过来，若 22:05 验收槽被宿主拖到 00:0x，
#    旧逻辑直接 `<2145` 早退 NO_REPLY → **那晚的验收静默消失**（既不判也不补）。
#    现口径：**SLOT_DATE = 最近一个已过去的 21:30 槽所在的日期**
#      · 21:45 之后运行 → 槽＝今天
#      · 00:00–03:00 运行 → 槽＝昨天（跨日补验／验收槽被拖过午夜）
#      · 03:00–21:44 运行 → 不在验收窗口内 → NO_REPLY（不判不补，防白天误触发）
#    证据一律取 SLOT_DATE 当天（日历日）而不是脚本运行日。
SLOT_DATE_OVERRIDE="${SLOT_DATE_OVERRIDE:-}"
if [ -n "$SLOT_DATE_OVERRIDE" ]; then
  SLOT_DATE="$SLOT_DATE_OVERRIDE"; IN_WINDOW=1          # 测试用
elif [ "$NOW_HM" -ge 2145 ]; then
  SLOT_DATE="$TODAY"; IN_WINDOW=1                         # 正常窗口：21:45 之后
elif [ "$NOW_HM" -le 0300 ]; then
  SLOT_DATE="$YESTERDAY"; IN_WINDOW=1                     # 跨日补验：00:00–03:00
else
  SLOT_DATE="$YESTERDAY"; IN_WINDOW=0                     # 白天不在验收窗口
fi

if [ "$IN_WINDOW" -eq 0 ]; then
  echo "NO_REPLY"
  exit 0
fi
# 证据窗口：**槽日 00:00 → 次日 03:00**（含跨日补跑窗口）——不能只用 --since，
# 否则更晚日期的 commit 会把「那一夜其实没交」掩盖掉（这正是本次要堵的洞）。
# BSD date 的 -f/-v 组合会吞掉输出格式（实测得到 "Fri Nov 13 01:10 JST"）→ 改用 python 算窗口。
eval "$(python3 - "$SLOT_DATE" <<'PYEOF'
import datetime, sys
d = datetime.date.fromisoformat(sys.argv[1])
start = datetime.datetime.combine(d, datetime.time(0, 0, 0))
end = start + datetime.timedelta(days=1, hours=3)
print(f"SLOT_START='{start:%Y-%m-%d %H:%M:%S}'")
print(f"SLOT_END='{end:%Y-%m-%d %H:%M:%S}'")
print(f"SLOT_NEXT='{(d + datetime.timedelta(days=1)):%Y-%m-%d}'")
PYEOF
)"
echo "[ch6-verify] 运行时刻 $TODAY $NOW_HM · 校验槽日 SLOT_DATE=$SLOT_DATE · 证据窗口 $SLOT_START → $SLOT_END" >> /tmp/ch6-verify-last.log

NEXT=""
for s in $ORDER; do
  if [ ! -f "manuscripts/ch6-$s.md" ]; then NEXT="$s"; break; fi
done

# ── 期望工作判定（2026-11-18 扩充：切片期 → 章级阶段期）────────────────────
# 切片期：下一场切片文件不存在 → 今晚该交一场切片（commit 标题含「ch6 …切片」）
# 章级期（六场齐，2026-11-17 B3 之后进入）：改判阶段 ——
#   ① 阶段1 合成：manuscripts/ch6-sample.md 未生成
#   ② 阶段2 去 AI 味：tracks/ch6-deslop-report.md 未生成
#   ③ 阶段3 四视角评审 + v1.0：尚无 ch6 v1.0 定稿 commit
#   ④ 本章已定稿（v1.0 commit 在 git log 里）→ 无待办 → 静默（等主编切 ch7 轨道）
# ⚠️ 2026-11-18 之前本脚本在六场齐时一律 NO_REPLY → 切到章级轨道后，
#    21:30 槽若被宿主掐掉／空跑，22:05 槽**看不见**（切片已齐 → 直接静默）→ 纪律失去可执行轨道。
EXPECT=""
# 「评审已落」态（2026-11-20 Mico 补）
#   阶段 3 的产物是 `tracks/ch6-review.md`；它已落仓、但 v1.0 定稿 commit 还没有时：
#   21:30 槽按 prompt 的**⑤并行锁**「不重复跑评审、不重复改稿」→ **当晚 0 commit 是预期**，
#   不是「产出/提交失败」。旧逻辑只认「有成功条目 + 0 commit = 🔴 异常」→ 每晚必误报，
#   而且报出的 EXPECT 还写着「阶段3 四视角评审 + v1.0」→ **会把已经做完的阶段说成待做**，
#   存在把「重复评审」重新勾起来的风险。
REVIEW_DONE=0
# commit 判据分两种形态，**取并集**：
#   切片期：「ch6 [AB][0-9] 切片」（如「Yomi: ch6 B3 切片 — …」）
#   章级期：「ch6 阶段N …」／「ch6 v1.0 …」／「tracks(ch6): chapter review|deslop …」
# ⚠️ **不能用宽口径「ch6」**：同日的**轨道维护类 commit**（如「tracks(ch6): R54 入档 …」）
#    会被误当成阶段 commit → 22:05 槽看不见「今晚阶段没交」→ 又一次假绿（R53 同族）。
SLICE_COMMIT_RE="ch6 [AB][0-9] 切片"
STAGE_COMMIT_RE="ch6 (阶段[0-9]|v1\.0)|tracks\(ch6\): (chapter review|deslop)"
COMMIT_RE="$SLICE_COMMIT_RE|$STAGE_COMMIT_RE"
if [ -z "$NEXT" ]; then
  if git log --pretty=%s 2>/dev/null | grep -q "ch6 v1.0"; then
    echo "NO_REPLY"; exit 0
  fi
  if [ ! -f "manuscripts/ch6-sample.md" ]; then
    EXPECT="阶段1 合成（manuscripts/ch6-sample.md 未生成）"
  elif [ ! -f "tracks/ch6-deslop-report.md" ]; then
    EXPECT="阶段2 去 AI 味（tracks/ch6-deslop-report.md 未生成）"
  elif [ -f "tracks/ch6-review.md" ]; then
    REVIEW_DONE=1
    EXPECT="阶段3 已落（评审在仓）→ 等作者改稿 → 改稿后由主编出 v1.0 认可记录"
  else
    EXPECT="阶段3 四视角评审 + v1.0（尚无 ch6 v1.0 定稿 commit）"
  fi
else
  EXPECT="切片 $NEXT"
fi

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
    slot = '$SLOT_DATE'
    slot_next = '$SLOT_NEXT'
    for e in d.get('entries', []):
        r = str(e.get('runAtIso') or '')
        # 槽日当天，或跨日补跑窗口内（次日 03:00 之前）
        in_win = r.startswith(slot)
        if r.startswith(slot_next) and len(r) >= 13 and r[11:13] <= '03':
            in_win = True
        if not in_win:
            continue
        if e.get('status') == 'ok':
            ok += 1
        else:
            bad += 1
print(ok, bad)
" 2>/dev/null || echo "0 0"
}

COMMITS=$(git log --since="$SLOT_START" --until="$SLOT_END" --pretty=%s 2>/dev/null | grep -cE "$COMMIT_RE")
read -r RUNS_OK RUNS_BAD <<<"$(count_runs)"

# 当日已有切片 commit → 正常
if [ "$COMMITS" -ge 1 ]; then echo "NO_REPLY"; exit 0; fi
echo "[ch6-verify] SLOT_DATE=$SLOT_DATE 槽日已有 commit ${COMMITS} 条（期望：$EXPECT）→ 正常" >> /tmp/ch6-verify-last.log

# 「评审已落」态（2026-11-20 Mico 补）：21:30 槽按⑤并行锁**故意不产 commit** →
#   当晚 0 commit 属预期 → **不报🔴、也不自动补跑**（补跑只会再报一次「阶段 3 进行中」）。
if [ "$REVIEW_DONE" = "1" ]; then
  echo "ℹ️ ch6（槽日 $SLOT_DATE）：阶段 3 已落（评审报告在仓）→ 21:30 槽按⑤并行锁不重复跑评审、当晚 0 commit 属预期，无需人工查。cron 当日成功条目 ${RUNS_OK:-0} 条（0 ＝ 宿主层压根没跑；但按⑤它本来也不该产 commit → 不补跑）。现在该做的是「$EXPECT」。"
  exit 0
fi

# 当日有**成功**条目 → 槽跑过了却 0 commit → 只告警，不自动重跑（防重复交付）
if [ "${RUNS_OK:-0}" -ge 1 ]; then
  echo "🔴 ch6 异常（槽日 $SLOT_DATE）：cron 有当日成功条目但 0 commit，今晚该做的是「$EXPECT」。→ 产出/提交失败问题，需人工查；不要重复提交已存在的稿件。"
  exit 0
fi

# 下一场文件已存在却没 commit → 上一轮还在写或提交失败，不自动重跑（避免同夜双交）
if [ -f "manuscripts/ch6-$NEXT.md" ]; then
  echo "🟡 ch6 待提交（槽日 $SLOT_DATE）：manuscripts/ch6-$NEXT.md 已存在但当日 0 commit。→ 上一轮可能仍在写/提交失败，请人工确认后再决定是否补跑。"
  exit 0
fi

# 槽被掐（error/interrupted）或零条目 → 宿主进程级漏跑 → 立刻补跑，不等下一个 21:30
if [ "${RUNS_BAD:-0}" -ge 1 ]; then
  SLOT_STATE="槽被宿主掐掉（$RUNS_BAD 条 interrupted/error 条目）"
else
  SLOT_STATE="零条目（宿主进程当时不在位）"
fi

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[DRY_RUN] 槽日 $SLOT_DATE：git 0 commit + $SLOT_STATE + 今晚该做的是「$EXPECT」→ 判定为宿主进程级漏跑，实际执行会立刻补跑 $JOB。"
  exit 0
fi

( openclaw cron run "$JOB" >/tmp/ch6-backfill.log 2>&1 & )
sleep 10
read -r RUNS2_OK RUNS2_BAD <<<"$(count_runs)"
if [ "${RUNS2_OK:-0}" -ge 1 ]; then
  echo "🔴 ch6 漏跑（槽日 $SLOT_DATE）：git 0 commit + $SLOT_STATE → 已手动补跑 $JOB（补跑成功条目已出现），今晚该做的是「$EXPECT」。"
else
  echo "🔴 ch6 漏跑（槽日 $SLOT_DATE）：git 0 commit + $SLOT_STATE → 自动补跑未生效，请手动执行：openclaw cron run $JOB。今晚该做的是「$EXPECT」。"
fi
exit 0
