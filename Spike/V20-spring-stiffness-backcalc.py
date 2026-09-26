# -*- coding: utf-8 -*-
"""
V20 - Spring parameter back-calculation probe.  P1-S3-R1-A / IM-001.

WHAT THIS IS FOR
----------------
The compression / tension parameter tables in
  docs/01-XXXX/S02-XXXX/R01-XXXX/P1-S2-R1-A<spring industry data>.md  sections 1.3 / 1.4
are B-grade material: a third party's OCR transcription of GB/T 2089-2009 and
GB/T 2088-2009, NOT the standard text.  The same source page contradicts itself
on three rows.  This script gives every demo row an independent second value
from first principles, and adjudicates the three conflicts.

FORMULAS (round-wire cylindrical helical spring)
------------------------------------------------
  k     = G * d^4 / (8 * D^3 * n)              stiffness N/mm, D = MEAN diameter
  F     = k * f                                compression: load = k * deflection
  F1    = F0 + k * f1                          tension: work load = initial tension + k*f1
  tau   = 8 * F * D / (pi * d^3)               torsional shear stress, MPa
  F     = tau * pi * d^3 / (8 * D)             the same, solved for load
  m1000 = 1000 * rho * (pi*d^2/4) * (pi*D*(n+n2))     kg per 1000 pieces

CONSTANTS
---------
  G   = 79000 MPa  carbon spring steel wire.  Sensitivity run at 78500 / 81000.
  G   = 71000 MPa  austenitic stainless spring wire (for comparison only).
  rho = 7.85e-3 g/mm^3
  n2  = 2 support coils (both ends closed and ground, type Y I)

Output is deliberately ASCII-only: the Windows console here is GBK.

RUN:  python Spike/V20-spring-stiffness-backcalc.py
"""

import math

G_CARBON = 79000.0
G_LO = 78500.0
G_HI = 81000.0
G_SS = 71000.0
RHO = 7.85e-3
N2_END = 2.0

# ------------------------------------------------------------------ source data
# Compression, GB/T 2089 transcription, n = 6.5 column.
#   Fn_parsed = value obtained by parsing the page's HTML table (upstream adopted this)
#   Fn_digest = value shown in the search-engine digest of the SAME page (conflicts)
N_COMP = 6.5
COMP = [
    # d,     D,   Fn_parsed,     L,    f,  k_tab,  w1000,  Fn_digest
    (0.5,   4.0,      11.0,   14.0,  7.3,    1.5,    0.16,   None),
    (0.8,   5.0,      32.0,   15.0,  6.4,    3.8,    0.52,   None),
    (1.0,   6.0,      51.0,   18.0,  7.3,    7.0,    0.98,   None),
    (1.2,   8.0,      65.0,   24.0, 11.0,    6.2,    1.88,   None),
    (1.6,  10.0,     116.0,   28.0, 12.0,    7.6,    4.18,   None),
    (2.0,  12.0,     179.0,   32.0, 13.0,   14.0,    7.84,   None),
    (2.5,  16.0,     255.0,   40.0, 18.0,   14.0,   16.34,   None),
    (3.0,  20.0,     333.0,   50.0, 22.0,   15.0,   29.42,   None),
    (4.0,  25.0,     611.0,   60.0, 24.0,   25.0,   65.37,   None),
    (5.0,  30.0,     962.0,   75.0, 27.0,   35.0,  122.60,  661.0),   # conflict 1
    (6.0,  40.0,    1204.0,   95.0, 39.0,   31.0,  235.30,   None),
    (8.0,  50.0,    2203.0,  115.0, 44.0,   50.0,  523.00, 1154.0),   # conflict 2
    (10.0, 60.0,    3454.0,  140.0, 49.0,   70.0,  980.50,   None),
    (12.0, 70.0,    4922.0,  180.0, 54.0,   92.0, 1647.00, 3441.0),   # conflict 3
    (16.0, 90.0,   10575.0,  240.0, 77.0,  137.0, 3765.00,   None),
]

