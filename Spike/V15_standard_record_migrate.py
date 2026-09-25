# V15 探针：改 standard=1 的导航记录后跑 bench migrate，改动的字段值是否被覆盖回 json 原值。
#
# 三张表分别验：Workspace Sidebar / Workspace Sidebar Item / Desktop Icon。
#
# 跑法（在 /workspace/frappe-bench 下；bench execute 无法 import /workspace/Spike，故直接跑脚本）：
#   env/bin/python /workspace/Spike/V15_standard_record_migrate.py step_snapshot
#   env/bin/python /workspace/Spike/V15_standard_record_migrate.py step_mutate
#   bench --site erx.localhost migrate
#   env/bin/python /workspace/Spike/V15_standard_record_migrate.py step_check
#   env/bin/python /workspace/Spike/V15_standard_record_migrate.py step_restore
#
# 安全约束：
#   - 每张表只改一条记录，改的都是非命名字段（Sidebar 改 header_icon 不改 title；
#     Desktop Icon 改 icon 不改 label；Item 改 label 但 Item 的 autoname 是 hash，不受 label 影响）。
#   - 改动一律加后缀 -V15TEST / 可辨识值，便于人工识别与回滚。
#   - 不删记录、不 drop/restore 库、不 reinstall。
import json
import os

import frappe

APPS = "/workspace/frappe-bench/apps"
STATE = "/workspace/Spike/V15-state.json"

# 选定的测试目标（只此三条）
SIDEBAR = "Stock"  # Workspace Sidebar，改 header_icon
ITEM_PARENT = "Stock"  # Workspace Sidebar Item 所属 sidebar
ITEM_LABEL = "Stock Entry"  # 该子行原 label，改成 label+"-V15TEST"
ICON = "Stock"  # Desktop Icon，改 icon

MARK = "-V15TEST"


def _json_path(folder, name, app=None):
    """standard 记录的 json 源路径。app 级目录布局：<app>/<app>/<folder>/<scrubbed>.json"""
    cands = [app] if app else ["erpnext", "frappe"]
    for a in cands:
        p = os.path.join(APPS, a, a, folder, frappe.scrub(name.lower()) + ".json")
        if os.path.exists(p):
            return p
    return None


def _read_json(folder, name, app=None):
    p = _json_path(folder, name, app)
    if not p:
        return None, None
    with open(p, encoding="utf-8") as f:
        return p, json.load(f)


def _snapshot():
    """三张表当前的实际字段值 + json 原值 + modified 时间戳。"""
    snap = {}

    # --- Workspace Sidebar ---
    sb = frappe.get_doc("Workspace Sidebar", SIDEBAR)
    p, j = _read_json("workspace_sidebar", SIDEBAR, sb.app)
    snap["workspace_sidebar"] = {
        "name": sb.name,
        "standard": sb.standard,
        "app": sb.app,
        "db_header_icon": sb.header_icon,
        "db_modified": str(sb.modified),
        "json_path": p,
        "json_header_icon": (j or {}).get("header_icon"),
        "json_modified": (j or {}).get("modified"),
    }

    # --- Workspace Sidebar Item（子表行）---
    parent = frappe.get_doc("Workspace Sidebar", ITEM_PARENT)
    target = None
    for it in parent.items:
        if it.label in (ITEM_LABEL, ITEM_LABEL + MARK):
            target = it
            break
    pj, jj = _read_json("workspace_sidebar", ITEM_PARENT, parent.app)
    json_labels = [i.get("label") for i in (jj or {}).get("items") or []]
    snap["workspace_sidebar_item"] = {
        "parent": ITEM_PARENT,
        "row_name": target.name if target else None,
        "db_label": target.label if target else None,
        "db_idx": target.idx if target else None,
        "db_parent_modified": str(parent.modified),
        "json_labels_head": json_labels[:8],
        "json_has_orig_label": ITEM_LABEL in json_labels,
        "json_has_marked_label": (ITEM_LABEL + MARK) in json_labels,
        "row_count_db": len(parent.items),
        "row_count_json": len(json_labels),
    }

    # --- Desktop Icon ---
    di = frappe.get_doc("Desktop Icon", ICON)
    # 注意 app_name 是 create_desktop_icons_from_workspace() 里设的运行期属性,
    # 不是 Desktop Icon 的持久化字段, 故用 get() 取而非属性访问。
    p2, j2 = _read_json("desktop_icon", ICON, di.get("app_name") or di.app)
    snap["desktop_icon"] = {
        "name": di.name,
        "standard": di.standard,
        "app": di.app,
        "app_name": di.get("app_name"),
        "icon_type": di.icon_type,
        "db_icon": di.icon,
        "db_modified": str(di.modified),
        "json_path": p2,
        "json_icon": (j2 or {}).get("icon"),
        "json_modified": (j2 or {}).get("modified"),
    }
    return snap


