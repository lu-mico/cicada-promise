#!/usr/bin/env python3
"""跨章／章内复读扫描（10-gram 最长公共子串）—— ch6 起的新红线门禁。

为什么有它（2026-11-20 立，Mico）：
    `tracks/ch6-review.md` §八 第 2 条把「**10-gram 复读扫描：ch6 与 ch1–ch5 的
    ≥14 字公共片段必须为 0**」写成**复审硬判据**，但评审当轮用的是**会话内临时脚本，
    没有落仓** → 改稿方与复审方手里都没有一条可复现的命令（评审 §一 声称「同一把尺子」，
    §八 声称「我会用同一脚本验」，而那条脚本不在仓库里）。
    本文件把那把尺子**落仓**：口径、阈值、退出码全部写死，任何人可复现。

口径（与 check.py 同源，**不另起炉灶**）：
    正文段 ＝ `tracks/check.py` 的 `slice_bodies`（切片/分线标题行 → 「## 写作说明」前）。
    归一化：**只去空白**（含全角空格 U+3000、换行），标点与汉字**原样保留**
    → 与评审报告里「28／18／12 字」的计法一致。
    阈值：
      · 跨章（本章 vs ch1–ch(N-1)）≥ **14** 字 ＝ **硬门禁**（有命中 → 退出码 1）
      · 章内（场 vs 场 / 同场复读） ≥ **12** 字 ＝ **advisory**（只报，不拦）
    章内 advisory 的存在理由：评审 §七 明列「B1 车灯 ×2」「B2/B3 瓶底 ×2」是**有意呼应**，
    要求保留 → 章内命中不等于缺陷，必须人看，硬门禁只给跨章。

用法（**必须在项目根目录跑**，与其它门禁同口径）：
    python3 tracks/ngram_scan.py --chapter ch6
    python3 tracks/ngram_scan.py --chapter ch7
    python3 tracks/ngram_scan.py --chapter ch6 --selftest    # 负向测试：证明门禁真的会红
    python3 tracks/ngram_scan.py --chapter ch6 --json        # 机器可读

白名单：`tracks/ngram-whitelist.txt`，一行一条**字面片段**（`#` 开头为注释）。
    命中片段里**含**白名单任一条 → 判为「有意复用」，只报不拦。
    （例：案纸引文「建议不予处理」跨章复现 —— 是那份纸的引文，不是 tic。）

退出码：0 = 通过（章内 advisory 不影响）· 1 = 跨章硬门禁有命中 · 2 = 扫描失败
"""

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check as ck  # noqa: E402  —— 正文段口径唯一定义在 check.py

try:
    import line_rules as lr  # noqa: E402
    ROSTERS = lr.ROSTERS
except Exception:  # pragma: no cover
    ROSTERS = {}

ROOT = pathlib.Path(__file__).resolve().parent.parent
WHITELIST = ROOT / "tracks" / "ngram-whitelist.txt"
DEFAULT_ROSTER = ["A1", "B1", "A2", "B2", "A3", "B3"]

# 正文段之间的分隔符：非空白 → 归一化后保留 → 阻断跨段误匹配
SEP = ""


# **小节标题行**（`#### 一` / `## 三` 之类）是**元数据**，不是正文。
# 为什么要单独认它（2026-11-24 修）：
#     `extract_bodies()` 只按 `ck.SECTION`（`^##\s+[AB]\s*(?:线|\d)`）与 `ck.END_MARK`
#     切段 → 正文里的 `#### 一`／`#### 八` 这种**小节标题留在段内**；
#     而 `normalize()` 把换行与空白全删掉 → 标题的字符（`####`）留在归一化串里 →
#     「上一小节末句 ＋ 标题 ＋ 下一小节首句」会被**拼成一句**去比对。
#     实测假命中（ch7 复审时由复审方抓出）：ch7-A3 ↔ ch5-B2
#     「了一下，才收回去。##」＝ 7 汉字 ＋ 4 个 `#` → 长度 11 ≥ 提示层 10 → **假命中**。
#     危险在于：标题字符一旦在两侧**位置相同**（两场的小节编号都是 `####`），
#     就能把两段不相干的话连起来 → **将来跨标题拼出 ≥14 字就会变成假红**（罚没复读的章）。
# 口径：**标题行只保留行结构（换行），内容清空** → 行号映射（`line_of`）不受影响，
#     归一化后标题字符不再进入被比较的正文。
# 📌 **边界（已知残留，不追求完备）**：**段落**之间的换行仍被归一化去掉，
#     即「上一段末句 ＋ 下一段首句」仍可能被拼起来比 → 属既有行为，本次不动
#     （尺子的**分界**优先于**完备**：先切小节这一层，剩下的记为已知限制）。
HEADING = re.compile(r"^#{2,6}\s*")