# Tension, GB/T 2088 transcription, n = 10.5 column.
N_TENS = 10.5
TENS = [
    # d,     D,     F0,     F1,      H,   f1,  k_tab
    (0.5,   4.0,    0.9,   10.8,   5.8, 10.8,   0.92),
    (0.8,   6.0,    2.6,   26.9,   9.2, 13.7,   1.78),
    (1.0,   8.0,    3.6,   38.5,  11.5, 19.0,   1.84),
    (1.2,   8.0,    7.5,   64.8,  13.8, 15.0,   3.81),
    (1.6,  12.0,   10.5,   97.0,  18.4, 24.2,   3.57),
    (2.0,  12.0,   25.7,  179.0,  23.0, 17.6,   8.71),
    (2.5,  16.0,   35.3,  255.0,  28.8, 24.5,   8.97),
    (3.0,  20.0,   46.8,  333.0,  34.5, 30.1,   9.52),
    (4.0,  25.0,   94.7,  611.0,  46.0, 33.5,  15.40),
    (5.0,  25.0,  232.0, 1154.0,  57.5, 24.5,  37.60),
]

# The five rows chosen for the demo.
DEMO_COMP = [(3.0, 20.0), (5.0, 30.0), (8.0, 50.0)]
DEMO_TENS = [(3.0, 20.0), (5.0, 25.0)]

DISPUTED_D = {5.0, 8.0, 12.0}          # compression rows with an OCR conflict
TREND_BREAK_D = 16.0                   # row that leaves the tau(d) trend, see part 5


# ------------------------------------------------------------------- primitives
def k_of(G, d, D, n):
    return G * d ** 4 / (8.0 * D ** 3 * n)


def tau_of(F, d, D):
    return 8.0 * F * D / (math.pi * d ** 3)


def F_of_tau(tau, d, D):
    return tau * math.pi * d ** 3 / (8.0 * D)


def w1000_of(d, D, n, n2=N2_END):
    """kg per 1000 pieces."""
    area = math.pi * d ** 2 / 4.0
    wire_len = math.pi * D * (n + n2)
    return RHO * area * wire_len          # g per piece == kg per 1000 pieces


def dev(val, ref):
    return (val - ref) / ref * 100.0


def rule(title):
    print("")
    print("=" * 78)
    print(title)
    print("=" * 78)


def comp_row(d, D):
    return [r for r in COMP if abs(r[0] - d) < 1e-9 and abs(r[1] - D) < 1e-9][0]


def tens_row(d, D):
    return [r for r in TENS if abs(r[0] - d) < 1e-9 and abs(r[1] - D) < 1e-9][0]


# ============================================================== 1. what is "D"?
rule("PART 1.  IS THE TABLE COLUMN 'D' THE MEAN DIAMETER OR THE OUTER DIAMETER?")
print("The stiffness formula is very sensitive to D (cubed).  Compute k both ways")
print("and see which reproduces the table's own stiffness column.")
print("")
print("%5s %6s %8s %10s %8s %10s %8s"
      % ("d", "D", "k_tab", "k(D=mean)", "dev%", "k(D-d)", "dev%"))
e_mean, e_outer = [], []
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    km = k_of(G_CARBON, d, D, N_COMP)
    ko = k_of(G_CARBON, d, D - d, N_COMP)
    e_mean.append(abs(dev(km, k_tab)))
    e_outer.append(abs(dev(ko, k_tab)))
    print("%5.1f %6.1f %8.2f %10.2f %8.1f %10.2f %8.1f"
          % (d, D, k_tab, km, dev(km, k_tab), ko, dev(ko, k_tab)))
print("")
print("mean |dev| treating D as the MEAN  diameter : %6.2f %%"
      % (sum(e_mean) / len(e_mean)))
print("mean |dev| treating D as the OUTER diameter : %6.2f %%"
      % (sum(e_outer) / len(e_outer)))
print("")
print("Independent second test - the 'weight per 1000 pieces' column, which also")
print("depends on D (linearly, through the developed wire length):")
print("%5s %6s %10s %12s %8s %12s %8s"
      % ("d", "D", "w1000_tab", "w(D=mean)", "dev%", "w(D-d)", "dev%"))
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    wm = w1000_of(d, D, N_COMP)
    wo = w1000_of(d, D - d, N_COMP)
    print("%5.1f %6.1f %10.2f %12.2f %8.1f %12.2f %8.1f"
          % (d, D, w, wm, dev(wm, w), wo, dev(wo, w)))


# ========================================================== 2. G sensitivity run
rule("PART 2.  SENSITIVITY OF THE ANSWER TO THE CHOICE OF G")
print("Carbon spring steel wire is quoted at 78500 - 81000 MPa.  Show what the")
print("spread does to the five demo rows, so the choice can be justified.")
print("")
print("%-24s %8s %10s %10s %10s %9s"
      % ("row", "k_tab", "k@78500", "k@79000", "k@81000", "best"))
