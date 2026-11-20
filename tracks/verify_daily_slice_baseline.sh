#!/bin/bash
# tracks/verify_daily_slice_baseline.sh
#
# 用途：**重新生成** tracks/verify_daily_slice_baseline_ch6.txt（ch6 模式的逐字输出基线）。
#       本脚本的 stdout 就是那个基线文件的全文（含头注释），因此判据只有一条：
#         diff <(bash tracks/verify_daily_slice_baseline.sh) tracks/verify_daily_slice_baseline_ch6.txt
#       为空即「ch6 行为没漂」。
#
# 边界（硬性）：
#   · 不读真实 cron —— 自建 stub `openclaw`（只 `cat` 夹具 JSON），只放 PATH 里给自己用
#   · 不写真实仓 —— 全部动作在 mktemp 里；真仓只被 `git clone` 读一次
#   · 不产生任何 commit —— 历史态用 `git worktree add --detach <sha>`；合成态的 commit 只落在
#     /tmp 的空 repo 里（带钉死的 GIT_AUTHOR_DATE／GIT_COMMITTER_DATE）
#   · 不改 tracks/verify_daily_slice.sh —— 只读它
#
# 用法：
#   bash tracks/verify_daily_slice_baseline.sh                  # 打印基线全文（stdout）
#   bash tracks/verify_daily_slice.sh                            # 被测脚本（ch6 默认模式）
#   校验：diff <(bash tracks/verify_daily_slice_baseline.sh) tracks/verify_daily_slice_baseline_ch6.txt
#   重冻：bash tracks/verify_daily_slice_baseline.sh > tracks/verify_daily_slice_baseline_ch6.txt
#
# ⚠️ 历史态锚在具体 SHA 上（96a0ecf／4ac23c4／8cec218／465e6c8）。若历史被改写／rebase，
#    生成器会失败（worktree add 找不到 SHA）——那时需要重新冻基线并同步改本脚本与头注释。

set -u
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SELF_DIR/.." && pwd)"
VERIFY="$REPO/tracks/verify_daily_slice.sh"

[ -f "$VERIFY" ] || { echo "🔴 找不到被测脚本：$VERIFY" >&2; exit 1; }

T="$(mktemp -d "${TMPDIR:-/tmp}/vdsbase.XXXXXX")" || exit 1
trap 'rm -rf "$T"' EXIT

mkdir -p "$T/bin"
cat > "$T/bin/openclaw" <<'EOF'
#!/bin/bash
# stub：只回放夹具 JSON，绝不真调 cron
cat "${STUB_RUNS_FILE:-/dev/null}"
EOF
chmod +x "$T/bin/openclaw"
export PATH="$T/bin:$PATH"
export DRY_RUN=1
export STUB_CALL_LOG=/dev/null

clone="$T/repo"
git clone -q "$REPO" "$clone" || { echo "🔴 git clone 失败：$REPO" >&2; exit 1; }

emit_fixture() { printf '%s\n' "$1" > "$T/runs.json"; export STUB_RUNS_FILE="$T/runs.json"; }
OK1='{"entries":[{"runAtIso":"2026-11-19T21:30:00.015+09:00","status":"ok"}]}'
ERR1='{"entries":[{"runAtIso":"2026-11-19T21:30:00.015+09:00","status":"error"}]}'
NONE='{"entries":[]}'

hdr() { printf '===== [%s] %s =====\n' "$1" "$2"; }
run() { # run <dir> <slot> <命令行示意>
  local d=$1 slot=$2 shown=$3 out ec
  # ⚠️ REPO 空会让被测脚本 `cd ""`（bash 里＝no-op）→ 拿**当前目录**当仓判，静默读错账。硬堵。
  [ -n "$d" ] && [ -d "$d" ] || { echo "🔴 run(): 工作树为空/不存在（$d）" >&2; exit 1; }
  out=$(env REPO="$d" CHAPTER=ch6 SLOT_DATE_OVERRIDE="$slot" bash "$VERIFY" 2>&1); ec=$?
  printf '$ %s\n%s\n[exit %s]\n\n' "$shown" "$out" "$ec"
}

