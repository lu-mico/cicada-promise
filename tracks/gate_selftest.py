#!/usr/bin/env python3
"""门禁自测（2026-11-12 补洞后）——**每条判据都必须先证明它「能失败」**。

**两份纪律（Mico 2026-11-12 09:44 / 10:47 / 14:39 钉）**：
1. **判据要先用「最容易被漏掉的写法」去攻击**：正常写法通过了不算修好。
   R44 主题句检查写的是字面串 `"时间是一种很危险的东西" in body`，而 ch1 原句被对话打断
   （`"时间，"他说，"是一种很危险的东西。"`）→ 该串在任何正文里都不存在
   → 「ch3–ch7 禁第三句」**自 ch1 起从未生效**。
2. **每条测试都要先证明它「能失败」**：一个永远不会失败的校验等于没有校验。
   本文件提供 `--prove`：把判据**换成旧版坏的**，整套用例必须变红——
   变不红就说明这些用例是摆设（而不是「通过了」）。

同族第二颗雷（R45）：粗判据两头出错——「三十多岁」这种年龄被当成三十年破线（误伤 ch1 已认可的
原句），而「二十九年」「多少年」这种真跨度**根本没查**（漏网）。
同族第三颗雷（R46）：窗口太窄（`.{0,8}`）＋主语锚定单一（只有「时间」）→ 长节拍中断与换主语写法
从两个门禁的缝里滑过去。

用法：
    python3 tracks/gate_selftest.py           # 跑全套用例（须全过，退出码 0）
    python3 tracks/gate_selftest.py --prove   # 证明「用例能失败」：换旧判据，整套必须变红
退出码：0 = 通过；1 = 有用例失败（或 --prove 未变红）。
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import theme_rules as tr  # noqa: E402
import span_rules as sr  # noqa: E402

# ── 主题句用例（negative case：喂必然违规的句子，断言「必须命中」）───────────
# 前 6 条＝已交付写法回归；后 12 条＝**攻击用**（最容易漏的写法）。
THEME_CASES = [
    ("ch1 原句（对话打断）", '　"时间，"他说，"是一种很危险的东西。"', True, 1),
    ("连续写法", '　他说时间是一种很危险的东西。', True, 3),
    ("ch2 降级句", '　时间不是被记住的, 是被用掉的。', True, 3),
    ("引号内同句（ch2 式）", '　"——\'时间是一种很危险的东西\'。"', True, 2),
    ("干净句（不得误报）", '　她把纸边对齐，抹了两遍，扣好搭扣。', False, 3),
    # ── R46 漏网点 A：对话插入长一点就全漏（带情绪节拍的中断）──
    ("漏网点 A（长节拍中断）", '　"时间，"他停了一下，把书合上，"是一种很危险的东西。"', True, 3),
    # ── R46 漏网点 B：换主语（字面式原本锚死在「时间」）──
    ("漏网点 B（换主语·记忆）", '　"记忆，"他说，"是一种很危险的东西。"', True, 3),
    ("漏网点 B（换主语·遗忘）", '　"遗忘，"他说，"是一种很危险的东西。"', True, 3),
    ("漏网点 B（换主语·孤独）", '　"孤独，"他说，"是一种很危险的东西。"', True, 3),
    ("漏网点 B（换主语·命运）", '　"命运，"他说，"是一种很危险的东西。"', True, 3),
    ("少一个「很」", '　他说时间是一种危险的东西。', True, 3),
    ("极长中断（三十字）", '　"时间，"他把窗推开又关上，屋里只剩钟走的声音，"是一种很危险的东西。"', True, 3),
    # ── 换词复活旧句（Mico 10:47 钉）：ch2 被删那句「时间不是被记住的，是被用掉的」，
    #    改成「是拿来用的」＝原句复活，只换三个字 → 必须 ERROR 层命中。──
    ("换词复活·拿来用", '　时间是拿来用的。', True, 3),
    ("换词复活·拿来用（对话打断）", '　"时间，"他说，"是拿来用的。"', True, 3),
    ("换词复活·被用掉", '　时间被用掉了。', True, 3),
    ("换词复活·原句（ch2 被删那一句）", '　时间不是被记住的，是被用掉的。', True, 3),
]

# ── 结构候选用例（评审兜底层）──────────────────────────────────────────────
STRUCT_CASES = [
    ("结构候选（抽象名词作主语）", '　他说，记忆是一种债。'),
    ("结构候选（长节拍中断）", '　"时间，"他停了一下，把书合上，"是一种很危险的东西。"'),
    ("结构候选（换主语）", '　"记忆，"他说，"是一种很危险的东西。"'),
    ("结构候选（时间+是，非危险尾串）", '　时间是拿来用的。'),
]

# ── 年数跨度用例（rule 4）──────────────────────────────────────────────────
SPAN_CASES = [
    ("三十年（跨度）", '　三十年过去了。', True),
    ("三十年前（跨度）", '　这封信是三十年前写的。', True),
    ("三十多年（跨度）", '　他记着三十多年前的事。', True),
    ("三十七年前（跨度）", '　三十七年前那场案子。', True),
    ("二十九年（跨度）", '　差着二十九年。', True),
    ("多少年（跨度）", '　他不肯说多少年了。', True),
    ("三十来年（跨度）", '　三十来年前他还是个学徒。', True),
    ("快三十年（跨度）", '　快三十年没人提起过。', True),
    ("三十年光景（跨度）", '　那是三十年前光景。', True),
    ("三十多岁（年龄，应放行）", '　镜子里映出一个三十多岁的男人。', False),
    ("三十岁（年龄，应放行）", '　她那年三十岁。', False),
    ("三十来岁（年龄，应放行）", '　一个三十来岁的人。', False),
    ("三十出头（年龄，应放行）", '　三十出头的年纪。', False),
    ("三十七分（时刻，应放行）", '　钟面停在三十七分。', False),
    ("他今年三十岁了（年龄，应放行）", '　他今年三十岁了。', False),
    ("干净句（不得误报）", '　她把纸边对齐，抹了两遍。', False),
]


def run_suite(verbose=True):
    """跑全套用例，返回失败用例名列表。"""
    failed = []

    def check(name, cond, detail=""):
        if verbose:
            mark = "OK  " if cond else "FAIL"
            print(f"  [{mark}] {name}" + (f" —— {detail}" if detail and not cond else ""))
        if not cond:
            failed.append(name)

    if verbose:
        print("=== 主题句（ch3–ch7 禁第三句）===")
    for name, body, expect, chap in THEME_CASES:
        hits = tr.theme_hits(body)
        check(name + "（字面命中）", bool(hits) == expect, f"实际命中={hits}")
        banned = tr.banned_for(chap)
        check(name + f"（章 {chap} 门禁={'禁' if banned else '允许'}）",
              banned == (chap is None or chap >= 3))

    if verbose:
        print("=== 结构候选（评审兜底）===")
    for name, body in STRUCT_CASES:
        cands = tr.abstract_candidates(body)
        check(name, bool(cands), f"候选={cands}")

    if verbose:
        print("=== 作用域（正文段口径）===")
    doc = """# 样例

