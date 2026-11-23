#!/usr/bin/env python3
"""ch8 **整章级**判据（2026-11-24 · tracks/ch8-daily.md「八之二」D2）。

**为什么需要它（2026-11-24 peer 实测抓到的洞）**：
`tracks/check.py` 是**逐切片**跑的 → `ch8_rules.ch8_hits()` 也是**逐场**判的。
而 D2 的口径是**整章只许 1 次**「三十年前」→ 作者跨六天写六场，**每场各写一次**时，
**每场门禁全绿、整章却超了上限** → **跨场必须累加后判**。

**它查什么**（只查**正文段** —— 写作说明区与顶部抬头一律不入正文段，
否则「禁项复核：无林默」这类说明行会被当成破线 → 罚合格稿）：
  ① D2：整章 A 线「三十年前」**合计 ≤ 1 次**；整章 B 线 **0 次**。
  ② D1／D4：整章任何正文段出现「林默」 → 判红。
  ③ D7：整章任何正文段出现「胸针」 → 判红。

**用法**：
  python3 tracks/ch8_chapter_checks.py             # 扫 manuscripts/ch8-*.md
  python3 tracks/ch8_chapter_checks.py --selftest  # 自测（含**跨切片**负向用例）
  python3 tracks/ch8_chapter_checks.py --prove     # 证明用例能失败（换成不查的坏判据）
  python3 tracks/ch8_chapter_checks.py --nightly   # 夜间槽用：**只在破线时说话**（干净 → NO_REPLY）
退出码：0 = 通过；1 = 有破（或 --prove 未变红）。
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tracks"))

import check as ck  # noqa: E402  —— 正文段口径复用（不另起炉灶）
import ch8_rules as ch8r  # noqa: E402

SLICE_RE = re.compile(r"^ch8-[AB]\d+\.md$")


def collect():
    """读 ch8 各切片，取正文段 → [(标签, 正文段, 是否 B 线), ...]"""
    scenes = []
    mdir = ROOT / "manuscripts"
    for p in sorted(mdir.glob("ch8-*.md")):
        if not SLICE_RE.match(p.name):
            continue
        text = p.read_text(encoding="utf-8")
        for title, body, _body_no_head in ck.slice_bodies(text):
            is_b = bool(re.match(r"^B", title))
            scenes.append((f"{p.name}·{title}", body, is_b))
    return scenes


def run(verbose=True):
    scenes = collect()
    errs, warns = ch8r.chapter_hits(scenes)
    if verbose:
        print("=== ch8 整章级判据（D2 跨切片累加 · D1／D7 整章扫）===")
        if not scenes:
            print("  [ERROR] 没有 ch8-*.md 切片 → 无可聚合的正文段（**零切片 ≠ 通过**，ch7 G3 同款）")
        for label, _body, is_b in scenes:
            print(f"  · {label}（{'B' if is_b else 'A'} 线）")
        a_span = sum(b.count(ch8r.ALLOWED_PHRASE) for _l, b, is_b in scenes if not is_b)
        b_span = sum(b.count(ch8r.ALLOWED_PHRASE) for _l, b, is_b in scenes if is_b)
        print(f"  整章 A 线「{ch8r.ALLOWED_PHRASE}」合计 {a_span} 次（上限 1）· B 线 {b_span} 次（上限 0）")
        for e in errs:
            print(f"  [ERROR] {e}")
        for w in warns:
            print(f"  [WARN] {w}")
        if not errs and scenes:
            print("  [OK] 整章级判据通过")
    if not scenes:
        errs = errs or ["零切片：没有 ch8-*.md → 无可聚合的正文段（判红）"]
    return errs


# ── 自测用例（负向为主）────────────────────────────────────────────────────
# 结构：(名称, [(标签, 正文, 是否 B 线), ...], 应当报错)
SELFTEST_CASES = [
    ("跨切片·两条 A 线各 1 次「三十年前」→ 必须红",
     [("ch8-A1.md·A1", "　那封信是三十年前写的。", False),
      ("ch8-A3.md·A3", "　又是三十年前的事。", False)], True),
    ("单切片·A 线 1 次「三十年前」→ 必须绿",
     [("ch8-A1.md·A1", "　那封信是三十年前写的。", False)], False),
    ("单切片·A 线 2 次「三十年前」→ 必须红",
     [("ch8-A3.md·A3", "　那是三十年前的案子。也是三十年前的。", False)], True),
    ("B 线 1 次「三十年前」→ 必须红",
     [("ch8-B1.md·B1", "　她记得三十年前的事。", True)], True),
    ("任一切片出现「林默」→ 必须红",
     [("ch8-A2.md·A2", "　林默站在门口。", False)], True),
    ("任一切片出现「胸针」→ 必须红",
     [("ch8-A1.md·A1", "　桌上放着一枚胸针。", False)], True),
    ("干净章 → 必须绿",
     [("ch8-A1.md·A1", "　她把纸边对齐，抹了两遍。", False),
      ("ch8-B1.md·B1", "　母亲把帘子拉上一半。", True)], False),
]


def nightly(verbose=True):
    """夜间槽口径：**只在破线时说话**（干净 → 印 NO_REPLY＝静默）。"""
    scenes = collect()
    errs, warns = ch8r.chapter_hits(scenes)
    if not scenes:
        # 零切片：**不假警报**（夜里 22:05 若一章都还没交，交付检查会报，不必这里再报一次）
        if verbose:
            print("NO_REPLY")
        return []
    if not errs:
        if verbose:
            print("NO_REPLY")
        return []
    if verbose:
        for e in errs:
            print(f"[ERROR] {e}")
        for w in warns:
            print(f"[WARN] {w}")
    return errs


def selftest(verbose=True):
    failed = []
    for name, scenes, expect_err in SELFTEST_CASES:
        errs, _w = ch8r.chapter_hits(scenes)
        got = bool(errs)
        if verbose:
            print(f"  [{'OK  ' if got == expect_err else 'FAIL'}] {name}"
                  + ("" if got == expect_err else f" —— 实际报错={errs}"))
        if got != expect_err:
            failed.append(name)
    if verbose:
        print("全部通过" if not failed else f"失败 {len(failed)} 条")
    return failed


def prove():
    """换成「不查」的坏判据 → 用例必须变红（证明用例真在检验）。"""
    original = ch8r.ENABLED
    try:
        ch8r.ENABLED = ch8r.BROKEN_ENABLED
        failed = selftest(verbose=False)
        print(f"  旧判据（整章不查）下失败用例数：{len(failed)}")
        if not failed:
            print("  [FAIL] 换成坏判据后用例仍全绿 → 用例是摆设！")
            return 1
        print(f"  [OK  ] 用例会变红（如：{failed[0]}）——证明跨切片用例真在检验")
        return 0
    finally:
        ch8r.ENABLED = original


def main():
    args = sys.argv[1:]
    if "--prove" in args:
        print("=== 证明 ch8 整章级用例「能失败」===")
        return prove()
    if "--nightly" in args:
        nightly()
        return 0
    if "--selftest" in args:
        print("=== ch8 整章级判据自测 ===")
        return 0 if not selftest() else 1
    errs = run()
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