cat <<'HDR'
# tracks/verify_daily_slice_baseline_ch6.txt
#
# 【这是什么】tracks/verify_daily_slice.sh 在 **CHAPTER=ch6（默认模式）** 下、14 个固定状态上的
#   **完整输出逐字快照**（含退出码）。用途：机器证明「按章参数化 / 后续改动没有漂 ch6 行为」，
#   并作为 ch6 模式的行为回归基线。
#   ⚠️ 本文件**由 tracks/verify_daily_slice_baseline.sh 生成，手工编辑无效**；校验判据见文末 [REGEN]。
#
# 【口径作废 · 2026-11-20】此前 `COMMIT_RE` 把 ch7 期望串并进**并集**
#   （`ch6 …|ch7 …|阶段…`）→ ch6 模式下一条「ch7 A1 切片」commit 会被算成「今晚已交」
#   （ch7 模式下反向同理）＝双向假绿。现已按章隔离（ch6 模式只认 ch6 形态）。
#   → **并集口径下产出的任何「今晚已交」读数一律作废，不得再当证据**；本章只认按章隔离口径。
#   → 历史读数**不重算**（旧读数保留原样，仅作废、不再引用）。
#
# 【有意变更 · 2026-11-20 · 之一】[S5] 与参数化前的旧脚本不同：旧 NO_REPLY（假绿），
#   新判漏跑。其余状态与参数化前旧脚本逐字相同（旧/新 diff 仅此一处）。
#
# 【有意变更 · 2026-11-20 · 之二】v1.0 定稿判定收紧（commit 4623947）后新增 [V1]／[V2] 两条覆盖：
#   旧写法是子串匹配 ＋ `.` 未转义 → 「计划 <章> v1.0 的时间表」「<章> v1.05 排版」都会被当成
#   已定稿 → 整晚静默（假绿）。新口径：标题须以「<章> v1.0」或「Yomi: <章> v1.0」**开头**
#   ＋ 其后不是数字 ＋ 不含计划类词。[V1]／[V2] 冻结的正是这两种标题**不再**触发静默。
#   （[R4]／[R5] 用的是真实定稿标题「ch6 v1.0：…」，新口径下仍静默 → 读数未变。）
#
# 【生成环境】SLOT_DATE_OVERRIDE 固定槽日 ＋ 自建 stub cron 夹具 ＋ 历史 commit 工作树；
#   不读真实 cron、不写真实仓、不产生任何 commit。
#   ⚠️ [R5] 是**唯一**与墙钟有关的一条：它验的是「不在验收窗口就早退 NO_REPLY」，
#   而窗口判定读的是当前时刻（03:00–21:44 才真走到早退；窗内则因 v1.0 已定稿而静默）。
#   **两条路径的读数都是 NO_REPLY**，所以本文件在任何时刻生成都一致；但只有白天重生成时
#   才算真验到了早退分支。其余 13 条与生成时刻完全无关。
#
HDR

# ── 历史态（仓里真实 commit，用 git worktree 检出；不动历史）────────────
# 同一个 SHA 可能被多段用到（R4／R5 共用 465e6c8）→ 路径已存在则复用，别再 add（会失败）
wt() { local p="$T/wt-$1"
  if [ -d "$p" ]; then printf '%s' "$p"; return 0; fi
  if git -C "$clone" worktree add -q --detach "$p" "$1" 2>/dev/null; then printf '%s' "$p"; return 0; fi
  return 1; }
fail_wt() { echo "🔴 worktree 失败：找不到历史 commit $1（历史被改写／rebase 过？）" >&2; exit 1; }

d=$(wt 96a0ecf) || fail_wt 96a0ecf; hdr R1 "历史态 96a0ecf（11-18 20:18 · 六场齐 · sample+deslop 在 · 无 review · 无 v1.0）｜槽日 2026-11-19｜cron 夹具 ok×1"
emit_fixture "$OK1"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<96a0ecf 工作树> bash tracks/verify_daily_slice.sh  # 期望：🔴 异常（阶段3 待做）" </dev/null

d=$(wt 4ac23c4) || fail_wt 4ac23c4; hdr R2 "历史态 4ac23c4（11-20 00:11 · review 刚落仓，该 commit 在槽日窗口内）｜槽日 2026-11-19｜cron 夹具 ok×1"
emit_fixture "$OK1"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<4ac23c4 工作树> bash tracks/verify_daily_slice.sh  # 期望：NO_REPLY（评审 commit 本身落在窗口内 → 已算当日交付）"

