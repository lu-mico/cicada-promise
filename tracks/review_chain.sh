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
# 📌 **按章参数化（2026-11-24 · G11a）**：CHAPTER 未设 → ch7（**ch7 模式的读数与参数化前逐字相同**）。
#    为什么要参数化（承 ch7 G5 的教训）：原来这条链**整份写死 ch7** → 拿它验 ch8 ＝ **验的不是本章**。
#    现在同一份链按 CHAPTER 走，ch7／ch8 各跑各的章。
CHAPTER="${CHAPTER:-ch7}"
case "$CHAPTER" in
  ch[0-9]|ch[0-9][0-9]) ;;
  *) echo "🔴 复审链参数错：CHAPTER=$CHAPTER（形如 ch7／ch8）"; exit 1 ;;
esac
LOG=/tmp/${CHAPTER}-review-chain.log
SHA=""
PROVE=0
for a in "$@"; do
  case "$a" in
    --prove) PROVE=1 ;;
    *) SHA="$a" ;;
  esac
done

if [ "$PROVE" = "1" ]; then
  rc1=0
  if [ -f "tracks/${CHAPTER}_body_checks.py" ]; then
    python3 tracks/${CHAPTER}_body_checks.py --prove
    rc1=$?
  else
    echo "⚠️ 本章无 tracks/${CHAPTER}_body_checks.py —— **尚未落仓**（期望值要等本章合格稿实测，G11b）"
    echo "   → 本链**不完整**：--prove 通过不代表本章可复审"
    rc1=1
  fi
  echo ""
  rc3=0
  if [ -f "tracks/${CHAPTER}_chapter_checks.py" ]; then
    python3 tracks/${CHAPTER}_chapter_checks.py --prove
    rc3=$?
  fi
  echo ""
  python3 tracks/ch5_frozen_check.py --prove
  rc2=$?
  echo ""
  echo "=== 负向自测汇总：${CHAPTER}_body_checks=$rc1 · ${CHAPTER}_chapter_checks=$rc3 · ch5_frozen=$rc2 ==="
  [ $rc1 -eq 0 ] && [ $rc2 -eq 0 ] && [ $rc3 -eq 0 ]
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
# [0] 定稿 commit：**必须带 sha**（复审规矩＝拿定稿 sha 跑）。
#     为什么改成必须带（2026-11-24 · peer 抓的洞）：原来 sha 只是**标签**——
#     链里真正做门禁的是 `git log --grep "<章> v1.0"`（扫全历史）→ 不传 sha 时
#     它照样能“绿”，而打印的「目标 : <未指定，用 HEAD>」**与实际行为不符**
#     （实际取的是最近一笔标题匹配的 commit，不是 HEAD）→ **「忘了传 sha 也绿着过」
#     是最危险的那种绿**（判据罚不到人，还让人以为验过了）。
#     现在：**不传 sha → 直接判红**；传了 → **门禁就判那一笔**（sha 的 subject 须是
#     「<章> v1.0」，且排除 v1.0.1）。历史匹配列表只作信息附上。
check_final_commit() {
  local hits matched sha_line sha_subj
  if [ -z "$SHA" ]; then
    echo "🔴 未传定稿 sha —— 本步直接判红"
    echo "   用法：${CHAPTER} 复审链必须带 sha：zsh tracks/review_chain.sh <定稿sha>"
    echo "   （理由：sha 只当标签时，「忘了传 sha」也能绿过＝最危险的那种绿）"
    echo "exit=1"
    FAIL=1
    return 0
  fi
  sha_line=$(git log -1 --format='%h %s' "$SHA" 2>/dev/null || true)
  if [ -z "$sha_line" ]; then
    echo "🔴 找不到 sha $SHA —— 本步判红"
    echo "exit=1"
    FAIL=1
    return 0
  fi
  sha_subj="${sha_line#* }"
  hits=$(git log --format='%h %s' --grep="${CHAPTER} v1.0")
  matched=$(printf '%s\n' "$hits" | grep -E "${CHAPTER} v1\.0([^0-9.]|$)" || true)
  if [ -z "$matched" ]; then
    if [ -n "$hits" ]; then
      echo "（正文提到过 ${CHAPTER} v1.0、但没有 subject 是定稿的 commit：）"
      printf '%s\n' "$hits" | sed 's/^/  · /'
    fi
    echo "（本章无「${CHAPTER} v1.0」定稿 commit —— 本章尚未定稿，预期红）"
    echo "exit=1"
    FAIL=1
    return 0
  fi
  if printf '%s\n' "$sha_subj" | grep -qE "${CHAPTER} v1\.0([^0-9.]|$)"; then
    echo "目标 sha：$sha_line"
    echo "（本章标题为定稿的 commit：）"
    printf '%s\n' "$matched" | sed 's/^/  · /'
    echo "exit=0"
  else
    echo "🔴 给定 sha $SHA 的 subject 不是本章定稿：$sha_subj"
    echo "   （本章标题为定稿的 commit：）"
    printf '%s\n' "$matched" | sed 's/^/  · /'
    echo "exit=1"
    FAIL=1
  fi
}

