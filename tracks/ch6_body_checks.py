#!/usr/bin/env python3
"""ch6 v1.0 正文段口径门禁 —— 对应 tracks/ch6-review-merge.md §八 item 7／8。

口径（2026-11-20 复核更正，落仓版；改稿方与复审方跑同一条命令）：

1) **只扫正文段**：用 `check.slice_bodies()` 切出的 body_no_head（不含标题行，
   到「## 写作说明」为止）。
   为什么：各场末尾的「## 写作说明」表格里写着「全篇不出现『父亲是被害的』
   『死因是人为』」这类**规则说明行**（A1:173 ／ A3:195）——裸 `grep` 会把**规则
   说明本身**当成违规命中（假阳性）；同一批表格行里还写着「车灯／瓶底／旧痕」，
   裸 grep 的呼应计数会偏大。**裸 grep 在干净稿上就是红的**，见 `--prove`。

2) **item 7 的期望值是三个数，不是一个**：
     · 车灯 = 2（B1 ×2）
     · 旧痕 = 2（B2 ／ B3）
     · 瓶底与旧痕同行 = 2（B2 ／ B3）
   B1 那一次单独的「瓶底」是**窄窗台铺垫**，不是呼应计数 —— 按「瓶底出现 2 次」
   判会把改稿误判成「破了呼应」。

3) **item 8（死因定性）**：正文段不得出现「父亲是被害…」「死因是人为」「被人害死」
   「有人害死」一类**定性**。注意正文**可以**出现「死因那一栏写的是『病故』」
   这类**案由／死因两栏的边界陈述**（A1 正文 body 行 112 就是）——那是本章的
   核心动作，不是违规。

用法：
    python3 tracks/ch6_body_checks.py           # 跑门禁（退出码非 0 = FAIL）
    python3 tracks/ch6_body_checks.py --prove   # 证明判据「能失败」（负向自测）
退出码：0 = 通过；1 = 有项失败。
"""

import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tracks"))
import check as ck  # noqa: E402

SLICES = ["A1", "A2", "A3", "B1", "B2", "B3"]
EXPECT = {"车灯": 2, "旧痕": 2, "瓶底+旧痕同行": 2}
BAN = ["父亲是被害", "死因是人为", "被人害死", "有人害死"]


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


def scan(files):
    """返回 (counts, where, bans)。counts 只数**正文段**。"""
    counts = {k: 0 for k in EXPECT}
    where = {k: [] for k in EXPECT}
    bans = []
    for path in files:
        for title, buf, abs_start in segments(path):
            for offset, line in enumerate(buf):
                ln = abs_start + offset
                n_lamp = line.count("车灯")
                n_mark = line.count("旧痕")
                n_bottle = line.count("瓶底")
                if n_lamp:
                    counts["车灯"] += n_lamp
                    where["车灯"].append(f"{pathlib.Path(path).name}:{ln} [{title}]")
                if n_mark:
                    counts["旧痕"] += n_mark
                    where["旧痕"].append(f"{pathlib.Path(path).name}:{ln} [{title}]")
                if n_bottle and n_mark:
                    counts["瓶底+旧痕同行"] += 1
                    where["瓶底+旧痕同行"].append(f"{pathlib.Path(path).name}:{ln} [{title}]")
                for b in BAN:
                    if b in line:
                        bans.append((pathlib.Path(path).name, ln, b, line.strip()[:60]))
    return counts, where, bans


def report(files, counts, where, bans):
    ok = True
    for key, want in EXPECT.items():
        got = counts[key]
        flag = "OK" if got == want else "FAIL"
        if got != want:
            ok = False
        print(f"  [{flag}] 有意呼应「{key}」正文段出现 {got} 次（期望 {want}）")
        for w in where[key]:
            print(f"         · {w}")
    if bans:
        ok = False
        for f, ln, b, snippet in bans:
            print(f"  [FAIL] 死因定性用语「{b}」出现在 {f}:{ln} → {snippet}")
    else:
        print("  [OK] 死因定性用语 0 命中（正文段口径）")
    return ok


def run_gate(files, verbose=True):
    counts, where, bans = scan(files)
    if verbose:
        print("── 正文段口径（§八 item 7／8）──")
        ok = report(files, counts, where, bans)
    else:
        ok = all(counts[k] == v for k, v in EXPECT.items()) and not bans
    return ok


