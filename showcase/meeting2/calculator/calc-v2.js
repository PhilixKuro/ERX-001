"use strict";
/* 经营测算器第二版 · 计算部分（P1-S10 R04 第 3 步，复制自 calc.js 后改）
   只算数，不碰页面。单位：金额万元、时间天、人数人；比例一律用小数（0.1 即 10%）。
   第二版的变化：除年数、推向市场年份、加入年份、试验厂、名称以外，所有数都按年份填（数组下标 0 即第 1 年）；
   没填的年份沿用前面最近一个填了的年份。「自家工厂买」只在勾的那年算，不沿用。
   分成比例改为一张表：每行一类收入，每列一个角色，填的是占整单的比例。
   介绍单量按年、按人填；试验厂是具体某几位销售合伙人的工厂；线下课按年填在哪个示范工厂上。
   默认值出自合作方案草案 v16 与讲稿 index-v5.html 经营测算 5 页；口径见
   docs/01-需求摸底/S10-商业化商讨/R04-经营测算器/P1-S10-R4-Pai000协作记录.md 第 2、3 步。 */
const CALC = (() => {
  const num = x => (Number.isFinite(+x) ? +x : 0);
  const isSet = x => x !== null && x !== undefined && x !== "";
  /* 逐年值：第 i 年没填时沿用前面最近一个填了的年份 */
  function yv(a, i) {
    if (!Array.isArray(a)) return num(a);
    for (let k = Math.min(i, a.length - 1); k >= 0; k--) if (isSet(a[k])) return num(a[k]);
    return 0;
  }
  /* 第 i 年的值来自哪一年（下标）；-1 表示一直没填 */
  function src(a, i) {
    if (!Array.isArray(a)) return 0;
    for (let k = Math.min(i, a.length - 1); k >= 0; k--) if (isSet(a[k])) return k;
    return -1;
  }
  /* 只在当年算、不沿用 */
  const ev = (a, i) => (Array.isArray(a) ? num(a[i]) : 0);
  const clampYears = n => Math.max(1, Math.min(10, Math.round(num(n)) || 1));

  /* 分成表：每行一类收入，cols 是这一行能填的角色 */
  const SPLIT_ROWS = [
    { k: "erpP", g: "ERP 模块费", n: "销售合伙人介绍", cols: ["co", "tech", "intro"] },
    { k: "erpO", g: "ERP 模块费", n: "其他销售介绍", cols: ["co", "tech", "intro"] },
    { k: "dayP", g: "实施人天与变更单", n: "销售合伙人介绍", cols: ["co", "tech", "intro"] },
    { k: "dayO", g: "实施人天与变更单", n: "其他销售介绍", cols: ["co", "tech", "intro"] },
    { k: "maint", g: "年维护", n: "ERP 与降本增效项目", cols: ["co", "tech"] },
    { k: "projP", g: "降本增效项目", n: "销售合伙人介绍", cols: ["co", "tech", "intro"] },
    { k: "projO", g: "降本增效项目", n: "其他销售介绍", cols: ["co", "tech", "intro"] },
    { k: "geoP", g: "宣传与获客（GEO）", n: "销售合伙人介绍", cols: ["co", "tech", "intro"] },
    { k: "geoO", g: "宣传与获客（GEO）", n: "其他销售介绍", cols: ["co", "tech", "intro"] },
    { k: "course", g: "驻厂工程师培训班", n: "线下课（扣直接成本以后）", cols: ["co", "tech", "demo"] },
    { k: "online", g: "驻厂工程师培训班", n: "线上课", cols: ["co", "tech"] },
    { k: "referral", g: "驻厂工程师培训班", n: "学员推荐费", cols: ["co", "tech"] },
  ];
  const ROLES = [["co", "数字化合作公司"], ["tech", "技术方"], ["intro", "介绍人"], ["demo", "示范工厂"]];
  const m3 = (co, tech, intro) => ({ co: [co], tech: [tech], intro: [intro] });

  const DEFAULTS = {
    years: 3,
    tax: { vat: [0], introducerTax: [0] },
    partners: [
      { id: "tech", tech: true, name: "技术方", share: [0.35] },
      { id: "p1", name: "销售合伙人", join: 1, share: [0.65] },
    ],
    split: {
      erpP: m3(0.10, 0.63, 0.27), erpO: m3(0.165, 0.70, 0.135),
      dayP: m3(0, 0.70, 0.30), dayO: m3(0.15, 0.70, 0.15),
      maint: { co: [0], tech: [1] },
      projP: m3(0.10, 0.63, 0.27), projO: m3(0.165, 0.70, 0.135),
      geoP: m3(0.10, 0.63, 0.27), geoO: m3(0.165, 0.70, 0.135),
      course: { co: [0.10], tech: [0.45], demo: [0.45] },
      online: { co: [0], tech: [1] },
      referral: { co: [1], tech: [0] },
      trialRatio: [0.5], trialDeduct: [0.05],
    },
    erp: { module: [13], dayRate: [0.15, 0.18], implDays: [30], changeDays: [0], maintRate: [0.10], maintRetain: [1],
           sales: { p1: [4, 5, 6], other: [2, 3, 4] }, own: {} },
    projects: [
      { id: "j1", name: "AI 报价助手", launch: 1, trials: ["p1"], rdDays: 60, hardware: 1,
        price: [4], implDays: [0], maintRate: [0.10], sales: { p1: [3, 5], other: [2, 3] }, own: {} },
    ],
    geo: { price: [3], renew: [0.8], days: [10], sales: { p1: [2], other: [2] } },
    course: { students: [30], fee: [0.6], directCost: [0.15], teachDays: [10], hosts: { ext: [4] },
              onlineFee: [0.2], online: [0], referralFee: [0.5], referrals: [0] },
    company: { ops: [0.6], marketing: [3], reserveAnnual: [5], reserveCap: [5], refundRate: [0], bonusRate: [0.30],
               cit: [0], legalReserve: [0], techShareMin: [0.35] },
    tech: { ownerMonthly: [1.5], staffMonthly: [2], staff: [0, 1, 2], ownerDays: [120], staffDays: [200], maintDays: [3],
            serverCost: [1.5], perServer: [10], aiCost: [0.2] },
  };

  const KEYS = ["co", "tech", "introP", "introO", "demo", "direct"];
  function newLine(name) {
    const L = { name, gross: 0, vat: 0, parts: {} };
    KEYS.forEach(k => { L[k] = 0; L.parts[k] = []; });
    return L;
  }
  function put(L, key, label, v) { if (!v) return; L[key] += v; L.parts[key].push([label, v]); }
  const n1 = x => String(Math.round(x * 10) / 10);
  const pc = x => `${Math.round(x * 1000) / 10}%`;
  const yuan = x => `${Math.round(x * 10000)} 元`;
  const joinYear = p => (p.tech ? 1 : Math.max(1, Math.round(num(p.join)) || 1));

  function compute(inp) {
    const N = clampYears(inp.years);
    const sales = inp.partners.filter(p => !p.tech);
    const techRow = inp.partners.find(p => p.tech) || { share: [0] };
    const st = { erp: 0, proj: inp.projects.map(() => ({ active: 0, pools: null })), geo: {}, reserve: 0, loss: 0 };
    const out = [];

    for (let i = 0; i < N; i++) {
      const y = i + 1;
      const Y = a => yv(a, i);
      const act = p => y >= joinYear(p);
      const actSales = sales.filter(act);
      const ids = [...actSales.map(p => p.id), "other"];
      const nm = id => (id === "other" ? "其他销售" : (sales.find(p => p.id === id) || {}).name || "销售合伙人");
      const sp = (k, c) => yv((inp.split[k] || {})[c], i);
      const v = 1 / (1 + Y(inp.tax.vat));
      const staff = Math.max(0, Y(inp.tech.staff)), rate = Y(inp.erp.dayRate), md = Y(inp.tech.maintDays);
      const lines = { erp: newLine("ERP"), proj: inp.projects.map(p => newLine(p.name || "降本增效项目")),
                      geo: newLine("宣传与获客（GEO）"), course: newLine("驻厂工程师培训班") };
      const per = {};
      sales.forEach(p => { per[p.id] = { intro: 0, introParts: [], vol: 0, own: 0, ownParts: [], demo: 0, trial: 0, trialParts: [] }; });
      const other = { intro: 0, introParts: [], vol: 0 };
      const P = id => (id === "other" ? other : per[id]);
      const days = { impl: 0, maint: 0, proj: 0, rd: 0, geo: 0, teach: 0 };
      let hardware = 0, onlineGross = 0, extDemo = 0;
      const sale = (L, G) => { L.gross += G; L.vat += G * (1 - v); return G * v; };
      /* 按分成表的一行分一笔钱；who 是介绍人 id（没有介绍人时为 null） */
      function split(L, k, who, label, G) {
        const net = sale(L, G);
        put(L, "co", label, net * sp(k, "co"));
        put(L, "tech", label, net * sp(k, "tech"));
        const intro = net * sp(k, "intro");
        if (intro && who) {
          put(L, who === "other" ? "introO" : "introP", label, intro);
          P(who).intro += intro; P(who).introParts.push([`${L.name} · ${label}`, intro]);
        }
        return net;
      }
      const pk = id => (id === "other" ? "O" : "P");

      /* ---- ERP ---- */
      let L = lines.erp;
      const M = Y(inp.erp.module), impl = Y(inp.erp.implDays), chg = Y(inp.erp.changeDays), ret = Y(inp.erp.maintRetain);
      const ext = { P: 0, O: 0 };
      let ownNew = 0;
      for (const id of ids) {
        const n = Y((inp.erp.sales || {})[id]);
        if (!n) continue;
        const tag = `${nm(id)}介绍 ${n1(n)} 家`;
        split(L, "erp" + pk(id), id, `${tag}：模块费 ${M} 万 × ${n1(n)}`, M * n);
        if (impl + chg) split(L, "day" + pk(id), id, `${tag}：实施与变更 ${impl + chg} 天 × ${yuan(rate)} × ${n1(n)}`, (impl + chg) * rate * n);
        P(id).vol += (M + (impl + chg) * rate) * n;
        ext[pk(id)] += n;
      }
      actSales.forEach(p => {
        if (!ev((inp.erp.own || {})[p.id], i)) return;
        ownNew++;
        const co = M * sp("erpP", "co"), tech = M * sp("erpP", "tech"), paid = co + tech;
        sale(L, paid);
        const tag = `${p.name || "销售合伙人"}自家工厂：销售合伙人价 ${M} 万 × ${pc(sp("erpP", "co") + sp("erpP", "tech"))}，免实施费`;
        put(L, "co", tag, co * v); put(L, "tech", tag, tech * v);
        per[p.id].own += paid; per[p.id].ownParts.push(["ERP", paid]); per[p.id].vol += paid;
      });
      const kept = st.erp * ret;
      if (kept) split(L, "maint", null, `年维护 ${n1(kept)} 家 × ${M} 万 × ${pc(Y(inp.erp.maintRate))}`, kept * M * Y(inp.erp.maintRate));
      st.erp = kept + ext.P + ext.O + ownNew;
      days.impl += (ext.P + ext.O) * (impl + chg) + ownNew * impl;
      days.maint += kept * md;
      const perOrder = {
        P: M * sp("erpP", "tech") + (impl + chg) * rate * sp("dayP", "tech"),
        O: M * sp("erpO", "tech") + (impl + chg) * rate * sp("dayO", "tech"),
      };

      /* ---- 降本增效项目 ---- */
      const tRatio = yv(inp.split.trialRatio, i), tDeduct = yv(inp.split.trialDeduct, i);
      inp.projects.forEach((pj, j) => {
        const L = lines.proj[j], S = st.proj[j], launch = Math.max(1, Math.round(num(pj.launch)) || 1);
        if (y < launch) return;
        const Pp = Y(pj.price), Di = Y(pj.implDays);
        if (S.pools === null) {                                   /* 推向市场那年按当年市场价锁定 */
          S.pools = {};
          (pj.trials || []).forEach(id => { if (per[id]) S.pools[id] = Pp * tRatio; });
        }
        if (y === launch) { hardware += num(pj.hardware); days.rd += num(pj.rdDays); }
        const keptP = S.active * ret;
        if (keptP) split(L, "maint", null, `年维护 ${n1(keptP)} 家 × ${Pp} 万 × ${pc(Y(pj.maintRate))}`, keptP * Pp * Y(pj.maintRate));
        days.maint += keptP * md;
        let n = 0, own = 0;
        for (const id of ids) {
          const c = Y((pj.sales || {})[id]);
          if (!c) continue;
          const tag = `${nm(id)}介绍 ${n1(c)} 家`;
          split(L, "proj" + pk(id), id, `${tag}：${Pp} 万 × ${n1(c)}`, Pp * c);
          if (Di) split(L, "day" + pk(id), id, `${tag}：实施 ${Di} 天 × ${yuan(rate)} × ${n1(c)}`, Di * rate * c);
          P(id).vol += (Pp + Di * rate) * c; n += c;
        }
        actSales.forEach(p => {
          if (!ev((pj.own || {})[p.id], i)) return;
          own++;
          const co = Pp * sp("projP", "co") + Di * rate * sp("dayP", "co"), tech = Pp * sp("projP", "tech") + Di * rate * sp("dayP", "tech");
          const paid = co + tech; sale(L, paid);
          const tag = `${p.name || "销售合伙人"}自家工厂：销售合伙人价 ${Pp} 万 × ${pc(sp("projP", "co") + sp("projP", "tech"))}`;
          put(L, "co", tag, co * v); put(L, "tech", tag, tech * v);
          per[p.id].own += paid; per[p.id].ownParts.push([pj.name || "降本增效项目", paid]); per[p.id].vol += paid;
        });
        /* 替试验厂抵扣：每卖一单从合作公司拿出整单一定比例付技术方，平分给还没抵清的各家 */
        let rem = n * Pp * tDeduct, guard = 0;
        const ded = {};
        while (rem > 1e-9 && guard++ < 50) {
          const open = Object.keys(S.pools).filter(k => S.pools[k] > 1e-9);
          if (!open.length) break;
          const each = rem / open.length;
          let used = 0;
          open.forEach(k => { const x = Math.min(each, S.pools[k]); S.pools[k] -= x; ded[k] = (ded[k] || 0) + x; used += x; });
          rem -= used;
        }
        const total = Object.values(ded).reduce((a, b) => a + b, 0);
        if (total > 1e-9) {
          const who = Object.keys(ded).map(k => `${nm(k)} ${Math.round(ded[k] * 100) / 100} 万`).join("、");
          const tag = `替试验厂抵扣：${Pp} 万 × ${pc(tDeduct)} × ${n1(n)} 单${rem > 1e-9 ? "（已抵清的不再抵）" : ""}，${who}`;
          put(L, "co", tag, -total * v); put(L, "tech", tag, total * v);
          Object.keys(ded).forEach(k => { per[k].trial += ded[k]; per[k].trialParts.push([pj.name || "降本增效项目", ded[k]]); });
        }
        S.active = keptP + n + own;
        days.proj += (n + own) * Di;
      });

      /* ---- 宣传与获客（GEO 年度服务，按年收费，老客户续费） ---- */
      L = lines.geo;
      const G = Y(inp.geo.price), renew = Y(inp.geo.renew);
      let geoAll = 0;
      for (const id of ids) {
        st.geo[id] = (st.geo[id] || 0) * renew + Y((inp.geo.sales || {})[id]);
        const n = st.geo[id];
        if (!n) continue;
        split(L, "geo" + pk(id), id, `${nm(id)}介绍 ${n1(n)} 家（含续费）：${G} 万 × ${n1(n)}`, G * n);
        P(id).vol += G * n; geoAll += n;
      }
      days.geo += geoAll * Y(inp.geo.days);

      /* ---- 驻厂工程师培训班 ---- */
      L = lines.course;
      const cs = inp.course, stu = Y(cs.students), fee = Y(cs.fee), dc = Y(cs.directCost);
      const hosts = {};
      let sesAll = 0;
      for (const h of [...actSales.map(p => p.id), "ext"]) {
        const ses = Y((cs.hosts || {})[h]);
        if (!ses) continue;
        sesAll += ses; hosts[h] = ses;
        const Gc = ses * stu * fee, net = sale(L, Gc), direct = Gc * dc, rest = net - direct;
        const hn = h === "ext" ? "非合伙人的示范工厂" : `${nm(h)}的工厂`;
        const tag = `${hn}：线下课 ${n1(ses)} 期 × ${stu} 人 × ${yuan(fee)}`;
        put(L, "direct", `${tag}，直接成本 ${pc(dc)}`, direct);
        put(L, "co", `${tag}，扣直接成本后 ${pc(sp("course", "co"))}`, rest * sp("course", "co"));
        put(L, "tech", `${tag}，扣直接成本后 ${pc(sp("course", "tech"))}`, rest * sp("course", "tech"));
        const dm = rest * sp("course", "demo");
        put(L, "demo", `${tag}，扣直接成本后 ${pc(sp("course", "demo"))}`, dm);
        if (h === "ext") extDemo += dm; else per[h].demo += dm;
      }
      days.teach += sesAll * Y(cs.teachDays);
      const onl = Y(cs.online) * Y(cs.onlineFee);
      if (onl) { onlineGross += onl; split(L, "online", null, `线上课 ${n1(Y(cs.online))} 人 × ${yuan(Y(cs.onlineFee))}`, onl); }
      const rf = Y(cs.referrals) * Y(cs.referralFee);
      if (rf) split(L, "referral", null, `学员推荐费 ${n1(Y(cs.referrals))} 人 × ${yuan(Y(cs.referralFee))}`, rf);

      /* ---- 汇总 ---- */
      const all = [lines.erp, ...lines.proj, lines.geo, lines.course];
      const sum = k => all.reduce((a, l) => a + l[k], 0);
      const gross = sum("gross"), vat = sum("vat"), coRev = sum("co"), introP = sum("introP"), introO = sum("introO");
      const demo = sum("demo"), direct = sum("direct"), lineTech = sum("tech");

      /* ---- 数字化合作公司的账 ---- */
      const c = inp.company;
      const refunds = (gross - onlineGross) * Y(c.refundRate);
      let b = st.reserve;
      const fromRes = Math.min(b, refunds); b -= fromRes;
      const shortfall = refunds - fromRes;
      const contrib = Math.min(Y(c.reserveAnnual), Math.max(0, Y(c.reserveCap) - b)); b += contrib; st.reserve = b;
      const expenses = Y(c.ops) + Y(c.marketing) + hardware + contrib + shortfall;
      const lossIn = st.loss;
      let pre = coRev - expenses - lossIn, bonus = 0, cit = 0, legal = 0, div = 0;
      if (pre < 0) st.loss = -pre;
      else {
        st.loss = 0; bonus = pre * Y(c.bonusRate);
        const ab = pre - bonus; cit = ab * Y(c.cit); legal = (ab - cit) * Y(c.legalReserve); div = ab - cit - legal;
      }
      const V = sales.reduce((a, p) => a + per[p.id].vol, 0) + other.vol;
      const techShare = Y(techRow.share), divTech = div * techShare;
      const iTax = Y(inp.tax.introducerTax);
      const people = sales.map(p => {
        const q = per[p.id], on = act(p), share = on ? Y(p.share) : 0;
        const bn = V ? bonus * q.vol / V : 0, dv = div * share, intro = q.intro * (1 - iTax);
        return { id: p.id, name: p.name || "销售合伙人", active: on, share, intro, introParts: q.introParts, bonus: bn, div: dv,
                 demo: q.demo, own: q.own, ownParts: q.ownParts, trial: q.trial, trialParts: q.trialParts, vol: q.vol,
                 net: intro + bn + dv + q.demo - q.own };
      });
      const otherBonus = V ? bonus * other.vol / V : 0;
      const oth = { intro: other.intro * (1 - iTax), introParts: other.introParts, bonus: otherBonus, vol: other.vol,
                    net: other.intro * (1 - iTax) + otherBonus };
      const divP = people.reduce((a, p) => a + p.div, 0);
      const assigned = otherBonus + people.reduce((a, p) => a + p.bonus, 0) + divTech + divP;
      const introTax = (introP + introO) * iTax;

      /* ---- 技术方 ---- */
      const servers = st.erp > 0 && Y(inp.tech.perServer) > 0 ? Math.ceil(st.erp / Y(inp.tech.perServer) - 1e-9) : 0;
      const cost = { owner: 12 * Y(inp.tech.ownerMonthly), staff: 12 * staff * Y(inp.tech.staffMonthly),
                     server: servers * Y(inp.tech.serverCost), ai: st.erp * Y(inp.tech.aiCost) };
      cost.total = cost.owner + cost.staff + cost.server + cost.ai;
      const techIncome = lineTech + divTech;
      const need = days.impl + days.maint + days.proj + days.rd + days.geo + days.teach;
      const ownerDays = Y(inp.tech.ownerDays), staffDays = Y(inp.tech.staffDays);
      const cap = ownerDays + staff * staffDays;
      const nn = ext.P + ext.O;
      const avg = nn ? (ext.P * perOrder.P + ext.O * perOrder.O) / nn : perOrder.P;
      const tech = { income: techIncome, lineTech, div: divTech, share: techShare, cost, profit: techIncome - cost.total,
                     margin: techIncome ? (techIncome - cost.total) / techIncome : 0, staff, rate, servers, clients: st.erp,
                     staffMonthly: Y(inp.tech.staffMonthly), perServer: Y(inp.tech.perServer), serverCost: Y(inp.tech.serverCost),
                     days, need, cap, util: cap ? need / cap : Infinity,
                     needStaff: staffDays > 0 ? Math.max(0, Math.ceil((need - ownerDays) / staffDays - 1e-9)) : 0,
                     breakeven: avg > 0 ? Math.ceil(cost.total / avg - 1e-9) : Infinity, perOrder: avg };

      const partyPartners = people.reduce((a, p) => a + p.intro + p.bonus + p.div, 0);
      const parties = {
        tech: techIncome, partners: partyPartners, other: oth.net, demo,
        coKept: coRev - assigned, costTax: vat + direct + introTax,
        unsplit: gross - (lineTech + coRev + introP + introO + demo + direct + vat),
      };
      out.push({ y, lines, all, gross, vat, direct, coRev, introP, introO, demo, extDemo, lineTech, people, other: oth, parties, hosts,
                 company: { rev: coRev, ops: Y(c.ops), marketing: Y(c.marketing), hardware, contrib, refunds, fromRes, shortfall,
                            expenses, lossIn, pre, bonus, cit, legal, div, reserve: b, lossOut: st.loss, divTech,
                            unallocated: div - divTech - divP },
                 tech });
    }
    return out;
  }

  /* 输入是否自洽：只提示，不阻止。同一句话按年份合并 */
  function warnings(inp, res) {
    const msgs = new Map();
    /* y 可以是年份数字，也可以是「年份（说明）」 */
    const add = (key, y, note) => {
      if (!msgs.has(key)) msgs.set(key, []);
      if (y) { const t = `第 ${y} 年${note ? `（${note}）` : ""}`; if (!msgs.get(key).includes(t)) msgs.get(key).push(t); }
    };
    const N = clampYears(inp.years);
    const sales = inp.partners.filter(p => !p.tech);
    const tr = inp.partners.find(p => p.tech);
    for (let i = 0; i < N; i++) {
      const y = i + 1, on = p => p.tech || y >= joinYear(p);
      const tot = inp.partners.filter(on).reduce((a, p) => a + yv(p.share, i), 0);
      if (Math.abs(tot - 1) > 1e-6) add(`股份合计不是 100%（分红按各人填的比例分，差额列为「未分配」）`, y, `${Math.round(tot * 1000) / 10}%`);
      if (tr && yv(tr.share, i) < yv(inp.company.techShareMin, i) - 1e-9) add("技术方股份低于下限", y);
      SPLIT_ROWS.forEach(r => {
        const s = r.cols.reduce((a, c) => a + yv((inp.split[r.k] || {})[c], i), 0);
        if (Math.abs(s - 1) > 1e-6) add(`分成比例「${r.g} · ${r.n}」加起来不是 100%（差额在「逐年」页单列）`, y, `${Math.round(s * 1000) / 10}%`);
      });
      sales.filter(p => !on(p)).forEach(p => {
        const has = yv((inp.erp.sales || {})[p.id], i) || inp.projects.some(pj => yv((pj.sales || {})[p.id], i)) || yv((inp.geo.sales || {})[p.id], i) || yv((inp.course.hosts || {})[p.id], i);
        if (has) add(`${p.name || "销售合伙人"}第 ${joinYear(p)} 年才加入，之前年份填的单量与期数不算`, null);
      });
    }
    sales.forEach(p => {
      const cnt = a => (Array.isArray(a) ? a.slice(0, N).filter(x => num(x)).length : 0);
      if (cnt((inp.erp.own || {})[p.id]) > 1) add(`${p.name || "销售合伙人"}的自家工厂在不止一年买了 ERP，每勾一年算买一次`, null);
      inp.projects.forEach(pj => {
        if (cnt((pj.own || {})[p.id]) > 1) add(`${p.name || "销售合伙人"}的自家工厂在不止一年买了「${pj.name}」`, null);
        if ((pj.trials || []).includes(p.id) && joinYear(p) > Math.max(1, Math.round(num(pj.launch)) || 1)) add(`「${pj.name}」的试验厂 ${p.name} 在推向市场以后才加入`, null);
      });
    });
    res.filter(r => r.tech.util > 1).forEach(r => add("交付天数超出技术方产能（见「逐年」页的需要员工数）", r.y, `${Math.round(r.tech.util * 100)}%`));
    res.filter(r => r.company.lossOut > 0).forEach(r => add("数字化合作公司亏损，当年不发业绩奖、不分红，亏损结转下一年", r.y));
    return [...msgs].map(([k, ys]) => (ys.length ? `${k}：${ys.join("、")}` : k));
  }

  /* 默认值下的第一年应与讲稿 index-v5.html 经营测算 5 页一致 */
  const DECK = [["总收入", r => r.gross, 209], ["技术方", r => r.parties.tech, 122.11], ["销售合伙人（合计）", r => r.parties.partners, 31.08],
                ["其他销售（合计）", r => r.parties.other, 7.87], ["示范工厂", r => r.parties.demo, 27.54], ["合作公司留作支出", r => r.parties.coKept, 9.6],
                ["ERP 技术方", r => r.lines.erp.tech, 69.86], ["AI 报价助手 合作公司", r => r.lines.proj[0].co, 1.52], ["GEO 介绍人", r => r.lines.geo.introP + r.lines.geo.introO, 2.43],
                ["合作公司收入", r => r.coRev, 20.07], ["业绩奖", r => r.company.bonus, 3.141], ["分红", r => r.company.div, 7.329]];
  function selfCheck() {
    const r = compute(JSON.parse(JSON.stringify(DEFAULTS)))[0];
    return DECK.map(([name, f, want]) => { const got = f(r); return { name, want, got, ok: Math.abs(got - want) < 0.006 }; });
  }

  return { DEFAULTS, SPLIT_ROWS, ROLES, compute, warnings, selfCheck, yv, ev, src, clampYears, joinYear };
})();
