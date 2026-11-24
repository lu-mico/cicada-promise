#!/usr/bin/env python3
"""去 AI 味检测归属扫描（2026-11-18 立）——**每场 blocking 落在哪一行，脚本说了算**。

为什么有它（Mico 2026-11-18 00:09 / 00:40 两版口头清单全错）：
    00:09 说「六场共 2 条 blocking：A1 一条 · B2 一条」；
    00:40 说「A1 与 B3 各带 1 条（A3/B1/B2 是 0）」。
    仓库实测（项目目录就地跑 detector，正文段口径）：
        **A1 1 · B1 1 · B2 1 ＝ 3 条**（A2／A3／B3 ＝ 0）。
    两版都**漏了 B1**，第二版还把 **B2 记成 0**、把 **B3 记成 1**。
    这与 R49（「交割类备注写之前必须回源文件逐字核对象」）、
    R43（「清单给的是疑点，归属与连带面要自己核到全仓」）同族：
    **清单是人写的，归属得机器核**。

用法（在项目根目录，**必须就地跑** —— 白名单 `manuscripts/.deslop-whitelist` 与稿件同目录，
      复制到 /tmp 再跑会让白名单失效、误报 em-dash blocking=18）：
    python3 tracks/deslop_scan.py                 # 默认 ch6
    python3 tracks/deslop_scan.py --chapter ch7
    python3 tracks/deslop_scan.py --keep          # 保留临时正文段文件（调试用）

口径：
    正文段 ＝ `tracks/check.py` 的正文段（切片/分线标题行 → 「## 写作说明」前），
    复用 check.py 的正则与汉字口径，**不另起炉灶**。
    检测器 ＝ story-deslop 的 `check-ai-patterns.js`（AI 味）与 `check-degeneration.js`（模型退化），
    对**正文段**逐场扫描 → 报 blocking／advisory 归属，并**把行号映射回原切片文件**。

退出码：0 = 扫描完成（blocking 条数见输出）；1 = 扫描失败（检测器不可用等）。
"""

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as ck  # noqa: E402  —— 正文段口径唯一定义在 check.py

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = pathlib.Path.home() / ".openclaw/workspace-yomi/skills/story-deslop/scripts"

sys.path.insert(0, str(ROOT / "tracks"))
try:
    import line_rules as lr  # noqa: E402
    ROSTER = lr.ROSTERS
except Exception:  # pragma: no cover
    ROSTER = {"ch6": ["A1", "B1", "A2", "B2", "A3", "B3"]}


