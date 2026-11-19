#!/usr/bin/env python3
"""ch5 冻结门禁 —— ch6 复审链 §八 item 5 后半「**ch5 一个字未改**」的机器判据。

为什么要有这个文件（2026-11-20，认可记录方 Mico）：
    §八 item 5 要求「M4 若采用 → 核 ch5-A2:161 与 ch6 的落差在 A3 兑现，**且 ch5 一个字
    未改**」。但「ch5 一个字未改」此前**只有人在会话里口头讲**，没有可复现命令
    → 纪律 9 的同类洞（判据只活在会话里 → 改稿方与复审方都没有同一把尺子）。

基线（为什么是它）：
    `e1ed9ef` = **ch5 v1.0 认可记录** commit（「Mico: ch5 v1.0 认可记录 — 五条判据全过
    （对象 7abe232）」）。它只新增 `tracks/ch5-v1.0-acceptance.md`，**没碰任何稿件**；
    被它认可的 ch5 定稿对象是 `7abe232`（「ch5 v1.0 定稿候选」）。
    → 以 `e1ed9ef` 为基线做 `base..HEAD` 的比对，等于问「ch5 定稿之后有人碰过 ch5 吗」。

判定（四条，任一红即 FAIL）：
    1. 基线存在，且是 HEAD 的祖先（否则基线失效，例如历史被 rebase／reset）；
    2. `git diff --stat base..HEAD -- manuscripts/ch5-*.md` **为空** → ch5 正文一字未改；
    3. `git log --oneline base..HEAD -- manuscripts/ch5-*.md` **为空** → 没人碰过 ch5 文件
       （**「改了又改回」也算碰过** —— 那种情况 diff 看不出来，但 log 会留下两条提交；
       注意：**内容完全一致根本不会产生提交**，git 会报 nothing to commit，所以这一条
       抓的不是「空提交」，而是「碰过并改回」）；
    4. `git status --porcelain -- manuscripts/ch5-*.md` **为空** → 工作树里没有未提交的
       ch5 改动（未提交的内容 `base..HEAD` 比不出来，这条专堵这个洞）。

用法：
    python3 tracks/ch5_frozen_check.py                    # 跑门禁（退出码非 0 = FAIL）
    python3 tracks/ch5_frozen_check.py --baseline <sha>   # 换基线
    python3 tracks/ch5_frozen_check.py --prove            # 负向自测（临时仓，不碰工作树）
退出码：0 = 通过；1 = 有项失败。
"""

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = "e1ed9ef"  # ch5 v1.0 认可记录 commit（认可对象 = 7abe232）
PATTERN = "manuscripts/ch5-*.md"
# M4 落差起点（advisory，只打印给人看，不拦）：ch5 的「未结」必须在 ch6 的 A3 兑现
M4_FROM = ("manuscripts/ch5-A2.md", "附卷：治安，未结")
M4_TO = ("manuscripts/ch6-A2.md", "结案")


def git(repo, *args):
    p = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def gate(repo, baseline=DEFAULT_BASELINE, verbose=True):
    """返回 (是否通过, 失败原因列表)。"""
    repo = pathlib.Path(repo)
    bad = []

    # 1) 基线存在 + 是 HEAD 的祖先
    rc, _, err = git(repo, "cat-file", "-e", f"{baseline}^{{commit}}")
    if rc != 0:
        bad.append(f"基线 {baseline} 不存在（{err or 'cat-file 失败'}）")
    else:
        rc, _, _ = git(repo, "merge-base", "--is-ancestor", baseline, "HEAD")
        if rc != 0:
            bad.append(f"基线 {baseline} 不是 HEAD 的祖先 → 历史被 rebase／reset 过，基线失效")

    # 2) ch5 正文一字未改
    _, out, _ = git(repo, "diff", "--stat", f"{baseline}..HEAD", "--", PATTERN)
    if out:
        bad.append(f"ch5 稿件在 {baseline}..HEAD 之间**被改过**：\n{out}")

    # 3) 没人碰过 ch5 文件
    _, out, _ = git(repo, "log", "--oneline", f"{baseline}..HEAD", "--", PATTERN)
    if out:
        bad.append(f"有人碰过 ch5 文件（**改了又改回也算碰过** —— 这种 diff 看不出来）：\n{out}")

    # 4) 工作树里没有未提交的 ch5 改动
    _, out, _ = git(repo, "status", "--porcelain", "--", PATTERN)
    if out:
        bad.append(f"工作树里 ch5 有未提交改动（base..HEAD 比不出来，必须堵）：\n{out}")

    if verbose:
        print("── ch5 冻结门禁（§八 item 5 后半：ch5 一个字未改）──")
        print(f"  基线 {baseline}（ch5 v1.0 认可记录 commit）· 范围 {PATTERN}")
        if bad:
            for b in bad:
                print(f"  [FAIL] {b}")
        else:
            print("  [OK] ch5 一字未改（diff 空 · log 空 · 工作树干净）")
        _print_m4_advisory(repo)
    return (not bad), bad


