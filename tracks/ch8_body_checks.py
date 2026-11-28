#!/usr/bin/env python3
"""ch8 v1.0 正文段口径门禁 —— 依据 tracks/ch8-daily.md §二之二 / §五 / §八之二（D1–D7 · D9 · D12 · D13）。

口径（改稿方与复审方跑**同一条命令**）：`python3 tracks/ch8_body_checks.py`

1) **只扫正文段**：用 `check.slice_bodies()` 的口径切出正文段（切片标题行 →「## 写作说明」）。
   为什么：每场末尾的「## 写作说明」表里写着「林默 0 次」「胸针 0 次」「B 线年份 0 个」
   「三十年前 A 线 1 次」这类**规则说明行**——裸 `grep` 会把**规则说明本身**当成违规命中
   （假阳性）。**裸 grep 在干净稿上就是红的**，见 `--prove` 用例 2。

2) **D2「三十年前」是整章口径**（跨切片累加），不是单场口径 → 本脚本按**全章正文段**累加，
   并且**同时**单查 B 线 0 次（G9 的 ch8_rules.py 已做同样一件事；两处独立实现互为交叉验证）。

3) **期望值的作用域与实测值**（2026-11-28 主编在六场齐的合格产物上实测，HEAD `47a94f4`）：

   | # | 语义 | 作用域 | 判据 | 实测 |
   |---|------|--------|------|------|
   | 1 | D2：「三十年前」整章恰好 1 次（A 线首现） | 全章 | 字面「三十年前」 | **1** |
   | 2 | D2：B 线「三十年前」0 次 | B 线 | 字面「三十年前」 | **0** |
   | 3 | 「三十」全章 1 次（就是那一处） | 全章 | 字面「三十」 | **1** |
   | 4 | D12：其它年数推算写法 0 次 | 全章 | 三十年整／多少年／二十九年／快三十年 | **0** |
   | 5 | B 线阿拉伯年份 0 个 | B 线 | `(18\|19\|20)\\d{2}` | **0** |
   | 6 | D1／D4：林默 0 次 | 全章 | 字面「林默」 | **0** |
   | 7 | D7：胸针 0 次 | 全章 | 字面「胸针」 | **0** |
   | 8 | B 线誓言语汇 0 次 | 全章 | 永远／永不／一辈子／到死 | **0**（四个各 0） |
   | 9 | B 线誓言符号 0 次 | 全章 | 独立大写「L」 | **0** |
   | 10 | 称谓口径 0 次 | 全章 | 字面「夏父」 | **0** |
   | 11 | D6：B 线死因定性 0 次 | B 线 | 自杀／病故／意外 | **0**（三个各 0） |
   | 12 | D5：A 线「自杀」＝报纸用词 | **只** A2 | 字面「自杀」 | **2** |
   | 13 | D5：「自杀」不得出现在 A1／A3 | A1／A3 | 字面「自杀」 | **0** |
   | 14 | D3：唯一纸面结论（「潜逃」＋「不成立」各 1 次） | 全章 | 字面 | **1／1** |
   | 15 | D3：不推死因 | 全章 | 字面「死因」 | **0** |
   | 16 | D3：不重开 ch6 定论 | 全章 | 字面「治-17」「顶名」 | **0** |
   | 17 | 墓地／祭拜 0 次（ch12 才查） | 全章 | 墓地／公墓／坟／祭 | **0**（四个各 0） |
   | 18 | 台词口径锁：A 线引号台词总数 | A 线 | `“([^”]*)”` 对数 | **44**（A1 19 · A2 17 · A3 8） |
   | 19 | 台词口径锁：B 线引号台词总数 | B 线 | 同上 | **25**（B1 9 · B2 16 · B3 0） |
   | 20 | D13：B3 引号台词 0 次（亡者叙述第一场不出现对话；她的声音是记忆里的一句，不是台词） | **只** B3 | 引号对数 | **0** |
   | 21 | 章末落点（判据 3）：合成稿场序 A1 B1 A2 B2 A3 B3，**末节是 B3** | 合成稿 | 标题序列 | **A1…B3** |

   作用域说明（纪律：**尺子不得大于被量的事实**）：
   * 第 12 条是「A 线允许出现『自杀』，但只许作**外地报纸的用词**」→ **只查 A2**（报纸那一场）；
     A1／A3 另立一条（第 13 条）单独锁 0 → 换句话说：**「自杀」只允许出现在 A2，且恰好 2 次**。
   * 第 5 条只查 B 线（A 线允许档案年份，**不是**红线 → 不锁 A 线计数）。
   * 第 9 条用「独立大写 L」的正则（同 `bline_rules.py`），**不是**裸 grep「L」——
     裸 grep 会命中一切含字母 L 的字串（机器即失败的真因）。

4) **期望值是「口径锁」，不是永久常量**：
   来源 ＝ **最近一次实测**（2026-11-28，对象 = HEAD `47a94f4`，六场齐）。
   作者的改稿落地后，**由主编当场重测并更新本文件、附重测记录**（落仓），再让复审方跑链。
   → **复审方看到红，先对表上的日期与 HEAD，不要先假定作者写错**。

用法：
    python3 tracks/ch8_body_checks.py           # 跑门禁（退出码非 0 = FAIL）
    python3 tracks/ch8_body_checks.py --prove   # 证明**每条**判据都能失败（负向自测）
退出码：0 = 通过；1 = 有项失败。
"""

