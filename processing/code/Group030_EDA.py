"""EDA code exported cell-by-cell from Group030_EDA.ipynb."""

from pathlib import Path
import os
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter, MaxNLocator
from IPython.display import Image, display

GROUP_ID = "Group030"
BASE = Path.cwd()
if (BASE / "processing" / "outputs").is_dir():
    OUTPUT_DIR = BASE / "processing" / "outputs"
    FIGURE_DIR = BASE / "processing" / "figures"
elif (BASE.parent.parent / "processing" / "outputs").is_dir():
    BASE = BASE.parent.parent
    OUTPUT_DIR = BASE / "processing" / "outputs"
    FIGURE_DIR = BASE / "processing" / "figures"
else:
    OUTPUT_DIR = BASE / "outputs"
    FIGURE_DIR = BASE / "figures"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
DATA = str(OUTPUT_DIR)
FIGS = str(FIGURE_DIR)
print("Reading standardised tables from:", os.path.relpath(OUTPUT_DIR, Path.cwd()))
print("Writing assessed figures to:", os.path.relpath(FIGURE_DIR, Path.cwd()))

# ----------------------------------------------------------------- styling ---
INK = "#1a1a1a"
MUTED = "#6b7280"
GRID = "#e5e7eb"
BLUE = "#2563eb"
TEAL = "#0d9488"
AMBER = "#d97706"
ROSE = "#e11d48"
VIOLET = "#7c3aed"
SLATE = "#475569"
SEQ = [BLUE, TEAL, AMBER, ROSE, VIOLET, SLATE, "#0891b2", "#ca8a04",
       "#be123c", "#4338ca"]

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 9,
    "text.color": INK, "axes.labelcolor": INK,
    "axes.edgecolor": "#9ca3af", "axes.linewidth": 0.8,
    "xtick.color": "#374151", "ytick.color": "#374151",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "figure.facecolor": "white",
    "axes.facecolor": "white", "legend.frameon": False,
})


def finish(ax, title=None, xlabel=None, ylabel=None, xgrid=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x" if xgrid else "y", alpha=0.9)
    ax.grid(axis="y" if xgrid else "x", visible=False)
    if title:
        ax.set_title(title, fontsize=10.5, fontweight="bold", loc="left", pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=MUTED)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=MUTED)


def save(fig, num, slug):
    descriptive_path = FIGURE_DIR / f"Figure_{num}_{slug}.png"
    report_path = FIGURE_DIR / f"Figure_{num}.png"
    fig.savefig(descriptive_path, facecolor="white")
    fig.savefig(report_path, facecolor="white")
    plt.show()
    plt.close(fig)
    print(f"saved {report_path.name} and {descriptive_path.name}")


money = FuncFormatter(lambda v, _: f"${v:,.0f}")
money_k = FuncFormatter(lambda v, _: f"${v/1e3:,.0f}k")
money_m = FuncFormatter(lambda v, _: f"${v/1e6:,.1f}M")

# -------------------------------------------------------------------- load ---
L = lambda n: pd.read_csv(f"{DATA}/Group030_{n}_standardised.csv",
                          keep_default_na=False)
orders = L("orders")
items = L("order_items")
customers = L("customers")
deliveries = L("deliveries")
products = L("products")
reviews = L("product_reviews")

for df, cols in [(orders, ["order_price", "order_total", "delivery_charges",
                           "coupon_discount", "tax_amount"]),
                 (items, ["quantity", "unit_price", "line_revenue"]),
                 (customers, ["lifetime_value_before_period", "prior_12m_orders"]),
                 (deliveries, ["delay_days", "shipping_distance_km",
                               "fulfilment_hours", "delivery_cost"]),
                 (products, ["unit_price", "unit_cost", "weight_kg"]),
                 (reviews, ["rating", "helpful_votes", "review_length_chars",
                            "review_word_count"])]:
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

orders["ts"] = pd.to_datetime(orders["order_timestamp"])
deliveries["on_time_in_full"] = deliveries["on_time_in_full"].astype(str) == "True"
reviews["contains_non_latin_script"] = (
    reviews["contains_non_latin_script"].astype(str) == "True")

print("=" * 78)
print("GRAIN CHECKS BEFORE JOINING")
print("=" * 78)
TOTAL_REV = round(items["line_revenue"].sum(), 2)
print(f"orders            : {len(orders):>6,} rows, {orders.order_id.nunique():>6,} distinct order_id")
print(f"order_items       : {len(items):>6,} rows, {items.order_item_id.nunique():>6,} distinct order_item_id")
print(f"customers         : {len(customers):>6,} rows, {customers.customer_id.nunique():>6,} distinct customer_id")
print(f"deliveries        : {len(deliveries):>6,} rows, {deliveries.order_id.nunique():>6,} distinct order_id (1:1 with orders)")
print(f"products          : {len(products):>6,} rows, {products.product_id.nunique():>6,} distinct product_id")
print(f"product_reviews   : {len(reviews):>6,} rows, {reviews.review_id.nunique():>6,} distinct review_id")
print(f"\ncontrol total: sum(order_items.line_revenue) = ${TOTAL_REV:,.2f}")
print(f"             : sum(orders.order_price)       = ${orders.order_price.sum():,.2f}")

