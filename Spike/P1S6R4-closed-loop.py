"""Disposable HDTH acceptance data. Restore backup A after acceptance."""
import json,os,sys
from pathlib import Path
import frappe
from frappe.utils import nowdate, add_days
STATE=Path('/workspace/Spike/P1S6R4-closed-loop.json')
COMPANY='华东弹簧有限公司'
PREFIX='_S6 验收'

def run(action):
 state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'company':COMPANY,'docs':[]}
 assert state['company']==COMPANY
 company=frappe.get_doc('Company',COMPANY)
 def account(number):return frappe.db.get_value('Account',{'company':COMPANY,'account_number':number,'is_group':0})
 def save(key,values):
  if key in state and frappe.db.exists(values['doctype'],state[key]):return frappe.get_doc(values['doctype'],state[key])
  doc=frappe.get_doc(values).insert();state[key]=doc.name;state['docs'].append([doc.doctype,doc.name]);return doc
 def persist():
  frappe.db.commit();STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
 def submit(key):
  dt=next(dt for dt,name in state['docs'] if name==state[key]);doc=frappe.get_doc(dt,state[key])
  if doc.docstatus==0:doc.submit()
  return doc
 def mapped(key,doc):
  if key in state:return frappe.get_doc(doc.doctype,state[key])
  doc.company=COMPANY;doc.insert();state[key]=doc.name;state['docs'].append([doc.doctype,doc.name]);return doc
 if action=='masters':
  assert frappe.db.count('Account',{'company':COMPANY})==266
  for key,label in [('raw_wh','原料'),('wip_wh','在制'),('fg_wh','成品'),('scrap_wh','废料')]:save(key,{'doctype':'Warehouse','warehouse_name':PREFIX+label,'company':COMPANY})
  company.default_wip_warehouse=state['wip_wh'];company.default_fg_warehouse=state['fg_wh'];company.default_scrap_warehouse=state['scrap_wh'];company.save()
  save('supplier',{'doctype':'Supplier','supplier_name':PREFIX+'供应商','supplier_type':'Company','supplier_group':'Raw Material'})
  save('customer',{'doctype':'Customer','customer_name':PREFIX+'客户','customer_type':'Company','customer_group':'Commercial','territory':'China'})
  if not frappe.db.exists('Gender','Male'): frappe.get_doc({'doctype':'Gender','gender':'Male'}).insert()
  save('employee',{'doctype':'Employee','first_name':PREFIX+'员工','gender':'Male','date_of_birth':'1990-01-01','date_of_joining':'2025-01-01','company':COMPANY,'status':'Active'})
  for key,label in [('raw','弹簧钢丝'),('fg','成品弹簧')]:
   save(key,{'doctype':'Item','item_code':PREFIX+label,'item_name':PREFIX+label,'item_group':'Raw Material' if key=='raw' else 'Products','stock_uom':'Nos','is_stock_item':1,'valuation_rate':10,'item_defaults':[{'company':COMPANY,'default_warehouse':state['raw_wh' if key=='raw' else 'fg_wh'],'expense_account':company.default_expense_account,'income_account':company.default_income_account}],'uoms':[{'uom':'Nos','conversion_factor':1},{'uom':'Box','conversion_factor':10}]})
  save('price',{'doctype':'Item Price','item_code':state['fg'],'price_list':'Standard Selling','price_list_rate':50,'currency':'CNY'})
  save('workstation',{'doctype':'Workstation','workstation_name':PREFIX+'工站','production_capacity':1,'working_hours':[{'start_time':'00:00:00','end_time':'23:59:59'}]})
  for i,label in enumerate(['卷簧','热处理','检验'],1):save('op'+str(i),{'doctype':'Operation','name':PREFIX+label,'operation':PREFIX+label})
  operations=[{'operation':state['op'+str(i)],'workstation':state['workstation'],'time_in_mins':1,'hour_rate':60,'sequence_id':i}for i in range(1,4)]
  save('routing',{'doctype':'Routing','routing_name':PREFIX+'路线','operations':operations})
  save('bom',{'doctype':'BOM','item':state['fg'],'company':COMPANY,'quantity':1,'with_operations':1,'routing':state['routing'],'operations':operations,'items':[{'item_code':state['raw'],'qty':1,'uom':'Nos','rate':10,'source_warehouse':state['raw_wh']}]})
  save('purchase_order',{'doctype':'Purchase Order','company':COMPANY,'supplier':state['supplier'],'transaction_date':nowdate(),'schedule_date':add_days(nowdate(),1),'currency':'CNY','buying_price_list':'Standard Buying','set_warehouse':state['raw_wh'],'items':[{'item_code':state['raw'],'qty':10,'rate':10,'schedule_date':add_days(nowdate(),1),'warehouse':state['raw_wh']}]})
  save('opening',{'doctype':'Journal Entry','company':COMPANY,'posting_date':nowdate(),'is_opening':'Yes','accounts':[{'account':account('1002'),'debit_in_account_currency':10000,'cost_center':company.cost_center},{'account':account('3001'),'credit_in_account_currency':10000,'cost_center':company.cost_center}]})
  save('quotation',{'doctype':'Quotation','company':COMPANY,'quotation_to':'Customer','party_name':state['customer'],'currency':'CNY','selling_price_list':'Standard Selling','items':[{'item_code':state['fg'],'qty':1,'rate':50,'warehouse':state['fg_wh']}]})
 elif action=='receipt':
  from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
  submit('opening');submit('purchase_order');mapped('purchase_receipt',make_purchase_receipt(state['purchase_order']))
 elif action=='purchase-invoice':
  from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
  submit('purchase_receipt');mapped('purchase_invoice',make_purchase_invoice(state['purchase_receipt']))
 elif action=='purchase-payment':
  from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
  submit('purchase_invoice');doc=get_payment_entry('Purchase Invoice',state['purchase_invoice'],bank_account=company.default_bank_account);doc.reference_no=PREFIX+'采购付款';doc.reference_date=nowdate();mapped('purchase_payment',doc)
 elif action=='sales-order':
  from erpnext.selling.doctype.quotation.quotation import make_sales_order
  submit('bom');submit('purchase_payment');submit('quotation');doc=make_sales_order(state['quotation']);doc.delivery_date=add_days(nowdate(),1)
  for row in doc.items:row.delivery_date=doc.delivery_date;row.warehouse=state['fg_wh']
  mapped('sales_order',doc)
 elif action=='production-plan':
  submit('sales_order')
  plan=frappe.get_doc({'doctype':'Production Plan','company':COMPANY,'get_items_from':'Sales Order','sales_orders':[{'sales_order':state['sales_order'],'sales_order_date':nowdate(),'customer':state['customer'],'grand_total':50}],'for_warehouse':state['fg_wh']})
  plan.get_items();mapped('production_plan',plan)
 elif action=='work-order':
  submit('production_plan');frappe.db.set_single_value('Manufacturing Settings','disable_capacity_planning',1)
  doc=frappe.get_doc({'doctype':'Work Order','company':COMPANY,'production_item':state['fg'],'bom_no':state['bom'],'qty':1,'source_warehouse':state['raw_wh'],'wip_warehouse':state['wip_wh'],'fg_warehouse':state['fg_wh'],'planned_start_date':frappe.utils.now_datetime(),'sales_order':state['sales_order']})
  doc.get_items_and_operations_from_bom();mapped('work_order',doc)
 elif action=='transfer':
  from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
  submit('work_order');doc=frappe.get_doc(make_stock_entry(state['work_order'],'Material Transfer for Manufacture',1));mapped('transfer',doc)
  state['job_cards']=frappe.get_all('Job Card',filters={'work_order':state['work_order']},pluck='name',order_by='sequence_id asc')
 elif action=='manufacture':
  from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
  submit('transfer')
  state['job_cards']=frappe.get_all('Job Card',filters={'work_order':state['work_order']},pluck='name',order_by='sequence_id asc')
  for idx,name in enumerate(state['job_cards']):
   card=frappe.get_doc('Job Card',name)
   if card.docstatus==0:
    start=frappe.utils.add_to_date(frappe.utils.now_datetime(),minutes=idx*2);end=frappe.utils.add_to_date(start,minutes=1)
    card.append('time_logs',{'employee':state['employee'],'from_time':str(start),'to_time':str(end),'completed_qty':1});card.save();card.submit()
  manufacture = frappe.get_doc(make_stock_entry(state['work_order'],'Manufacture',1))
  # ERPNext's manufacture helper leaves the operating-cost row's expense
  # account blank for a custom company.  Fill it from the company's configured
  # default before the native GL validation runs.
  for charge in manufacture.additional_costs:
   if not charge.expense_account:
    charge.expense_account = company.default_expense_account
   if not charge.cost_center:
    charge.cost_center = company.cost_center
  mapped('manufacture',manufacture)
 elif action=='delivery':
  from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
  submit('manufacture');mapped('delivery_note',make_delivery_note(state['sales_order']))
 elif action=='sales-invoice':
  from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
  submit('delivery_note');mapped('sales_invoice',make_sales_invoice(state['delivery_note']))
 elif action=='sales-payment':
  from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
  submit('sales_invoice');doc=get_payment_entry('Sales Invoice',state['sales_invoice'],bank_account=company.default_bank_account);doc.reference_no=PREFIX+'销售收款';doc.reference_date=nowdate();mapped('sales_payment',doc)
 elif action=='finish':submit('sales_payment')
 else:raise ValueError(action)
 persist();print(frappe.as_json(state))

if __name__=='__main__':
 os.chdir('/workspace/frappe-bench/sites');frappe.init(site='erx.localhost',sites_path='.');frappe.connect();frappe.set_user('Administrator');frappe.local.lang='zh'
 try:run(sys.argv[1])
 finally:frappe.db.rollback();frappe.destroy()
