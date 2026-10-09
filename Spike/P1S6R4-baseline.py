import argparse
import ast
import csv
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "frappe-bench"
APPS = ("frappe", "erpnext", "crm", "hrms", "insights", "raven", "frappe_china")
NAMED_SOURCES = {
    "Dr", "Setup", "Settings", "Payment References", "Payment Entry Reference",
    "Cash Flow Worksheet", "Cash Flow", "Create Chart Of Accounts Based On",
    "Disable Opening Balance Calculation", "Closed Date", "Unpaid", "Paid",
    "Is Paid", "Paid Amount", "Received Amount", "Payment Amount", "Payment Type",
    "Type of Payment", "Mode of Payment", "Outstanding Amount", "Outward", "Inward",
    "Item", "Accounts Setup", "HR Setup", "Is Sales Item", "Create Quotation",
    "View Customer", "Add Row", "Qualification", "Agents", "Bot",
    "Accounts Receivable", "Debtors", "Receivable", "Opening & Closing",
}
CALL_LITERAL = re.compile(r"""(?<![\w])_{1,2}\(\s*((?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'))""")
COMPONENT_IMPORT = re.compile(r"""(?:from\s+|import\s*)["']([^"']*components/[^"']+)["']""")


def parse_po(path):
    if not path.exists():
        return []
    entries = []
    current = {"id": "", "context": None, "str": "", "refs": []}
    field = None
    for line in [*path.read_text(encoding="utf-8-sig").splitlines(), ""]:
        if not line.strip():
            if current["id"]:
                entries.append(current)
            current = {"id": "", "context": None, "str": "", "refs": []}
            field = None
        elif line.startswith("#:"):
            current["refs"].extend(line[2:].strip().split())
        elif line.startswith("msgctxt "):
            field = "context"
            current[field] = ast.literal_eval(line[8:])
        elif line.startswith("msgid "):
            field = "id"
            current[field] = ast.literal_eval(line[6:])
        elif line.startswith("msgstr "):
            field = "str"
            current[field] = ast.literal_eval(line[7:])
        elif line.startswith("msgstr["):
            raise ValueError(f"Plural entry unsupported: {path}: {line}")
        elif line.startswith('"') and field:
            current[field] += ast.literal_eval(line)
    return entries


def entry_key(entry):
    return entry["id"] + (":" + entry["context"] if entry["context"] else "")


def parse_csv(path):
    if not path.exists():
        return {}
    values = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for line_number, row in enumerate(csv.reader(handle), 1):
            if len(row) not in (2, 3):
                raise ValueError(f"{path}:{line_number}: expected 2 or 3 columns: {row}")
            source, target = (value.replace("\\n", "\n") for value in row[:2])
            key = source + (":" + row[2] if len(row) == 3 and row[2] else "")
            if key in values:
                raise ValueError(f"{path}:{line_number}: duplicate key: {key}")
            values[key] = target.strip()
    return values


def app_path(app):
    return ROOT / "apps" / app / app


def merged_dict():
    merged = {}
    plain_keys = set()
    for app in APPS:
        app_csv = parse_csv(app_path(app) / "translations/zh.csv")
        merged.update(app_csv)
        csv_path = app_path(app) / "translations/zh.csv"
        if csv_path.exists():
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                plain_keys.update(row[0].replace("\\n", "\n") for row in csv.reader(handle)
                                  if len(row) == 2 or len(row) == 3 and not row[2])
        for entry in parse_po(app_path(app) / "locale/zh.po"):
            if entry["str"]:
                merged[entry_key(entry)] = entry["str"]
                if not entry["context"]:
                    plain_keys.add(entry["id"])
    return merged, plain_keys


def gaps(merged):
    result = {}
    identity_counts = {}
    for app in APPS[:-1]:
        missing = []
        identity = 0
        for entry in parse_po(app_path(app) / "locale/main.pot"):
            key = entry_key(entry)
            value = merged.get(key) or merged.get(entry["id"])
            if not value or value == entry["id"]:
                missing.append([key, entry["refs"]])
                identity += bool(value and value == entry["id"])
        result[app] = missing
        identity_counts[app] = identity
    return result, identity_counts


