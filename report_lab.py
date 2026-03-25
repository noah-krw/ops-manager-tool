# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.9.1", layout="wide")
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a; color: #e2e8f0; }
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        font-family: 'Courier New', monospace;
    }
    .summary-box {
        margin-top: 20px;
        padding: 15px;
        background-color: #1e293b;
        border-left: 5px solid #38bdf8;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.1")

def to_int(val):
    if not val: return 0
    # 계산을 위해 숫자와 소수점, 마이너스 부호만 남기고 제거
    num_str = re.sub(r'[^\d.-]', '', str(val))
    if not num_str: return 0
    try:
        return int(round(float(num_str)))
    except:
        return 0

SECTION_KEYS = ['앞장', '롤링장', '출금장', '중간장', '뒷장', '금고장', '기타']

# ── 레이아웃 (3단 입력 시스템 유지) ───────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 텍스트 입력창 3개를 순서대로 활용하세요.")
    raw_input = st.text_area("📋 1. 어드민 텍스트", height=250, key="raw_input")
    st.divider()
    bank_raw = st.text_area("🏦 2. 은행 메모", height=180, key="bank_raw", placeholder="[앞장]- 이름 : 금액...")
    st.divider()
    usdt_raw = st.text_area("💱 3. USDT 내역", height=150, key="usdt_raw", placeholder="[USDT 정산]- 업체명 : 금액...")

# ── 데이터 파싱 ──────────────────────────────────────────
bank_data = {k: [] for k in SECTION_KEYS}
total_bank_sum_for_sijae = 0

if bank_raw:
    sec_pattern = '|'.join(SECTION_KEYS)
    # 줄바꿈 유지하며 섹션 분리
    parts = re.split(rf'\[({sec_pattern})\]', bank_raw)
    it = iter(parts[1:])
    for sec in it:
        sec_content = next(it, '')
        # [수정] 콜론(:) 뒤의 모든 텍스트를 긁어오도록 변경 (메모 보존)
        items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([^\n\r]+)', sec_content)
        parsed_items = [(name.strip(), val.strip()) for name, val in items]
        bank_data[sec] = parsed_items
        
        # '기타'를 제외한 섹션만 시재 합산 (to_int가 텍스트 사이에서 숫자만 골라냄)
        if sec != '기타':
            total_bank_sum_for_sijae += sum(to_int(v) for n, v in parsed_items)

# USDT 파싱
usdt_settle_lines = ""
usdt_topup_lines = ""
if usdt_raw:
    u_parts = re.split(r'\[(USDT 정산|USDT 탑업)\]', usdt_raw)
    u_it = iter(u_parts[1:])
    for u_sec in u_it:
        u_content = next(u_it, '')
        u_items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([^\n\r]+)', u_content)
        for name, val in u_items:
            if u_sec == "USDT 정산":
                usdt_settle_lines += f"- {name} : {val}\n"
            else:
                usdt_topup_lines += f"- {name} : {val}\n"

with col_right:
    if not raw_input:
        st.info("👈 왼쪽에 데이터를 입력하면 정산표가 생성됩니다.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        full = raw_input.replace('\n', ' ')
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', full)
        now_str = f"{date_match.group(2)}월 {date_match.group(3)}일" if date_match else datetime.now().strftime("%m월 %d일")

        # 어드민 요약 추출
        summary_match = re.search(r'Summary\s*(.*)', full)
        if summary_match:
            nums = re.findall(r'[\d,.-]+', summary_match.group(1))
            if len(nums) >= 17:
                data['b_in'], data['b_out'], data['b_rev'] = to_int(nums[0]), to_int(nums[2]), to_int(nums[7])
                data['b_agent'], data['b_gate'], data['b_virtual'] = to_int(nums[10]), to_int(nums[11]), to_int(nums[14])
                data['b_other'], data['b_profit'] = to_int(nums[13]), to_int(nums[16])

        # 업체 밸런스
        balance_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama']
        total_merchant_balance = 0
        for t in balance_targets:
            m = re.search(rf'\t{re.escape(t)}\t.*?([\d,.-]+)\s*원', full)
            val = to_int(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_merchant_balance += val

        # 손익 계산
        rev_val = data.get('b_rev', 0)
        exp_val = abs(data.get('b_other', 0)) + abs(data.get('b_agent', 0)) + abs(data.get('b_gate', 0)) + abs(data.get('b_virtual', 0))

        # ── 보고서 생성 ──
        usdt_section = ""
        if usdt_settle_lines: usdt_section += f"[USDT 정산]\n{usdt_settle_lines}\n"
        if usdt_topup_lines: usdt_section += f"[USDT 탑업]\n{usdt_topup_lines}\n"

        def get_bank_txt(k):
            items = bank_data.get(k, [])
            # [수정] 금액 포맷팅을 건드리지 않고 입력값 그대로 출력
            return f"[{k}]\n" + '\n'.join([f"- {n} : {v}" for n, v in items]) if items else ""

        bank_text = '\n\n'.join([p for p in [get_bank_txt(k) for k in SECTION_KEYS] if p])

        report = f"""***{now_str} 티엘 현황***

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

{usdt_section}{bank_text}

[손익]
- 에이전트 : -{abs(data.get('b_agent', 0)):,}
- 게이트웨이 : -{abs(data.get('b_gate', 0)):,}
- 가상 수수료 : -{abs(data.get('b_virtual', 0)):,}
- 일매출 및 일지출 : {rev_val:,} / -{exp_val:,}
- 최종순익 : {data.get('b_profit', 0):,}
- 시재금 : {total_bank_sum_for_sijae - total_merchant_balance:,}
"""
        components.html(f"""
            <textarea id="rep" style="width:100%;height:600px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <button onclick="var t=document.getElementById('rep');t.select();document.execCommand('copy');this.innerText='✅ 복사완료';var me=this;setTimeout(function(){{me.innerText='📋 복사하기';}},1500);" style="margin-top:8px;padding:10px 20px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-weight:600;">📋 복사하기</button>
        """, height=700)

        # ── 하단 리스크 관리 섹션 (v4.9 로직 유지) ──
        SAFE_MIN = 30000000
        custom_won_sijae = total_bank_sum_for_sijae - total_merchant_balance
        risk_managed_buy = max(0, math.floor((total_bank_sum_for_sijae - SAFE_MIN) / 10000000) * 10000000)

        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0; font-size:14px; color:#38bdf8;">원화시재 : {custom_won_sijae:,}원</p>
            <p style="margin:5px 0; font-size:14px; color:#38bdf8;">은행 잔고 합계 : {total_bank_sum_for_sijae:,}원</p>
            <p style="margin:5px 0; font-size:14px; color:#38bdf8;">머천트밸런스 : {total_merchant_balance:,}원</p>
            <p style="margin:0; font-size:14px; color:#38bdf8;">리스크 관리형 USDT 구매 : {risk_managed_buy:,}원</p>
            <p style="margin-top:5px; font-size:11px; color:rgba(255,255,255,0.4);">* 로직: 은행 잔고 최소화 (유지비 {SAFE_MIN/10000:,.0f}만 원 제외 전액 매입)</p>
        </div>
        """, unsafe_allow_html=True)