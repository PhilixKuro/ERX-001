-- P1-S6-R13 F 片 1：只读。库里有没有写死「报销管理」的记录（FD-008 收回后不随 csv 回落的部分）。
SELECT 'account' AS kind, name FROM tabAccount WHERE account_name LIKE '%报销管理%'
UNION ALL SELECT 'desktop_icon', name FROM `tabDesktop Icon` WHERE label LIKE '%报销管理%'
UNION ALL SELECT 'sidebar', name FROM `tabWorkspace Sidebar` WHERE title LIKE '%报销管理%'
UNION ALL SELECT 'translation_rows', COUNT(*) FROM tabTranslation;