def normalize(text):
    """去空白（含全角空格 U+3000），其余原样。返回 (归一化串, 归一化位 → 原位 映射表)。"""
    chars, index = [], []
    for i, ch in enumerate(text):
        if ch.isspace() or ch == "　":
            continue
        chars.append(ch)
        index.append(i)
    return "".join(chars), index


def extract_bodies(path):
    """按 check.py 口径切正文段，**去掉标题行**（标题是元数据，不是正文），并记住起始行号。

    为什么要去掉标题行（2026-11-20 实测踩到）：
        check.py 的 `slice_bodies` 把标题行算进正文段（它的年份扫描要跳过标题行），
        但复读扫描拿它当正文 → 各章标题尾缀「（周睿视角，2026）」在 ch5↔ch6 之间
        互撞 15 字 → **假阳性**（ch6-A3.md L9 就是这一条）。
        故此处只取**标题行以下**的正文，起始行号相应 +1。

    返回 [(正文段文本（不含标题行）, 该段首行的原文件行号)]。
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if not ck.SECTION.match(lines[i]):
            i += 1
            continue
        j = i + 1
        buf = []
        while j < len(lines) and not ck.END_MARK.match(lines[j]) and not ck.SECTION.match(lines[j]):
            # 小节标题行 → 内容清空、只留行结构（见 HEADING 的说明）
            if HEADING.match(lines[j]):
                buf.append("")
            else:
                buf.append(lines[j])
            j += 1
        if buf:
            out.append(("\n".join(buf), i + 2))  # buf 首行 = 标题行下一行（行号从 1 起）
        i = j
    return out


def common_runs(a, b, k):
    """a、b 为已归一化字符串。返回 [(a 起, b 起, 长度)]，取**互不重叠的最长公共片段**。

    算法：以 k-gram 为种子（a 的每个 k-gram 去 b 的 k-gram 索引里查），
    命中后向两侧**只向后**延长到不等为止，再跳过已覆盖区间，避免重叠重复报。
    """
    b_grams = {}
    for j in range(len(b) - k + 1):
        b_grams.setdefault(b[j:j + k], j)
    runs = []
    i = 0
    while i <= len(a) - k:
        j = b_grams.get(a[i:i + k])
        if j is None:
            i += 1
            continue
        length = k
        while i + length < len(a) and j + length < len(b) and a[i + length] == b[j + length]:
            length += 1
        runs.append((i, j, length))
        i += length
    return runs


def self_repeats(text, k, min_len):
    """同一段正文内部的复读：找两个**不重叠**位置的相同片段，长度 ≥ min_len。"""
    pos = {}
    for i in range(len(text) - k + 1):
        pos.setdefault(text[i:i + k], []).append(i)
    best = {}
    for g, places in pos.items():
        if len(places) < 2:
            continue
        for x in range(len(places)):
            for y in range(x + 1, len(places)):
                i, j = places[x], places[y]
                length = k
                while (i + length < len(text) and j + length < len(text)
                       and text[i + length] == text[j + length]):
                    length += 1
                if length < min_len:
                    continue
                if j - i < length:      # 重叠 → 不算复读（中文里太常见，噪声大）
                    continue
                key = (i, j)
                if length > best.get(key, 0):
                    best[key] = length
    return [(i, j, length) for (i, j), length in sorted(best.items())]


def dedupe_hits(hits):
    """丢掉被别的命中**整段包含**的短命中（同一起点的级联后缀只留最长那条）。"""
    out = []
    for h in sorted(hits, key=lambda d: -d["length"]):
        if any((h["text"] in o["text"]) or (o["text"] in h["text"]) for o in out):
            continue
        out.append(h)
    return sorted(out, key=lambda d: -d["length"])


def line_of(body, start_line, offset):
    """归一化前的字符偏移 → 原文件行号。"""
    return start_line + body.count("\n", 0, offset)


def load_whitelist():
    if not WHITELIST.exists():
        return []
    out = []
    for line in WHITELIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def chapter_text(chapter, roster):
    """一章的正文全文（各场正文段用 SEP 隔开）。返回 (归一化串, 原串)。"""
    sample = ROOT / "manuscripts" / f"{chapter}-sample.md"
    if sample.exists():
        bodies = extract_bodies(sample)
        if bodies:
            raw = SEP.join(b for b, _ in bodies)
            return normalize(raw)[0], raw
    parts = []
    for s in roster:
        p = ROOT / "manuscripts" / f"{chapter}-{s}.md"
        if p.exists():
            parts += [b for b, _ in extract_bodies(p)]
    raw = SEP.join(parts)
    return normalize(raw)[0], raw


def chapter_slices(chapter):
    """该章已落的切片文件（`manuscripts/<章>-<场>.md`，不含合成稿）。"""
    d = ROOT / "manuscripts"
    return sorted(p for p in d.glob(f"{chapter}-*.md") if "sample" not in p.name)


def scan(chapter, k, cross_min, intra_min, roster, near_min=10):
    """返回扫描结果 dict。"""
    num = int(chapter[2:]) if chapter[2:].isdigit() else 0
    whitelist = load_whitelist()
    refs = {}
    for c in range(1, num):
        norm, _ = chapter_text(f"ch{c}", roster)
        if norm:
            refs[f"ch{c}"] = norm

    cross_hits, intra_hits, scenes = [], [], []
    chars = 0           # 扫到的正文汉字数（不含标题行）—— 为 0 说明「什么都没扫」
    scene_bodies = []   # [(场名, 文件名, [(正文段, 起始行), ...])]
    for s in roster:
        p = ROOT / "manuscripts" / f"{chapter}-{s}.md"
        if not p.exists():
            continue
        bodies = extract_bodies(p)
        if not bodies:
            continue
        scene_bodies.append((s, p.name, bodies))
        scene = {"scene": s, "file": p.name, "cross": [], "intra": []}
        for body, start_line in bodies:
            norm, idx = normalize(body)
            if not norm:
                continue
            chars += len(ck.HANZI.findall(body))
            # —— 跨章（硬门禁）——
            for ref_name, ref in refs.items():
                for a, b, length in common_runs(norm, ref, k):
                    if length < near_min:
                        continue
                    frag = norm[a:a + length]
                    raw_off = idx[a]
                    wl = next((w for w in whitelist if w in frag), None)
                    scene["cross"].append({
                        "ref": ref_name, "length": length,
                        "level": "hard" if length >= cross_min else "near",
                        "hanzi": len(ck.HANZI.findall(frag)),
                        "text": frag, "line": line_of(body, start_line, raw_off),
                        "whitelisted": bool(wl), "whitelist": wl,
                    })
            # —— 章内：同场复读 ——
            for i, j, length in self_repeats(norm, k, intra_min):
                frag = norm[i:i + length]
                raw_off = idx[i]
                wl = next((w for w in whitelist if w in frag), None)
                scene["intra"].append({
                    "kind": "self", "other": s, "length": length,
                    "hanzi": len(ck.HANZI.findall(frag)),
                    "text": frag, "line": line_of(body, start_line, raw_off),
                    "whitelisted": bool(wl), "whitelist": wl,
                })
        scenes.append(scene)
        scene["cross"] = dedupe_hits(scene["cross"])
        scene["intra"] = dedupe_hits(scene["intra"])

    # —— 章内：场 vs 场（跨切片文件）——
    norm_cache = []
    for name, fname, bodies in scene_bodies:
        for bi, (body, start_line) in enumerate(bodies):
            n, ix = normalize(body)
            norm_cache.append((name, fname, bi, n, body, start_line, ix))
    for x in range(len(norm_cache)):
        for y in range(x + 1, len(norm_cache)):
            ax = norm_cache[x]
            ay = norm_cache[y]
            if ax[0] == ay[0] and ax[2] == ay[2]:
                continue          # 同一场的同一段 → 交给「同场复读」判定
            for a, b, length in common_runs(ax[3], ay[3], k):
                if length < intra_min:
                    continue
                frag = ax[3][a:a + length]
                wl = next((w for w in whitelist if w in frag), None)
                owner = next(sc for sc in scenes if sc["scene"] == ax[0])
                owner["intra"].append({
                    "kind": "pair", "other": ay[0],
                    "length": length, "hanzi": len(ck.HANZI.findall(frag)),
                    "text": frag, "line": line_of(ax[4], ax[5], ax[6][a]),
                    "whitelisted": bool(wl), "whitelist": wl,
                })

    for sc in scenes:
        cross_hits += [(sc["scene"], h) for h in sc["cross"]]
        intra_hits += [(sc["scene"], h) for h in sc["intra"]]
    return {
        "chapter": chapter, "k": k, "cross_min": cross_min, "intra_min": intra_min,
        "chars": chars,
        "scenes": scenes, "cross_hits": cross_hits, "intra_hits": intra_hits,
        "hard": [x for x in cross_hits if not x[1]["whitelisted"] and x[1].get("level") == "hard"],
        "near": [x for x in cross_hits if not x[1]["whitelisted"] and x[1].get("level") == "near"],
    }





def selftest():
    """负向测试：证明这把尺子会红、且不会误报。"""
    k = 10
    cases = []
    dup = "从前有座山，山里有座庙，庙里有个老和尚在讲故事，讲的正是从前有座山。"
    runs = common_runs(normalize(dup)[0], normalize(dup)[0], k)
    cases.append(("同一段自比 → 必须命中", bool(runs) and max(r[2] for r in runs) >= len(dup) - 1))
    a = normalize("今天天气很好，适合去公园散步，看了一场电影就回家了。")[0]
    b = normalize("他沿着河堤走了很久才停下脚步，看着水面发呆。")[0]
    runs2 = common_runs(a, b, k)
    cases.append(("无关两段 → 不得命中", not [r for r in runs2 if r[2] >= 14]))
    rep = normalize("他把碗放在门槛上，碗口朝下。过了很久，他把碗放在门槛上，碗口朝下。")[0]
    sr = self_repeats(rep, k, 12)
    cases.append(("同场复读 → 必须命中", bool(sr) and max(r[2] for r in sr) >= 12))
    # —— 2026-11-24 新增（文件级）：跨小节标题的假命中 vs 同小节内的真复读 ——
    # 反例（改前必须命中、改后必须不命中）：两场正文末尾句相同（**7 字符**），
    #   两侧接下来都是 `####` 小节标题 → 改前标题字符把两段不相干的话拼起来
    #   （7 + 4 = 11 ≥ 提示层 10 → 报假提示）；改后标题内容不进正文
    #   → 只剩 7 字符 < 10 → 不报。
    #   （对照真实实例：ch7-A3 ↔ ch5-B2「了一下，才收回去。##」＝ 9 字符 + 2 个 # ＝ 11）
    import tempfile
    _d = pathlib.Path(tempfile.mkdtemp(prefix="ngram-selftest-"))
    _a = _d / "a.md"
    _b = _d / "b.md"
    _a.write_text("## A1 · 测试\n\n#### 一\n他把手放下，指头才收回。\n\n#### 八\n屋里没有声音。\n", encoding="utf-8")
    _b.write_text("## A1 · 测试\n\n#### 三\n她把碗挪开，指头才收回。\n\n#### 九\n后来就没有再提。\n", encoding="utf-8")
    _hits = []
    for _ba, _ in extract_bodies(_a):
        for _bb, _ in extract_bodies(_b):
            _na, _ = normalize(_ba)
            _nb, _ = normalize(_bb)
            _hits += [r for r in common_runs(_na, _nb, k) if r[2] >= 10]
    cases.append(("跨小节标题拼接 → 不得命中（标题是元数据，不进正文）", not _hits))
    # 正例（必须仍命中）：同小节内的真复读 12 汉字 → 判据不许被改钝。
    _c = _d / "c.md"
    _e = _d / "e.md"
    _c.write_text("## A1 · 测试\n\n#### 一\n他把碗放在门槛上，碗口朝下。\n\n#### 二\n过了很久，他把碗放在门槛上，碗口朝下。\n", encoding="utf-8")
    _e.write_text("## B1 · 测试\n\n#### 一\n他把碗放在门槛上，碗口朝下。\n", encoding="utf-8")
    _hits2 = []
    for _bc, _ in extract_bodies(_c):
        for _be, _ in extract_bodies(_e):
            _nc, _ = normalize(_bc)
            _ne, _ = normalize(_be)
            _hits2 += [r for r in common_runs(_nc, _ne, k) if r[2] >= 12]
    cases.append(("同小节内的真复读 → 必须仍命中（判据不许被改钝）", bool(_hits2)))
    print("=== ngram_scan 自测 ===")
    ok = True
    for name, passed in cases:
        print(f"  [{'OK' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print("  [OK  ] 自测通过" if ok else "  [FAIL] 自测失败")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default="ch6")
    ap.add_argument("--k", type=int, default=10, help="k-gram 长度（默认 10）")
    ap.add_argument("--cross", type=int, default=14, help="跨章硬门禁字数（默认 14）")
    ap.add_argument("--intra", type=int, default=12, help="章内 advisory 字数（默认 12）")
    ap.add_argument("--near", type=int, default=10, help="跨章提示层字数（默认 10，只报不拦）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    # G3（2026-11-20）：**零切片必须判红**。旧版在没有一个切片文件时照样印
    # 「跨章硬门禁命中：0（通过）」并 exit 0 —— 等于「什么都没扫」被当成「扫过且干净」。
    # 判据只认「有正文字可扫」：一个 <章>-*.md 切片都没有、也没有合成稿 → 红。
    sample = ROOT / "manuscripts" / f"{args.chapter}-sample.md"
    if not chapter_slices(args.chapter) and not sample.exists():
        print(f"=== 跨章／章内复读扫描（{args.chapter}）===")
        print(f"  [FAIL] 没有 {args.chapter}-*.md 切片"
              f"（也没有 {args.chapter}-sample.md 合成稿）→ 无可扫描正文，**判红**"
              f"（零切片 ≠ 0 命中，不得记作通过）")
        return 1

    roster = ROSTERS.get(args.chapter, DEFAULT_ROSTER)
    res = scan(args.chapter, args.k, args.cross, args.intra, roster, args.near)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 1 if (res["hard"] or not res["scenes"] or res["chars"] == 0) else 0

    # 文件在、但一场正文段都切不出来（正文段口径见 check.py）→ 同样不算通过。
    if not res["scenes"] or res["chars"] == 0:
        print(f"=== 跨章／章内复读扫描（{args.chapter}）===")
        print(f"  [FAIL] {args.chapter} 有切片文件但正文为空"
              f"（无「## A1 ·」/「## A 线 ·」标题，或标题下没有正文；实测正文汉字 {res['chars']}）"
              f"→ **判红**（不是 0 命中）")
        return 1

    _num = int(res["chapter"][2:]) if res["chapter"][2:].isdigit() else 1
    _prev = max(1, _num - 1)  # 比的是 ch1–ch(N-1)（含自己＝显示错，且会把章内复读当跨章）
    print(f"=== 跨章／章内复读扫描（{args.chapter} vs ch1–ch{_prev} 之前各章）===")
    print(f"    口径：正文段（check.py）· {args.k}-gram 最长公共子串"
          f" · 跨章 ≥{args.cross} 硬门禁 / 章内 ≥{args.intra} advisory")
    for sc in res["scenes"]:
        print(f"\n  · {sc['scene']}（{sc['file']}）")
        if not sc["cross"] and not sc["intra"]:
            print("      无命中")
            continue
        for h in sorted(sc["cross"], key=lambda d: -d["length"]):
            if h["whitelisted"]:
                tag = "[白名单]"
            elif h.get("level") == "hard":
                tag = "[HARD]"
            else:
                tag = "[near]"
            print(f"      {tag} 跨章 {h['ref']}  {h['length']} 字（汉字 {h['hanzi']}）"
                  f"  {sc['file']} L{h['line']}")
            print(f"           「{h['text']}」")
        for h in sorted(sc["intra"], key=lambda d: -d["length"]):
            kind = "同场复读" if h["kind"] == "self" else f"vs {h['other']}"
            tag = "[白名单]" if h["whitelisted"] else "[advisory]"
            print(f"      {tag} 章内 {kind}  {h['length']} 字（汉字 {h['hanzi']}）"
                  f"  {sc['file']} L{h['line']}")
            print(f"           「{h['text']}」")

    hard = len(res["hard"])
    near = len(res["near"])
    print(f"\n  ▸ 跨章硬门禁命中：{hard}"
          + ("（**门禁红**）" if hard else "（通过）"))
    print(f"  ▸ 跨章提示层（{args.near}–{args.cross - 1} 字）：{near}（只报不拦；"
          "改稿要求「与前章不得 ≥10 字重合」时看这层）")
    print(f"  ▸ 章内 advisory：{len(res['intra_hits'])}（不拦，需人看：有意呼应要保留）")
    print("  📌 改的是**切片原件**（manuscripts/<章>-<场>.md）→ 改完重合成再复扫。")
    return 1 if hard else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[FAIL] 扫描失败：{exc}")
        sys.exit(2)