def collisions(merged, plain_keys):
    groups = defaultdict(set)
    for key in plain_keys:
        if key in merged:
            groups[merged[key].strip()].add(key)
    return {value: sorted(keys) for value, keys in sorted(groups.items()) if len(keys) >= 2}


def doctypes():
    index = {}
    for app in APPS:
        for path in sorted(app_path(app).glob("**/doctype/*/*.json")):
            if path.stem != path.parent.name:
                continue
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if data.get("doctype") == "DocType":
                index[data["name"]] = (path, data)
    return index


def original_scope():
    script = PROJECT / "Spike/P1S3R1-po-demoline-direct.py"
    for statement in ast.parse(script.read_text(encoding="utf-8-sig")).body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "DEMO_DOCTYPES" for target in statement.targets
        ):
            return set(ast.literal_eval(statement.value))
    raise ValueError(f"DEMO_DOCTYPES missing: {script}")


def harvest_literals(path, surface):
    source = path.read_text(encoding="utf-8-sig")
    for match in CALL_LITERAL.finditer(source):
        value = ast.literal_eval(match.group(1))
        surface[value].add(f"{path.relative_to(PROJECT).as_posix()}:{source.count(chr(10), 0, match.start()) + 1}")


def harvest_labels(data, reference, surface):
    if isinstance(data, dict):
        if data.get("label"):
            surface[data["label"]].add(reference)
        for value in data.values():
            harvest_labels(value, reference, surface)
    elif isinstance(data, list):
        for value in data:
            harvest_labels(value, reference, surface)


def demo_surface(index, merged):
    base = original_scope()
    worksheet = "Cash Flow Worksheet" if "Cash Flow Worksheet" in index else "Cash Flow"
    scope = base | {"Routing", "Employee", "Month End Closing Voucher", worksheet, "Bank Statement Preprocess"}
    queue = list(scope)
    while queue:
        name = queue.pop()
        if name not in index:
            raise ValueError(f"Demo DocType not found: {name}")
        for field in index[name][1].get("fields", []):
            child = field.get("options")
            if field.get("fieldtype") in ("Table", "Table MultiSelect") and child and child not in scope:
                scope.add(child)
                queue.append(child)
    surface = defaultdict(set)
    for name in sorted(scope):
        path, data = index[name]
        reference = path.relative_to(PROJECT).as_posix()
        surface[name].add(reference)
        for field in data.get("fields", []):
            if field.get("label"):
                surface[field["label"]].add(f"{reference}:{field['fieldname']}")
            if field.get("fieldtype") == "Select":
                for option in (field.get("options") or "").splitlines():
                    if option.strip():
                        surface[option.strip()].add(f"{reference}:{field['fieldname']}")
        for script in (path.with_suffix(".js"), path.with_name(path.stem + "_list.js")):
            if script.exists():
                harvest_literals(script, surface)
    frontend = ROOT / "apps/crm/frontend/src"
    for page in ("Lead", "Leads", "Deal", "Deals", "Dashboard"):
        path = frontend / f"pages/{page}.vue"
        if not path.exists():
            raise ValueError(f"Demo frontend page missing: {path}")
        harvest_literals(path, surface)
        for imported in COMPONENT_IMPORT.findall(path.read_text(encoding="utf-8-sig")):
            component = frontend / imported[2:] if imported.startswith("@/") else path.parent / imported
            component = component.resolve()
            if not component.exists():
                candidates = [component.with_suffix(suffix) for suffix in (".vue", ".ts", ".tsx", ".js", ".jsx")]
                candidates.append(component / "index.vue")
                candidates.append(component / "index.ts")
                component = next((candidate for candidate in candidates if candidate.exists()), component)
            if not component.exists():
                raise ValueError(f"Imported component missing: {component}")
            harvest_literals(component, surface)
    raven = ROOT / "apps/raven/apps/web/src/components/features"
    for directory in (raven / "cmdk", raven / "settings/panels/ai"):
        if not directory.exists():
            raise ValueError(f"Demo frontend directory missing: {directory}")
        for path in sorted(directory.rglob("*")):
            if path.suffix in (".tsx", ".ts", ".js", ".jsx", ".vue"):
                harvest_literals(path, surface)
    navigation = set(app_path("erpnext").glob("workspace_sidebar/*.json"))
    navigation.update(app_path("frappe_china").glob("workspace_sidebar/*.json"))
    for app in APPS:
        navigation.update(app_path(app).glob("**/desktop_icon/*.json"))
    for path in sorted(navigation):
        harvest_labels(json.loads(path.read_text(encoding="utf-8-sig")), path.relative_to(PROJECT).as_posix(), surface)
    for source in NAMED_SOURCES | {key for key in merged if re.search(r"time\s*sheet", key, re.IGNORECASE)}:
        surface[source].add("需求 §4.2.4")
    operation = PROJECT / "docs/01-需求摸底/S01-场景摸底/0-P1-S1文档/最小闭环操作稿.md"
    mentioned = set(re.findall(r"`([^`\n]+)`", operation.read_text(encoding="utf-8-sig"))) & set(index)
    return surface, scope, sorted(mentioned - scope), sorted(mentioned - base)


