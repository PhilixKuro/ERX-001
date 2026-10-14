select 'stc', count(*) from `tabSales Taxes and Charges Template`;
select 'ptc', count(*) from `tabPurchase Taxes and Charges Template`;
select 'ect', count(*) from `tabExpense Claim Type`;
select 'sched', value from tabSingles where doctype='System Settings' and field='enable_scheduler';
select 'bot', name from `tabRaven Bot`;
