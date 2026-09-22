# V-02 探针：把 unverified/cn_l10n_chart_china.json 整理成可用模板的工作量测量。
# 做法：不猜工时，先把"要改多少处"数清楚，再按可核对的口径折算。
# 纯静态分析 + 与已 verified 的国家模板做对照，不连站点。
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
COA = os.path.join(
    HERE, "..", "frappe-bench", "apps", "erpnext", "erpnext", "accounts",
    "doctype", "account", "chart_of_accounts",
)

META = {"root_type", "account_type", "account_number", "is_group", "tax_rate",
        "account_name", "disable_account_type_validation"}


def walk(node, depth=1):
    """返回 (科目节点数, 最大层级, 各元字段已填数)"""
    cnt = 0
    maxd = depth
    filled = {"root_type": 0, "account_type": 0, "account_number": 0}
    for k, v in node.items():
        if k in META:
            if k in filled and str(v).strip():
                filled[k] += 1
            continue
        cnt += 1
        if isinstance(v, dict):
            c, d, f = walk(v, depth + 1)
            cnt += c
            maxd = max(maxd, d)
            for kk in filled:
                filled[kk] += f[kk]
    return cnt, maxd, filled


def count_meta_slots(node):
    """数「有多少个科目节点需要被赋 root_type/account_type/account_number」。"""
    n = 0
    for k, v in node.items():
        if k in META:
            continue
        n += 1
        if isinstance(v, dict):
            n += count_meta_slots(v)
    return n


def analyze(path, label):
    d = json.load(open(path, encoding="utf-8"))
    tree = d.get("tree", {})
    cnt, maxd, filled = walk(tree)
    print(f"--- {label} ---")
    print(f"  文件: {os.path.basename(path)}")
    print(f"  顶层节点: {len(tree)}   全部科目节点: {cnt}   最大层级: {maxd}")
    print(f"  已填 root_type: {filled['root_type']}  account_type: {filled['account_type']}"
          f"  account_number: {filled['account_number']}")
    print(f"  元字段: disabled={d.get('disabled')} country_code={d.get('country_code')}")
    # 有子节点的顶层科目
    kids = [k for k, v in tree.items()
            if isinstance(v, dict) and [x for x in v if x not in META]]
    print(f"  有子科目的顶层节点: {len(kids)}")
    return {"top": len(tree), "nodes": cnt, "depth": maxd, "filled": filled,
            "with_kids": len(kids)}


def main():
    cn = analyze(os.path.join(COA, "unverified", "cn_l10n_chart_china.json"),
                 "中国（unverified，待整理）")

    print()
    print("=== 对照：已 verified 的国家模板长什么样 ===")
    vdir = os.path.join(COA, "verified")
    samples = [f for f in sorted(os.listdir(vdir)) if f.endswith(".json")][:6]
    for f in samples:
        analyze(os.path.join(vdir, f), f"verified/{f}")

    print()
    print("=== 工作量测量（按「要动多少处」算，不按感觉算）===")
    n = cn["nodes"]
    print(f"1) 补 root_type：需赋值节点数 = {cn['top']}（仅顶层需显式声明，"
          f"create_charts 里子科目继承父级 root_type —— chart_of_accounts.py:22-24）")
    print(f"2) 补 account_type：真正需要指定的是有语义的科目（现金/银行/应收/应付/存货/"
          f"税金/固定资产/累计折旧/成本 等），其余可留空；")
    print(f"   全部节点 {n} 个，其中需指定 account_type 的按 ERPNext 语义类型约 20-30 个")
    print(f"3) 补 account_number：{n} 个节点全要编号（财会[2006]3号有标准编号，可查表照抄）")
    print(f"4) 按五大类重组：当前 {cn['top']} 个顶层节点全平铺（只有 1 个有子科目），"
          f"需建 资产/负债/权益/收入/费用 5 个 root + 若干中间层，把 {cn['top']} 个节点归位")
    print(f"5) 清理废止科目：含「营业税」的科目需删（营业税已于 2016 年全面改征增值税）")
    print()
    print("=== 折算 ===")
    print("可核对的量：顶层归类 82 处 + 编号 103 处 + account_type 20-30 处")
    print("            + 建 5 大类及中间层 + 删废止科目若干")
    print("另需：建完后实际建公司跑一遍，核对 create_charts 不报错、")
    print("      报表（资产负债表/利润表）能出数、default_receivable/payable_account 能自动取到")
    print()
    print("注意：本探针只给出「要动多少处」的客观计数；")
    print("      人日折算取决于执行者对中国会计科目表的熟悉度，见待验表实际观察列。")


main()
