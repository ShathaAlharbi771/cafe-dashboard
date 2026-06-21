import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(page_title="Cafe Dashboard", page_icon="☕", layout="wide")

# ------------------------------------------------------------------
# Palette (matches the admin-template look)
# ------------------------------------------------------------------
BLUE = "#2D9CDB"
ORANGE = "#F5A623"
GREEN = "#27AE60"
YELLOW = "#F2C94C"
RED = "#EB5757"
PURPLE = "#9B51E0"
INK = "#2B3245"
MUTED = "#8A93A6"
BARS = [RED, BLUE, YELLOW, GREEN, PURPLE, ORANGE]

# ------------------------------------------------------------------
# Global CSS
# ------------------------------------------------------------------
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp { font-family: 'Poppins', system-ui, sans-serif; }
.stApp { background: #D8E4F2; }
.block-container { padding: 1.4rem 1.8rem 3rem; max-width: 1500px; }
.title { font-weight:700; font-size:1.7rem; color:#2B3245; margin:.2rem 0 .1rem; }
/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#5f6e8e,#516086); }
section[data-testid="stSidebar"] label { color:#eaf0fa !important; font-weight:600 !important; font-size:.86rem !important; }
.brand { font-weight:700; letter-spacing:.14em; font-size:1.2rem; color:#fff; padding:.6rem .2rem 1rem; border-bottom:1px solid rgba(255,255,255,.14); margin-bottom:.6rem; }
.navhead { color:#c2cce0; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; margin:.8rem 0 1rem; font-weight:600; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div, section[data-testid="stSidebar"] [data-baseweb="input"] { background:#fff !important; border:1px solid rgba(255,255,255,.25) !important; border-radius:10px !important; }
section[data-testid="stSidebar"] [data-baseweb="tag"] { background:#2D9CDB !important; }
section[data-testid="stSidebar"] [data-baseweb="tag"] span { color:#fff !important; }
/* Top bar */
.topbar { display:flex; align-items:center; justify-content:space-between; background:#eef3fb; border-radius:12px; padding:.7rem 1.1rem; margin-bottom:.4rem; box-shadow:0 4px 14px rgba(31,45,80,.06); }
.search { flex:1; max-width:520px; background:#fff; border-radius:20px; padding:.5rem 1.1rem; color:#9aa3b5; border:1px solid #e3e9f3; }
.hi { color:#5f6e8e; font-weight:600; }
.crumb { color:#5f6e8e; font-weight:600; margin:.6rem 0 1rem; }
.crumb span { color:#9aa3b5; font-weight:500; }
/* Cards */
div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:none !important; border-radius:12px; box-shadow:0 8px 22px rgba(31,45,80,.08); padding:1.05rem 1.25rem; }
.card-h { color:#54607a; font-weight:600; font-size:1.02rem; margin:.1rem 0 .8rem; }
/* KPI */
.kpi-h { color:#54607a; font-weight:600; font-size:1rem; text-align:center; }
.kpi-v { font-weight:700; font-size:2.1rem; text-align:center; line-height:1.2; }
.kpi-s { color:#9aa3b5; font-size:.8rem; text-align:center; margin-bottom:.2rem; }
/* Progress list */
.pg-label { display:flex; justify-content:space-between; font-size:.86rem; color:#54607a; margin:.55rem 0 .25rem; font-weight:500; }
.pg-label b { color:#2B3245; font-weight:600; }
.track { height:8px; background:#eef1f6; border-radius:6px; overflow:hidden; }
.fill { height:8px; border-radius:6px; }
/* Recent list */
.news { padding:.55rem 0; border-bottom:1px solid #eef1f6; }
.news:last-child { border-bottom:0; }
.news-top { display:flex; justify-content:space-between; }
.news-top b { color:#2B3245; font-size:.9rem; font-weight:600; }
.news-top .t { color:#9aa3b5; font-size:.78rem; }
.news-sub { color:#8A93A6; font-size:.82rem; }
#MainMenu, footer, header { visibility:hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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
    df["MonthLbl"] = df["Transaction Date"].dt.strftime("%b")
    df["Weekday"] = df["Transaction Date"].dt.day_name()
    for col in ["Item", "Payment Method", "Location"]:
        df[col] = df[col].fillna("Unknown").replace("", "Unknown")
    return df


df = load_data()

# ------------------------------------------------------------------
# Header + filters (inside the dashboard)
# ------------------------------------------------------------------
st.markdown("<div class='title'>☕ Cafe Sales Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='crumb'>Dashboard &nbsp;&rsaquo;&nbsp; <span>Cafe Sales</span></div>", unsafe_allow_html=True)

with st.container(border=True):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_items = st.multiselect("Item", sorted(df["Item"].unique()), default=sorted(df["Item"].unique()))
    with fc2:
        sel_locs = st.multiselect("Location", sorted(df["Location"].unique()), default=sorted(df["Location"].unique()))
    with fc3:
        min_d, max_d = df["Transaction Date"].min(), df["Transaction Date"].max()
        date_range = st.date_input("Date range", [min_d, max_d], min_value=min_d, max_value=max_d)

f = df[df["Item"].isin(sel_items) & df["Location"].isin(sel_locs)]
if len(date_range) == 2:
    s, e = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    f = f[(f["Transaction Date"] >= s) & (f["Transaction Date"] <= e)]

st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def blank(fig, height):
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def rgba(hexc, a):
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def sparkline(series, color):
    fig = go.Figure(go.Scatter(y=series, mode="lines", line=dict(color=color, width=2.5),
                               fill="tozeroy", fillcolor=rgba(color, 0.20)))
    return blank(fig, 90)


# ------------------------------------------------------------------
# Row 1 — detailed line chart + top items
# ------------------------------------------------------------------
monthly = (f.groupby("Month")
             .agg(rev=("Total Spent", "sum"), cnt=("Total Spent", "size"), qty=("Quantity", "sum"))
             .reset_index())
monthly["lbl"] = pd.to_datetime(monthly["Month"]).dt.strftime("%b")

r1c1, r1c2 = st.columns([2, 1])
with r1c1:
    with st.container(border=True):
        st.markdown("<div class='card-h'>Monthly Revenue</div>", unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(x=monthly["lbl"], y=monthly["rev"], mode="lines+markers",
                                   line=dict(color=ORANGE, width=3),
                                   marker=dict(color=BLUE, size=9)))
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Poppins", color=MUTED, size=12))
        fig.update_xaxes(showgrid=False, linecolor="#e6ebf3")
        fig.update_yaxes(showgrid=True, griddash="dot", gridcolor="#e6ebf3", zeroline=False)
        st.plotly_chart(fig, use_container_width=True)

with r1c2:
    with st.container(border=True):
        st.markdown("<div class='card-h'>Top Items by Revenue</div>", unsafe_allow_html=True)
        top = f.groupby("Item")["Total Spent"].sum().sort_values(ascending=False).head(6)
        mx = top.max() if len(top) else 1
        html = ""
        for i, (name, val) in enumerate(top.items()):
            pct = val / mx * 100
            html += (f"<div class='pg-label'><b>{name}</b><span>${val:,.0f}</span></div>"
                     f"<div class='track'><div class='fill' style='width:{pct:.0f}%;"
                     f"background:{BARS[i % len(BARS)]}'></div></div>")
        st.markdown(html, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Row 2 — KPI cards with sparklines
# ------------------------------------------------------------------
k1, k2, k3 = st.columns(3)
kpis = [
    (k1, "Revenue", f"${f['Total Spent'].sum():,.0f}", BLUE, monthly["rev"], "total sales"),
    (k2, "Transactions", f"{len(f):,}", ORANGE, monthly["cnt"], "orders placed"),
    (k3, "Units Sold", f"{f['Quantity'].sum():,.0f}", GREEN, monthly["qty"], "items sold"),
]
for col, label, value, color, series, sub in kpis:
    with col:
        with st.container(border=True):
            st.markdown(
                f"<div class='kpi-h'>{label}</div>"
                f"<div class='kpi-v' style='color:{color}'>{value}</div>"
                f"<div class='kpi-s'>{sub}</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(sparkline(series, color), use_container_width=True,
                            config={"displayModeBar": False})

# ------------------------------------------------------------------
# Row 3 — gauge + bar chart + recent list
# ------------------------------------------------------------------
g1, g2, g3 = st.columns([1, 1.4, 1.1])

with g1:
    with st.container(border=True):
        st.markdown("<div class='card-h'>Top Item Share</div>", unsafe_allow_html=True)
        item_rev = f.groupby("Item")["Total Spent"].sum()
        share = (item_rev.max() / item_rev.sum() * 100) if item_rev.sum() else 0
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=share, number={"suffix": "%", "font": {"size": 34, "color": INK}},
            gauge={"axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": MUTED},
                   "bar": {"color": INK, "thickness": 0.18},
                   "steps": [{"range": [0, 33], "color": RED}, {"range": [33, 66], "color": ORANGE},
                             {"range": [66, 100], "color": GREEN}]}))
        fig.update_layout(height=240, margin=dict(l=20, r=20, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Poppins"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with g2:
    with st.container(border=True):
        st.markdown("<div class='card-h'>Revenue by Weekday</div>", unsafe_allow_html=True)
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        by_day = f.groupby("Weekday")["Total Spent"].sum().reindex(order).reset_index()
        by_day["lbl"] = by_day["Weekday"].str[:3]
        fig = px.bar(by_day, x="lbl", y="Total Spent")
        fig.update_traces(marker_color=[BARS[i % len(BARS)] for i in range(len(by_day))],
                          marker_line_width=0)
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Poppins", color=MUTED, size=12))
        fig.update_xaxes(showgrid=False, title=None, linecolor="#e6ebf3")
        fig.update_yaxes(showgrid=True, griddash="dot", gridcolor="#e6ebf3", title=None, zeroline=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with g3:
    with st.container(border=True):
        st.markdown("<div class='card-h'>Recent Transactions</div>", unsafe_allow_html=True)
        recent = f.sort_values("Transaction Date", ascending=False).head(5)
        html = ""
        for _, r in recent.iterrows():
            html += (f"<div class='news'><div class='news-top'><b>{r['Item']} · {r['Location']}</b>"
                     f"<span class='t'>{r['Transaction Date'].date()}</span></div>"
                     f"<div class='news-sub'>${r['Total Spent']:,.2f} · {r['Payment Method']}</div></div>")
        st.markdown(html, unsafe_allow_html=True)

# ------------------------------------------------------------------
# Raw data
# ------------------------------------------------------------------
with st.expander("View raw data"):
    st.dataframe(f, use_container_width=True)
    st.download_button("Download filtered data (CSV)",
                       f.to_csv(index=False).encode("utf-8-sig"),
                       "filtered_cafe_sales.csv", "text/csv")
