#!/usr/bin/env python3
"""线级字数闸门（2026-11-14 立）——A 线 / B 线 / 全章合计的**仓库侧**硬闸。

为什么有它（与 R48 同族：红线必须落在仓库侧的脚本里）：
    线级合计（A ≥ 4,100／B ≥ 4,300／全章 ≥ 8,400；ch3／ch4 为 4,000／4,000／8,000）
    此前**只活在 Mico 那侧的验收脚本里**，仓库侧 `tracks/check.py` 只报**单场**字数、
    **不判线级合计** → 同一个病：切片级守住的东西，到章级合成／阶段 3 评审／v1.0 就没人守。
    （ch3-done.md §五把「双线字数达标」判据说成 `check.py` 可验，其实 check.py 只打印不断言。）

口径：**正文汉字**（U+4E00–U+9FFF），与 `tracks/check.py` 完全一致（同函数复用，不另起炉灶）。

硬闸只判**线级与全章**（既定教义：「线级合计是硬闸，单场下沿让位」）；
单场区间只报 WARN —— 单场是量纲，线级才是合同。

三道口径裁定（改这里必须同步 `tracks/ch6-daily.md`）：
    ① A 线**只认下限 4,100**：上沿 4,300 已不可达（A1 1,595 ＋ A2 1,598 ＝ 3,193，
       A3 按 Mico 2026-11-14 22:08 预批 1,300–1,700 → A 线 4,493–4,893；
       ch5 实测 A 4,889 也早已越顶）→ 上沿不作闸门，只作历史注记。
    ② A3 单场区间 **1,300–1,700**（Mico 2026-11-14 22:08 预批，取代 2026-11-12 的
       「A3 硬上限 1,600」）——**且不得为凑 A 线而缩**（A 线只要 A3 ≥ 907 即过 4,100）。
    ③ B 线 ≥ 4,300 底线不变（ch4 的 B 线只剩 65 字余量，ch5 起改 4,300，不赌余量）。
"""

import re

# 章级线级口径（**只有下限**）。上沿一律不设闸。
FLOORS = {
    "ch3": {"a": 4000, "b": 4000, "total": 8000},
    "ch4": {"a": 4000, "b": 4000, "total": 8000},
    "ch5": {"a": 4100, "b": 4300, "total": 8400},
    "ch6": {"a": 4100, "b": 4300, "total": 8400},
    # ch7（2026-11-20 立，tracks/ch7-daily.md「八之二」D10）：沿用 ch6 四个数字，**只认下限**。
    # 无此条时 analyze() 走「无线级口径 → 只报数不判闸」→ A 线 0 字也印 [OK]（G2 假绿）。
    "ch7": {"a": 4100, "b": 4300, "total": 8400},
    # ch8（2026-11-24 立，tracks/ch8-daily.md「八之二」D10）：沿用 ch6／ch7 四个数字，**只认下限**。
    # 无此条时 analyze() 走「无线级口径 → 只报数不判闸」→ A 线 0 字也印 [OK]（G7 假绿）。
    "ch8": {"a": 4100, "b": 4300, "total": 8400},
}

# 各章场次名册（用于「还差多少／还差几场」推算）。
ROSTERS = {
    "ch3": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch4": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch5": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch6": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch7": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch8": ["A1", "A2", "A3", "B1", "B2", "B3"],
}

# 交付顺序（＝ `tracks/compose.py` 各章配置的 `order`；ch3 是 A 线整块在前，ch4 起交错）。
# 用途：交稿顺序闸 —— 「选片规则＝第一个尚不存在的场」⇒ 已交场次必须是本表的前缀集合。
# 与 ROSTERS 分开是因为 ROSTERS 只是名册（用于算缺口），不是交付次序。
DELIVERY = {
    "ch3": ["A1", "A2", "A3", "B1", "B2", "B3"],
    "ch4": ["A1", "B1", "A2", "B2", "A3", "B3"],
    "ch5": ["A1", "B1", "A2", "B2", "A3", "B3"],
    "ch6": ["A1", "B1", "A2", "B2", "A3", "B3"],
    "ch7": ["A1", "B1", "A2", "B2", "A3", "B3"],
    "ch8": ["A1", "B1", "A2", "B2", "A3", "B3"],
}

# 单场实操区间（只报 WARN，不作硬闸）。
PER_SCENE = {
    "ch6": {"A": (1300, 1700), "B": (1434, 1600)},
    # ch7：A3 的 1,300–1,700 预批带**不预先续用**（D10）→ A 线按 1,367–1,600 的实操区间报 WARN。
    "ch7": {"A": (1367, 1600), "B": (1434, 1600)},
    # ch8（2026-11-24 立）：沿用 ch7 的两个区间；**B3（全书第一次亡者叙述）不预先给带子**
    # → 不足时在 B1／B2 补（B 线合计是硬闸），不许为凑 B3 拉长亡者叙述（D10）。
    "ch8": {"A": (1367, 1600), "B": (1434, 1600)},
}

