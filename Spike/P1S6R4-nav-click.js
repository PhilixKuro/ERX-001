const fs = require('node:fs');
const assert = require('node:assert/strict');
const { open } = require('./P1S6R4-cdp.cjs');
const file = 'Spike/P1S6R4-nav-click.out.json';
const report = { results: [] };
const save = () => fs.writeFileSync(file, JSON.stringify(report, null, 2));

(async () => {
	const c = await open();
	try {
		report.browser = c.browser;
		report.boot = await c.evaluate(`({language:frappe.boot.lang, first_icon:frappe.boot.desktop_icons[0],
			icons:frappe.boot.desktop_icon_urls.frappe_china})`);
		assert.equal(report.boot.first_icon.label, 'Business Flow');
		await c.evaluate(`frappe.set_route('desktop');true`);
		await c.until(`!!document.querySelector('.desktop-icon')`);
		report.home = await c.evaluate(`([...document.querySelectorAll('.desktop-icon')].filter(e=>e.getClientRects().length).map(e=>({text:e.innerText,html:e.outerHTML.slice(0,1500)}))).slice(0,3)`);
		await c.screenshot('Spike/P1S6R4-nav-home.png');
		await c.evaluate(`(()=>{const icon=[...document.querySelectorAll('.desktop-icon')].find(e=>e.innerText.includes('业务流程'));if(!icon)throw Error('Business Flow icon missing');icon.click();return true})()`);
		await c.until(`frappe.app.sidebar.sidebar_title==='Business Flow' && document.querySelectorAll('.body-sidebar .sidebar-item-container a[href]').length===51`);
		await c.pause(1000);
		report.sections = await c.evaluate(`([...document.querySelectorAll('.body-sidebar .section-item > .standard-sidebar-item .sidebar-item-label')].map(e=>e.innerText.trim()))`);
		assert.deepEqual(report.sections, ['基础资料','销售','采购','库存','生产','财务','报表']);
		const items = await c.evaluate(`([...document.querySelectorAll('.body-sidebar .sidebar-item-container a[href]')].map(e=>({label:e.innerText.trim(),href:e.getAttribute('href'),target:e.target})))`);
		assert.equal(items.length, 51);
		assert.equal(new Set(items.map(x=>x.label)).size,51);
		await c.screenshot('Spike/P1S6R4-nav-sidebar.png'); save();
		for (const item of items) {
			const r = { ...item, pass: false };
			try {
				const before = (await c.send('Target.getTargets')).targetInfos.map(x=>x.targetId);
				await c.evaluate(`(()=>{const el=[...document.querySelectorAll('.body-sidebar .sidebar-item-container a[href]')].find(e=>e.getAttribute('href')===${JSON.stringify(item.href)});if(!el)throw Error('Sidebar link missing');el.click();return true})()`);
				if (item.target === '_blank') {
					let target;
					for(let i=0;i<30;i++){target=(await c.send('Target.getTargets')).targetInfos.find(x=>x.type==='page'&&!before.includes(x.targetId));if(target)break;await c.pause(100);}
					assert.ok(target,'URL did not open a new tab');
					const sid=(await c.send('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
					await c.send('Runtime.enable',{},sid);
					await c.until(`document.readyState==='complete' && document.body.innerText.length>40`,30000,sid);
					await c.pause(1800);
					r.page=await c.evaluate(`({url:location.href,title:document.title,text:document.body.innerText.slice(0,1200)})`,sid);
					assert.ok(!/\/login\b|404|Not Found|Traceback/.test(r.page.url+' '+r.page.title));
					await c.screenshot(`Spike/P1S6R4-nav-url-${item.href.split('/').filter(Boolean).join('-')}.png`,sid);
					await c.send('Target.closeTarget',{targetId:target.targetId});
				} else {
					await c.until(`decodeURI(location.pathname).startsWith(${JSON.stringify(item.href)})`);
					await c.pause(1000);
					r.page=await c.evaluate(`({url:decodeURI(location.href),route:frappe.get_route(),title:document.title,sidebar:frappe.app.sidebar.sidebar_title,
						text:document.querySelector('.content.page-container[style*="block"]')?.innerText?.slice(0,250),
						trees:[...document.querySelectorAll('.tree-node')].filter(e=>e.getClientRects().length).length})`);
					assert.ok(!/not-found|Not Found|Traceback/.test(r.page.url+' '+r.page.title));
					if(['/desk/account','/desk/cost-center','/desk/warehouse'].includes(item.href)){
						assert.equal(r.page.route[0],'Tree');assert.ok(r.page.trees>0,'Tree has no visible nodes');
						await c.screenshot(`Spike/P1S6R4-nav-tree-${item.href.split('/').pop()}.png`);
					}
					if(['/desk/company','/desk/employee'].includes(item.href)){
						await c.until(`cur_list?.data?.length>0`);
						r.page.records=await c.evaluate('cur_list.data.length');
						await c.screenshot(`Spike/P1S6R4-nav-list-${item.href.split('/').pop()}.png`);
					}
				}
				r.pass=true;
			} catch(error){r.error=String(error);}
			report.results.push(r);save();console.log(JSON.stringify({label:r.label,pass:r.pass,error:r.error}));
			await c.evaluate(`frappe.app.sidebar.setup('Business Flow');true`);
		}
		report.undefined_requests=c.events.filter(x=>x.method==='Network.requestWillBeSent'&&/\/undefined(?:$|\?)/.test(x.params.request.url)).map(x=>x.params.request.url);
		report.passed=report.results.filter(x=>x.pass).length;
		save();console.log(JSON.stringify({passed:report.passed,total:51,undefined:report.undefined_requests}));
		if(report.passed!==51)process.exitCode=1;
	} finally {c.close();}
})().catch(e=>{report.error=String(e);save();console.error(e);process.exitCode=1;});
