const {open} = require('../P1S6R4-cdp.cjs');
(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    console.log(await c.evaluate(`(async () => {
      const config=await frappe.xcall('frappe_debug.demo.config.get_demo_config');
      const args={from_date:config.segments[0][0],to_date:config.segments[0][1]};
      try{return {config:{dates:config.dates,segments:config.segments},args,result:await frappe.xcall('frappe_debug.scenario.runner.start_generate',args)}}
      catch(error){return {config:{dates:config.dates,segments:config.segments},args,error:JSON.stringify(error)}}
    })()`));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
