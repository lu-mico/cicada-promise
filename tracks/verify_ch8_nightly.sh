#!/usr/bin/env bash
# ch8 夜间验收（22:05 槽用 · 2026-11-24 主编）—— **两件事**
#   ① 当日切片交付检查（沿用 verify_daily_slice.sh 的按章口径，`CHAPTER=ch8`）
#   ② **整章级**判据（跨切片累加「三十年前」≤ 1）→ 只在**已有切片**时跑
#      （零切片不假警报：夜里若一章都还没交，① 会报，不必这里再报一次）
#
# ⚠️ **为什么要单独一层**：D2「三十年前」的口径是**整章 1 次**，而**单切片门禁是「每场 1 次」**
#    → 只跑①（逐场）会漏掉「A1 一次 + A3 一次」的整章超限 → **必须有一处整章可见的聚合**。
#    （2026-11-24 实测：单场门禁对跨场超限全绿。）
#
# 输出语义（与 verify_daily_slice.sh 一致）：一切正常 → **只印 NO_REPLY**（＝静默，不刷屏）；
# 有破线 → 印破线内容（进频道，由人看）。**退出码恒 0**（不拿退出码吓人，避免假警报）。
#
# ⚠️ **测副本必须显式给 REPO**（2026-11-24 实测踩到）：本脚本早先写死
#    `REPO="${REPO:-<真仓绝对路径>}"` → 在 /tmp 的 clone 里直接跑它，**实际判的是真仓**
#    （真仓零切片 → 一切「绿」→ 差点误报「整章判据没接上」）。
#    现在默认取**本脚本所在仓的根**（scripts 目录的上一级）→ **副本测副本、真仓跑真仓**；
#    `REPO=` 仍可显式覆盖。
#    ⚠️ **测试必须带 DRY_RUN=1**：`verify_daily_slice.sh` 判定「宿主漏跑」时会**真的**
#    `openclaw cron run be2b1e10` **补跑**（那会把作者叫醒）→ 端到端测试一律 `DRY_RUN=1`。
#    （生产路径本来就该补跑 —— 这是对的；只是测的人要知道。）
#
# 📌 **登记未做**：退出码恒 0 ⇒ cron `lastRunStatus` 永远是 ok → **万一 announce 投递失败，
#    破线就只剩日志**（频道里没有）。本轮判定：**保持退出码恒 0**（house 规矩：不拿退出码吓人）
#    → 投递失败这一情形登记为「未做」，等真有需要再改（改法：破线时 exit 1 ＋ 给 22:05 槽加 failureAlert）。
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$REPO" 2>/dev/null || { echo "🔴 ch8 夜间验收失败：进不了项目仓 $REPO"; exit 0; }
[ -e "$REPO/.git" ] || { echo "🔴 ch8 夜间验收失败：REPO 不是 git 仓 $REPO → 拒绝在未知目录上判账"; exit 0; }

# ⚠️ REPO 要**显式透传**给内层脚本：它自己也有默认路径，不传就会去判真仓（上面那个坑）。
SLICE_OUT="$(REPO="$REPO" CHAPTER=ch8 bash tracks/verify_daily_slice.sh 2>&1)"

CHAP_OUT=""
if ls manuscripts/ch8-*.md >/dev/null 2>&1; then
  CHAP_OUT="$(python3 tracks/ch8_chapter_checks.py --nightly 2>&1)"
fi

if [ -n "$CHAP_OUT" ] && [ "$CHAP_OUT" != "NO_REPLY" ]; then
  echo "🔴 ch8 整章级判据破线（22:05 夜间验收）"
  echo "$CHAP_OUT"
  if [ -n "$SLICE_OUT" ] && [ "$SLICE_OUT" != "NO_REPLY" ]; then
    echo "—— 当日切片检查同时有话："
    echo "$SLICE_OUT"
  fi
  exit 0
fi

if [ -n "$SLICE_OUT" ] && [ "$SLICE_OUT" != "NO_REPLY" ]; then
  echo "$SLICE_OUT"
  exit 0
fi

echo NO_REPLY