# =============================================================================
# FIGURE 1 - univariate distribution and composition
# =============================================================================
print("\nFigure 1 ...")
fig = plt.figure(figsize=(12.5, 7.4))
gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1], hspace=0.55, wspace=0.30,
                      left=0.065, right=0.985, top=0.855, bottom=0.190)

ax = fig.add_subplot(gs[0, :2])
vals = orders["order_total"]
ax.hist(vals, bins=60, color=BLUE, alpha=0.85, edgecolor="white", linewidth=0.4)
ax.axvline(vals.median(), color=ROSE, lw=1.8, ls="--",
           label=f"Median  ${vals.median():,.0f}")
ax.axvline(vals.mean(), color=AMBER, lw=1.8, ls=":",
           label=f"Mean  ${vals.mean():,.0f}")
ax.xaxis.set_major_formatter(money)
ax.legend(fontsize=8.5, loc="upper right")
finish(ax, "Order value is strongly right-skewed",
       "Order total (AUD, GST-inclusive)", "Number of orders")

ax = fig.add_subplot(gs[0, 2])
q = vals.quantile([.25, .5, .75, .9, .99])
ax.boxplot([vals], vert=True, widths=0.45, patch_artist=True,
           boxprops=dict(facecolor=BLUE, alpha=0.35, edgecolor=BLUE),
           medianprops=dict(color=ROSE, lw=2),
           whiskerprops=dict(color=SLATE), capprops=dict(color=SLATE),
           flierprops=dict(marker="o", ms=2, alpha=0.25,
                           markerfacecolor=SLATE, markeredgecolor="none"))
ax.set_xticks([])
ax.yaxis.set_major_formatter(money)
finish(ax, "Spread and outliers", None, "Order total (AUD)")
ax.text(0.04, 0.97,
        f"P25  ${q[.25]:,.0f}\nP50  ${q[.5]:,.0f}\nP75  ${q[.75]:,.0f}\n"
        f"P99  ${q[.99]:,.0f}\nMax  ${vals.max():,.0f}",
        transform=ax.transAxes, ha="left", va="top", fontsize=8, color=SLATE,
        linespacing=1.5)

for j, (col, ttl) in enumerate([("sales_channel", "Sales channel"),
                                ("payment_method", "Payment method"),
                                ("season", "Season")]):
    ax = fig.add_subplot(gs[1, j])
    s = orders[col].value_counts().sort_values()
    pct = 100 * s / len(orders)
    ax.barh(s.index, pct, color=SEQ[j], alpha=0.85, height=0.6)
    for k, (lab, v) in enumerate(pct.items()):
        ax.text(v + 0.6, k, f"{v:.1f}%", va="center", fontsize=8, color=SLATE)
    ax.set_xlim(0, max(pct) * 1.30)
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.xaxis.set_major_locator(MaxNLocator(4))
    finish(ax, ttl, "Share of orders", None, xgrid=True)
    ax.tick_params(labelsize=8.5)

save(fig, 1, "order_value_distribution_and_composition")

# =============================================================================
# FIGURE 2 - bivariate group comparison  (JOIN orders -> customers)
# =============================================================================
print("Figure 2 ...")
before = len(orders)
oc = orders.merge(customers[["customer_id", "customer_segment", "loyalty_tier",
                             "age_band", "lifetime_value_before_period"]],
                  on="customer_id", how="left", validate="many_to_one")
print(f"  grain check: orders {before:,} -> after join {len(oc):,} "
      f"(many_to_one on customer_id; unchanged = no row multiplication)")
assert len(oc) == before

fig = plt.figure(figsize=(12.5, 7.0))
gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.25, 1], wspace=0.30,
                      left=0.065, right=0.985, top=0.850, bottom=0.230)

seg_order = oc.groupby("customer_segment")["order_total"].median().sort_values().index
ax = fig.add_subplot(gs[0, 0])
data = [oc.loc[oc.customer_segment == s, "order_total"] for s in seg_order]
bp = ax.boxplot(data, vert=True, widths=0.55, patch_artist=True, showfliers=False)
for k, b in enumerate(bp["boxes"]):
    b.set(facecolor=SEQ[k], alpha=0.35, edgecolor=SEQ[k])
for m in bp["medians"]:
    m.set(color=INK, lw=1.8)
ax.set_xticklabels([s.replace(" ", "\n") for s in seg_order], fontsize=8.5)
ax.yaxis.set_major_formatter(money_k)
for k, s in enumerate(seg_order):
    n = (oc.customer_segment == s).sum()
    ax.text(k + 1, ax.get_ylim()[0], f"n={n:,}", ha="center", va="bottom",
            fontsize=7.6, color=MUTED)
finish(ax, "Order value by customer segment", "Customer segment", "Order total (AUD)")

tier_order = ["Bronze", "Silver", "Gold", "Platinum"]
ax = fig.add_subplot(gs[0, 1])
means = oc.groupby("loyalty_tier")["order_total"].agg(["mean", "sem", "count"]).reindex(tier_order)
ax.bar(tier_order, means["mean"], yerr=1.96 * means["sem"], capsize=4,
       color=[SEQ[i] for i in range(4)], alpha=0.85, width=0.6,
       error_kw=dict(ecolor=SLATE, lw=1.2))