{
echo "=== ${CHAPTER} 复审链 $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
echo "repo : $REPO"
echo "HEAD : $(git log --oneline -1)"
echo "目标 : ${SHA:-<未传 → [0] 判红>}"
echo "dirty: $(git status --porcelain | wc -l | tr -d ' ') 个文件"

echo ""
echo "--- [0] 目标 commit（grep '${CHAPTER} v1.0'）---"
check_final_commit

step "[1a] check.py（合成稿）" python3 tracks/check.py manuscripts/${CHAPTER}-sample.md
step "[1b] check_theme.py（六场切片）" python3 tracks/check_theme.py manuscripts/${CHAPTER}-A1.md manuscripts/${CHAPTER}-A2.md manuscripts/${CHAPTER}-A3.md manuscripts/${CHAPTER}-B1.md manuscripts/${CHAPTER}-B2.md manuscripts/${CHAPTER}-B3.md
step "[1c] check_line_totals.py --chapter ${CHAPTER}" python3 tracks/check_line_totals.py --chapter ${CHAPTER}
step "[1d] deslop_scan.py --chapter ${CHAPTER}" python3 tracks/deslop_scan.py --chapter ${CHAPTER}
step "[1e] verify_factsource.py（事实源单向）" python3 tracks/verify_factsource.py
step "[1f] projection.py（体量投影，advisory）" python3 tracks/projection.py
step "[2] ngram_scan.py --chapter ${CHAPTER}（跨章硬门禁必须 0 命中）" python3 tracks/ngram_scan.py --chapter ${CHAPTER}

echo ""
echo "--- [2b] 整章级判据（跨切片累加 · 有才跑；缺则本链不完整，见 [4]）---"
if [ -f "tracks/${CHAPTER}_chapter_checks.py" ]; then
  python3 tracks/${CHAPTER}_chapter_checks.py
  rc=$?
  echo "exit=$rc"
  if [ $rc -ne 0 ]; then FAIL=1; fi
else
  echo "（本章无 tracks/${CHAPTER}_chapter_checks.py —— 本章无整章级判据）"
fi

echo ""
echo "--- [3] compose.py ${CHAPTER} → manuscripts/ 必须无 diff（重合成逐字节一致）---"
python3 tracks/compose.py ${CHAPTER}
rc=$?
echo "compose exit=$rc"
if [ $rc -ne 0 ]; then
  echo "[FAIL] compose.py ${CHAPTER} 退出码非 0 —— 本章稿件不是可合成的状态"
  FAIL=1
fi
# ⚠️ 只看**本章**的稿件：别章正在写的切片不该让本章判红
DIFF=$(git status --porcelain -- "manuscripts/${CHAPTER}-*.md" "manuscripts/${CHAPTER}-sample.md")
OTHER=$(git status --porcelain -- manuscripts/ | grep -v "manuscripts/${CHAPTER}-" || true)
if [ -z "$DIFF" ]; then
  echo "[OK] 本章稿件无 diff（重合成逐字节一致）"
else
  echo "[FAIL] 本章稿件有 diff:"; echo "$DIFF"; FAIL=1
fi
if [ -n "$OTHER" ]; then
  echo "[提示] manuscripts/ 下**别章**的在写文件（不计入本章判定）："; echo "$OTHER"
fi

echo ""
echo "--- [4] 正文段口径门禁（判据落仓在 tracks/${CHAPTER}_body_checks.py）---"
if [ -f "tracks/${CHAPTER}_body_checks.py" ]; then
  python3 tracks/${CHAPTER}_body_checks.py
  rc=$?
  echo "exit=$rc"
  if [ $rc -ne 0 ]; then FAIL=1; fi
else
  echo "[FAIL] tracks/${CHAPTER}_body_checks.py **尚未落仓** —— 本章的正文段口径门禁缺失"
  echo "       （**期望值必须在本章合格稿上实测后再落仓**，不能先写死措辞）"
  echo "       → 本链**不完整**：不得把本链的绿当本章的通过结论"
  FAIL=1
fi

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
