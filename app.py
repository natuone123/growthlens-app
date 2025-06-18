import streamlit as st

st.set_page_config(page_title="GrowthLens", layout="centered", initial_sidebar_state="expanded")

st.title("📊 GrowthLens – 企業分析＆決算レビューGPT用テンプレート生成")

mode = st.radio("モード選択", ["企業分析", "決算レビュー"])

if mode == "企業分析":
    st.subheader("① 企業情報を入力してください")

    name = st.text_input("企業名")
    code = st.text_input("証券コード（任意）")
    sales_growth = st.text_input("売上成長率（%）")
    op_margin = st.text_input("営業利益率（%）")
    roe = st.text_input("ROE（%）")
    per = st.text_input("PER（倍）")
    capital_ratio = st.text_input("自己資本比率（%）")
    dividend = st.text_input("配当利回り（%）")
    business = st.text_area("主な事業内容")
    theme = st.text_input("成長テーマ（例：AI、半導体、ヘルスケア など）")

    if st.button("📋 テンプレート生成"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の企業データに基づき、企業分析を行ってください。

【企業名】{name}
【証券コード】{code}
【売上成長率】{sales_growth}%
【営業利益率】{op_margin}%
【ROE】{roe}%
【PER】{per}倍
【自己資本比率】{capital_ratio}%
【配当利回り】{dividend}%
【主な事業内容】{business}
【成長テーマ】{theme}

出力は「強み・弱み・成長性・中長期リスク・競合優位性」の見出し＋箇条書き形式で整理してください。
"""
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=300)

else:
    st.subheader("② 決算情報を入力してください")

    name = st.text_input("企業名")
    fiscal = st.text_input("決算期（例：2025年3月期）")
    sales = st.text_input("売上高（億円）")
    yoy = st.text_input("売上前年同期比（%）")
    op_profit = st.text_input("営業利益（億円）")
    op_yoy = st.text_input("営業利益前年同期比（%）")
    net_profit = st.text_input("純利益（億円）")
    net_yoy = st.text_input("純利益前年同期比（%）")
    eps = st.text_input("EPS（円）")
    future = st.text_area("会社コメント・来期見通し（任意）")

    if st.button("📋 テンプレート生成"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の決算情報に基づき、決算レビューを行ってください。

【企業名】{name}
【決算期】{fiscal}
【売上高】{sales}億円（前年比{yoy}%）
【営業利益】{op_profit}億円（前年比{op_yoy}%）
【純利益】{net_profit}億円（前年比{net_yoy}%）
【EPS】{eps}円
【会社見通し・注記】{future}

出力は「良い点・懸念点・投資家視点でのまとめ」の見出し＋箇条書き形式で整理してください。
"""
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=300)
