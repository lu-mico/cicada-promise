# ch6 S1／S2 十一条 · 人工回核清单（复审方用）

📌 **出处**：peer instance（`agent:main:discord:channel:1473450501168300113`）2026-11-20 06:23 起草于 `/tmp/ch6_11items_checklist.md` → **认可记录方 Mico 06:3x 落仓**（/tmp 版会随重启消失 → 判据必须落仓，纪律 9）。
📌 **锚点已逐条实测**（2026-11-20 06:2x，11/11 命中且行号完全一致）：`我不并` A1:123 · `我不连` A2:147 · `有一句话我没有写` A3:75 · `经手登记本摊在桌角` A1:141＋A2:157 · `按了两下` A1:139＋A3:161 · `扣好搭扣` A1:143 · `桌上那只碗` B3:145 ＋ `桌上那个纸包` B3:165 · `衣袋里见过` B3:71。
📌 **改动面基线** = tag **`ch6-criteria-frozen`**（判据冻结那一刻；作者改稿即在它之后）→ 不要用固定的 sha，改稿可能分多笔。

所有命令在仓库根就地跑：`cd ~/.openclaw/workspace-yomi/projects/cicada-promise`

## 先看改动面（决定哪些条目可能真被改）

```bash
git diff --stat ch6-criteria-frozen..<sha> -- manuscripts/
git diff ch6-criteria-frozen..<sha> -- manuscripts/ | head -400
```

## S1（2 条）

| # | 要求 | 回核命令／判据 | 结论 |
|---|---|---|---|
| **1** | 周睿读到「张扬」要有反应（加一拍 ≤120 字，不写推断、不与父亲并读） | `grep -n "张扬" manuscripts/ch6-A2.md manuscripts/ch6-A3.md` → A2 原 `:95`「后头两个字：张扬」处必须有「停笔／翻回看栏名／这名字在案卷封面上」一类动作；**不得**出现把张扬与父亲并读的推断句 | |
| **2** | 「人命案」只留 A1 收文登记；A2 调解书案由改法定词；A3 记一句「两处案由不一样」；A3 写「这一册里没有死者的姓名」（归待查，不判死因）；赔偿额随案由调整 | ① `grep -n "人命案" manuscripts/ch6-*.md` → **A2 应 0 处**（只在 A1）<br>② `grep -n "案由" manuscripts/ch6-A3.md` → 有「两处案由不一样」<br>③ `grep -n "死者" manuscripts/ch6-A3.md` → 有「没有死者的姓名」<br>④ `grep -n "4,200\|4200" manuscripts/ch6-A2.md` → 金额是否随案由调整<br>⑤ **⚠️ 承重墙三条（item 2 照字面改会打断本章脊柱「三个字」，必须同时查）**：<br>　`grep -n "多留了半个字" manuscripts/ch6-A2.md` → 该字距指认**要么整段挪走、要么改挂责任栏**，不能留着一段比同一串三个字的话<br>　`sed -n '41p' manuscripts/ch6-A3.md` → 第二张（调解书）的案由栏**不得**再断言「三个字，同一笔字」<br>　`sed -n '184p' manuscripts/ch6-A2.md` → 写作说明不得再写「案由栏三字与夹页同笔同一人填」（除非调解书案由栏仍是**同一串**三个字） | |

> 📌 **item 2 的 ① 单独用会漏**：作者若只把 A2 的案由换成四字法定词、却把 `A2:45-49` 的字距指认原样留着，`grep 人命案 → A2 0 处` **照样通过**，而本章脊柱已经断了 → **⑤ 才是 item 2 的硬判据**。修法见 `tracks/ch6-review-merge.md` §二·执行注记（item 2）。

## S2 必改（9 条）

