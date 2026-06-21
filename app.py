import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(page_title="Cafe Sales Dashboard", page_icon="☕", layout="wide")

# ------------------------------------------------------------------
# Design tokens
# ------------------------------------------------------------------
INK = "#16191D"
MUTED = "#5C6470"
ACCENT = "#0E7C66"  # committed teal — avoids the coffee/cream cliché
# Cohesive categorical palette (teal-led, balanced warm/cool)
PALETTE = ["#0E7C66", "#E0A33E", "#3E5C76", "#C2557A", "#7A9E6E", "#9B6BB0", "#D9694A"]

# ------------------------------------------------------------------
# Global styling (fonts, layout, cards, sidebar)
# ------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"], .stApp { font-family: 'Inter', system-ui, sans-serif; }
      .stApp { background: #F3F4F6; }
      .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1300px; }

      /* Header */
      .app-title { font-family: 'Fraunces', serif; font-weight: 600; font-size: clamp(2rem, 4vw, 3rem);
                   color: #16191D; letter-spacing: -0.02em; margin: 0; line-height: 1.05; }
      .app-sub { color: #5C6470; font-size: 1rem; margin: .35rem 0 0; }
      .rule { height: 1px; background: rgba(22,25,29,.10); border: 0; margin: 1.4rem 0 1.8rem; }

      /* Section headings */
      .sec { font-family: 'Inter'; font-weight: 600; font-size: 1.05rem; color: #16191D;
             margin: .2rem 0 .6rem; letter-spacing: -0.01em; }

      /* Metric cards */
      div[data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid rgba(22,25,29,.08); border-radius: 16px;
        padding: 1.1rem 1.25rem; box-shadow: 0 1px 2px rgba(16,24,40,.04);
      }
      div[data-testid="stMetricLabel"] p { color: #5C6470; font-weight: 500; font-size: .82rem;
        text-transform: uppercase; letter-spacing: .04em; }
      div[data-testid="stMetricValue"] { color: #16191D; font-weight: 700; }

      /* Sidebar */
      section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid rgba(22,25,29,.08); }
      section[data-testid="stSidebar"] h2 { font-family: 'Inter'; font-weight: 600; }

      /* Chart cards */
      div[data-testid="stPlotlyChart"] {
        background: #FFFFFF; border: 1px solid rgba(22,25,29,.08); border-radius: 16px;
        padding: .5rem .25rem; box-shadow: 0 1px 2px rgba(16,24,40,.04);
      }
      #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig, height=340):
    """Apply a cohesive, restrained look to a Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)),
        hoverlabel=dict(font_family="Inter", bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(22,25,29,.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(22,25,29,.06)", zeroline=False)
    return fig


# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
@st.cache_data
def load_data(path: str = "clean_cafe_sales.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in ["Quantity", "Price Per Unit", "Total Spent"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    mask = df["Total Spent"].isna()
    df.loc[mask, "Total Spent"] = df.loc[mask, "Quantity"] * df.loc[mask, "Price Per Unit"]
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    df = df.dropna(subset=["Transaction Date", "Total Spent"])
    df["Month"] = df["Transaction Date"].dt.to_period("M").astype(str)
    df["Weekday"] = df["Transaction Date"].dt.day_name()
    for col in ["Item", "Payment Method", "Location"]:
        df[col] = df[col].fillna("Unknown").replace("", "Unknown")
    return df


df = load_data()

# ------------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------------
st.sidebar.markdown("## Filters")
sel_items = st.sidebar.multiselect("Item", sorted(df["Item"].unique()), default=sorted(df["Item"].unique()))
sel_pays = st.sidebar.multiselect("Payment method", sorted(df["Payment Method"].unique()), default=sorted(df["Payment Method"].unique()))
sel_locs = st.sidebar.multiselect("Location", sorted(df["Location"].unique()), default=sorted(df["Location"].unique()))
min_d, max_d = df["Transaction Date"].min(), df["Transaction Date"].max()
date_range = st.sidebar.date_input("Date range", [min_d, max_d], min_value=min_d, max_value=max_d)

f = df[df["Item"].isin(sel_items) & df["Payment Method"].isin(sel_pays) & df["Location"].isin(sel_locs)]
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    f = f[(f["Transaction Date"] >= start) & (f["Transaction Date"] <= end)]

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.markdown(
    "<div><h1 class='app-title'>☕ Cafe Sales Dashboard</h1>"
    "<p class='app-sub'>Interactive analysis of 2023 transactions</p></div>",
    unsafe_allow_html=True,
)
st.markdown("<hr class='rule'>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# KPIs
# ------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total revenue", f"${f['Total Spent'].sum():,.0f}")
c2.metric("Transactions", f"{len(f):,}")
c3.metric("Avg. order value", f"${f['Total Spent'].mean():,.2f}" if len(f) else "$0")
c4.metric("Units sold", f"{f['Quantity'].sum():,.0f}")

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Row 1 — revenue by item + payment mix
# ------------------------------------------------------------------
col1, col2 = st.columns([1.3, 1])
with col1:
    st.markdown("<p class='sec'>Revenue by item</p>", unsafe_allow_html=True)
    by_item = f.groupby("Item")["Total Spent"].sum().sort_values().reset_index()
    fig = px.bar(by_item, x="Total Spent", y="Item", orientation="h", text_auto=".2s")
    fig.update_traces(marker_color=ACCENT, textposition="outside", cliponaxis=False)
    st.plotly_chart(style_fig(fig), use_container_width=True)

with col2:
    st.markdown("<p class='sec'>Payment method mix</p>", unsafe_allow_html=True)
    by_pay = f.groupby("Payment Method")["Total Spent"].sum().reset_index()
    fig = px.pie(by_pay, values="Total Spent", names="Payment Method", hole=0.55,
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent", textfont_size=13)
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ------------------------------------------------------------------
# Row 2 — monthly trend
# ------------------------------------------------------------------
st.markdown("<p class='sec'>Monthly revenue trend</p>", unsafe_allow_html=True)
by_month = f.groupby("Month")["Total Spent"].sum().reset_index()
fig = px.area(by_month, x="Month", y="Total Spent", markers=True)
fig.update_traces(line_color=ACCENT, fillcolor="rgba(14,124,102,.10)",
                  marker=dict(size=7, color=ACCENT))
st.plotly_chart(style_fig(fig, height=320), use_container_width=True)

# ------------------------------------------------------------------
# Row 3 — location + weekday
# ------------------------------------------------------------------
col3, col4 = st.columns(2)
with col3:
    st.markdown("<p class='sec'>Revenue by location</p>", unsafe_allow_html=True)
    by_loc = f.groupby("Location")["Total Spent"].sum().reset_index()
    fig = px.bar(by_loc, x="Location", y="Total Spent", text_auto=".2s", color="Location",
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_fig(fig), use_container_width=True)

with col4:
    st.markdown("<p class='sec'>Revenue by weekday</p>", unsafe_allow_html=True)
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = f.groupby("Weekday")["Total Spent"].sum().reindex(order).reset_index()
    fig = px.bar(by_day, x="Weekday", y="Total Spent", text_auto=".2s")
    fig.update_traces(marker_color=ACCENT, textposition="outside", cliponaxis=False)
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ------------------------------------------------------------------
# Data table
# ------------------------------------------------------------------
with st.expander("View raw data"):
    st.dataframe(f, use_container_width=True)
    st.download_button(
        "Download filtered data (CSV)",
        f.to_csv(index=False).encode("utf-8-sig"),
        "filtered_cafe_sales.csv",
        "text/csv",
    )