import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tracks"))
import check as ck  # noqa: E402

SLICES = ["A1", "B1", "A2", "B2", "A3", "B3"]   # 表序（interleaved）

# 口径锁：2026-11-28 主编实测（HEAD 47a94f4，六场齐）。改稿后由主编重测更新。
QUOTE_TOTALS = {"A": 44, "B": 25}   # A1 19 · A2 17 · A3 8 ／ B1 9 · B2 16 · B3 0
QUOTE_RE = re.compile(r"“([^”]*)”")
YEAR_RE = re.compile(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)")
LETTER_L_RE = re.compile(r"(?<![A-Za-z])L(?![A-Za-z])")

# (编号, 语义, 作用域, 类型, 词表, 期望值)
# 作用域：'ALL' ／ 'A' ／ 'B' ／ 具体切片号（'A2'、'B3'…）
ITEMS = [
    (1, "D2：「三十年前」整章恰好 1 次（A 线首现）", "ALL", "literal", ["三十年前"], 1),
    (2, "D2：B 线「三十年前」0 次", "B", "literal", ["三十年前"], 0),
    (3, "「三十」全章 1 次（就是那一处）", "ALL", "literal", ["三十"], 1),
    (4, "D12：其它年数推算写法 0 次", "ALL", "literal",
     ["三十年整", "多少年", "二十九年", "快三十年"], 0),
    (5, "B 线阿拉伯年份 0 个", "B", "year", None, 0),
    (6, "D1／D4：林默 0 次", "ALL", "literal", ["林默"], 0),
    (7, "D7：胸针 0 次", "ALL", "literal", ["胸针"], 0),
    (8, "B 线誓言语汇 0 次（永远／永不／一辈子／到死）", "ALL", "literal",
     ["永远", "永不", "一辈子", "到死"], 0),
    (9, "B 线誓言符号 0 次（独立大写 L）", "ALL", "letter_l", None, 0),
    (10, "称谓口径 0 次（夏父）", "ALL", "literal", ["夏父"], 0),
    (11, "D6：B 线死因定性 0 次（自杀／病故／意外）", "B", "literal",
     ["自杀", "病故", "意外"], 0),
    (12, "D5：A 线「自杀」＝报纸用词（只在 A2）", "A2", "literal", ["自杀"], 2),
    (13, "D5：「自杀」不得出现在 A1／A3", "A1A3", "literal", ["自杀"], 0),
    (14, "D3：唯一纸面结论（「潜逃」＋「不成立」各 1 次）", "ALL", "literal_multi",
     ["潜逃", "不成立"], [1, 1]),
    (15, "D3：不推死因", "ALL", "literal", ["死因"], 0),
    (16, "D3：不重开 ch6 定论", "ALL", "literal", ["治-17", "顶名"], 0),
    (17, "墓地／祭拜 0 次（ch12 才查）", "ALL", "literal",
     ["墓地", "公墓", "坟", "祭"], 0),
    (18, "台词口径锁：A 线引号台词总数", "A", "quote_total", None, QUOTE_TOTALS["A"]),
    (19, "台词口径锁：B 线引号台词总数", "B", "quote_total", None, QUOTE_TOTALS["B"]),
    (20, "D13：B3 引号台词 0 次（亡者叙述不出现对话）", "B3", "quote_total", None, 0),
    (21, "章末落点：合成稿场序 A1 B1 A2 B2 A3 B3，末节是 B3", "SAMPLE", "sample_order", None, None),
    (22, "小节序号：每场正文段内「## 一/## 二…」**唯一且连续**（无重号、无跳号）", "ALL", "section_seq", None, None),
]


