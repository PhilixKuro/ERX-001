select 'icon_max_mod_nonown', max(modified), count(*) from `tabDesktop Icon` where ifnull(app,'')<>'frappe_china';
select 'icon_mod_after_s5', count(*) from `tabDesktop Icon` where ifnull(app,'')<>'frappe_china' and modified>'2026-10-08 21:18:05';
select 'sb_mod_after_s5', count(*) from `tabWorkspace Sidebar` where ifnull(app,'')<>'frappe_china' and modified>'2026-10-08 21:18:05';
select 'sbi_mod_after_s5', count(*) from `tabWorkspace Sidebar Item` where parent not in (select name from `tabWorkspace Sidebar` where app='frappe_china') and modified>'2026-10-08 21:18:05';
select 'ar_accounts', account_name, is_group, account_type from tabAccount where account_name like '%应收账款%';
select 'salutation', count(*) from tabSalutation;