for k, (m, se, n) in enumerate(zip(means["mean"], means["sem"], means["count"])):
    ax.text(k, m + 1.96 * se + 70, f"${m:,.0f}", ha="center", fontsize=8.5,
            fontweight="bold", color=INK)
    ax.text(k, 90, f"n={int(n):,}", ha="center", fontsize=7.6, color="white")
ax.set_ylim(0, means["mean"].max() * 1.30)
ax.yaxis.set_major_formatter(money)
ax.yaxis.set_major_locator(MaxNLocator(5))
finish(ax, "Mean order value by loyalty tier (95% CI)", "Loyalty tier",
       "Mean order total (AUD)")

ax = fig.add_subplot(gs[0, 2])
cust = (orders.groupby("customer_id")
        .agg(orders_n=("order_id", "count"), revenue=("order_total", "sum"))
        .merge(customers.set_index("customer_id")[["loyalty_tier"]],
               left_index=True, right_index=True))
for k, t in enumerate(tier_order):
    s = cust[cust.loyalty_tier == t]
    ax.scatter(s.orders_n, s.revenue, s=16, alpha=0.65, color=SEQ[k],
               label=f"{t} (n={len(s)})", edgecolors="none")
ax.yaxis.set_major_formatter(money_k)
ax.legend(fontsize=7.6, loc="upper left", handletextpad=0.3)
finish(ax, "Customer revenue vs order count", "Orders placed in 2018",
       "Total revenue (AUD)")

_segmed = oc.groupby("customer_segment").order_total.median()
save(fig, 2, "order_value_by_segment_and_loyalty")

# =============================================================================
# FIGURE 3 - multivariate  (JOIN order_items -> products)  GRAIN CRITICAL
# =============================================================================
print("Figure 3 ...")
before = len(items)
ip = items.merge(products[["product_id", "category", "brand", "unit_cost"]],
                 on="product_id", how="left", validate="many_to_one")
print(f"  grain check: order_items {before:,} -> after join {len(ip):,} "
      f"(many_to_one on product_id; unchanged)")
print(f"  revenue control: joined ${ip.line_revenue.sum():,.2f} vs source ${TOTAL_REV:,.2f} "
      f"-> {'MATCH' if abs(ip.line_revenue.sum()-TOTAL_REV) < 0.01 else 'MISMATCH'}")
naive = orders.merge(items, on="order_id").merge(
    products[["product_id", "category"]], on="product_id")
print(f"  DOUBLE-COUNT DEMO: summing orders.order_total across the "
      f"orders\u22c8items\u22c8products fan-out gives ${naive.order_total.sum():,.0f} "
      f"({naive.order_total.sum()/orders.order_total.sum():.2f}x the true "
      f"${orders.order_total.sum():,.0f}) - order-grain metrics must NOT be summed at item grain")

cat = (ip.groupby("category")
       .agg(revenue=("line_revenue", "sum"), units=("quantity", "sum"),
            lines=("order_item_id", "count"))
       .assign(asp=lambda d: d.revenue / d.units)
       .sort_values("revenue", ascending=False))

fig = plt.figure(figsize=(12.5, 7.2))
gs = fig.add_gridspec(1, 2, width_ratios=[1.20, 1], wspace=0.30,
                      left=0.115, right=0.980, top=0.855, bottom=0.215)

# --- paired share bars: revenue share vs unit share (no twin axis) -----------
ax = fig.add_subplot(gs[0, 0])
rev_share = 100 * cat.revenue / cat.revenue.sum()
unit_share = 100 * cat.units / cat.units.sum()
y = np.arange(len(cat))
h = 0.38
ax.barh(y - h / 2, rev_share, h, color=BLUE, alpha=0.88, label="Share of revenue")
ax.barh(y + h / 2, unit_share, h, color=AMBER, alpha=0.88, label="Share of units")
for k in range(len(cat)):
    ax.text(rev_share.iloc[k] + 0.35, y[k] - h / 2,
            f"{rev_share.iloc[k]:.1f}%  (${cat.revenue.iloc[k]/1e6:.2f}M)",
            va="center", fontsize=7.9, color=BLUE)
    ax.text(unit_share.iloc[k] + 0.35, y[k] + h / 2,
            f"{unit_share.iloc[k]:.1f}%  ({cat.units.iloc[k]:,} u)",
            va="center", fontsize=7.9, color="#a16207")
ax.set_yticks(y)
ax.set_yticklabels(cat.index, fontsize=8.9)
ax.invert_yaxis()
ax.set_xlim(0, max(rev_share.max(), unit_share.max()) * 1.52)
ax.xaxis.set_major_formatter(PercentFormatter())
ax.xaxis.set_major_locator(MaxNLocator(6))
ax.legend(fontsize=8.4, loc="center right", bbox_to_anchor=(1.0, 0.52))
finish(ax, "Revenue share and unit share rank almost inversely",
       "Share of total (revenue $16.12M / units 41,993)", None, xgrid=True)

# --- price vs volume ---------------------------------------------------------
ax = fig.add_subplot(gs[0, 1])
ax.scatter(cat.units, cat.asp, s=cat.revenue / 4200, alpha=0.55,
           c=range(len(cat)), cmap="viridis", edgecolors="white", linewidth=1.2)
