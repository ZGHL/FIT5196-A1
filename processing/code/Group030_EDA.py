"""EDA code exported cell-by-cell from Group030_EDA.ipynb."""

from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, PercentFormatter

GROUP_ID = 'Group030'
PROJECT_ROOT = Path.cwd()
if (PROJECT_ROOT / 'processing' / 'outputs').is_dir():
    OUTPUT_DIR = PROJECT_ROOT / 'processing' / 'outputs'
    FIGURE_DIR = PROJECT_ROOT / 'processing' / 'figures'
else:
    OUTPUT_DIR = PROJECT_ROOT / 'outputs'
    FIGURE_DIR = PROJECT_ROOT / 'figures'

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
TABLE_NAMES = ['orders', 'order_items', 'customers', 'deliveries', 'products', 'product_reviews']

BLUE = '#2F6690'
LIGHT_BLUE = '#8CB9D9'
ORANGE = '#D97732'
GREEN = '#4C956C'
PURPLE = '#7A6FA8'
DARK = '#243746'
GREY = '#7B8794'
PALE = '#E9EFF4'

plt.rcParams.update({
    'figure.figsize': (10, 5.8),
    'figure.dpi': 120,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'axes.edgecolor': '#C6D0D8',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': False,
    'xtick.labelsize': 9.5,
    'ytick.labelsize': 9.5,
    'legend.frameon': False,
    'font.family': 'DejaVu Sans',
})

aud = FuncFormatter(lambda value, _: f'${value/1000:,.0f}k' if abs(value) >= 1000 else f'${value:,.0f}')
aud_k1 = FuncFormatter(lambda value, _: f'${value/1000:,.1f}k')

tables = {
    name: pd.read_csv(
        OUTPUT_DIR / f'{GROUP_ID}_{name}_standardised.csv',
        keep_default_na=False,
    )
    for name in TABLE_NAMES
}

table_sizes = pd.DataFrame([
    {'table': name, 'rows': len(frame), 'columns': len(frame.columns)}
    for name, frame in tables.items()
])
table_sizes

orders = tables['orders'].copy()
order_items = tables['order_items'].copy()
customers = tables['customers'].copy()
deliveries = tables['deliveries'].copy()
products = tables['products'].copy()
reviews = tables['product_reviews'].copy()

for field in ['order_price', 'order_total', 'coupon_discount', 'delivery_charges']:
    orders[field] = pd.to_numeric(orders[field])
for field in ['quantity', 'unit_price', 'line_revenue']:
    order_items[field] = pd.to_numeric(order_items[field])
for field in ['unit_cost', 'unit_price']:
    products[field] = pd.to_numeric(products[field])
for field in ['rating', 'review_length_chars', 'helpful_votes']:
    reviews[field] = pd.to_numeric(reviews[field])
for field in ['fulfilment_hours', 'delay_days']:
    deliveries[field] = pd.to_numeric(deliveries[field])

orders['order_timestamp'] = pd.to_datetime(orders['order_timestamp'])
reviews['review_timestamp'] = pd.to_datetime(reviews['review_timestamp'])
for field in ['dispatch_date', 'promised_date', 'delivered_date']:
    deliveries[field] = pd.to_datetime(deliveries[field])
deliveries['otif'] = deliveries['on_time_in_full'].astype(str).eq('True')

key_checks = pd.DataFrame([
    {'table': 'orders', 'key': 'order_id', 'rows': len(orders), 'unique_keys': orders.order_id.nunique()},
    {'table': 'order_items', 'key': 'order_item_id', 'rows': len(order_items), 'unique_keys': order_items.order_item_id.nunique()},
    {'table': 'customers', 'key': 'customer_id', 'rows': len(customers), 'unique_keys': customers.customer_id.nunique()},
    {'table': 'deliveries', 'key': 'delivery_id', 'rows': len(deliveries), 'unique_keys': deliveries.delivery_id.nunique()},
    {'table': 'products', 'key': 'product_id', 'rows': len(products), 'unique_keys': products.product_id.nunique()},
    {'table': 'product_reviews', 'key': 'review_id', 'rows': len(reviews), 'unique_keys': reviews.review_id.nunique()},
])
key_checks['unique'] = key_checks.rows.eq(key_checks.unique_keys)
assert key_checks['unique'].all()
key_checks

