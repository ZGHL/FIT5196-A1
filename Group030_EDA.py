"""Focused EDA and a compact, reproducible PDF report for Group030."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

GROUP_ID="Group030"; OUTPUT_DIR=Path("outputs"); FIGURE_DIR=Path("figures")

def load_tables():
    out={}
    for n in ["orders","order_items","customers","deliveries","products","product_reviews"]:
        out[n]=pd.read_csv(OUTPUT_DIR/f"{GROUP_ID}_{n}_standardised.csv",keep_default_na=False)
    return out

def make_eda():
    t=load_tables(); FIGURE_DIR.mkdir(exist_ok=True)
    o,items,c,d,p,r=(t[x] for x in ["orders","order_items","customers","deliveries","products","product_reviews"])
    for f in ["order_total","order_price"]: o[f]=pd.to_numeric(o[f])
    for f in ["rating","review_length_chars","helpful_votes"]: r[f]=pd.to_numeric(r[f])
    d["on_time_in_full"]=d.on_time_in_full.astype(str).eq("True")
    o["month"]=pd.to_datetime(o.order_timestamp).dt.to_period("M").astype(str)
    figures=[]
    def save(fig,n):
        fig.tight_layout(); path=FIGURE_DIR/f"Figure_{n}.png"; fig.savefig(path,dpi=180,bbox_inches="tight"); figures.append(fig)
    fig,ax=plt.subplots(figsize=(8,4)); ax.hist(o.order_total,bins=30,color="#355c7d",edgecolor="white"); ax.axvline(o.order_total.median(),color="#c06c84",ls="--",label=f"Median ${o.order_total.median():,.0f}"); ax.set(title="Figure 1. Distribution of order totals",xlabel="Order total (AUD)",ylabel="Orders");ax.legend();save(fig,1)
    channel=o.groupby("sales_channel").agg(orders=("order_id","size"),mean_total=("order_total","mean")).sort_values("mean_total")
    fig,ax=plt.subplots(figsize=(8,4)); channel.mean_total.plot.barh(ax=ax,color="#6c5b7b"); ax.set(title="Figure 2. Mean order total by sales channel",xlabel="Mean order total (AUD)",ylabel="Sales channel");save(fig,2)
    oc=o.merge(c[["customer_id","loyalty_tier"]],on="customer_id",validate="many_to_one")
    seg=oc.groupby(["loyalty_tier","sales_channel"]).order_total.mean().unstack()
    fig,ax=plt.subplots(figsize=(8,4));seg.plot.bar(ax=ax);ax.set(title="Figure 3. Mean order total by loyalty tier and channel",xlabel="Loyalty tier",ylabel="Mean order total (AUD)");ax.legend(title="Channel");save(fig,3)
    monthly=o.groupby("month").agg(orders=("order_id","size"),revenue=("order_total","sum"))
    fig,ax=plt.subplots(figsize=(8,4));monthly.orders.plot(ax=ax,marker="o",color="#355c7d");ax.set(title="Figure 4. Monthly order volume",xlabel="Month",ylabel="Orders");ax.tick_params(axis="x",rotation=45);save(fig,4)
    ratings=r.rating.value_counts().sort_index()
    fig,axs=plt.subplots(1,2,figsize=(9,4));ratings.plot.bar(ax=axs[0],color="#f67280");axs[0].set(title="Rating composition",xlabel="Stars",ylabel="Reviews");axs[1].scatter(r.review_length_chars,r.helpful_votes,s=7,alpha=.18,color="#355c7d");axs[1].set(title="Length and helpful votes",xlabel="Clean review characters",ylabel="Helpful votes");fig.suptitle("Figure 5. Review behaviour");save(fig,5)
    rd=r[["review_id","order_id","rating"]].merge(d[["order_id","service_level","on_time_in_full"]],on="order_id",validate="many_to_one")
    ops=rd.groupby(["service_level","on_time_in_full"]).agg(mean_rating=("rating","mean"),reviews=("review_id","size")).reset_index()
    pivot=ops.pivot(index="service_level",columns="on_time_in_full",values="mean_rating")
    fig,ax=plt.subplots(figsize=(8,4));pivot.plot.bar(ax=ax,color=["#c06c84","#355c7d"]);ax.set(title="Figure 6. Review rating by service level and OTIF",xlabel="Service level",ylabel="Mean rating (1–5)",ylim=(3.5,3.9));ax.legend(title="On time in full");save(fig,6)
    cat=items.merge(p[["product_id","category"]],on="product_id",validate="many_to_one").groupby("category").agg(revenue=("line_revenue","sum"),lines=("order_item_id","size")).sort_values("revenue")
    fig,ax=plt.subplots(figsize=(8,4));cat.revenue.plot.barh(ax=ax,color="#4f9d8a");ax.set(title="Figure 7. Line revenue by product category",xlabel="Line revenue (AUD)",ylabel="Category");save(fig,7)
    # Grain checks protect against inflated metrics after relational joins.
    assert len(oc)==len(o) and len(rd)==len(r) and len(items.merge(p,on="product_id",validate="many_to_one"))==len(items)
    metrics={"orders":len(o),"revenue":o.order_total.sum(),"median_order":o.order_total.median(),"reviews":len(r),"mean_rating":r.rating.mean(),"nonlatin":int(r.contains_non_latin_script.astype(str).eq("True").sum()),"otif":d.on_time_in_full.mean(),"delayed":int((~d.on_time_in_full).sum()),"top_category":cat.index[-1],"top_category_revenue":cat.revenue.iloc[-1],"length_helpful_corr":r.review_length_chars.corr(r.helpful_votes),"monthly_min":int(monthly.orders.min()),"monthly_max":int(monthly.orders.max())}
    return figures,metrics

def _page(pdf,title,body,fontsize=11):
    fig=plt.figure(figsize=(8.27,11.69));fig.text(.08,.94,title,fontsize=20,weight="bold",va="top");fig.text(.08,.89,body,fontsize=fontsize,va="top",wrap=True,linespacing=1.45);pdf.savefig(fig,bbox_inches="tight");plt.close(fig)

def build_report(path=Path("Group030_EDA.pdf")):
    figures,m=make_eda()
    findings=[
      f"1. Figure 1: Across {m['orders']:,} orders, the median order total was ${m['median_order']:,.2f}; the broad distribution makes median-based planning safer than relying only on the mean. Product mix may explain the spread, so investigate category-adjusted values.",
      f"2. Figure 1: Total 2018 order revenue was ${m['revenue']:,.2f} across {m['orders']:,} orders. This establishes commercial scale but excludes margin and returns; pair revenue with product cost before profitability decisions.",
      "3. Figure 2: Mean order values were similar across Web, Store and Mobile relative to within-channel dispersion. Channel is therefore a weak standalone basis for targeting; uncertainty should be quantified before reallocating spend.",
      "4. Figure 3: Loyalty-tier/channel cells show only modest mean-value separation at the order grain. Unequal cell sizes and repeated customers can confound the pattern; use customer-level sensitivity analysis before tier policy changes.",
      f"5. Figure 4: Monthly order volume ranged from {m['monthly_min']} to {m['monthly_max']} orders. The variation may reflect calendar length or promotions rather than seasonality; multiple years and daily rates are needed for staffing forecasts.",
      f"6. Figure 5: Mean rating was {m['mean_rating']:.2f}/5 across {m['reviews']:,} reviews, with four- and five-star reviews most common. Verified purchase is constant, so it cannot explain rating variation in this period.",
      f"7. Figure 5: Review length and helpful votes had correlation r={m['length_helpful_corr']:.3f} across {m['reviews']:,} reviews—effectively no linear association. Nonlinear effects and review exposure remain plausible, so length should not be optimised alone.",
      f"8. Figure 5: {m['nonlatin']:,} of {m['reviews']:,} reviews contained non-Latin letters. Erasing them would systematically discard customer evidence; preserve multilingual text and audit language-specific performance.",
      f"9. Figure 6: {m['delayed']:,} of {len(pd.read_csv(OUTPUT_DIR/f'{GROUP_ID}_deliveries_standardised.csv')):,} deliveries were not OTIF, yet mean ratings were close across OTIF groups. Product experience may dominate, and observational averages do not imply delivery has no causal effect.",
      f"10. Figure 7: {m['top_category']} generated the highest line revenue (${m['top_category_revenue']:,.2f}). Revenue is not profit and category prices differ; combine unit costs and quantities before assortment decisions."
    ]
    ml=("MLQ-1 — Classification: At order placement, predict failure to deliver OTIF to choose proactive intervention. Unit/target: order/OTIF failure. Predictors: warehouse, service level, distance, basket size, channel and order time available then. Use forward-chaining time split; evaluate PR-AUC and recall at intervention capacity. Exclude delivered date, delay reason and post-order tracking; audit suburb/service disparities.\n\n"
        "MLQ-2 — Regression: Predict order total at session checkout for capacity and offer planning. Unit/target: order/final total. Use customer history, channel, season and pre-checkout basket features; temporal holdout and MAE. Coupon choice or final line totals can leak the target depending on decision time; monitor error by customer segment.\n\n"
        "MLQ-3 — Classification: Predict whether a review will be 1–2 stars to prioritise service recovery. Unit/target: completed order/review rating class. Use order, product, delivery-service and customer history available before review. Temporal split; PR-AUC and calibrated precision. Never use review text, helpful votes or post-review fields; non-reviewers create selection bias.\n\n"
        "MLQ-4 — Forecasting: Forecast weekly order counts by channel for staffing. Unit/target: channel-week/order count. Use lagged counts, calendar, season and known planned promotions; rolling-origin validation and WAPE. One year limits seasonal learning, and unknown future promotions/weather create deployment drift.\n\n"
        "MLQ-5 — Clustering: Identify product demand/value profiles for assortment review. Unit/objective: product, clustered on pre-period or rolling line volume, revenue, price, cost and review summaries. Validate stability across time windows and silhouette plus business interpretability. Scaling choices dominate clusters; popularity exposure and sparse products can bias conclusions.")
    with PdfPages(path) as pdf:
        _page(pdf,"FIT5196 A1 — Group030","Focused exploratory analysis of reconciled 2018 commerce and operations data\n\nPrepared from six standardised relational tables\n\nAssessed report: 7 figures, 10 findings, 5 future ML questions")
        _page(pdf,"1. Context and preparation assurance","The workflow integrates JSON commerce and XML operations exports into six analysis-ready tables at their published grains. Material decisions: structured parsing precedes regex; identifiers retain case and leading zeros; duplicate records are compared after normalisation and reconciled by business key; monetary arithmetic follows rounded line revenue, included GST, discount then delivery; multilingual cleaned reviews are preserved separately from Latin-only analysis (MAP-*).\n\nValidation evidence: all six schemas and field orders pass (VAL-SCHEMA-*); primary and foreign keys are complete and unique (VAL-PK-* / VAL-FK-*); no normalised cross-source conflicts remain (VAL-FLOW-01); arithmetic differences are within $0.01 (VAL-ARITH-*); temporal checks pass at the published date/timestamp precision (VAL-TIME-*); and literal NaN plus multilingual indicators pass (VAL-TEXT-*). Join assertions in the EDA preserve the left-table grain.")
        for start in [0,2,4,6]:
            figs=figures[start:start+2]; page=plt.figure(figsize=(8.27,11.69)); gs=page.add_gridspec(2,1)
            for idx,src in enumerate(figs):
                src.canvas.draw(); import numpy as np
                img=np.asarray(src.canvas.buffer_rgba()); ax=page.add_subplot(gs[idx]);ax.imshow(img);ax.axis("off")
            pdf.savefig(page,bbox_inches="tight");plt.close(page)
        _page(pdf,"3. Ten evidence-based findings","\n\n".join(findings),fontsize=8.7)
        _page(pdf,"4. Five future machine-learning questions",ml,fontsize=8.8)
        _page(pdf,"5. Limitations and conclusion","Limitations. The data cover one historical year and one retailer, so seasonality and external validity are limited. Associations are observational, repeated customers/products are not independent, and review analyses condition on customers who submitted reviews. Revenue is not profit; delivery-date fields are day-level; small language groups make subgroup estimates uncertain. No causal or model-performance claim is made.\n\nConclusion. The reconciled relational data show broad order-value variation, stable channel-level averages, commercially concentrated product-category revenue, high but imperfect OTIF performance and little raw relationship between review helpfulness and length. Operational prediction and forecasting are feasible next steps only with temporal evaluation, decision-time feature controls and subgroup monitoring.")
    for f in figures: plt.close(f)
    return m

if __name__=="__main__": print(build_report())
