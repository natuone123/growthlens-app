import html
import re
from io import BytesIO
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components


LOGO_URL = "https://raw.githubusercontent.com/natuone123/growthlens-app/main/.streamlit/growthlens_logo.png"
FAVICON_URL = "https://raw.githubusercontent.com/natuone123/growthlens-app/main/.streamlit/growthlens_favicon.ico"


st.set_page_config(
    page_title="GrowthLens",
    page_icon=FAVICON_URL,
    layout="centered",
    initial_sidebar_state="collapsed",
)


def init_state():
    defaults = {
        "history": [],
        "holding_memos": [],
        "企業名": "",
        "証券コード": "",
        "主な事業内容": "",
        "成長テーマ": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def pct(numerator, denominator):
    return numerator / denominator * 100 if denominator else 0.0


def multiple(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def fmt_pct(value):
    return f"{value:.1f}%"


def fmt_multiple(value):
    return f"{value:.1f}倍" if value else "算出不可"


def fmt_money(value):
    return f"{value:,.0f} 百万円"


def add_history(kind, company, content):
    st.session_state.history.append(
        {
            "kind": kind,
            "company": company or "未入力",
            "timestamp": datetime.now(),
            "content": content.strip(),
        }
    )


def output_box(label, content, key):
    st.markdown(f"**{label}**")
    safe_content = html.escape(content.strip())
    components.html(
        f"""
        <div style="position: relative;">
            <textarea id="{key}" readonly
                style="width:100%; height:360px; box-sizing:border-box; padding:12px 14px;
                       border:1px solid #3f434d; border-radius:8px; color:#fafafa;
                       background:#111827; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                       font-size:13px; line-height:1.55;">{safe_content}</textarea>
            <button
                onclick="navigator.clipboard.writeText(document.getElementById('{key}').value)"
                style="position:absolute; top:10px; right:10px; border:0; border-radius:6px;
                       background:#4CAF50; color:white; padding:7px 12px; cursor:pointer;">
                コピー
            </button>
        </div>
        """,
        height=390,
    )


def number_input(label, key, min_value=None, help_text=None):
    return st.number_input(
        label,
        min_value=min_value,
        value=0.0,
        step=1.0,
        format="%.2f",
        key=key,
        help=help_text,
    )


def normalize_text(text):
    return (
        text.replace("△", "-")
        .replace("▲", "-")
        .replace("−", "-")
        .replace("－", "-")
        .replace("（", "(")
        .replace("）", ")")
        .replace("，", ",")
        .replace("％", "%")
    )


def read_pdf_text(uploaded_file):
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "PDF読み取りに必要な pypdf がインストールされていません。"

    try:
        reader = PdfReader(BytesIO(uploaded_file.getvalue()))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text(extraction_mode="layout") or "")
            except TypeError:
                pages.append(page.extract_text() or "")
        return "\n".join(pages), ""
    except Exception as exc:
        return "", f"PDFを読み取れませんでした: {exc}"


def extract_numbers(line):
    normalized = normalize_text(line)
    matches = re.finditer(r"[-]?\(?\d[\d,]*(?:\.\d+)?\)?\s*%?", normalized)
    values = []
    for match in matches:
        raw = match.group().strip()
        is_percent = raw.endswith("%")
        cleaned = raw.replace("%", "").replace(",", "").replace("(", "-").replace(")", "")
        try:
            values.append({"value": float(cleaned), "is_percent": is_percent})
        except ValueError:
            continue
    return values


def is_likely_table_header(line):
    if ("年" in line and "期" in line) or "前期" in line or "当期" in line:
        return True
    header_words = ["百万円", "％", "%", "円", "銭", "会計期間", "連結累計期間", "期", "年度"]
    return any(word in line for word in header_words) and not extract_numbers(line)


def clean_number_candidates(values):
    cleaned = []
    for item in values:
        value = item["value"]
        if item["is_percent"]:
            continue
        if 1900 <= abs(value) <= 2100:
            continue
        cleaned.append(item)
    return cleaned


def values_from_nearby_lines(lines, start_index, matched_label, max_following_lines=6):
    first_line = lines[start_index]
    first_target = first_line.split(matched_label, 1)[1] or first_line
    candidate_lines = [first_target]

    for offset in range(1, max_following_lines + 1):
        if start_index + offset >= len(lines):
            break

        line = lines[start_index + offset]
        if any(stop in line for stop in ["営業利益", "経常利益", "純利益", "売上高", "売上収益", "営業収益", "1株当たり", "キャッシュ"]):
            break
        if is_likely_table_header(line):
            continue
        candidate_lines.append(line)

    values = []
    for line in candidate_lines:
        values.extend(extract_numbers(line))
    return clean_number_candidates(values), " / ".join(candidate_lines).strip()


def find_line_values(lines, labels):
    for index, line in enumerate(lines):
        matched_label = next((label for label in labels if label in line), "")
        if matched_label:
            values, source = values_from_nearby_lines(lines, index, matched_label)
            if values:
                return values, line if line in source else f"{line} / {source}"
    return [], ""


def current_and_previous(values, is_eps=False):
    if not values:
        return 0.0, 0.0

    current = values[0]["value"]
    if len(values) == 1:
        return current, 0.0

    if is_eps:
        return current, values[1]["value"]

    if len(values) >= 3 and 0 < abs(values[1]["value"]) <= 300:
        return current, values[2]["value"]

    non_percent = [item["value"] for item in values if not item["is_percent"]]
    if len(non_percent) >= 2:
        return non_percent[0], non_percent[1]

    if len(values) >= 3 and abs(values[1]["value"]) <= 300:
        return current, values[2]["value"]

    return current, values[1]["value"]


def current_only(values):
    return values[0]["value"] if values else 0.0


def parse_financial_values_from_text(text):
    lines = [line.strip() for line in normalize_text(text).splitlines() if line.strip()]

    sales_values, sales_line = find_line_values(lines, ["売上高", "売上収益", "営業収益"])
    op_values, op_line = find_line_values(lines, ["営業利益", "営業損失"])
    net_values, net_line = find_line_values(
        lines,
        [
            "親会社株主に帰属する当期純利益",
            "親会社の所有者に帰属する当期利益",
            "親会社株主に帰属する四半期純利益",
            "当期純利益",
            "四半期純利益",
        ],
    )
    eps_values, eps_line = find_line_values(
        lines,
        [
            "1株当たり当期純利益",
            "1株当たり四半期純利益",
            "１株当たり当期純利益",
            "１株当たり四半期純利益",
            "基本的1株当たり当期利益",
            "基本的１株当たり当期利益",
        ],
    )
    operating_cf_values, operating_cf_line = find_line_values(
        lines,
        ["営業活動によるキャッシュ・フロー", "営業活動によるキャッシュフロー"],
    )
    investing_cf_values, investing_cf_line = find_line_values(
        lines,
        ["投資活動によるキャッシュ・フロー", "投資活動によるキャッシュフロー"],
    )

    sales_current, sales_prev = current_and_previous(sales_values)
    op_current, op_prev = current_and_previous(op_values)
    net_profit, net_profit_prev = current_and_previous(net_values)
    eps_current, eps_prev = current_and_previous(eps_values, is_eps=True)

    return {
        "earnings_sales_current": sales_current,
        "earnings_sales_prev": sales_prev,
        "earnings_op_current": op_current,
        "earnings_op_prev": op_prev,
        "earnings_net_profit": net_profit,
        "earnings_net_profit_prev": net_profit_prev,
        "earnings_eps_current": eps_current,
        "earnings_eps_prev": eps_prev,
        "earnings_operating_cf": current_only(operating_cf_values),
        "earnings_investing_cf": current_only(investing_cf_values),
        "_source_lines": {
            "売上高": sales_line,
            "営業利益": op_line,
            "純利益": net_line,
            "EPS": eps_line,
            "営業CF": operating_cf_line,
            "投資CF": investing_cf_line,
        },
    }


def build_editable_extracted_values(extracted):
    st.markdown("**抽出候補**")
    st.caption("ずれている値はここで修正してから入力欄へ反映できます。")

    rows = [
        ("今期売上高", "earnings_sales_current"),
        ("前期売上高", "earnings_sales_prev"),
        ("今期営業利益", "earnings_op_current"),
        ("前期営業利益", "earnings_op_prev"),
        ("今期純利益", "earnings_net_profit"),
        ("前期純利益", "earnings_net_profit_prev"),
        ("今期EPS", "earnings_eps_current"),
        ("前期EPS", "earnings_eps_prev"),
        ("営業CF", "earnings_operating_cf"),
        ("投資CF", "earnings_investing_cf"),
    ]

    edited = {"_source_lines": extracted["_source_lines"]}
    for index in range(0, len(rows), 2):
        columns = st.columns(2)
        for col, (label, key) in zip(columns, rows[index : index + 2]):
            edited[key] = col.number_input(
                label,
                value=float(extracted.get(key, 0.0)),
                step=1.0,
                format="%.2f",
                key=f"extracted_{key}",
            )
    return edited


def apply_extracted_values(values):
    for key, value in values.items():
        if key.startswith("_"):
            continue
        if value:
            st.session_state[key] = float(value)


def render_pdf_importer():
    with st.expander("決算短信PDFから数字を取り込む", expanded=False):
        uploaded_file = st.file_uploader("決算短信PDF", type=["pdf"], key="earnings_pdf")
        st.caption("読み取った値は候補です。反映後に必ず決算短信の原文と照合してください。")

        if not uploaded_file:
            return

        text, error = read_pdf_text(uploaded_file)
        if error:
            st.error(error)
            return

        extracted = build_editable_extracted_values(parse_financial_values_from_text(text))

        if st.button("候補値を入力欄へ反映", key="apply_pdf_values"):
            apply_extracted_values(extracted)
            st.success("候補値を反映しました。各入力欄を確認してください。")
            st.rerun()

        with st.expander("読み取り元の行を確認"):
            for label, line in extracted["_source_lines"].items():
                st.write(f"{label}: {line or '見つかりませんでした'}")

        with st.expander("PDFから抽出したテキストを確認"):
            st.text_area("抽出テキスト", value=text[:8000], height=220, disabled=True)


def calculate_metrics(data):
    fcf = data["operating_cf"] + data["investing_cf"]
    market_cap = data["market_cap"]
    if not market_cap and data["stock_price"] and data["shares_outstanding"]:
        market_cap = data["stock_price"] * data["shares_outstanding"] / 1_000_000

    metrics = {
        "売上成長率": pct(data["sales_current"] - data["sales_prev"], data["sales_prev"]),
        "営業利益成長率": pct(data["op_current"] - data["op_prev"], data["op_prev"]),
        "営業利益率": pct(data["op_current"], data["sales_current"]),
        "純利益率": pct(data["net_profit"], data["sales_current"]),
        "EPS成長率": pct(data["eps_current"] - data["eps_prev"], data["eps_prev"]),
        "ROE": pct(data["net_profit"], data["equity"]),
        "自己資本比率": pct(data["equity"], data["total_assets"]),
        "ネットキャッシュ": data["cash"] - data["interest_bearing_debt"],
        "PER": multiple(market_cap, data["net_profit"]),
        "PSR": multiple(market_cap, data["sales_current"]),
        "FCF": fcf,
        "FCFマージン": pct(fcf, data["sales_current"]),
        "配当性向": pct(data["dividend_total"], data["net_profit"]),
        "時価総額": market_cap,
    }
    return metrics


def score_company(metrics):
    growth = 5 if metrics["売上成長率"] >= 20 else 4 if metrics["売上成長率"] >= 10 else 3 if metrics["売上成長率"] >= 3 else 2 if metrics["売上成長率"] >= 0 else 1
    profitability = 5 if metrics["営業利益率"] >= 20 else 4 if metrics["営業利益率"] >= 12 else 3 if metrics["営業利益率"] >= 7 else 2 if metrics["営業利益率"] > 0 else 1
    finance = 5 if metrics["自己資本比率"] >= 60 and metrics["ネットキャッシュ"] >= 0 else 4 if metrics["自己資本比率"] >= 40 else 3 if metrics["自己資本比率"] >= 25 else 2 if metrics["自己資本比率"] > 0 else 1
    cash_quality = 5 if metrics["FCFマージン"] >= 12 else 4 if metrics["FCFマージン"] >= 6 else 3 if metrics["FCF"] >= 0 else 2 if metrics["FCFマージン"] >= -5 else 1

    per = metrics["PER"]
    psr = metrics["PSR"]
    if not per:
        valuation = "判定保留"
    elif per <= 15 and psr <= 2:
        valuation = "割安"
    elif per <= 30 and psr <= 5:
        valuation = "妥当"
    else:
        valuation = "割高"

    average = (growth + profitability + finance + cash_quality) / 4
    if average >= 4.2 and valuation != "割高":
        fit = "A"
    elif average >= 3.4:
        fit = "B"
    elif average >= 2.6:
        fit = "C"
    else:
        fit = "D"

    return {
        "成長性": growth,
        "収益性": profitability,
        "財務安全性": finance,
        "利益の質": cash_quality,
        "バリュエーション": valuation,
        "投資スタイル適合度": fit,
    }


def render_metric_summary(metrics, scores):
    col1, col2, col3 = st.columns(3)
    col1.metric("売上成長率", fmt_pct(metrics["売上成長率"]))
    col2.metric("営業利益率", fmt_pct(metrics["営業利益率"]))
    col3.metric("FCFマージン", fmt_pct(metrics["FCFマージン"]))

    col4, col5, col6 = st.columns(3)
    col4.metric("ROE", fmt_pct(metrics["ROE"]))
    col5.metric("PER", fmt_multiple(metrics["PER"]))
    col6.metric("適合度", scores["投資スタイル適合度"])

    st.caption(
        f"ネットキャッシュ: {fmt_money(metrics['ネットキャッシュ'])} / "
        f"PSR: {fmt_multiple(metrics['PSR'])} / "
        f"バリュエーション: {scores['バリュエーション']}"
    )


def company_analysis_prompt(name, code, business, theme, data, metrics, scores, hypothesis):
    return f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の一次情報と自動計算指標に基づき、投資判断に使える企業分析を行ってください。

【企業名】{name}
【証券コード】{code}
【主な事業内容】{business}
【成長テーマ】{theme}

【一次情報】
売上高: 今期 {fmt_money(data['sales_current'])} / 前期 {fmt_money(data['sales_prev'])}
営業利益: 今期 {fmt_money(data['op_current'])} / 前期 {fmt_money(data['op_prev'])}
純利益: {fmt_money(data['net_profit'])}
EPS: 今期 {data['eps_current']:.2f}円 / 前期 {data['eps_prev']:.2f}円
営業CF: {fmt_money(data['operating_cf'])}
投資CF: {fmt_money(data['investing_cf'])}
現金等: {fmt_money(data['cash'])}
有利子負債: {fmt_money(data['interest_bearing_debt'])}
自己資本: {fmt_money(data['equity'])}
総資産: {fmt_money(data['total_assets'])}
発行済株式数: {data['shares_outstanding']:,.0f}株
株価: {data['stock_price']:,.2f}円
時価総額: {fmt_money(metrics['時価総額'])}
年間配当総額: {fmt_money(data['dividend_total'])}

【自動計算指標】
売上成長率: {fmt_pct(metrics['売上成長率'])}
営業利益成長率: {fmt_pct(metrics['営業利益成長率'])}
営業利益率: {fmt_pct(metrics['営業利益率'])}
純利益率: {fmt_pct(metrics['純利益率'])}
EPS成長率: {fmt_pct(metrics['EPS成長率'])}
ROE: {fmt_pct(metrics['ROE'])}
自己資本比率: {fmt_pct(metrics['自己資本比率'])}
ネットキャッシュ: {fmt_money(metrics['ネットキャッシュ'])}
PER: {fmt_multiple(metrics['PER'])}
PSR: {fmt_multiple(metrics['PSR'])}
FCF: {fmt_money(metrics['FCF'])}
FCFマージン: {fmt_pct(metrics['FCFマージン'])}
配当性向: {fmt_pct(metrics['配当性向'])}

【アプリ側の仮スコア】
成長性: {scores['成長性']}/5
収益性: {scores['収益性']}/5
財務安全性: {scores['財務安全性']}/5
利益の質: {scores['利益の質']}/5
バリュエーション: {scores['バリュエーション']}
投資スタイル適合度: {scores['投資スタイル適合度']}

【投資仮説】
{hypothesis}

以下の形式で、文章よりも判定と根拠を重視して出力してください。
1. 投資判断サマリー
2. スコア評価（成長性・収益性・財務安全性・競争優位性・バリュエーション許容度）
3. 投資仮説が成り立つ理由
4. 反証条件
5. 買う前チェックリスト
6. 30%下落時にも保有できるか
7. 現在の判断（新規検討・継続・買い増し・縮小・売却検討）
8. 次に確認すべき一次情報
""".strip()


def earnings_review_prompt(name, period, data, metrics, thesis_impact, current_decision, comment):
    return f"""
あなたは中長期投資家を支援するAI株式アナリストです。
以下の決算情報に基づき、保有判断に直結する厳しめの決算レビューを行ってください。

【企業名】{name}
【決算期】{period}

【一次情報】
売上高: 今期 {fmt_money(data['sales_current'])} / 前期 {fmt_money(data['sales_prev'])}
営業利益: 今期 {fmt_money(data['op_current'])} / 前期 {fmt_money(data['op_prev'])}
純利益: 今期 {fmt_money(data['net_profit'])} / 前期 {fmt_money(data['net_profit_prev'])}
EPS: 今期 {data['eps_current']:.2f}円 / 前期 {data['eps_prev']:.2f}円
営業CF: {fmt_money(data['operating_cf'])}
投資CF: {fmt_money(data['investing_cf'])}
会社コメント・見通し: {comment}

【自動計算指標】
売上成長率: {fmt_pct(metrics['売上成長率'])}
営業利益成長率: {fmt_pct(metrics['営業利益成長率'])}
営業利益率: {fmt_pct(metrics['営業利益率'])}
純利益率: {fmt_pct(metrics['純利益率'])}
EPS成長率: {fmt_pct(metrics['EPS成長率'])}
FCF: {fmt_money(metrics['FCF'])}
FCFマージン: {fmt_pct(metrics['FCFマージン'])}

【現時点の自己判断】
投資仮説への影響: {thesis_impact}
現在の判断: {current_decision}

以下の形式で出力してください。
1. 決算の一言評価（期待以上・期待通り・やや期待未満・明確に悪い）
2. 数字面の評価（売上・営業利益・利益率・EPS・キャッシュフロー）
3. 質的評価（成長ドライバー、一過性/構造的要因、会社説明の納得度）
4. 投資仮説への影響（強まった・維持・黄信号・崩壊）
5. 次回決算で確認すること
6. 現在の判断（継続・買い増し検討・様子見・一部売却・売却検討）
""".strip()


def render_company_analysis_tab():
    st.subheader("企業分析")
    st.caption("決算書や短信の一次情報を入れると、主要指標を自動計算してGPT用プロンプトを作ります。")

    name = st.text_input("企業名", value=st.session_state.get("企業名", ""), key="analysis_name")
    code = st.text_input("証券コード", value=st.session_state.get("証券コード", ""), key="analysis_code")
    business = st.text_area("主な事業内容", value=st.session_state.get("主な事業内容", ""), key="analysis_business")
    theme = st.text_input("成長テーマ", value=st.session_state.get("成長テーマ", ""), key="analysis_theme")

    st.markdown("**一次情報**")
    col1, col2 = st.columns(2)
    with col1:
        sales_current = number_input("今期売上高（百万円）", "analysis_sales_current")
        op_current = number_input("今期営業利益（百万円）", "analysis_op_current")
        net_profit = number_input("純利益（百万円）", "analysis_net_profit")
        eps_current = number_input("今期EPS（円）", "analysis_eps_current")
        operating_cf = number_input("営業CF（百万円）", "analysis_operating_cf")
        cash = number_input("現金等（百万円）", "analysis_cash")
        equity = number_input("自己資本（百万円）", "analysis_equity")
        stock_price = number_input("株価（円）", "analysis_stock_price")
    with col2:
        sales_prev = number_input("前期売上高（百万円）", "analysis_sales_prev")
        op_prev = number_input("前期営業利益（百万円）", "analysis_op_prev")
        eps_prev = number_input("前期EPS（円）", "analysis_eps_prev")
        investing_cf = number_input("投資CF（百万円）", "analysis_investing_cf")
        interest_bearing_debt = number_input("有利子負債（百万円）", "analysis_debt")
        total_assets = number_input("総資産（百万円）", "analysis_total_assets")
        shares_outstanding = number_input("発行済株式数（株）", "analysis_shares")
        market_cap = number_input("時価総額（百万円・任意）", "analysis_market_cap")

    dividend_total = number_input("年間配当総額（百万円）", "analysis_dividend_total")
    investment_hypothesis = st.text_area(
        "投資仮説",
        placeholder="なぜこの企業に投資するのか。売上成長、利益率改善、シェア拡大など。",
        key="analysis_hypothesis",
    )

    data = {
        "sales_current": sales_current,
        "sales_prev": sales_prev,
        "op_current": op_current,
        "op_prev": op_prev,
        "net_profit": net_profit,
        "eps_current": eps_current,
        "eps_prev": eps_prev,
        "operating_cf": operating_cf,
        "investing_cf": investing_cf,
        "cash": cash,
        "interest_bearing_debt": interest_bearing_debt,
        "equity": equity,
        "total_assets": total_assets,
        "shares_outstanding": shares_outstanding,
        "stock_price": stock_price,
        "market_cap": market_cap,
        "dividend_total": dividend_total,
    }
    metrics = calculate_metrics(data)
    scores = score_company(metrics)

    render_metric_summary(metrics, scores)

    if st.button("企業分析プロンプトを生成", key="analysis_generate"):
        prompt = company_analysis_prompt(name, code, business, theme, data, metrics, scores, investment_hypothesis)
        output_box("GPT用プロンプト", prompt, "analysis_output")
        add_history("企業分析", name, prompt)
        st.session_state["企業名"] = name
        st.session_state["証券コード"] = code
        st.session_state["主な事業内容"] = business
        st.session_state["成長テーマ"] = theme


def render_earnings_tab():
    st.subheader("決算レビュー")
    st.caption("数字の良し悪しだけでなく、投資仮説への影響と現在の判断まで固定します。")

    name = st.text_input("企業名", value=st.session_state.get("企業名", ""), key="earnings_name")
    current_year = datetime.now().year % 100
    col_period1, col_period2, col_period3 = st.columns(3)
    fiscal_year = col_period1.text_input("決算期（年）", value=str(current_year), key="earnings_year")
    fiscal_month = col_period2.text_input("決算期（月）", placeholder="例: 6", key="earnings_month")
    quarter = col_period3.selectbox("区分", ["通期", "第1四半期", "第2四半期", "第3四半期", "第4四半期"], key="earnings_quarter")
    period = f"20{fiscal_year}年{fiscal_month}月期 {quarter}".strip()

    render_pdf_importer()

    col1, col2 = st.columns(2)
    with col1:
        sales_current = number_input("今期売上高（百万円）", "earnings_sales_current")
        op_current = number_input("今期営業利益（百万円）", "earnings_op_current")
        net_profit = number_input("今期純利益（百万円）", "earnings_net_profit")
        eps_current = number_input("今期EPS（円）", "earnings_eps_current")
        operating_cf = number_input("営業CF（百万円）", "earnings_operating_cf")
    with col2:
        sales_prev = number_input("前期売上高（百万円）", "earnings_sales_prev")
        op_prev = number_input("前期営業利益（百万円）", "earnings_op_prev")
        net_profit_prev = number_input("前期純利益（百万円）", "earnings_net_profit_prev")
        eps_prev = number_input("前期EPS（円）", "earnings_eps_prev")
        investing_cf = number_input("投資CF（百万円）", "earnings_investing_cf")

    comment = st.text_area("会社コメント・来期見通し", key="earnings_comment")
    thesis_impact = st.selectbox("投資仮説への影響", ["仮説は強まった", "仮説は維持", "仮説に黄信号", "仮説崩壊"], key="earnings_thesis_impact")
    current_decision = st.selectbox("現在の判断", ["継続", "買い増し検討", "様子見", "一部売却", "売却検討"], key="earnings_decision")

    data = {
        "sales_current": sales_current,
        "sales_prev": sales_prev,
        "op_current": op_current,
        "op_prev": op_prev,
        "net_profit": net_profit,
        "net_profit_prev": net_profit_prev,
        "eps_current": eps_current,
        "eps_prev": eps_prev,
        "operating_cf": operating_cf,
        "investing_cf": investing_cf,
        "cash": 0.0,
        "interest_bearing_debt": 0.0,
        "equity": 0.0,
        "total_assets": 0.0,
        "shares_outstanding": 0.0,
        "stock_price": 0.0,
        "market_cap": 0.0,
        "dividend_total": 0.0,
    }
    metrics = calculate_metrics(data)

    col1, col2, col3 = st.columns(3)
    col1.metric("売上成長率", fmt_pct(metrics["売上成長率"]))
    col2.metric("営業利益成長率", fmt_pct(metrics["営業利益成長率"]))
    col3.metric("FCF", fmt_money(metrics["FCF"]))

    if st.button("決算レビュープロンプトを生成", key="earnings_generate"):
        prompt = earnings_review_prompt(name, period, data, metrics, thesis_impact, current_decision, comment)
        output_box("GPT用プロンプト", prompt, "earnings_output")
        add_history("決算レビュー", name, prompt)
        st.session_state["企業名"] = name


def render_holding_memo_tab():
    st.subheader("保有メモ")
    st.caption("買う前と保有中の判断基準を残します。")

    name = st.text_input("企業名", value=st.session_state.get("企業名", ""), key="memo_name")
    code = st.text_input("証券コード", value=st.session_state.get("証券コード", ""), key="memo_code")
    hypothesis = st.text_area("投資仮説", key="memo_hypothesis")
    expected_scenario = st.text_area("期待シナリオ", key="memo_expected")
    disconfirming = st.text_area("反証条件", key="memo_disconfirming")
    holding_reason = st.text_area("保有理由", key="memo_holding_reason")
    sell_condition = st.text_area("売却条件", key="memo_sell_condition")
    downside_plan = st.text_area("30%下落した場合の対応", key="memo_downside_plan")
    post_earnings_decision = st.selectbox("決算後判断", ["継続", "買い増し検討", "様子見", "一部売却", "売却検討"], key="memo_decision")

    checklist = {
        "事業理解": st.checkbox("何で稼いでいるか説明できる", key="check_business"),
        "成長余地": st.checkbox("3〜5年後も伸びる理由がある", key="check_growth"),
        "競争優位性": st.checkbox("他社に負けにくい理由がある", key="check_moat"),
        "財務": st.checkbox("借金過多ではない", key="check_finance"),
        "利益の質": st.checkbox("営業CFが伴っている", key="check_cashflow"),
        "バリュエーション": st.checkbox("期待を織り込みすぎていない", key="check_valuation"),
        "下落耐性": st.checkbox("30%下落しても保有理由が残る", key="check_downside"),
        "売却条件": st.checkbox("買う前に売却条件を決めている", key="check_sell_condition"),
    }

    checked_count = sum(checklist.values())
    st.progress(checked_count / len(checklist), text=f"買う前チェック: {checked_count}/{len(checklist)}")

    if st.button("保有メモを保存", key="memo_save"):
        memo = {
            "company": name or "未入力",
            "code": code,
            "timestamp": datetime.now(),
            "hypothesis": hypothesis,
            "expected_scenario": expected_scenario,
            "disconfirming": disconfirming,
            "holding_reason": holding_reason,
            "sell_condition": sell_condition,
            "downside_plan": downside_plan,
            "post_earnings_decision": post_earnings_decision,
            "checklist": checklist,
        }
        st.session_state.holding_memos.append(memo)
        st.success("保有メモを保存しました。")

    if st.session_state.holding_memos:
        st.markdown("**保存済みメモ**")
        for memo in reversed(st.session_state.holding_memos):
            with st.expander(f"{memo['company']}（{memo['timestamp'].strftime('%Y-%m-%d %H:%M')}）"):
                st.markdown(f"**投資仮説**\n\n{memo['hypothesis'] or '未入力'}")
                st.markdown(f"**反証条件**\n\n{memo['disconfirming'] or '未入力'}")
                st.markdown(f"**売却条件**\n\n{memo['sell_condition'] or '未入力'}")
                st.markdown(f"**決算後判断**: {memo['post_earnings_decision']}")


def render_history_tab():
    st.subheader("履歴")
    st.caption("この画面を開いている間の生成履歴を確認できます。")

    if not st.session_state.history:
        st.info("まだ履歴はありません。")
        return

    for item in reversed(st.session_state.history):
        with st.expander(f"{item['kind']} / {item['company']} / {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
            st.code(item["content"], language="markdown")

    if st.button("履歴をすべて削除", key="history_clear"):
        st.session_state.history.clear()
        st.rerun()


init_state()

st.image(LOGO_URL, width=72)
st.title("GrowthLens")
st.caption("一次情報から財務指標を計算し、投資仮説・決算評価・売買判断を記録する中長期投資ツール")

tab_analysis, tab_earnings, tab_memo, tab_history = st.tabs(["企業分析", "決算レビュー", "保有メモ", "履歴"])

with tab_analysis:
    render_company_analysis_tab()

with tab_earnings:
    render_earnings_tab()

with tab_memo:
    render_holding_memo_tab()

with tab_history:
    render_history_tab()
