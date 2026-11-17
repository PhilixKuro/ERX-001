"use strict";
/* 经营测算器第十二版 · 计算部分（P1-S10 R04 第 13 步，复制自 calc-v11.js 后改）
   第十二版的变化：合作公司企业所得税不再把提取的风险准备金当费用扣，实际用准备金付的退款才扣（citBase）；
   法定公积金累计到注册资本 × 上限比例（默认 3 万 × 50%）后不再提（legalSum）；降本增效项目自家工厂买也按开关免现场实施费（与 ERP 同一个开关）。
   以下为第十一版注释（P1-S10 R04 第 12 步，复制自 calc-v10.js 后改）
   第十一版的变化：可分配利润（交完所得税、提完法定公积金后余下的）只按一定比例分红（divRate，默认 100%），其余留作公司现金（retain），逐年累计（cash）。
   以下为第十版注释（P1-S10 R04 第 11 步，复制自 calc-v9.js 后改）
   第十版的变化：每项业务记下自家工厂买的含税金额（L.own），供概览「钱从哪来」；水电、网络与物业默认 2.5 万。
   以下为第九版注释（P1-S10 R04 第 10 步，复制自 calc-v8.js 后改）
   第九版的变化：增值税附加（按增值税额的比例，默认 6%）与增值税一起在分钱之前扣，每项业务记 vatB（增值税）、sur（附加）、vat（两项合计）；
   上课工厂分得的那份交企业所得税（hostCit）；技术方从合作公司拿的分红免企业所得税；
   每项业务记下各方在这项业务上的税（tx：合作公司按收入占比分、技术方扣成本时按扣成本后的利润分、不扣时按分成占比分、每个人与上课工厂逐笔算），供页面切换税前、税后。
   以下为第八版注释（P1-S10 R04 第 9 步，复制自 calc-v7.js 后改）
   第八版的变化：ERP 与降本增效项目每家的人天改为现场实施（计费、算销售分成、算差旅）、内部开发（不计费、不算分成、不算差旅，只算技术方工作量）、
   变更单（计费、算分成、远程处理）三项；实施费 ＝（现场实施 ＋ 变更单）× 人天价。
   技术方成本改用标准成本法：每人天成本 ＝（人员 ＋ 场地 ＋ 水电网络物业 ＋ 软件 ＋ 办公杂费）÷ 可交付人天，一年一个数；
   每项业务的成本 ＝ 分到的人天 × 每人天成本 ＋ 它自己的现场人天 × 差旅单价，服务器只归 ERP；与实际成本之差为产能差异（variance）。
   每个人记下自家工厂买的业务额（volOwn），合作公司记下全部业务额（volAll），供业绩奖悬停写明算法；每个人天任务记下需要人天的来由（how）。
   以下为第七版注释（P1-S10 R04 第 8 步，复制自 calc-v6.js 后改）
   第七版的变化：人天分现场与远程（ERP、降本增效项目各有现场实施、远程实施、变更单三项；年维护、GEO 各有现场、远程两项；研发远程，讲课现场），
   差旅只算现场人天；默认谁来做：讲课只能本人，现场先给本人、远程先给其他岗位（byOwner、byRest）；
   风险准备金每年提合作公司收入的一定比例，上限为上一年总收入的一定比例且不低于最低额；
   公司运营四项（场地、水电网络物业、软件、办公杂费）从第一次请人那年起算；场地默认 1.5 万、水电网络物业 2.52 万、讲课 17 人天。
   以下为第六版注释（P1-S10 R04 第 7 步，复制自 calc-v5.js 后改）
   第六版的变化：人天按项目记账（tasks），每个项目每年可分配人天（alloc，没填按需要）；线下课讲课只能由本人上，本人剩下的人天与其他岗位一起给其他项目；
   技术方成本按分配到各项业务的人天分摊（costLine），没分出去的算闲置；默认岗位只有本人（300 人天）与 FDE（195 人天）；
   去掉每家客户 AI 调用费；加软件费用；水电与网络每年 2.28 万；AI 报价助手默认销售合伙人 1 当试验厂、不再自家工厂买。
   以下为第五版注释（P1-S10 R04 第 6 步，复制自 calc-v4.js 后改）
   第五版的变化：每项业务按人记下分到每个人的钱（L.pp），供图表按人、按项目显示组成；每个人带一个颜色序号 c；
   默认值改为：只有销售合伙人 1、没有其他销售；ERP 每家变更 5 人天、第 1～3 年介绍 3／4／5 家且自家工厂第 1 年买；
   AI 报价助手市场价 3 万、自家工厂第 1 年买、默认不设试验厂；GEO 每年新签 1 家；线下课 2／4／6 期都在销售合伙人 1 的工厂；
   每家每年维护 6 人天、每台服务器放 3 家、每家 AI 调用 0.5 万。自检改为单独搭讲稿的场景（deckInput），不再从默认值改。
   以下为第四版注释（P1-S10 R04 第 5 步，复制自 calc-v3.js 后改）
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
    alloc: {},
    tax: { vat: [0.06], vatSur: [0.06], introducerTax: [0.16], divTax: [0.20], cit: [0.05], techCit: [0.05], hostCit: [0.05] },
    partners: [
      { id: "tech", tech: true, name: "技术方", share: [0.35] },
      { id: "p1", name: "销售合伙人 1", join: 1, share: [0.65], c: 0 },
    ],
    others: [],
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
    erp: { module: [13], dayRate: [0.15], onsiteDays: [10], devDays: [30], changeDays: [10], maintRate: [0.10], maintRetain: [1],
           freeImplP: true, freeImplO: false, sales: { p1: [3, 4, 5] }, own: { p1: [1] } },
    projects: [
      { id: "j1", name: "AI 报价助手", launch: 1, trials: ["p1"], rdDays: 60, hardware: 1,
        price: [3], onsiteDays: [5], devDays: [5], changeDays: [5], maintRate: [0.10], sales: { p1: [3, 5] }, own: {} },
    ],
    geo: { price: [3], renew: [0.8], onsiteDays: [0], remoteDays: [10], sales: { p1: [1] }, own: {} },
    course: { students: [30], fee: [0.6], directCost: [0.15], teachDays: [17], hosts: { p1: [2, 4, 6] }, referralFee: [0.5], referrals: {} },
    company: { ops: [0.6], marketing: [3], reserveRate: [0.20], reserveCapRate: [0.03], reserveMin: [5], refundRate: [0], bonusRate: [0.30],
               legalReserve: [0.10], capital: [3], legalCapRate: [0.5], divRate: [1], techShareMin: [0.35] },
    tech: {
      siRate: [0.25], hfRate: [0.12],
      roles: [
        { id: "owner", name: "技术负责人（本人）", count: [1], salary: [0.5], ai: [1], base: [0], days: [300] },
        { id: "fde", name: "驻厂实施工程师（FDE）", count: [0, 1], salary: [2.5], ai: [1], base: [1], days: [195] },
      ],
      rent: [1.5], utilities: [2.5], software: [1], office: [0.6], travelPerDay: [0.015],
      maintOnsite: [0], maintRemote: [6], serverCost: [1.5], perServer: [3],
    },
  };

  const KEYS = ["co", "tech", "introP", "introO", "demo", "direct"];
  function newLine(name) {
    const L = { name, gross: 0, own: 0, vat: 0, vatB: 0, sur: 0, parts: {}, pp: {}, ppParts: {}, ppTax: {}, ext: 0, extParts: [], extTax: 0 };
    KEYS.forEach(k => { L[k] = 0; L.parts[k] = []; });
    return L;
  }
  function put(L, key, label, v) { if (!v) return; L[key] += v; L.parts[key].push([label, v]); }
  /* 这项业务分到某个人的钱（介绍费，或在他的工厂上线下课分得的那份） */
  function putP(L, id, label, v, tr) { if (!v) return; L.pp[id] = (L.pp[id] || 0) + v; L.ppTax[id] = (L.ppTax[id] || 0) + v * tr; (L.ppParts[id] || (L.ppParts[id] = [])).push([label, v]); }
  const n1 = x => String(Math.round(x * 10) / 10);
  const r2 = x => String(Math.round(x * 100) / 100);
  const pc = x => `${Math.round(x * 1000) / 10}%`;
  const yuan = x => `${Math.round(x * 10000)} 元`;

  function compute(inp) {
    const N = clampYears(inp.years);
    const partners = inp.partners.filter(p => !p.tech), others = inp.others || [];
    const techRow = inp.partners.find(p => p.tech) || { share: [0] };
    const everyone = [
      ...partners.map(p => ({ id: p.id, name: p.name || "销售合伙人", type: "P", c: p.c, src: p })),
      ...others.map(p => ({ id: p.id, name: p.name || "其他销售", type: "O", c: p.c, src: p })),
    ];
    const byId = Object.fromEntries(everyone.map(p => [p.id, p]));
    const st = { erp: {}, proj: inp.projects.map(() => ({ act: {}, pools: null })), geo: {}, reserve: 0, loss: 0, prevGross: 0, cash: 0, legalSum: 0 };
    const out = [];
    /* 公司运营四项从第一次请人（本人以外的岗位人数大于 0）那年起算 */
    const firstHire = (() => { for (let k = 0; k < N; k++) if ((inp.tech.roles || []).some(r => r.id !== "owner" && yv(r.count, k) > 0)) return k; return Infinity; })();

    for (let i = 0; i < N; i++) {
      const y = i + 1, Y = a => yv(a, i);
      const on = p => y >= joinYear(p.src);
      const act = everyone.filter(on);
      const sp = (k, c) => yv(((inp.split || {})[k] || {})[c], i);
      /* 价格视为含税：增值税 ＝ 含税价 × 税率 ÷（1 ＋ 税率），附加 ＝ 增值税 × 附加比例；两项在分钱之前扣，v 是扣完剩下的比例 */
      const vr = Y(inp.tax.vat), sr = Y(inp.tax.vatSur), v = 1 - vr * (1 + sr) / (1 + vr);
      const iTax = Y(inp.tax.introducerTax), dTax = Y(inp.tax.divTax), hTax = Y(inp.tax.hostCit);
      const rate = Y(inp.erp.dayRate), mOn = Y(inp.tech.maintOnsite), mRem = Y(inp.tech.maintRemote), md = mOn + mRem, ret = Y(inp.erp.maintRetain);
      const lines = { erp: newLine("ERP"), proj: inp.projects.map(p => newLine(p.name || "降本增效项目")),
                      geo: newLine("宣传与获客（GEO）"), course: newLine("驻厂工程师培训班") };
      const per = {};
      everyone.forEach(p => { per[p.id] = { byLine: {}, intro: 0, introParts: [], vol: 0, volOwn: 0, own: 0, ownParts: [], items: [], demo: 0, demoParts: [], trial: 0, trialParts: [] }; });
      const days = { impl: 0, maint: 0, proj: 0, rd: 0, geo: 0, teach: 0, onsite: 0 };
      const tasks = {}, task = (key, line, name, d, mode, how) => { if (!(d > 0)) return; const t = tasks[key] || (tasks[key] = { key, line, name, mode, need: 0, how: [] }); t.need += d; if (how) t.how.push(how); };
      /* 年维护：k 家老客户，分现场、远程两项 */
      const mt = (key, line, name, k) => {
        task(`${key}:mon`, line, `${name} 现场维护`, k * mOn, "on", `老客户 ${n1(k)} 家 × ${mOn} 人天`);
        task(`${key}:mrem`, line, `${name} 远程维护`, k * mRem, "rem", `老客户 ${n1(k)} 家 × ${mRem} 人天`); days.onsite += k * mOn;
      };
      let hardware = 0, extDemo = 0;
      const sale = (L, G) => { const vb = G * vr / (1 + vr), su = vb * sr; L.gross += G; L.vatB += vb; L.sur += su; L.vat += vb + su; return G - vb - su; };

      /* 按分成表的一行分一笔钱；who 是介绍人 id，没有介绍人时分成方那份归合作公司 */
      function split(L, k, who, label, G, countVol) {
        const net = sale(L, G);
        put(L, "co", label, net * sp(k, "co"));
        put(L, "tech", label, net * sp(k, "tech"));
        const pa = net * sp(k, "party");
        if (pa) {
          if (who && byId[who]) {
            put(L, byId[who].type === "O" ? "introO" : "introP", label, pa);
            putP(L, who, label, pa, iTax); per[who].byLine[L.name] = (per[who].byLine[L.name] || 0) + pa;
            per[who].intro += pa; per[who].introParts.push([`${L.name} · ${label}`, pa]);
          } else put(L, "co", `${label}（没有介绍人，分成方那份归合作公司）`, pa);
        }
        if (who && countVol && per[who]) per[who].vol += G;
      }
      /* 给自家工厂买：分成方那份返给自己，实付 = 市场价 × (合作公司 + 技术方) */
      function ownBuy(L, k, id, label, item, market, countVol) {
        const co = market * sp(k, "co"), tech = market * sp(k, "tech"), paid = co + tech;
        sale(L, paid); L.own += paid;
        const tag = `${byId[id].name}自家工厂 · ${label}`;
        put(L, "co", tag, co * v); put(L, "tech", tag, tech * v);
        per[id].own += paid; per[id].ownParts.push([`${L.name} · ${label}`, paid]);
        if (countVol) { per[id].vol += paid; per[id].volOwn += paid; }
        per[id].items.push({ item, how: `分成方那份 ${pc(sp(k, "party"))} 返给自己`, market, reduce: market - paid, paid });
      }

      /* ---- ERP ---- */
      let L = lines.erp;
      const M = Y(inp.erp.module), eOn = Y(inp.erp.onsiteDays), eDev = Y(inp.erp.devDays), chg = Y(inp.erp.changeDays), mr = Y(inp.erp.maintRate);
      const Dfee = (eOn + chg) * rate;            /* 计费：现场实施与变更单；内部开发不计费、不算分成 */
      for (const id of Object.keys(st.erp)) {                  /* 老客户年维护（上一年及以前卖出的） */
        const s = st.erp[id]; if (!byId[id]) continue;
        const ke = s.ext * ret, ko = s.own * ret, T = byId[id].type;
        if (ke) split(L, "maint" + T, id, `${byId[id].name}介绍的老客户年维护 ${n1(ke)} 家 × ${M} 万 × ${pc(mr)}`, ke * M * mr, false);
        if (ko) ownBuy(L, "maint" + T, id, `年维护 ${M} 万 × ${pc(mr)}`, "ERP 年维护", ko * M * mr, false);
        days.maint += (ke + ko) * md; mt("erp", "ERP", "ERP", ke + ko); s.ext = ke; s.own = ko;
      }
      const ext = { P: 0, O: 0 };
      for (const p of act) {
        const s = st.erp[p.id] || (st.erp[p.id] = { ext: 0, own: 0 });
        const n = Y((inp.erp.sales || {})[p.id]);
        if (n) {
          const tag = `${p.name}介绍 ${n1(n)} 家`;
          split(L, "erp" + p.type, p.id, `${tag}：模块费 ${M} 万 × ${n1(n)}`, M * n, true);
          if (Dfee) split(L, "day" + p.type, p.id, `${tag}：现场实施 ${eOn} ＋ 变更单 ${chg} 人天 × ${yuan(rate)} × ${n1(n)}`, Dfee * n, true);
          ext[p.type] += n; s.ext += n; days.impl += n * (eOn + eDev + chg); days.onsite += n * eOn;
          const wt = `${p.name}介绍 ${n1(n)} 家 × `;
          task("erp:on", "ERP", "ERP 现场实施", n * eOn, "on", `${wt}${eOn} 人天`);
          task("erp:dev", "ERP", "ERP 内部开发", n * eDev, "rem", `${wt}${eDev} 人天`);
          task("erp:chg", "ERP", "ERP 变更单（远程）", n * chg, "rem", `${wt}${chg} 人天`);
        }
        if (ev((inp.erp.own || {})[p.id], i)) {
          s.own += 1;
          ownBuy(L, "erp" + p.type, p.id, `模块费 ${M} 万`, "ERP 模块费", M, true);
          const D = eOn * rate, free = p.type === "P" ? inp.erp.freeImplP : inp.erp.freeImplO;
          if (D) {
            if (free) per[p.id].items.push({ item: "ERP 现场实施费", how: "免现场实施费", market: D, reduce: D, paid: 0 });
            else ownBuy(L, "day" + p.type, p.id, `现场实施 ${eOn} 人天 × ${yuan(rate)}`, "ERP 现场实施费", D, true);
          }
          days.impl += eOn + eDev; days.onsite += eOn;
          task("erp:on", "ERP", "ERP 现场实施", eOn, "on", `${p.name}自家工厂 1 家 × ${eOn} 人天`);
          task("erp:dev", "ERP", "ERP 内部开发", eDev, "rem", `${p.name}自家工厂 1 家 × ${eDev} 人天`);
        }
      }
      const clients = Object.values(st.erp).reduce((a, s) => a + s.ext + s.own, 0);
      const perOrder = { P: M * sp("erpP", "tech") + Dfee * sp("dayP", "tech"), O: M * sp("erpO", "tech") + Dfee * sp("dayO", "tech") };

      /* ---- 降本增效项目 ---- */
      const tRatio = Y(inp.split.trialRatio), tDed = Y(inp.split.trialDeduct);
      inp.projects.forEach((pj, j) => {
        const L = lines.proj[j], S = st.proj[j], launch = Math.max(1, Math.round(num(pj.launch)) || 1), pn = pj.name || "降本增效项目";
        if (y < launch) return;
        const Pp = Y(pj.price), pOn = Y(pj.onsiteDays), pDev = Y(pj.devDays), pChg = Y(pj.changeDays), pFee = pOn + pChg, pmr = Y(pj.maintRate);
        if (S.pools === null) {                                  /* 推向市场那年按当年市场价锁定 */
          S.pools = {};
          (pj.trials || []).forEach(id => {
            if (!byId[id] || byId[id].type !== "P") return;
            S.pools[id] = Pp * tRatio;
            per[id].items.push({ item: pn, how: `试验厂：${pc(tRatio)} 价先用后付，由合作公司从以后每一单里替你抵扣`, market: Pp, reduce: Pp - Pp * tRatio, paid: 0, trial: true });
          });
        }
        if (y === launch) { hardware += num(pj.hardware); days.rd += num(pj.rdDays); task(`proj:${pj.id}:rd`, L.name, `${pn} 研发`, num(pj.rdDays), "rem", `第 ${y} 年推向市场，研发 ${num(pj.rdDays)} 人天`); }
        for (const id of Object.keys(S.act)) {
          const s = S.act[id]; if (!byId[id]) continue;
          const ke = s.ext * ret, ko = s.own * ret, T = byId[id].type;
          if (ke) split(L, "maint" + T, id, `${byId[id].name}介绍的老客户年维护 ${n1(ke)} 家 × ${Pp} 万 × ${pc(pmr)}`, ke * Pp * pmr, false);
          if (ko) ownBuy(L, "maint" + T, id, `年维护 ${Pp} 万 × ${pc(pmr)}`, `${pn} 年维护`, ko * Pp * pmr, false);
          days.maint += (ke + ko) * md; mt(`proj:${pj.id}`, L.name, pn, ke + ko); s.ext = ke; s.own = ko;
        }
        let n = 0;
        for (const p of act) {
          const s = S.act[p.id] || (S.act[p.id] = { ext: 0, own: 0 });
          const c = Y((pj.sales || {})[p.id]);
          if (c) {
            const tag = `${p.name}介绍 ${n1(c)} 家`;
            split(L, "proj" + p.type, p.id, `${tag}：${Pp} 万 × ${n1(c)}`, Pp * c, true);
            if (pFee) split(L, "day" + p.type, p.id, `${tag}：现场实施 ${pOn} ＋ 变更单 ${pChg} 人天 × ${yuan(rate)} × ${n1(c)}`, pFee * rate * c, true);
            s.ext += c; n += c; days.proj += c * (pOn + pDev + pChg); days.onsite += c * pOn;
            const wt = `${p.name}介绍 ${n1(c)} 家 × `;
            task(`proj:${pj.id}:on`, L.name, `${pn} 现场实施`, c * pOn, "on", `${wt}${pOn} 人天`);
            task(`proj:${pj.id}:dev`, L.name, `${pn} 内部开发`, c * pDev, "rem", `${wt}${pDev} 人天`);
            task(`proj:${pj.id}:chg`, L.name, `${pn} 变更单（远程）`, c * pChg, "rem", `${wt}${pChg} 人天`);
          }
          if (ev((pj.own || {})[p.id], i)) {
            s.own += 1; n += 1; days.proj += pOn + pDev; days.onsite += pOn;
            task(`proj:${pj.id}:on`, L.name, `${pn} 现场实施`, pOn, "on", `${p.name}自家工厂 1 家 × ${pOn} 人天`);
            task(`proj:${pj.id}:dev`, L.name, `${pn} 内部开发`, pDev, "rem", `${p.name}自家工厂 1 家 × ${pDev} 人天`);
            ownBuy(L, "proj" + p.type, p.id, `${Pp} 万`, pn, Pp, true);
            const free = p.type === "P" ? inp.erp.freeImplP : inp.erp.freeImplO;   /* 与 ERP 同一个开关 */
            if (pOn && free) per[p.id].items.push({ item: `${pn} 现场实施费`, how: "免现场实施费", market: pOn * rate, reduce: pOn * rate, paid: 0 });
            else if (pOn) ownBuy(L, "day" + p.type, p.id, `现场实施 ${pOn} 人天 × ${yuan(rate)}`, `${pn} 现场实施费`, pOn * rate, true);
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
      const gOn = Y(inp.geo.onsiteDays), gRem = Y(inp.geo.remoteDays); days.geo += geoAll * (gOn + gRem); days.onsite += geoAll * gOn;
      task("geo:on", lines.geo.name, "GEO 现场服务", geoAll * gOn, "on", `在服务的客户 ${n1(geoAll)} 家 × ${gOn} 人天`);
      task("geo:rem", lines.geo.name, "GEO 远程服务", geoAll * gRem, "rem", `在服务的客户 ${n1(geoAll)} 家 × ${gRem} 人天`);

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
        if (h === "ext") { extDemo += dm; L.ext += dm; L.extTax += dm * hTax; L.extParts.push([tag, dm]); }
        else { per[h].demo += dm; per[h].demoParts.push([tag, dm]); putP(L, h, `${tag}（上课工厂分成）`, dm, hTax); }
      }
      days.teach += sesAll * Y(cs.teachDays); days.onsite += sesAll * Y(cs.teachDays); task("course", lines.course.name, "线下课讲课（现场，只能由本人上）", sesAll * Y(cs.teachDays), "teach", `${n1(sesAll)} 期 × 每期 ${Y(cs.teachDays)} 人天`);
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
      const gross = sum("gross"), vat = sum("vat"), vatB = sum("vatB"), sur = sum("sur"), coRev = sum("co"), introP = sum("introP"), introO = sum("introO");
      const demo = sum("demo"), direct = sum("direct"), lineTech = sum("tech");

      /* ---- 合作公司的账 ---- */
      const c = inp.company;
      const refunds = gross * Y(c.refundRate);
      let b = st.reserve; const resPrev = b;
      const fromRes = Math.min(b, refunds); b -= fromRes;
      const shortfall = refunds - fromRes;
      /* 每年提合作公司收入的一定比例，攒到上限为止；上限 ＝ 上一年总收入 × 比例，不低于最低额 */
      const resCap = Math.max(Y(c.reserveMin), st.prevGross * Y(c.reserveCapRate));
      const contrib = Math.min(Math.max(0, coRev) * Y(c.reserveRate), Math.max(0, resCap - b)); b += contrib; st.reserve = b; st.prevGross = gross;
      const expenses = Y(c.ops) + Y(c.marketing) + hardware + contrib + shortfall;
      const lossIn = st.loss;
      let pre = coRev - expenses - lossIn, bonus = 0, cit = 0, legal = 0, div = 0, retain = 0;
      /* 企业所得税：自己提的风险准备金不能税前扣，实际用准备金付出的退款才扣；业绩奖（劳务报酬，代扣个税）税前扣 */
      const taxAdj = contrib - fromRes, legalRoom = Math.max(0, Y(c.capital) * Y(c.legalCapRate) - st.legalSum);
      let citBase = 0;
      if (pre < 0) { citBase = Math.max(0, pre + taxAdj); cit = citBase * Y(inp.tax.cit); st.loss = -pre + cit; }
      else {
        st.loss = 0; bonus = pre * Y(c.bonusRate);
        const ab = pre - bonus; citBase = Math.max(0, ab + taxAdj); cit = citBase * Y(inp.tax.cit);
        legal = Math.min(Math.max(0, ab - cit) * Y(c.legalReserve), legalRoom);   /* 累计到注册资本 × 上限比例后不再提 */
        if (ab - cit < 0) st.loss = cit - ab;   /* 准备金不能税前扣，交税后反而亏了：亏的部分结转 */
        const dist = Math.max(0, ab - cit - legal); div = dist * Y(c.divRate); retain = dist - div;   /* 可分配利润只按比例分红，其余留作公司现金 */
      }
      st.cash += retain; st.legalSum += legal;

      /* ---- 每个人 ---- */
      const V = everyone.reduce((a, p) => a + per[p.id].vol, 0);
      const people = everyone.map(p => {
        const q = per[p.id], active = on(p), share = p.type === "P" && active ? Y(p.src.share) : 0;
        const bn = V ? bonus * q.vol / V : 0, dv = div * share;
        const tax = (q.intro + bn) * iTax + dv * dTax;
        const income = q.intro + bn + dv - tax, demoTax = q.demo * hTax;
        return { id: p.id, name: p.name, type: p.type, c: p.c, active, join: joinYear(p.src), share, byLine: q.byLine, intro: q.intro, introParts: q.introParts,
                 bonus: bn, div: dv, tax, income, demo: q.demo, demoTax, after: income + q.demo - demoTax, demoParts: q.demoParts, own: q.own, ownParts: q.ownParts,
                 items: q.items, trial: q.trial, trialParts: q.trialParts, vol: q.vol, volOwn: q.volOwn,
                 reduce: q.items.reduce((a, x) => a + x.reduce, 0), net: income + q.demo - demoTax - q.own };
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
      const travelDays = days.onsite;          /* 差旅只算现场人天：现场实施、现场维护、现场 GEO 服务、线下课讲课 */
      const opsOn = i >= firstHire ? 1 : 0;
      const cost = { wage: sumR("wage"), social: sumR("social"), ai: sumR("ai"), server: servers * Y(t.serverCost),
                     rent: opsOn * Y(t.rent), util: opsOn * Y(t.utilities), software: opsOn * Y(t.software), office: opsOn * Y(t.office), travel: travelDays * Y(t.travelPerDay) };
      cost.people = cost.wage + cost.social + cost.ai;
      cost.ops = cost.rent + cost.util + cost.software + cost.office + cost.travel;
      cost.total = cost.people + cost.server + cost.ops;
      const techIncome = lineTech + divTech, profit = techIncome - cost.total;
      /* 居民企业之间直接投资的分红免企业所得税：技术方只按扣成本后的业务利润交 */
      const taxable = profit - divTech, tcr = Y(inp.tax.techCit), techTax = Math.max(0, taxable) * tcr;
      /* ---- 人天：线下课讲课只能由本人上；本人剩下的与其他岗位的人天一起给其他项目 ---- */
      const ownerR = roles.find(r => r.id === "owner"), ownerCap = ownerR ? ownerR.days : 0, restCap = sumR("days") - ownerCap;
      const tl = Object.values(tasks).map(x => {
        const a = (inp.alloc || {})[x.key], k = Array.isArray(a) ? src(a, i) : -1, alloc = k >= 0 ? Math.max(0, yv(a, i)) : x.need;
        return { ...x, alloc, set: k >= 0, short: Math.max(0, x.need - alloc) };
      });
      const sumT = (arr, f) => arr.reduce((s, x) => s + x[f], 0);
      const teachT = tl.filter(x => x.key === "course"), otherT = tl.filter(x => x.key !== "course");
      const teachNeed = sumT(teachT, "need"), teachAlloc = sumT(teachT, "alloc"), otherNeed = sumT(otherT, "need"), otherAlloc = sumT(otherT, "alloc");
      const generalCap = Math.max(0, ownerCap - teachAlloc) + restCap, remaining = generalCap - otherAlloc;
      const cap = ownerCap + restCap, need = teachNeed + otherNeed, allocAll = teachAlloc + otherAlloc;
      const gap = Math.max(0, otherNeed - (Math.max(0, ownerCap - teachNeed) + restCap));
      const fde = roles.find(r => r.id === "fde"), fdeDays = fde && fde.perDays > 0 ? fde.perDays : 195;
      /* 默认谁来做：讲课只能本人；现场人天先给本人剩下的，不够再给其他岗位；远程人天先给其他岗位，不够再用本人剩下的 */
      let oLeft = ownerCap, rLeft = restCap;
      const give = (x, order) => {
        x.byOwner = 0; x.byRest = 0; let left = x.alloc;
        for (const w of order) { const a = Math.max(0, Math.min(left, w === "o" ? oLeft : rLeft)); if (w === "o") { oLeft -= a; x.byOwner += a; } else { rLeft -= a; x.byRest += a; } left -= a; }
        x.unfilled = left;
      };
      tl.filter(x => x.mode === "teach").forEach(x => give(x, ["o"]));
      tl.filter(x => x.mode === "on").forEach(x => give(x, ["o", "r"]));
      tl.filter(x => x.mode !== "teach" && x.mode !== "on").forEach(x => give(x, ["r", "o"]));
      /* 技术方成本按分配到各项业务的人天分摊；没分出去的人天算闲置，成本单列 */
      /* 第八版改为标准成本法：每人天成本 ＝（人员 ＋ 场地 ＋ 水电网络物业 ＋ 软件 ＋ 办公杂费）÷ 可交付人天，一年一个数，不随各项目的人天变；
         每项业务的成本 ＝ 分到的人天 × 每人天成本 ＋ 它自己的现场人天 × 差旅单价；服务器只归 ERP；
         当年实际成本与各项业务合计之差为产能差异：有闲置人天时为正，人手不够时为负 */
      const pool = cost.people + cost.rent + cost.util + cost.software + cost.office, perDay = cap > 0 ? pool / cap : 0, tpd = Y(t.travelPerDay), costLine = {};
      tl.forEach(x => {
        x.labor = x.alloc * perDay; x.travel = x.mode === "on" || x.mode === "teach" ? x.need * tpd : 0; x.cost = x.labor + x.travel;
        costLine[x.line] = (costLine[x.line] || 0) + x.cost;
      });
      if (cost.server) costLine.ERP = (costLine.ERP || 0) + cost.server;
      const variance = cost.total - Object.values(costLine).reduce((s, v2) => s + v2, 0);
      /* 各方在每项业务上的税：合作公司所得税按这项业务占合作公司收入的比例分；技术方所得税扣成本时按这项业务扣成本后的利润分（亏的分到负数，产能差异同理），
         不扣成本时按技术方在这项业务分得的比例分；每个人、上课工厂逐笔算（putP 时已记）。各项加起来等于当年的税 */
      const hostTax = people.reduce((a, p) => a + p.demoTax, 0) + extDemo * hTax;
      all.forEach(l => {
        l.tx = { co: coRev > 1e-9 ? cit * l.co / coRev : 0, techNet: taxable > 0 ? (l.tech - (costLine[l.name] || 0)) * tcr : 0,
                 techGross: lineTech > 1e-9 ? techTax * l.tech / lineTech : 0, pp: l.ppTax, ext: l.extTax };
        l.tx.ppAll = Object.values(l.ppTax).reduce((a, x) => a + x, 0);
      });
      const varTax = taxable > 0 ? -variance * tcr : 0;
      const nn = ext.P + ext.O, avg = nn ? (ext.P * perOrder.P + ext.O * perOrder.O) / nn : perOrder.P;
      const tech = { income: techIncome, lineTech, div: divTech, share: Y(techRow.share), roles, cost, profit, tax: techTax, after: profit - techTax,
                     margin: techIncome ? profit / techIncome : 0, heads: sumR("count"), rate, servers, clients,
                     perServer: Y(t.perServer), serverCost: Y(t.serverCost), siRate: Y(t.siRate), hfRate: Y(t.hfRate), travelDays, travelPerDay: Y(t.travelPerDay),
                     days, tasks: tl, ownerCap, restCap, teachNeed, teachAlloc, teachOver: Math.max(0, teachAlloc - ownerCap), teachShort: Math.max(0, teachNeed - ownerCap),
                     otherNeed, otherAlloc, generalCap, remaining, need, cap, allocAll, util: cap ? need / cap : Infinity,
                     gap, needFde: Math.ceil(gap / fdeDays - 1e-9), fdeDays, costLine, variance, varTax, perDay, pool, taxable,
                     ownerUsed: ownerCap - oLeft, restUsed: restCap - rLeft, unfilled: tl.reduce((s, x) => s + x.unfilled, 0), opsFrom: firstHire + 1, opsOn,
                     breakeven: avg > 0 ? Math.ceil(cost.total / avg - 1e-9) : Infinity, perOrder: avg };

      const parties = {
        tech: techIncome,
        partners: people.filter(p => p.type === "P").reduce((a, p) => a + p.income, 0),
        other: people.filter(p => p.type === "O").reduce((a, p) => a + p.income, 0),
        demo, coKept: coRev - bonusAll - divTech - divP - cit, direct, taxAll: vat + pTax + cit + techTax + hostTax,
        unsplit: gross - (lineTech + coRev + introP + introO + demo + direct + vat),
        /* 按人：每个人 ＝ 税后收入 ＋ 在他的工厂上线下课分得的那份；ext 是不属于任何人的上课工厂 */
        persons: people.map(p => ({ id: p.id, name: p.name, type: p.type, c: p.c, v: p.after })), ext: extDemo, extTax: extDemo * hTax,
      };
      out.push({ y, lines, all, gross, vat, direct, coRev, introP, introO, demo, extDemo, lineTech, people, parties,
                 taxes: { vat, vatB, sur, introTax, divTax, cit, techTax, hostTax },
                 own: { paid: people.reduce((a, p) => a + p.own, 0), reduce: people.reduce((a, p) => a + p.reduce, 0), trial: people.reduce((a, p) => a + p.trial, 0) },
                 company: { rev: coRev, volAll: V, bonusRate: Y(c.bonusRate), refundRate: Y(c.refundRate), resPrev, ops: Y(c.ops), marketing: Y(c.marketing), hardware, contrib, refunds, fromRes, shortfall,
                            expenses, lossIn, pre, bonus, cit, citBase, taxAdj, legal, legalSum: st.legalSum, legalCap: Y(c.capital) * Y(c.legalCapRate), div, retain, cash: st.cash, divRate: Y(c.divRate), reserve: b, reserveCap: resCap, lossOut: st.loss, divTech,
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
        if (Math.abs(s - 1) > 1e-6) add(`分成比例「${r.g} · ${r.n}」加起来不是 100%（差额在「概览」页单列）`, y, `${Math.round(s * 1000) / 10}%`);
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
      const own = (pj.own || {})[p.id];
      if ((pj.trials || []).includes(p.id) && Array.isArray(own) && own.slice(0, N).some(x => num(x))) add(`${p.name}的工厂既是「${pj.name}」的试验厂，又在自家工厂里买了它，同一个项目算了两次`, null);
    }));
    res.filter(r => r.tech.heads <= 0).forEach(r => add("技术方没有人（岗位人数都是 0）", r.y));
    res.filter(r => r.tech.gap > 1e-9).forEach(r => add("项目需要的人天超出技术方可交付人天（见「技术方」页）", r.y, `还差 ${Math.ceil(r.tech.gap)} 人天，约 ${r.tech.needFde} 名 FDE`));
    res.filter(r => r.tech.teachShort > 1e-9).forEach(r => add("线下课讲课只能由本人上，讲课需要的人天超出本人可交付人天", r.y, `超出 ${Math.ceil(r.tech.teachShort)} 人天`));
    res.filter(r => r.tech.remaining < -1e-9).forEach(r => add("分配给项目的人天超出可调用人天（见「技术方」页）", r.y, `超出 ${Math.ceil(-r.tech.remaining)} 人天`));
    res.filter(r => r.company.lossOut > 0).forEach(r => add("合作公司亏损，当年不发业绩奖、不分红，亏损结转下一年", r.y));
    return [...msgs].map(([k, ys]) => (ys.length ? `${k}：${ys.join("、")}` : k));
  }

  /* 讲稿 index-v5.html 经营测算 5 页的场景下，第一年应与讲稿一致。第五版的默认值已与讲稿不同，故单独搭讲稿的场景：
     销售合伙人 1 与其他销售 1；ERP 4／2 家、不含变更；AI 报价助手 4 万、3／2 家、不含实施、销售合伙人 1 当试验厂；
     GEO 2／2 家；线下课 4 期在其他工厂；不算税与法定公积金；没有人给自家工厂买 */
  const DECK = [["总收入", r => r.gross, 209], ["技术方", r => r.parties.tech, 122.11], ["销售合伙人（合计）", r => r.parties.partners, 31.08],
                ["其他销售（合计）", r => r.parties.other, 7.87], ["上课工厂", r => r.parties.demo, 27.54], ["合作公司留作支出", r => r.parties.coKept, 9.6],
                ["ERP 技术方", r => r.lines.erp.tech, 69.86], ["AI 报价助手 合作公司", r => r.lines.proj[0].co, 1.52], ["GEO 介绍人", r => r.lines.geo.introP + r.lines.geo.introO, 2.43],
                ["合作公司收入", r => r.coRev, 20.07], ["业绩奖", r => r.company.bonus, 3.141], ["分红", r => r.company.div, 7.329]];
  function deckInput() {
    const d = JSON.parse(JSON.stringify(DEFAULTS));
    Object.keys(d.tax).forEach(k => { d.tax[k] = [0]; });
    d.company.legalReserve = [0];
    d.others = [{ id: "o1", name: "其他销售 1", join: 1, c: 1 }];
    d.erp.onsiteDays = [30]; d.erp.devDays = [0]; d.erp.changeDays = [0];
    d.company.reserveRate = [1]; d.company.reserveCapRate = [0]; d.company.reserveMin = [5]; d.erp.sales = { p1: [4], o1: [2] }; d.erp.own = {};
    d.projects = [{ id: "j1", name: "AI 报价助手", launch: 1, trials: ["p1"], rdDays: 60, hardware: 1,
                    price: [4], onsiteDays: [0], devDays: [0], changeDays: [0], maintRate: [0.10], sales: { p1: [3], o1: [2] }, own: {} }];
    d.geo.sales = { p1: [2], o1: [2] }; d.geo.own = {};
    d.course.hosts = { ext: [4] }; d.course.referrals = {};
    return d;
  }
  function selfCheck() {
    const r = compute(deckInput())[0];
    return DECK.map(([name, f, want]) => { const got = f(r); return { name, want, got, ok: Math.abs(got - want) < 0.006 }; });
  }

  return { DEFAULTS, SPLIT_ROWS, COLS, compute, warnings, selfCheck, deckInput, yv, ev, src, clampYears, joinYear };
})();