offsets = {"Laptop": (0, 22), "Home Entertainment": (0, -30),
           "Gaming": (46, 12), "Smartphone": (-40, 10), "Tablet": (-34, -20),
           "Networking": (44, -6), "Wearable": (40, 14), "Audio": (-6, -26),
           "Smart Home": (44, 8), "Accessory": (0, 22)}
for name, row in cat.iterrows():
    ax.annotate(name, (row.units, row.asp), fontsize=8, color=INK,
                xytext=offsets.get(name, (0, 12)), textcoords="offset points",
                ha="center")
ax.set_yscale("log")
ax.yaxis.set_major_formatter(money)
ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
ax.set_yticks([200, 400, 700, 1000, 2000, 3000])
ax.set_ylim(cat.asp.min() * 0.60, cat.asp.max() * 2.1)
ax.set_xlim(cat.units.min() * 0.60, cat.units.max() * 1.30)
finish(ax, "Price-volume trade-off (bubble area = revenue)",
       "Units sold", "Average selling price (AUD, log scale)")
ax.text(0.98, 0.97, "High price,\nlow volume", transform=ax.transAxes,
        ha="right", va="top", fontsize=8, color=MUTED, style="italic")
ax.text(0.98, 0.06, "Low price,\nhigh volume", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=8, color=MUTED, style="italic")

_infl = naive.order_total.sum() / orders.order_total.sum()
save(fig, 3, "category_revenue_price_volume")

# =============================================================================
# FIGURE 4 - temporal pattern
# =============================================================================
print("Figure 4 ...")
o = orders.copy()
o["month"] = o.ts.dt.to_period("M").dt.to_timestamp()
o["dow"] = o.ts.dt.dayofweek
o["hour"] = o.ts.dt.hour
monthly = o.groupby("month").agg(orders_n=("order_id", "count"),
                                 revenue=("order_total", "sum"),
                                 aov=("order_total", "mean"))

fig = plt.figure(figsize=(12.5, 7.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=0.52, wspace=0.26,
                      left=0.070, right=0.930, top=0.855, bottom=0.190)

ax = fig.add_subplot(gs[0, :])
ax.bar(monthly.index, monthly.revenue, width=20, color=BLUE, alpha=0.80,
       label="Monthly revenue (AUD)")
ax.yaxis.set_major_formatter(money_m)
mean_rev = monthly.revenue.mean()
ax.axhline(mean_rev, color=SLATE, ls="--", lw=1.1,
           label=f"Mean revenue (${mean_rev/1e6:.2f}M)")
finish(ax, "Monthly revenue and order count show no seasonal cycle",
       None, "Revenue (AUD)")
ax.set_ylim(0, monthly.revenue.max() * 1.22)

axb = ax.twinx()
axb.plot(monthly.index, monthly.orders_n, "o-", color=AMBER, lw=1.9, ms=5.5,
         label="Order count")
axb.set_ylabel("Orders", fontsize=9, color=AMBER)
axb.tick_params(axis="y", colors=AMBER)
axb.set_ylim(0, monthly.orders_n.max() * 1.30)
axb.grid(False)
for s in ("top", "left"):
    axb.spines[s].set_visible(False)
axb.spines["right"].set_color(AMBER)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = axb.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8.3, loc="upper right", ncol=2)
ax.set_xticks(monthly.index)
ax.set_xticklabels([d.strftime("%b") for d in monthly.index], fontsize=8.5)
ax.set_xlabel("Month of 2018", fontsize=9, color=MUTED)