def checked_many_to_one(left, right, key, label):
    before = len(left)
    joined = left.merge(right, on=key, how='left', validate='many_to_one')
    after = len(joined)
    assert before == after, f'{label}: the join changed the left-table grain'
    assert joined[right.columns.difference([key])].notna().any(axis=1).all(), f'{label}: unmatched parent key'
    return joined, {'join': label, 'rows_before': before, 'rows_after': after}

def mean_summary(frame, group, value):
    result = frame.groupby(group, observed=True)[value].agg(['count', 'mean', 'std']).reset_index()
    result['ci95'] = 1.96 * result['std'] / np.sqrt(result['count'])
    return result


def wilson_interval(successes, total, z=1.96):
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    return centre - half, centre + half


def save_figure(fig, number):
    fig.savefig(FIGURE_DIR / f'Figure_{number}.png', dpi=200, bbox_inches='tight', facecolor='white')

order_value_summary = orders.order_total.describe(percentiles=[0.25, 0.50, 0.75, 0.90]).to_frame('AUD')
order_value_summary

median_total = orders.order_total.median()
p90_total = orders.order_total.quantile(0.90)

fig1, ax = plt.subplots(figsize=(10, 5.6))
ax.hist(orders.order_total, bins=36, color=BLUE, edgecolor='white', linewidth=0.7)
ax.axvline(median_total, color=ORANGE, linestyle='--', linewidth=2, label=f'Median  ${median_total:,.0f}')
ax.axvline(p90_total, color=PURPLE, linestyle='--', linewidth=2, label=f'90th percentile  ${p90_total:,.0f}')
ax.set_title('Figure 1. Order value is strongly right-skewed')
ax.set_xlabel('Net order total (AUD)')
ax.set_ylabel('Number of orders')
ax.xaxis.set_major_formatter(aud)
ax.grid(axis='y', color=PALE, linewidth=0.8)
ax.legend(loc='upper right')
fig1.tight_layout()
save_figure(fig1, 1)
plt.show()

discount_order = [0, 5, 10, 15, 20, 25]
discount_summary = orders.groupby('coupon_discount').order_price.agg(
    orders='size', mean='mean', median='median',
    q1=lambda values: values.quantile(0.25),
    q3=lambda values: values.quantile(0.75),
    std='std',
).reindex(discount_order)
discount_summary['mean_ci95'] = 1.96 * discount_summary['std'] / np.sqrt(discount_summary['orders'])
discount_summary.round(2)

fig2, (ax_dist, ax_mean) = plt.subplots(2, 1, figsize=(10.5, 7.6), sharex=True,
                                           gridspec_kw={'height_ratios': [1.7, 1]})
box_data = [orders.loc[orders.coupon_discount.eq(level), 'order_price'] for level in discount_order]
box = ax_dist.boxplot(box_data, positions=discount_order, widths=3.2, patch_artist=True,
                 showfliers=False, medianprops={'color': DARK, 'linewidth': 1.8},
                 whiskerprops={'color': GREY}, capprops={'color': GREY})
for patch in box['boxes']:
    patch.set_facecolor(LIGHT_BLUE)
    patch.set_alpha(0.65)

ax_mean.errorbar(discount_order, discount_summary['mean'], yerr=discount_summary['mean_ci95'],
                 fmt='o', color=DARK, ecolor=BLUE, elinewidth=2, capsize=6,
                 capthick=2, markersize=7, label='Mean and 95% CI')
ci_low = (discount_summary['mean'] - discount_summary['mean_ci95']).min()
ci_high = (discount_summary['mean'] + discount_summary['mean_ci95']).max()
ci_pad = max(60, (ci_high - ci_low) * 0.18)
ax_mean.set_ylim(ci_low - ci_pad, ci_high + ci_pad)
for level, row in discount_summary.iterrows():
    ax_mean.text(level, ci_low - ci_pad * 0.72, f"n={int(row['orders']):,}",
                 ha='center', va='bottom', fontsize=8.5, color=GREY)