d=$(wt 8cec218) || fail_wt 8cec218; hdr R3 "历史态 8cec218（11-17 21:31 · B3 当晚交付）｜槽日 2026-11-17｜cron 夹具 ok×1"
emit_fixture "$OK1"; run "$d" 2026-11-17 "CHAPTER=ch6 DRY_RUN=1 REPO=<8cec218 工作树> bash tracks/verify_daily_slice.sh  # 期望：NO_REPLY（当日有切片 commit）"

d=$(wt 465e6c8) || fail_wt 465e6c8; hdr R4 "历史态 465e6c8（11-20 09:28 · ch6 已 v1.0 定稿）｜槽日 2026-11-19｜cron 夹具 ok×1"
emit_fixture "$OK1"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<465e6c8 工作树> bash tracks/verify_daily_slice.sh  # 期望：NO_REPLY（v1.0 静默）"

d=$(wt 465e6c8) || fail_wt 465e6c8; hdr R5 "同 R4 工作树，但**默认窗口**（不设 SLOT_DATE_OVERRIDE）｜cron 夹具 ok×1 —— 验「不在窗口就早退」；窗内/窗外两条路径的读数都是 NO_REPLY，故本条与生成时刻无关（详见文件头【生成环境】）"
emit_fixture "$OK1"
[ -n "$d" ] && [ -d "$d" ] || { echo "🔴 R5: 工作树为空" >&2; exit 1; }
out=$(env REPO="$d" CHAPTER=ch6 bash "$VERIFY" 2>&1); ec=$?
printf '$ CHAPTER=ch6 REPO=<465e6c8 工作树> bash tracks/verify_daily_slice.sh  # 期望：NO_REPLY（不在验收窗口）\n%s\n[exit %s]\n\n' "$out" "$ec"

# ── 合成态（空 repo；状态在历史里不可达，或需要夹具）──────────────────
mk() { local p="$T/syn-$1"; rm -rf "$p"; mkdir -p "$p/manuscripts" "$p/tracks"
       git -C "$p" init -q; git -C "$p" config user.email t@e.com; git -C "$p" config user.name t
       printf '%s' "$p"; }
cm() { local d=$1 m=$2 dt=$3; git -C "$d" add -A >/dev/null 2>&1
       ( cd "$d" && GIT_AUTHOR_DATE="$dt" GIT_COMMITTER_DATE="$dt" git commit -q --allow-empty -m "$m" ); }
six() { local d=$1 ch=$2 s; for s in A1 B1 A2 B2 A3 B3; do echo 正文 > "$d/manuscripts/$ch-$s.md"; done; }
IN="2026-11-19T10:00:00+09:00"; BEFORE="2026-11-18T10:00:00+09:00"

d=$(mk s1); hdr S1 "合成态 · 切片期零产物 · 零 cron 条目｜槽日 2026-11-19"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S1> bash tracks/verify_daily_slice.sh  # 期望：漏跑（切片 A1）"

d=$(mk s2); six "$d" ch6; hdr S2 "合成态 · 六场齐、无 sample · 零 cron 条目｜槽日 2026-11-19"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S2> bash tracks/verify_daily_slice.sh  # 期望：漏跑（阶段1 合成）"

d=$(mk s3); six "$d" ch6; echo s > "$d/manuscripts/ch6-sample.md"
hdr S3 "合成态 · 六场齐+sample、无 deslop 报告 · 零 cron 条目｜槽日 2026-11-19"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S3> bash tracks/verify_daily_slice.sh  # 期望：漏跑（阶段2 去 AI 味）"

d=$(mk s4); hdr S4 "合成态 · 零产物、cron 条目为 **error**（槽被宿主掐掉）｜槽日 2026-11-19"
emit_fixture "$ERR1"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S4> bash tracks/verify_daily_slice.sh  # 期望：漏跑＋槽被掐"

d=$(mk s5); six "$d" ch6; cm "$d" "Yomi: ch6 B3 切片 — 收束" "$BEFORE"; cm "$d" "Yomi: ch7 A1 切片 — 门与铃" "$IN"
hdr S5 "合成态 · 六场齐、无 sample · 窗口内**只有一条 ch7 A1 切片** commit · 零 cron 条目｜槽日 2026-11-19 —— 【有意变更·之一】旧＝NO_REPLY 假绿，新＝不数"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S5> bash tracks/verify_daily_slice.sh  # 期望：漏跑（ch7 commit 不算 ch6 交付）"