| 8 | 📝 主题句 | ch1「时间是一种很危险的东西」已立 |

## A1 · 测试

正文里没有那句话。

## 写作说明

| 主题句 | ch1「时间是一种很危险的东西」已立 |
"""
    bodies = tr.slice_bodies(doc)
    check("作用域（写作说明区不入正文）",
          len(bodies) == 1 and not tr.theme_hits(bodies[0][2]),
          f"bodies={[(b[0], b[2][:20]) for b in bodies]}")
    check("作用域（顶部规划表不入正文）",
          len(bodies) == 1 and "已立" not in bodies[0][2],
          f"body={bodies[0][2][:40] if bodies else None}")

    if verbose:
        print("=== 年数跨度（rule 4，禁「三十年」式推算）===")
    for name, body, expect in SPAN_CASES:
        hits = sr.span_mentions(body)
        check(name, bool(hits) == expect, f"实际命中={hits}")

    return failed


# R44 时代的坏判据（字面串，从未成立）——用来证明用例能变红
BROKEN_THEME = [re.compile(r"时间是一种很危险的东西")]
# R46 时代的坏判据（窄窗口 + 单一主语）
BROKEN_NARROW = [re.compile(r"时间.{0,8}是一种很危险的东西")]


def prove_can_fail():
    """把判据换成旧的坏版本，整套用例**必须变红**——不变红就说明用例是摆设。"""
    print("=== 证明用例「能失败」（Mico 2026-11-12 10:47 钉）===")
    original_theme = tr.THEME_PATTERNS
    original_span = sr._SPAN_PATTERNS
    ok = True
    try:
        tr.THEME_PATTERNS = BROKEN_THEME
        failed = run_suite(verbose=False)
        print(f"  旧判据（R44 字面串）下失败用例数：{len(failed)}")
        if not failed:
            print("  [FAIL] 换成 R44 的坏判据后用例仍全绿 → 这些用例是摆设！")
            ok = False
        else:
            print(f"  [OK  ] 用例会变红（如：{failed[0]}）——证明它们真在检验判据")

        tr.THEME_PATTERNS = BROKEN_NARROW
        failed2 = run_suite(verbose=False)
        print(f"  旧判据（R46 窄窗口）下失败用例数：{len(failed2)}")
        if not failed2:
            print("  [FAIL] 换成 R46 的坏判据后用例仍全绿 → 漏网点用例缺失！")
            ok = False
        else:
            print(f"  [OK  ] 用例会变红（如：{failed2[0]}）——证明漏网点用例真在检验")

        sr._SPAN_PATTERNS = [re.compile(r"三十")]
        failed3 = run_suite(verbose=False)
        print(f"  旧判据（R45 粗 count）下失败用例数：{len(failed3)}")
        if not failed3:
            print("  [FAIL] 换成 R45 的坏判据后用例仍全绿 → 年龄放行用例缺失！")
            ok = False
        else:
            print(f"  [OK  ] 用例会变红（如：{failed3[0]}）——证明年龄放行用例真在检验")
    finally:
        tr.THEME_PATTERNS = original_theme
        sr._SPAN_PATTERNS = original_span
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if args and args[0] == "--prove":
        return prove_can_fail()
    failed = run_suite(verbose=True)
    print(f"\n{'全部通过' if not failed else '失败用例：' + '、'.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
