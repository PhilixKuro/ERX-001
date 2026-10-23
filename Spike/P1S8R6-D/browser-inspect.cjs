const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const site=process.argv[2];
if(!['s8ts023preview.localhost','s8dev.localhost'].includes(site))throw Error('Invalid site');
(async()=>{
 for(const directory of fs.readdirSync(os.tmpdir()).filter(p=>p.startsWith('erx-s6-cdp-')).reverse()){
  let port;try{port=fs.readFileSync(path.join(os.tmpdir(),directory,'DevToolsActivePort'),'utf8').split('\n')[0];}catch{continue;}
  let targets;try{targets=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();}catch{continue;}
  const target=targets.find(t=>t.type==='page' && t.url.startsWith(`http://${site}:6787/`));if(!target)continue;
  const socket=new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r,j)=>{socket.addEventListener('open',r);socket.addEventListener('error',j);});
  const expression=process.argv[3]?fs.readFileSync(process.argv[3],'utf8'):`({site:window.frappe?.boot?.sitename,route:location.href,state:sessionStorage.getItem('frappe_debug_rehearsal'),config:!!window.frappe_debug?.demo?.config,functions:Object.keys(window.frappe_debug?.demo?.functions||{}),busy:window.frappe_debug?.demo?.rehearsal?.busy,progress:window.frappe_debug?.demo?.progress,error:window.frappe_debug?.demo?.error?.message,body:document.body.innerText.slice(-5000),errors:window.__s8Errors})`;
  const result=new Promise((r,j)=>{socket.addEventListener('message',e=>{const d=JSON.parse(e.data);if(d.id===1)r(d);});setTimeout(()=>j(Error('Inspection timed out')),10000).unref();});
  socket.send(JSON.stringify({id:3,method:'Network.enable',params:{}}));
  socket.send(JSON.stringify({id:4,method:'Network.clearBrowserCache',params:{}}));
  socket.send(JSON.stringify({id:2,method:'Network.setCacheDisabled',params:{cacheDisabled:true}}));
  socket.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression,awaitPromise:true,returnByValue:true}}));
  console.log(JSON.stringify(await result,null,2));socket.close();return;
 }
 throw Error('No running test browser for '+site);
})().catch(e=>{console.error(e);process.exitCode=1;});
