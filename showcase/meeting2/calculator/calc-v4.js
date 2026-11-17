"use strict";
/* 经营测算器第四版 · 计算部分（P1-S10 R04 第 5 步，复制自 calc-v3.js 后改）
   只算数，不碰页面。单位：金额万元、时间天、人数人；比例一律用小数（0.1 即 10%）。
   按年份的数：数组下标 0 即第 1 年；没填的年份沿用前面最近一个填了的年份。「自家工厂今年买」只在勾的那年算，不沿用。
   第三版的变化：
   - 分成表三列：合作公司、技术方、分成方。线下课的分成方是上课工厂，其他各行的分成方都是这一单的介绍人
   - 年维护、学员推荐费也按介绍人分两行，分成方可调
   - 其他销售按人列（可增删、可设第几年加入）；介绍单量精确到人
   - 销售合伙人与其他销售都可以给自家工厂买 ERP、降本增效项目、GEO：分成方那份返给自己作为减免
   - 去掉线上课；技术方成本按岗位算（工资、五险一金、AI），五险一金按缴费基数与单位比例
   - 各项税率给常见默认值；自检时把税率与法定公积金设为 0（讲稿未算税）
   第四版的变化：不再单列示范工厂，线下课的分成方是上课的工厂；实施、变更、维护、讲课、研发都按人天；
   技术方岗位按用户给的月薪与每月 AI 费用，项目经理换成勤务；加场地租金、水电网络物业、办公杂费与按现场人天计的差旅；
   客户 AI 调用费按 DeepSeek 官方价估；学员推荐费改为三方分；AI 报价助手默认实施 30 人天（自检时设为 0）。
   口径见 docs/01-需求摸底/S10-商业化商讨/R04-经营测算器/P1-S10-R4-Pai000协作记录.md 第 2～5 步。 */
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
  const joinYear = p => (p.tech ? 1 : Math.max(1, Math.round(num(p.join)) || 1));

  /* 分成表：每行一类收入；三列都可填，填的是占整单的比例 */
  const SPLIT_ROWS = [
    { k: "erpP", g: "ERP 模块费", n: "销售合伙人介绍" }, { k: "erpO", g: "ERP 模块费", n: "其他销售介绍" },
    { k: "dayP", g: "实施人天与变更单", n: "销售合伙人介绍" }, { k: "dayO", g: "实施人天与变更单", n: "其他销售介绍" },
    { k: "maintP", g: "年维护（ERP 与降本增效项目）", n: "销售合伙人介绍" }, { k: "maintO", g: "年维护（ERP 与降本增效项目）", n: "其他销售介绍" },
    { k: "projP", g: "降本增效项目", n: "销售合伙人介绍" }, { k: "projO", g: "降本增效项目", n: "其他销售介绍" },
    { k: "geoP", g: "宣传与获客（GEO）", n: "销售合伙人介绍" }, { k: "geoO", g: "宣传与获客（GEO）", n: "其他销售介绍" },
    { k: "course", g: "驻厂工程师线下课", n: "扣直接成本以后", demo: true },
    { k: "refP", g: "学员推荐费", n: "销售合伙人介绍的招聘工厂" }, { k: "refO", g: "学员推荐费", n: "其他销售介绍的招聘工厂" },
  ];
  const COLS = [["co", "合作公司"], ["tech", "技术方"], ["party", "分成方"]];
  const s3 = (co, tech, party) => ({ co: [co], tech: [tech], party: [party] });

  const DEFAULTS = {
    years: 3,
    tax: { vat: [0.06], introducerTax: [0.16], divTax: [0.20], cit: [0.05], techCit: [0.05] },
    partners: [
      { id: "tech", tech: true, name: "技术方", share: [0.35] },
      { id: "p1", name: "销售合伙人", join: 1, share: [0.65] },
    ],
    others: [{ id: "o1", name: "其他销售 1", join: 1 }],
    split: {
      erpP: s3(0.10, 0.63, 0.27), erpO: s3(0.165, 0.70, 0.135),
      dayP: s3(0, 0.70, 0.30), dayO: s3(0.15, 0.70, 0.15),
      maintP: s3(0, 1, 0), maintO: s3(0, 1, 0),
      projP: s3(0.10, 0.63, 0.27), projO: s3(0.165, 0.70, 0.135),
      geoP: s3(0.10, 0.63, 0.27), geoO: s3(0.165, 0.70, 0.135),
      course: s3(0.10, 0.45, 0.45),
      refP: s3(0.35, 0.30, 0.35), refO: s3(0.35, 0.35, 0.30),
      trialRatio: [0.5], trialDeduct: [0.05],
    },
    erp: { module: [13], dayRate: [0.15], implDays: [30], changeDays: [0], maintRate: [0.10], maintRetain: [1],
           freeImplP: true, freeImplO: false, sales: { p1: [4, 5, 6], o1: [2, 3, 4] }, own: {} },
    projects: [
      { id: "j1", name: "AI 报价助手", launch: 1, trials: ["p1"], rdDays: 60, hardware: 1,
        price: [4], implDays: [30], maintRate: [0.10], sales: { p1: [3, 5], o1: [2, 3] }, own: {} },
    ],
    geo: { price: [3], renew: [0.8], days: [10], sales: { p1: [2], o1: [2] }, own: {} },
    course: { students: [30], fee: [0.6], directCost: [0.15], teachDays: [10], hosts: { ext: [4] }, referralFee: [0.5], referrals: {} },
    company: { ops: [0.6], marketing: [3], reserveAnnual: [5], reserveCap: [5], refundRate: [0], bonusRate: [0.30],
               legalReserve: [0.10], techShareMin: [0.35] },
    tech: {
      siRate: [0.25], hfRate: [0.12],
      roles: [
        { id: "owner", name: "技术负责人（本人）", count: [1], salary: [0.5], ai: [1], base: [0], days: [120] },
        { id: "fde", name: "驻厂实施工程师（FDE）", count: [0, 1], salary: [2.5], ai: [1], base: [1], days: [200] },
        { id: "dev", name: "开发工程师（Frappe / Python）", count: [0, 0, 1], salary: [1.8], ai: [1.5], base: [1], days: [150] },
        { id: "ops", name: "网络与服务器运维", count: [0], salary: [1.3], ai: [0.8], base: [1], days: [120] },
        { id: "aux", name: "勤务（打扫卫生、接待等杂项）", count: [0], salary: [0.45], ai: [0], base: [1], days: [0] },
      ],
      rent: [1.2, 3.6], utilities: [0.3, 1.2], office: [0.6], travelPerDay: [0.015],
      maintDays: [3], serverCost: [1.5], perServer: [10], aiCost: [0.4],
    },
  };

  const KEYS = ["co", "tech", "introP", "introO", "demo", "direct"];
  function newLine(name) {
    const L = { name, gross: 0, vat: 0, parts: {} };
    KEYS.forEach(k => { L[k] = 0; L.parts[k] = []; });
    return L;
  }
  function put(L, key, label, v) { if (!v) return; L[key] += v; L.parts[key].push([label, v]); }
  const n1 = x => String(Math.round(x * 10) / 10);
  const r2 = x => String(Math.round(x * 100) / 100);
  const pc = x => `${Math.round(x * 1000) / 10}%`;
  const yuan = x => `${Math.round(x * 10000)} 元`;

  function compute(inp) {
    const N = clampYears(inp.years);
    const partners = inp.partners.filter(p => !p.tech), others = inp.others || [];
    const techRow = inp.partners.find(p => p.tech) || { share: [0] };
    const everyone = [
      ...partners.map(p => ({ id: p.id, name: p.name || "销售合伙人", type: "P", src: p })),
      ...others.map(p => ({ id: p.id, name: p.name || "其他销售", type: "O", src: p })),
    ];
    const byId = Object.fromEntries(everyone.map(p => [p.id, p]));
    const st = { erp: {}, proj: inp.projects.map(() => ({ act: {}, pools: null })), geo: {}, reserve: 0, loss: 0 };
    const out = [];

    for (let i = 0; i < N; i++) {
      const y = i + 1, Y = a => yv(a, i);
      const on = p => y >= joinYear(p.src);
      const act = everyone.filter(on);
      const sp = (k, c) => yv(((inp.split || {})[k] || {})[c], i);
      const v = 1 / (1 + Y(inp.tax.vat));
      const rate = Y(inp.erp.dayRate), md = Y(inp.tech.maintDays), ret = Y(inp.erp.maintRetain);
      const lines = { erp: newLine("ERP"), proj: inp.projects.map(p => newLine(p.name || "降本增效项目")),
                      geo: newLine("宣传与获客（GEO）"), course: newLine("驻厂工程师培训班") };
      const per = {};
      everyone.forEach(p => { per[p.id] = { intro: 0, introParts: [], vol: 0, own: 0, ownParts: [], items: [], demo: 0, demoParts: [], trial: 0, trialParts: [] }; });
      const days = { impl: 0, maint: 0, proj: 0, rd: 0, geo: 0, teach: 0 };
      let hardware = 0, extDemo = 0;
      const sale = (L, G) => { L.gross += G; L.vat += G * (1 - v); return G * v; };

      /* 按分成表的一行分一笔钱；who 是介绍人 id，没有介绍人时分成方那份归合作公司 */
      function split(L, k, who, label, G, countVol) {
        const net = sale(L, G);
        put(L, "co", label, net * sp(k, "co"));
        put(L, "tech", label, net * sp(k, "tech"));
        const pa = net * sp(k, "party");
        if (pa) {
          if (who && byId[who]) {
            put(L, byId[who].type === "O" ? "introO" : "introP", label, pa);
            per[who].intro += pa; per[who].introParts.push([`${L.name} · ${label}`, pa]);
          } else put(L, "co", `${label}（没有介绍人，分成方那份归合作公司）`, pa);
        }
        if (who && countVol && per[who]) per[who].vol += G;
      }
      /* 给自家工厂买：分成方那份返给自己，实付 = 市场价 × (合作公司 + 技术方) */
      function ownBuy(L, k, id, label, item, market, countVol) {
        const co = market * sp(k, "co"), tech = market * sp(k, "tech"), paid = co + tech;
        sale(L, paid);
        const tag = `${byId[id].name}自家工厂 · ${label}`;
        put(L, "co", tag, co * v); put(L, "tech", tag, tech * v);
        per[id].own += paid; per[id].ownParts.push([`${L.name} · ${label}`, paid]);
        if (countVol) per[id].vol += paid;
        per[id].items.push({ item, how: `分成方那份 ${pc(sp(k, "party"))} 返给自己`, market, reduce: market - paid, paid });
      }

      /* ---- ERP ---- */
      let L = lines.erp;
      const M = Y(inp.erp.module), impl = Y(inp.erp.implDays), chg = Y(inp.erp.changeDays), mr = Y(inp.erp.maintRate);
      const Dfee = (impl + chg) * rate;
      for (const id of Object.keys(st.erp)) {                  /* 老客户年维护（上一年及以前卖出的） */
        const s = st.erp[id]; if (!byId[id]) continue;
        const ke = s.ext * ret, ko = s.own * ret, T = byId[id].type;
        if (ke) split(L, "maint" + T, id, `${byId[id].name}介绍的老客户年维护 ${n1(ke)} 家 × ${M} 万 × ${pc(mr)}`, ke * M * mr, false);
        if (ko) ownBuy(L, "maint" + T, id, `年维护 ${M} 万 × ${pc(mr)}`, "ERP 年维护", ko * M * mr, false);
        days.maint += (ke + ko) * md; s.ext = ke; s.own = ko;
      }
      const ext = { P: 0, O: 0 };
      for (const p of act) {
        const s = st.erp[p.id] || (st.erp[p.id] = { ext: 0, own: 0 });
        const n = Y((inp.erp.sales || {})[p.id]);
        if (n) {
          const tag = `${p.name}介绍 ${n1(n)} 家`;
          split(L, "erp" + p.type, p.id, `${tag}：模块费 ${M} 万 × ${n1(n)}`, M * n, true);
          if (Dfee) split(L, "day" + p.type, p.id, `${tag}：实施与变更 ${impl + chg} 人天 × ${yuan(rate)} × ${n1(n)}`, Dfee * n, true);
          ext[p.type] += n; s.ext += n; days.impl += n * (impl + chg);
        }
        if (ev((inp.erp.own || {})[p.id], i)) {
          s.own += 1;
          ownBuy(L, "erp" + p.type, p.id, `模块费 ${M} 万`, "ERP 模块费", M, true);
          const D = impl * rate, free = p.type === "P" ? inp.erp.freeImplP : inp.erp.freeImplO;
          if (D) {
            if (free) per[p.id].items.push({ item: "ERP 实施费", how: "免实施费", market: D, reduce: D, paid: 0 });
            else ownBuy(L, "day" + p.type, p.id, `实施 ${impl} 人天 × ${yuan(rate)}`, "ERP 实施费", D, true);
          }
          days.impl += impl;
        }
      }
      const clients = Object.values(st.erp).reduce((a, s) => a + s.ext + s.own, 0);
      const perOrder = { P: M * sp("erpP", "tech") + Dfee * sp("dayP", "tech"), O: M * sp("erpO", "tech") + Dfee * sp("dayO", "tech") };

      /* ---- 降本增效项目 ---- */
      const tRatio = Y(inp.split.trialRatio), tDed = Y(inp.split.trialDeduct);
      inp.projects.forEach((pj, j) => {
        const L = lines.proj[j], S = st.proj[j], launch = Math.max(1, Math.round(num(pj.launch)) || 1), pn = pj.name || "降本增效项目";
        if (y < launch) return;
        const Pp = Y(pj.price), Di = Y(pj.implDays), pmr = Y(pj.maintRate);
        if (S.pools === null) {                                  /* 推向市场那年按当年市场价锁定 */
          S.pools = {};
          (pj.trials || []).forEach(id => {
            if (!byId[id] || byId[id].type !== "P") return;
            S.pools[id] = Pp * tRatio;
            per[id].items.push({ item: pn, how: `试验厂：${pc(tRatio)} 价先用后付，由合作公司从以后每一单里替你抵扣`, market: Pp, reduce: Pp - Pp * tRatio, paid: 0, trial: true });
          });
        }
        if (y === launch) { hardware += num(pj.hardware); days.rd += num(pj.rdDays); }
        for (const id of Object.keys(S.act)) {
          const s = S.act[id]; if (!byId[id]) continue;
          const ke = s.ext * ret, ko = s.own * ret, T = byId[id].type;
          if (ke) split(L, "maint" + T, id, `${byId[id].name}介绍的老客户年维护 ${n1(ke)} 家 × ${Pp} 万 × ${pc(pmr)}`, ke * Pp * pmr, false);
          if (ko) ownBuy(L, "maint" + T, id, `年维护 ${Pp} 万 × ${pc(pmr)}`, `${pn} 年维护`, ko * Pp * pmr, false);
          days.maint += (ke + ko) * md; s.ext = ke; s.own = ko;
        }
        let n = 0;
        for (const p of act) {
          const s = S.act[p.id] || (S.act[p.id] = { ext: 0, own: 0 });
          const c = Y((pj.sales || {})[p.id]);
          if (c) {
            const tag = `${p.name}介绍 ${n1(c)} 家`;
            split(L, "proj" + p.type, p.id, `${tag}：${Pp} 万 × ${n1(c)}`, Pp * c, true);
            if (Di) split(L, "day" + p.type, p.id, `${tag}：实施 ${Di} 人天 × ${yuan(rate)} × ${n1(c)}`, Di * rate * c, true);
            s.ext += c; n += c; days.proj += c * Di;
          }
          if (ev((pj.own || {})[p.id], i)) {
            s.own += 1; n += 1; days.proj += Di;
            ownBuy(L, "proj" + p.type, p.id, `${Pp} 万`, pn, Pp, true);
            if (Di) ownBuy(L, "day" + p.type, p.id, `实施 ${Di} 人天 × ${yuan(rate)}`, `${pn} 实施费`, Di * rate, true);
          }
        }
        /* 替试验厂抵扣：每卖一单（含自家工厂买的）从合作公司拿出整单一定比例付技术方，平分给还没抵清的各家 */
        let rem = n * Pp * tDed, guard = 0;
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
          const who = Object.keys(ded).map(k => `${byId[k].name} ${r2(ded[k])} 万`).join("、");
          const tag = `替试验厂抵扣：${Pp} 万 × ${pc(tDed)} × ${n1(n)} 单${rem > 1e-9 ? "（已抵清的不再抵）" : ""}，${who}`;
          put(L, "co", tag, -total * v); put(L, "tech", tag, total * v);
        }
        Object.keys(S.pools).forEach(k => {
          if (!per[k]) return;
          const d = ded[k] || 0;
          per[k].trial += d;
          if (d > 1e-9 || y === launch) per[k].trialParts.push({ item: pn, ded: d, left: S.pools[k] });
        });
      });

      /* ---- 宣传与获客（GEO 年度服务，按年收费，老客户续费） ---- */
      L = lines.geo;
      const G = Y(inp.geo.price), renew = Y(inp.geo.renew);
      let geoAll = 0;
      for (const p of everyone) {
        st.geo[p.id] = (st.geo[p.id] || 0) * renew + (on(p) ? Y((inp.geo.sales || {})[p.id]) : 0);
        const n = st.geo[p.id];
        if (n) { split(L, "geo" + p.type, p.id, `${p.name}介绍 ${n1(n)} 家（含续费）：${G} 万 × ${n1(n)}`, G * n, true); geoAll += n; }
        if (on(p) && ev((inp.geo.own || {})[p.id], i)) {           /* 按年买，只在勾的那年算 */ ownBuy(L, "geo" + p.type, p.id, `${G} 万`, "GEO 年度服务", G, true); geoAll += 1; }
      }
      days.geo += geoAll * Y(inp.geo.days);

      /* ---- 驻厂工程师培训班（只算线下课） ---- */
      L = lines.course;
      const cs = inp.course, stu = Y(cs.students), fee = Y(cs.fee), dc = Y(cs.directCost);
      let sesAll = 0;
      for (const h of [...act.map(p => p.id), "ext"]) {
        const ses = Y((cs.hosts || {})[h]);
        if (!ses) continue;
        sesAll += ses;
        const Gc = ses * stu * fee, net = sale(L, Gc), direct = Gc * dc, rest = net - direct;
        const hn = h === "ext" ? "其他工厂" : `${byId[h].name}的工厂`;
        const tag = `${hn}：线下课 ${n1(ses)} 期 × ${stu} 人 × ${yuan(fee)}`;
        put(L, "direct", `${tag}，直接成本 ${pc(dc)}`, direct);
        put(L, "co", `${tag}，扣直接成本后 ${pc(sp("course", "co"))}`, rest * sp("course", "co"));
        put(L, "tech", `${tag}，扣直接成本后 ${pc(sp("course", "tech"))}`, rest * sp("course", "tech"));
        const dm = rest * sp("course", "party");
        put(L, "demo", `${tag}，扣直接成本后 ${pc(sp("course", "party"))}`, dm);
        if (h === "ext") extDemo += dm; else { per[h].demo += dm; per[h].demoParts.push([tag, dm]); }
      }
      days.teach += sesAll * Y(cs.teachDays);
      const rfee = Y(cs.referralFee);
      for (const id of [...act.map(p => p.id), "none"]) {
        const c = Y((cs.referrals || {})[id]);
        if (!c || !rfee) continue;
        if (id === "none") split(L, "refP", null, `学员推荐费 ${n1(c)} 人 × ${yuan(rfee)}`, c * rfee, false);
        else split(L, "ref" + byId[id].type, id, `${byId[id].name}介绍的工厂招走学员 ${n1(c)} 人 × ${yuan(rfee)}`, c * rfee, false);
      }

      /* ---- 汇总 ---- */
      const all = [lines.erp, ...lines.proj, lines.geo, lines.course];
      const sum = k => all.reduce((a, l) => a + l[k], 0);
      const gross = sum("gross"), vat = sum("vat"), coRev = sum("co"), introP = sum("introP"), introO = sum("introO");
      const demo = sum("demo"), direct = sum("direct"), lineTech = sum("tech");

      /* ---- 合作公司的账 ---- */
      const c = inp.company;
      const refunds = gross * Y(c.refundRate);
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
        const ab = pre - bonus; cit = ab * Y(inp.tax.cit); legal = (ab - cit) * Y(c.legalReserve); div = ab - cit - legal;
      }

      /* ---- 每个人 ---- */
      const V = everyone.reduce((a, p) => a + per[p.id].vol, 0);
      const iTax = Y(inp.tax.introducerTax), dTax = Y(inp.tax.divTax);
      const people = everyone.map(p => {
        const q = per[p.id], active = on(p), share = p.type === "P" && active ? Y(p.src.share) : 0;
        const bn = V ? bonus * q.vol / V : 0, dv = div * share;
        const tax = (q.intro + bn) * iTax + dv * dTax;
        const income = q.intro + bn + dv - tax;
        return { id: p.id, name: p.name, type: p.type, active, join: joinYear(p.src), share, intro: q.intro, introParts: q.introParts,
                 bonus: bn, div: dv, tax, income, demo: q.demo, demoParts: q.demoParts, own: q.own, ownParts: q.ownParts,
                 items: q.items, trial: q.trial, trialParts: q.trialParts, vol: q.vol,
                 reduce: q.items.reduce((a, x) => a + x.reduce, 0), net: income + q.demo - q.own };
      });
      const divTech = div * Y(techRow.share);
      const divP = people.reduce((a, p) => a + p.div, 0), bonusAll = people.reduce((a, p) => a + p.bonus, 0);
      const pTax = people.reduce((a, p) => a + p.tax, 0);
      const introTax = people.reduce((a, p) => a + (p.intro + p.bonus) * iTax, 0), divTax = pTax - introTax;

      /* ---- 技术方 ---- */
      const t = inp.tech, si = Y(t.siRate) + Y(t.hfRate);
      const roles = (t.roles || []).map(r => {
        const n = Math.max(0, Y(r.count)), s = Y(r.salary), a = Y(r.ai), bs = Y(r.base), d = Y(r.days);
        const wage = 12 * n * s, social = wage * bs * si, ai = 12 * n * a;
        return { id: r.id, name: r.name || "岗位", count: n, salary: s, aiMonthly: a, base: bs, perDays: d, days: n * d, wage, social, ai, total: wage + social + ai };
      });
      const sumR = k => roles.reduce((a, r) => a + r[k], 0);
      const servers = clients > 0 && Y(t.perServer) > 0 ? Math.ceil(clients / Y(t.perServer) - 1e-9) : 0;
      const travelDays = days.impl + days.proj + days.teach;          /* 现场人天：实施、变更、讲课；年维护、研发、GEO 按远程 */
      const cost = { wage: sumR("wage"), social: sumR("social"), ai: sumR("ai"), server: servers * Y(t.serverCost), clientAi: clients * Y(t.aiCost),
                     rent: Y(t.rent), util: Y(t.utilities), office: Y(t.office), travel: travelDays * Y(t.travelPerDay) };
      cost.people = cost.wage + cost.social + cost.ai;
      cost.ops = cost.rent + cost.util + cost.office + cost.travel;
      cost.total = cost.people + cost.server + cost.clientAi + cost.ops;
      const techIncome = lineTech + divTech, profit = techIncome - cost.total;
      const techTax = Math.max(0, profit) * Y(inp.tax.techCit);
      const need = days.impl + days.maint + days.proj + days.rd + days.geo + days.teach;
      const cap = sumR("days"), gap = Math.max(0, need - cap);
      const fde = roles.find(r => r.id === "fde"), fdeDays = fde && fde.perDays > 0 ? fde.perDays : 200;
      const nn = ext.P + ext.O, avg = nn ? (ext.P * perOrder.P + ext.O * perOrder.O) / nn : perOrder.P;
      const tech = { income: techIncome, lineTech, div: divTech, share: Y(techRow.share), roles, cost, profit, tax: techTax, after: profit - techTax,
                     margin: techIncome ? profit / techIncome : 0, heads: sumR("count"), rate, servers, clients,
                     perServer: Y(t.perServer), serverCost: Y(t.serverCost), siRate: Y(t.siRate), hfRate: Y(t.hfRate), travelDays, travelPerDay: Y(t.travelPerDay),
                     days, need, cap, util: cap ? need / cap : Infinity, gap, needFde: Math.ceil(gap / fdeDays - 1e-9), fdeDays,
                     breakeven: avg > 0 ? Math.ceil(cost.total / avg - 1e-9) : Infinity, perOrder: avg };

      const parties = {
        tech: techIncome,
        partners: people.filter(p => p.type === "P").reduce((a, p) => a + p.income, 0),
        other: people.filter(p => p.type === "O").reduce((a, p) => a + p.income, 0),
        demo, coKept: coRev - bonusAll - divTech - divP - cit, costTax: vat + direct + pTax + cit,
        unsplit: gross - (lineTech + coRev + introP + introO + demo + direct + vat),
      };
      out.push({ y, lines, all, gross, vat, direct, coRev, introP, introO, demo, extDemo, lineTech, people, parties,
                 taxes: { vat, introTax, divTax, cit, techTax },
                 own: { paid: people.reduce((a, p) => a + p.own, 0), reduce: people.reduce((a, p) => a + p.reduce, 0), trial: people.reduce((a, p) => a + p.trial, 0) },
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
    const add = (key, y, note) => {
      if (!msgs.has(key)) msgs.set(key, []);
      if (y) { const t = `第 ${y} 年${note ? `（${note}）` : ""}`; if (!msgs.get(key).includes(t)) msgs.get(key).push(t); }
    };
    const N = clampYears(inp.years);
    const ps = inp.partners.filter(p => !p.tech), everyone = [...ps, ...(inp.others || [])];
    const tr = inp.partners.find(p => p.tech);
    const maps = [["ERP", inp.erp.sales], ["ERP 自家工厂", inp.erp.own], ["GEO", inp.geo.sales], ["GEO 自家工厂", inp.geo.own],
                  ["线下课", inp.course.hosts], ["学员推荐费", inp.course.referrals],
                  ...inp.projects.flatMap(pj => [[pj.name, pj.sales], [`${pj.name} 自家工厂`, pj.own]])];
    for (let i = 0; i < N; i++) {
      const y = i + 1, on = p => p.tech || y >= joinYear(p);
      const tot = inp.partners.filter(on).reduce((a, p) => a + yv(p.share, i), 0);
      if (Math.abs(tot - 1) > 1e-6) add("股份合计不是 100%（分红按各人填的比例分，差额列为「未分配」）", y, `${Math.round(tot * 1000) / 10}%`);
      if (tr && yv(tr.share, i) < yv(inp.company.techShareMin, i) - 1e-9) add("技术方股份低于下限", y);
      SPLIT_ROWS.forEach(r => {
        const s = COLS.reduce((a, [c]) => a + yv((inp.split[r.k] || {})[c], i), 0);
        if (Math.abs(s - 1) > 1e-6) add(`分成比例「${r.g} · ${r.n}」加起来不是 100%（差额在「逐年」页单列）`, y, `${Math.round(s * 1000) / 10}%`);
      });
      everyone.filter(p => !on(p)).forEach(p => {
        const hit = maps.filter(([, m]) => m && yv(m[p.id], i)).map(([n]) => n);
        if (hit.length) add(`${p.name || "销售"}第 ${joinYear(p)} 年才加入，之前年份填的不算：${hit.join("、")}`, null);
      });
    }
    everyone.forEach(p => {
      const cnt = a => (Array.isArray(a) ? a.slice(0, N).filter(x => num(x)).length : 0);
      if (cnt((inp.erp.own || {})[p.id]) > 1) add(`${p.name}的自家工厂在不止一年买了 ERP，每勾一年算买一次`, null);
      inp.projects.forEach(pj => { if (cnt((pj.own || {})[p.id]) > 1) add(`${p.name}的自家工厂在不止一年买了「${pj.name}」`, null); });
    });
    ps.forEach(p => inp.projects.forEach(pj => {
      if ((pj.trials || []).includes(p.id) && joinYear(p) > Math.max(1, Math.round(num(pj.launch)) || 1)) add(`「${pj.name}」的试验厂 ${p.name} 在推向市场以后才加入`, null);
    }));
    res.filter(r => r.tech.heads <= 0).forEach(r => add("技术方没有人（岗位人数都是 0）", r.y));
    res.filter(r => r.tech.util > 1).forEach(r => add("交付人天超出技术方产能（见「逐年」页的还差几名 FDE）", r.y, `${Math.round(r.tech.util * 100)}%`));
    res.filter(r => r.company.lossOut > 0).forEach(r => add("合作公司亏损，当年不发业绩奖、不分红，亏损结转下一年", r.y));
    return [...msgs].map(([k, ys]) => (ys.length ? `${k}：${ys.join("、")}` : k));
  }

  /* 默认值下的第一年应与讲稿 index-v5.html 经营测算 5 页一致；讲稿未算税与法定公积金、AI 报价助手不含实施，自检时都设为 0 */
  const DECK = [["总收入", r => r.gross, 209], ["技术方", r => r.parties.tech, 122.11], ["销售合伙人（合计）", r => r.parties.partners, 31.08],
                ["其他销售（合计）", r => r.parties.other, 7.87], ["上课工厂", r => r.parties.demo, 27.54], ["合作公司留作支出", r => r.parties.coKept, 9.6],
                ["ERP 技术方", r => r.lines.erp.tech, 69.86], ["AI 报价助手 合作公司", r => r.lines.proj[0].co, 1.52], ["GEO 介绍人", r => r.lines.geo.introP + r.lines.geo.introO, 2.43],
                ["合作公司收入", r => r.coRev, 20.07], ["业绩奖", r => r.company.bonus, 3.141], ["分红", r => r.company.div, 7.329]];
  function deckInput() {
    const d = JSON.parse(JSON.stringify(DEFAULTS));
    Object.keys(d.tax).forEach(k => { d.tax[k] = [0]; });
    d.company.legalReserve = [0];
    d.projects.forEach(p => { p.implDays = [0]; });
    return d;
  }
  function selfCheck() {
    const r = compute(deckInput())[0];
    return DECK.map(([name, f, want]) => { const got = f(r); return { name, want, got, ok: Math.abs(got - want) < 0.006 }; });
  }

  return { DEFAULTS, SPLIT_ROWS, COLS, compute, warnings, selfCheck, deckInput, yv, ev, src, clampYears, joinYear };
})();