ax = fig.add_subplot(gs[1, 0])
dow = o.groupby("dow").size()
names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
cols = [TEAL if d < 5 else AMBER for d in dow.index]
ax.bar(names, dow.values, color=cols, alpha=0.85, width=0.62)
ax.axhline(dow.mean(), color=SLATE, ls="--", lw=1)
ax.set_ylim(0, dow.max() * 1.30)
finish(ax, "Orders by day of week", None, "Orders")
ax.tick_params(labelsize=8.5)
ax.text(0.99, 0.98, f"weekday mean {dow[:5].mean():.0f}   weekend mean {dow[5:].mean():.0f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.8, color=SLATE)

ax = fig.add_subplot(gs[1, 1])
hour = o.groupby("hour").size().reindex(range(24), fill_value=0)
ax.fill_between(hour.index, hour.values, color=VIOLET, alpha=0.30)
ax.plot(hour.index, hour.values, color=VIOLET, lw=1.9)
ax.set_xticks(range(0, 24, 3))
ax.set_xlim(0, 23)
finish(ax, "Orders by hour of day", "Hour of day (local, 24h)", "Orders")
peak = hour.idxmax()
ax.annotate(f"peak {peak:02d}:00", (peak, hour.max()), fontsize=8, color=VIOLET,
            xytext=(0, 8), textcoords="offset points", ha="center")

save(fig, 4, "temporal_demand_patterns")

# =============================================================================
# FIGURE 5 - review / text behaviour
# =============================================================================
print("Figure 5 ...")
fig = plt.figure(figsize=(12.5, 7.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.52, wspace=0.30,
                      left=0.070, right=0.985, top=0.855, bottom=0.205)

ax = fig.add_subplot(gs[0, 0])
rc = reviews.rating.value_counts().sort_index()
pct = 100 * rc / len(reviews)
bars = ax.bar(rc.index, pct, color=[ROSE, ROSE, AMBER, TEAL, TEAL], alpha=0.85,
              width=0.62)
for x, v in zip(rc.index, pct):
    ax.text(x, v + 0.7, f"{v:.1f}%", ha="center", fontsize=8.3, color=INK)
ax.set_ylim(0, pct.max() * 1.22)
ax.yaxis.set_major_formatter(PercentFormatter())
ax.set_xticks([1, 2, 3, 4, 5])
finish(ax, "Ratings skew strongly positive", "Star rating", "Share of reviews")

ax = fig.add_subplot(gs[0, 1:])
styles = reviews.groupby("writing_style").review_length_chars.median().sort_values().index
data = [reviews.loc[reviews.writing_style == s, "review_length_chars"] for s in styles]
bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=False)
for k, b in enumerate(bp["boxes"]):
    b.set(facecolor=SEQ[k], alpha=0.40, edgecolor=SEQ[k])
for m in bp["medians"]:
    m.set(color=INK, lw=1.8)
ax.set_yticklabels([f"{s}\n(n={int((reviews.writing_style==s).sum()):,})" for s in styles],
                   fontsize=8.3)
finish(ax, "Review length is set by writing style, not sentiment",
       "Review length (characters in review_body_clean)", None, xgrid=True)

ax = fig.add_subplot(gs[1, 0])
g = reviews.groupby("rating").review_length_chars.agg(["mean", "sem"])
ax.errorbar(g.index, g["mean"], yerr=1.96 * g["sem"], fmt="o-", color=BLUE,
            lw=1.8, ms=6, capsize=4, ecolor=SLATE)
ax.set_xticks([1, 2, 3, 4, 5])
ax.set_ylim(g["mean"].min() * 0.90, g["mean"].max() * 1.10)
finish(ax, "Length vs rating (95% CI)", "Star rating", "Mean length (chars)")

ax = fig.add_subplot(gs[1, 1])
g = reviews.groupby("rating").helpful_votes.agg(["mean", "sem"])
ax.errorbar(g.index, g["mean"], yerr=1.96 * g["sem"], fmt="o-", color=TEAL,
            lw=1.8, ms=6, capsize=4, ecolor=SLATE)
ax.set_xticks([1, 2, 3, 4, 5])
ax.set_ylim(g["mean"].min() * 0.90, g["mean"].max() * 1.10)
finish(ax, "Helpfulness vs rating (95% CI)", "Star rating", "Mean helpful votes")

ax = fig.add_subplot(gs[1, 2])
g = reviews.groupby("value_experience").rating.agg(["mean", "sem", "count"])
g = g.reindex(["poor_value", "good_value"])
ax.bar(range(len(g)), g["mean"], yerr=1.96 * g["sem"], capsize=5, width=0.55,
       color=[ROSE, TEAL], alpha=0.85, error_kw=dict(ecolor=SLATE, lw=1.2))
ax.set_xticks(range(len(g)))
ax.set_xticklabels([f"{i.replace('_',' ')}\n(n={int(n):,})"
                    for i, n in zip(g.index, g["count"])], fontsize=8.3)
for k, (v, se) in enumerate(zip(g["mean"], g["sem"])):
    ax.text(k, v + 1.96 * se + 0.07, f"{v:.2f}", ha="center", fontsize=8.5, fontweight="bold")
ax.set_ylim(0, 4.6)
finish(ax, "Rating by value perception", None, "Mean star rating")

_len_med = reviews.groupby("writing_style").review_length_chars.median()
_ve = reviews.groupby("value_experience").rating.mean()
save(fig, 5, "review_text_behaviour")

# =============================================================================
# FIGURE 6 - multilingual text: the script/tokenisation effect
# =============================================================================
print("Figure 6 ...")
fig = plt.figure(figsize=(12.5, 7.0))
gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.15, 1.15], wspace=0.32,
                      left=0.070, right=0.985, top=0.850, bottom=0.235)

ax = fig.add_subplot(gs[0, 0])
lang = reviews.language_code.value_counts()
top = lang.sort_values()
colors = [ROSE if l == "en" else BLUE for l in top.index]
ax.barh(top.index, top.values, color=colors, alpha=0.85, height=0.62)
for k, v in enumerate(top.values):
    ax.text(v * 1.06, k, f"{v:,}", va="center", fontsize=7.8, color=SLATE)
ax.set_xscale("log")
ax.set_xlim(30, lang.max() * 3.4)
ax.set_xticks([50, 100, 250, 1000, 5000])
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
finish(ax, "Language mix (log scale)", "Reviews (log scale)", None, xgrid=True)
ax.tick_params(labelsize=9.2)
ax.set_ylim(-1.4, len(top) - 0.4)
ax.text(0.50, 0.035, f"English = {100*lang['en']/len(reviews):.1f}% of all reviews",
        transform=ax.transAxes, ha="center", fontsize=8.6, color="#111827")

ax = fig.add_subplot(gs[0, 1])
lat = reviews[~reviews.contains_non_latin_script]
non = reviews[reviews.contains_non_latin_script]
bins = np.linspace(0, reviews.review_length_chars.max(), 45)
ax.hist(lat.review_length_chars, bins=bins, color=BLUE, alpha=0.60,
        label=f"Latin script only (n={len(lat):,})", density=True)