def _emit(tag, payload):
    print(f"===V15-{tag}-BEGIN===")
    print(json.dumps(payload, ensure_ascii=False, indent=1, default=str))
    print(f"===V15-{tag}-END===")


def step_snapshot():
    _emit("SNAPSHOT", _snapshot())


def step_mutate():
    """改三条记录的字段值，各加可辨识标记；原值存盘供回滚。"""
    before = _snapshot()
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(before, f, ensure_ascii=False, indent=1, default=str)

    # 1. Workspace Sidebar.header_icon（非命名字段）
    sb = frappe.get_doc("Workspace Sidebar", SIDEBAR)
    sb.header_icon = "bug"  # json 原值是 "stock"，换成一眼可辨的不同值
    sb.save(ignore_permissions=True)

    # 2. Workspace Sidebar Item.label（子表行；Item autoname=hash，改 label 不改行名）
    parent = frappe.get_doc("Workspace Sidebar", ITEM_PARENT)
    for it in parent.items:
        if it.label == ITEM_LABEL:
            it.label = ITEM_LABEL + MARK
            break
    parent.save(ignore_permissions=True)

    # 3. Desktop Icon.icon（非命名字段，label 才是命名字段，不动）
    di = frappe.get_doc("Desktop Icon", ICON)
    di.icon = "bug"
    di.save(ignore_permissions=True)

    frappe.db.commit()
    _emit("AFTER-MUTATE", _snapshot())


def step_check():
    """migrate 之后再看一次：字段值是否被覆盖回 json 原值。"""
    now = _snapshot()
    with open(STATE, encoding="utf-8") as f:
        before = json.load(f)

    verdict = {}

    # Sidebar：期望仍是 "bug"；若变回 json 原值即被覆盖
    cur = now["workspace_sidebar"]["db_header_icon"]
    verdict["Workspace Sidebar"] = {
        "field": "header_icon",
        "json_original": now["workspace_sidebar"]["json_header_icon"],
        "value_set_by_probe": "bug",
        "value_after_migrate": cur,
        "overwritten": cur != "bug",
    }

    # Item：期望 label 仍带 -V15TEST
    curl = now["workspace_sidebar_item"]["db_label"]
    verdict["Workspace Sidebar Item"] = {
        "field": "label",
        "json_original": ITEM_LABEL,
        "value_set_by_probe": ITEM_LABEL + MARK,
        "value_after_migrate": curl,
        "row_name_before": before["workspace_sidebar_item"]["row_name"],
        "row_name_after": now["workspace_sidebar_item"]["row_name"],
        "overwritten": curl != (ITEM_LABEL + MARK),
    }

    # Desktop Icon：期望 icon 仍是 "bug"
    curi = now["desktop_icon"]["db_icon"]
    verdict["Desktop Icon"] = {
        "field": "icon",
        "json_original": now["desktop_icon"]["json_icon"],
        "value_set_by_probe": "bug",
        "value_after_migrate": curi,
        "overwritten": curi != "bug",
    }

    _emit("AFTER-MIGRATE", {"snapshot": now, "verdict": verdict})


