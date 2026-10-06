# P1-S5-R7 回执（D 阶段：代码）

**轮次**：P1-S5-R7  
**日期**：2026-10-06  
**执行者**：Codex  
**依据**：[R6-C 开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)  
**状态**：代码已落地，等待 E 阶段复核

## 执行结果

| 任务 | 结果 | 实际变更 |
|---|---|---|
| TS-017 公司删除清理 | 已实现，待集成验证 | `Company.on_trash` 清理当前公司的 `Expense Claim Account`；中式公司同时清理其 `Tax Rule`；删除逻辑不使用 `force`。 |
| TS-018 保存前预配与回退科目 | 已实现，待集成验证 | 新增 `Company.validate`；已有中式公司保存前补齐报销类型科目；未匹配类型按名称或翻译匹配，最终回退到 `5602250`。 |
| TS-019 复制建账重挂 | 已实现，待集成验证 | 公司更新时扫描无编号报销科目，改挂到映射科目；有 GL Entry 或链接阻止删除的旧科目保留并记录结果；删除不使用 `force`。 |
| TS-020 全量回归与收尾 | 未完成 | 尚未运行 bench 集成测试，也未完成回执后的 E 阶段复核。 |

## 修改文件

- `frappe_china/accounting/company.py`
- `frappe_china/accounting/hr.py`
- `frappe_china/hooks.py`
- `frappe_china/cn_tax/data/company_defaults.json`

## 已执行验证

```text
python -m py_compile frappe_china/accounting/company.py frappe_china/accounting/hr.py frappe_china/hooks.py
git diff --check
```

上述静态检查通过。

## 尚未验证

- `bench --site test.localhost run-tests --module frappe_china.tests.test_company_hr_lifecycle`
- HRMS 已安装时的 `Expense Claim Type` 全量枚举与翻译名称匹配
- 删除有 GL Entry 的公司时的事务回滚
- 中式公司和 Standard 公司删除、复制建账的真实数据库行为
- 全量回归数量与 R5 基线的对比

## 下一步

进入 R7 后续 E 复核，先在测试站点运行生命周期专项测试；若测试发现实现与 SL-011/SL-012 验收条件不符，回到 C 阶段修订方案后再执行。