ax_dist.set_title('Figure 2. Gross basket distributions overlap across discount levels')
ax_dist.set_ylabel('Gross basket value (AUD)')
ax_dist.yaxis.set_major_formatter(aud)
ax_dist.grid(axis='y', color=PALE, linewidth=0.8)
ax_mean.set_title('Mean comparison on an enlarged scale', fontsize=11)
ax_mean.set_xlabel('Coupon discount (percentage points)')
ax_mean.set_ylabel('Mean gross value (AUD)')
ax_mean.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f'${value / 1000:.1f}k'))
ax_mean.grid(axis='y', color=PALE, linewidth=0.8)
ax_mean.legend(loc='upper left')
fig2.tight_layout()
save_figure(fig2, 2)
plt.show()

item_product, figure3_join = checked_many_to_one(
    order_items,
    products[['product_id', 'category', 'unit_cost']],
    'product_id',
    'order items to products',
)
figure3_join

item_product['estimated_margin'] = (
    item_product['line_revenue'] - item_product['quantity'] * item_product['unit_cost']
)
category_summary = item_product.groupby('category').agg(
    lines=('order_item_id', 'size'),
    revenue=('line_revenue', 'sum'),
    estimated_margin=('estimated_margin', 'sum'),
).sort_values('estimated_margin')
category_summary['margin_rate'] = category_summary.estimated_margin / category_summary.revenue
category_summary.round(3)

fig3, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(12, 6.2), sharey=True,
                                         gridspec_kw={'width_ratios': [1.45, 1]})
y = np.arange(len(category_summary))
ax_left.set_axisbelow(True)
ax_left.barh(y, category_summary.estimated_margin, color=BLUE, alpha=0.95, zorder=3)
ax_left.set_yticks(y, category_summary.index)
ax_left.set_xlabel('Estimated margin contribution (AUD)')
ax_left.xaxis.set_major_formatter(aud)
ax_left.grid(axis='x', color=PALE, linewidth=0.8)

ax_right.scatter(category_summary.margin_rate * 100, y, color=ORANGE, s=55, zorder=3)
ax_right.axvline(category_summary.estimated_margin.sum() / category_summary.revenue.sum() * 100,
                 color=GREY, linestyle='--', linewidth=1.4, label='Overall rate')
ax_right.set_xlabel('Estimated margin rate (%)')
ax_right.set_xlim(35.5, 40.5)
ax_right.xaxis.set_major_formatter(PercentFormatter(100, decimals=1))
ax_right.grid(axis='x', color=PALE, linewidth=0.8)
ax_right.legend(loc='lower right')

fig3.suptitle('Figure 3. Category scale and estimated margin rate tell different stories', y=1.01,
              fontsize=14, fontweight='bold')
fig3.tight_layout()
save_figure(fig3, 3)
plt.show()

orders['month'] = orders.order_timestamp.dt.to_period('M')
monthly = orders.groupby('month').agg(
    orders=('order_id', 'size'),
    mean_order_total=('order_total', 'mean'),
).reset_index()
monthly['calendar_days'] = monthly.month.dt.days_in_month
monthly['orders_per_day'] = monthly.orders / monthly.calendar_days
monthly['month_label'] = monthly.month.astype(str)
monthly[['month_label', 'orders', 'calendar_days', 'orders_per_day', 'mean_order_total']].round(2)

fig4, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
x = np.arange(len(monthly))
ax_top.plot(x, monthly.orders_per_day, color=BLUE, marker='o', linewidth=2.2)
ax_top.fill_between(x, monthly.orders_per_day, monthly.orders_per_day.mean(), color=LIGHT_BLUE, alpha=0.22)
ax_top.axhline(monthly.orders_per_day.mean(), color=GREY, linestyle='--', linewidth=1.2, label='Annual daily average')
ax_top.set_ylabel('Orders per calendar day')
ax_top.grid(axis='y', color=PALE, linewidth=0.8)
ax_top.legend(loc='lower right')