d=$(mk s6); cm "$d" "Yomi: ch6 A1 切片 — 门" "$BEFORE"
hdr S6 "合成态 · ch6 切片 commit 落在**窗口外**（11-18 10:00，槽日 11-19）· 零 cron 条目｜槽日 2026-11-19"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S6> bash tracks/verify_daily_slice.sh  # 期望：漏跑（窗口纪律）"

d=$(mk s7); six "$d" ch6; echo s > "$d/manuscripts/ch6-sample.md"; echo r > "$d/tracks/ch6-deslop-report.md"; echo rv > "$d/tracks/ch6-review.md"
cm "$d" "Yomi: ch6 B3 切片 — 收束" "$BEFORE"
hdr S7 "合成态 · 六场齐+sample+deslop+**review 在**、窗口内 0 commit、「评审已落」态｜槽日 2026-11-19"
emit_fixture "$OK1"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 S7> bash tracks/verify_daily_slice.sh  # 期望：ℹ️ 阶段3 已落（按⑤并行锁，0 commit 属预期）"

# ── v1.0 定稿判定收紧（4623947）的覆盖：两种「看起来像定稿」的标题 ──────────
d=$(mk v1); six "$d" ch6; cm "$d" "tracks(ch6): 计划 ch6 v1.0 的时间表" "$BEFORE"
hdr V1 "合成态 · 六场齐 · 历史里只有**计划类**标题「tracks(ch6): 计划 ch6 v1.0 的时间表」· 零 cron 条目｜槽日 2026-11-19 —— 【有意变更·之二】旧＝NO_REPLY 整晚静默，新＝不静默、按阶段判"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 V1> bash tracks/verify_daily_slice.sh  # 期望：漏跑（计划类标题不算定稿）"

d=$(mk v2); six "$d" ch6; cm "$d" "ch6 v1.05 排版" "$BEFORE"
hdr V2 "合成态 · 六场齐 · 历史里只有「ch6 v1.05 排版」（v1.0 后面跟数字）· 零 cron 条目｜槽日 2026-11-19 —— 【有意变更·之二】旧＝NO_REPLY 整晚静默，新＝不静默、按阶段判"
emit_fixture "$NONE"; run "$d" 2026-11-19 "CHAPTER=ch6 DRY_RUN=1 REPO=<合成态 V2> bash tracks/verify_daily_slice.sh  # 期望：漏跑（v1.05 ≠ v1.0 定稿）"

cat <<'FTR'
===== [REGEN] 重新生成与本文件的校验 =====
# 生成器：tracks/verify_daily_slice_baseline.sh（本文件的唯一来源；它只读被测脚本，不改它）
# 生成器做的事：
#   1) mktemp；写 stub `openclaw`（只 cat 夹具 JSON）并前插 PATH → 不读真实 cron
#   2) git clone 真仓到临时目录；历史态用 `git worktree add --detach <sha>` → 不动历史、不产 commit
#   3) 合成态：/tmp 空 repo + 只 touch 必需文件；commit 用 GIT_AUTHOR_DATE/GIT_COMMITTER_DATE 钉死
#   4) 每态执行：REPO=<dir> CHAPTER=ch6 SLOT_DATE_OVERRIDE=<slot> DRY_RUN=1 bash tracks/verify_daily_slice.sh
#   5) cron 夹具：ok×1   = {"entries":[{"runAtIso":"2026-11-19T21:30:00.015+09:00","status":"ok"}]}
#                  error×1 同上换 "status":"error"；零条目 = {"entries":[]}
#
# 校验（应该只输出 CH6_BASELINE_IDENTICAL）：
#   diff <(bash tracks/verify_daily_slice_baseline.sh) tracks/verify_daily_slice_baseline_ch6.txt \
#     && echo CH6_BASELINE_IDENTICAL
#
# 重冻（确实改了被测脚本、并确认新读数正确之后才做）：
#   bash tracks/verify_daily_slice_baseline.sh > tracks/verify_daily_slice_baseline_ch6.txt
FTR