ax.hist(non.review_length_chars, bins=bins, color=ROSE, alpha=0.60,
        label=f"Contains non-Latin (n={len(non):,})", density=True)
ax.axvline(lat.review_length_chars.median(), color=BLUE, ls="--", lw=1.6)
ax.axvline(non.review_length_chars.median(), color=ROSE, ls="--", lw=1.6)
ax.legend(fontsize=8, loc="upper left", frameon=True,
          facecolor="white", edgecolor="none", framealpha=0.95)
ax.set_yticks([])
finish(ax, "Character length by script class",
       "Review length (characters)", "Density")

ax = fig.add_subplot(gs[0, 2])
grp = reviews.groupby("contains_non_latin_script")[
    ["review_length_chars", "review_word_count"]].mean()
grp.index = ["Latin only", "Contains non-Latin"]
x = np.arange(2)
w = 0.36
b1 = ax.bar(x - w/2, grp.review_length_chars, w, color=BLUE, alpha=0.85,
            label="Characters")
b2 = ax.bar(x + w/2, grp.review_word_count, w, color=AMBER, alpha=0.85,
            label="Whitespace tokens")
for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 22,
            f"{b.get_height():,.0f}", ha="center", fontsize=8.2, color=INK)
ax.set_xticks(x)
ax.set_xticklabels(grp.index, fontsize=8.6)
ax.set_ylim(0, grp.values.max() * 1.34)
ax.legend(fontsize=8.4, loc="upper center", bbox_to_anchor=(0.5, -0.085), ncol=2)
finish(ax, "Characters vs word tokens", None, "Mean per review")
r_chars = grp.review_length_chars.iloc[1] / grp.review_length_chars.iloc[0]
r_words = grp.review_word_count.iloc[1] / grp.review_word_count.iloc[0]
ax.text(0.50, 0.96,
        f"Relative to Latin-only reviews\nCharacters: {r_chars:.2f}×   Whitespace tokens: {r_words:.2f}×",
        transform=ax.transAxes, va="top", ha="center", fontsize=7.6,
        color="#111827", fontweight="bold",
        bbox=dict(facecolor="#fef3c7", edgecolor="#d97706", linewidth=0.8,
                  boxstyle="round,pad=0.35"))

save(fig, 6, "multilingual_text_measures")

# =============================================================================
# FIGURE 7 - delivery / operational performance  (JOIN deliveries -> orders)
# =============================================================================
print("Figure 7 ...")
before = len(deliveries)
do = deliveries.merge(orders[["order_id", "nearest_warehouse", "sales_channel",
                              "expedited_delivery", "order_total"]],
                      on="order_id", how="left", validate="one_to_one")
print(f"  grain check: deliveries {before:,} -> after join {len(do):,} "
      f"(one_to_one on order_id; unchanged)")

fig = plt.figure(figsize=(12.5, 7.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1], hspace=0.55, wspace=0.30,
                      left=0.070, right=0.985, top=0.855, bottom=0.190)

ax = fig.add_subplot(gs[0, :2])
piv = do.pivot_table(index="carrier", columns="service_level",
                     values="on_time_in_full", aggfunc="mean") * 100
cnt = do.pivot_table(index="carrier", columns="service_level",
                     values="order_id", aggfunc="count")
piv = piv.loc[piv.mean(axis=1).sort_values().index]
x = np.arange(len(piv))
w = 0.36
overall = do.on_time_in_full.mean() * 100
for k, sl in enumerate(["Standard", "Express"]):
    bars = ax.bar(x + (k - 0.5) * w, piv[sl], w, color=[BLUE, TEAL][k],
                  alpha=0.85, label=f"{sl}")
    for b, v, n in zip(bars, piv[sl], cnt.loc[piv.index, sl]):
        label_y = max(v + 2.4, overall + 2.4)
        ax.text(b.get_x() + b.get_width()/2, label_y, f"{v:.1f}%",
                ha="center", fontsize=8, color=INK)
        ax.text(b.get_x() + b.get_width()/2, 4, f"{sl}  n={n:,}", ha="center",
                va="bottom", fontsize=7.6, color="white", rotation=90)