# 坏判据（`gate_selftest.py --prove` 用）：永远放行 → 用例必须变红。
BROKEN_FLOORS = {}
BROKEN_PER_SCENE = {}


def norm_chapter(chapter):
    """章号归一：6 / '6' / 'ch6' 一律 → 'ch6'（口径表的键是 'chN'）。"""
    if chapter is None:
        return None
    if isinstance(chapter, int):
        return f"ch{chapter}"
    s = str(chapter).strip()
    if s.isdigit():
        return f"ch{s}"
    return s.lower()


def line_of(label):
    """从场景标题切出所属线：「A2 · 另一份纸（周睿视角，2026）」→ 「A」。"""
    m = re.match(r"^\s*([AB])\s*(\d*)", label)
    if not m:
        return "?"
    return m.group(1)


def analyze(scenes, chapter, floors=None, per_scene=None, rosters=None, delivery=None):
    """判线级合计 + 全章合计 + 单场区间 + 剩余缺口推算。

    scenes: [(场景标签, 正文汉字数), ...]
    返回 dict：errors（硬闸破线）／warns（提示）／info（口径与缺口）
    """
    floors = FLOORS if floors is None else floors
    per_scene = PER_SCENE if per_scene is None else per_scene
    rosters = ROSTERS if rosters is None else rosters
    delivery = DELIVERY if delivery is None else delivery
    chapter = norm_chapter(chapter)

    errors, warns, info = [], [], []
    totals = {"A": 0, "B": 0}
    total = 0
    present = []
    bands = per_scene.get(chapter, {})

    for label, hanzi in scenes:
        total += hanzi
        sid = re.match(r"^\s*([AB]\d*)", label)
        present.append(sid.group(1) if sid else label.split("·")[0].strip())
        ln = line_of(label)
        if ln in totals:
            totals[ln] += hanzi
        else:
            warns.append(f"{label}: 标题无法归线（既非 A 也非 B）→ 未计入线级合计")
        band = bands.get(ln)
        if band:
            lo, hi = band
            if hanzi < lo:
                warns.append(f"{label}: 单场 {hanzi} 低于实操下沿 {lo}（单场下沿让位，线级才是硬闸）")
            elif hanzi > hi:
                warns.append(f"{label}: 单场 {hanzi} 高于实操上沿 {hi}（余量别赌）")

    rule = floors.get(chapter)
    if not rule:
        warns.append(
            f"{chapter}: 仓库侧无线级口径 → 只报数不判闸"
            f"（实际 A {totals['A']}／B {totals['B']}／全章 {total}）"
        )
        return {"errors": errors, "warns": warns, "info": info, "missing": []}

    roster = rosters.get(chapter, [])
    missing = [s for s in roster if s not in present]

    # 交稿顺序闸（2026-11-20 补，G2 同族）：选片规则是「切片表顺序里第一个尚不存在的场」
    #   （tracks/ch7-daily.md §二）→ **已交场次必须构成名册的前缀集合**。
    #   跳场（例：B1／B2／B3 已交而 A1 未交）不是「写到一半」，是**量错了对象**：
    #   此时线级合计无从判定，若只报 PENDING／缺口，就会退化成「A 线 0 字也放行」。
    order = delivery.get(chapter) or roster
    if order and set(present) <= set(order) and len(set(present)) < len(order):
        n = len(set(present))
        if set(present) != set(order[:n]):
            errors.append(
                f"交稿顺序异常：已交 {('、'.join(sorted(set(present))))} 不构成名册前缀"
                f"（按交付顺序应为 {('、'.join(order[:n]))}）→ 线级合计无法判定（跳场交付）"
            )

    info.append(
        f"{chapter} 线级实测：A {totals['A']}／B {totals['B']}／全章 {total}"
        f"（底线 A {rule['a']}／B {rule['b']}／全章 {rule['total']}）"
    )

    for ln, key in (("A", "a"), ("B", "b")):
        need = rule[key] - totals[ln]
        if need <= 0:
            info.append(f"{ln} 线已达底线（余 {totals[ln] - rule[key]}）")
            continue
        left = [s for s in missing if s.startswith(ln)]
        if not left:
            errors.append(
                f"{ln} 线合计 {totals[ln]} < 底线 {rule[key]}，且已无剩余场次可补"
            )
        else:
            info.append(
                f"{ln} 线还差 {need} 字，由剩余场次 {('、'.join(left))} 承担"
                f"（{len(left)} 场均摊 ≥ {need // len(left)}）"
            )

    if not missing:
        if total < rule["total"]:
            errors.append(f"全章合计 {total} < 底线 {rule['total']}")
        else:
            info.append(f"全章已达底线（余 {total - rule['total']}）")
    else:
        info.append(
            f"尚未齐章（缺 {('、'.join(missing))}）→ 全章合计闸门待六场齐后判定"
        )

    return {"errors": errors, "warns": warns, "info": info, "missing": missing}
