(async () => {
  if (frappe.boot.sitename !== 's8ts023preview.localhost') throw Error('Unexpected site');
  const alert = window.jQuery('.modal:visible').toArray().find(el => el.querySelector('.modal-title')?.innerText === '必填字段信息缺失');
  alert?.querySelector('.btn-primary')?.click();
  await new Promise(resolve => setTimeout(resolve, 300));
  try {
    await cur_frm.save('Submit');
    return JSON.stringify({docstatus: cur_frm.doc.docstatus, dirty: cur_frm.is_dirty(), name: cur_frm.doc.name});
  } catch (error) {
    return JSON.stringify({error: error?.message || String(error), docstatus: cur_frm.doc.docstatus, dirty: cur_frm.is_dirty(), name: cur_frm.doc.name});
  }
})()