ax.axhline(overall, color=ROSE, ls="--", lw=1.4)
ax.set_xlim(-0.62, 3.85)
ax.text(3.83, overall - 1.8, f"overall {overall:.1f}%",
        fontsize=8, color=ROSE, ha="right", va="top",
        bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
ax.set_xticks(x)
ax.set_xticklabels(piv.index, fontsize=8.8)
ax.set_ylim(0, 104)
ax.yaxis.set_major_formatter(PercentFormatter())
ax.yaxis.set_major_locator(MaxNLocator(5))
finish(ax, "On-time-in-full rate by carrier and service level",
       "Carrier", "OTIF rate")
car = (do.groupby("carrier").on_time_in_full.mean() * 100).sort_values()

ax = fig.add_subplot(gs[0, 2])
dr = do.loc[do.delay_reason != "none", "delay_reason"].value_counts()
ax.pie(dr.values, labels=[l.replace("_", "\n") for l in dr.index],
       autopct=lambda p: f"{p:.0f}%", colors=[ROSE, AMBER, VIOLET],
       startangle=90, textprops=dict(fontsize=8.2),
       wedgeprops=dict(edgecolor="white", linewidth=1.6))
ax.set_title(f"Delay reasons\n({dr.sum():,} late of {len(do):,} = "
             f"{100*dr.sum()/len(do):.1f}%)",
             fontsize=10, fontweight="bold", loc="center", pad=6)
ax.grid(False)

ax = fig.add_subplot(gs[1, 0])
wh = do.groupby("nearest_warehouse").agg(
    otif=("on_time_in_full", "mean"), dist=("shipping_distance_km", "mean"),
    n=("order_id", "count"))
ax.scatter(wh.dist, wh.otif * 100, s=wh.n / 4, color=TEAL, alpha=0.65,
           edgecolors="white", linewidth=1.4)
for name, row in wh.iterrows():
    ax.annotate(f"{name}\n(n={int(row.n):,})", (row.dist, row.otif * 100),
                fontsize=7.8, ha="center", xytext=(0, 13),
                textcoords="offset points", color=INK)
ax.set_xlim(wh.dist.min() - 0.28, wh.dist.max() + 0.28)
ax.set_ylim(wh.otif.min() * 100 - 1.6, wh.otif.max() * 100 + 2.4)
ax.yaxis.set_major_formatter(PercentFormatter())
finish(ax, "Warehouse: distance vs OTIF", "Mean shipping distance (km)",
       "OTIF rate")

ax = fig.add_subplot(gs[1, 1])
bins = [0, 2, 4, 6, 8, 12]
do["dist_band"] = pd.cut(do.shipping_distance_km, bins=bins,
                         labels=["0-2", "2-4", "4-6", "6-8", "8-12"])
g = do.groupby("dist_band", observed=True).agg(
    hrs=("fulfilment_hours", "mean"), n=("order_id", "count"))
ax.bar(g.index.astype(str), g.hrs, color=VIOLET, alpha=0.85, width=0.62)
for k, (v, n) in enumerate(zip(g.hrs, g.n)):
    ax.text(k, v + 0.9, f"{v:.0f}h", ha="center", fontsize=8.2, color=INK)
    ax.text(k, 2.5, f"n={n:,}", ha="center", fontsize=7.2, color="white",
            rotation=90)
ax.set_ylim(0, g.hrs.max() * 1.20)
finish(ax, "Fulfilment time by distance", "Shipping distance band (km)",
       "Mean fulfilment (hours)")

ax = fig.add_subplot(gs[1, 2])
exp = do.groupby("expedited_delivery").agg(
    hrs=("fulfilment_hours", "mean"), otif=("on_time_in_full", "mean"),
    n=("order_id", "count"))
exp.index = ["Standard request", "Expedited"]
x = np.arange(2)
ax.bar(x, exp.hrs, 0.5, color=[SLATE, AMBER], alpha=0.85)
for k, (v, n) in enumerate(zip(exp.hrs, exp.n)):
    ax.text(k, v + 1.0, f"{v:.0f}h", ha="center", fontsize=8.5,
            fontweight="bold")
    ax.text(k, 2.5, f"n={int(n):,}", ha="center", fontsize=7.4, color="white")
ax.set_xticks(x)
ax.set_xticklabels(exp.index, fontsize=8.4)
ax.set_ylim(0, exp.hrs.max() * 1.22)
finish(ax, "Expedited flag vs fulfilment", None, "Mean fulfilment (hours)")

save(fig, 7, "delivery_operational_performance")

# =============================================================================
# FIGURE 8 - does delivery performance shape reviews?  (JOIN reviews->deliveries)
# =============================================================================
print("Figure 8 ...")
before = len(reviews)
rd = reviews.merge(
    deliveries[["order_id", "delay_days", "on_time_in_full", "service_level",
                "carrier", "shipping_distance_km", "delay_reason"]],
    on="order_id", how="left", validate="many_to_one")
print(f"  grain check: product_reviews {before:,} -> after join {len(rd):,} "
      f"(many_to_one on order_id; unchanged)")
print(f"  note: {reviews.order_id.nunique():,} distinct orders carry the 7,000 reviews "
      f"(mean {len(reviews)/reviews.order_id.nunique():.2f} reviews per reviewed order) - "
      f"delivery attributes therefore repeat across sibling reviews and must NOT be "
      f"aggregated as if one row per delivery")

fig = plt.figure(figsize=(12.5, 7.8))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.52, wspace=0.30,
                      left=0.070, right=0.985, top=0.855, bottom=0.230)

ax = fig.add_subplot(gs[0, 0])
g = rd.groupby("on_time_in_full").rating.agg(["mean", "sem", "count"])
g.index = ["Late", "On time"]
ax.bar(range(2), g["mean"], yerr=1.96 * g["sem"], capsize=5, width=0.5,
       color=[ROSE, TEAL], alpha=0.85, error_kw=dict(ecolor=SLATE, lw=1.2))
for k, (v, se, n) in enumerate(zip(g["mean"], g["sem"], g["count"])):
    ax.text(k, v + 1.96 * se + 0.07, f"{v:.2f}", ha="center", fontsize=8.8, fontweight="bold")
    ax.text(k, 0.14, f"n={int(n):,}", ha="center", fontsize=7.6, color="white")
ax.set_xticks(range(2))
ax.set_xticklabels(g.index, fontsize=8.8)
ax.set_ylim(0, 4.9)
finish(ax, "Rating by OTIF outcome (95% CI)", None, "Mean star rating")

