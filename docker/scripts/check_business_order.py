#!/usr/bin/env python3
"""Check that docker/apps.json and frappe_china's business app order agree."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def _business_order(install_path: Path) -> list[str]:
    module = ast.parse(install_path.read_text(encoding="utf-8-sig"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == "BUSINESS_APP_ORDER"
            for target in targets
        ):
            parsed = ast.literal_eval(value)
            if isinstance(parsed, (tuple, list)) and all(
                isinstance(item, str) for item in parsed
            ):
                return list(parsed)
            break
    raise ValueError("BUSINESS_APP_ORDER was not found as a string tuple/list")


def _apps_order(apps_path: Path) -> list[str]:
    data = json.loads(apps_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("apps.json must contain a list")
    return [
        entry["app_name"]
        for entry in data
        if isinstance(entry, dict) and "app_name" in entry
    ]


def main(apps_json: str, install_py: str) -> int:
    apps_path = Path(apps_json)
    install_path = Path(install_py)
    try:
        declared = _business_order(install_path)
        available = _apps_order(apps_path)
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"business app order check failed: {error}")
        return 1

    actual = [app for app in available if app in declared]
    if actual != declared:
        print(f"apps.json business order: {actual}")
        print(f"install.py BUSINESS_APP_ORDER: {declared}")
        return 1
    print(f"business app order ok: {actual}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apps_json")
    parser.add_argument("install_py")
    args = parser.parse_args()
    raise SystemExit(main(args.apps_json, args.install_py))
