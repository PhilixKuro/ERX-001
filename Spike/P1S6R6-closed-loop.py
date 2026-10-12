"""S6 R6 TS-022／023 造数（由 P1S6R4-closed-loop.py 参数化而来；旧文件不改）。
用法：env/bin/python /workspace/Spike/P1S6R6-closed-loop.py <site> <action>
站点、公司、前缀、状态文件按站点取（SITES）；状态文件即逐屏核的 values.json。用完恢复备份（演示站）或留在测试站。"""
import json,os,sys
from pathlib import Path
import frappe
from frappe.utils import nowdate, add_days
SITES={'erx.localhost':('华东弹簧有限公司','_S6R6 验收'),'test.localhost':('_S6R6 测试公司','_S6R6 验收')}
SITE=sys.argv[1]
COMPANY,PREFIX=SITES[SITE]
STATE=Path(f'/workspace/Spike/P1S6R6-closed-loop-{SITE.split(".")[0]}.json')

def run(action):
 state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'company':COMPANY,'docs':[]}
 assert state['company']==COMPANY
 company=frappe.get_doc('Company',COMPANY) if frappe.db.exists('Company',COMPANY) else None
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
 if action=='company':
  if not frappe.db.exists('Company',COMPANY):
   from frappe_china.tests.utils import make_cn_company
   make_cn_company(COMPANY,'S6R')
  state['docs']=state.get('docs',[])
 elif action=='masters':
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
  for i,name in enumerate(state['job_cards'],1):state[f'job_card_{i}']=name
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

 elif action=='closing':
  # 结转凭证（已提交，供取消确认框）与现金流量底稿（已提交 11 月、草稿 12 月）；须在 drafts 之前跑，免得草稿挡住结转
  from frappe_china.accounting.closing import generate_month_end_closing
  fy=frappe.db.get_value('Fiscal Year',{'year_start_date':['<=',nowdate()],'year_end_date':['>=',nowdate()]},'name')
  month=int(nowdate()[5:7])
  if 'mecv' not in state:
   names=generate_month_end_closing(COMPANY,fy,month,ignore_drafts=1)
   names=names if isinstance(names,list) else frappe.get_all('Month End Closing Voucher',filters={'company':COMPANY,'month':month,'docstatus':1},pluck='name')
   state['mecv']=names[0];state['docs'].extend(['Month End Closing Voucher',n] for n in names)
  if 'cfw' not in state:
   for m in range(1,month):
    if frappe.db.exists('Cash Flow Worksheet',{'company':COMPANY,'fiscal_year':fy,'month':m,'docstatus':1}):continue
    doc=frappe.get_doc({'doctype':'Cash Flow Worksheet','company':COMPANY,'fiscal_year':fy,'month':m})
    doc.get_cash_flow_items();doc.insert();doc.submit();state['docs'].append(['Cash Flow Worksheet',doc.name])
   state['cfw']=doc.name
  if 'cfw_draft' not in state:
   doc=frappe.get_doc({'doctype':'Cash Flow Worksheet','company':COMPANY,'fiscal_year':fy,'month':month});doc.get_cash_flow_items()
   for row in doc.items:
    row.cash_flow_code=row.cash_flow_code or '1'
   doc.insert();state['cfw_draft']=doc.name;state['docs'].append(['Cash Flow Worksheet',doc.name])
 elif action=='drafts':
  # 提交确认框要草稿：复制已提交单据为草稿。逐张提交事务，失败的记下原因、不连累其余
  strip={'purchase_order','purchase_order_item','purchase_receipt','pr_detail','delivery_note','dn_detail','against_sales_order','against_sales_invoice','prevdoc_docname','quotation_item','job_card','material_request','material_request_item','against_stock_entry','ste_detail'}
  keep_links={'Production Plan','Work Order','Sales Order'}  # 这几种的上游链接是必填，保留
  state.setdefault('draft_errors',{})
  for key,src in (('bom_draft','bom'),('po_draft','purchase_order'),('pr_draft','purchase_receipt'),('pi_draft','purchase_invoice'),('pe_draft','purchase_payment'),('qtn_draft','quotation'),('so_draft','sales_order'),('se_draft','transfer'),('si_draft','sales_invoice')):
   if key in state:continue
   dt=next(d for d,n in state['docs'] if n==state[src])
   try:
    doc=frappe.copy_doc(frappe.get_doc(dt,state[src]))
    if dt not in keep_links:
     for row in doc.get_all_children():
      for f in strip:
       if row.meta.has_field(f):row.set(f,None)
    if dt=='Payment Entry':doc.references=[];doc.reference_no=PREFIX+'草稿'
    if dt=='Stock Entry':doc.purpose='Material Transfer';doc.stock_entry_type='Material Transfer';doc.work_order=None
    if dt=='BOM':doc.is_default=0
    doc.insert();state[key]=doc.name;state['docs'].append([dt,doc.name]);state['draft_errors'].pop(key,None);persist()
   except Exception as e:
    frappe.db.rollback();state['draft_errors'][key]=f'{type(e).__name__}: {e}'
  # 第二张销售订单（已提交）：给生产计划、工单、发货单的草稿当上游，免得撞第一张已满
  if 'so2' not in state:
   so2=frappe.get_doc({'doctype':'Sales Order','company':COMPANY,'customer':state['customer'],'transaction_date':nowdate(),'delivery_date':add_days(nowdate(),1),'currency':'CNY','selling_price_list':'Standard Selling','items':[{'item_code':state['fg'],'qty':1,'rate':50,'warehouse':state['fg_wh'],'delivery_date':add_days(nowdate(),1)}]});so2.insert();so2.submit()
   state['so2']=so2.name;state['docs'].append(['Sales Order',so2.name]);persist()
  if 'so2' in state:
   from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
   tries={
    'pp_draft':lambda:(lambda p:(p.get_items(),p)[1])(frappe.get_doc({'doctype':'Production Plan','company':COMPANY,'get_items_from':'Sales Order','sales_orders':[{'sales_order':state['so2'],'sales_order_date':nowdate(),'customer':state['customer'],'grand_total':50}],'for_warehouse':state['fg_wh']})),
    'wo_draft':lambda:(lambda w:(w.get_items_and_operations_from_bom(),w)[1])(frappe.get_doc({'doctype':'Work Order','company':COMPANY,'production_item':state['fg'],'bom_no':state['bom'],'qty':1,'source_warehouse':state['raw_wh'],'wip_warehouse':state['wip_wh'],'fg_warehouse':state['fg_wh'],'planned_start_date':frappe.utils.now_datetime(),'sales_order':state['so2']})),
    'dn_draft':lambda:make_delivery_note(state['so2']),
   }
   for key,make in tries.items():
    if key in state:continue
    try:
     doc=make();doc.company=COMPANY;doc.insert();state[key]=doc.name;state['docs'].append([doc.doctype,doc.name]);state['draft_errors'].pop(key,None);persist()
    except Exception as e:
     frappe.db.rollback();state['draft_errors'][key]=f'{type(e).__name__}: {e}'
  # 第二张工单（已提交，无销售订单）：提交后生成未完成的生产任务单（供「开始计时」对话框、生产任务单提交确认框）
  if 'wo2' not in state:
   try:
    wo=frappe.get_doc({'doctype':'Work Order','company':COMPANY,'production_item':state['fg'],'bom_no':state['bom'],'qty':1,'source_warehouse':state['raw_wh'],'wip_warehouse':state['wip_wh'],'fg_warehouse':state['fg_wh'],'planned_start_date':frappe.utils.now_datetime()})
    wo.get_items_and_operations_from_bom();wo.insert();wo.submit();state['wo2']=wo.name;state['docs'].append(['Work Order',wo.name]);state['draft_errors'].pop('wo2',None);persist()
   except Exception as e:
    frappe.db.rollback();state['draft_errors']['wo2']=f'{type(e).__name__}: {e}'
  if 'wo2' in state:
   jcs=frappe.get_all('Job Card',filters={'work_order':state['wo2'],'docstatus':0},pluck='name',order_by='sequence_id asc')
   if jcs:state['jc_open']=jcs[0]
 elif action=='opens':
  # 预填屏与取消确认框要「已提交、尚无下游」的上游单据：逐张复制原单、去掉上游链接、提交
  state.setdefault('draft_errors',{})
  if 'fg_receipt' not in state:
   se=frappe.get_doc({'doctype':'Stock Entry','company':COMPANY,'purpose':'Material Receipt','stock_entry_type':'Material Receipt','items':[{'item_code':state['fg'],'qty':5,'t_warehouse':state['fg_wh'],'basic_rate':30}]})
   se.insert();se.submit();state['fg_receipt']=se.name;state['docs'].append(['Stock Entry',se.name]);persist()
  strip={'purchase_order','purchase_order_item','purchase_receipt','pr_detail','delivery_note','dn_detail','against_sales_order','so_detail','sales_order','sales_order_item','prevdoc_docname','quotation_item'}
  # 采购侧复制会连带「已收货／已开票」比例，状态成「已完成」、「创建」菜单不出现；故采购三单新建
  sch=add_days(nowdate(),1)
  makers={
   'po_fresh':lambda:frappe.get_doc({'doctype':'Purchase Order','company':COMPANY,'supplier':state['supplier'],'transaction_date':nowdate(),'schedule_date':sch,'currency':'CNY','buying_price_list':'Standard Buying','set_warehouse':state['raw_wh'],'items':[{'item_code':state['raw'],'qty':10,'rate':10,'schedule_date':sch,'warehouse':state['raw_wh']}]}),
   'pr_fresh':lambda:frappe.get_doc({'doctype':'Purchase Receipt','company':COMPANY,'supplier':state['supplier'],'posting_date':nowdate(),'currency':'CNY','buying_price_list':'Standard Buying','set_warehouse':state['raw_wh'],'items':[{'item_code':state['raw'],'qty':10,'rate':10,'warehouse':state['raw_wh']}]}),
   'pi_fresh':lambda:frappe.get_doc({'doctype':'Purchase Invoice','company':COMPANY,'supplier':state['supplier'],'posting_date':nowdate(),'bill_date':nowdate(),'due_date':nowdate(),'currency':'CNY','buying_price_list':'Standard Buying','items':[{'item_code':state['raw'],'qty':1,'rate':10}]}),
  }
  for key,make in makers.items():
   if key in state:continue
   try:
    doc=make();doc.insert();doc.submit();state[key]=doc.name;state['docs'].append([doc.doctype,doc.name]);state['draft_errors'].pop(key,None);persist()
   except Exception as e:
    frappe.db.rollback();state['draft_errors'][key]=f'{type(e).__name__}: {e}'
  for key,src in (('qtn_open','quotation'),('dn_open','delivery_note'),('si_open','sales_invoice')):
   if key in state:continue
   dt=next(d for d,n in state['docs'] if n==state[src])
   try:
    doc=frappe.copy_doc(frappe.get_doc(dt,state[src]))
    for row in doc.get_all_children():
     for f in strip:
      if row.meta.has_field(f):row.set(f,None)
    if dt in ('Purchase Invoice','Sales Invoice'):
     doc.payment_schedule=[];doc.due_date=nowdate();doc.posting_date=nowdate();doc.set_posting_time=1
     if dt=='Purchase Invoice':doc.bill_date=nowdate()
    doc.insert();doc.submit();state[key]=doc.name;state['docs'].append([dt,doc.name]);state['draft_errors'].pop(key,None);persist()
   except Exception as e:
    frappe.db.rollback();state['draft_errors'][key]=f'{type(e).__name__}: {e}'
 elif action=='crm':
  if 'crm_lead' not in state:
   lead=frappe.get_doc({'doctype':'CRM Lead','first_name':PREFIX+'线索','organization':PREFIX+'客户','email':'s6r6-lead@example.com','status':'New'}).insert();state['crm_lead']=lead.name;state['docs'].append(['CRM Lead',lead.name])
  if 'crm_deal' not in state:
   deal=frappe.get_doc({'doctype':'CRM Deal','organization':None,'lead':state['crm_lead'],'status':'Qualification','expected_deal_value':50,'expected_closure_date':add_days(nowdate(),30)}).insert(ignore_mandatory=True);state['crm_deal']=deal.name;state['docs'].append(['CRM Deal',deal.name])
 else:raise ValueError(action)
 persist();print(frappe.as_json(state))

if __name__=='__main__':
 os.chdir('/workspace/frappe-bench/sites');frappe.init(site=SITE,sites_path='.');frappe.connect();frappe.set_user('Administrator');frappe.local.lang='zh'
 try:run(sys.argv[2])
 finally:frappe.db.rollback();frappe.destroy()
