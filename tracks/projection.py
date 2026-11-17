#!/usr/bin/env python3
"""全书体量投影（2026-11-18 立）——**用脚本算，不许口算**。

为什么有它（Mico 2026-11-18 00:10 的血训）：
    Mico 把全书投影口算成「≈ 16.8 万」，实算是 **16.16 万**（差 6,400 字）→
    结论没变（都超 plan-v2 §8「13–16 万」上沿），但**数字错了**。
    这与 2026-11-13「体量必须用各章实测值、不能拿一章章长套全书」是同一族错误，
    只是这次错在**加总环节**而不是取值环节。
    → 与 R48 同族：**红线与算术必须落在仓库侧的脚本里**，不能活在任何人的脑子/聊天里。

口径（与 `tracks/check.py` 完全一致，**同函数复用**，不另起炉灶）：
    正文汉字（U+4E00–U+9FFF）＝ `check.py` 的正文段切法（切片/分线标题行 → 「## 写作说明」前）。
    ch1–ch5 取已定稿合成稿 `manuscripts/ch<N>-sample.md`；
    ch6 取 `manuscripts/ch6-sample.md`（合成后）；未合成时退回**六场切片正文合计**并标注。
    未来章（ch7–ch20）按**地板** 8,400/章（`line_rules.FLOORS['ch6']['total']`）。

带子（上下沿）**从 `outline/plan-v2.md` §8 现场解析**，不写死 → owner 改带子后脚本自动跟随：
    「20 章 × 6–8 千字 ≈ 13–16 万字」 → 130,000–160,000。

用法（在项目根目录）：
    python3 tracks/projection.py             # 打印全部投影（退出码 0；超带子只报 WARN）
    python3 tracks/projection.py --strict    # 超带子 → 退出码 1（作闸门用）

退出码：0 = 正常（可能带 WARN：超带子）；1 = 仅在 --strict 且超带子时。
"""

import pathlib
import re
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as ck  # noqa: E402  —— 复用正文段切法与汉字口径（唯一定义在 check.py）
import line_rules as lr  # noqa: E402  —— 地板口径

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAN = ROOT / "outline" / "plan-v2.md"
TOTAL_CHAPTERS = 20
# 节奏投影只用「双线成型的近端章」（ch1 1,869／ch2 5,769 是短篇集结构，不属常态节奏）
RHYTHM_CHAPTERS = ["ch3", "ch4", "ch5", "ch6"]


def body_hanzi(path):
    """单文件正文汉字合计（与 check.py 同口径）。"""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return sum(len(ck.HANZI.findall(body)) for _, body, _ in ck.slice_bodies(text))


def measure_chapter(chapter):
    """实测一章的字数。返回 (字数, 来源说明) 或 None（该章尚无稿）。"""
    n = chapter[2:]
    sample = ROOT / "manuscripts" / f"{chapter}-sample.md"
    if sample.exists():
        return body_hanzi(sample), f"{sample.name}（合成稿）"
    slices = sorted((ROOT / "manuscripts").glob(f"{chapter}-*.md"))
    if slices:
        total = sum(body_hanzi(p) for p in slices)
        return total, "＋".join(p.name.replace(".md", "") for p in slices) + "（切片合计，尚未合成）"
    return None


def parse_band():
    """从 plan-v2 §8 解析体量带子（万 → 字）。找不到 → 返回 None。"""
    text = PLAN.read_text(encoding="utf-8")
    m = re.search(r"(\d+)\s*[–\-~]\s*(\d+)\s*万字", text)
    if not m:
        return None
    return int(m.group(1)) * 10000, int(m.group(2)) * 10000


def main():
    strict = "--strict" in sys.argv
    band = parse_band()
    floor = lr.FLOORS["ch6"]["total"]

    print("=== 全书体量投影（脚本实测，不口算）===")
    measured = {}
    for i in range(1, TOTAL_CHAPTERS + 1):
        chapter = f"ch{i}"
        got = measure_chapter(chapter)
        if got is None:
            if i <= 6:
                print(f"  · {chapter}  —— 无稿")
            continue
        value, src = got
        measured[chapter] = value
        tag = "" if i <= 6 else "（未来章，按地板推算）"
        print(f"  · {chapter}  {value:>7,}  {src}{tag}")

    done = {k: v for k, v in measured.items() if int(k[2:]) <= 6}
    subtotal = sum(done.values())
    rest = TOTAL_CHAPTERS - len(done)
    floor_total = subtotal + rest * floor

    print(f"\n  已定稿章合计（ch1–ch{len(done)}）  {subtotal:,}")
    print(f"  未来 {rest} 章 × 地板 {floor:,}       {rest * floor:,}")
    print(f"  ▸ 地板投影（最低口径）             {floor_total:,}")

    rhythm_vals = [measured[c] for c in RHYTHM_CHAPTERS if c in measured]
    rhythm_mean = statistics.mean(rhythm_vals) if rhythm_vals else floor
    rhythm_total = subtotal + rest * rhythm_mean
    print(f"  ▸ 节奏投影（均值 {rhythm_mean:,.0f}／章，取自 {' '.join(RHYTHM_CHAPTERS)}）  {rhythm_total:,}")

    if band:
        lo, hi = band
        print(f"\n  plan-v2 §8 带子：{lo:,}–{hi:,}")
        for label, total in (("地板投影", floor_total), ("节奏投影", rhythm_total)):
            if total > hi:
                print(f"  [WARN] {label} {total:,} → **超上沿 {total - hi:,} 字**")
            elif total < lo:
                print(f"  [WARN] {label} {total:,} → 低于下沿 {lo - total:,} 字")
            else:
                print(f"  [OK  ] {label} {total:,} → 落在带内")
        print("  📌 带子口径（① 8,400/章不动带子 ② 改 §8 带子）**待 owner（Luminary）拍板**；")
        print("     本脚本只报事实，不改 plan-v2。")
        if strict and floor_total > hi:
            print("\n[FAIL] 地板投影超 plan-v2 §8 上沿（--strict）")
            return 1
    else:
        print("  ⚠️ 未能在 plan-v2 §8 解析出体量带子 → 不判带内/超限")

    print("\n[OK  ] 投影计算完成（退出码 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
