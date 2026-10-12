# Upstream bug report draft (P1-S6-R9 TS-030 / IT-035)

> **DRAFT — not submitted.** Filing this on GitHub is an outbound action and needs the user's explicit permission first (R9 plan A25).
> Target: `frappe/frappe`, branch `version-16`. Locked commit in this project: `c1f1e8ec3708750d7254f7f99d869ffb9886f19f`.

## Title

Form timeline shows `null` / `undefined` for fields changed from or to an empty value

## Description

When a field changes from an empty value to a value (or the other way round), the form timeline renders the empty side as the literal word **null** (sometimes **undefined**), for example:

> Actual Start Date from **null** to **12-10-2026 09:00**

Expected: the empty side is shown as empty (`""`, which the same function already uses as its fallback for empty strings) instead of the JavaScript literal.

## Steps to reproduce

1. Open a submitted-able document whose field starts out empty, e.g. a new **Work Order** with *Actual Start Date* empty.
2. Save, then set *Actual Start Date* (or let a Job Card set it) and save again.
3. Look at the timeline under the form.

Observed on Work Order, Job Card, Stock Entry (Manufacture) and Sales Order (status change) with the Chinese UI; the code path below does not depend on the language (not re-checked in an English session).

## Root cause

`frappe/public/js/frappe/form/footer/version_timeline_content_builder.js:411-418`

```javascript
function format_content_for_timeline(content) {
	content = frappe.utils.html2text(content);
	content = frappe.ellipsis(content, 40) || '""';
	content = frappe.utils.escape_html(content);
	return content.bold();
}
```

The Version `changed` entries store the old/new values as JSON, so an empty side arrives here as JS `null` (or `undefined`). `frappe.utils.html2text` (`frappe/public/js/frappe/utils/utils.js:269-273`) passes it to `DOMParser.parseFromString`, which coerces it to the string `"null"`; the `|| '""'` fallback never triggers because `"null"` is truthy.

## Suggested fix

Either of:

1. In `format_content_for_timeline`, treat nullish input as empty before converting:
   ```javascript
   content = frappe.utils.html2text(content ?? "");
   ```
2. Or make `frappe.utils.html2text` return `""` for `null` / `undefined`.

Option 1 is the narrower change.

## Workaround in this project

`frappe_china/public/js/desk_patches.js` rewrites bold texts that are exactly `null` / `undefined` inside `.new-timeline .timeline-content` (MutationObserver), Chinese sessions only. Remove it once upstream is fixed.
