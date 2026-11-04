/* 主题切换与 ECharts 主题。
   用法：页面 <html data-theme="dark|light"> 写默认主题；地址栏 ?theme=light 可覆盖。
   图表用 SC.chart(el, optionFn) 建，切主题时自动按新配色重画。 */
(function () {
  const root = document.documentElement;
  const qs = new URLSearchParams(location.search).get("theme");
  if (qs === "dark" || qs === "light") root.dataset.theme = qs;
  if (!root.dataset.theme) root.dataset.theme = "light";

  const charts = [];
  const css = (name) => getComputedStyle(root).getPropertyValue(name).trim();

  function echartsTheme() {
    const text = css("--text-2"), border = css("--border");
    const axis = { axisLine: { lineStyle: { color: border } }, axisTick: { show: false },
      axisLabel: { color: text }, splitLine: { lineStyle: { color: border, type: "dashed" } } };
    return {
      color: ["--c1", "--c2", "--c3", "--c4", "--c5", "--c6"].map(css),
      backgroundColor: "transparent",
      textStyle: { fontFamily: css("--font-sans"), color: css("--text") },
      legend: { textStyle: { color: text } },
      tooltip: { backgroundColor: css("--surface"), borderColor: border, textStyle: { color: css("--text") } },
      categoryAxis: axis, valueAxis: axis, timeAxis: axis,
    };
  }

  function render(item) {
    if (item.inst) item.inst.dispose();
    echarts.registerTheme("sc", echartsTheme());
    item.inst = echarts.init(item.el, "sc");
    item.inst.setOption(item.optionFn(SC));
  }

  const SC = window.SC = {
    css,
    get theme() { return root.dataset.theme; },
    chart(el, optionFn) { const item = { el, optionFn }; charts.push(item); render(item); return item; },
    setTheme(t) { root.dataset.theme = t; charts.forEach(render); },
    toggleTheme() { SC.setTheme(SC.theme === "dark" ? "light" : "dark"); },
    yuan: (v) => "¥" + Number(v).toLocaleString("zh-CN", { maximumFractionDigits: 0 }),
    pct: (v, d = 1) => (v * 100).toFixed(d) + "%",
  };
  window.addEventListener("resize", () => charts.forEach((c) => c.inst && c.inst.resize()));
})();
