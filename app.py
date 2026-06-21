import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cafe Sales Dashboard", page_icon="☕", layout="wide")


# تحميل وتنظيف البيانات
@st.cache_data
def load_data(path: str = "clean_cafe_sales.csv") -> pd.DataFrame:
    df = pd.read_csv(path)

    # الأعمدة الرقمية: نحول النص لأرقام، والقيم الناقصة تصير NaN
    for col in ["Quantity", "Price Per Unit", "Total Spent"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # نعوّض Total Spent الناقص = الكمية * السعر إذا متوفرين
    mask = df["Total Spent"].isna()
    df.loc[mask, "Total Spent"] = df.loc[mask, "Quantity"] * df.loc[mask, "Price Per Unit"]

    # التاريخ
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    df = df.dropna(subset=["Transaction Date", "Total Spent"])

    # أعمدة مساعدة للوقت
    df["Month"] = df["Transaction Date"].dt.to_period("M").astype(str)
    df["Weekday"] = df["Transaction Date"].dt.day_name()

    # نعالج القيم "Unknown" بحيث تبقى ظاهرة بس واضحة
    for col in ["Item", "Payment Method", "Location"]:
        df[col] = df[col].fillna("Unknown").replace("", "Unknown")

    return df


df = load_data()

#الفلاتر 
# st.sidebar.header("🔎 الفلاتر")

items = sorted(df["Item"].unique())
sel_items = st.sidebar.multiselect("الصنف", items, default=items)

pays = sorted(df["Payment Method"].unique())
sel_pays = st.sidebar.multiselect("طريقة الدفع", pays, default=pays)

locs = sorted(df["Location"].unique())
sel_locs = st.sidebar.multiselect("المكان", locs, default=locs)

min_d, max_d = df["Transaction Date"].min(), df["Transaction Date"].max()
date_range = st.sidebar.date_input("الفترة الزمنية", [min_d, max_d], min_value=min_d, max_value=max_d)

# تطبيق الفلاتر
f = df[
    df["Item"].isin(sel_items)
    & df["Payment Method"].isin(sel_pays)
    & df["Location"].isin(sel_locs)
]
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    f = f[(f["Transaction Date"] >= start) & (f["Transaction Date"] <= end)]

# العنوان & (KPIs)
st.title("☕ لوحة مبيعات الكافيه")
st.markdown("تحليل تفاعلي لبيانات المبيعات لعام 2023")

c1, c2, c3, c4 = st.columns(4)
c1.metric("إجمالي المبيعات", f"${f['Total Spent'].sum():,.0f}")
c2.metric("عدد المعاملات", f"{len(f):,}")
c3.metric("متوسط قيمة المعاملة", f"${f['Total Spent'].mean():,.2f}" if len(f) else "$0")
c4.metric("إجمالي الكمية المباعة", f"{f['Quantity'].sum():,.0f}")

st.divider()

# الرسوم
col1, col2 = st.columns(2)

# المبيعات حسب الصنف
with col1:
    st.subheader("المبيعات حسب الصنف")
    by_item = f.groupby("Item")["Total Spent"].sum().sort_values(ascending=True).reset_index()
    fig = px.bar(by_item, x="Total Spent", y="Item", orientation="h", text_auto=".2s")
    st.plotly_chart(fig, use_container_width=True)

# توزيع طرق الدفع
with col2:
    st.subheader("طرق الدفع")
    by_pay = f.groupby("Payment Method")["Total Spent"].sum().reset_index()
    fig = px.pie(by_pay, values="Total Spent", names="Payment Method", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# اتجاه المبيعات الشهري
st.subheader("اتجاه المبيعات الشهري")
by_month = f.groupby("Month")["Total Spent"].sum().reset_index()
fig = px.line(by_month, x="Month", y="Total Spent", markers=True)
st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

# المبيعات حسب المكان
with col3:
    st.subheader("المبيعات حسب المكان")
    by_loc = f.groupby("Location")["Total Spent"].sum().reset_index()
    fig = px.bar(by_loc, x="Location", y="Total Spent", text_auto=".2s", color="Location")
    st.plotly_chart(fig, use_container_width=True)

# المبيعات حسب يوم الأسبوع
with col4:
    st.subheader("المبيعات حسب يوم الأسبوع")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = f.groupby("Weekday")["Total Spent"].sum().reindex(order).reset_index()
    fig = px.bar(by_day, x="Weekday", y="Total Spent", text_auto=".2s")
    st.plotly_chart(fig, use_container_width=True)

# جدول البيانات
with st.expander("📄 عرض البيانات الخام"):
    st.dataframe(f, use_container_width=True)
    st.download_button(
        "تحميل البيانات المفلترة (CSV)",
        f.to_csv(index=False).encode("utf-8-sig"),
        "filtered_cafe_sales.csv",
        "text/csv",
    )
