/* 共享假数据：七个演示界面只读这一份，同一张订单在各界面数字一致。
   名字沿用一年期场景（frappe_debug/data/scenario.yaml），规模扩到 11 台设备（P1-S9-R2 第 1 步）。
   上半部是原始数据，下半部「派生」由原始数据算出（金额、负荷、排程、交期风险、应收），不要手改派生结果。
   全局变量：window.SC_DATA */
(function () {
  const TODAY = "2026-11-02"; // 周一，同场景终点

  // ---------- 工具 ----------
  function rng(seed) { // mulberry32，种子同场景 817，结果固定
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rand = rng(817);
  const gauss = () => Math.sqrt(-2 * Math.log(rand() || 1e-9)) * Math.cos(2 * Math.PI * rand());
  const pad = (n) => String(n).padStart(2, "0");
  const fmt = (t) => t.getFullYear() + "-" + pad(t.getMonth() + 1) + "-" + pad(t.getDate()); // 本地时间，不用 toISOString（会转成 UTC）
  const D = (offset) => { const t = new Date(TODAY + "T00:00:00"); t.setDate(t.getDate() + offset); return fmt(t); }; // 相对今天的日期

  // ---------- 公司与角色 ----------
  const company = { name: "华东弹簧有限公司", abbr: "HDTH", currency: "CNY" };
  // 界面按角色设计，称呼只在这里，换客户时改这一处（R01 DEC-011）
  const roles = {
    production: { title: "生产负责人", person: "老板" },
    sales: { title: "销售负责人", person: "老板娘" },
  };
  const statusText = { run: "运行", wait: "待料", down: "停机", over: "超负荷", alarm: "异常", idle: "空闲" };

  // ---------- 设备 ----------
  // speed：相对场景标准工时的系数（卷簧机-2 场景里比 -1 快 12%）；capacity：并行数；pos：厂区平面格子坐标（12×6）
  const emp = (n) => "HDTH 场景员工 " + String(n).padStart(2, "0");
  const workstations = [
    { id: "卷簧机-1", type: "卷簧", zone: "卷簧区", speed: 1.00, capacity: 1, hourRate: 45, status: "over", operator: emp(1), pos: { x: 0, y: 0 } },
    { id: "卷簧机-2", type: "卷簧", zone: "卷簧区", speed: 0.88, capacity: 1, hourRate: 65, status: "alarm", operator: emp(2), pos: { x: 0, y: 2 } },
    { id: "卷簧机-3", type: "卷簧", zone: "卷簧区", speed: 1.00, capacity: 1, hourRate: 45, status: "run", operator: emp(3), pos: { x: 0, y: 4 } },
    { id: "卷簧机-4", type: "卷簧", zone: "卷簧区", speed: 1.10, capacity: 1, hourRate: 50, status: "wait", operator: emp(4), pos: { x: 2, y: 4 } },
    { id: "回火炉-1", type: "回火", zone: "热处理区", speed: 1.00, capacity: 2, hourRate: 60, status: "run", operator: emp(5), pos: { x: 4, y: 0 } },
    { id: "回火炉-2", type: "回火", zone: "热处理区", speed: 1.00, capacity: 2, hourRate: 60, status: "run", operator: emp(6), pos: { x: 4, y: 3 } },
    { id: "磨端机-1", type: "磨端", zone: "磨端区", speed: 1.00, capacity: 1, hourRate: 35, status: "run", operator: emp(7), pos: { x: 7, y: 0 } },
    { id: "磨端机-2", type: "磨端", zone: "磨端区", speed: 1.00, capacity: 1, hourRate: 35, status: "run", operator: emp(8), pos: { x: 7, y: 2 } },
    { id: "喷丸机-1", type: "喷丸", zone: "表面处理区", speed: 1.00, capacity: 1, hourRate: 40, status: "down", operator: emp(9), pos: { x: 7, y: 4 } },
    { id: "检验台-1", type: "检验", zone: "检验包装区", speed: 1.00, capacity: 1, hourRate: 30, status: "run", operator: emp(10), pos: { x: 10, y: 0 } },
    { id: "包装线-1", type: "包装", zone: "检验包装区", speed: 1.00, capacity: 1, hourRate: 25, status: "idle", operator: emp(11), pos: { x: 10, y: 3 } },
  ];
  // 卷簧机能卷的最大线径（mm）：φ8.0 只有卷簧机-4 能卷
  const maxWire = { "卷簧机-1": 5, "卷簧机-2": 5, "卷簧机-3": 5, "卷簧机-4": 8 };
  workstations.forEach((w) => { if (maxWire[w.id]) w.maxWireMm = maxWire[w.id]; });
  const statusNote = { // 非运行状态的原因，与下文缺料、SPC 判异对应
    "卷簧机-2": "压簧 3.0 自由长度连续 9 组在中心线上方（SPC 判异）",
    "卷簧机-4": "60Si2Mn φ8.0 钢丝低于安全库存，等到货",
    "喷丸机-1": "计划保养，预计今天 15:00 恢复",
    "包装线-1": "上道检验未放行",
  };
  // ---------- 工艺路线（每 1000 支的标准分钟、工序损耗率；前三道取自场景，喷丸、检验、包装为扩规模新增） ----------
  const routings = {
    compression: [
      { op: "卷簧", type: "卷簧", min: 50, loss: 3 }, { op: "回火", type: "回火", min: 18, loss: 1 },
      { op: "磨端", type: "磨端", min: 36, loss: 1 }, { op: "喷丸", type: "喷丸", min: 12, loss: 0 },
      { op: "检验", type: "检验", min: 6, loss: 0 }, { op: "包装", type: "包装", min: 6, loss: 0 },
    ],
    tension: [
      { op: "卷簧", type: "卷簧", min: 65, loss: 3 }, { op: "回火", type: "回火", min: 18, loss: 1 },
      { op: "检验", type: "检验", min: 6, loss: 0 }, { op: "包装", type: "包装", min: 6, loss: 0 },
    ],
  };

  // ---------- 产品与原料（编码、名称、单价、每千支用钢量取自场景） ----------
  const products = [
    { code: "SPR-C-3.0-23-50", name: "压簧 YA 3.0×23×50", kind: "压簧", routing: "compression", price: 0.88, wire: "WIRE-65MN-3.0", kgPer1000: 29.42 },
    { code: "SPR-C-5.0-35-75", name: "压簧 YA 5.0×35×75", kind: "压簧", routing: "compression", price: 2.30, wire: "WIRE-65MN-5.0", kgPer1000: 122.60 },
    { code: "SPR-C-8.0-58-115", name: "压簧 YA 8.0×58×115", kind: "压簧", routing: "compression", price: 8.50, wire: "WIRE-60SI2MN-8.0", kgPer1000: 523 },
    { code: "SPR-T-3.0-23-34", name: "拉簧 3.0×23×34.5", kind: "拉簧", routing: "tension", price: 1.25, wire: "WIRE-65MN-3.0", kgPer1000: 43.58 },
    { code: "SPR-T-5.0-30-58", name: "拉簧 5.0×30×57.5", kind: "拉簧", routing: "tension", price: 2.85, wire: "WIRE-65MN-5.0", kgPer1000: 151.32 },
  ];
  // 库存单位千克；safety 安全库存、rop 再订货点、onOrder 在途、dailyUse 近 30 天日均出库
  const materials = [
    // arrival：在途那批的到货日；φ8.0 低于安全库存，卷簧机-4 等它（statusNote）
    { code: "WIRE-65MN-3.0", name: "65Mn弹簧钢丝φ3.0", price: 8.16, leadDays: 7, stock: 6200, safety: 2400, rop: 4800, onOrder: 3000, arrival: D(3), dailyUse: 520 },
    { code: "WIRE-65MN-5.0", name: "65Mn弹簧钢丝φ5.0", price: 7.96, leadDays: 7, stock: 2900, safety: 1500, rop: 3200, onOrder: 0, arrival: null, dailyUse: 310 },
    { code: "WIRE-60SI2MN-8.0", name: "60Si2Mn弹簧钢丝φ8.0", price: 8.76, leadDays: 10, stock: 1650, safety: 2600, rop: 5200, onOrder: 6000, arrival: D(2), dailyUse: 380 },
  ];

  // ---------- 供应商（价格按场景 supplier_trend 的基价加 12 个月涨跌；准时率、合格率、评分为演示值） ----------
  const supplierTrend = [
    ["钢丝供应商01", "WIRE-65MN-3.0", 7.80, 0.03], ["钢丝供应商02", "WIRE-65MN-3.0", 7.86, 0.01],
    ["钢丝供应商03", "WIRE-65MN-3.0", 7.98, -0.01], ["钢丝供应商04", "WIRE-65MN-3.0", 8.16, -0.03],
    ["钢丝供应商05", "WIRE-65MN-5.0", 7.60, 0.03], ["钢丝供应商06", "WIRE-65MN-5.0", 7.66, 0.01],
    ["钢丝供应商07", "WIRE-65MN-5.0", 7.78, -0.01], ["钢丝供应商08", "WIRE-65MN-5.0", 7.96, -0.03],
    ["钢丝供应商09", "WIRE-60SI2MN-8.0", 8.40, 0.03], ["钢丝供应商10", "WIRE-60SI2MN-8.0", 8.46, 0.01],
    ["钢丝供应商11", "WIRE-60SI2MN-8.0", 8.58, -0.01], ["钢丝供应商12", "WIRE-60SI2MN-8.0", 8.76, -0.03],
  ];
  const supplierQuality = [[0.96, 0.995], [0.93, 0.990], [0.91, 0.985], [0.82, 0.950], [0.97, 0.993], [0.92, 0.988],
    [0.90, 0.982], [0.84, 0.955], [0.95, 0.991], [0.94, 0.989], [0.88, 0.980], [0.80, 0.948]];
  const suppliers = supplierTrend.map(([name, item, base, change], i) => {
    const [onTime, pass] = supplierQuality[i];
    return { name, item, price: +(base + change * 12).toFixed(2), onTime, passRate: pass,
      score: Math.round(onTime * 45 + pass * 45 + (i % 4 === 3 ? 0 : 6)) };
  });
  // ---------- 客户（30 个，名字同场景 customer_names：城市＋弹簧厂） ----------
  const cityPool = ["苏州", "无锡", "常州", "南通", "宁波", "嘉兴", "湖州", "绍兴", "台州", "合肥", "芜湖", "马鞍山", "泰州", "扬州", "镇江",
    "淮安", "宿迁", "盐城", "温州", "金华", "丽水", "舟山", "铜陵", "宣城", "滁州", "蚌埠", "徐州", "连云港", "衢州", "黄山"];
  const creditSteps = [80000, 100000, 150000, 200000, 300000, 500000];
  const customers = cityPool.map((city, i) => ({
    name: city + "弹簧厂",
    contact: "采购联系人",
    level: i < 6 ? "A" : i < 16 ? "B" : "C",
    creditLimit: creditSteps[(i * 7) % 6] * (i < 6 ? 2 : 1),
    termDays: [30, 45, 60][i % 3],
    since: D(-365 + i * 9),
  }));

  // ---------- CRM：线索与商机（状态名同 frappe_china 译名：zh.csv） ----------
  // 场景里线索联系人一律「采购联系人」；第 1 幕现场新建的线索是常州恒力机械有限公司／张伟（demo.yaml:42）
  const leadStatus = { New: "新线索", Contacted: "已联系", Nurture: "培育中", Qualified: "合格", Unqualified: "不合格", Junk: "无效" };
  const leads = [
    { id: "CRM-LEAD-2026-00104", org: "常州恒力机械有限公司", contact: "张伟", status: "New", source: "展会", created: D(0) },
    { id: "CRM-LEAD-2026-00103", org: "湖州弹簧厂", contact: "采购联系人", status: "Contacted", source: "老客户介绍", created: D(-2) },
    { id: "CRM-LEAD-2026-00102", org: "丽水弹簧厂", contact: "采购联系人", status: "Nurture", source: "官网", created: D(-5) },
    { id: "CRM-LEAD-2026-00101", org: "铜陵弹簧厂", contact: "采购联系人", status: "Qualified", source: "电话", created: D(-6) },
    { id: "CRM-LEAD-2026-00100", org: "宣城弹簧厂", contact: "采购联系人", status: "Contacted", source: "展会", created: D(-9) },
    { id: "CRM-LEAD-2026-00099", org: "黄山弹簧厂", contact: "采购联系人", status: "Unqualified", source: "官网", created: D(-12) },
  ];
  const dealStatus = { Qualification: "需求确认", "Demo/Making": "方案演示", "Proposal/Quotation": "报价",
    Negotiation: "谈判中", "Ready to Close": "待成交", Won: "赢单", Lost: "输单" };
  // 未成交商机：product/qty/wantDate 供「能不能接」计算（见派生 ctp）
  const deals = [
    { id: "CRM-DEAL-2026-00087", customer: "常州弹簧厂", product: "SPR-C-3.0-23-50", qty: 40000, wantDate: D(14), status: "Negotiation", probability: 70, owner: "sales" },
    { id: "CRM-DEAL-2026-00086", customer: "苏州弹簧厂", product: "SPR-T-3.0-23-34", qty: 30000, wantDate: D(18), status: "Proposal/Quotation", probability: 50, owner: "sales" },
    { id: "CRM-DEAL-2026-00085", customer: "宁波弹簧厂", product: "SPR-C-8.0-58-115", qty: 8000, wantDate: D(12), status: "Ready to Close", probability: 90, owner: "sales" },
    { id: "CRM-DEAL-2026-00084", customer: "铜陵弹簧厂", product: "SPR-C-5.0-35-75", qty: 15000, wantDate: D(25), status: "Qualification", probability: 20, owner: "sales" },
    { id: "CRM-DEAL-2026-00083", customer: "温州弹簧厂", product: "SPR-T-5.0-30-58", qty: 12000, wantDate: D(21), status: "Demo/Making", probability: 35, owner: "sales" },
    { id: "CRM-DEAL-2026-00082", customer: "无锡弹簧厂", product: "SPR-C-3.0-23-50", qty: 50000, wantDate: D(30), status: "Proposal/Quotation", probability: 50, owner: "sales" },
    { id: "CRM-DEAL-2026-00081", customer: "嘉兴弹簧厂", product: "SPR-C-3.0-23-50", qty: 25000, wantDate: D(12), status: "Won", probability: 100, owner: "sales", salesOrder: "SAL-ORD-2026-00318" },
    { id: "CRM-DEAL-2026-00080", customer: "扬州弹簧厂", product: "SPR-T-3.0-23-34", qty: 20000, wantDate: D(-5), status: "Lost", probability: 0, owner: "sales", lostReason: "价格高于对方现供应商 6%" },
  ];
  // ---------- 销售订单（场景一年共 318 张，这里取末尾在手的 12 张；数量按扩规模放大） ----------
  const so = (n, customer, product, qty, ordered, delivery) =>
    ({ id: "SAL-ORD-2026-00" + n, customer, product, qty, ordered: D(ordered), delivery: D(delivery) });
  const salesOrders = [
    so(318, "嘉兴弹簧厂", "SPR-C-3.0-23-50", 25000, -3, 12), so(317, "常州弹簧厂", "SPR-T-3.0-23-34", 30000, -4, 10),
    so(316, "苏州弹簧厂", "SPR-C-3.0-23-50", 45000, -5, 9), so(315, "南通弹簧厂", "SPR-C-8.0-58-115", 6000, -8, 6),
    so(314, "宁波弹簧厂", "SPR-T-3.0-23-34", 30000, -8, 8), so(313, "绍兴弹簧厂", "SPR-C-5.0-35-75", 18000, -10, 5),
    so(312, "台州弹簧厂", "SPR-C-3.0-23-50", 45000, -11, 4), so(311, "合肥弹簧厂", "SPR-T-5.0-30-58", 15000, -12, 7),
    so(310, "芜湖弹簧厂", "SPR-C-3.0-23-50", 30000, -13, 2), so(309, "无锡弹簧厂", "SPR-T-3.0-23-34", 35000, -15, 3),
    so(308, "马鞍山弹簧厂", "SPR-C-3.0-23-50", 20000, -16, 1), so(307, "泰州弹簧厂", "SPR-C-8.0-58-115", 5000, -18, 0),
  ];

  // ---------- 生产工单（每张在手订单一张）：ws 为 BOM 指定的设备，done 为各道工序已完成比例 ----------
  const wo = (n, soN, ws, done) => ({ id: "MFG-WO-2026-00" + n, salesOrder: "SAL-ORD-2026-00" + soN, ws, done });
  const W = (coil, temper, grind) => ({ 卷簧: "卷簧机-" + coil, 回火: "回火炉-" + temper, 磨端: grind ? "磨端机-" + grind : null,
    喷丸: "喷丸机-1", 检验: "检验台-1", 包装: "包装线-1" });
  const workOrders = [
    wo(312, 318, W(1, 1, 1), [0, 0, 0, 0, 0, 0]),       wo(311, 317, W(3, 2), [0, 0, 0, 0]),
    wo(310, 316, W(2, 1, 2), [0.15, 0, 0, 0, 0, 0]),    wo(309, 315, W(4, 2, 2), [0, 0, 0, 0, 0, 0]),
    wo(308, 314, W(1, 1), [0.35, 0.2, 0, 0]),           wo(307, 313, W(3, 2, 1), [0.6, 0.5, 0.3, 0, 0, 0]),
    wo(306, 312, W(1, 1, 1), [0.7, 0.55, 0.4, 0.2, 0, 0]), wo(305, 311, W(3, 2), [0.8, 0.6, 0, 0]),
    wo(304, 310, W(3, 1, 2), [1, 0.9, 0.7, 0.4, 0.2, 0]), wo(303, 309, W(2, 2), [1, 1, 0.5, 0.3]),
    wo(302, 308, W(2, 1, 1), [1, 1, 1, 0.8, 0.6, 0.4]), wo(301, 307, W(4, 2, 2), [1, 1, 1, 1, 0.7, 0.5]),
  ];

  // ---------- 已交货开票与回款（含税 13%）：近 8 周开票的 16 张 ----------
  const inv = (n, customer, product, qty, invoiced, paidRatio) =>
    ({ id: "ACC-SINV-2026-00" + n, salesOrder: "SAL-ORD-2026-00" + n, customer, product, qty, invoiced: D(invoiced), paidRatio });
  const invoices = [
    inv(306, "徐州弹簧厂", "SPR-C-3.0-23-50", 30000, -2, 0), inv(305, "扬州弹簧厂", "SPR-T-3.0-23-34", 25000, -4, 0),
    inv(304, "镇江弹簧厂", "SPR-C-5.0-35-75", 12000, -7, 0), inv(303, "南通弹簧厂", "SPR-C-3.0-23-50", 40000, -9, 0.5),
    inv(302, "苏州弹簧厂", "SPR-T-5.0-30-58", 10000, -12, 1), inv(301, "盐城弹簧厂", "SPR-C-8.0-58-115", 4000, -15, 0),
    inv(300, "宁波弹簧厂", "SPR-C-3.0-23-50", 35000, -18, 1), inv(299, "淮安弹簧厂", "SPR-T-3.0-23-34", 30000, -21, 0.3),
    inv(298, "常州弹簧厂", "SPR-C-3.0-23-50", 50000, -25, 1), inv(297, "宿迁弹簧厂", "SPR-C-5.0-35-75", 16000, -28, 0),
    inv(296, "无锡弹簧厂", "SPR-T-3.0-23-34", 28000, -32, 1), inv(295, "温州弹簧厂", "SPR-C-3.0-23-50", 22000, -36, 0),
    inv(294, "金华弹簧厂", "SPR-C-8.0-58-115", 5000, -52, 0.6), inv(293, "合肥弹簧厂", "SPR-C-3.0-23-50", 26000, -42, 1),
    inv(292, "泰州弹簧厂", "SPR-C-8.0-58-115", 3000, -40, 0), inv(291, "宿迁弹簧厂", "SPR-T-3.0-23-34", 18000, -55, 0.2),
  ];
  // ---------- 近 12 个月经营（2025-11～2026-10，未税金额；2 月春节回落，4 月 SPC 异常段不良率升） ----------
  const months = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"];
  const monthly = months.map((m, i) => ({
    month: m,
    revenue: [312000, 298000, 265000, 188000, 305000, 336000, 348000, 362000, 355000, 371000, 389000, 402000][i],
    orders: [26, 25, 23, 16, 27, 28, 29, 30, 28, 29, 30, 27][i], // 合计 318，同场景
    grossMargin: [0.31, 0.30, 0.29, 0.26, 0.30, 0.31, 0.32, 0.33, 0.32, 0.33, 0.34, 0.335][i],
    onTimeRate: [0.86, 0.88, 0.87, 0.82, 0.89, 0.90, 0.92, 0.91, 0.93, 0.94, 0.93, 0.95][i],
    defectRate: [0.021, 0.019, 0.020, 0.024, 0.018, 0.026, 0.016, 0.017, 0.015, 0.014, 0.013, 0.012][i],
  }));

  // ---------- SPC：压簧 3.0 自由长度，卷簧机-2，近 25 组、每组 5 件（均值 50、σ0.15、规格 49.5～50.5，同场景） ----------
  const spcSpec = { item: "SPR-C-3.0-23-50", param: "自由长度", unit: "mm", workstation: "卷簧机-2", usl: 50.5, lsl: 49.5, target: 50 };
  const spcGroups = [];
  for (let g = 0; g < 25; g++) {
    const shift = g >= 16 ? 0.09 : 0; // 第 17 组起整体偏上，造出 Nelson 第 2 条（连续 9 点同侧）
    let r = Array.from({ length: 5 }, () => +(50 + gauss() * 0.15 + shift).toFixed(3));
    const mean = r.reduce((a, b) => a + b) / 5;
    if (g >= 16 && mean < 50.04) r = r.map((v) => +(v + 50.04 - mean).toFixed(3));
    const t = new Date(TODAY + "T08:00:00"); t.setHours(t.getHours() - (24 - g) * 2);
    spcGroups.push({ no: g + 1, time: fmt(t).slice(5) + " " + pad(t.getHours()) + ":00", readings: r });
  }
  // ==================== 派生 ====================
  const byId = (list, key = "id") => Object.fromEntries(list.map((x) => [x[key], x]));
  const P = byId(products, "code"), M = byId(materials, "code"), WS = byId(workstations), C = byId(customers, "name");
  const SO = byId(salesOrders);
  const round2 = (v) => Math.round(v * 100) / 100;

  // 工作日历：每天 480 分钟（08:00-12:00、13:00-17:00），周日休；时间用「从今天 08:00 起的工作分钟」表示
  const DAY = 480, NOW = 150, HORIZON_DAYS = 6; // NOW＝今天 10:30
  function workDate(min) {
    let n = Math.floor(min / DAY); const t = new Date(TODAY + "T00:00:00");
    while (n > 0) { t.setDate(t.getDate() + 1); if (t.getDay() !== 0) n--; }
    return fmt(t);
  }
  const dayStart = (date) => workdaysUntil(date) * DAY; // 某日 08:00 的工作分钟
  function workdaysUntil(date) { // 今天到该日相隔的工作日数（今天为 0）
    const t = new Date(TODAY + "T00:00:00"), end = new Date(date + "T00:00:00"); let n = 0;
    const step = end >= t ? 1 : -1;
    while (t.getTime() !== end.getTime()) { t.setDate(t.getDate() + step); if (t.getDay() !== 0) n += step; }
    return n;
  }
  const clock = (min) => { const m = ((min % DAY) + DAY) % DAY, h = m < 240 ? 8 + m / 60 : 9 + m / 60;
    return String(Math.floor(h)).padStart(2, "0") + ":" + String(Math.round((h % 1) * 60)).padStart(2, "0"); };

  // 单位成本：钢丝＋工序（设备小时费率 × 制造费用系数 3.5，含折旧、电费、人工）
  const OVERHEAD = 3.5;
  function unitCost(code) {
    const p = P[code], mat = (p.kgPer1000 / 1000) * M[p.wire].price;
    const ops = routings[p.routing].reduce((s, op) => {
      const rate = workstations.filter((w) => w.type === op.type)[0].hourRate;
      return s + (op.min / 60) * rate / 1000;
    }, 0);
    return round2((mat + ops * OVERHEAD) * 1000) / 1000;
  }
  products.forEach((p) => { p.unitCost = unitCost(p.code); p.margin = round2(1 - p.unitCost / p.price); });
  const yieldOf = (code) => routings[P[code].routing].reduce((y, op) => y * (1 - op.loss / 100), 1);

  salesOrders.forEach((s) => {
    const p = P[s.product];
    s.amount = round2(s.qty * p.price); s.amountWithTax = round2(s.amount * 1.13);
    s.cost = round2(s.qty * p.unitCost); s.margin = round2(1 - s.cost / s.amount);
  });
  // ---------- 排程：按交期先后，每道工序在指定设备上排，取「上道完工」与「设备空出」中较晚者 ----------
  products.forEach((p) => { p.wireMm = parseFloat(p.code.split("-")[2]); });
  const freeInit = () => Object.fromEntries(workstations.map((w) => [w.id, w.status === "down" ? 360 : NOW])); // 喷丸机-1 15:00 恢复
  const free = freeInit();
  const wireLeft = Object.fromEntries(materials.map((m) => [m.code, m.stock])); // 现存可分配量
  const wireReady = (code, kg) => { // 返回原料齐套的工作分钟，并扣减可分配量
    const m = M[code];
    if (kg <= wireLeft[code]) { wireLeft[code] -= kg; return { at: NOW }; }
    if (m.arrival && kg <= wireLeft[code] + m.onOrder) { wireLeft[code] -= kg; return { at: dayStart(m.arrival), note: m.name + " 在途，" + m.arrival + " 到货" }; }
    return { at: dayStart(D(m.leadDays)), note: m.name + " 须新采购，提前期 " + m.leadDays + " 天" };
  };
  const order = workOrders.slice().sort((a, b) => SO[a.salesOrder].delivery.localeCompare(SO[b.salesOrder].delivery));
  order.forEach((w) => {
    const s = SO[w.salesOrder], p = P[s.product], route = routings[p.routing];
    w.product = s.product; w.customer = s.customer; w.delivery = s.delivery;
    w.plannedQty = Math.ceil(s.qty / yieldOf(s.product)); // 按损耗反算（同 S8 能力「损耗反算」）
    let prev = NOW, y = 1;
    if (w.done[0] < 1) {
      const need = (w.plannedQty * (1 - w.done[0]) * p.kgPer1000) / 1000, r = wireReady(p.wire, need);
      prev = r.at; w.materialNote = r.note || null;
    }
    w.operations = route.map((op, i) => {
      const ws = WS[w.ws[op.op]], done = w.done[i];
      const remain = ((w.plannedQty / 1000) * op.min * ws.speed * (1 - done)) / ws.capacity;
      y *= 1 - op.loss / 100;
      const row = { op: op.op, workstation: ws.id, done, goodQty: Math.round(w.plannedQty * done * y), remainMin: Math.round(remain) };
      if (remain > 0) {
        row.start = Math.max(free[ws.id], done > 0 ? NOW : prev);
        row.end = Math.max(row.start + remain, prev); free[ws.id] = row.start + remain; prev = row.end;
      } else { row.start = row.end = null; }
      return row;
    });
    w.finishMin = prev; w.finishDate = workDate(prev);
    w.slackDays = workdaysUntil(s.delivery) - workdaysUntil(w.finishDate);
    w.risk = w.slackDays < 0 ? "late" : w.slackDays === 0 ? "tight" : "ok";
    w.currentOp = (w.operations.find((o) => o.done < 1) || {}).op || "完工";
    s.workOrder = w.id; s.risk = w.risk; s.finishDate = w.finishDate;
  });

  // ---------- 设备负荷（未来 6 个工作日，口径同 Capacity Load：剩余工时 ÷ 可用工时）与当前在做 ----------
  const horizonMin = HORIZON_DAYS * DAY - NOW;
  workstations.forEach((ws) => {
    const ops = order.flatMap((w) => w.operations.filter((o) => o.workstation === ws.id && o.remainMin > 0).map((o) => ({ ...o, workOrder: w.id })));
    ws.backlogMin = ops.reduce((s, o) => s + o.remainMin, 0);
    ws.load = round2(ws.backlogMin / horizonMin);
    if (ws.status === "run" || ws.status === "over") ws.status = ws.load > 1 ? "over" : "run";
    const now = ops.find((o) => o.start <= NOW && o.end > NOW && o.done > 0);
    ws.current = now ? { workOrder: now.workOrder, op: now.op } : null;
    ws.queue = ops.map((o) => o.workOrder);
    ws.freeDate = workDate(free[ws.id]);
  });
  // ---------- 能不能接（CTP）：把商机插到现有排程之后，每道工序挑最早空出的同类设备 ----------
  function ctp(product, qty, wantDate) {
    const p = P[product], f = { ...free }, plannedQty = Math.ceil(qty / yieldOf(product));
    const kg = (plannedQty * p.kgPer1000) / 1000, m = M[p.wire];
    const spare = wireLeft[p.wire] + (m.arrival ? m.onOrder : 0);
    const mat = kg <= wireLeft[p.wire] ? { at: NOW, note: null }
      : kg <= spare && m.arrival ? { at: dayStart(m.arrival), note: m.name + " 用在途那批，" + m.arrival + " 到货" }
      : { at: dayStart(D(m.leadDays)), note: m.name + " 不够，须新采购 " + Math.ceil(kg - Math.max(spare, 0)) + " 千克，提前期 " + m.leadDays + " 天" };
    let prev = mat.at; const steps = [];
    routings[p.routing].forEach((op) => {
      const cands = workstations.filter((w) => w.type === op.type && (!w.maxWireMm || w.maxWireMm >= p.wireMm));
      const ws = cands.reduce((a, b) => (f[a.id] <= f[b.id] ? a : b));
      const dur = ((plannedQty / 1000) * op.min * ws.speed) / ws.capacity, start = Math.max(f[ws.id], prev);
      steps.push({ op: op.op, workstation: ws.id, waitMin: Math.round(start - prev), runMin: Math.round(dur), start: workDate(start), end: workDate(start + dur) });
      f[ws.id] = start + dur; prev = start + dur;
    });
    const finishDate = workDate(prev), slack = workdaysUntil(wantDate) - workdaysUntil(finishDate);
    const bottleneck = steps.reduce((a, b) => (b.waitMin + b.runMin > a.waitMin + a.runMin ? b : a));
    return { plannedQty, finishDate, wantDate, slackDays: slack, ok: slack >= 0, material: mat.note, bottleneck, steps };
  }
  deals.forEach((d) => { if (!["Won", "Lost"].includes(d.status)) d.ctp = ctp(d.product, d.qty, d.wantDate); d.amount = round2(d.qty * P[d.product].price); });

  // ---------- 应收与回款 ----------
  invoices.forEach((v) => {
    const c = C[v.customer];
    v.amount = round2(v.qty * P[v.product].price * 1.13);
    v.paid = round2(v.amount * v.paidRatio); v.outstanding = round2(v.amount - v.paid);
    const due = new Date(v.invoiced + "T00:00:00"); due.setDate(due.getDate() + c.termDays); v.due = fmt(due);
    v.overdueDays = v.outstanding > 0 && v.due < TODAY ? Math.round((new Date(TODAY) - new Date(v.due)) / 864e5) : 0;
  });
  customers.forEach((c) => {
    const mine = invoices.filter((v) => v.customer === c.name), open = salesOrders.filter((s) => s.customer === c.name);
    c.receivable = round2(mine.reduce((s, v) => s + v.outstanding, 0));
    c.overdue = round2(mine.filter((v) => v.overdueDays > 0).reduce((s, v) => s + v.outstanding, 0));
    c.openOrderAmount = round2(open.reduce((s, o) => s + o.amountWithTax, 0));
    c.creditUsed = round2(c.receivable + c.openOrderAmount);
    c.creditUsage = round2(c.creditUsed / c.creditLimit);
  });

  // ---------- 客户近 12 个月销售额（未税、已开票口径）与单数：逐月合计等于 monthly[].revenue、monthly[].orders ----------
  // 另起种子，不动上面 SPC 用的 rand（P1-S9-R3 第 1 步）。当月已开票的发票先落到对应客户，余额按客户等级、走势分摊；建档前的月份为 0
  const hrand = rng(2026);
  const levelWeight = { A: 3, B: 1.4, C: 0.6 }, levelActive = { A: 1, B: 0.5, C: 0.25 };
  const trendOf = { "常州弹簧厂": 0.08, "泰州弹簧厂": -0.1 }; // 情节：常州在涨（商机 087 是它的），泰州在跌、又有逾期；两家每月都有单
  const cw = Object.fromEntries(customers.map((c) => [c.name, { w: levelWeight[c.level] * (0.6 + hrand() * 0.8),
    trend: trendOf[c.name] ?? (hrand() - 0.5) * 0.08 }]));
  customers.forEach((c) => { c.history = []; });
  monthly.forEach((m, i) => {
    const fixed = {};
    invoices.filter((v) => v.invoiced.startsWith(m.month)).forEach((v) => { fixed[v.customer] = (fixed[v.customer] || 0) + v.amount / 1.13; });
    let active = customers.filter((c) => fixed[c.name] || (c.since.slice(0, 7) <= m.month && (trendOf[c.name] || hrand() < levelActive[c.level])));
    if (active.length > m.orders) active = active.sort((a, b) => (fixed[b.name] ? 1e9 : cw[b.name].w) - (fixed[a.name] ? 1e9 : cw[a.name].w)).slice(0, m.orders);
    const wt = Object.fromEntries(active.map((c) => [c.name, cw[c.name].w * Math.pow(1 + cw[c.name].trend, i - 11) * (0.85 + hrand() * 0.3)]));
    const W = Object.values(wt).reduce((a, b) => a + b, 0), rest = m.revenue - Object.values(fixed).reduce((a, b) => a + b, 0);
    const rev = Object.fromEntries(active.map((c) => [c.name, Math.round((fixed[c.name] || 0) + (rest * wt[c.name]) / W)]));
    const big = active.reduce((a, b) => (rev[b.name] > rev[a.name] ? b : a));
    rev[big.name] += m.revenue - Object.values(rev).reduce((a, b) => a + b, 0); // 取整尾差放到最大的那家
    // 单数：每家至少 1 单，余下按金额占比用最大余数法分
    const cnt = Object.fromEntries(active.map((c) => [c.name, 1])), extra = m.orders - active.length;
    const share = active.map((c) => ({ n: c.name, q: (extra * rev[c.name]) / m.revenue }));
    share.forEach((s) => { cnt[s.n] += Math.floor(s.q); });
    share.sort((a, b) => (b.q % 1) - (a.q % 1)).slice(0, m.orders - Object.values(cnt).reduce((a, b) => a + b, 0)).forEach((s) => { cnt[s.n]++; });
    customers.forEach((c) => c.history.push({ month: m.month, revenue: rev[c.name] || 0, orders: cnt[c.name] || 0 }));
  });
  customers.forEach((c) => {
    const h = c.history.map((x) => x.revenue), sum = (a) => a.reduce((s, v) => s + v, 0);
    c.yearRevenue = sum(h);
    const recent = h.slice(-3), before = h.slice(-6, -3), act = (a) => a.filter((v) => v > 0).length;
    c.trend3m = act(recent) >= 2 && act(before) >= 2 ? round2(sum(recent) / sum(before) - 1) : null; // 近 3 个月对前 3 个月；单太稀的不算
  });

  // ---------- 报价试算：金额、毛利、能不能接（ctp）、信用额度够不够；单价缺省取产品标准价，可现场改 ----------
  const yuanText = (v) => Math.round(v).toLocaleString("zh-CN") + " 元";
  function quote(customer, product, qty, wantDate, price) {
    const p = P[product], c = C[customer], unit = price > 0 ? price : p.price;
    const amount = round2(qty * unit), withTax = round2(amount * 1.13), cost = round2(qty * p.unitCost);
    const margin = round2(1 - cost / amount), plan = ctp(product, qty, wantDate);
    const creditAfter = round2(c.creditUsed + withTax), usageAfter = round2(creditAfter / c.creditLimit);
    const warnings = [];
    if (!plan.ok) warnings.push({ level: "alarm", text: "按现有排程 " + plan.finishDate + " 完工，比客户要的晚 " + -plan.slackDays + " 个工作日" });
    if (plan.material) warnings.push({ level: "wait", text: plan.material });
    if (creditAfter > c.creditLimit) warnings.push({ level: "alarm", text: "接下后信用占用 " + Math.round(usageAfter * 100) + "%，超出额度 " + yuanText(creditAfter - c.creditLimit) });
    if (c.overdue > 0) warnings.push({ level: "over", text: "该客户有逾期应收 " + yuanText(c.overdue) });
    if (margin < 0.2) warnings.push({ level: "wait", text: "毛利率 " + Math.round(margin * 100) + "%，低于 20%" });
    return { customer, product, qty, wantDate, price: unit, listPrice: p.price, discount: round2(unit / p.price - 1),
      amount, tax: round2(withTax - amount), withTax, unitCost: p.unitCost, cost, margin, ctp: plan,
      creditLimit: c.creditLimit, creditUsedBefore: c.creditUsed, creditUsageBefore: c.creditUsage, creditAfter, usageAfter,
      creditOk: creditAfter <= c.creditLimit, termDays: c.termDays, warnings };
  }

  // ---------- 补货：低于安全库存报警；库存＋在途低于再订货点则按经济订货量建议（订货成本 80、持有成本率 18%，同场景） ----------
  materials.forEach((m) => {
    m.belowSafety = m.stock < m.safety;
    m.coverDays = round2(m.stock / m.dailyUse);
    const eoq = Math.sqrt((2 * m.dailyUse * 365 * 80) / (m.price * 0.18));
    m.suggestQty = m.stock + m.onOrder < m.rop ? Math.ceil(eoq / 100) * 100 : 0;
  });

  // ---------- SPC：X̄-R 控制限（n=5：A2=0.577、D4=2.114），前 16 组算限；Cpk 用全部读数 ----------
  const gm = spcGroups.map((g) => g.readings.reduce((a, b) => a + b) / 5), gr = spcGroups.map((g) => Math.max(...g.readings) - Math.min(...g.readings));
  spcGroups.forEach((g, i) => { g.mean = +gm[i].toFixed(4); g.range = +gr[i].toFixed(4); });
  const base = 16, xbb = gm.slice(0, base).reduce((a, b) => a + b) / base, rb = gr.slice(0, base).reduce((a, b) => a + b) / base;
  const all = spcGroups.flatMap((g) => g.readings), mu = all.reduce((a, b) => a + b) / all.length, sigma = rb / 2.326;
  const spc = { ...spcSpec, groups: spcGroups, xbar: { cl: +xbb.toFixed(4), ucl: +(xbb + 0.577 * rb).toFixed(4), lcl: +(xbb - 0.577 * rb).toFixed(4) },
    range: { cl: +rb.toFixed(4), ucl: +(2.114 * rb).toFixed(4), lcl: 0 },
    cpk: round2(Math.min(spcSpec.usl - mu, mu - spcSpec.lsl) / (3 * sigma)) };
  // Nelson 第 2 条：连续 9 点在中心线同侧
  let run = 0;
  const flagged = new Set();
  spcGroups.forEach((g, i) => {
    run = g.mean > spc.xbar.cl ? Math.max(run, 0) + 1 : Math.min(run, 0) - 1;
    if (Math.abs(run) >= 9) for (let k = i - Math.abs(run) + 1; k <= i; k++) flagged.add(k);
  });
  spc.violations = [...flagged].sort((a, b) => a - b).map((k) => ({ group: k + 1, rule: 2, text: "连续 9 组在中心线同侧" }));
  spcGroups.forEach((g, i) => { g.flagged = flagged.has(i); });
  // ---------- 汇总指标（驾驶舱、销售工作台、手机端共用） ----------
  const last = monthly[monthly.length - 1], prevM = monthly[monthly.length - 2];
  const kpi = {
    wipOrders: workOrders.length,
    riskOrders: workOrders.filter((w) => w.risk !== "ok").length,
    lateOrders: workOrders.filter((w) => w.risk === "late").length,
    openOrderAmount: round2(salesOrders.reduce((s, o) => s + o.amount, 0)),
    monthRevenue: last.revenue, monthRevenueDelta: round2(last.revenue / prevM.revenue - 1),
    grossMargin: last.grossMargin, onTimeRate: last.onTimeRate, defectRate: last.defectRate,
    materialValue: round2(materials.reduce((s, m) => s + m.stock * m.price, 0)),
    receivable: round2(invoices.reduce((s, v) => s + v.outstanding, 0)),
    overdue: round2(invoices.filter((v) => v.overdueDays > 0).reduce((s, v) => s + v.outstanding, 0)),
    pipeline: round2(deals.filter((d) => d.ctp).reduce((s, d) => s + d.amount, 0)),
    weightedPipeline: round2(deals.filter((d) => d.ctp).reduce((s, d) => s + (d.amount * d.probability) / 100, 0)),
    avgLoad: round2(workstations.reduce((s, w) => s + w.load, 0) / workstations.length),
    // 商机漏斗：到达过该阶段的商机数（赢单算走完全程，输单不计），另记当前停在该阶段的张数与金额
    funnel: ["Qualification", "Demo/Making", "Proposal/Quotation", "Negotiation", "Ready to Close", "Won"].map((st, i, arr) => {
      const at = deals.filter((x) => x.status === st), reached = deals.filter((x) => x.status !== "Lost" && arr.indexOf(x.status) >= i);
      return { status: st, name: dealStatus[st], reached: reached.length, count: at.length, amount: round2(at.reduce((s, x) => s + x.amount, 0)) };
    }),
    // 应收账龄（含税未收）与近期开票回款
    aging: {
      buckets: [["未到期", 0, 0], ["逾期 1～30 天", 1, 30], ["逾期 31～60 天", 31, 60], ["逾期 60 天以上", 61, 1e9]].map(([name, lo, hi]) => {
        const vs = invoices.filter((v) => v.outstanding > 0 && v.overdueDays >= lo && v.overdueDays <= hi);
        return { name, count: vs.length, amount: round2(vs.reduce((s, v) => s + v.outstanding, 0)) };
      }),
      invoiced: round2(invoices.reduce((s, v) => s + v.amount, 0)),
      collected: round2(invoices.reduce((s, v) => s + v.paid, 0)),
    },
    alerts: [
      ...materials.filter((m) => m.belowSafety).map((m) => ({ level: "alarm", text: m.name + " 低于安全库存（" + m.stock + "／" + m.safety + " 千克）" })),
      ...materials.filter((m) => m.suggestQty).map((m) => ({ level: "wait", text: m.name + " 建议补货 " + m.suggestQty + " 千克" })),
      ...(spc.violations.length ? [{ level: "alarm", text: spc.workstation + " " + spc.param + " 判异：" + spc.violations[0].text }] : []),
      ...workstations.filter((w) => w.status === "over").map((w) => ({ level: "over", text: w.id + " 未来 6 天负荷 " + Math.round(w.load * 100) + "%" })),
      ...workOrders.filter((w) => w.risk === "late").map((w) => ({ level: "alarm", text: w.salesOrder + " 预计 " + w.finishDate + " 完工，晚于交期 " + w.delivery })),
    ],
  };

  window.SC_DATA = {
    today: TODAY, nowClock: clock(NOW), company, roles, statusText, statusNote,
    workstations, routings, products, materials, suppliers, customers,
    leads, leadStatus, deals, dealStatus, salesOrders, workOrders, invoices, monthly, spc, kpi,
    ctp, // 现场改数量、交期再算：SC_DATA.ctp("SPR-C-3.0-23-50", 40000, "2026-11-16")
    quote, // 报价试算：SC_DATA.quote("常州弹簧厂", "SPR-C-3.0-23-50", 40000, "2026-11-16", 0.85)
    get: { product: (c) => P[c], material: (c) => M[c], workstation: (id) => WS[id], customer: (n) => C[n], salesOrder: (id) => SO[id] },
  };
})();
