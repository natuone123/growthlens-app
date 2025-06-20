import streamlit as st
from datetime import datetime

# アプリ設定
st.set_page_config(page_title="GrowthLens", layout="centered", initial_sidebar_state="expanded")

# 🌱 ロゴ画像を表示（ファビコンと同じ画像）
st.image("https://raw.githubusercontent.com/natuone123/growthlens-app/main/.streamlit/growthlens_logo.png", width=80)

# アプリタイトル
st.title("GrowthLens – 企業分析＆決算レビューGPT用テンプレート生成")

# モード選択
mode = st.radio("モード選択", ["企業分析", "決算レビュー"])

# 履歴保存用セッション状態初期化
if "history" not in st.session_state:
    st.session_state.history = []

# --- 企業分析モード ---
if mode == "企業分析":
    st.subheader("① 企業情報を入力してください")

    name = st.text_input("企業名", value=st.session_state.get("企業名", ""))
    code = st.text_input("証券コード（任意）", value=st.session_state.get("証券コード", ""))
    sales_current = st.number_input("今期売上高（百万円）", step=1, value=st.session_state.get("今期売上高", 0))
    sales_prev = st.number_input("前期売上高（百万円）", step=1, value=st.session_state.get("前期売上高", 0))
    op_profit = st.number_input("営業利益（百万円）", step=1, value=st.session_state.get("営業利益", 0))
    roe = st.text_input("ROE（%）", value=st.session_state.get("ROE", ""))
    per = st.text_input("PER（倍）", value=st.session_state.get("PER", ""))
    capital_ratio = st.text_input("自己資本比率（%）", value=st.session_state.get("自己資本比率", ""))
    dividend = st.text_input("配当利回り（%）", value=st.session_state.get("配当利回り", ""))
    business = st.text_area("主な事業内容", value=st.session_state.get("主な事業内容", ""))
    theme = st.text_input("成長テーマ（例：AI、半導体、ヘルスケア など）", value=st.session_state.get("成長テーマ", ""))

    sales_growth = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0
    op_margin = (op_profit / sales_current * 100) if sales_current else 0

    if st.button("📋 テンプレート生成"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の企業データに基づき、企業分析を行ってください。

【企業名】{name}
【証券コード】{code}
【売上高】今期 {sales_current:,} 百万円 ／ 前期 {sales_prev:,} 百万円（成長率：{sales_growth:.1f}%）
【営業利益】{op_profit:,} 百万円（営業利益率：{op_margin:.1f}%）
【ROE】{roe}%
【PER】{per}倍
【自己資本比率】{capital_ratio}%
【配当利回り】{dividend}%
【主な事業内容】{business}
【成長テーマ】{theme}

出力は「強み・弱み・成長性・中長期リスク・競合優位性」の見出し＋箇条書き形式で整理してください。
分析は中長期（3〜10年）目線で行い、最新の成長テーマ（AI、量子コンピュータ、半導体、DX、ESG等）を積極的に考慮してください。
"""
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=350)
        st.code(output.strip(), language="markdown")
        st.session_state.history.append(("企業分析", datetime.now(), output.strip()))
        # 入力値の保存（相互反映用）
        st.session_state["企業名"] = name
        st.session_state["証券コード"] = code
        st.session_state["今期売上高"] = sales_current
        st.session_state["前期売上高"] = sales_prev
        st.session_state["営業利益"] = op_profit
        st.session_state["ROE"] = roe
        st.session_state["PER"] = per
        st.session_state["自己資本比率"] = capital_ratio
        st.session_state["配当利回り"] = dividend
        st.session_state["主な事業内容"] = business
        st.session_state["成長テーマ"] = theme

# --- 決算レビュー モード ---
else:
    st.subheader("② 決算情報を入力してください")

    name = st.text_input("企業名", value=st.session_state.get("企業名", ""))
    fiscal_year = st.number_input("決算期（年, 例: 25）", step=1)
    fiscal_month = st.number_input("決算期（月, 例: 6）", min_value=1, max_value=12, step=1)
    sales_current = st.number_input("今期売上高（百万円）", step=1)
    sales_prev = st.number_input("前期売上高（百万円）", step=1)
    op_current = st.number_input("今期営業利益（百万円）", step=1)
    op_prev = st.number_input("前期営業利益（百万円）", step=1)
    net_profit = st.text_input("純利益（百万円）")
    net_yoy = st.text_input("純利益前年同期比（%）")
    eps = st.text_input("EPS（円）")
    future = st.text_area("会社コメント・来期見通し（任意）")

    sales_yoy = ((sales_current - sales_prev) / sales_prev * 100) if sales_prev else 0
    op_yoy = ((op_current - op_prev) / op_prev * 100) if op_prev else 0

    if st.button("📋 テンプレート生成"):
        fiscal_str = f"20{fiscal_year:.0f}年{fiscal_month:.0f}月期"
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の決算情報に基づき、決算レビューを行ってください。

【企業名】{name}
【決算期】{fiscal_str}
【売上高】今期 {sales_current:,} 百万円 ／ 前期 {sales_prev:,} 百万円（前年比：{sales_yoy:.1f}%）
【営業利益】今期 {op_current:,} 百万円 ／ 前期 {op_prev:,} 百万円（前年比：{op_yoy:.1f}%）
【純利益】{net_profit} 百万円（前年比：{net_yoy}%）
【EPS】{eps}円
【会社見通し・注記】{future}

出力は「決算の総合評価・良い点・懸念点・中長期投資家としての判断材料・今後の注意点」の見出し＋箇条書き形式で整理してください。
"""
        st.text_area("📤 GPT用テンプレート", value=output.strip(), height=320)
        st.code(output.strip(), language="markdown")
        st.session_state.history.append(("決算レビュー", datetime.now(), output.strip()))
        # 入力内容の保存
        st.session_state["企業名"] = name
        st.session_state["今期売上高"] = sales_current
        st.session_state["前期売上高"] = sales_prev
        st.session_state["営業利益"] = op_current

# --- 履歴表示・削除 ---
with st.expander("📜 生成履歴"):
    for i, (mode_str, ts, content) in enumerate(reversed(st.session_state.history)):
        st.markdown(f"**{mode_str}**（{ts.strftime('%Y-%m-%d %H:%M:%S')}）")
        st.code(content, language="markdown")
    if st.button("🗑️ 履歴を全て削除"):
        st.session_state.history.clear()
        st.rerun()