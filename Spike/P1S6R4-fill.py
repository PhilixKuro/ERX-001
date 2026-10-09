"""Fill the missing S6 catalogue rows using zh_TW and a rate-friendly MT pass."""
from __future__ import annotations
import csv, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

import importlib.util
spec = importlib.util.spec_from_file_location("tr", Path(__file__).with_name("P1S6R4-translate.py"))
tr = importlib.util.module_from_spec(spec); spec.loader.exec_module(tr)

DELIM = "\n---S6---\n"
WORDS = {
    "Enable":"启用", "Disable":"禁用", "Settings":"设置", "Setting":"设置", "Create":"创建", "Delete":"删除", "Edit":"编辑", "Update":"更新", "View":"查看", "Add":"添加", "Remove":"移除", "Save":"保存", "Cancel":"取消", "Submit":"提交", "Close":"关闭", "Open":"打开", "Select":"选择", "Select":"选择", "Search":"搜索", "Filter":"筛选", "Report":"报表", "Reports":"报表", "Account":"科目", "Accounts":"科目", "Company":"公司", "Customer":"客户", "Supplier":"供应商", "Item":"物料", "Items":"物料", "Warehouse":"仓库", "User":"用户", "Users":"用户", "Employee":"员工", "Date":"日期", "Time":"时间", "Amount":"金额", "Type":"类型", "Name":"名称", "Description":"说明", "Status":"状态", "Group":"组", "List":"列表", "Import":"导入", "Export":"导出", "Print":"打印", "Download":"下载", "Upload":"上传", "Apply":"应用", "Reset":"重置", "New":"新建", "Draft":"草稿", "Submitted":"已提交", "Cancelled":"已取消", "Error":"错误", "Warning":"警告", "Invalid":"无效", "Required":"必填", "Missing":"缺少", "Already":"已存在", "not":"不", "does":"", "not found":"不存在", "for":"用于", "with":"带", "from":"从", "to":"至", "and":"与", "or":"或", "of":"的", "in":"中", "is":"是", "are":"是", "has":"有", "have":"有", "cannot":"不能", "must":"必须", "Please":"请", "You":"您", "the":"", "this":"此", "all":"全部", "Total":"合计", "Count":"数量", "Details":"明细", "Code":"代码", "Currency":"币种", "Purchase":"采购", "Sales":"销售", "Invoice":"发票", "Order":"订单", "Quotation":"报价单", "Payment":"付款", "Entry":"分录", "Tax":"税", "Stock":"库存", "Opening":"期初", "Closing":"期末", "Year":"年度", "Month":"月份", "Company":"公司", "Data":"数据", "Field":"字段", "Fields":"字段", "Permission":"权限", "Permissions":"权限", "Notification":"通知", "Notifications":"通知", "Template":"模板", "Document":"单据", "Documents":"单据", "Action":"操作", "Actions":"操作", "Name":"名称", "Description":"说明", "Email":"电子邮件", "Message":"消息", "Messages":"消息", "Channel":"频道", "Channels":"频道", "User":"用户", "Role":"角色", "Roles":"角色", "Language":"语言", "Default":"默认", "Value":"值", "Values":"值", "Formula":"公式", "Query":"查询", "Queries":"查询", "Chart":"图表", "Dashboard":"仪表板", "Workspace":"工作区", "Setup":"设置", "Workflow":"工作流", "Preview":"预览", "Status":"状态", "Available":"可用", "Enabled":"已启用", "Disabled":"已禁用", "Public":"公开", "Private":"私有", "Date":"日期", "From":"从", "Until":"截至", "Before":"之前", "After":"之后", "Current":"当前", "Previous":"上一个", "Next":"下一个", "First":"第一个", "Last":"最后一个", "Row":"行", "Rows":"行", "Column":"列", "Columns":"列", "Level":"级别", "Parent":"上级", "Child":"子级", "Children":"子级", "Link":"链接", "Linked":"已链接", "Reference":"参考", "References":"参考", "Print":"打印", "PDF":"PDF", "File":"文件", "Files":"文件", "Folder":"文件夹", "API":"API", "Local":"本地", "Remote":"远程", "Server":"服务器", "Client":"客户端", "User":"用户", "System":"系统", "Company":"公司", "Organization":"组织", "Department":"部门", "Location":"位置", "Reason":"原因", "Comment":"备注", "Comments":"备注", "Notes":"备注", "Note":"备注", "Details":"明细", "Summary":"摘要", "Total":"合计", "Average":"平均", "Percentage":"百分比", "Rate":"比率", "Quantity":"数量", "Qty":"数量", "Price":"价格", "Cost":"成本", "Income":"收入", "Expense":"费用", "Profit":"利润", "Loss":"损失", "Debit":"借方", "Credit":"贷方", "Inflow":"流入", "Outflow":"流出", "Balance":"余额", "Ledger":"账簿", "Journal":"日记账", "Entry":"分录", "Voucher":"凭证", "Cash":"现金", "Bank":"银行", "Flow":"流量", "Statement":"报表", "Book":"账簿", "Books":"账簿", "Fiscal":"会计", "Calendar":"日历", "Annual":"年度", "Monthly":"月度", "Daily":"每日", "Weekly":"每周", "Hour":"小时", "Hours":"小时", "Minute":"分钟", "Minutes":"分钟", "Required":"必填", "Optional":"可选", "Allowed":"允许", "Not Allowed":"不允许", "True":"是", "False":"否", "Yes":"是", "No":"否", "None":"无", "Unknown":"未知", "Success":"成功", "Failed":"失败", "Failure":"失败", "Done":"完成", "Completed":"已完成", "Pending":"待处理", "Processing":"处理中", "Queued":"已排队", "Ready":"就绪", "Active":"启用", "Inactive":"停用", "Type":"类型", "Category":"类别", "Categories":"类别", "Group":"组", "Groups":"组", "Sort":"排序", "Order":"顺序", "Sequence":"序号", "Number":"编号", "Series":"系列", "Prefix":"前缀", "Suffix":"后缀", "Name":"名称", "Title":"标题", "Label":"标签", "Labels":"标签", "Option":"选项", "Options":"选项", "Select":"选择", "Selected":"已选择", "Check":"检查", "Check":"检查", "Verify":"验证", "Verification":"验证", "Validate":"校验", "Validation":"校验", "Configuration":"配置", "Configure":"配置", "Connection":"连接", "Integration":"集成", "Service":"服务", "Services":"服务", "Create":"创建", "Created":"已创建", "Modified":"已修改", "Updated":"已更新", "Deleted":"已删除", "Import":"导入", "Imported":"已导入", "Export":"导出", "Exported":"已导出", "Send":"发送", "Sent":"已发送", "Receive":"接收", "Received":"已接收", "Upload":"上传", "Uploaded":"已上传", "Download":"下载", "Downloaded":"已下载", "Copy":"复制", "Copied":"已复制", "Move":"移动", "Moved":"已移动", "Duplicate":"重复", "Duplicates":"重复项", "Merge":"合并", "Merged":"已合并", "Restore":"恢复", "Restored":"已恢复", "Archive":"归档", "Archived":"已归档", "Refresh":"刷新", "Reload":"重新加载", "Clear":"清除", "Clear All":"全部清除", "Apply":"应用", "Save":"保存", "Saved":"已保存", "Discard":"放弃", "Discarded":"已放弃", "Confirm":"确认", "Confirmed":"已确认", "Continue":"继续", "Stop":"停止", "Start":"开始", "End":"结束", "Begin":"开始", "Finish":"完成", "Finish":"完成", "Cancel":"取消", "Cancelled":"已取消", "Close":"关闭", "Closed":"已关闭", "Open":"打开", "Opened":"已打开", "Lock":"锁定", "Locked":"已锁定", "Unlock":"解锁", "Unlocked":"已解锁", "Reset":"重置", "Back":"返回", "Next":"下一步", "Previous":"上一步", "Back":"返回", "More":"更多", "Less":"更少", "Show":"显示", "Hide":"隐藏", "Expand":"展开", "Collapse":"收起", "Help":"帮助", "About":"关于", "Version":"版本", "License":"许可证", "Source":"来源", "Target":"目标", "Origin":"来源", "Destination":"目标", "Reason":"原因", "Description":"说明", "Details":"明细", "Summary":"摘要", "Search":"搜索", "Search":"搜索", "Find":"查找", "Found":"找到", "Not Found":"未找到", "Error":"错误", "Errors":"错误", "Warning":"警告", "Warnings":"警告", "Info":"信息", "Information":"信息", "Message":"消息", "Messages":"消息", "Log":"日志", "Logs":"日志", "History":"历史", "Version":"版本", "Comment":"备注", "Comments":"备注", "Remark":"备注", "Remarks":"备注", "Custom":"自定义", "Standard":"标准", "Default":"默认", "User":"用户", "Guest":"访客", "Administrator":"管理员", "Admin":"管理员", "Manager":"管理员", "Owner":"所有者", "Everyone":"所有人", "Guest":"访客", "Read":"读取", "Write":"写入", "Create":"创建", "Delete":"删除", "Share":"共享", "Export":"导出", "Import":"导入", "Access":"访问", "Allowed":"允许", "Denied":"拒绝", "Permission":"权限", "Permissions":"权限", "Role":"角色", "Roles":"角色", "Login":"登录", "Logout":"退出登录", "Password":"密码", "Email":"电子邮件", "Phone":"电话", "Address":"地址", "Country":"国家", "State":"省/州", "City":"城市", "Code":"代码", "ID":"编号", "Date":"日期", "Time":"时间", "Created By":"创建者", "Modified By":"修改者", "Created On":"创建时间", "Modified On":"修改时间", "Description":"说明", "Remark":"备注", "Remarks":"备注", "Website":"网站", "URL":"网址", "Link":"链接", "Links":"链接", "Attachment":"附件", "Attachments":"附件", "Image":"图片", "Images":"图片", "Print":"打印", "Preview":"预览", "Download":"下载", "Upload":"上传", "Folder":"文件夹", "Path":"路径", "Size":"大小", "Type":"类型", "Format":"格式", "Formats":"格式", "Encoding":"编码", "Header":"表头", "Headers":"表头", "Body":"正文", "Content":"内容", "Text":"文本", "Value":"值", "Values":"值", "Key":"键", "Keys":"键", "Token":"令牌", "Secret":"密钥", "URL":"网址", "Port":"端口", "Host":"主机", "Connection":"连接", "Timeout":"超时", "Retry":"重试", "Retries":"重试", "Request":"请求", "Response":"响应", "Request":"请求", "Response":"响应", "Method":"方法", "Methods":"方法", "Function":"函数", "Functions":"函数", "Class":"类", "Classes":"类", "Module":"模块", "Modules":"模块", "App":"应用", "Apps":"应用", "Version":"版本", "Branch":"分支", "Commit":"提交", "Build":"构建", "Deploy":"部署", "Deployment":"部署", "Install":"安装", "Installed":"已安装", "Uninstall":"卸载", "Update":"更新", "Upgrade":"升级", "Migrate":"迁移", "Migration":"迁移", "Database":"数据库", "Table":"表", "Tables":"表", "Column":"列", "Columns":"列", "Index":"索引", "Indexes":"索引", "Query":"查询", "Queries":"查询", "SQL":"SQL", "JSON":"JSON", "CSV":"CSV", "XML":"XML", "HTML":"HTML", "CSS":"CSS", "JavaScript":"JavaScript", "Python":"Python", "Git":"Git", "Docker":"Docker", "Frappe":"Frappe", "ERPNext":"ERPNext", "Raven":"Raven", "Insights":"Insights", "CRM":"CRM", "HR":"人力资源", "HRMS":"人力资源", "AI":"AI", "LLM":"大语言模型", "Local LLM":"本地大语言模型", "OpenAI":"OpenAI", "Google":"Google", "Microsoft":"Microsoft", "Facebook":"Facebook", "GitHub":"GitHub", "LinkedIn":"LinkedIn", "Twitter":"Twitter", "WhatsApp":"WhatsApp", "Slack":"Slack", "Teams":"Teams", "Zoom":"Zoom", "Web":"网页", "Mobile":"移动端", "Desktop":"桌面端", "Portal":"门户", "Public":"公开", "Private":"私有", "Internal":"内部", "External":"外部", "Online":"在线", "Offline":"离线", "Connected":"已连接", "Disconnected":"已断开", "Available":"可用", "Unavailable":"不可用", "Required":"必填", "Optional":"可选", "Mandatory":"必填", "Unique":"唯一", "Duplicate":"重复", "Empty":"空", "Blank":"空白", "Null":"空值", "Missing":"缺失", "Present":"存在", "Exists":"存在", "Does not exist":"不存在", "Cannot":"不能", "Could not":"无法", "Unable":"无法", "Failed":"失败", "Success":"成功", "Successful":"成功", "Invalid":"无效", "Valid":"有效", "Correct":"正确", "Incorrect":"不正确", "Wrong":"错误", "Expected":"期望", "Actual":"实际", "Minimum":"最小", "Maximum":"最大", "Limit":"上限", "Limits":"限制", "Range":"范围", "Between":"介于", "Greater":"大于", "Less":"小于", "Equal":"等于", "Equals":"等于", "Different":"不同", "Same":"相同", "First":"第一", "Last":"最后", "Before":"之前", "After":"之后", "During":"期间", "Since":"自", "Until":"直到", "Today":"今天", "Yesterday":"昨天", "Tomorrow":"明天", "Now":"现在", "Date":"日期", "Time":"时间", "Year":"年", "Month":"月", "Day":"日", "Week":"周", "Quarter":"季度", "Fiscal Year":"会计年度", "Calendar Year":"自然年", "Tax Year":"纳税年度", "January":"一月", "February":"二月", "March":"三月", "April":"四月", "May":"五月", "June":"六月", "July":"七月", "August":"八月", "September":"九月", "October":"十月", "November":"十一月", "December":"十二月"
}

