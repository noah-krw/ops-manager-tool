# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.0", layout="wide")
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a; color: #e2e8f0; }
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.0")

def to_int(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.]', '', str(val))
    if not num_str: return 0
    try:
        return math.ceil(float(num_str.replace(',', '')))
    except:
        return 0

def to_float(val):
    if not val: return 0.0
    num_str = re.sub(r'[^\d.]', '', str(val))
    if not num_str: return 0.0
    try:
        return float(num_str)
    except:
        return 0.0

SECTION_KEYS = ['앞장', '롤링장', '출금장', '중간장', '뒷장', '금고장', '기타']

# ── 2컬럼 레이아웃 ─────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

# ── 왼쪽: 입력 영역 ────────────────────────────────────
with col_left:
    st.info("💡 본사 손익 + Merchant By Date + 업체 관리 페이지를 모두 붙여넣으세요.")
    raw_input = st.text_area("📋 어드민 텍스트", height=280, key="raw_input",
        placeholder="세 페이지 텍스트를 모두 복사해서 붙여넣으세요.")

    st.divider()
    st.subheader("💱 USDT 정산 / 탑업")
    balance_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama']
    c1, c2 = st.columns(2)
    with c1:
        usdt_settle_merchant = st.selectbox("USDT 정산 업체", balance_targets, key="usdt_s_m")
        usdt_settle_amount   = st.number_input("금액 (KRW)", min_value=0, step=1000000, key="usdt_s_a")
    with c2:
        usdt_topup_merchant  = st.selectbox("USDT 탑업 업체", balance_targets, key="usdt_t_m")
        usdt_topup_amount    = st.number_input("금액 (KRW)", min_value=0, step=1000000, key="usdt_t_a")

    st.divider()
    st.subheader("🏦 은행 메모 붙여넣기")
    bank_raw = st.text_area("메모장 텍스트", height=180, key="bank_raw",
        placeholder="[앞장]- 이름 : 금액\n[롤링장]- 이름 : 금액\n...")

# ── 은행 파싱 ───────────────────────────────────────────
bank_data = {k: [] for k in SECTION_KEYS}
if bank_raw:
    sec_pattern = '|'.join(SECTION_KEYS)
    parts = re.split(rf'\[({sec_pattern})\]', bank_raw.replace('\n', ''))
    it = iter(parts[1:])
    for sec in it:
        sec_content = next(it, '')
        items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([\d,]+)', sec_content)
        bank_data[sec] = [(name.strip(), int(val.replace(',',''))) for name, val in items]