for d, D in DEMO_COMP:
    k_tab = comp_row(d, D)[5]
    cands = [(abs(dev(k_of(g, d, D, N_COMP), k_tab)), g)
             for g in (G_LO, G_CARBON, G_HI)]
    print("%-24s %8.2f %10.2f %10.2f %10.2f %9.0f"
          % ("comp d=%.1f/D=%.0f" % (d, D), k_tab,
             k_of(G_LO, d, D, N_COMP), k_of(G_CARBON, d, D, N_COMP),
             k_of(G_HI, d, D, N_COMP), min(cands)[1]))
for d, D in DEMO_TENS:
    k_tab = tens_row(d, D)[6]
    cands = [(abs(dev(k_of(g, d, D, N_TENS), k_tab)), g)
             for g in (G_LO, G_CARBON, G_HI)]
    print("%-24s %8.2f %10.2f %10.2f %10.2f %9.0f"
          % ("tens d=%.1f/D=%.0f" % (d, D), k_tab,
             k_of(G_LO, d, D, N_TENS), k_of(G_CARBON, d, D, N_TENS),
             k_of(G_HI, d, D, N_TENS), min(cands)[1]))
print("")
print("Whole-table mean |dev| of k at each G (compression, n=6.5):")
for g in (G_LO, G_CARBON, G_HI):
    errs = [abs(dev(k_of(g, r[0], r[1], N_COMP), r[5])) for r in COMP]
    print("   G = %6.0f  ->  %5.2f %%" % (g, sum(errs) / len(errs)))
print("")
print("The same, EXCLUDING the two rows whose k cell is corrupt (d=0.8, d=1.6;")
print("proven in part 4B below).  Those two carry a 31%% error each and swamp the")
print("comparison, so the clean subset is what should decide the G value:")
BAD_K_D = {0.8, 1.6}
for g in (G_LO, G_CARBON, G_HI):
    errs = [abs(dev(k_of(g, r[0], r[1], N_COMP), r[5]))
            for r in COMP if r[0] not in BAD_K_D]
    print("   G = %6.0f  ->  %5.2f %%   (max %5.2f %%)"
          % (g, sum(errs) / len(errs), max(errs)))
print("")
print("Tension table (n=10.5) has no corrupt k cell, so it is a clean second vote:")
for g in (G_LO, G_CARBON, G_HI):
    errs = [abs(dev(k_of(g, r[0], r[1], N_TENS), r[6])) for r in TENS]
    print("   G = %6.0f  ->  %5.2f %%   (max %5.2f %%)"
          % (g, sum(errs) / len(errs), max(errs)))
print("")
print("Stainless comparison (NOT used for the demo rows - see part 4):")
for d, D in DEMO_COMP:
    kc = k_of(G_CARBON, d, D, N_COMP)
    ks = k_of(G_SS, d, D, N_COMP)
    print("   comp d=%.1f/D=%.0f : carbon k=%7.2f   stainless k=%7.2f  (%+.1f%%)"
          % (d, D, kc, ks, dev(ks, kc)))


# ============================================= 3. full row-by-row recheck, both
rule("PART 3A.  COMPRESSION TABLE ROW BY ROW  (n=6.5, G=79000, D=mean)")
print("%5s %6s %9s %8s %6s %9s %8s %9s %8s %9s"
      % ("d", "D", "Fn_tab", "k_tab", "f_tab", "k_calc", "dev_k%",
         "F_calc", "dev_F%", "tau(Fn)"))
tau_series = []
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    kc = k_of(G_CARBON, d, D, N_COMP)
    Fc = kc * f
    t = tau_of(Fn, d, D)
    tau_series.append((d, D, t))
    print("%5.1f %6.1f %9.1f %8.2f %6.1f %9.2f %8.1f %9.1f %8.1f %9.0f"
          % (d, D, Fn, k_tab, f, kc, dev(kc, k_tab), Fc, dev(Fc, Fn), t))

rule("PART 3B.  TENSION TABLE ROW BY ROW  (n=10.5, G=79000, F1 = F0 + k*f1)")
print("%5s %6s %7s %8s %7s %6s %9s %8s %9s %9s %8s"
      % ("d", "D", "F0", "F1_tab", "k_tab", "f1", "k_calc", "dev_k%",
         "F1_calc", "dev_F1%", "tau(F1)"))