ax_bottom.plot(x, monthly.mean_order_total, color=ORANGE, marker='o', linewidth=2.2)
ax_bottom.axhline(orders.order_total.mean(), color=GREY, linestyle='--', linewidth=1.2, label='Annual mean order value')
ax_bottom.set_ylabel('Mean order total (AUD)')
ax_bottom.yaxis.set_major_formatter(aud_k1)
ax_bottom.set_xticks(x, monthly.month_label.str[-2:])
ax_bottom.set_xlabel('Month in 2018')
ax_bottom.grid(axis='y', color=PALE, linewidth=0.8)
ax_bottom.legend(loc='lower right')

fig4.suptitle('Figure 4. Daily order frequency and average value vary differently by month', y=0.98,
              fontsize=14, fontweight='bold')
fig4.tight_layout()
save_figure(fig4, 4)
plt.show()

current_frequency = orders.groupby('customer_id').agg(
    current_orders=('order_id', 'size')
).reset_index()
customer_frequency = customers[['customer_id', 'prior_12m_orders']].merge(
    current_frequency, on='customer_id', how='left', validate='one_to_one'
)
customer_frequency['current_orders'] = customer_frequency.current_orders.fillna(0).astype(int)
customer_frequency['prior_12m_orders'] = pd.to_numeric(customer_frequency.prior_12m_orders)
assert len(customer_frequency) == len(customers)
frequency_correlation = customer_frequency.prior_12m_orders.corr(customer_frequency.current_orders)
customer_frequency.describe().round(2)

fig5, ax = plt.subplots(figsize=(9.5, 6))
hexes = ax.hexbin(customer_frequency.prior_12m_orders, customer_frequency.current_orders,
                  gridsize=18, mincnt=1, cmap='Blues', linewidths=0.3)
coef = np.polyfit(customer_frequency.prior_12m_orders, customer_frequency.current_orders, 1)
line_x = np.linspace(customer_frequency.prior_12m_orders.min(), customer_frequency.prior_12m_orders.max(), 100)
ax.plot(line_x, np.polyval(coef, line_x), color=DARK, linewidth=2.2,
        label=f'Linear summary, Pearson r = {frequency_correlation:.2f}')
colourbar = fig5.colorbar(hexes, ax=ax, pad=0.02)
colourbar.set_label('Customers in hexagon')
ax.set_title('Figure 5. Prior frequency is a weak guide to current ordering')
ax.set_xlabel('Orders in the prior 12 months')
ax.set_ylabel('Orders in the current period')
ax.legend(loc='upper left')
fig5.tight_layout()
save_figure(fig5, 5)
plt.show()

operations = deliveries.groupby(['carrier', 'service_level']).agg(
    otif_successes=('otif', 'sum'),
    deliveries=('delivery_id', 'size'),
    otif_rate=('otif', 'mean'),
    median_fulfilment=('fulfilment_hours', 'median'),
).reset_index()
intervals = np.array([
    wilson_interval(successes, total)
    for successes, total in zip(operations.otif_successes, operations.deliveries)
])
operations['lower'] = intervals[:, 0]
operations['upper'] = intervals[:, 1]
operations['label'] = operations.carrier + ' — ' + operations.service_level
operations = operations.sort_values(['carrier', 'service_level']).reset_index(drop=True)
operations.round(4)

service_colours = {'Express': ORANGE, 'Standard': BLUE}
labels = operations.label.tolist()
y = np.arange(len(labels))

fig6, (ax_rate, ax_time) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True,
                                        gridspec_kw={'width_ratios': [1.05, 1.25]})
for idx, row in operations.iterrows():
    colour = service_colours[row.service_level]
    ax_rate.errorbar(row.otif_rate * 100, idx,
                     xerr=[[100 * (row.otif_rate - row.lower)], [100 * (row.upper - row.otif_rate)]],
                     fmt='o', color=colour, capsize=4, markersize=7)