def extract_bodies(path):
    """按 check.py 口径切正文段，并记住每段在原文件的起始行号（用于行号回映射）。

    返回 [(正文段文本, 原文件起始行号)]。
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if not ck.SECTION.match(lines[i]):
            i += 1
            continue
        start = i
        j = i + 1
        buf = []
        while j < len(lines) and not ck.END_MARK.match(lines[j]) and not ck.SECTION.match(lines[j]):
            buf.append(lines[j])
            j += 1
        out.append(("\n".join([lines[i]] + buf), start + 1))  # 行号从 1 起
        i = j
    return out


def run_detector(script, target):
    """跑一个检测器，返回 findings 列表（失败则抛异常）。"""
    cmd = ["node", str(SKILL_SCRIPTS / script), "--check", "--json", str(target)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    raw = proc.stdout
    i = raw.find("{")
    if i < 0:
        raise RuntimeError(f"{script} 无 JSON 输出：{raw[:200]} / {proc.stderr[:200]}")
    data = json.loads(raw[i:])
    return data.get("findings", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="ch6")
    ap.add_argument("--keep", action="store_true", help="保留临时正文段文件")
    args = ap.parse_args()

    roster = ROSTER.get(args.chapter, ["A1", "B1", "A2", "B2", "A3", "B3"])
    print(f"=== 去 AI 味检测归属（{args.chapter}）===")
    print("    口径：正文段（check.py）· 就地跑（白名单有效）· 行号回映射到原切片文件")

    # G3（2026-11-20）：**零切片必须判红**。旧版在一场切片都没有时照样印
    # 「blocking 合计：0」＋「[OK] 归属扫描完成」并 exit 0 —— 等于「没扫」被当成「扫过且干净」。
    slices = sorted(p for p in (ROOT / "manuscripts").glob(f"{args.chapter}-*.md")
                    if "sample" not in p.name)
    if not slices:
        print(f"\n  [FAIL] 没有 {args.chapter}-*.md 切片 → 无可扫描正文，**判红**"
              f"（零切片 ≠ blocking 0，不得记作通过）")
        return 1

    total_blocking = 0
    scanned = 0        # 扫到的场次数
    scanned_hanzi = 0  # 扫到的**正文**汉字数（不含标题行）—— 为 0 说明「什么都没扫」
    detector_failed = 0  # 检测器不可用的场次数（node 缺失／检测器报错）→ 什么都没查 ≠ blocking 0
    tmp_files = []
    # 📌 清理挂 atexit（2026-11-24）：原来清理在主循环**之后**的普通语句 →
    #   脚本崩掉或被 kill 时，`manuscripts/.tmp-body-<场>.md` 会留成未跟踪垃圾。
    #   ⚠️ **不要把这些临时文件搬到 /tmp**：检测器白名单按**路径**生效
    #   （:15）→ 搬走会让白名单失效（em-dash 误报 blocking=18）→ **正解是 finally/atexit，目录不动**。
    import atexit

    def _cleanup_tmp_files():
        if getattr(args, "keep", False):
            return
        for t_ in tmp_files:
            try:
                t_.unlink(missing_ok=True)
            except Exception:
                pass

    atexit.register(_cleanup_tmp_files)
    for s in roster:
        src = ROOT / "manuscripts" / f"{args.chapter}-{s}.md"
        if not src.exists():
            print(f"\n  · {s} —— 尚无切片文件")
            continue
        bodies = extract_bodies(src)
        if not bodies:
            print(f"\n  · {s} —— 找不到正文段")
            continue
        body = "\n\n".join(b for b, _ in bodies)
        offset = bodies[0][1]  # 正文段在原文件的起始行
        tmp = ROOT / "manuscripts" / f".tmp-body-{s}.md"
        tmp.write_text(body, encoding="utf-8")
        tmp_files.append(tmp)
        scanned += 1
        scanned_hanzi += sum(len(ck.HANZI.findall(b.split("\n", 1)[1] if "\n" in b else ""))
                             for b, _ in bodies)

        findings = []
        for script in ("check-ai-patterns.js", "check-degeneration.js"):
            try:
                findings += run_detector(script, tmp)
            except Exception as exc:  # pragma: no cover
                print(f"\n  · {s} —— 检测器失败：{exc}")
                detector_failed += 1
                findings = None
                break
        if findings is None:
            continue

        blocking = [f for f in findings if f.get("severity") == "blocking"]
        advisory = [f for f in findings if f.get("severity") != "blocking"]
        total_blocking += len(blocking)
        print(f"\n  · {s} —— blocking {len(blocking)} / advisory {len(advisory)}")
        for f in blocking:
            orig = offset + int(f.get("line", 1)) - 1
            print(f"      [blocking] {f.get('type')}  正文段 L{f.get('line')} → 原文件 L{orig}"
                  f"  「{(f.get('excerpt') or '').strip()}」")
        for f in advisory:
            orig = offset + int(f.get("line", 1)) - 1
            print(f"      [advisory] {f.get('type')}  正文段 L{f.get('line')} → 原文件 L{orig}")

    for tmp in tmp_files:
        if not args.keep:
            tmp.unlink(missing_ok=True)

    if detector_failed:
        print(f"\n  [FAIL] {args.chapter} 有 {detector_failed} 场**检测器不可用**"
              f"（node 缺失／检测器报错）→ **判红**（什么都没查 ≠ blocking 0）")
        return 1

    if scanned == 0 or scanned_hanzi == 0:
        print(f"\n  [FAIL] {args.chapter} 有切片文件但正文为空"
              f"（无「## A1 ·」/「## A 线 ·」标题，或标题下没有正文；实测正文汉字 {scanned_hanzi}）"
              f"→ **判红**（不是 blocking 0）")
        return 1

    print(f"\n  ▸ 全章 blocking 合计：{total_blocking}")
    print("  📌 改的是**切片原件**（manuscripts/<章>-<场>.md），不是合成稿 → 改完重合成再复扫。")
    print("  📌 清单给的是疑点，**归属与连带面要自己核到全仓**（R43）；交付文件里不得原样引用被命中的句式。")
    print("[OK  ] 归属扫描完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
