# ch6 去 AI 味处置报告（Yomi · 2026-11-18）

> 对象：六场切片 `manuscripts/ch6-A1.md` … `ch6-B3.md` → 重合成 `manuscripts/ch6-sample.md`（v0.1）
> 口径：`story-deslop` v1.0.0 `deslop-gates.md`；**只改表达，不改剧情功能**
> 机器清单来源：`tracks/deslop_scan.py`（正文段口径 + 项目目录就地跑 detector + 行号回映射）——**blocking 3 条**
> ⚠️ **归属只认机器扫描**：Mico 口头清单两版（11-18 00:09「A1+B2」／00:40「A1+B3、B2=0」）**两版都漏了 B1**；仓库账本（§六／`ch6-daily.md` §二）从 11/14 起记的就是 A1／B1／B2，**账本是对的**。

## 一、结果

| 项 | 处理前（切片 v0.1） | 处理后 |
|---|---|---|
| blocking | 3 | **0** |
| ├ A1 `negation-parade` | 1（L93） | **0** ✅ |
| ├ B1 `not-is-comparison` | 1（L49） | **0** ✅ |
| ├ B2 `not-is-comparison` | 1（L85） | **0** ✅ |
| └ A2／A3／B3 | 0 | 0 |
| advisory | 9 | 9（全部功能性，保留，见 §四） |
| degeneration blocking | 0 | **0** ✅ |
| `check.py`（合成稿） | **ERROR 4（假阳性，R56）** | **ERROR 0，退出码 0** |
| 字数（正文段） | A 4,812／B 8,943※ | A **4,812**／B **4,504**／全章 **9,316** |
| 合计 | — | **9,316**（底线 8,400 ✓；A ≥4,100 ✓ 余 712；B ≥4,300 ✓ 余 204） |

※ B 线改前报 8,943 是 R56 口径事故的产物（末场 B3 吞进了整份章级写作说明，见 §三），不是真实字数。

切片层面改动合计：**3 个文件、3 处正文句**（A1 ×1 · B1 ×1 · B2 ×1）＋ **1 处连带措辞**（B1 折痕道数 P3）＋ **1 处 notes 首行层级**（R56）。合成稿 `ch6-sample.md` 为生成物，不直接编辑。

## 二、blocking 逐条处置（3 条正文段，全部改写）

1. **ch6-A1.md L93 · `negation-parade`** —— 原句三项否定排比（日期／签名／期限）。
   → **「写“缓办”的那一栏，日期、签名、缓到什么时候，一样也没写。」**
   门禁：删掉否定铺垫的排比架，只留三项事实本身；**同时把主语从「这两个字」换成「写‘缓办’的那一栏」**——原文上文有四个签名（传阅单），若主语含混，读者会把「签名也没写」误读成与那四个签名打架。
2. **ch6-B1.md L49 · `not-is-comparison`** —— 原句「否定铺垫 + 肯定翻转」双段式。
   → **「疼倒不疼，就是忽然没了力气，膝盖先弯下去。」**
   门禁：否定对比改成口语否定（保留叙述者否认「是疼」这层语气），后项直写；**剧情功能（腿软是虚不是伤）一字未改**。
3. **ch6-B2.md L85 · `not-is-comparison`** —— 原句「不是不能。」独立成段的否定铺垫。
   → **「嘴能张开，声音出不来，也懒得去拽。」**
   门禁：删否定铺垫，把「能开口」这一事实改成正面动作句（嘴能张开），保留「懒得去拽」的**选择意味**——闭口是选择不是失能，这是 B3 立誓的前提，**一个字都不能丢**。

## 三、连带面（自己核到全仓，不只改清单指的那一处）

1. **R56｜notes 首行标题层级 → 口径事故伪装成剧情事故（已修）**
   `tracks/ch6-notes.md` 首行原为 `# 写作说明（评审参考）`（H1），ch3／ch4／ch5 的 notes 首行都是 `##`（H2）。
   `tracks/check.py` 的正文段结束标记 `^##\s*(写作说明|下一切片|…)` **匹配不上 H1** → 整份章级写作说明被算进**末场 B3 的正文**：B3 报 5,198 字，并凭空爆出 4 项 ERROR（年数跨度 ×3／B 线年份 1979·1996·2026／B 线红线「永远」×4·「永不」×2·「一辈子」×2·「到死」×2·「L」×17／林默主题句）——**全部来自 notes 区，与正文无关**。
   **已修**：首行改回 `## 写作说明（评审参考）`；重合成后 B3 ＝ **1,441** 字，ERROR 0。
   **新铁律**：① notes 首行必须 H2；② 末场字数异常偏大（5,198 vs 他场 1,4xx–1,6xx）＝ notes 被吞的典型信号，**先查口径再谈改稿**；③ 口径事故会伪装成剧情事故（假红线、假年份、假主题句）——**先看口径，再动正文**。