def step_restore():
    """改回原值并确认。"""
    with open(STATE, encoding="utf-8") as f:
        before = json.load(f)

    sb = frappe.get_doc("Workspace Sidebar", SIDEBAR)
    sb.header_icon = before["workspace_sidebar"]["db_header_icon"]
    sb.save(ignore_permissions=True)

    parent = frappe.get_doc("Workspace Sidebar", ITEM_PARENT)
    for it in parent.items:
        if it.label == ITEM_LABEL + MARK:
            it.label = ITEM_LABEL
    parent.save(ignore_permissions=True)

    di = frappe.get_doc("Desktop Icon", ICON)
    di.icon = before["desktop_icon"]["db_icon"]
    di.save(ignore_permissions=True)

    frappe.db.commit()

    after = _snapshot()
    ok = {
        "sidebar_header_icon_restored": after["workspace_sidebar"]["db_header_icon"]
        == before["workspace_sidebar"]["db_header_icon"],
        "item_label_restored": after["workspace_sidebar_item"]["db_label"] == ITEM_LABEL,
        "desktop_icon_restored": after["desktop_icon"]["db_icon"] == before["desktop_icon"]["db_icon"],
        "no_V15TEST_left_in_sidebar_items": not any(
            MARK in (i.label or "") for i in frappe.get_doc("Workspace Sidebar", ITEM_PARENT).items
        ),
        "global_V15TEST_scan_items": frappe.db.sql(
            "select name, parent, label from `tabWorkspace Sidebar Item` where label like %s",
            ("%" + MARK + "%",),
            as_dict=True,
        ),
    }
    _emit("AFTER-RESTORE", {"snapshot": after, "restore_ok": ok})


def step_why():
    """顺手记：migrate 靠什么决定要不要重新导入某条 standard 记录。"""
    from frappe.modules.import_file import calculate_hash

    info = {}
    for folder, name, app in (
        ("workspace_sidebar", SIDEBAR, None),
        ("desktop_icon", ICON, None),
    ):
        p, j = _read_json(folder, name, app)
        dbm = frappe.db.get_value(j["doctype"], j["name"], "modified")
        info[f"{j['doctype']}::{j['name']}"] = {
            "json_path": p,
            "file_md5": calculate_hash(p),
            "json_modified": j.get("modified"),
            "db_modified": str(dbm),
            # import_file_by_path: 只有 doctype=="DocType" 才查 migration_hash；
            # 其余一律走 modified 时间戳比对
            "hash_used_for_this_doctype": j["doctype"] == "DocType",
            "db_ts_newer_or_equal": str(dbm) >= str(j.get("modified")),
        }
    info["_note"] = (
        "import_file_by_path(frappe/modules/import_file.py:128-142): stored_hash 仅在 "
        "doc['doctype']=='DocType' 时读取(:130)，故 Workspace Sidebar / Desktop Icon 不走 hash；"
        "判据落在 :141 is_db_timestamp_latest —— json.modified <= db.modified 则 continue(跳过导入)。"
        "任何 doc.save() 都会把 db.modified 刷成 now()，于是必然新于 json.modified，导入被跳过。"
        "推论：只要 json 里的 modified 不被上游改得更晚(升级换文件)，本地改动就一直留着。"
    )
    _emit("WHY", info)


# ---------------------------------------------------------------------------
# 覆盖判据的边界验证（同一命题的另一半：改动"能维持多久"）
#
# 上面验到的是 json.modified <= db.modified 时 migrate 跳过导入。反向条件——
# json.modified 比 db.modified 新（= 上游升级换了文件）——是否就会覆盖？
# 不实测就只是读码推断，故此处把 json 的 modified 调到未来再跑一次 migrate。
# 字段值仍留 json 原值（stock / Stock Entry），只动时间戳，这样一旦发生导入，
# DB 里的 bug / -V15TEST 会被打回 json 原值，一眼可辨。
# ---------------------------------------------------------------------------

FUTURE_TS = "2026-12-31 00:00:00.000000"

