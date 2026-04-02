# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.9.3", layout="wide")
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a; color: #e2e8f0; }
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        font-family: 'Courier New', monospace;
    }
    .stNumberInput input { color: #e2e8f0 !important; background-color: #1e293b !important; }
    .summary-box {
        margin-top: 20px; padding: 15px;
        background-color: #1e293b;
        border-left: 5px solid #38bdf8;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.3")

def to_int(val):
    if not val: return 0
    # 숫자와 쉼표만 남기고 제거
    num_str = re.sub(r'[^\d]', '', str(val))
    if not num_str: return 0
    return int(num_str)

# 날짜와 붙은 금액에서 금액만 추출 (예: 14,399,32626.04.01 -> 14,399,326)
def extract_balance(text):
    if not text: return 0
    # 날짜 형식(YY.MM.DD)이 나타나기 전까지만 숫자로 간주
    match = re.match(r'([\d,]+)(?=\d{2}\.\d{2}\.\d{2})', text)
    if match:
        return忽视_int(match.group(1))
    # 날짜가 안 붙어있는 경우
    return忽视_int(text)

def忽视_int(val):
    num = re.sub(r'[^\d]', '', str(val))
    return int(num) if num else 0

today_str = datetime.now().strftime("%Y-%m-%d")

# ── session_state 초기화 ─────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state: st.session_state[k] = ""

# ── 삭제 플래그 처리 ────────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    flag = f'_clear_{k}'
    if st.session_state.get(flag):
        st.session_state[k] = ""
        st.session_state[flag] = False

# ── 레이아웃 ────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 데이터를 입력하면 정산서가 자동 생성됩니다.")

    # 1. TL 어드민
    raw_input = st.text_area("📋 1. TL 어드민 텍스트", height=150, key="raw_input")
    if st.button("🗑 TL 삭제", key="clear_raw"): st.session_state['_clear_raw_input'] = True

    st.divider()

    # 2. ADA 어드민 (자동 파싱 강화)
    ada_input = st.text_area("📋 2. ADA 어드민 (전체 복사)", height=150, key="ada_input")
    if st.button("🗑 ADA 삭제", key="clear_ada"): st.session_state['_clear_ada_input'] = True
    
    # --- ADA 자동 파싱 로직 ---
    parsed_ada_in = 0
    parsed_ada_out = 0
    if ada_input:
        # 상단 합계 파싱 (입금/출금 금일완료 수치)
        # 텍스트 예: "출금 요청0 대기0 금일완료4 9,236,560원"
        in_match = re.search(r'입금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        out_match = re.search(r'출금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        if in_match: parsed_ada_in = 忽视_int(in_match.group(1))
        if out_match: parsed_ada_out = 忽视_int(out_match.group(1))

    st.caption(f"✨ ADA 파싱 결과: 입금 {parsed_ada_in:,} / 출금 {parsed_ada_out:,}")
    
    ada_col1, ada_col2, ada_col3 = st.columns(3)
    with ada_col1:
        u_ada_in = st.number_input("ADA 입금 수정", value=parsed_ada_in, step=1000)
    with ada_col2:
        u_ada_out = st.number_input("ADA 출금 수정", value=parsed_ada_out, step=1000)
    with ada_col3:
        # 매출 자동 계산 (입금 3.5% + 출금 2% 예시 - 필요시 요율 수정)
        u_ada_rev = math.ceil(u_ada_in * 0.035 + u_ada_out * 0.02)
        st.metric("ADA 매출(자동)", f"{u_ada_rev:,}")

    st.divider()

    # 3. USDT / 4. 은행 / 5. MBD (기존 유지)
    usdt_raw = st.text_area("💱 3. USDT 내역", height=100, key="usdt_raw")
    bank_raw = st.text_area("🏦 4. 은행 메모", height=100, key="bank_raw")
    mbd_raw = st.text_area("📊 5. 머천트 통계 (MBD)", height=100, key="mbd_raw")

# ── 결과 처리 ───────────────────────────────────────────
with col_right:
    if not raw_input and not ada_input:
        st.info("👈 데이터를 입력해주세요.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        tl_full = raw_input.replace('\n', ' ')
        ada_full = ada_input.replace('\n', ' ')

        # [1] TL 업체 밸런스 파싱
        tl_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_tl_balance = 0
        for t in tl_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원'
            m = re.search(pattern, tl_full)
            val = 忽视_int(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_tl_balance += val

        # [2] ADA 업체 밸런스 파싱 (날짜 결합 대응)
        # 예: v99_BTV99liveN14,399,32626.04.01
        ada_targets = ['v99_BT', 'v99_GAME_BT', 'v99_GIFT']
        total_ada_balance = 0
        ada_bal_text = ""
        for t in ada_targets:
            # liveN 또는 liveY 뒤의 숫자 뭉치를 찾고, 날짜 패턴(YY.MM.DD) 앞에서 끊음
            pattern = rf'{re.escape(t)}.+?live[NY]([\d,]+)'
            m = re.search(pattern, ada_full)
            if m:
                raw_val = m.group(1)
                # 만약 숫자가 10자리 이상이면 날짜가 붙은 것임 (예: 14399326260401)
                if len(raw_val.replace(',','')) >= 10:
                    val = 忽视_int(raw_val[:-6]) # 뒤의 날짜 6자리(260401) 제거
                else:
                    val = 忽视_int(raw_val)
            else:
                val = 0
            
            data['merchants'][t] = val
            total_ada_balance += val
            if val > 0 or t == 'v99_BT': # v99_BT는 0이라도 표시
                ada_bal_text += f"- {t} : {val:,}\n"

        # [3] 손익 계산
        summary_match = re.search(r'Summary\s*(.*)', tl_full)
        tl_in, tl_out, tl_rev, tl_agent, tl_gate, tl_virtual, tl_profit = 0, 0, 0, 0, 0, 0, 0
        if summary_match:
            nums = re.findall(r'[\d,.-]+', summary_match.group(1))
            if len(nums) >= 17:
                tl_in, tl_out, tl_rev = 忽视_int(nums[0]), 忽视_int(nums[2]), 忽视_int(nums[7])
                tl_agent, tl_gate, tl_virtual = 忽视_int(nums[10]), 忽视_int(nums[11]), 忽视_int(nums[14])
                tl_profit = 忽视_int(nums[16])

        # ADA 에이전트 수수료 (입금의 0.1% 예시)
        ada_agent_fee = math.ceil(u_ada_in * 0.001) 
        
        # [4] 정산서 작성
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', tl_full)
        now_str = f"{date_match.group(2)}월 {date_match.group(3)}일" if date_match else datetime.now().strftime("%m월 %d일")

        report = f"""***{now_str} 티엘 현황***

[본사]
- 입금 : {tl_in:,}
- 출금 : {tl_out:,}
- 매출 : {tl_rev:,}

[ADA]
- 입금 : {u_ada_in:,}
- 출금 : {u_ada_out:,}
- 매출 : {u_ada_rev:,}

[TL업체]
{chr(10).join([f"- {k} : {v:,}" for k, v in data['merchants'].items() if k in tl_targets and v > 0])}

[ADA 업체]
{ada_bal_text.strip()}

[손익]
- 에이전트 : TL -{tl_agent:,} / ADA -{ada_agent_fee:,}
- 게이트웨이 : TL -{tl_gate:,}
- 가상 수수료 : -{tl_virtual:,}
- 일매출 : TL {tl_rev:,} / ADA {u_ada_rev:,}
- 최종순익 : {tl_profit + u_ada_rev - ada_agent_fee:,}
- 시재금 : {忽视_int(total_bank_sum_for_sijae) - (total_tl_balance + total_ada_balance):,}
"""
        components.html(f"""
            <textarea id="rep" style="width:100%;height:500px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <button onclick="var t=document.getElementById('rep');t.select();document.execCommand('copy');" style="margin-top:8px;padding:8px 16px;background:#38bdf8;color:#000;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">📋 정산서 복사</button>
        """, height=560)