2. **B1 折痕道数（P3，不阻塞，已改）**
   正文 §六原写「折痕已经有四道」，与同场「对折，再对折，折成四方」的折叠次数对不上（对折两次出三道）。
   → **「折痕已经有三道，白得发亮。」** 只改道数措辞，**不动剧情、不动折叠动作**。
3. **交付文件不得原样引用被门禁命中的句式（R43）**
   本报告与 `tracks/ch6-notes.md` §六 一律**只记改后写法**（原句以类型＋行号＋改后文本落账），不再把三条命中句原样抄进交付文件——避免整文件扫描时被自己的记录再打回来。

## 四、保留项（advisory，判定为功能性，非遗漏）

| advisory | 处数 | 位置 | 保留理由 |
|---|---|---|---|
| `quote-emphasis-tic` | A1 L45 · A2 L79 · A3 L41 | 纸面原词（“转”“病故”“人命案”等） | 引号标的是**纸上原字**，去引号即丢证据性质（ch3 已同原则留过「实未迁」） |
| `low-connective-density-tic` | A2 L13 · A3 L13 | 卷宗／调卷开篇 | 档案叙述本就该短句直给，补连接词会变成解说 |
| `micro-action-tic` | B2 L17 · B3 L57 | 病中动作补语 | 身体状态承担后果（「六个字」级微动作是病态本身），删则信息掉 |
| `negation-pair-tic` | A1 §三「两栏不在一张纸上，也不在一本册子里」／A1「三个字……没有变重，也没有变轻」／B2「她不说，我也不说」／B3「我没有点头，也没有关门」 | 4 处 | 否定对偶承担**证据逻辑**（两栏分离）、**物性**（三个字不重不轻）与**关系静默**（母子／林默都不说），是本书「纸与沉默」主题的承重句，非套式 |

## 五、未做（留给评审）

- A1 §三「一句话就成立了」与 A3 结论页的呼应、A2 两处笔迹差异写法与 A1 四签名差异写法的**递进**是否够——属结构判断，交阶段 3 四视角评审。
- B1 折痕「三道」是否与 ch6 其他场次对折动作描述一致——已自查仅本场一处，未再动。

## 六、复现命令（在项目根目录，**必须就地跑**——白名单在 `manuscripts/.deslop-whitelist`）

```bash
python3 tracks/deslop_scan.py --chapter ch6      # 逐场归属扫描（blocking 0 / advisory 9）
python3 tracks/compose.py --chapter ch6            # 重合成
python3 tracks/check.py manuscripts/ch6-sample.md  # ERROR 0，退出码 0
python3 tracks/check_line_totals.py --chapter ch6 # A 4812／B 4504／9316，全线过
python3 tracks/check_theme.py manuscripts/ch6-sample.md
python3 tracks/verify_factsource.py               # 三不变式 True
python3 tracks/gate_selftest.py                   # 门禁自测全过
```

合成稿正文段复扫（blocking 0）：

```bash
python3 - <<'PY'
import pathlib, sys, subprocess, json
sys.path.insert(0, "tracks"); import check as ck
t = pathlib.Path("manuscripts/ch6-sample.md").read_text(encoding="utf-8")
p = ck.slice_bodies(t); tmp = pathlib.Path("manuscripts/.tmp-body.md")
tmp.write_text("\n\n".join(b for _, b, _ in p), encoding="utf-8")
for s in ("check-ai-patterns.js", "check-degeneration.js"):
    r = subprocess.run(["node", f"/Users/lumico/.openclaw/workspace-yomi/skills/story-deslop/scripts/{s}", "--check", "--json", str(tmp)], capture_output=True, text=True)
    d = json.loads(r.stdout[r.stdout.find("{"):])
    print(s, "blocking", len([f for f in d["findings"] if f.get("severity") == "blocking"]))
tmp.unlink()
PY
```