# (json 路径, 原 modified) —— 原值取自 step_snapshot 的实测输出
BUMP_TARGETS = {
    "/workspace/frappe-bench/apps/erpnext/erpnext/workspace_sidebar/stock.json": (
        "2026-02-20 16:45:15.295668"
    ),
    "/workspace/frappe-bench/apps/erpnext/erpnext/desktop_icon/stock.json": (
        "2026-01-01 20:07:01.212940"
    ),
}


def _swap_in_file(path, old, new):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    if old not in s:
        return False
    # 只替换 modified 那一处，保持文件其余字节不变
    s = s.replace(f'"modified": "{old}"', f'"modified": "{new}"', 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    return True


def step_bump_json():
    """把两个 json 的 modified 调到未来（模拟上游升级换文件）。"""
    res = {}
    for path, orig in BUMP_TARGETS.items():
        res[path] = {"bumped": _swap_in_file(path, orig, FUTURE_TS), "from": orig, "to": FUTURE_TS}
    _emit("BUMP", res)


def step_unbump_json():
    """把 json 的 modified 改回原值，并把 DB 的 modified 也复位到原值，
    使站点回到与备份一致的原始状态（update_modified 在导入时会把 db 刷成 json 值）。"""
    res = {}
    for path, orig in BUMP_TARGETS.items():
        res[path] = {"restored": _swap_in_file(path, FUTURE_TS, orig), "back_to": orig}

    # DB 侧 modified 复位：import_file.update_modified 用的就是这种直写，
    # 不触发 on_update，故不会再次导出 json。
    for dt, dn, orig in (
        ("Workspace Sidebar", SIDEBAR, BUMP_TARGETS[
            "/workspace/frappe-bench/apps/erpnext/erpnext/workspace_sidebar/stock.json"
        ]),
        ("Desktop Icon", ICON, BUMP_TARGETS[
            "/workspace/frappe-bench/apps/erpnext/erpnext/desktop_icon/stock.json"
        ]),
    ):
        frappe.db.set_value(dt, dn, "modified", orig, update_modified=False)
    frappe.db.commit()

    res["db_modified_reset"] = {
        "Workspace Sidebar": str(frappe.db.get_value("Workspace Sidebar", SIDEBAR, "modified")),
        "Desktop Icon": str(frappe.db.get_value("Desktop Icon", ICON, "modified")),
    }
    _emit("UNBUMP", res)


def step_check_bumped():
    """第二次 migrate 之后：字段值是否被打回 json 原值。"""
    now = _snapshot()
    _emit(
        "AFTER-BUMPED-MIGRATE",
        {
            "snapshot": now,
            "verdict": {
                "Workspace Sidebar": {
                    "value_before_this_migrate": "bug",
                    "value_now": now["workspace_sidebar"]["db_header_icon"],
                    "overwritten_to_json_original": now["workspace_sidebar"]["db_header_icon"]
                    == now["workspace_sidebar"]["json_header_icon"],
                },
                "Workspace Sidebar Item": {
                    "value_before_this_migrate": ITEM_LABEL + MARK,
                    "value_now": now["workspace_sidebar_item"]["db_label"],
                    "overwritten_to_json_original": now["workspace_sidebar_item"]["db_label"]
                    == ITEM_LABEL,
                },
                "Desktop Icon": {
                    "value_before_this_migrate": "bug",
                    "value_now": now["desktop_icon"]["db_icon"],
                    "overwritten_to_json_original": now["desktop_icon"]["db_icon"]
                    == now["desktop_icon"]["json_icon"],
                },
            },
        },
    )


if __name__ == "__main__":
    import sys
    # 必须以 /workspace/frappe-bench/sites 为 cwd 跑：frappe 的 logger 用相对路径
    # os.path.join("..","logs",...)（utils/logger.py:24），cwd 不对会 FileNotFoundError。
    os.chdir("/workspace/frappe-bench/sites")
    frappe.init(site="erx.localhost", sites_path=".")
    frappe.connect()
    try:
        globals()[sys.argv[1]]()
    finally:
        frappe.destroy()
