#!/usr/bin/env python3
"""ch7 v1.0 正文段口径门禁 —— 依据 tracks/ch7-daily.md §八之二～§八之五（D1／D3／D4）。

口径（改稿方与复审方跑**同一条命令**）：

1) **只扫正文段**：用 `check.slice_bodies()` 的口径切出正文段（不含标题行，
   到「## 写作说明」为止）。
   为什么：每场末尾的「## 写作说明」表格里写着「胸针 0 次」「不出现合照」
   「不提治-17、不提顶名」「不写收拾东西」「不进病房、不进学校」「「三十」0 次」
   这类**规则说明行**——裸 `grep` 会把**规则说明本身**当成违规命中（假阳性）。
   **裸 grep 在干净稿上就是红的**，见 `--prove` 用例 2。

2) **台词数的正确拆法（2026-11-23 主编实测纠正）**：
   * B 线引号台词**总数 14**（B1 3 ＋ B2 5 ＋ B3 6）＝ 母亲 13 ＋ 晓晓 1。
     母亲说话**合法且必需**（D5：「他来过没有」由母亲一句话交代；ch6 B3 亦然）
     → **不能**把「B 线台词总数」判成 1（那是尺子罚合格稿）。
   * 晓晓唯一那一句用**字面＋全章**判：「晃眼。」== 1（B3 §九，D4 附则②）。
   * 机器只判**总量**（防多一句／少一句）＋「晃眼。」恰好一次；
     **说话人归属（谁在说）正文里无法机械切分 → 列为人工核对项**，
     复审方逐场读；脚本只打印引号句清单，不硬判说话人。

3) **期望值的作用域与实测值**（2026-11-23 主编在 HEAD 六场齐的合格产物上实测）：

   | # | 语义 | 作用域 | 判据 | 实测 |
   |---|------|--------|------|------|
   | 1 | D4 附则②：晓晓全章只说这一句 | 全章 | 字面「晃眼。」 | **1** |
   | 2 | B 线引号台词总数（口径锁；母亲 13 ＋ 晓晓 1） | B1／B2／B3 | `“([^”]*)”` 对数 | **14** |
   | 3 | A 线引号台词总数（口径锁） | A1／A2／A3 | 同上 | **78**（38／20／20） |
   | 4 | 年份数字 0 个（全章；B 线是红线） | 全章 | `(18|19|20)\\d{2}` | **0** |
   | 5 | 禁「三十年前」年数跨度 | 全章 | 字面「三十」 | **0** |
   | 6 | 誓言词零出现 | 全章 | 永远／永不／一辈子／到死 | **0**（四个各 0） |
   | 7 | B 线誓言符号零出现 | 全章 | 拉丁大写「L」 | **0** |
   | 8 | 蝉蜕胸针 ch7 零出现（ch8 物证） | 全章 | 字面「胸针」 | **0** |
   | 9 | 合照 ch7 零出现（D1：1996 合照＝ch8 物证） | 全章 | 字面「合照」 | **0** |
   | 10 | D3：周睿不得落判断 | 全章 | 「他就是」「也许就是」 | **0** |
   | 11 | D3：不接 ch6 定论 | 全章 | 「治-17」「顶名」 | **0** |
   | 12 | D3／B 线：不推死因、不落「他认识夏晓晓」 | 全章 | 「死因」「他认识夏晓晓」 | **0** |
   | 13 | D4 禁项：不预告 ch8 死亡 | 全章 | 收拾东西／送人／烧掉／烧信 | **0** |
   | 14 | B 线三场场景禁项 | **只** B1／B2／B3 | 张扬／病房／学校 | **0** |

   作用域说明（纪律：尺子不得大于被量的事实）：
   * 第 14 条是 **B 线**约束 → 只查 B1／B2／B3。把「病房」写进 A 线
     （2026 年的医院走廊）是合法的，不该被罚（`--prove` 用例 7）。
   * 第 10 条只抓**判断**的固定搭配（「他就是」「也许就是」）；A3 正文里的
     「**就是**昨天那只。」（`manuscripts/ch7-A3.md:25`，说明盒子是哪只）
     是合法陈述，不误伤（`--prove` 用例 6）。

4) **期望值是「口径锁」，不是永久常量**：
   来源 ＝ **最近一次实测**（2026-11-23，对象 = HEAD `50e92d7`，六场齐）。
   作者的改稿落地后，**由主编当场重测并更新本文件、附重测记录**（落仓），
   再让复审方跑链。→ **复审方看到红，先看本表日期与 HEAD，不要先假定作者写错。**

用法：
    python3 tracks/ch7_body_checks.py           # 跑门禁（退出码非 0 = FAIL）
    python3 tracks/ch7_body_checks.py --prove   # 证明**每条**判据都能失败（负向自测）
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

SLICES = ["A1", "A2", "A3", "B1", "B2", "B3"]
B_SLICES = ["B1", "B2", "B3"]

# 口径锁：2026-11-23 主编实测（HEAD 50e92d7，六场齐）。改稿后由主编重测更新。
QUOTE_TOTALS = {"A": 78, "B": 14}   # A1 38 · A2 20 · A3 20 ／ B1 3 · B2 5 · B3 6
QUOTE_RE = re.compile(r"“([^”]*)”")
YEAR_RE = re.compile(r"(?<!\d)(?:18|19|20)\d{2}(?!\d)")

# (编号, 语义, 作用域, 类型, 词表, 期望值)
ITEMS = [
    (1, "「晃眼。」（晓晓全章唯一一句，D4 附则②）", "ALL", "literal", ["晃眼。"], 1),
    (2, "B 线引号台词总数（口径锁：母亲 13 ＋ 晓晓 1）", "B", "quote_total", None, QUOTE_TOTALS["B"]),
    (3, "A 线引号台词总数（口径锁）", "A", "quote_total", None, QUOTE_TOTALS["A"]),
    (4, "阿拉伯年份（全章；B 线为红线）", "ALL", "year", None, 0),
    (5, "「三十」（禁年数跨度）", "ALL", "literal", ["三十"], 0),
    (6, "「永远」族誓言词", "ALL", "literal", ["永远", "永不", "一辈子", "到死"], 0),
    (7, "「L」（B 线誓言符号）", "ALL", "literal", ["L"], 0),
    (8, "「胸针」（ch8 物证，ch7 零出现）", "ALL", "literal", ["胸针"], 0),
    (9, "「合照」（ch8 物证，D1 禁项）", "ALL", "literal", ["合照"], 0),
    (10, "D3 判断句（他就是／也许就是）", "ALL", "literal", ["他就是", "也许就是"], 0),
    (11, "「治-17」／「顶名」（不接 ch6 定论）", "ALL", "literal", ["治-17", "顶名"], 0),
    (12, "死因／他认识夏晓晓（D3 边界）", "ALL", "literal", ["死因", "他认识夏晓晓"], 0),
    (13, "D4 禁项（收拾东西／送人／烧掉／烧信）", "ALL", "literal",
     ["收拾东西", "送人", "烧掉", "烧信"], 0),
    (14, "B 线场景禁项（张扬／病房／学校）", "B", "literal",
     ["张扬", "病房", "学校"], 0),
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
    if scope == "ALL":
        return True
    return name.startswith(f"ch7-{scope}")


def scan_literal(data, scope, tokens):
    """返回 [(文件, 绝对行号, 标题, 命中词, 次数, 行片段)]，只扫作用域内正文段。"""
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


def evaluate(files):
    """返回 (结果列表, 是否通过)。"""
    data = collect(files)
    results = []
    for num, sem, scope, kind, tokens, want in ITEMS:
        info = ""
        if kind == "quote_total":
            got, per, lines = scan_quote_total(data, scope)
            where = [f"{name} {n} 句" for name, n in sorted(per.items())]
            info = "说话人归属＝人工核对项（机器只判总量）：" + "／".join(
                f"{name}:{ln}「{q}」" for name, ln, q in lines[:8]
            ) + ("…" if len(lines) > 8 else "")
        elif kind == "year":
            hits = scan_years(data, scope)
            got = sum(h[4] for h in hits)
            where = [f"{n}:{ln} [{t}] {tok} → {snip}" for n, ln, t, tok, _, snip in hits]
        else:
            hits = scan_literal(data, scope, tokens)
            got = sum(h[4] for h in hits)
            where = [f"{n}:{ln} [{t}] 「{tok}」→ {snip}" for n, ln, t, tok, _, snip in hits]
        results.append(dict(num=num, sem=sem, scope=scope, ok=(got == want),
                            got=got, want=want, where=where, info=info))
    return results, all(r["ok"] for r in results)


def run_gate(files, verbose=True):
    results, ok = evaluate(files)
    if verbose:
        print("── ch7 正文段口径门禁（D1／D3／D4 ＋ B 线红线）──")
        for r in results:
            flag = "OK  " if r["ok"] else "FAIL"
            scope = "全章" if r["scope"] == "ALL" else f"{r['scope']} 线"
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
    """负向自测：干净稿必须绿；坏写法必须红；作用域不许误伤合格稿。"""
    real = [ROOT / "manuscripts" / f"ch7-{s}.md" for s in SLICES]
    for f in real:
        if not f.exists():
            raise SystemExit(f"缺文件：{f}")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ch7_body_selftest_"))
    try:
        results = []

        # 用例 1：干净稿 → 必须**绿**
        clean_dir = tmp / "clean"
        clean = _copy_slices(real, clean_dir)
        ok_clean = run_gate(clean, verbose=False)
        print(f"  [{'OK' if ok_clean else 'FAIL'}] 用例1：干净稿 → 14 条全绿（必须绿）")
        results.append(ok_clean)

        # 用例 2：旧口径（裸 grep 扫全文，含写作说明）→ 干净稿**必须红**
        raw = {}
        for f in real:
            text = f.read_text(encoding="utf-8")
            for _, _, _, _, tokens, _ in ITEMS:
                for tok in tokens or []:
                    raw[tok] = raw.get(tok, 0) + text.count(tok)
        raw_hit = {k: v for k, v in raw.items() if v}
        old_red = bool(raw_hit)
        shown = "／".join(f"{k} {v}" for k, v in sorted(raw_hit.items())[:6])
        print(
            f"  [{'OK' if old_red else 'FAIL'}] 用例2：旧口径（裸 grep 扫全文）在干净稿上判红"
            f"（规则说明表里的 {shown} … 全被误命中）→ 证明必须用正文段口径"
        )
        results.append(old_red)

        # 用例 3：逐条注入 —— **每条字面判据**都要能被打红（判据要能失败）
        injected = []
        for num, sem, scope, kind, tokens, want in ITEMS:
            if kind != "literal":
                continue
            d = tmp / f"inj{num}"
            files = _copy_slices(real, d)
            target = d / "manuscripts" / "ch7-B3.md"
            ok_insert = _insert_before_write_notes(target, f"自测：{tokens[0]}。")
            red = not run_gate(files, verbose=False)
            injected.append((num, tokens[0], ok_insert and red))
        all_inj = all(x[2] for x in injected)
        bad = ", ".join("#%d %s" % (n, t) for n, t, ok in injected if not ok)
        print(
            f"  [{'OK' if all_inj else 'FAIL'}] 用例3：{len(injected)} 条字面判据逐条注入 → 条条判红"
            f"（{'全部打红' if all_inj else '未打红：' + bad}）"
        )
        results.append(all_inj)

        # 用例 3b：B 线塞阿拉伯年份 → 第 4 条必须红
        d = tmp / "inj_year"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch7-B3.md", "自测：那一年是一九九六年，墙上有 1996 四个数字。"
        )
        year_red = not run_gate(files, verbose=False)
        print(f"  [{'OK' if ok_insert and year_red else 'FAIL'}] 用例3b：B 线正文塞阿拉伯年份 → 判红（第 4 条能失败）")
        results.append(ok_insert and year_red)

        # 用例 4：正文塞**第二句** B 线台词 → B 线台词总数 15 → 第 2 条必须红
        d = tmp / "mut_line"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch7-B3.md", "“嗯。”我说。"
        )
        line_red = not run_gate(files, verbose=False)
        print(f"  [{'OK' if ok_insert and line_red else 'FAIL'}] 用例4：B3 正文塞第二句「“嗯。”我说。」→ 台词总数 15 → 判红（第 2 条能失败）")
        results.append(ok_insert and line_red)

        # 用例 4b：把她唯一那一句拿掉 → 第 1 条**必须红**（「晃眼。」恰好 1，不是 ≥1）
        d = tmp / "mut_noline"
        files = _copy_slices(real, d)
        b3 = d / "manuscripts" / "ch7-B3.md"
        before = b3.read_text(encoding="utf-8")
        b3.write_text(before.replace("“晃眼。”我说。", "我没有答。"), encoding="utf-8")
        changed = b3.read_text(encoding="utf-8") != before
        zero_red = not run_gate(files, verbose=False)
        print(f"  [{'OK' if changed and zero_red else 'FAIL'}] 用例4b：抹掉「晃眼。」→ 判红（证明是「恰好一句」不是「至少一句」）")
        results.append(changed and zero_red)

        # 用例 4c：A 线多一句台词 → A 线台词总数 79 → 第 3 条必须红
        d = tmp / "mut_aquote"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch7-A2.md", "“几点了。”他问。"
        )
        a_red = not run_gate(files, verbose=False)
        print(f"  [{'OK' if ok_insert and a_red else 'FAIL'}] 用例4c：A2 正文多一句台词 → A 线总数 79 → 判红（第 3 条能失败）")
        results.append(ok_insert and a_red)

        # 用例 5：口径锁复现（A 78／B 14）＋ 母亲台词在多句里合法存在
        data = collect(real)
        a_total, a_per, _ = scan_quote_total(data, "A")
        b_total, b_per, _ = scan_quote_total(data, "B")
        ok_lock = (a_total == QUOTE_TOTALS["A"] and b_total == QUOTE_TOTALS["B"])
        print(
            f"  [{'OK' if ok_lock else 'FAIL'}] 用例5：台词总数口径锁复现 A {a_total}／B {b_total}"
            f"（期望 78／14；B 线含母亲 13 句）"
        )
        results.append(ok_lock)

        # 用例 6：合法的边界表述不得误伤（A3「就是昨天那只。」）
        boundary = [line.strip() for f in real for line in f.read_text(encoding="utf-8").split("\n")
                    if "就是昨天那只" in line]
        boundary_sentence = boundary[0].split("。")[0] + "。" if boundary else "<未找到>"
        ok_green = ok_clean and bool(boundary)
        print(
            f"  [{'OK' if ok_green else 'FAIL'}] 用例6：A3 正文合法句「{boundary_sentence}」"
            f"（含「就是」）→ 干净稿仍绿（证明第 10 条只抓「他就是／也许就是」判断搭配）"
        )
        results.append(ok_green)

        # 用例 7：把 B 线禁项写进 **A 线** → 必须**仍绿**（作用域不得罚 A 线）
        d = tmp / "scope_a"
        files = _copy_slices(real, d)
        ok_insert = _insert_before_write_notes(
            d / "manuscripts" / "ch7-A1.md", "走廊尽头是病房，病房的门半开着。"
        )
        scope_green = run_gate(files, verbose=False)
        print(f"  [{'OK' if ok_insert and scope_green else 'FAIL'}] 用例7：把「病房」写进 A1（2026 年医院走廊，合法）→ 仍绿（第 14 条只罚 B 线）")
        results.append(ok_insert and scope_green)

        allok = all(results)
        print(f"  → 负向自测{'全部通过' if allok else '有项失败'}")
        return allok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--prove":
        print("── ch7 正文段门禁 · 负向自测（--prove）──")
        return 0 if prove_can_fail() else 1
    files = [ROOT / "manuscripts" / f"ch7-{s}.md" for s in SLICES]
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"[FAIL] 缺切片文件：{[str(f) for f in missing]}")
        return 1
    return 0 if run_gate(files) else 1


if __name__ == "__main__":
    sys.exit(main())
