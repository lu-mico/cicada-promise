#!/usr/bin/env python3
"""线级字数闸门（仓库侧 · 2026-11-14 立）——A 线 / B 线 / 全章合计的**硬闸**。

为什么有它（R48 同族：红线必须落在仓库侧的脚本里）：
    线级合计（A ≥ 4,100／B ≥ 4,300／全章 ≥ 8,400；ch3／ch4 为 4,000／4,000／8,000）
    此前**只活在 Mico 那侧的验收脚本里**；仓库侧 `tracks/check.py` 只报**单场**字数、
    **不判线级合计**（ch3-done.md §五把「双线字数达标」判据说成 check.py 可验，其实它只打印不断言）
    → 切片级守住的东西，到章级合成／阶段 3 评审／v1.0 就没人守。

用法（项目根目录）：
    python3 tracks/check_line_totals.py manuscripts/ch6-A1.md manuscripts/ch6-A2.md ...
    python3 tracks/check_line_totals.py manuscripts/ch6-sample.md
    python3 tracks/check_line_totals.py --chapter ch6     # 自动收该章所有已交切片（写作端最常用）
    # 还没交齐时也给「还差多少、由哪场承担」（写作端的算盘）

口径：**正文汉字**（U+4E00–U+9FFF），与 `tracks/check.py` 完全一致（复用同一套切段函数，不另起炉灶）。
退出码：0 = 通过；1 = 有硬闸破线（WARN 不影响退出码）。
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as ck            # noqa: E402 —— 复用 slice_bodies / HANZI（口径唯一定义）
import line_rules as lr       # noqa: E402 —— 线级口径与判据

import re


def collect(paths):
    """从切片文件或章级合成稿里取出 [(场景标签, 正文汉字数)]。"""
    scenes, seen = [], {}
    for p in paths:
        text = pathlib.Path(p).read_text(encoding="utf-8")
        for title, body, _ in ck.slice_bodies(text):
            n = len(ck.HANZI.findall(body))
            sid = re.match(r"^\s*([AB]\d*)", title)
            sid = sid.group(1) if sid else title.strip()
            if sid in seen:
                print(f"  [ERROR] 场景 {sid} 出现两次（{seen[sid]} 与 {p}）→ 疑似重复计入口径")
            seen[sid] = p
            scenes.append((title, n))
    return scenes, seen


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    chapter = None
    paths = []
    if args[0] in ("-c", "--chapter"):
        chapter = ck.tr.chapter_of(args[1])
        if not chapter:
            print(f"  [ERROR] 无法从 {args[1]} 读出章号")
            return 1
        paths = sorted(str(p) for p in pathlib.Path("manuscripts").glob(f"ch{chapter}-*.md"))
        paths = [p for p in paths if "sample" not in p]
        if not paths:
            print(f"  [ERROR] manuscripts/ 下没有 ch{chapter}-*.md 切片")
            return 1
    else:
        paths = args
        for p in paths:
            chapter = ck.tr.chapter_of(p)
            if chapter:
                break
    scenes, _ = collect(paths)
    if not scenes:
        print("  [ERROR] 找不到正文段（既没有「## A1 ·」也没有「## A 线 ·」）")
        print("\n合计 ERROR 1 项")
        return 1

    print(f"\n=== 线级字数闸门（章 ch{chapter}）===")
    for title, n in scenes:
        print(f"  · {title}  正文汉字 {n}")

    res = lr.analyze(scenes, chapter)
    for i in res["info"]:
        print(f"  [INFO] {i}")
    for w in res["warns"]:
        print(f"  [WARN] {w}")
    for e in res["errors"]:
        print(f"  [ERROR] {e}")
    if not res["errors"]:
        print("  [OK  ] 线级合计闸门通过")
    print(f"\n合计 ERROR {len(res['errors'])} 项")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
