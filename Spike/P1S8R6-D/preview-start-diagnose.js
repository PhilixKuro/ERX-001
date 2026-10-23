(async()=>{
 if(frappe.boot.sitename!=='s8ts023preview.localhost')throw Error('Wrong preview site');
 const demo=frappe_debug.demo;
 let error;try{await demo.start();}catch(cause){error=cause.message||String(cause);}
 return {error,config:!!demo.config,functions:Object.keys(demo.functions),scripts:Array.from(document.scripts).map(script=>script.src).filter(src=>src.includes('frappe_debug')),sourceHasNewFunction:(await(await fetch('/assets/frappe_debug/js/demo/functions.js?inspect='+Date.now())).text()).includes('create_purchase_order_from_request'),state:JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal'))};
})()
