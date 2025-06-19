import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GrowthLens", layout="centered", initial_sidebar_state="expanded")
st.title("📊 GrowthLens – 企業分析＆決算レビューGPT用テンプレート生成")

if "history" not in st.session_state:
    st.session_state["history"] = []

# 企業名と売上・営業利益（共通項目）をセッション状態に保持
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

    # 他の非共通項目
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

出力は「強み・弱み・成長性・中長期リスク・競合優位性」の見出し＋箇条書き形式で整理してください。
"""
        st.session_state["history"].append({
            "モード": "企業分析",
            "企業名": name,
            "テンプレート": output.strip(),
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

# --------------------------
# 決算レビュー
# --------------------------
if mode == "決算レビュー":
    st.subheader("② 決算情報を入力してください")

    name = st.text_input("企業名", value=get_value("name"), key="name_2")

    default_year = int(str(datetime.now().year)[2:])
    fiscal_year = st.number_input("決算期（年, 例: 25）", min_value=0, max_value=99, value=default_year, step=1, key="fiscal_year")
    fiscal_month = st.number_input("決算期（月, 例: 6）", min_value=1, max_value=12, value=None, step=1, format="%d", key="fiscal_month")
    fiscal = f"20{fiscal_year:02d}年{fiscal_month}月期" if fiscal_month else "未入力"

    sales_current = st.number_input("今期売上高（百万円）", value=get_value("sales_current"), step=100.0, format="%.0f", key="sales_current_2")
    sales_prev = st.number_input("前期売上高（百万円）", value=get_value("sales_prev"), step=100.0, format="%.0f", key="sales_prev_2")
    op_profit = st.number_input("今期営業利益（百万円）", value=get_value("op_profit"), step=100.0, format="%.0f", key="op_profit_2")
    op_prev = st.number_input("前期営業利益（百万円）", value=get_value("op_prev"), step=100.0, format="%.0f", key="op_prev")
    net_current = st.number_input("今期純利益（百万円）", value=get_value("net_current"), step=100.0, format="%.0f", key="net_current")
    net_prev = st.number_input("前期純利益（百万円）", value=get_value("net_prev"), step=100.0, format="%.0f", key="net_prev")
    eps_current = st.number_input("今期EPS（円）", value=get_value("eps_current"), step=1.0, format="%.1f", key="eps_current")
    eps_prev = st.number_input("前期EPS（円）", value=get_value("eps_prev"), step=1.0, format="%.1f", key="eps_prev")
    future = st.text_area("会社コメント・来期見通し（任意）", value=get_value("future"), key="future")

    def calc_growth(current, previous):
        return ((current - previous) / previous * 100) if previous else 0

    sales_yoy = calc_growth(sales_current, sales_prev)
    op_yoy = calc_growth(op_profit, op_prev)
    net_yoy = calc_growth(net_current, net_prev)
    eps_yoy = calc_growth(eps_current, eps_prev)

    if st.button("📋 テンプレート生成", key="generate_review"):
        output = f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の決算情報に基づき、決算レビューを行ってください。

【企業名】{name}
【決算期】{fiscal}
【売上高】今期 {sales_current:,.0f} 百万円 ／ 前期 {sales_prev:,.0f} 百万円（前年比：{sales_yoy:.1f}%）
【営業利益】今期 {op_profit:,.0f} 百万円 ／ 前期 {op_prev:,.0f} 百万円（前年比：{op_yoy:.1f}%）
【純利益】今期 {net_current:,.0f} 百万円 ／ 前期 {net_prev:,.0f} 百万円（前年比：{net_yoy:.1f}%）
【EPS】今期 {eps_current:.1f} 円 ／ 前期 {eps_prev:.1f} 円（前年比：{eps_yoy:.1f}%）
【会社見通し・注記】{future}

出力は「良い点・懸念点・投資家視点でのまとめ」の見出し＋箇条書き形式で整理してください。
"""
        st.session_state["history"].append({
            "モード": "決算レビュー",
            "企業名": name,
            "テンプレート": output.strip(),
            "日時": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

# --------------------------
# 出力エリア＋コピー
# --------------------------
if output:
    st.text_area("📤 GPT用テンプレート（表示確認用）", value=output.strip(), height=350)
    components.html(f"""
        <textarea id="templateText" style="opacity:0; height:0;">{output.strip()}</textarea>
        <button onclick="
            var copyText = document.getElementById('templateText');
            copyText.select();
            document.execCommand('copy');
            alert('テンプレートをコピーしました！');
        " style="padding:10px 20px; font-size:16px; margin-top:10px;">📎 コピーする</button>
    """, height=70)

# --------------------------
# 履歴表示＆削除
# --------------------------
st.markdown("---")
st.subheader("📚 テンプレート履歴")

for i, item in enumerate(reversed(st.session_state["history"])):
    idx = len(st.session_state["history"]) - 1 - i
    cols = st.columns([6, 1])
    with cols[0]:
        st.markdown(f"- **{item['日時']}**｜{item['企業名']}（{item['モード']}）")
        with st.expander("▶ 内容を表示"):
            st.code(item["テンプレート"], language="markdown")
    with cols[1]:
        if st.button("🗑 削除", key=f"delete_{i}"):
            del st.session_state["history"][idx]
            st.rerun()

if st.session_state["history"]:
    if st.button("🗑️ 履歴をすべて削除"):
        st.session_state["history"].clear()
        st.success("履歴を削除しました")

    df = pd.DataFrame(st.session_state["history"])
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("💾 履歴をCSVでダウンロード", csv, file_name="growthlens_history.csv", mime="text/csv")