ax_rate.axvline(deliveries.otif.mean() * 100, color=GREY, linestyle='--', linewidth=1.3,
                label=f'Overall {deliveries.otif.mean():.1%}')
ax_rate.set_yticks(y, labels)
ax_rate.set_xlabel('OTIF rate (95% Wilson CI)')
ax_rate.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax_rate.grid(axis='x', color=PALE, linewidth=0.8)

fulfilment_groups = [
    deliveries.loc[
        deliveries.carrier.eq(row.carrier) & deliveries.service_level.eq(row.service_level),
        'fulfilment_hours'
    ]
    for _, row in operations.iterrows()
]
box = ax_time.boxplot(fulfilment_groups, orientation='horizontal', positions=y, widths=0.58,
                      showfliers=False, patch_artist=True,
                      medianprops={'color': DARK, 'linewidth': 1.6},
                      whiskerprops={'color': GREY}, capprops={'color': GREY})
for patch, service in zip(box['boxes'], operations.service_level):
    patch.set_facecolor(service_colours[service])
    patch.set_alpha(0.42)
ax_time.set_xlabel('Fulfilment hours (median and IQR)')
ax_time.grid(axis='x', color=PALE, linewidth=0.8)
ax_rate.set_yticks(y, labels)
ax_time.tick_params(axis='y', labelleft=False)
service_legend = [
    Line2D([0], [0], marker='o', color='none', markerfacecolor=ORANGE, markeredgecolor=ORANGE, label='Express'),
    Line2D([0], [0], marker='o', color='none', markerfacecolor=BLUE, markeredgecolor=BLUE, label='Standard'),
    Line2D([0], [0], color=GREY, linestyle='--', label=f'Overall {deliveries.otif.mean():.1%}'),
]
ax_rate.legend(handles=service_legend, loc='lower right')

fig6.suptitle('Figure 6. Carrier–service reliability varies more than fulfilment time', y=0.98,
              fontsize=14, fontweight='bold')
fig6.tight_layout()
save_figure(fig6, 6)
plt.show()

order_rating = reviews.groupby('order_id').agg(
    order_mean_rating=('rating', 'mean'),
    review_count=('review_id', 'size'),
    first_review_timestamp=('review_timestamp', 'min'),
).reset_index()

rating_delivery = order_rating.merge(
    deliveries[['order_id', 'promised_date', 'delivered_date']],
    on='order_id', how='inner', validate='one_to_one'
)
assert len(rating_delivery) == len(order_rating)
rating_delivery['timing_days'] = (
    rating_delivery.delivered_date - rating_delivery.promised_date
).dt.days
rating_delivery['delivery_timing'] = np.select(
    [rating_delivery.timing_days.lt(0), rating_delivery.timing_days.eq(0)],
    ['Early', 'On promised date'],
    default='Late',
)
rating_delivery['review_lag_days'] = (
    rating_delivery.first_review_timestamp.dt.normalize() - rating_delivery.delivered_date
).dt.days

timing_order = ['Early', 'On promised date', 'Late']
timing_rating = mean_summary(rating_delivery, 'delivery_timing', 'order_mean_rating').set_index('delivery_timing').reindex(timing_order).reset_index()
rating_delivery['review_lag_band'] = pd.cut(
    rating_delivery.review_lag_days,
    bins=[0, 7, 14, 30, np.inf],
    labels=['1–7', '8–14', '15–30', '31–45'],
)
lag_rating = rating_delivery.groupby(['delivery_timing', 'review_lag_band'], observed=True).order_mean_rating.agg(
    count='size', mean='mean', std='std'
).reset_index()
lag_rating['ci95'] = 1.96 * lag_rating['std'] / np.sqrt(lag_rating['count'])
timing_rating.round(3), lag_rating.round(3)

timing_colours = {'Early': BLUE, 'On promised date': GREEN, 'Late': ORANGE}
fig7, (ax_main, ax_lag) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={'width_ratios': [0.8, 1.5]})
rating_low = min((timing_rating['mean'] - timing_rating['ci95']).min(),
                 (lag_rating['mean'] - lag_rating['ci95']).min())