def prove_can_fail():
    """负向自测：证明每条判据**能失败**（干净稿必须绿；坏写法必须红）。"""
    real = [ROOT / "manuscripts" / f"ch6-{s}.md" for s in SLICES]
    for f in real:
        if not f.exists():
            raise SystemExit(f"缺文件：{f}")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ch6_body_selftest_"))
    try:
        # 用例 1：干净稿 → 正文段口径必须**绿**
        copy_dir = tmp / "clean"
        (copy_dir / "manuscripts").mkdir(parents=True)
        for f in real:
            shutil.copy2(f, copy_dir / "manuscripts" / f.name)
        clean_files = [copy_dir / "manuscripts" / f.name for f in real]
        ok_clean = run_gate(clean_files, verbose=False)
        print(f"  [{'OK' if ok_clean else 'FAIL'}] 用例1：干净稿 → 正文段口径判定通过（必须绿）")

        # 用例 2：旧口径（裸 grep 扫全文）→ 干净稿**必须红**（证明旧判据不可用）
        raw_counts = {"车灯": 0, "旧痕": 0}
        raw_bans = 0
        for f in real:
            text = f.read_text(encoding="utf-8")
            raw_counts["车灯"] += text.count("车灯")
            raw_counts["旧痕"] += text.count("旧痕")
            raw_bans += sum(text.count(b) for b in BAN)
        old_red = (
            raw_counts["车灯"] != EXPECT["车灯"]
            or raw_counts["旧痕"] != EXPECT["旧痕"]
            or raw_bans > 0
        )
        print(
            f"  [{'OK' if old_red else 'FAIL'}] 用例2：旧口径（裸 grep 扫全文）在干净稿上判红"
            f"（车灯 {raw_counts['车灯']}／旧痕 {raw_counts['旧痕']}／定性命中 {raw_bans}）→ 证明必须换正文段口径"
        )

        # 用例 3：把 B1 的一处「车灯」改掉 → 呼应计数必须**红**
        mut_dir = tmp / "mut_lamp"
        (mut_dir / "manuscripts").mkdir(parents=True)
        for f in real:
            shutil.copy2(f, mut_dir / "manuscripts" / f.name)
        b1 = mut_dir / "manuscripts" / "ch6-B1.md"
        lines = b1.read_text(encoding="utf-8").split("\n")
        changed = False
        for idx, line in enumerate(lines):
            if "车灯" in line and not line.lstrip().startswith("|"):
                lines[idx] = line.replace("车灯", "车头", 1)
                changed = True
                break
        b1.write_text("\n".join(lines), encoding="utf-8")
        ok_mut = not run_gate([mut_dir / "manuscripts" / f.name for f in real], verbose=False)
        print(f"  [{'OK' if changed and ok_mut else 'FAIL'}] 用例3：B1 抹掉一处「车灯」→ 门禁判红（证明呼应计数会失败）")

        # 用例 4：正文里塞一句死因定性 → 定性检查必须**红**
        mut_dir2 = tmp / "mut_ban"
        (mut_dir2 / "manuscripts").mkdir(parents=True)
        for f in real:
            shutil.copy2(f, mut_dir2 / "manuscripts" / f.name)
        a1 = mut_dir2 / "manuscripts" / "ch6-A1.md"
        lines = a1.read_text(encoding="utf-8").split("\n")
        inserted = False
        for idx, line in enumerate(lines):
            if line.strip() == "## 写作说明":
                lines.insert(idx, "他后来才明白，父亲是被害的。")
                inserted = True
                break
        a1.write_text("\n".join(lines), encoding="utf-8")
        ok_ban = not run_gate([mut_dir2 / "manuscripts" / f.name for f in real], verbose=False)
        print(f"  [{'OK' if inserted and ok_ban else 'FAIL'}] 用例4：A1 正文塞入「父亲是被害的」→ 门禁判红（证明定性检查会失败）")

        # 用例 5：正文里合法的「死因那一栏」边界陈述**不得**误伤（干净稿必须仍绿）
        has_death_line = any(
            "死因那一栏" in line
            for f in real
            for line in f.read_text(encoding="utf-8").split("\n")
        )
        ok_green = ok_clean and has_death_line
        print(
            f"  [{'OK' if ok_green else 'FAIL'}] 用例5：正文既有「死因那一栏」边界陈述"
            f"（A1 body 行 112）不误伤 → 干净稿仍判绿（证明 ban 列表只抓**定性**）"
        )

        results = [ok_clean, old_red, ok_mut, ok_ban, ok_green]
        allok = all(results)
        print(f"  → 负向自测{'全部通过' if allok else '有项失败'}")
        return allok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--prove":
        print("── ch6 正文段门禁 · 负向自测（--prove）──")
        return 0 if prove_can_fail() else 1
    files = [ROOT / "manuscripts" / f"ch6-{s}.md" for s in SLICES]
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"[FAIL] 缺切片文件：{[str(f) for f in missing]}")
        return 1
    return 0 if run_gate(files) else 1


if __name__ == "__main__":
    sys.exit(main())
