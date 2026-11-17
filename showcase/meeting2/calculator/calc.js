"use strict";
/* 经营测算器 · 计算部分（P1-S10 R04）
   只算数，不碰页面。单位：金额万元、时间天、人数人；比例一律用小数（0.1 即 10%）。
   默认值出自合作方案草案 v16 与讲稿 index-v5.html 经营测算 5 页；口径见
   docs/01-需求摸底/S10-商业化商讨/R04-经营测算器/P1-S10-R4-Pai000协作记录.md 第 2 步 ⑥。 */
const CALC = (() => {
  const DEFAULTS = {
    years: 3,
    tax: { vat: 0, introducerTax: 0 },
    price: { erpModule: 13, dayRate: 0.15, dayRateHired: 0.18, implDays: 30, changeDays: 0, maintRate: 0.10, maintRetain: 1 },
    erp: { partnerSales: [4, 5, 6], otherSales: [2, 3, 4] },
    projects: [
      { name: "AI 报价助手", price: 4, launch: 1, trials: 1, implDays: 0, maintRate: 0.10, rdDays: 60, hardware: 1,
        partnerSales: [3, 5, 5], otherSales: [2, 3, 3] },
    ],
    geo: { price: 3, renew: 0.8, days: 10, partnerNew: [2, 2, 2], otherNew: [2, 2, 2] },
    course: { students: 30, fee: 0.6, directCost: 0.15, cut: 0.10, techShare: 0.5, teachDays: 10, sessions: [4, 4, 4],
              onlineFee: 0.2, online: [0, 0, 0], referralFee: 0.5, referrals: [0, 0, 0] },
    split: { cut: 0.10, partner: 0.30, other: 0.15, techWhenOther: 0.70, dayTech: 0.70, maintTech: 1, trialRatio: 0.5, trialDeduct: 0.05 },
    partners: [
      { tech: true, name: "技术方", share: 0.35 },
      { name: "销售合伙人", share: 0.65, weight: 1, ownErpYear: 0, demo: false },
    ],
    company: { ops: 0.6, marketing: 3, reserveAnnual: 5, reserveCap: 5, refundRate: 0, bonusRate: 0.30, cit: 0, legalReserve: 0, techShareMin: 0.35 },
    tech: { ownerMonthly: 1.5, staffMonthly: 2, staff: [0, 1, 2], ownerDays: 120, staffDays: 200, maintDays: 3,
            serverCost: 1.5, perServer: 10, aiCost: 0.2 },
  };

  const num = x => (Number.isFinite(+x) ? +x : 0);
  /* 逐年数组：第 i 年没填时沿用最后一个值 */
  const at = (a, i) => (Array.isArray(a) && a.length ? num(i < a.length ? a[i] : a[a.length - 1]) : 0);
  const KEYS = ["co", "tech", "introP", "introO", "demo", "direct"];

  function newLine(name) {
    const L = { name, gross: 0, vat: 0, parts: {} };
    KEYS.forEach(k => { L[k] = 0; L.parts[k] = []; });
    return L;
  }
  function put(L, key, label, v) { if (!v) return; L[key] += v; L.parts[key].push([label, v]); }
  function book(L, who, label, sh) {
    put(L, "co", label, sh.co); put(L, "tech", label, sh.tech); put(L, who === "p" ? "introP" : "introO", label, sh.intro);
  }
  /* 模块费、项目费、GEO：先抽给合作公司，再分 */
  function shareMod(g, who, s) {
    if (who === "p") { const co = g * s.cut, intro = g * (1 - s.cut) * s.partner; return { co, intro, tech: g - co - intro }; }
    const tech = g * s.techWhenOther, intro = g * (1 - s.cut) * s.other; return { tech, intro, co: g - tech - intro };
  }
  /* 实施人天、变更单：不抽 */
  function shareDay(g, who, s) {
    const tech = g * s.dayTech, intro = g * (who === "p" ? s.partner : s.other); return { tech, intro, co: g - tech - intro };
  }
  const WHO = { p: "销售合伙人", o: "其他销售" };
  const n1 = x => String(Math.round(x * 10) / 10);

  function compute(inp) {
    const N = Math.max(1, Math.min(10, Math.round(num(inp.years)) || 1));
    const pr = inp.price, s = inp.split, geo = inp.geo, cs = inp.course, c = inp.company, t = inp.tech;
    const v = 1 / (1 + num(inp.tax.vat));
    const techRow = inp.partners.find(p => p.tech) || { share: 0 };
    const partners = inp.partners.filter(p => !p.tech);
    const wRaw = partners.map(p => Math.max(0, num(p.weight)));
    const wSum = wRaw.reduce((a, b) => a + b, 0);
    const w = wRaw.map(x => (wSum ? x / wSum : 0));
    const demoIdx = partners.map((p, k) => (p.demo ? k : -1)).filter(k => k >= 0);
    const st = { erpActive: 0, proj: inp.projects.map(() => ({ active: 0, pool: null })), geoP: 0, geoO: 0, reserve: 0, loss: 0 };
    const out = [];

    for (let i = 0; i < N; i++) {
      const y = i + 1;
      const staff = Math.max(0, at(t.staff, i));
      const rate = staff > 0 ? num(pr.dayRateHired) : num(pr.dayRate);
      const lines = { erp: newLine("ERP"), proj: inp.projects.map(p => newLine(p.name || "降本增效项目")),
                      geo: newLine("宣传与获客（GEO）"), course: newLine("驻厂工程师培训班") };
      const vol = { p: 0, o: 0, own: partners.map(() => 0) };
      const ownPaid = partners.map(() => 0);
      const days = { impl: 0, maint: 0, proj: 0, rd: 0, geo: 0, teach: 0 };
      let hardware = 0, onlineGross = 0;
      const sale = (L, G) => { L.gross += G; L.vat += G * (1 - v); return G * v; };
      const ret = num(pr.maintRetain), md = num(t.maintDays);

      /* ---- ERP ---- */
      let L = lines.erp;
      const M = num(pr.erpModule), D = num(pr.implDays) * rate, C = num(pr.changeDays) * rate;
      const nP = at(inp.erp.partnerSales, i), nO = at(inp.erp.otherSales, i);
      for (const [who, n] of [["p", nP], ["o", nO]]) {
        if (!n) continue;
        const tag = `${WHO[who]}介绍 ${n1(n)} 家`;
        book(L, who, `${tag}：模块费 ${M} 万 × ${n1(n)}`, shareMod(sale(L, M * n), who, s));
        if (D + C) book(L, who, `${tag}：实施与变更 ${num(pr.implDays) + num(pr.changeDays)} 天 × ${rate * 10000} 元 × ${n1(n)}`, shareDay(sale(L, (D + C) * n), who, s));
        vol[who] += (M + D + C) * n;
      }
      let ownNew = 0;
      const ownRatio = 1 - (1 - s.cut) * s.partner;           /* 销售合伙人价：介绍人那份返给自己 */
      partners.forEach((p, k) => {
        if (Math.round(num(p.ownErpYear)) !== y) return;
        ownNew++;
        const paid = M * ownRatio; sale(L, paid);
        const tag = `${p.name || "销售合伙人"}自家工厂（销售合伙人价 ${M} 万 × ${Math.round(ownRatio * 1000) / 10}%，免实施费）`;
        put(L, "co", tag, M * s.cut * v); put(L, "tech", tag, M * (1 - s.cut) * (1 - s.partner) * v);
        vol.own[k] += paid; ownPaid[k] += paid;
      });
      const kept = st.erpActive * ret;
      if (kept) {
        const net = sale(L, kept * M * num(pr.maintRate)), tag = `年维护 ${n1(kept)} 家 × ${M} 万 × ${Math.round(num(pr.maintRate) * 1000) / 10}%`;
        put(L, "tech", tag, net * s.maintTech); put(L, "co", tag, net * (1 - s.maintTech));
      }
      st.erpActive = kept + nP + nO + ownNew;
      days.impl += (nP + nO + ownNew) * num(pr.implDays) + (nP + nO) * num(pr.changeDays);
      days.maint += kept * md;
      const erpTechPer = { p: M * (1 - s.cut) * (1 - s.partner) + (D + C) * s.dayTech, o: M * s.techWhenOther + (D + C) * s.dayTech };

      /* ---- 降本增效项目 ---- */
      let launches = 0, projSales = 0;
      inp.projects.forEach((p, j) => {
        const L = lines.proj[j], S = st.proj[j], P = num(p.price), launch = Math.round(num(p.launch));
        if (y < launch) return;
        if (S.pool === null) S.pool = num(p.trials) * P * s.trialRatio;   /* 推向市场那年按市场价锁定 */
        if (y === launch) { hardware += num(p.hardware); days.rd += num(p.rdDays); launches++; }
        const keptP = S.active * ret;
        if (keptP) {
          const net = sale(L, keptP * P * num(p.maintRate)), tag = `年维护 ${n1(keptP)} 家 × ${P} 万 × ${Math.round(num(p.maintRate) * 1000) / 10}%`;
          put(L, "tech", tag, net * s.maintTech); put(L, "co", tag, net * (1 - s.maintTech));
        }
        days.maint += keptP * md;
        const Di = num(p.implDays) * rate;
        let n = 0;
        for (const [who, nn] of [["p", at(p.partnerSales, i)], ["o", at(p.otherSales, i)]]) {
          if (!nn) continue;
          const tag = `${WHO[who]}介绍 ${n1(nn)} 家`;
          book(L, who, `${tag}：${P} 万 × ${n1(nn)}`, shareMod(sale(L, P * nn), who, s));
          if (Di) book(L, who, `${tag}：实施 ${num(p.implDays)} 天 × ${rate * 10000} 元 × ${n1(nn)}`, shareDay(sale(L, Di * nn), who, s));
          vol[who] += (P + Di) * nn; n += nn;
        }
        const ded = Math.min(S.pool, n * P * s.trialDeduct);
        if (ded > 0) {
          const tag = `替试验厂抵扣：${P} 万 × ${Math.round(s.trialDeduct * 1000) / 10}% × ${n1(n)} 单${ded < n * P * s.trialDeduct - 1e-9 ? "（抵清为止）" : ""}`;
          put(L, "co", tag, -ded * v); put(L, "tech", tag, ded * v); S.pool -= ded;
        }
        S.active = keptP + n; projSales += n;
        days.proj += n * num(p.implDays);
      });

      /* ---- 宣传与获客（GEO 年度服务，按年收费，老客户续费） ---- */
      L = lines.geo;
      const G = num(geo.price);
      st.geoP = st.geoP * num(geo.renew) + at(geo.partnerNew, i);
      st.geoO = st.geoO * num(geo.renew) + at(geo.otherNew, i);
      for (const [who, n] of [["p", st.geoP], ["o", st.geoO]]) {
        if (!n) continue;
        book(L, who, `${WHO[who]}介绍 ${n1(n)} 家（含续费）：${G} 万 × ${n1(n)}`, shareMod(sale(L, G * n), who, s));
        vol[who] += G * n;
      }
      days.geo += (st.geoP + st.geoO) * num(geo.days);

      /* ---- 驻厂工程师培训班 ---- */
      L = lines.course;
      const ses = at(cs.sessions, i);
      if (ses) {
        const Gc = ses * num(cs.students) * num(cs.fee), net = sale(L, Gc), direct = Gc * num(cs.directCost);
        const rest = net - direct, co = rest * num(cs.cut), tech = (rest - co) * num(cs.techShare);
        const tag = `线下课 ${n1(ses)} 期 × ${num(cs.students)} 人 × ${Math.round(num(cs.fee) * 10000)} 元`;
        put(L, "direct", `${tag}，直接成本 ${Math.round(num(cs.directCost) * 1000) / 10}%`, direct);
        put(L, "co", `${tag}，扣直接成本后抽 ${Math.round(num(cs.cut) * 1000) / 10}%`, co);
        put(L, "tech", `${tag}，余下的 ${Math.round(num(cs.techShare) * 1000) / 10}%`, tech);
        put(L, "demo", `${tag}，余下的 ${Math.round((1 - num(cs.techShare)) * 1000) / 10}%`, rest - co - tech);
      }
      days.teach += ses * num(cs.teachDays);
      const onl = at(cs.online, i) * num(cs.onlineFee);
      if (onl) { onlineGross += onl; put(L, "tech", `线上课 ${n1(at(cs.online, i))} 人（技术方的公司直接收）`, sale(L, onl)); }
      const rf = at(cs.referrals, i) * num(cs.referralFee);
      if (rf) put(L, "co", `学员推荐费 ${n1(at(cs.referrals, i))} 人`, sale(L, rf));

      /* ---- 汇总 ---- */
      const all = [lines.erp, ...lines.proj, lines.geo, lines.course];
      const sum = k => all.reduce((a, l) => a + l[k], 0);
      const gross = sum("gross"), vat = sum("vat"), coRev = sum("co"), introP = sum("introP"), introO = sum("introO");
      const demo = sum("demo"), direct = sum("direct"), lineTech = sum("tech");

      /* ---- 数字化合作公司的账 ---- */
      const refunds = (gross - onlineGross) * num(c.refundRate);
      let b = st.reserve;
      const fromRes = Math.min(b, refunds); b -= fromRes;
      const shortfall = refunds - fromRes;
      const contrib = Math.min(num(c.reserveAnnual), Math.max(0, num(c.reserveCap) - b)); b += contrib; st.reserve = b;
      const expenses = num(c.ops) + num(c.marketing) + hardware + contrib + shortfall;
      const lossIn = st.loss;
      let pre = coRev - expenses - lossIn, bonus = 0, cit = 0, legal = 0, div = 0;
      if (pre < 0) st.loss = -pre;
      else {
        st.loss = 0; bonus = pre * num(c.bonusRate);
        const ab = pre - bonus; cit = ab * num(c.cit); legal = (ab - cit) * num(c.legalReserve); div = ab - cit - legal;
      }
      const V = vol.p + vol.o + vol.own.reduce((a, x) => a + x, 0);
      const bonusO = V ? bonus * vol.o / V : 0;
      const bonusP = partners.map((p, k) => (V ? bonus * (vol.p * w[k] + vol.own[k]) / V : 0));
      const divTech = div * num(techRow.share);
      const divP = partners.map(p => div * num(p.share));
      const iTax = num(inp.tax.introducerTax);
      const demoEach = demoIdx.length ? demo / demoIdx.length : 0;
      const people = partners.map((p, k) => {
        const intro = introP * w[k] * (1 - iTax);
        const dm = p.demo ? demoEach : 0;
        return { name: p.name || `销售合伙人 ${k + 1}`, intro, bonus: bonusP[k], div: divP[k], demo: dm, own: ownPaid[k],
                 net: intro + bonusP[k] + divP[k] + dm - ownPaid[k], vol: vol.p * w[k] + vol.own[k] };
      });
      const other = { intro: introO * (1 - iTax), bonus: bonusO, net: introO * (1 - iTax) + bonusO, vol: vol.o };
      const assigned = bonusO + bonusP.reduce((a, x) => a + x, 0) + divTech + divP.reduce((a, x) => a + x, 0);
      const introTax = (introP * (wSum ? 1 : 0) + introO) * iTax;
      const unpaidIntro = wSum ? 0 : introP;                    /* 没有可分的销售合伙人时，这部分无人领 */

      /* ---- 技术方 ---- */
      const servers = st.erpActive > 0 && num(t.perServer) > 0 ? Math.ceil(st.erpActive / num(t.perServer) - 1e-9) : 0;
      const cost = { owner: 12 * num(t.ownerMonthly), staff: 12 * staff * num(t.staffMonthly),
                     server: servers * num(t.serverCost), ai: st.erpActive * num(t.aiCost) };
      cost.total = cost.owner + cost.staff + cost.server + cost.ai;
      const techIncome = lineTech + divTech;
      const need = days.impl + days.maint + days.proj + days.rd + days.geo + days.teach;
      const cap = num(t.ownerDays) + staff * num(t.staffDays);
      const nn = nP + nO;
      const per = nn ? (nP * erpTechPer.p + nO * erpTechPer.o) / nn : erpTechPer.p;
      const techTbl = { income: techIncome, lineTech, div: divTech, cost, profit: techIncome - cost.total,
                        margin: techIncome ? (techIncome - cost.total) / techIncome : 0, staff, rate, servers, clients: st.erpActive,
                        days, need, cap, util: cap ? need / cap : Infinity,
                        needStaff: num(t.staffDays) > 0 ? Math.max(0, Math.ceil((need - num(t.ownerDays)) / num(t.staffDays) - 1e-9)) : 0,
                        breakeven: per > 0 ? Math.ceil(cost.total / per - 1e-9) : Infinity, perOrder: per };

      const partyPartners = people.reduce((a, p) => a + p.intro + p.bonus + p.div, 0);
      const parties = {
        tech: techIncome, partners: partyPartners, other: other.net, demo,
        coKept: coRev - assigned, costTax: vat + direct + introTax, unpaid: unpaidIntro,
      };
      out.push({ y, lines, all, gross, vat, direct, coRev, introP, introO, demo, lineTech, vol, people, other, parties,
                 company: { rev: coRev, ops: num(c.ops), marketing: num(c.marketing), hardware, launches, contrib, refunds, fromRes, shortfall,
                            expenses, lossIn, pre, bonus, cit, legal, div, reserve: b, lossOut: st.loss, divTech, divP,
                            unallocated: div - divTech - divP.reduce((a, x) => a + x, 0) },
                 tech: techTbl, projSales });
    }
    return out;
  }

  /* 输入是否自洽：只提示，不阻止 */
  function warnings(inp, res) {
    const w = [];
    const tot = inp.partners.reduce((a, p) => a + num(p.share), 0);
    if (Math.abs(tot - 1) > 1e-6) w.push(`股份合计 ${Math.round(tot * 1000) / 10}%，不是 100%；分红按各行填的比例分，差额列为「未分配」`);
    const tr = inp.partners.find(p => p.tech);
    if (tr && num(tr.share) < num(inp.company.techShareMin) - 1e-9) w.push(`技术方股份 ${Math.round(num(tr.share) * 1000) / 10}% 低于下限 ${Math.round(num(inp.company.techShareMin) * 1000) / 10}%`);
    const s = inp.split;
    if (s.techWhenOther + (1 - s.cut) * s.other > 1 + 1e-9) w.push("其他销售介绍时，技术方与介绍人的比例加起来超过 100%，合作公司那份成了负数");
    if (s.dayTech + s.partner > 1 + 1e-9 || s.dayTech + s.other > 1 + 1e-9) w.push("人天费的技术方比例加介绍人比例超过 100%，合作公司那份成了负数");
    const ps = inp.partners.filter(p => !p.tech);
    if (!ps.length) w.push("合伙人表里没有销售合伙人，销售合伙人介绍的介绍费无人领");
    else if (!ps.some(p => num(p.weight) > 0)) w.push("销售合伙人的「介绍业务占比」都是 0，介绍费无人领");
    const over = res.filter(r => r.tech.util > 1).map(r => `第 ${r.y} 年 ${Math.round(r.tech.util * 100)}%`);
    if (over.length) w.push(`交付天数超出技术方产能：${over.join("、")}（见「逐年」页的需要员工数）`);
    const loss = res.filter(r => r.company.lossOut > 0).map(r => `第 ${r.y} 年`);
    if (loss.length) w.push(`数字化合作公司亏损：${loss.join("、")}，当年不发业绩奖、不分红，亏损结转下一年`);
    return w;
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

  return { DEFAULTS, compute, warnings, selfCheck, at };
})();
