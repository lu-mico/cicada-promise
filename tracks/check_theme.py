#!/usr/bin/env python3
"""林默主题句专项检查（2026-11-12 补门禁洞）。

**为什么需要它**：旧判据 `"时间是一种很危险的东西" in body` **从 ch1 起从未成立**——
ch1 的原句被对话打断（`"时间，"他说，"是一种很危险的东西。"`），
字面串在正文里根本不存在 → 「ch3–ch7 禁第三句」这条限制**一直是空门禁**。
现改为**归一化后匹配**（去标点/引号/空白，对话插入 ≤8 字照样命中），
并按章号分级：ch1（立句）／ch2（降级）已交付允许，**ch3 起为 ERROR**。

**两条并行**（Mico 2026-11-12 09:44 钉）：
1. **字面回归**：上面那两句的归一化命中 —— 门禁可自动判定。
2. **结构规则**：正文里林默的对话出现**抽象名词作主语的判断句**
   （时间／记忆／遗忘／孤独／命运）→ 新第三句**无字可 grep**，门禁只**报候选**，
   **由评审兜底判定**（WARN 级，不阻断）。

用法：
    python3 tracks/check_theme.py manuscripts/ch6-A1.md [更多文件…]
    python3 tracks/check_theme.py --selftest     # 跑门禁自测（gate_selftest.py）
退出码：0 = 无违例；1 = 有 ERROR（禁章出现主题句字面）。
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import theme_rules as tr  # noqa: E402


def check_file(path):
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    chapter = tr.chapter_of(p.name)
    banned = tr.banned_for(chapter)
    print(f"\n=== {path} ===")
    print(f"  章号 {chapter}（主题句：{'禁（ch3 起）' if banned else '允许（ch1 立句／ch2 降级，已交付）'}）")
    errors, warns = [], []
    for title, _body, body_no_head in tr.slice_bodies(text):
        hits = tr.theme_hits(body_no_head)
        if hits:
            msg = f"{title}: 出现林默主题句原文 → {hits}"
            (errors if banned else warns).append(msg)
        cands = tr.abstract_candidates(body_no_head)
        if cands and banned:
            warns.append(f"{title}: 抽象名词作主语的判断句（候选，需评审判定是否第三句）→ {cands[:3]}")
    for e in errors:
        print(f"  [ERROR] {e}")
    for w in warns:
        print(f"  [WARN]  {w}")
    if not errors:
        print("  [OK] 主题句门禁通过" + ("（有候选待评审）" if warns else ""))
    return errors


def main():
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        import subprocess
        return subprocess.call([sys.executable, str(pathlib.Path(__file__).with_name("gate_selftest.py"))])
    if not args:
        print(__doc__)
        return 2
    all_errors = []
    for path in args:
        all_errors += check_file(path)
    print(f"\n合计 ERROR {len(all_errors)} 项")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
