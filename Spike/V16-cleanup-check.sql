-- V-16 cleanup verification: any database row still referencing the throwaway
-- test app erx_spike after `bench uninstall-app`?
--   docker exec -i -w /workspace/frappe-bench erx001-frappe-1 \
--     bench --site erx.localhost mariadb < /workspace/Spike/V16-cleanup-check.sql
SELECT 'Module Def' AS source, name AS value FROM `tabModule Def` WHERE app_name = 'erx_spike'
UNION ALL
SELECT 'Desktop Icon', name FROM `tabDesktop Icon` WHERE label LIKE '%Erx Spike%'
UNION ALL
SELECT 'Workspace Sidebar', name FROM `tabWorkspace Sidebar` WHERE name LIKE '%Erx%'
UNION ALL
SELECT 'Workspace Sidebar Item', name FROM `tabWorkspace Sidebar Item` WHERE parent LIKE '%Erx%'
UNION ALL
SELECT 'DocType', name FROM `tabDocType` WHERE module LIKE '%Erx Spike%'
UNION ALL
SELECT 'installed_apps single', LEFT(value, 200) FROM `tabSingles` WHERE field = 'installed_apps' AND value LIKE '%erx_spike%'
UNION ALL
SELECT 'DefaultValue', CONCAT(defkey, '=', LEFT(defvalue, 100)) FROM `tabDefaultValue` WHERE defvalue LIKE '%erx_spike%';
