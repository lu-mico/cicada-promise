#!/usr/bin/env python3
"""事实源单向核对（2026-11-12，Mico ⑨ 钉）。

五条不变式（任一破 = ERROR）：
1. **未被改写**：`tracks/ch5-daily.md` §三 自 ch6 立轨那版（commit 4b48a26）起**一字未改**
   —— 事实源单向：ch6 只读它，不得回写。
2. **逐字一致（轨道）**：`tracks/ch6-daily.md` §三 正文 ＝ `tracks/ch5-daily.md` §三 正文
   —— ch6 抄的是 ch5 的事实集，不是另立版本。
3. **逐字一致（章级 notes）**：`tracks/ch6-notes.md` §三 正文 ＝ `tracks/ch5-daily.md` §三 正文
   —— Mico ⑨ 验收单点名的那一处；两份抄本都在机器校验下，任何漂移立刻暴露。
4. **ch7 链（2026-11-20 立轨补上）**：`tracks/ch7-daily.md` §三 正文 ＝ `tracks/ch6-notes.md` §三 正文
   —— ch7 抄的是 ch6 的事实集，不是另立版本。
5. **ch7 章级 notes**：`tracks/ch7-notes.md` §三 正文 ＝ `tracks/ch7-daily.md` §三 正文
   —— 与 ch6 同一手势：轨道抄本与章级抄本都在机器校验下。
6. **ch8 链（2026-11-24 立轨补上）**：`tracks/ch8-daily.md` §三 正文 ＝ `tracks/ch7-notes.md` §三 正文
   —— ch8 抄的是 ch7 的事实集，不是另立版本。
7. **ch8 章级 notes**：`tracks/ch8-notes.md` §三 正文 ＝ `tracks/ch8-daily.md` §三 正文
   —— 与前几章同一手势。

用法：python3 tracks/verify_factsource.py
退出码：0 = 七条都成立；1 = 有破。
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CH5 = ROOT / "tracks" / "ch5-daily.md"
CH6 = ROOT / "tracks" / "ch6-daily.md"
CH7 = ROOT / "tracks" / "ch7-daily.md"
CH7_NOTES = ROOT / "tracks" / "ch7-notes.md"
CH8 = ROOT / "tracks" / "ch8-daily.md"
CH8_NOTES = ROOT / "tracks" / "ch8-notes.md"
BASELINE_COMMIT = "4b48a26"  # ch6 立轨那版（ch5-daily.md 当时的形态）


def sec3(text):
    """取 §三 **正文**（跳过标题行：标题行含各章自己的来源说明，不属事实集本体）。

    只比事实集本体，才能要求「ch6 抄本 ＝ ch5 原件 逐字相同」。
    """
    m = re.search(r"^##+\s*三、唯一事实源.*?\n(.*?)(?=^##+\s*四、|\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else None


def git_show(path, commit):
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main():
    cur5 = sec3(CH5.read_text(encoding="utf-8"))
    cur6 = sec3(CH6.read_text(encoding="utf-8"))
    notes = sec3((ROOT / "tracks" / "ch6-notes.md").read_text(encoding="utf-8"))
    base5 = git_show("tracks/ch5-daily.md", BASELINE_COMMIT)
    base5 = sec3(base5) if base5 else None

    cur7 = sec3(CH7.read_text(encoding="utf-8"))
    notes7 = sec3(CH7_NOTES.read_text(encoding="utf-8")) if CH7_NOTES.exists() else None

    ok_same_daily = bool(cur5 and cur6 and cur5.strip() == cur6.strip())
    ok_same_notes = bool(cur5 and notes and cur5.strip() == notes.strip())
    ok_untouched = bool(cur5 and base5 and cur5.strip() == base5.strip())
    # ch7 链（2026-11-20 立轨补上）：ch7 抄的是 ch6 的事实集，不是另立版本。
    ok_same_7daily = bool(cur6 and cur7 and cur6.strip() == cur7.strip())
    ok_same_7notes = bool(cur7 and notes7 and cur7.strip() == notes7.strip())

    cur8 = sec3(CH8.read_text(encoding="utf-8")) if CH8.exists() else None
    notes8 = sec3(CH8_NOTES.read_text(encoding="utf-8")) if CH8_NOTES.exists() else None
    # ch8 链（2026-11-24 立轨补上）：ch8 抄的是 ch7 的事实集，不是另立版本。
    ok_same_8daily = bool(cur7 and cur8 and cur7.strip() == cur8.strip())
    ok_same_8notes = bool(cur8 and notes8 and cur8.strip() == notes8.strip())

    print("=== 事实源单向核对 ===")
    print(f"  ① ch5-daily §三 自 {BASELINE_COMMIT} 起未被改写：{ok_untouched}")
    print(f"  ② ch6-daily §三 ＝ ch5-daily §三（逐字）：{ok_same_daily}")
    print(f"  ③ ch6-notes §三 ＝ ch5-daily §三（逐字）：{ok_same_notes}")
    print(f"  ④ ch7-daily §三 ＝ ch6-notes §三（逐字）：{ok_same_7daily}")
    print(f"  ⑤ ch7-notes §三 ＝ ch7-daily §三（逐字）：{ok_same_7notes}")
    print(f"  ⑥ ch8-daily §三 ＝ ch7-notes §三（逐字）：{ok_same_8daily}")
    print(f"  ⑦ ch8-notes §三 ＝ ch8-daily §三（逐字）：{ok_same_8notes}")
    if not ok_same_8daily:
        print("     → ch8 轨道抄本与 ch7 原件已分叉。")
    if not ok_same_8notes:
        print("     → ch8 章级 notes 抄本与 ch8 轨道已分叉（或 ch8-notes.md 尚未建立）。")
    if not ok_same_7daily:
        print("     → ch7 轨道抄本与 ch6 原件已分叉。")
    if not ok_same_7notes:
        print("     → ch7 章级 notes 抄本与 ch7 轨道已分叉（或 ch7-notes.md 尚未建立）。")
    if not ok_same_daily:
        print("     → 轨道抄本与原件已分叉。")
    if not ok_same_notes:
        print("     → 章级 notes 抄本与原件已分叉。")
    if not ok_untouched:
        print(f"     → ch5-daily.md §三 与 {BASELINE_COMMIT} 不一致：ch6 期间有人回写了事实源。")
    ok_all = (ok_same_daily and ok_same_notes and ok_untouched
              and ok_same_7daily and ok_same_7notes
              and ok_same_8daily and ok_same_8notes)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