def _print_m4_advisory(repo):
    """打印 M4 落差起点（advisory，不拦）：ch5 的「未结」与 ch6 的「结案」要扣在一起。"""
    print("  [提示] M4 落差起点（人工核对，不拦）：")
    for rel, needle in (M4_FROM, M4_TO):
        path = pathlib.Path(repo) / rel
        if not path.exists():
            print(f"    · {rel} 不存在")
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if needle in line:
                print(f"    · {rel}:{i} → {line.strip()[:70]}")
                break
        else:
            print(f"    · {rel} 里没找到「{needle}」（本项按人工核对）")


def prove_can_fail():
    """负向自测：证明每条判据**能失败**（临时 git 仓，不碰工作树）。"""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ch5_frozen_selftest_"))
    try:
        repo = tmp / "repo"
        (repo / "manuscripts").mkdir(parents=True)
        (repo / "tracks").mkdir(parents=True)
        git(repo.parent, "init", "-q", str(repo))
        git(repo, "config", "user.email", "selftest@local")
        git(repo, "config", "user.name", "selftest")
        (repo / "manuscripts" / "ch5-A2.md").write_text("附卷：治安，未结。\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "ch5 v1.0 定稿候选")
        base = git(repo, "rev-parse", "HEAD")[1]

        # 用例 1：只动 tracks/ → 必须**绿**
        (repo / "tracks" / "x.md").write_text("ok\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "动别的文件")
        ok1, _ = gate(repo, base, verbose=False)
        print(f"  [{'OK' if ok1 else 'FAIL'}] 用例1：只动非 ch5 文件 → 门禁判绿（必须绿）")

        # 用例 2：改 ch5 内容并提交 → 必须**红**
        (repo / "manuscripts" / "ch5-A2.md").write_text("附卷：治安，未结。改。\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "偷偷改 ch5")
        ok2, reasons = gate(repo, base, verbose=False)
        hit2 = any("被改过" in r for r in reasons)
        print(f"  [{'OK' if (not ok2 and hit2) else 'FAIL'}] 用例2：提交里改了 ch5 正文 → 门禁判红（必须红）")

        # 用例 3：**改了又改回**（diff 空、log 非空）→ 必须**红**（log 检查专抓这种）
        git(repo, "reset", "-q", "--hard", "HEAD~1")
        (repo / "manuscripts" / "ch5-A2.md").write_text("附卷：治安，未结。动过。\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "碰了 ch5")
        (repo / "manuscripts" / "ch5-A2.md").write_text("附卷：治安，未结。\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "改回 ch5")
        diff_empty = not git(repo, "diff", "--stat", f"{base}..HEAD", "--", PATTERN)[1]
        ok3, reasons = gate(repo, base, verbose=False)
        hit3 = any("有人碰过 ch5 文件" in r for r in reasons)
        print(
            f"  [{'OK' if (not ok3 and hit3 and diff_empty) else 'FAIL'}] 用例3：改了又改回"
            f"（diff 空 · log 有两条）→ 门禁判红（证明 log 检查抓得住「碰过就碰过」）"
        )

        # 用例 4：工作树里未提交的 ch5 改动 → 必须**红**（工作树检查）
        git(repo, "reset", "-q", "--hard", "HEAD~1")
        (repo / "manuscripts" / "ch5-A2.md").write_text("工作树里偷偷改了\n", encoding="utf-8")
        ok4, reasons = gate(repo, base, verbose=False)
        hit4 = any("未提交改动" in r for r in reasons)
        print(f"  [{'OK' if (not ok4 and hit4) else 'FAIL'}] 用例4：工作树里未提交的 ch5 改动 → 门禁判红（必须红）")

        # 用例 5：基线不是祖先（历史被 reset）→ 必须**红**
        git(repo, "reset", "-q", "--hard", "HEAD")
        git(repo, "commit", "-q", "--allow-empty", "-m", "无关提交")
        ok5, reasons = gate(repo, "0" * 40, verbose=False)
        hit5 = any("祖先" in r or "不存在" in r for r in reasons)
        print(f"  [{'OK' if (not ok5 and hit5) else 'FAIL'}] 用例5：基线无效（不存在／非祖先）→ 门禁判红（必须红）")

        results = [ok1, not ok2, not ok3, not ok4, not ok5]
        print(f"  → 负向自测{'全部通过' if all(results) else '有项失败'}")
        return all(results)
    finally:
        subprocess.run(["rm", "-rf", str(tmp)], check=False)


def main():
    args = sys.argv[1:]
    baseline = DEFAULT_BASELINE
    if args and args[0] == "--baseline":
        args = args[1:]
        baseline = args.pop(0)
    if args and args[0] == "--prove":
        print("── ch5 冻结门禁 · 负向自测（--prove）──")
        return 0 if prove_can_fail() else 1
    ok, _ = gate(ROOT, baseline)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
