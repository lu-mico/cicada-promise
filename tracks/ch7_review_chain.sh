#!/bin/zsh
# ch7 v1.0 复审链 —— 对应 tracks/ch7-daily.md §八之五（唯一对照表）＋ §七 交付流程
#
# 用法：
#   zsh tracks/ch7_review_chain.sh [<sha>]        # 跑全链（退出码非 0 = 有门禁红）
#   zsh tracks/ch7_review_chain.sh --prove        # 只跑负向自测（证明判据能失败）
#
# 纪律（照抄 ch6 链）：
#   * **必须在仓库根就地跑** —— deslop 白名单在 manuscripts/.deslop-whitelist，
#     复制到别处跑会误报 blocking。
#   * 改稿方与复审方跑**同一条命令**：判据落仓（tracks/ch7_body_checks.py），
#     不靠会话里的口头约定。
#   * 结论回给认可记录那一方（tracks/ch7-v1.0-acceptance.md 由主编 Mico 出）。
#   * 本链只读 + 重合成；compose.py 若产出与仓库不一致，会如实报 FAIL（不自动改写）。
#   * [0] 是**真门禁**（不是单纯 git log）：无 `ch7 v1.0` commit 时 exit=1
#     （ch6 链的 grep 步在无匹配时 git 仍返回 0，等于「红不了」；这里补上）。
#   * [3] 只看**本章**稿件：别章正在写的切片不得让本章判红（照抄 ch6 纪律）。
#   * **期望值是「口径锁」，不是永久常量**：tracks/ch7_body_checks.py 头部的实测值
#     来源＝最近一次实测（2026-11-23，HEAD 50e92d7，六场齐）。作者的改稿落地后，
#     由主编当场重测并更新期望值（落仓＋附记录），再让复审方跑链；
#     → **复审方看到红，先对表上的日期与 HEAD，不要先假定作者写错**。

set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
LOG=/tmp/ch7-review-chain.log
SHA=""
PROVE=0
for a in "$@"; do
  case "$a" in
    --prove) PROVE=1 ;;
    *) SHA="$a" ;;
  esac
done

if [ "$PROVE" = "1" ]; then
  python3 tracks/ch7_body_checks.py --prove
  rc1=$?
  echo ""
  python3 tracks/ch5_frozen_check.py --prove
  rc2=$?
  echo ""
  echo "=== 负向自测汇总：ch7_body_checks=$rc1 · ch5_frozen=$rc2 ==="
  [ $rc1 -eq 0 ] && [ $rc2 -eq 0 ]
  exit $?
fi

FAIL=0
step() {
  # step <名称> <命令...>
  local name="$1"; shift
  echo ""
  echo "--- $name ---"
  "$@"
  local rc=$?
  echo "exit=$rc"
  if [ $rc -ne 0 ]; then FAIL=1; fi
  return 0
}

# [0] 定稿 commit：subject 必须含「ch7 v1.0」（无命中 = 红）。
#     为什么不能只用 `git log --oneline --grep`：--grep 也搜**正文**，历史上几支
#     工具类提交的正文里讨论过「ch7 v1.0」→ 会假绿。这里加一道 subject 过滤；
#     并且排除 v1.0.1（定稿版必须是 v1.0，期望串不放宽）。
check_final_commit() {
  local hits matched
  hits=$(git log --format='%h %s' --grep="ch7 v1.0")
  matched=$(printf '%s\n' "$hits" | grep -E 'ch7 v1\.0([^0-9]|$)' || true)
  if [ -z "$matched" ]; then
    if [ -n "$hits" ]; then
      echo "（正文提到过 ch7 v1.0、但没有 subject 是定稿的 commit：）"
      printf '%s\n' "$hits" | sed 's/^/  · /'
    fi
    echo "（无「ch7 v1.0」定稿 commit —— 本章尚未定稿，预期红）"
    echo "exit=1"
    FAIL=1
  else
    printf '%s\n' "$matched"
    echo "exit=0"
  fi
}

{
echo "=== ch7 复审链 $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
echo "repo : $REPO"
echo "HEAD : $(git log --oneline -1)"
echo "目标 : ${SHA:-<未指定，用 HEAD>}"
echo "dirty: $(git status --porcelain | wc -l | tr -d ' ') 个文件"

echo ""
echo "--- [0] 目标 commit（grep 'ch7 v1.0'）---"
check_final_commit

step "[1a] check.py（合成稿）" python3 tracks/check.py manuscripts/ch7-sample.md
step "[1b] check_theme.py（六场切片）" python3 tracks/check_theme.py manuscripts/ch7-A1.md manuscripts/ch7-A2.md manuscripts/ch7-A3.md manuscripts/ch7-B1.md manuscripts/ch7-B2.md manuscripts/ch7-B3.md
step "[1c] check_line_totals.py --chapter ch7" python3 tracks/check_line_totals.py --chapter ch7
step "[1d] deslop_scan.py --chapter ch7" python3 tracks/deslop_scan.py --chapter ch7
step "[1e] verify_factsource.py（事实源单向：ch7-daily §三 ＝ ch6-notes §三）" python3 tracks/verify_factsource.py
step "[1f] projection.py（体量投影，advisory）" python3 tracks/projection.py
step "[2] ngram_scan.py --chapter ch7（跨章硬门禁必须 0 命中）" python3 tracks/ngram_scan.py --chapter ch7

echo ""
echo "--- [3] compose.py ch7 → manuscripts/ 必须无 diff（重合成逐字节一致）---"
python3 tracks/compose.py ch7
echo "compose exit=$?"
# ⚠️ 只看**本章**的稿件：别章正在写的切片不该让 ch7 判红
DIFF=$(git status --porcelain -- 'manuscripts/ch7-*.md' 'manuscripts/ch7-sample.md')
OTHER=$(git status --porcelain -- manuscripts/ | grep -v "manuscripts/ch7-" || true)
if [ -z "$DIFF" ]; then
  echo "[OK] 本章稿件无 diff（重合成逐字节一致）"
else
  echo "[FAIL] 本章稿件有 diff:"; echo "$DIFF"; FAIL=1
fi
if [ -n "$OTHER" ]; then
  echo "[提示] manuscripts/ 下**别章**的在写文件（不计入本章判定）："; echo "$OTHER"
fi

echo ""
echo "--- [4] 正文段口径门禁（D1／D3／D4 ＋ B 线红线，判据落仓在 tracks/ch7_body_checks.py）---"
python3 tracks/ch7_body_checks.py
rc=$?
echo "exit=$rc"
if [ $rc -ne 0 ]; then FAIL=1; fi

echo ""
echo "--- [5] ch5 冻结门禁（ch5 一个字未改 —— 原样复用 tracks/ch5_frozen_check.py）---"
python3 tracks/ch5_frozen_check.py
rc=$?
echo "exit=$rc"
if [ $rc -ne 0 ]; then FAIL=1; fi

echo ""
echo "=== 汇总 ==="
if [ $FAIL -eq 0 ]; then
  echo "[PASS] 全链绿"
else
  echo "[FAIL] 有门禁红 —— 见上面 exit≠0 的小节"
fi
echo "EXITCODE=$FAIL"
echo "=== 链跑完 $(date '+%H:%M:%S') ==="
} 2>&1 | tee "$LOG"

# ⚠️ 上面那个 `{ } | tee` 是**子 shell** → 里面的 FAIL 传不到这里 → 退出码必须
#    从日志里读回 verdict 行（否则「门禁红但退出码 0」，白跑）。
grep -q "^EXITCODE=0$" "$LOG"
exit $?
