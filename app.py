import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GrowthLens", layout="centered", initial_sidebar_state="expanded")
st.title("📊 GrowthLens – 企業分析＆決算レビューGPT用テンプレート生成")

if "history" not in st.session_state:
    st.session_state["history"] = []

# 共通項目保持用のgetter
def get_value(key, default=None):
    return st.session_state.get(key, default)

mode = st.radio("モード選択", ["企業分析", "決算レビュー"])

output = ""

# --------------------------
# 企業分析モード
# --------------------------
if mode == "企業分析":
    st.subheader("① 企業情報を入力してください")

    name = st.text_input("企業名", value=get_value("name"), key="name")
    code = st.text_input("証券コード（任意）", value=get_value("code"), key="code")
    sales_current = st.number_input("今期売上高（百万円）", value=get_value("sales_current"), step=100.0, format="%.0f", key="sales_current")
    sales_prev = st.number_input("前期売上高（百万円）", value=get_value("sales_prev"), step=100.0, format="%.0f", key="sales_prev")
    op_profit = st.number_input("営業利益（百万円）", value=get_value("op_profit"), step=100.0, format="%.0f", key="op_profit")

    # 非共有項目
    roe = st.text_input("ROE（%）", value=get_value("roe"), key="roe")
    per = st.text_input("PER（倍）", value=get_value("per"), key="per")
    capital_ratio = st.text_input("自己資本比率（%）", value=get_value("capital_ratio"), key="capital_ratio")
    dividend = st.text_input("配当利回り（%）", value=get_value("dividend"), key="dividend")
    business = st.text_area("主な事業内容", value=get_value("business"), key="business")
    theme = st.text_input("成長テーマ（例：AI、半導体、ヘルスケア など）", value=get_value("theme"), key="theme")

    sales_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0
    op_margin = (op_profit / sales_current * 100) if sales_current else 0

    if st.button("📋 テンプレート生成", key="generate_analysis"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の企業データに基づき、企業分析を行ってください。

【企業名】{name}
【証券コード】{code}
【売上高】今期 {sales_current:,.0f} 百万円 ／ 前期 {sales_prev:,.0f} 百万円（成長率：{sales_growth:.1f}%）
【営業利益】{op_profit:,.0f} 百万円（営業利益率：{op_margin:.1f}%）
【ROE】{roe}%
【PER】{per}倍
【自己資本比率】{capital_ratio}%
【配当利回り】{dividend}%
【主な事業内容】{business}
【成長テーマ】{theme}

出力は「強み・弱み・成長性・中長期リスク・競合優位性」の見出し＋箇条書き形式で整理してください。分析は中長期（3〜10年）目線で行い、最新の成長テーマ（AI、量子コンピュータ、半導体、DX、ESG等）を積極的に考慮してください。
"""
        st.session_state["history"].append({
            "モード": "企業分析",
            "企業名": name,
            "テンプレート": output.strip(),
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=350)
        st.button("📋 コピー", on_click=st.experimental_set_query_params, key="copy_btn")

# --------------------------
# 決算レビュー
# --------------------------
else:
    st.subheader("② 決算情報を入力してください")

    name = st.text_input("企業名", value=get_value("name"), key="name_review")

    # 年月分割
    now = datetime.now()
    default_year = int(str(now.year)[2:])
    fiscal_year = st.number_input("決算期（年, 例: 25）", min_value=0, max_value=99, value=default_year, step=1, key="fiscal_year")
    fiscal_month = st.number_input("決算期（月, 例: 6）", min_value=1, max_value=12, step=1, key="fiscal_month")
    fiscal = f"20{fiscal_year}年{fiscal_month}月期"

    # 共通項目
    sales = st.number_input("売上高（百万円）", value=get_value("sales_current"), step=100.0, format="%.0f", key="sales_review")
    sales_prev = st.number_input("前期売上高（百万円）", value=get_value("sales_prev"), step=100.0, format="%.0f", key="sales_prev_review")
    op_profit = st.number_input("営業利益（百万円）", value=get_value("op_profit"), step=100.0, format="%.0f", key="op_review")
    op_prev = st.number_input("前期営業利益（百万円）", value=0.0, step=100.0, format="%.0f", key="op_prev")

    net_profit = st.number_input("純利益（百万円）", step=100.0, format="%.0f", key="net_profit")
    net_prev = st.number_input("前期純利益（百万円）", step=100.0, format="%.0f", key="net_prev")
    eps = st.text_input("EPS（円）", key="eps")
    future = st.text_area("会社コメント・来期見通し（任意）", key="future")

    # 自動計算
    sales_yoy = ((sales - sales_prev) / sales_prev * 100) if sales_prev else 0
    op_yoy = ((op_profit - op_prev) / op_prev * 100) if op_prev else 0
    net_yoy = ((net_profit - net_prev) / net_prev * 100) if net_prev else 0

    op_prev_display = f"{op_prev:,.0f}" if op_prev else "―"
    op_yoy_display = f"{op_yoy:.1f}%" if op_prev else "―"

    if st.button("📋 テンプレート生成", key="generate_review"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の決算情報に基づき、決算レビューを行ってください。

【企業名】{name}
【決算期】{fiscal}
【売上高】{sales:,.0f} 百万円 ／ 前期 {sales_prev:,.0f} 百万円（前年比：{sales_yoy:.1f}%）
【営業利益】今期 {op_profit:,.0f} 百万円 ／ 前期 {op_prev_display} 百万円（前年比：{op_yoy_display}）
【純利益】今期 {net_profit:,.0f} 百万円 ／ 前期 {net_prev:,.0f} 百万円（前年比：{net_yoy:.1f}%）
【EPS】{eps}円
【会社見通し・注記】{future}

出力は「決算の総合評価・良い点・懸念点・中長期投資家としての判断材料・今後の注意点」の見出し＋箇条書き形式で整理してください。
"""
        st.session_state["history"].append({
            "モード": "決算レビュー",
            "企業名": name,
            "テンプレート": output.strip(),
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=350)
        st.button("📋 コピー", on_click=st.experimental_set_query_params, key="copy_btn_review")

# --------------------------
# 履歴の表示・削除
# --------------------------
st.markdown("---")
st.subheader("📚 生成履歴")
for i, item in enumerate(reversed(st.session_state["history"])):
    with st.expander(f"{item['日時']} ｜ {item['モード']} ｜ {item['企業名']}"):
        st.code(item["テンプレート"], language="markdown")
        if st.button(f"🗑 削除", key=f"delete_{i}"):
            del st.session_state["history"][len(st.session_state["history"]) - 1 - i]
            st.experimental_rerun()