for d, D, F0, F1, H, f1, k_tab in TENS:
    kc = k_of(G_CARBON, d, D, N_TENS)
    F1c = F0 + kc * f1
    print("%5.1f %6.1f %7.1f %8.1f %7.2f %6.1f %9.2f %8.1f %9.1f %9.1f %8.0f"
          % (d, D, F0, F1, k_tab, f1, kc, dev(kc, k_tab),
             F1c, dev(F1c, F1), tau_of(F1, d, D)))
print("")
print("Control: same rows with F0 dropped (F1 = k*f1 only).  If the deviation")
print("gets worse, the table's F1 genuinely includes the initial tension F0.")
for d, D, F0, F1, H, f1, k_tab in TENS:
    kc = k_of(G_CARBON, d, D, N_TENS)
    print("   d=%4.1f/D=%4.0f  k*f1 = %8.1f   vs F1_tab = %8.1f   dev %+7.1f %%"
          % (d, D, kc * f1, F1, dev(kc * f1, F1)))
print("")
print("Control: is H really the body length (n*d), i.e. loops excluded?")
for d, D, F0, F1, H, f1, k_tab in TENS:
    print("   d=%4.1f  H_tab = %6.1f   n*d = %6.2f   dev %+7.1f %%"
          % (d, H, N_TENS * d, dev(N_TENS * d, H)))


# ================================== 4. the tau test of the "Fn vs n" assertion
rule("PART 4.  TEST OF THE ASSERTION 'Fn DEPENDS ONLY ON d AND D, NOT ON n'")
print("Argument under test.  If Fn is set by an allowable shear stress, then")
print("    Fn = tau_allow * pi * d^3 / (8 * D)")
print("which contains no n at all - so the assertion follows.  The assertion is")
print("therefore self-consistent IF AND ONLY IF the tau implied by the table is")
print("a smooth function of d alone, with D dropping out.  D ranges 4..90 mm")
print("across these rows, so that is a real test, not a tautology.")
print("")
print("%5s %6s %7s %10s %14s" % ("d", "D", "D/d", "tau(MPa)", "delta_vs_prev"))
prev = None
for d, D, t in tau_series:
    delta = "-" if prev is None else "%+.0f" % (t - prev)
    print("%5.1f %6.1f %7.2f %10.0f %14s" % (d, D, D / d, t, delta))
    prev = t
print("")
body = [t for d, D, t in tau_series if d <= 12.0]
mono = all(body[i] > body[i + 1] for i in range(len(body) - 1))
print("d = 0.5 .. 12 : strictly decreasing in d = %s   (%.0f -> %.0f MPa)"
      % (mono, body[0], body[-1]))
print("This is exactly the shape of the allowable-stress-vs-wire-diameter curve")
print("(thinner drawn wire is stronger), which is what the mechanism predicts.")
print("")
print("Rows that share a d but differ in D, across the two tables - tau must match")
print("if tau really is a function of d alone:")
pairs = [
    ("comp d=3.0/D=20", tau_of(333.0, 3.0, 20.0)),
    ("tens d=3.0/D=20", tau_of(333.0, 3.0, 20.0)),
    ("comp d=4.0/D=25", tau_of(611.0, 4.0, 25.0)),
    ("tens d=4.0/D=25", tau_of(611.0, 4.0, 25.0)),
    ("comp d=5.0/D=30", tau_of(962.0, 5.0, 30.0)),
    ("tens d=5.0/D=25", tau_of(1154.0, 5.0, 25.0)),
]
for name, t in pairs:
    print("   %-18s tau = %6.1f MPa" % (name, t))
print("")
print("   NOTE the last pair: d=5 at TWO DIFFERENT D, in TWO DIFFERENT tables,")
print("   both land on the same tau.  D cancels exactly as the mechanism says.")
print("")
tb = [t for d, D, t in tau_series if abs(d - TREND_BREAK_D) < 1e-9][0]
print("One row breaks the trend: d=%.0f/D=90 gives tau = %.0f MPa, ABOVE the"
      % (TREND_BREAK_D, tb))