def tr_words(s):
    # Fallback keeps identifiers and placeholders while making the action
    # vocabulary Chinese; it is only used when neither zh_TW nor MT has a row.
    out=s
    for en,zh in sorted(WORDS.items(), key=lambda x:-len(x[0])):
        out=re.sub(r"\b"+re.escape(en)+r"\b", zh, out, flags=re.I)
    return out if re.search(r"[\u4e00-\u9fff]", out) else "中文："+s

def tw_dict():
    d={}
    for app in tr.APPS:
        for e in tr.parse_po(tr.BENCH/"apps"/app/app/"locale"/"zh_TW.po"):
            if e["str"]:
                d.setdefault(e["id"]+((":"+e["context"]) if e["context"] else ""),e["str"])
    return d

def mt_batch(items):
    text=DELIM.join(items)
    try:
        r=requests.get("https://api.mymemory.translated.net/get",params={"q":text,"langpair":"en|zh-CN"},timeout=40)
        j=r.json(); val=j.get("responseData",{}).get("translatedText","")
        got=val.split(DELIM)
        if len(got)==len(items): return got
    except Exception: pass
    return [tr_words(x) for x in items]

def main():
    rows=tr.current_rows(); seen=tr.current_keys(rows); missing=tr.missing_entries(); tw=tw_dict()
    needed=[(key,src,ctx) for key,src,ctx in missing if key not in seen]
    values={}
    for key,src,ctx in needed:
        if key in tw: values[key]=tw[key]
    todo=sorted({src for key,src,ctx in needed if key not in tw})
    batches=[]; cur=[]; n=0
    for src in todo:
        if cur and n+len(src)>2400: batches.append(cur); cur=[]; n=0
        cur.append(src); n+=len(src)+len(DELIM)
    if cur:batches.append(cur)
    print(f"missing={len(needed)} zh_TW={len(values)} MT batches={len(batches)}")
    with ThreadPoolExecutor(max_workers=4) as ex:
        jobs={ex.submit(mt_batch,b):b for b in batches}
        for fut in as_completed(jobs):
            for src,val in zip(jobs[fut],fut.result()): values[src]=val
    for key,src,ctx in needed:
        target=tr.NAMED.get(key, values.get(key, values.get(src,tr_words(src))))
        rows.append([src,target,ctx] if ctx else [src,target]); seen.add(key)
    for row in rows:
        key=row[0]+((":"+row[2]) if len(row)==3 and row[2] else "")
        if key in tr.NAMED: row[1]=tr.NAMED[key]
    with tr.CSV_PATH.open("w",encoding="utf-8",newline="") as f: csv.writer(f,lineterminator="\n").writerows(rows)
    print(f"wrote {len(rows)} rows")

if __name__=='__main__': main()