ax = fig.add_subplot(gs[0, 1:])
g = rd.groupby("delay_days").rating.agg(["mean", "sem", "count"])
ax.errorbar(g.index, g["mean"], yerr=1.96 * g["sem"], fmt="o-", color=BLUE,
            lw=1.8, ms=7, capsize=4, ecolor=SLATE)
ax.axhline(reviews.rating.mean(), color=ROSE, ls="--", lw=1.3)
ax.text(g.index.max(), reviews.rating.mean() + 0.03,
        f"overall mean {reviews.rating.mean():.2f}", fontsize=8, color=ROSE,
        ha="right", va="bottom")
for x_, m, n in zip(g.index, g["mean"], g["count"]):
    ax.text(x_, ax.get_ylim()[0], f"n={int(n):,}", ha="center", va="bottom",
            fontsize=7.4, color=MUTED)
ax.set_xticks(g.index)
ax.set_ylim(3.2, 4.3)
finish(ax, "Star rating does not decline as delivery lateness increases",
       "Delay (days beyond promised date)", "Mean star rating (95% CI)")

ax = fig.add_subplot(gs[1, 0])
mix = pd.crosstab(rd.on_time_in_full, rd.rating, normalize="index") * 100
mix.index = ["Late", "On time"]
bottom = np.zeros(len(mix))
star_cols = [ROSE, "#f43f5e", AMBER, "#5eead4", TEAL]
for k, star in enumerate(sorted(mix.columns)):
    ax.bar(mix.index, mix[star], 0.5, bottom=bottom, color=star_cols[k],
           alpha=0.90, label=f"{star}\u2605")
    for j, v in enumerate(mix[star]):
        if v > 5:
            ax.text(j, bottom[j] + v / 2, f"{v:.0f}%", ha="center", va="center",
                    fontsize=7.6, color="white", fontweight="bold")
    bottom += mix[star].values
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(PercentFormatter())
ax.legend(fontsize=7.6, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.075),
          columnspacing=0.8, handlelength=1.1, handletextpad=0.35,
          title="Star rating", title_fontsize=7.6)
finish(ax, "Rating mix is unchanged by lateness", None, "Share of reviews")
ax.tick_params(labelsize=8.6)

ax = fig.add_subplot(gs[1, 1])
g = rd.groupby("service_level").rating.agg(["mean", "sem", "count"])
ax.bar(range(len(g)), g["mean"], yerr=1.96 * g["sem"], capsize=5, width=0.5,
       color=[TEAL, BLUE], alpha=0.85, error_kw=dict(ecolor=SLATE, lw=1.2))
ax.set_xticks(range(len(g)))
ax.set_xticklabels([f"{i}\n(n={int(n):,})" for i, n in zip(g.index, g["count"])],
                   fontsize=8.4)
for k, (v, se) in enumerate(zip(g["mean"], g["sem"])):
    ax.text(k, v + 1.96 * se + 0.07, f"{v:.2f}", ha="center", fontsize=8.5, fontweight="bold")
ax.set_ylim(0, 4.9)
finish(ax, "Rating by service level", None, "Mean star rating")

ax = fig.add_subplot(gs[1, 2])
g = rd.groupby("delay_reason").rating.agg(["mean", "sem", "count"]).sort_values("mean")
lbl = {"none": "no delay", "carrier_capacity": "carrier\ncapacity",
       "warehouse_congestion": "warehouse\ncongestion", "weather": "weather"}
ax.bar(range(len(g)), g["mean"], yerr=1.96 * g["sem"], capsize=4, width=0.6,
       color=[SEQ[i] for i in range(len(g))], alpha=0.85,
       error_kw=dict(ecolor=SLATE, lw=1.1))
ax.set_xticks(range(len(g)))
ax.set_xticklabels([lbl.get(i, i) for i in g.index], fontsize=8)
for k, (v, se, n) in enumerate(zip(g["mean"], g["sem"], g["count"])):
    ax.text(k, v + 1.96 * se + 0.07, f"{v:.2f}", ha="center", fontsize=8.2, fontweight="bold")
    ax.text(k, 0.14, f"n={int(n):,}", ha="center", fontsize=7.2, color="white")
ax.set_ylim(0, 4.9)
finish(ax, "Rating by delay reason", None, "Mean star rating")

save(fig, 8, "delivery_impact_on_reviews")

figure_register = pd.DataFrame([
    [1, "Univariate distribution/composition", "orders", "none", "order"],
    [2, "Bivariate and customer comparison", "orders; customers", "customer_id", "order / customer"],
    [3, "Multivariate category analysis", "order_items; products", "product_id", "order-item line"],
    [4, "Temporal pattern", "orders", "none", "order aggregated by time"],
    [5, "Review/text behaviour", "product_reviews", "none", "review"],
    [6, "Review/text behaviour", "product_reviews", "none", "review"],
    [7, "Delivery/operational performance", "deliveries; orders", "order_id", "delivery"],
    [8, "Delivery-review relationship", "product_reviews; deliveries", "order_id", "review"],
], columns=["figure", "category", "tables", "join_key", "grain"])
assert len(figure_register) == 8
assert figure_register.tables.str.contains("orders|order_items|customers|deliveries|products|product_reviews").all()
figure_register