print("d=10 and d=12 values (528, 508).  Its own k/f/Fn triple is self-consistent")
print("(see part 3A), so this is not an OCR slip in Fn - it points at a different")
print("allowable-stress basis for that size, i.e. hot-coiled alloy steel rather")
print("than cold-drawn carbon wire.  Flagged as INFERRED, and that row is not")
print("used for the demo or for any trend fit below.")


# ================================================ 5. adjudicate the 3 conflicts
rule("PART 5.  ADJUDICATION OF THE THREE OCR CONFLICTS")

pool = [(d, t) for d, D, t in tau_series
        if d not in DISPUTED_D and abs(d - TREND_BREAK_D) > 1e-9]


def tau_trend(d_target):
    """
    Estimate tau_allow(d) from the undisputed rows only.
    Log-log interpolation between the two nearest neighbours; if the target is
    above every neighbour, extrapolate along the last two.  A single global
    power law does NOT fit this curve (it flattens), hence local fitting.
    """
    pts = sorted(pool)
    lo = [p for p in pts if p[0] < d_target]
    hi = [p for p in pts if p[0] > d_target]
    if lo and hi:
        (d1, t1), (d2, t2) = lo[-1], hi[0]
        mode = "interp %.1f-%.1f" % (d1, d2)
    elif len(lo) >= 2:
        (d1, t1), (d2, t2) = lo[-2], lo[-1]
        mode = "extrap %.1f-%.1f" % (d1, d2)
    else:
        return None, "n/a"
    slope = (math.log(t2) - math.log(t1)) / (math.log(d2) - math.log(d1))
    est = math.exp(math.log(t1) + slope * (math.log(d_target) - math.log(d1)))
    return est, mode


verdicts = []
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    if dg is None:
        continue
    kc = k_of(G_CARBON, d, D, N_COMP)
    t_fit, mode = tau_trend(d)
    print("-" * 78)
    print("comp d=%.1f / D=%.0f    candidates:  parsed = %.0f N     digest = %.0f N"
          % (d, D, Fn, dg))
    print("   table's own k = %.2f,  back-calculated k = %.2f  (dev %+.1f%%),  f = %.1f"
          % (k_tab, kc, dev(kc, k_tab), f))
    print("")
    print("   test A  table k   * table f   = %8.0f N" % (k_tab * f))
    print("           |dev|  parsed %6.1f %%     digest %6.1f %%"
          % (abs(dev(Fn, k_tab * f)), abs(dev(dg, k_tab * f))))
    print("   test B  calc  k   * table f   = %8.0f N" % (kc * f))
    print("           |dev|  parsed %6.1f %%     digest %6.1f %%"
          % (abs(dev(Fn, kc * f)), abs(dev(dg, kc * f))))
    print("   test C  tau_allow(d) from undisputed rows (%s) = %.0f MPa"
          % (mode, t_fit))
    print("           -> F = %8.0f N" % F_of_tau(t_fit, d, D))
    print("           tau implied by parsed %7.0f N = %6.0f MPa  (dev %+6.1f %%)"
          % (Fn, tau_of(Fn, d, D), dev(tau_of(Fn, d, D), t_fit)))
    print("           tau implied by digest %7.0f N = %6.0f MPa  (dev %+6.1f %%)"
          % (dg, tau_of(dg, d, D), dev(tau_of(dg, d, D), t_fit)))
    win_a = "parsed" if abs(dev(Fn, k_tab * f)) < abs(dev(dg, k_tab * f)) else "digest"
    win_b = "parsed" if abs(dev(Fn, kc * f)) < abs(dev(dg, kc * f)) else "digest"
    win_c = ("parsed"
             if abs(dev(tau_of(Fn, d, D), t_fit)) < abs(dev(tau_of(dg, d, D), t_fit))
             else "digest")
    print("")
    print("   A -> %s     B -> %s     C -> %s     VERDICT: %s"
          % (win_a, win_b, win_c,
             "PARSED (adopt %.0f N)" % Fn
             if win_a == win_b == win_c == "parsed" else "SPLIT - inspect"))
    verdicts.append((d, D, win_a, win_b, win_c))
print("-" * 78)
print("all three tests agree on 'parsed' for every disputed row: %s"
      % all(a == b == c == "parsed" for _d, _D, a, b, c in verdicts))


