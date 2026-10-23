const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
(async()=>{
 for(const directory of fs.readdirSync(os.tmpdir()).filter(name=>name.startsWith('erx-s6-cdp-')).reverse()){
  let port;try{port=fs.readFileSync(path.join(os.tmpdir(),directory,'DevToolsActivePort'),'utf8').split('\n')[0]}catch{continue}
  let targets;try{targets=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()}catch{continue}
  const target=targets.find(item=>item.type==='page'&&item.url.startsWith('http://s8dev.localhost:6787/'));
  if(!target)continue;
  const socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve);socket.addEventListener('error',reject)});
  const result=new Promise((resolve,reject)=>{socket.addEventListener('message',event=>{const data=JSON.parse(event.data);if(data.id===1)resolve(data)});setTimeout(()=>reject(Error('Inspection timeout')),10000).unref()});
  socket.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:`({route:location.pathname,progress:frappe_debug.demo.progress,state:sessionStorage.getItem('frappe_debug_rehearsal'),busy:frappe_debug.demo.rehearsal.busy,error:window.__s8Errors,wait:window.__s8WaitTrace,dialog:window.cur_dialog?.$wrapper?.text(),form:window.cur_frm?.doctype,requests:performance.getEntriesByType('resource').filter(x=>x.name.includes('/api/method/')).slice(-8).map(x=>({name:x.name.split('/api/method/')[1],duration:x.duration}))})`,returnByValue:true}}));
  const response=await result;console.log(JSON.stringify(response.result.result.value,null,2));socket.close();return;
 }
 throw Error('Acceptance browser not found');
})().catch(error=>{console.error(error);process.exitCode=1});
