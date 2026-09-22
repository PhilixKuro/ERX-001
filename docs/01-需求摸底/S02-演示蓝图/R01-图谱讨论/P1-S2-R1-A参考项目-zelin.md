# P1-S2-R1-A 参考项目调研：zelin-tech/erpnext_china —— 索引

> **本文件只是索引。** 原先由单个 Agent 承担的整仓调研连续失败两次（见 [P1-S2-R1-A图谱讨论.md](P1-S2-R1-A图谱讨论.md) 第 12、16 步），按用户裁决拆成三份重派，结论在下表三份报告里。本文件保留当时已落盘的基本信息，不再补填。

## 三份报告

| 范围 | 报告 | 判定 |
|---|---|---|
| 翻译 | [P1-S2-R1-A参考项目-zelin-翻译.md](P1-S2-R1-A参考项目-zelin-翻译.md) | 四条已知缺陷只解决第 4 条；用了 32 条 `context` 但解不了撞名；18297 条中仅 748 条覆盖官方；四条确定译错 |
| 中国财税能力 | [P1-S2-R1-A参考项目-zelin-财税.md](P1-S2-R1-A参考项目-zelin-财税.md) | **真做了财税且是其主体**——账务侧（4 份科目表 + 增值税模板 + 三张报表）有，票据侧（发票/金税/对账）全无；四处配置层缺陷会静默上线 |
| 接入机制与代码质量 | [P1-S2-R1-A参考项目-zelin-机制.md](P1-S2-R1-A参考项目-zelin-机制.md) | 走完了 monkeypatch → 纯 hook 的迁移；未用 `regional_overrides`；3 处复刻上游方法体；`fixtures/` 是死文件。含应翻译 Agent 请求的交叉确认一节 |

## 当时已落盘的基本信息

- 调研对象：`D:\ERX-001\Reference\zelin-tech-erpnext_china\`
- **上游地址：`https://gitee.com/yuzelin/erpnext_china.git`**（README 给出的安装源，**主仓在 Gitee 而非 GitHub**；本项目是从 GitHub 镜像克隆的）
- 仓库规模：93 个文件（不含 `.git`），51 个提交
- 调研日期：2026-09-23