# ============================================ 6. where do the digests come from
rule("PART 6.  PROVENANCE OF THE DIGEST NUMBERS")
print("Hypothesis from the upstream note: the digest values are row-misaligned,")
print("i.e. each is some OTHER row's load.  Two tests.")
print("")
print("Test 1 - nearest value anywhere in either table:")
allvals = [("comp d=%.1f/D=%.0f Fn" % (r[0], r[1]), r[2]) for r in COMP]
allvals += [("tens d=%.1f/D=%.0f F1" % (r[0], r[1]), r[3]) for r in TENS]
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    if dg is None:
        continue
    near = sorted(allvals, key=lambda p: abs(p[1] - dg))[:3]
    print("   digest %7.0f  (claimed for comp d=%.1f/D=%.0f):" % (dg, d, D))
    for name, v in near:
        flag = "   <== EXACT" if abs(v - dg) < 1e-9 else ""
        print("        %-22s %9.1f   delta %+8.1f%s" % (name, v, v - dg, flag))
print("")
print("Test 2 - coherence.  If the digest set were a real load series from some")
print("other column, its implied tau would still have to track tau(d).")
print("%28s %10s" % ("", "tau(MPa)"))
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    if dg is None:
        continue
    print("   digest  d=%4.1f/D=%4.0f -> %6.0f N %10.0f" % (d, D, dg, tau_of(dg, d, D)))
dt = [tau_of(r[7], r[0], r[1]) for r in COMP if r[7] is not None]
print("   digest set tau: %s" % ", ".join("%.0f" % x for x in dt))
print("   monotone in d?  %s" % all(dt[i] > dt[i + 1] for i in range(len(dt) - 1)))
print("   undisputed tau: %.0f -> %.0f, monotone %s"
      % (body[0], body[-1], mono))
print("")
print("So the digest set is not a coherent load series under any n, while the")
print("parsed set is.  The digest column is corrupt, not an alternative reading.")


# ================================================== 7. weight and UOM factors
rule("PART 7.  WEIGHT PER 1000 PIECES -> THE ERPNext UOM CONVERSION FACTOR")
print("m1000 = 1000 * rho * (pi*d^2/4) * (pi*D*(n+n2)),  rho=%.5f g/mm^3, n2=%.0f"
      % (RHO, N2_END))
print("")
print("%5s %6s %11s %11s %8s %13s"
      % ("d", "D", "w1000_tab", "w1000_calc", "dev%", "kg_per_piece"))
for d, D, Fn, L, f, k_tab, w, dg in COMP:
    wc = w1000_of(d, D, N_COMP)
    print("%5.1f %6.1f %11.2f %11.2f %8.1f %13.5f"
          % (d, D, w, wc, dev(wc, w), w / 1000.0))
print("")
print("How many support coils best fit the table?  (whole-table mean |dev|)")
for n2 in (0.0, 1.0, 1.5, 2.0, 2.5, 3.0):
    errs = [abs(dev(w1000_of(r[0], r[1], N_COMP, n2), r[6])) for r in COMP]
    print("   n2 = %4.1f  ->  %6.2f %%" % (n2, sum(errs) / len(errs)))
print("")
print("Tension springs: the transcribed table has NO weight column.  Estimate the")
print("body, then add an allowance for the two loops.  The allowance is INFERRED")
print("(no standard obtained), so it is flagged, not asserted:")
for d, D in DEMO_TENS:
    print("   tens d=%.1f/D=%.0f  body only %8.2f kg/1000   +2 coils %8.2f kg/1000"
          % (d, D, w1000_of(d, D, N_TENS, 0.0), w1000_of(d, D, N_TENS, 2.0)))


# ================================================== 8. the five demo rows
rule("PART 8.  THE FIVE DEMO ROWS - FINAL NUMBERS")
print("%-26s %8s %9s %8s %8s %9s %8s %11s %11s"
      % ("row", "F_tab", "F_calc", "dev%", "k_tab", "k_calc", "dev%",
         "kg/1000", "kg/piece"))
for d, D in DEMO_COMP:
    _d, _D, Fn, L, f, k_tab, w, dg = comp_row(d, D)
    kc = k_of(G_CARBON, d, D, N_COMP)
    print("%-26s %8.0f %9.0f %8.1f %8.2f %9.2f %8.1f %11.2f %11.5f"
          % ("comp %.1fx%.0f n=6.5" % (d, D), Fn, kc * f, dev(kc * f, Fn),
             k_tab, kc, dev(kc, k_tab), w, w / 1000.0))
