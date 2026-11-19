#!/bin/zsh
# ch6 v1.0 复审链 —— 对应 tracks/ch6-review-merge.md §八
#
# 用法：
#   zsh tracks/ch6_review_chain.sh [<sha>]        # 跑全链（退出码非 0 = 有门禁红）
#   zsh tracks/ch6_review_chain.sh --prove        # 只跑负向自测（证明判据能失败）
#
# 纪律：
#   * **必须在仓库根就地跑** —— deslop 白名单在 manuscripts/.deslop-whitelist，
#     复制到别处跑会误报 blocking。
#   * 改稿方与复审方跑**同一条命令**：判据落仓（tracks/ch6_body_checks.py），
#     不靠会话里的口头约定。
#   * 结论回给认可记录那一方（tracks/ch6-v1.0-acceptance.md 由 Mico 出）。
#   * 本链只读 + 重合成；compose.py 若产出与仓库不一致，会如实报 FAIL（不自动改写）。

set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
LOG=/tmp/ch6-review-chain.log
SHA=""
PROVE=0
for a in "$@"; do
  case "$a" in
    --prove) PROVE=1 ;;
    *) SHA="$a" ;;
  esac
done

if [ "$PROVE" = "1" ]; then
  python3 tracks/ch6_body_checks.py --prove
  rc1=$?
  echo ""
  python3 tracks/ch5_frozen_check.py --prove
  rc2=$?
  echo ""
  echo "=== 负向自测汇总：body_checks=$rc1 · ch5_frozen=$rc2 ==="
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

{
echo "=== ch6 复审链 $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
echo "repo : $REPO"
echo "HEAD : $(git log --oneline -1)"
echo "目标 : ${SHA:-<未指定，用 HEAD>}"
echo "dirty: $(git status --porcelain | wc -l | tr -d ' ') 个文件"

step "[0] 目标 commit（grep 'ch6 v1.0'）" git log --oneline --grep="ch6 v1.0"
step "[1a] check.py（合成稿）" python3 tracks/check.py manuscripts/ch6-sample.md
step "[1b] check_theme.py（六场切片）" python3 tracks/check_theme.py manuscripts/ch6-A1.md manuscripts/ch6-A2.md manuscripts/ch6-A3.md manuscripts/ch6-B1.md manuscripts/ch6-B2.md manuscripts/ch6-B3.md
step "[1c] check_line_totals.py --chapter ch6" python3 tracks/check_line_totals.py --chapter ch6
step "[1d] deslop_scan.py --chapter ch6" python3 tracks/deslop_scan.py --chapter ch6
step "[1e] verify_factsource.py" python3 tracks/verify_factsource.py
step "[1f] projection.py" python3 tracks/projection.py
step "[2] ngram_scan.py --chapter ch6（跨章硬门禁必须 0 命中）" python3 tracks/ngram_scan.py --chapter ch6

echo ""
echo "--- [3] compose.py ch6 → manuscripts/ 必须无 diff（重合成逐字节一致）---"
python3 tracks/compose.py ch6
echo "compose exit=$?"
DIFF=$(git status --porcelain manuscripts/)
if [ -z "$DIFF" ]; then
  echo "[OK] manuscripts/ 无 diff（重合成逐字节一致）"
else
  echo "[FAIL] manuscripts/ 有 diff:"; echo "$DIFF"; FAIL=1
fi

echo ""
echo "--- [4] 正文段口径门禁（§八 item 7／8，判据落仓在 tracks/ch6_body_checks.py）---"
python3 tracks/ch6_body_checks.py
rc=$?
echo "exit=$rc"
if [ $rc -ne 0 ]; then FAIL=1; fi

echo ""
echo "--- [5] ch5 冻结门禁（§八 item 5 后半：ch5 一个字未改 —— 机器判据）---"
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
