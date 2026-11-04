# ch4 去 AI 味处置报告（Yomi · 2026-11-04）

> 对象：六场切片 `manuscripts/ch4-A1.md` … `ch4-B3.md` → 重合成 `manuscripts/ch4-sample.md`
> 口径：`story-deslop` v1.0.0 `deslop-gates.md`；**只改表达，不改剧情功能**
> 机器清单来源：`tracks/ch4-deslop-worklist.md`（9 blocking / 3 advisory）

## 一、结果

| 项 | 处理前（合成稿 v0.1） | 处理后 |
|---|---|---|
| blocking | 9 | **0** |
| advisory | 3 | **2**（均为法定例外） |
| `check.py` | ERROR 0 | **ERROR 0，退出码 0** |
| 字数（正文段） | A 4,228 / B 4,098 | A 4,216 / B 4,046 |

切片层面改动合计：32 → 34 行（6 个文件）。

## 二、blocking 逐条处置

1. **not-is-comparison ×6**（L59 注销/迁出/没有；L198 琥珀色/旧茶；L210 空的/薄的；L373 三个「不是…是…」；L425 一户人家/一句话；L713 关系/缺口；L924 照礁/知礁）
   → 一律删否定铺垫、直接写后项，或改成动作/实物呈现。示例：
   - 「不是写着"注销"。不是写着"迁出"。是**没有**。」→ 直接落到"那一格是空的"这一视觉事实，判断留给读者。
   - 「不是空的，是薄」→ 只留"薄"，用透光结果承接。
2. **em-dash ×3**（L43 / L79 的「96—97」；L924 的插入说明）
   → 数字区间改成口头念法「九六、九七」，去破折号；插入说明改逗号分句，不一律改句号。
3. **advisory：negation-pair-tic L214**
   → 「不是随手绕的。……中间不留缝，也不叠。」重写为「绕得极慢，也极匀。」——保留"手艺人的稳"，去掉英文式否定节奏。

## 三、保留项（法定例外，非遗漏）

- **quote-emphasis-tic L33**「补充核对」：档案字段的转述，引号有实义（区分"登记事由原文"与他人评价），保留。
- **formulaic-parallelism L1028**：位于文末「写作说明（评审参考）」，属元信息区，非正文；按 `check.py` 正文段口径不计入 blocking。
- 同理 A2 切片 `## 写作说明` 表格内两条 not-is-comparison 命中，为元信息误判，正文段内 **0 命中**。

## 四、复现命令

```bash
cd projects/cicada-promise
python3 tracks/compose.py --chapter ch4
python3 tracks/check.py manuscripts/ch4-sample.md          # 退出码须 0
node ~/.openclaw/workspace-yomi/skills/story-deslop/scripts/check-ai-patterns.js --json manuscripts/ch4-sample.md
```

## 五、未做（留给评审）

- 剧情功能、场景功能、双线交错节拍**一处未动**；本章的 S1/S2 判断交 `story-review`，本报告不代出评审结论。
- ch4 v1.0 定稿仍差最后一步：**评审**。