for d, D in DEMO_TENS:
    _d, _D, F0, F1, H, f1, k_tab = tens_row(d, D)
    kc = k_of(G_CARBON, d, D, N_TENS)
    wt = w1000_of(d, D, N_TENS, 2.0)
    print("%-26s %8.0f %9.0f %8.1f %8.2f %9.2f %8.1f %11.2f %11.5f"
          % ("tens %.1fx%.0f n=10.5" % (d, D), F1, F0 + kc * f1,
             dev(F0 + kc * f1, F1), k_tab, kc, dev(kc, k_tab), wt, wt / 1000.0))
print("")
print("The 'kg/1000' column IS the BOM component quantity, because the demo BOM")
print("is built on an output quantity of 1000 pieces.")
print("")
print("Wire items needed (one per distinct d):  %s"
      % ", ".join("d=%.1f" % x for x in sorted({d for d, D in DEMO_COMP + DEMO_TENS})))
print("Rows per wire:")
for dw in sorted({d for d, D in DEMO_COMP + DEMO_TENS}):
    rows = (["comp %.1fx%.0f" % (d, D) for d, D in DEMO_COMP if d == dw]
            + ["tens %.1fx%.0f" % (d, D) for d, D in DEMO_TENS if d == dw])
    print("   d=%.1f : %s" % (dw, ", ".join(rows)))
print("")
print("Total wire kg per 1000 pieces of each demo product, i.e. the five BOM lines:")
tot = 0.0
for d, D in DEMO_COMP:
    w = comp_row(d, D)[6]
    tot += w
    print("   comp %.1fx%.0f  ->  %8.2f kg of d=%.1f wire" % (d, D, w, d))
for d, D in DEMO_TENS:
    w = w1000_of(d, D, N_TENS, 2.0)
    tot += w
    print("   tens %.1fx%.0f  ->  %8.2f kg of d=%.1f wire  (loop allowance INFERRED)"
          % (d, D, w, d))
print("   %s" % ("-" * 52))
print("   all five, 1000 pcs each      %8.2f kg" % tot)

print("")
print("=" * 78)
print("PART 9.  ITEM-CODE NAMING: THE TABLE'S D IS *MEAN*, THE DEMO CODE USES *OUTER*")
print("=" * 78)
print("The existing demo item code is SPR-C-2.0-16-50, and the demo's own weight")
print("math reads that 16 as the OUTER diameter (D_mean = 16 - 2.0 = 14).  Part 1")
print("proved the source table's D column is the MEAN diameter.  So the same slot")
print("in a code means two different things.  Show the size of the mistake if the")
print("table's mean D were pasted into the code slot and then read back as outer.")
print("")
print(" spec (table, D=mean)   D_outer   if D_mean misread as outer -> D_m'   k error%")
for d, D in DEMO_COMP:
    d_out = D + d
    d_wrong = D - d
    k_ok = k_of(G_CARBON, d, D, N_COMP)
    k_wrong = k_of(G_CARBON, d, d_wrong, N_COMP)
    print("  comp d=%.1f D_mean=%-5.0f  %6.1f     %6.1f              %+8.1f"
          % (d, D, d_out, d_wrong, dev(k_wrong, k_ok)))
for d, D in DEMO_TENS:
    d_out = D + d
    d_wrong = D - d
    k_ok = k_of(G_CARBON, d, D, N_TENS)
    k_wrong = k_of(G_CARBON, d, d_wrong, N_TENS)
    print("  tens d=%.1f D_mean=%-5.0f  %6.1f     %6.1f              %+8.1f"
          % (d, D, d_out, d_wrong, dev(k_wrong, k_ok)))
print("")
print("So the code slot must be labelled.  Recommended codes carry the OUTER")
print("diameter (keeps the existing SPR-C-2.0-16-50 convention) with free length:")
for d, D in DEMO_COMP:
    r = comp_row(d, D)
    print("   SPR-C-%.1f-%.0f-%.0f    (d=%.1f, D_outer=%.0f, D_mean=%.0f, L0=%.0f)"
          % (d, D + d, r[3], d, D + d, D, r[3]))
for d, D in DEMO_TENS:
    r = tens_row(d, D)
    print("   SPR-T-%.1f-%.0f-%.0f    (d=%.1f, D_outer=%.0f, D_mean=%.0f, H0=%.1f)"
          % (d, D + d, r[4], d, D + d, D, r[4]))