# ── 오른쪽: 결과 영역 ──────────────────────────────────
with col_right:
    if not raw_input:
        st.info("👈 왼쪽에 텍스트를 붙여넣으면 정산표가 여기에 나타납니다.")
    else:
        data = {
            'merchants': {},
            'merchant_in': {},
            'merchant_out': {},
        }

        full  = raw_input.replace('\n', ' ')
        lines_list = raw_input.split('\n')

        # 1. 본사 손익 현황
        hq_block = re.search(r'본사순이익(.+?)(?:List|Merchant|$)', full)
        if hq_block:
            block = hq_block.group(1)
            sum_m = re.search(r'Summary(.+?)(?:List|$)', block)
            b = sum_m.group(1) if sum_m else block
            # 0* 패턴으로 앞에 붙은 0 무시하고 의미있는 숫자 추출
            # 청크순서: 입금(0),입금수수료(1),출금(2),출금수수료(3),
            # 수수료합계일매출(4),업체출금Payout(5),수수료합계(6),밸런스+(7),
            # 에이젼시(8),게이트(9),기타지출(10),가상수수료(11),순이익(12)
            chunks = re.findall(r'0*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', b)
            chunks = [c for c in chunks if c]
            if len(chunks) >= 5:
                data['b_in']  = to_int(chunks[0])
                data['b_out'] = to_int(chunks[2])
                data['b_rev'] = to_int(chunks[4])
            if len(chunks) >= 9:
                data['b_agent']   = round(to_float(chunks[8]))
            if len(chunks) >= 10:
                data['b_gate']    = to_int(chunks[9])
            if len(chunks) >= 11:
                data['b_other']   = to_int(chunks[10])
            if len(chunks) >= 12:
                data['b_virtual'] = to_int(chunks[11])
            if len(chunks) >= 13:
                data['b_profit']  = round(to_float(chunks[12]))

        # 2. 업체 보유밸런스
        for t in balance_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원\s*\d{{4}}-\d{{2}}-\d{{2}}'
            m = re.search(pattern, full)
            data['merchants'][t] = to_int(m.group(1)) if m else 0

        # 3. Merchant By Date
        date_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'NextbetM']
        for line in lines_list:
            cols = line.split('\t')
            if len(cols) >= 9:
                mid = cols[2].strip()
                if mid in date_targets:
                    try:
                        data['merchant_in'][mid]  = to_int(cols[5])
                        data['merchant_out'][mid] = to_int(cols[8])
                    except: pass

        # 4. 손익
        daily_rev    = data.get('b_rev', 0)
        daily_exp    = round(abs(data.get('b_agent', 0)) + abs(data.get('b_gate', 0))
                       + abs(data.get('b_other', 0)) + abs(data.get('b_virtual', 0)))
        final_profit = data.get('b_profit', 0)

        # 5. 업체별 입금/출금
        io_lines = []
        for t in ['spfxm', 'dr188', 'drgtssen', 'NextbetM']:
            in_v  = data['merchant_in'].get(t, 0)
            out_v = data['merchant_out'].get(t, 0)
            if in_v > 0 or out_v > 0:
                io_lines.append(f"- {t} : {in_v:,} / {out_v:,}")
        merchant_io_text = '\n'.join(io_lines) if io_lines else "- (데이터 없음)"

        # 6. 은행 섹션
        def bank_section_text(sec_name):
            items = bank_data.get(sec_name, [])
            if not items:
                return ""
            lines_txt = '\n'.join([f"- {n} : {v:,}" for n, v in items])
            return f"[{sec_name}]\n{lines_txt}"

        bank_parts = [bank_section_text(k) for k in SECTION_KEYS]
        bank_sections_text = '\n\n'.join([p for p in bank_parts if p])

        # 7. USDT 섹션 (0이면 숨김)
        usdt_lines = ""
        if int(usdt_settle_amount) > 0:
            usdt_lines += f"[USDT 정산]\n- {usdt_settle_merchant} : {int(usdt_settle_amount):,}\n\n"
        if int(usdt_topup_amount) > 0:
            usdt_lines += f"[USDT 탑업]\n- {usdt_topup_merchant} : {int(usdt_topup_amount):,}\n\n"

        # 8. 정산표
        now = datetime.now().strftime("%m월 %d일")
        report = f"""💰정산표
***{now} 티엘 현황***

[본사]
- 입금 : {data.get('b_in', 0):,}
- 출금 : {data.get('b_out', 0):,}
- 매출 : {data.get('b_rev', 0):,}

[업체]
- spfxm : {data['merchants'].get('spfxm', 0):,}
- Dpinnacle : {data['merchants'].get('Dpinnacle', 0):,}
- dr188 : {data['merchants'].get('dr188', 0):,}
- drgtssen : {data['merchants'].get('drgtssen', 0):,}
- drSpinmama : {data['merchants'].get('drSpinmama', 0):,}

{usdt_lines}{bank_sections_text}

[업체별 입금/출금]
{merchant_io_text}

[손익]
- 에이전트 : -{round(abs(data.get('b_agent', 0))):,}
- 게이트 : -{abs(data.get('b_gate', 0)):,}
- 가상수수료 : -{abs(data.get('b_virtual', 0)):,}
- 기타지출 : -{abs(data.get('b_other', 0)):,}
- 일매출 및 일지출 : {daily_rev:,} / -{daily_exp:,}
- 최종순익 : {final_profit:,}
"""

        # 9. 출력
        import streamlit.components.v1 as components
        line_count = report.count("\n") + 1
        height = max(500, line_count * 22 + 60)
        components.html(f"""
        <div>
            <textarea id="report_area" style="
                width:100%;height:{height}px;
                background:#1e293b;color:#e2e8f0;
                border:1px solid #38bdf8;border-radius:8px;
                font-family:'Courier New',monospace;font-size:13px;
                line-height:1.7;padding:14px;box-sizing:border-box;
                resize:vertical;
            ">{report}</textarea>
            <button onclick="
                var t=document.getElementById('report_area');
                t.select();t.setSelectionRange(0,99999);
                document.execCommand('copy');
                this.innerText='✅ 복사완료';
                var me=this;
                setTimeout(function(){{me.innerText='📋 복사하기';}},1500);
            " style="
                margin-top:8px;padding:8px 18px;
                background:#1e3a5f;color:#e2e8f0;
                border:1px solid #38bdf8;border-radius:6px;
                cursor:pointer;font-size:13px;font-weight:600;
            ">📋 복사하기</button>
        </div>
        """, height=height+70)

        with st.expander("🔍 디버그"):
            st.write(f"입금: {data.get('b_in',0):,} | 출금: {data.get('b_out',0):,} | 매출: {data.get('b_rev',0):,}")
            st.write(f"에이젼시: {data.get('b_agent',0)} | 게이트: {data.get('b_gate',0)} | 순이익: {data.get('b_profit',0)}")
            for t in balance_targets:
                st.write(f"{t}: {data['merchants'].get(t,0):,}")