def official_overrides():
    official = {}
    for app in APPS[:-1]:
        for entry in parse_po(app_path(app) / "locale/zh.po"):
            if entry["str"]:
                official[entry_key(entry)] = {"official": entry["str"], "app": app}
    ours = parse_csv(app_path("frappe_china") / "translations/zh.csv")
    return [{"key": key, **official[key], "ours": ours[key]} for key in sorted(ours.keys() & official.keys())]


def commits():
    result = {}
    locked = {app["app_name"]: app["commit"] for app in json.loads((PROJECT / "docker/apps.json").read_text(encoding="utf-8-sig"))}
    for app in APPS:
        completed = subprocess.run(["git", "-C", str(ROOT / "apps" / app), "rev-parse", "HEAD"],
                                   check=True, capture_output=True, text=True)
        result[app] = completed.stdout.strip()
        if result[app] != locked[app]:
            raise ValueError(f"Unlocked commit for {app}: {result[app]} != {locked[app]}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).with_name("P1S6R4-baseline.out.json")))
    args = parser.parse_args()
    heads = commits()
    merged, plain_keys = merged_dict()
    missing, identity_counts = gaps(merged)
    collision_groups = collisions(merged, plain_keys)
    surface, scope, missing_doctypes, original_missing = demo_surface(doctypes(), merged)
    demo_groups = {target: {"sources": sources, "visible": {
        source: sorted(surface[source]) for source in sources if source in surface}}
        for target, sources in collision_groups.items()
        if sum(source in surface for source in sources) >= 2}
    output = {
        "commits": heads,
        "gaps": missing,
        "gap_counts": {app: len(items) for app, items in missing.items()},
        "identity_gap_counts": identity_counts,
        "collision_count": len(collision_groups),
        "collisions": collision_groups,
        "demo_collisions": demo_groups,
        "demo_surface_count": len(surface),
        "demo_surface": {source: sorted(refs) for source, refs in sorted(surface.items())},
        "demo_doctypes": sorted(scope),
        "official_overrides": official_overrides(),
        "lg009_missing_doctypes": missing_doctypes,
        "lg009_original_scope_missing": original_missing,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("commits", "gap_counts", "identity_gap_counts",
        "collision_count", "demo_surface_count", "lg009_missing_doctypes", "lg009_original_scope_missing")},
        ensure_ascii=False, indent=2))
    print(f"demo collision groups: {len(demo_groups)}; official overrides: {len(output['official_overrides'])}")


if __name__ == "__main__":
    main()
