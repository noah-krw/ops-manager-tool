# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

# [cite: 2] NOA SMART REPORT v4.9.3 설정
st.set_page_config(page_title="NOA SMART REPORT v4.9.3", layout="wide")

# [cite: 13, 15] 화면 스타일 정의
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
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: rgba(220,38,38,0.15) !important;
        border: 1px solid rgba(220,38,38,0.6) !important;
        color: #f87171 !important;
        font-size: 11px !important;
        padding: 3px 10px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.3")

# [해결: image_efe1b2.png] 한자 함수명을 영문으로 변경하여 SyntaxError 방지
def to_int_v2(val):
    if not val: return 0
    num_str = re.sub(r'[^\d]', '', str(val))
    if not num_str: return 0
    return int(num_str)

def to_int_signed(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.-]', '', str(val))
    if not num_str: return 0
    try: return int(round(float(num_str)))
    except: return 0

today_str = datetime.now().strftime("%Y-%m-%d")

# [cite: 127] 세션 상태 초기화
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state:
        st.session_state[k] = ""

# 삭제 플래그 처리
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    flag = f'_clear_{k}'
    if st.session_state.get(flag):
        st.session_state[k] = ""
        st.session_state[flag] = False

# [cite: 13, 16] 좌측 입력 영역
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 가이드에 따라 데이터를 순서대로 입력하세요. [cite: 4, 127]")

    # [cite: 17, 27] 1. TL 어드민 입력
    raw_input = st.text_area("📋 1. TL 어드민 텍스트 (본사 손익 + 머천트 관리)", height=150, key="raw_input")
    if st.button("🗑 TL 삭제", key="clear_raw"): st.session_state['_clear_raw_input'] = True

    st.divider()

    # [cite: 47] 2. ADA 어드민 입력 및 자동 파싱
    ada_input = st.text_area("📋 2. ADA 어드민 텍스트 (머천트 목록 전체)", height=150, key="ada_input")
    if st.button("🗑 ADA 삭제", key="clear_ada"): st.session_state['_clear_ada_input'] = True

    parsed_ada_in = 0
    parsed_ada_out = 0
    if ada_input:
        # 상단 금일완료 합계 파싱
        in_match = re.search(r'입금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        out_match = re.search(r'출금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        if in_match: parsed_ada_in = to_int_v2(in_match.group(1))
        if out_match: parsed_ada_out = to_int_v2(out_match.group(1))

    st.caption(f"✨ ADA 자동 감지: 입금 {parsed_ada_in:,} / 출금 {parsed_ada_out:,}")
    
    a_col1, a_col2, a_col3 = st.columns(3)
    with a_col1: u_ada_in = st.number_input("ADA 입금액", value=parsed_ada_in, step=100000)
    with a_col2: u_ada_out = st.number_input("ADA 출금액", value=parsed_ada_out, step=100000)
    with a_col3: 
        u_ada_rev = math.ceil(u_ada_in * 0.035 + u_ada_out * 0.02)
        st.metric("ADA 매출", f"{u_ada_rev:,}")

    st.divider()

    # [cite: 18, 51] 3. USDT / [cite: 19, 64] 4. 은행 / [cite: 20, 78] 5. MBD
    usdt_raw = st.text_area("💱 3. USDT 내역", height=100, key="usdt_raw", placeholder="정산 업체명, 금액\n탑업 업체명, 금액 [cite: 52]")
    bank_raw = st.text_area("🏦 4. 은행 메모", height=100, key="bank_raw", placeholder="[앞장]- 이름 : 금액 [cite: 69]")
    mbd_raw = st.text_area("📊 5. 머천트 통계 (MBD)", height=100, key="mbd_raw")

# ── 데이터 파싱 및 리포트 생성 ─────────────────────────────
with col_right:
    if not raw_input and not ada_input:
        st.info("👈 데이터를 입력하면 우측에 보고서가 생성됩니다. [cite: 15]")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        tl_full = raw_input.replace('\n', ' ')
        ada_full = ada_input.replace('\n', ' ')

        # 날짜 및 TL 본사 요약 파싱 [cite: 35, 36]
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', tl_full)
        now_str = f"{date_match.group(2)}월 {date_match.group(3)}일" if date_match else datetime.now().strftime("%m월 %d일")

        summary_match = re.search(r'Summary\s*(.*)', tl_full)
        tl_in, tl_out, tl_rev, tl_agent, tl_gate, tl_virtual, tl_profit = 0, 0, 0, 0, 0, 0, 0
        if summary_match:
            nums = re.findall(r'[\d,.-]+', summary_match.group(1))
            if len(nums) >= 17:
                tl_in, tl_out, tl_rev = to_int_signed(nums[0]), to_int_signed(nums[2]), to_int_signed(nums[7])
                tl_agent, tl_gate, tl_virtual = to_int_signed(nums[10]), to_int_signed(nums[11]), to_int_signed(nums[14])
                tl_profit = to_int_signed(nums[16])

        # TL 및 ADA 업체 밸런스 파싱 [cite: 37, 48]
        tl_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_tl_bal = 0
        for t in tl_targets:
            m = re.search(rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원', tl_full)
            val = to_int_v2(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_tl_bal += val

        ada_targets = ['v99_BT', 'v99_GAME_BT', 'v99_GIFT']
        total_ada_bal = 0
        ada_bal_text = ""
        for t in ada_targets:
            m = re.search(rf'{re.escape(t)}.+?live[NY]([\d,]+)', ada_full)
            if m:
                raw_val = m.group(1).replace(',', '')
                val = int(raw_val[:-6]) if len(raw_val) >= 10 else int(raw_val)
            else: val = 0
            data['merchants'][t] = val
            total_ada_bal += val
            if val > 0 or t == 'v99_BT': ada_bal_text += f"- {t} : {val:,}\n"

        # 은행 섹션 파싱 [cite: 66, 119]
        bank_info = {}
        total_bank_sum = 0
        if bank_raw:
            curr = None
            for line in bank_raw.split('\n'):
                m_sec = re.match(r'^\[([^\]]+)\]', line.strip())
                if m_sec:
                    curr = m_sec.group(1).strip()
                    bank_info[curr] = []
                elif curr and line.strip().startswith('-'):
                    m_item = re.match(r'-\s*([^:]+?)\s*:\s*(.+)', line.strip())
                    if m_item:
                        bank_info[curr].append(f"- {m_item.group(1).strip()} : {m_item.group(2).strip()}")
                        if '기타' not in curr: total_bank_sum += to_int_v2(m_item.group(2))

        # [해결: image_efe8b3.png] 모든 :,, 를 :, 로 수정하여 ValueError 해결
        report = f"""***{now_str} 티엘 현황*** [cite: 97]

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

{chr(10).join([f"[{k}]" + chr(10) + chr(10).join(items) for k, items in bank_info.items()])}

[손익]
- 에이전트 : TL -{tl_agent:,} / ADA -{math.ceil(u_ada_in*0.001):,}
- 게이트웨이 : TL -{tl_gate:,}
- 가상 수수료 : -{tl_virtual:,}
- 일매출 : TL {tl_rev:,} / ADA {u_ada_rev:,}
- 최종순익 : {tl_profit + u_ada_rev - math.ceil(u_ada_in*0.001):,}
- 시재금 : {total_bank_sum - (total_tl_bal + total_ada_bal):,} [cite: 118]
"""
        # [cite: 122, 123] 보고서 출력 및 복사 기능
        line_count = report.count("\n") + 1
        h = max(550, line_count * 22 + 60)
        components.html(f"""
            <textarea id="rep" style="width:100%;height:{h}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <button onclick="var t=document.getElementById('rep');t.select();document.execCommand('copy');this.innerText='✅ 복사완료';"
            style="margin-top:8px;padding:8px 16px;background:#38bdf8;color:#000;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">📋 보고서 복사</button>
        """, height=h+60)

        # [cite: 99, 103] 하단 요약 정보
        sijae = total_bank_sum - (total_tl_bal + total_ada_bal)
        risk_buy = max(0, math.floor((total_bank_sum - 30000000) / 10000000) * 10000000)
        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0;font-size:14px;color:#38bdf8;">원화시재 : {sijae:,}원 [cite: 100]</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">은행 잔고 합계 : {total_bank_sum:,}원 [cite: 101]</p>
            <p style="margin:0;font-size:14px;color:#38bdf8;">USDT 리스크 관리형 구매 : {risk_buy:,}원 [cite: 103, 121]</p>
        </div>
        """, unsafe_allow_html=True)