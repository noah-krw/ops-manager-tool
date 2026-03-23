# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.3", layout="wide")
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

st.title("🚀 노아 스마트 정산기 v4.3")

def to_int(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.]', '', str(val))
    if not num_str: return 0
    try:
        return int(round(float(num_str.replace(',', ''))))
    except:
        return 0

SECTION_KEYS = ['앞장', '롤링장', '출금장', '중간장', '뒷장', '금고장', '기타']

# ── 레이아웃 ───────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 본사 손익 + 업체 관리 페이지 텍스트를 모두 붙여넣으세요.")
    raw_input = st.text_area("📋 어드민 텍스트", height=280, key="raw_input")

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
    bank_raw = st.text_area("메모장 텍스트", height=180, key="bank_raw", placeholder="[앞장]- 이름 : 금액...")

# ── 데이터 파싱 ──────────────────────────────────────────
bank_data = {k: [] for k in SECTION_KEYS}
total_bank_sum = 0
if bank_raw:
    sec_pattern = '|'.join(SECTION_KEYS)
    parts = re.split(rf'\[({sec_pattern})\]', bank_raw.replace('\n', ''))
    it = iter(parts[1:])
    for sec in it:
        sec_content = next(it, '')
        items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([\d,]+)', sec_content)
        parsed_items = [(name.strip(), int(val.replace(',',''))) for name, val in items]
        bank_data[sec] = parsed_items
        total_bank_sum += sum(v for n, v in parsed_items)

with col_right:
    if not raw_input:
        st.info("👈 왼쪽에 텍스트를 붙여넣으세요.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        full = raw_input.replace('\n', ' ')
        
        # 1. 본사 수치 추출
        summary_match = re.search(r'Summary\s*(.*)', full)
        if summary_match:
            nums = re.findall(r'[\d,.]+', summary_match.group(1))
            if len(nums) >= 17:
                data['b_in']      = to_int(nums[0])
                data['b_out']     = to_int(nums[2])
                data['b_rev']     = to_int(nums[7])  # 수수료합계
                data['b_agent']   = to_int(nums[10]) # 에이젼시수수료
                data['b_gate']    = to_int(nums[11]) # 게이트웨이수수료
                data['b_other']   = to_int(nums[13]) # 기타지출
                data['b_virtual'] = to_int(nums[14]) # 가상수수료
                data['b_profit']  = to_int(nums[16]) # 본사순이익

        # 2. 업체 보유밸런스 & 합산
        total_merchant_balance = 0
        for t in balance_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원\s*\d{{4}}-\d{{2}}-\d{{2}}'
            m = re.search(pattern, full)
            val = to_int(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_merchant_balance += val

        # 3. 업체별 입/출
        lines_list = raw_input.split('\n')
        for line in lines_list:
            cols = line.split('\t')
            if len(cols) >= 9:
                mid = cols[2].strip()
                if mid in ['spfxm', 'dr188', 'drgtssen', 'NextbetM']:
                    data['merchant_in'][mid]  = data['merchant_in'].get(mid, 0) + to_int(cols[5])
                    data['merchant_out'][mid] = data['merchant_out'].get(mid, 0) + to_int(cols[8])

        # 4. 손익 및 시재금 계산
        rev_val = data.get('b_rev', 0)
        exp_val = abs(data.get('b_agent', 0)) + abs(data.get('b_gate', 0)) + abs(data.get('b_virtual', 0))
        
        # [수정된 시재금 공식]: 은행 메모 총합 - 업체 밸런스 총합
        sijae_val = total_bank_sum - total_merchant_balance

        # 5. 정산표 생성
        def bank_section_text(sec_name):
            items = bank_data.get(sec_name, [])
            if not items: return ""
            lines_txt = '\n'.join([f"- {n} : {v:,}" for n, v in items])
            return f"[{sec_name}]\n{lines_txt}"

        bank_parts = [bank_section_text(k) for k in SECTION_KEYS]
        bank_sections_text = '\n\n'.join([p for p in bank_parts if p])

        usdt_lines = ""
        if usdt_settle_amount > 0:
            usdt_lines += f"[USDT 정산]\n- {usdt_settle_merchant} : {int(usdt_settle_amount):,}\n\n"
        if usdt_topup_amount > 0:
            usdt_lines += f"[USDT 탑업]\n- {usdt_topup_merchant} : {int(usdt_topup_amount):,}\n\n"

        io_lines = [f"- {t} : {data['merchant_in'].get(t,0):,} / {data['merchant_out'].get(t,0):,}" 
                    for t in ['spfxm', 'dr188', 'drgtssen', 'NextbetM'] if data['merchant_in'].get(t,0) or data['merchant_out'].get(t,0)]
        merchant_io_text = '\n'.join(io_lines) if io_lines else "- (데이터 없음)"

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
- 에이전트 : -{abs(data.get('b_agent', 0)):,}
- 게이트웨이 : -{abs(data.get('b_gate', 0)):,}
- 가상 수수료 : -{abs(data.get('b_virtual', 0)):,}
- 일매출 및 일지출 : {rev_val:,} / -{exp_val:,}
- 기타지출 : -{abs(data.get('b_other', 0)):,}
- 최종순익 : {data.get('b_profit', 0):,}
- 시재금 : {sijae_val:,}
"""

        line_count = report.count("\n") + 1
        height = max(550, line_count * 22 + 60)
        components.html(f"""
            <div style="font-family:sans-serif;">
                <textarea id="report_area" readonly style="width:100%;height:{height}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;line-height:1.7;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
                <button onclick="var t=document.getElementById('report_area');t.select();document.execCommand('copy');this.innerText='✅ 복사완료';var me=this;setTimeout(function(){{me.innerText='📋 복사하기';}},1500);" style="margin-top:10px;padding:10px 20px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;">📋 복사하기</button>
            </div>
        """, height=height+100)