def segments(path):
    """返回 [(标题, 正文段行列表, 正文首行绝对行号)]。

    口径完全跟着 `check.slice_bodies` 走（正文段结束标记 ＝「## 写作说明」等），
    这里只额外记住**绝对行号**，好让报错能直接定位到文件行。
    若与 `check.slice_bodies` 产生任何分歧 → 直接报错退出（口径漂移防护）。
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    picked = ck.slice_bodies(text)
    out = []
    i = 0
    while i < len(lines):
        if not ck.SECTION.match(lines[i]):
            i += 1
            continue
        j = i + 1
        buf = []
        while j < len(lines) and not (ck.END_MARK.match(lines[j]) or ck.SECTION.match(lines[j])):
            buf.append(lines[j])
            j += 1
        out.append((lines[i][3:].strip(), buf, i + 2))
        i = j
    if len(out) != len(picked):
        raise SystemExit(f"[口径漂移] {path}: 正文段数与 check.slice_bodies 不一致")
    for (title, buf, _), (t2, _b2, bnh2) in zip(out, picked):
        if title != t2 or "\n".join(buf) != bnh2:
            raise SystemExit(f"[口径漂移] {path}: 正文段文本与 check.slice_bodies 不一致")
    return out


def collect(files):
    """{文件名: segments(...)}。"""
    return {pathlib.Path(f).name: segments(f) for f in files}


def in_scope(name, scope):
    """作用域过滤：ALL／A／B／具体切片号／'A1A3'（两个切片的并集）。"""
    if scope == "ALL":
        return True
    if scope == "SAMPLE":
        return False
    m = re.search(r"ch8-([AB]\d)\.md$", name)
    if not m:
        return False
    sid = m.group(1)
    if scope == "A":
        return sid.startswith("A")
    if scope == "B":
        return sid.startswith("B")
    if scope.endswith("A3") and scope == "A1A3":
        return sid in ("A1", "A3")
    return sid == scope


def scan_literal(data, scope, tokens):
    hits = []
    for name, segs in data.items():
        if not in_scope(name, scope):
            continue
        for title, buf, abs_start in segs:
            for offset, line in enumerate(buf):
                for tok in tokens:
                    n = line.count(tok)
                    if n:
                        hits.append((name, abs_start + offset, title, tok, n, line.strip()[:60]))
    return hits


def scan_years(data, scope):
    hits = []
    for name, segs in data.items():
        if not in_scope(name, scope):
            continue
        for title, buf, abs_start in segs:
            for offset, line in enumerate(buf):
                for m in YEAR_RE.finditer(line):
                    hits.append((name, abs_start + offset, title, m.group(0), 1, line.strip()[:60]))
    return hits


def scan_letter_l(data, scope):
    hits = []
    for name, segs in data.items():
        if not in_scope(name, scope):
            continue
        for title, buf, abs_start in segs:
            for offset, line in enumerate(buf):
                n = len(LETTER_L_RE.findall(line))
                if n:
                    hits.append((name, abs_start + offset, title, "L", n, line.strip()[:60]))
    return hits


def scan_quote_total(data, scope):
    """返回 (总数, {文件: 对数}, [(文件, 行号, 台词)])。"""
    per, lines = {}, []
    for name, segs in data.items():
        if not in_scope(name, scope):
            continue
        n = 0
        for title, buf, abs_start in segs:
            for offset, line in enumerate(buf):
                qs = QUOTE_RE.findall(line)
                n += len(qs)
                for q in qs:
                    lines.append((name, abs_start + offset, q))
        per[name] = n
    return sum(per.values()), per, lines


CN_NUM = "一二三四五六七八九十"
_SECTION_HEAD_RE = re.compile(r"^##\s+([一二三四五六七八九十]+)\s*$", flags=re.M)


def cn_to_int(s):
    """中文小节序号 → 整数（支持 一…十九、二十…）。"""
    if not s:
        return None
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN_NUM.index(s[1]) + 1
    if "十" in s:
        head, tail = s.split("十", 1)
        base = CN_NUM.index(head) + 1
        return base * 10 + (CN_NUM.index(tail) + 1 if tail else 0)
    return CN_NUM.index(s) + 1


def scan_section_seq(data):
    """查每场正文段的小节序号是否唯一且从「一」连续。

    为什么要有这条（2026-11-28 实测踩到）：作者新写的一���里**撞了两个「## 四」**
    → 读者看到两个第四节；**而 check.py / body_checks 全绿**（正文段口径不数小节序号）
    → 这是一条**机器门禁不覆盖**的结构缺陷。
    """
    hits = []
    for name, segs in data.items():
        for title, buf, abs_start in segs:
            seq = []
            for offset, line in enumerate(buf):
                m = _SECTION_HEAD_RE.match(line)
                if m:
                    seq.append((m.group(1), abs_start + offset))
            if not seq:
                continue
            nums = [cn_to_int(s) for s, _ in seq]
            want = list(range(1, len(nums) + 1))
            if nums != want:
                bad = []
                seen = {}
                for (s, ln), n in zip(seq, nums):
                    seen.setdefault(n, []).append(ln)
                for n, lns in seen.items():
                    if len(lns) > 1:
                        bad.append("序号「%s」重号（行 %s）" % (CN_NUM[n - 1], "／".join(map(str, lns))))
                missing = [CN_NUM[i - 1] for i in want if i not in nums]
                if missing:
                    bad.append("缺号：%s" % "／".join(missing))
                jumps = [(CN_NUM[nums[i] - 1], CN_NUM[nums[i + 1] - 1])
                         for i in range(len(nums) - 1) if nums[i + 1] != nums[i] + 1]
                if jumps:
                    bad.append("跳号：%s" % "／".join("%s→%s" % j for j in jumps))
                hits.append((name, seq[0][1], title, "小节序号", len(bad), "；".join(bad)))
    return hits


def sample_order_status(sample_path):
    """合成稿的场序与末节核（D9：全章最后一段必须落在 B3）。"""
    p = pathlib.Path(sample_path)
    if not p.exists():
        return False, ["合成稿不存在：%s" % sample_path]
    text = p.read_text(encoding="utf-8")
    heads = re.findall(r"^##\s+([AB]\d)\s*·", text, flags=re.M)
    want = ["A1", "B1", "A2", "B2", "A3", "B3"]
    where = []
    if heads != want:
        where.append("合成稿场序＝%s（期望 %s）" % (" ".join(heads), " ".join(want)))
    if heads and heads[-1] != "B3":
        where.append("合成稿末节＝%s（期望 B3）" % heads[-1])
    return (not where), where


def evaluate(files, sample_path=None):
    """返回 (结果列表, 是否通过)。"""
    data = collect(files)
    results = []
    for num, sem, scope, kind, tokens, want in ITEMS:
        info = ""
        if kind == "quote_total":
            got, per, lines = scan_quote_total(data, scope)
            where = ["%s %d 句" % (name, n) for name, n in sorted(per.items())]
            info = "台词清单（前 8 条）：" + "／".join(
                "%s:%d「%s」" % (name, ln, q) for name, ln, q in lines[:8]
            ) + ("…" if len(lines) > 8 else "")
        elif kind == "year":
            hits = scan_years(data, scope)
            got = sum(h[4] for h in hits)
            where = ["%s:%d [%s] %s → %s" % (n, ln, t, tok, snip) for n, ln, t, tok, _, snip in hits]
        elif kind == "letter_l":
            hits = scan_letter_l(data, scope)
            got = sum(h[4] for h in hits)
            where = ["%s:%d [%s] 「%s」→ %s" % (n, ln, t, tok, snip) for n, ln, t, tok, _, snip in hits]
        elif kind == "literal_multi":
            per_tok = []
            ok_all = True
            for tok, w in zip(tokens, want):
                hits = scan_literal(data, scope, [tok])
                got_tok = sum(h[4] for h in hits)
                ok_all = ok_all and (got_tok == w)
                per_tok.append("%s＝%d（期望 %d）" % (tok, got_tok, w))
                for h in hits:
                    where.append("%s:%d [%s] 「%s」→ %s" % (h[0], h[1], h[2], h[3], h[5]))
            got = "／".join(per_tok)
            want_s = "／".join("%s＝%d" % (t, w) for t, w in zip(tokens, want))
            results.append(dict(num=num, sem=sem, scope=scope, ok=ok_all,
                                 got=got, want=want_s, where=where, info=info))
            continue
        elif kind == "section_seq":
            hits = scan_section_seq(data)
            bad = [h for h in hits if h[4] > 0]
            got = sum(h[4] for h in bad)
            where = ["%s:%d [%s] %s" % (h[0], h[1], h[2], h[5]) for h in bad]
            results.append(dict(num=num, sem=sem, scope="全章", ok=(got == 0),
                                 got=got, want=0, where=where, info=info))
            continue
        elif kind == "sample_order":
            sp = sample_path or (ROOT / "manuscripts" / "ch8-sample.md")
            ok, where = sample_order_status(sp)
            results.append(dict(num=num, sem=sem, scope="合成稿", ok=ok,
                                 got="场序核" if ok else "不合序", want="A1…B3（末节 B3）",
                                 where=where, info=""))
            continue
        else:
            hits = scan_literal(data, scope, tokens)
            got = sum(h[4] for h in hits)
            where = ["%s:%d [%s] 「%s」→ %s" % (n, ln, t, tok, snip) for n, ln, t, tok, _, snip in hits]
        results.append(dict(num=num, sem=sem, scope=scope, ok=(got == want),
                             got=got, want=want, where=where, info=info))
    return results, all(r["ok"] for r in results)


def run_gate(files, verbose=True, sample_path=None):
    results, ok = evaluate(files, sample_path=sample_path)
    if verbose:
        print("── ch8 正文段口径门禁（D1–D7 · D9 · D12 · D13）──")
        for r in results:
            flag = "OK  " if r["ok"] else "FAIL"
            scope = "全章" if r["scope"] == "ALL" else r["scope"]
            print(f"  [{flag}] #{r['num']} {r['sem']}（{scope}）＝ {r['got']}，期望 {r['want']}")
            for w in r["where"]:
                print(f"         · {w}")
            if r["info"]:
                print(f"         info: {r['info']}")
        print(f"  → {'全 %d 条通过' % len(results) if ok else '有项失败'}")
    return ok


def _copy_slices(real, dest):
    (dest / "manuscripts").mkdir(parents=True)
    for f in real:
        shutil.copy2(f, dest / "manuscripts" / f.name)
    return [dest / "manuscripts" / f.name for f in real]


def _insert_before_write_notes(path, text):
    lines = path.read_text(encoding="utf-8").split("\n")
    for idx, line in enumerate(lines):
        if line.strip() == "## 写作说明":
            lines.insert(idx, text)
            path.write_text("\n".join(lines), encoding="utf-8")
            return True
    return False


def prove_can_fail():
    """负向自测：干净稿必须绿；每条判据都要能被打红；作用域不许误伤合格稿。"""
    real = [ROOT / "manuscripts" / f"ch8-{s}.md" for s in SLICES]
    for f in real:
        if not f.exists():
            raise SystemExit(f"缺文件：{f}")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ch8_body_selftest_"))
    try:
        results = []

        # 用例 1：干净稿 → 必须**绿**
        clean_dir = tmp / "clean"
        clean = _copy_slices(real, clean_dir)
        ok_clean = run_gate(clean, verbose=False, sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_clean else 'FAIL'}] 用例1：干净稿 → 全绿（必须绿）")
        results.append(ok_clean)

        # 用例 2：旧口径（裸 grep 扫全文，含写作说明）→ 干净稿**必须红**
        raw = {}
        for f in real:
            text = f.read_text(encoding="utf-8")
            for _, _, _, _, tokens, _ in ITEMS:
                if not tokens:
                    continue
                for tok in (tokens if isinstance(tokens, list) else []):
                    raw[tok] = raw.get(tok, 0) + text.count(tok)
        raw_hit = {k: v for k, v in raw.items() if v}
        old_red = bool(raw_hit)
        shown = "／".join(f"{k} {v}" for k, v in sorted(raw_hit.items())[:8])
        print(
            f"  [{'OK' if old_red else 'FAIL'}] 用例2：旧口径（裸 grep 扫全文）在干净稿上判红"
            f"（规则说明表里的 {shown} … 全被误命中）→ 证明必须用正文段口径"
        )
        results.append(old_red)

        # 用例 3：逐条注入 —— **每条字面判据**都要能被打红
        injected = []
        for num, sem, scope, kind, tokens, want in ITEMS:
            if kind not in ("literal", "literal_multi"):
                continue
            toks = tokens if isinstance(tokens, list) else []
            for tok in toks:
                d = tmp / f"inj{num}_{tok}"
                files = _copy_slices(real, d)
                target = d / "manuscripts" / "ch8-B3.md"
                ok_insert = _insert_before_write_notes(target, f"自测：{tok}。")
                red = not run_gate(files, verbose=False,
                                   sample_path=ROOT / "manuscripts" / "ch8-sample.md")
                injected.append((num, tok, ok_insert and red))
        all_inj = all(x[2] for x in injected)
        bad = ", ".join("#%d %s" % (n, t) for n, t, ok in injected if not ok)
        print(
            f"  [{'OK' if all_inj else 'FAIL'}] 用例3：{len(injected)} 条字面判据逐条注入 → 条条判红"
            f"（{'全部打红' if all_inj else '未打红：' + bad}）"
        )
        results.append(all_inj)

        # 用例 3b：B 线塞阿拉伯年份 → 第 5 条必须红
        d = tmp / "inj_year"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-B3.md", "自测：那一年是一九九六年，墙上贴着 1996 四个数字。"
        )
        year_red = not run_gate(files, verbose=False,
                               sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and year_red else 'FAIL'}] 用例3b：B 线正文塞阿拉伯年份 → 判红（第 5 条能失败）")
        results.append(ok_insert and year_red)

        # 用例 3c：B 线塞独立大写 L → 第 9 条必须红
        d = tmp / "inj_letter"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-B2.md", "自测：她在盒底刻了一个 L。"
        )
        l_red = not run_gate(files, verbose=False,
                             sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and l_red else 'FAIL'}] 用例3c：B2 正文塞独立大写「L」→ 判红（第 9 条能失败）")
        results.append(ok_insert and l_red)

        # 用例 3d：A2 再加一句「自杀」→ 第 12 条（恰好 2 次）必须红
        d = tmp / "inj_zisha"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-A2.md", "自测：报上第二则也写着自杀。"
        )
        zisha_red = not run_gate(files, verbose=False,
                                 sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and zisha_red else 'FAIL'}] 用例3d：A2 再添一处「自杀」→ 3 次 → 判红（第 12 条能失败）")
        results.append(ok_insert and zisha_red)

        # 用例 4：B 线引号台词总数 +1 → 第 19 条必须红
        d = tmp / "mut_bquote"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-B3.md", "“嗯。”我说。"
        )
        bq_red = not run_gate(files, verbose=False,
                             sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and bq_red else 'FAIL'}] 用例4：B3 正文塞一句台词 → B 线总数 26 → 判红（第 19 条能失败）")
        results.append(ok_insert and bq_red)

        # 用例 4b：A 线引号台词总数 +1 → 第 18 条必须红
        d = tmp / "mut_aquote"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-A1.md", "“几点了。”他问。"
        )
        aq_red = not run_gate(files, verbose=False,
                             sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and aq_red else 'FAIL'}] 用例4b：A1 正文多一句台词 → A 线总数 45 → 判红（第 18 条能失败）")
        results.append(ok_insert and aq_red)

        # 用例 5：口径锁复现（A 44／B 25）
        data = collect(real)
        a_total, a_per, _ = scan_quote_total(data, "A")
        b_total, b_per, _ = scan_quote_total(data, "B")
        ok_lock = (a_total == QUOTE_TOTALS["A"] and b_total == QUOTE_TOTALS["B"])
        print(
            f"  [{'OK' if ok_lock else 'FAIL'}] 用例5：台词总数口径锁复现 A {a_total}／B {b_total}"
            f"（期望 44／25；B3 ＝ 0）"
        )
        results.append(ok_lock)

        # 用例 6：D2 跨切片累加 —— B2 再写一次「三十年前」→ 第 2 条必须红
        d = tmp / "mut_span"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-B2.md", "自测：那是三十年前的事了。"
        )
        span_red = not run_gate(files, verbose=False,
                                sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and span_red else 'FAIL'}] 用例6：B2 正文写「三十年前」→ 判红（第 2 条能失败：D2 是 B 线红线）")
        results.append(ok_insert and span_red)

        # 用例 7：作用域不得误伤 —— 「自杀」写进 A3（第 13 条红），写进 B2（第 11 条红）
        d = tmp / "scope_b"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch8-B2.md", "自测：她妈说，那是自杀。"
        )
        scope_b_red = not run_gate(files, verbose=False,
                                   sample_path=ROOT / "manuscripts" / "ch8-sample.md")
        print(f"  [{'OK' if ok_insert and scope_b_red else 'FAIL'}] 用例7：B2 正文写「自杀」→ 判红（第 11 条只罚 B 线）")
        results.append(ok_insert and scope_b_red)

        # 用例 7b：小节序号重号 → 第 22 条必须红（作者实踩过的洞：两个「## 四」）
        d = tmp / "mut_dupsec"
        files = _copy_slices(real, d)
        b3 = d / "manuscripts" / "ch8-B3.md"
        before = b3.read_text(encoding="utf-8")
        heads = re.findall(r"^##\s+([一二三四五六七八九十]+)\s*$", before, flags=re.M)
        if len(heads) >= 5:
            dup = heads[3]
            b3.write_text(before.replace(f"## {heads[4]}\n", f"## {dup}\n", 1), encoding="utf-8")
            changed = b3.read_text(encoding="utf-8") != before
            dup_red = not run_gate(files, verbose=False,
                                   sample_path=ROOT / "manuscripts" / "ch8-sample.md")
            print(f"  [{'OK' if changed and dup_red else 'FAIL'}] 用例7b：把第 5 节改成与第 4 节同号（重号）→ 判红（第 22 条能失败）")
            results.append(changed and dup_red)
        else:
            print("  [跳过] 用例7b：小节数不足，无法造重号")
            results.append(False)

        # 用例 8：合成稿末节核 —— 场序被打乱 → 第 21 条必须红
        d = tmp / "sample_bad"
        d.mkdir(parents=True, exist_ok=True)
        bad_sample = d / "ch8-sample.md"
        src = ROOT / "manuscripts" / "ch8-sample.md"
        if src.exists():
            txt = src.read_text(encoding="utf-8")
            txt = txt.replace("## B3 · 走廊", "## B9 · 走廊", 1)
            bad_sample.write_text(txt, encoding="utf-8")
            files = _copy_slices(real, d / "slices")
            order_red = not run_gate(files, verbose=False, sample_path=bad_sample)
            print(f"  [{'OK' if order_red else 'FAIL'}] 用例8：合成稿末节改成 B9 → 判红（第 21 条能失败）")
            results.append(order_red)
        else:
            print("  [跳过] 用例8：合成稿不存在 → 无法做末节核负向测试")
            results.append(False)

        allok = all(results)
        print(f"  → 负向自测{'全部通过' if allok else '有项失败'}")
        return allok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--prove":
        print("── ch8 正文段门禁 · 负向自测（--prove）──")
        return 0 if prove_can_fail() else 1
    files = [ROOT / "manuscripts" / f"ch8-{s}.md" for s in SLICES]
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"[FAIL] 缺切片文件：{[str(f) for f in missing]}")
        return 1
    return 0 if run_gate(files) else 1


if __name__ == "__main__":
    sys.exit(main())
