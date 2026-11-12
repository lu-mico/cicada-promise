#!/usr/bin/env python3
"""门禁自测（2026-11-12 补洞后）——**每条判据都必须有「喂已知真实句子」的自测**。

**为什么有这份文件**：主题句检查写的是字面串 `"时间是一种很危险的东西" in body`，
而 ch1 原句被对话打断（`"时间，"他说，"是一种很危险的东西。"`）→ 该串在任何正文里都不存在
→ 「ch3–ch7 禁第三句」**自 ch1 起从未生效**（Mico 2026-11-12 09:44 指出）。
同理，「三十」那条粗规则把**年龄说法**（「三十多岁」）也当成年数破线。
**新纪律：判据不配自测，就等于装得像在工作。**

用法：python3 tracks/gate_selftest.py
退出码：0 = 全部通过；1 = 有用例失败。
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import theme_rules as tr  # noqa: E402
import span_rules as sr  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    mark = "OK  " if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" —— {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


print("=== 门禁自测：主题句（ch3–ch7 禁第三句）===")

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
]

for name, body, expect, chap in THEME_CASES:
    hits = tr.theme_hits(body)
    check(name + "（字面命中）", bool(hits) == expect, f"实际命中={hits}")
    banned = tr.banned_for(chap)
    check(name + f"（章 {chap} 门禁={'禁' if banned else '允许'}）",
          banned == (chap is None or chap >= 3))

cands = tr.abstract_candidates('　他说，记忆是一种债。')
check("结构候选（抽象名词作主语）", bool(cands), f"候选={cands}")

# R46：长节拍中断也必须进结构候选（不能两层都看不见）
cands_a = tr.abstract_candidates('　"时间，"他停了一下，把书合上，"是一种很危险的东西。"')
check("结构候选（长节拍中断）", bool(cands_a), f"候选={cands_a}")
cands_b = tr.abstract_candidates('　"记忆，"他说，"是一种很危险的东西。"')
check("结构候选（换主语）", bool(cands_b), f"候选={cands_b}")
cands_c = tr.abstract_candidates('　时间是拿来用的。')
check("结构候选（时间+是，非危险尾串）", bool(cands_c), f"候选={cands_c}")

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

print("=== 门禁自测：年数跨度（rule 4，禁「三十年」式推算）===")

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

for name, body, expect in SPAN_CASES:
    hits = sr.span_mentions(body)
    check(name, bool(hits) == expect, f"实际命中={hits}")

print(f"\n{'全部通过' if not FAILED else '失败用例：' + '、'.join(FAILED)}")
sys.exit(1 if FAILED else 0)