rating_high = max((timing_rating['mean'] + timing_rating['ci95']).max(),
                  (lag_rating['mean'] + lag_rating['ci95']).max())
rating_pad = max(0.08, (rating_high - rating_low) * 0.18)
zoom_limits = (max(1, rating_low - rating_pad), min(5, rating_high + rating_pad))

x_main = np.arange(len(timing_rating))
for idx, row in timing_rating.iterrows():
    ax_main.errorbar(idx, row['mean'], yerr=row.ci95, fmt='o', markersize=8, capsize=5,
                     color=timing_colours[row.delivery_timing])
    ax_main.text(idx, zoom_limits[0] + 0.015, f"n={int(row['count']):,}",
                 ha='center', va='bottom', fontsize=9, color=GREY)
ax_main.set_xticks(x_main, ['Early', 'On date', 'Late'])
ax_main.set_ylim(*zoom_limits)
ax_main.set_ylabel('Mean order-level rating (1–5)')
ax_main.set_title('A. Delivery timing')
ax_main.grid(axis='y', color=PALE, linewidth=0.8)

lag_order = ['1–7', '8–14', '15–30', '31–45']
x_lag = np.arange(len(lag_order))
for timing in timing_order:
    subset = lag_rating.loc[lag_rating.delivery_timing.eq(timing)].set_index('review_lag_band').reindex(lag_order)
    ax_lag.errorbar(x_lag, subset['mean'], yerr=subset['ci95'], marker='o', capsize=3,
                    linewidth=1.8, color=timing_colours[timing], label=timing)
ax_lag.set_xticks(x_lag, lag_order)
ax_lag.set_ylim(*zoom_limits)
ax_lag.set_xlabel('Days from delivery to first review')
ax_lag.set_title('B. Delivery timing by review lag')
ax_lag.grid(axis='y', color=PALE, linewidth=0.8)
ax_lag.legend(loc='lower right')

fig7.suptitle('Figure 7. Rating differences are small across delivery and review timing', y=1.04,
              fontsize=14, fontweight='bold')
fig7.text(0.5, 0.955, 'Enlarged vertical scale; all values remain within the original 1–5 rating scale.',
          ha='center', fontsize=9.5, color=GREY)
fig7.tight_layout(rect=[0, 0, 1, 0.91])
save_figure(fig7, 7)
plt.show()

figure_register = pd.DataFrame([
    (1, 'Order-value distribution', 'univariate distribution', 'orders', 'order', 'none'),
    (2, 'Discount and gross basket', 'bivariate group comparison', 'orders', 'order', 'none'),
    (3, 'Category contribution and rate', 'multivariate / product economics', 'order_items + products', 'order item', 'product_id many-to-one'),
    (4, 'Monthly frequency and value', 'temporal pattern', 'orders', 'month', 'none'),
    (5, 'Prior and current frequency', 'customer behaviour', 'orders + customers', 'customer', 'customer_id one-to-one after aggregation'),
    (6, 'OTIF and fulfilment by service', 'delivery operations / segmented', 'deliveries', 'delivery', 'relationship checked in solution'),
    (7, 'Delivery timing, review lag and rating', 'review behaviour + delivery operations', 'product_reviews + deliveries', 'rated order', 'order_id one-to-one after review aggregation'),
], columns=['figure', 'question_short', 'category', 'tables', 'analysis_unit', 'join'])
figure_register

ml_link_register = pd.DataFrame([
    ('OTIF-failure classification', 'Figure 6', 'carrier–service OTIF differs, with uncertainty'),
    ('Fulfilment-hours regression', 'Figure 6', 'fulfilment time has a broad overlapping distribution that may need order-level predictors'),
    ('Low-rating classification', 'Figure 7', 'simple delivery timing means do not separate low-rating risk'),
    ('Future customer-frequency regression', 'Figure 5', 'prior frequency alone has weak current-period association'),
    ('Product clustering', 'Figure 3', 'categories differ in contribution scale and estimated rate'),
], columns=['candidate_question', 'EDA_evidence', 'reason_for_next_step'])
ml_link_register