| # | 要求 | 回核命令／判据 | 结论 |
|---|---|---|---|
| **3** | A3 无新证据不得落「顶名」：走 (a) 读询问笔录正文／(b) 对照两处「姓而无名」／或 **M4**；都不加 → 「顶名」只留心里，结论栏止于「名与事，不在一处」 | `grep -n "顶名" manuscripts/ch6-A3.md`；`grep -n "名与事" manuscripts/ch6-A3.md` → 若采用 M4，(a) 或 (b) 必须真出现新证据段；否则「顶名」不得出现在**结论栏** | |
| **4** | §七「归待查」与备注栏必须自洽（备注补第四行，或 §七 末句改「这一栏不归我今天这张纸」） | `sed -n '95,150p' manuscripts/ch6-A3.md` → §七 与备注三行是否互相兑现；若补第四行，检查原收束意象「三个点排成一条竖线」是否已换（不换＝为新三行设计的意象套四行） | |
| **5** | B3 删「我在你妈衣袋里见过一回」，改从药铺端反查，不新增道具 | `grep -n "衣袋里见过\|药铺" manuscripts/ch6-B3.md` → 「衣袋里见过」0 处；有「问了两家药铺／褐瓶上的签问过药铺」一类 | |
| **6** | A3 §八 六行压到三行；省下篇幅给「手往前伸一寸」的动作（抄卷号与「附」字夹进自己夹子，不预告下章） | `sed -n '105,190p' manuscripts/ch6-A3.md`；对比 `git diff ch6-criteria-frozen..<sha> -- manuscripts/ch6-A3.md` 的字数变化；`python3 tracks/check_line_totals.py --chapter ch6` 看 A 线是否仍在带内 | |
| **7** | 六场收束改三场（一场落声音／一场落别人动作／一场落短对白）；B3 否定句删一半 — **禁区：不许顺手改「车灯」「瓶底旧痕」两处呼应** | `zsh tracks/ch6_review_chain.sh` 第 [4] 节必须仍全 OK（车灯 2／旧痕 2／瓶底+旧痕 2）；`sed -n` 各场末段看是否仍「末段落具体动作或物件」 | |
| **8** | A1 核对章句换框（保留「第一下没按匀」）、删签名句与「写完合上本子，扣好搭扣」；「按了两下」只留 A3，A1 换别的失误 | `grep -n "按了两下" manuscripts/ch6-A1.md manuscripts/ch6-A3.md` → **A1 0 处、A3 保留**；`grep -n "扣好搭扣" manuscripts/ch6-A1.md` → 0 处；`grep -n "第一下没按匀" manuscripts/ch6-A1.md` → 保留 | |
| **9** | 「很容易—但我不做」模板三次要拆：A1 改「我在第三行前面空了一行，没有再往下写」／A2 改「我把两张纸错开半寸，压上镇纸」／A3 §五 整节删或换动作；A1／A2 写作说明两条边界指针同步改 | `grep -n "我不并\|我不连\|有一句话我没有写" manuscripts/ch6-*.md` → 三处应消失或换形；`sed -n '165,200p' manuscripts/ch6-A1.md`、`sed -n '185,200p' manuscripts/ch6-A2.md` 看写作说明指针是否同步 | |
| **10** | A1／A2 签名段换形：A2 删「经手登记本摊在桌角」入口（改「她把本子推过来／笔递过来」）；**A2 只写姓、名留空** | `grep -n "经手登记本摊在桌角" manuscripts/ch6-A2.md` → 0 处；`grep -n "经手登记本摊在桌角" manuscripts/ch6-A1.md` → 允许 1 处（A1 保留）；`sed -n '150,170p' manuscripts/ch6-A2.md` 看是否只写姓 | |
| **M1** | B3「桌上那只碗」指代修：`:145` → 「压在门槛上那只碗底下」；`:165` → 「把门槛上那只碗掀开，纸包拿起来。纸是干的……」 | `grep -n "桌上那只碗\|桌上那个纸包" manuscripts/ch6-B3.md` → **0 处**；`grep -n "门槛上那只碗" manuscripts/ch6-B3.md` → ≥2 处；「纸是干的」必须有因（碗扣着／露水进不去） | |

## 另三条（不是十一条，但复审必过）

| 项 | 命令 | 结论 |
|---|---|---|
| 硬门禁 0（A1 §九／A2 §十 两条必须消失） | `python3 tracks/ngram_scan.py --chapter ch6`（或全链第 [2] 节）→ **退出码 0**，跨章硬门禁 0 命中 | |
| ch5 一字未改 | 全链第 **[5]** 节 → `[OK]`（基线 `e1ed9ef`，diff 空 · log 空 · 工作树干净） | |
| A2:184 与 merge 表 §九 第 1 条逐字比 ＋ 18／19／20 回源核引用出处 | `sed -n '180,190p' manuscripts/ch6-A2.md` 与 `tracks/ch6-review-merge.md` §九 第 1 条并排；18／19／20 的「不需改」理由逐条回源 | |

## M4（若被采用，额外两条）

- `ch5-A2.md:161`「死亡登记：八月，病故。附卷：治安，未结。」↔ `ch6-A2.md:127` 的落差必须在 **A3 兑现**（新证据段落在 A3）。
- **ch5 一个字未改**（第 [5] 节，机器判据）。

## 全链与自测

```bash
zsh tracks/ch6_review_chain.sh            # 全链：退出码非 0 = 有门禁红（改稿前 ngram 红 ⇒ 正常读数）
zsh tracks/ch6_review_chain.sh --prove    # 两套负向自测（body_checks 5 + ch5_frozen 5）
python3 tracks/ch6_body_checks.py          # item 7／8 正文段口径
python3 tracks/ch5_frozen_check.py         # item 5 后半 ch5 冻结
```

📌 **判据唯一版本在仓库里**（`tracks/` 下三个脚本 ＋ merge 表 §八补遗 ＋ 本清单）→ **复审方不得再在会话里另立口径**；本清单与 merge 表若有冲突，以 merge 表（唯一对照表）为准，并把冲突报给认可记录方。
