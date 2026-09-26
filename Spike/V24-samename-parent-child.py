#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
V-24 probe: find same-name parent/child pairs in zelin chart-of-accounts JSON.

Proposition under test: in zelin 小企业会计准则(2024) chart, exactly 2 pairs are
same-name parent/child (a parent account whose account_name equals one of its own
direct children's account_name).

Read-only. Parses the nested tree recursively. Does NOT touch the site.
'''

import json
import os
import sys

COA_DIR = os.path.join(
    'D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china',
    'erpnext_china', 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts',
)

TARGET = 'cn_smes_chart_of_accounts2024.json'
ALL_CHARTS = [
    'cn_smes_chart_of_accounts2024.json',
    'cn_norm_chart_of_accounts2024.json',
    'cn_cnpo_chart_of_accounts2025.json',
    'cn_sme_coa.json',
]


def children_of(node):
    '''Children are exactly the dict-valued keys; metadata values are scalars.'''
    return [(k, v) for k, v in node.items() if isinstance(v, dict)]


def meta(node, key):
    v = node.get(key, None)
    if isinstance(v, dict):
        return None
    return v


def walk(name, node, path, inherited_root, stats, hits, meta_keys):
    '''Depth-first walk. path is the list of ancestor names, root first.'''
    stats['count'] += 1
    root_type = meta(node, 'root_type') or inherited_root
    if meta(node, 'is_group') in (1, '1', True):
        stats['groups'] += 1
    else:
        stats['leaves'] += 1

    for k, v in node.items():
        if not isinstance(v, dict):
            meta_keys.add(k)

    kids = children_of(node)
    for cname, cnode in kids:
        if cname == name:
            hits.append({
                'depth': len(path),
                'ancestry': ' > '.join(path + [name, cname]),
                'parent': {
                    'account_name': name,
                    'account_number': meta(node, 'account_number'),
                    'is_group': meta(node, 'is_group'),
                    'account_type': meta(node, 'account_type'),
                    'root_type': root_type,
                },
                'child': {
                    'account_name': cname,
                    'account_number': meta(cnode, 'account_number'),
                    'is_group': meta(cnode, 'is_group'),
                    'account_type': meta(cnode, 'account_type'),
                    'root_type': meta(cnode, 'root_type') or root_type,
                },
                'parent_child_count': len(kids),
                'sibling_names': [n for n, _ in kids],
                'child_has_own_children': len(children_of(cnode)),
            })
        walk(cname, cnode, path + [name], root_type, stats, hits, meta_keys)


def scan(fname):
    fpath = os.path.join(COA_DIR, fname)
    with open(fpath, encoding='utf-8') as fh:
        data = json.load(fh)
    stats = {'count': 0, 'groups': 0, 'leaves': 0}
    hits = []
    meta_keys = set()
    for rname, rnode in data['tree'].items():
        walk(rname, rnode, [], meta(rnode, 'root_type'), stats, hits, meta_keys)
    return {
        'file': fname,
        'path': fpath,
        'chart_name': data.get('name'),
        'country_code': data.get('country_code'),
        'stats': stats,
        'hits': hits,
        'meta_keys': sorted(meta_keys),
        'root_names': list(data['tree'].keys()),
    }


def show(res, full):
    print('=' * 72)
    print('file        : ' + res['file'])
    print('chart name  : ' + str(res['chart_name']))
    print('total nodes : {0}  (groups {1} / leaves {2})'.format(
        res['stats']['count'], res['stats']['groups'], res['stats']['leaves']))
    print('roots       : ' + ', '.join(res['root_names']))
    print('meta keys   : ' + ', '.join(res['meta_keys']))
    print('same-name parent/child pairs : {0}'.format(len(res['hits'])))
    for i, h in enumerate(res['hits'], 1):
        p, c = h['parent'], h['child']
        print('  [{0}] {1}'.format(i, h['ancestry']))
        if not full:
            continue
        print('      parent: number={0!r} is_group={1!r} root_type={2!r} account_type={3!r}'.format(
            p['account_number'], p['is_group'], p['root_type'], p['account_type']))
        print('      child : number={0!r} is_group={1!r} root_type={2!r} account_type={3!r}'.format(
            c['account_number'], c['is_group'], c['root_type'], c['account_type']))
        print('      parent direct children ({0}): {1}'.format(
            h['parent_child_count'], ', '.join(h['sibling_names'])))
        print('      child own children: {0}'.format(h['child_has_own_children']))


def main():
    target = scan(TARGET)
    show(target, full=True)
    print()
    print('--- cross-check: other three charts (count only) ---')
    for f in ALL_CHARTS:
        if f == TARGET:
            continue
        show(scan(f), full=False)
    print()
    print('VERDICT INPUT: 小企业会计准则(2024) same-name parent/child pair count = {0}'.format(
        len(target['hits'])))

    out = os.path.join('D:', os.sep, 'ERX-001', 'Spike', 'V24-out')
    if not os.path.isdir(out):
        os.makedirs(out)
    with open(os.path.join(out, 'V24-hits.json'), 'w', encoding='utf-8') as fh:
        json.dump({f: scan(f) for f in ALL_CHARTS}, fh,
                  ensure_ascii=False, indent=2)
    print('raw dump: ' + os.path.join(out, 'V24-hits.json'))


if __name__ == '__main__':
    sys.exit(main())
