# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

# NOA SMART REPORT v4.9.15
st.set_page_config(page_title="NOA SMART REPORT v4.9.15", layout="wide")

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

st.title("🚀 노아 스마트 정산기 v4.9.15")

def to_int_clean(val):
    if not val: return 0
    num_str = re.sub(r'[^\d]', '', str(val))
    return int(num_str) if num_str else 0

def to_int_signed(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.-]', '', str(val))
    if not num_str: return 0
    try: return int(round(float(num_str)))
    except: return 0

# 세션 상태 초기화
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state: st.session_state[k] = ""

# 삭제 플래그 처리
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    flag = f'_clear_{k}'
    if st.session_state.get(flag):
        st.session_state[k] = ""
        st.session_state[flag] = False

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 손익 섹션에 '일지출' 항목(TL/ADA 합산)이 추가되었습니다.")

    raw_input = st.text_area("📋 1. TL 어드민 텍스트", height=150, key="raw_input")
    if st.button("🗑 TL 삭제", key="clear_raw"): st.session_state['_clear_raw_input'] = True

    st.divider()

    ada_input = st.text_area("📋 2. ADA 어드민 텍스트", height=150, key="ada_input")
    if st.button("🗑 ADA 삭제", key="clear_ada"): st.session_state['_clear_ada_input'] = True

    # ADA 요약 파싱
    p_ada_in, p_ada_out = 0, 0
    if ada_input:
        cleaned_ada = ada_input.replace('\n',' ')
        in_m = re.search(r'입금\s*요청.+?금일완료\d+\s*([\d,]+)원', cleaned_ada)
        out_m = re.search(r'출금\s*요청.+?금일완료\d+\s*([\d,]+)원', cleaned_ada)
        if in_m: p_ada_in = to_int_clean(in_m.group(1))
        if out_m: p_ada_out = to_int_clean(out_m.group(1))

    st.caption(f"✨ ADA 감지: 입금 {p_ada_in:,} / 출금 {p_ada_out:,}")
    
    a_col1, a_col2, a_col3 = st.columns(3)
    with a_col1: u_ada_in = st.number_input("ADA 입금액", value=p_ada_in, step=100000)
    with a_col2: u_ada_out = st.number_input("ADA 출금액", value=p_ada_out, step=100000)
    with a_col3: 
        u_ada_rev = math.ceil(u_ada_in * 0.035 + u_ada_out * 0.02)
        st.metric("ADA 매출 (자동)", f"{u_ada_rev:,}")

    st.divider()
    usdt_raw = st.text_area("💱 3. USDT 내역", height=100, key="usdt_raw")
    bank_raw = st.text_area("🏦 4. 은행 메모", height=100, key="bank_raw")
    mbd_raw = st.text_area("📊 5. 머천트 통계 (MBD)", height=100, key="mbd_raw")

# ── 결과 처리 ───────────────────────────────────────────
with col_right:
    if not raw_input and not ada_input:
        st.info("👈 데이터를 입력하면 보고서가 생성됩니다.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        tl_full = raw_input.replace('\n', ' ')
        ada_full = ada_input.replace('\n', ' ')

        date_m = re.search(r'(\d{4})-(\d{2})-(\d{2})', tl_full)
        now_str = f"{date_m.group(2)}월 {date_m.group(3)}일" if date_m else datetime.now().strftime("%m월 %d일")

        # TL 요약 수치 파싱
        summary_m = re.search(r'Summary\s*(.*)', tl_full)
        tl_profit = 0
        tl_agent, tl_gate, tl_virtual, tl_rev = 0, 0, 0, 0
        if summary_m:
            nums = re.findall(r'[\d,.-]+', summary_m.group(1))
            if len(nums) >= 17:
                data['b_in'], data['b_out'], tl_rev = to_int_signed(nums[0]), to_int_signed(nums[2]), to_int_signed(nums[7])
                tl_agent, tl_gate, tl_virtual = to_int_signed(nums[10]), to_int_signed(nums[11]), to_int_signed(nums[14])
                tl_profit = to_int_signed(nums[16])

        # TL 업체 파싱
        tl_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_tl_bal = 0
        for t in tl_targets:
            m = re.search(rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원', tl_full)
            val = to_int_clean(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_tl_bal += val

        # ADA 업체 파싱 (v4.9.13 방식 유지)
        ada_targets = ['v99_BT', 'v99_GAME_BT', 'v99_GIFT']
        total_ada_bal = 0
        ada_bal_text = ""
        for t in ada_targets:
            val = 0
            if t in ada_full:
                target_tail = ada_full.split(t)[-1]
                m = re.search(r'[NY]([^.]+)\.', target_tail)
                if m:
                    raw_blob = re.sub(r'[^\d]', '', m.group(1))
                    if len(raw_blob) > 2: val = int(raw_blob[:-2])
            data['merchants'][t] = val
            total_ada_bal += val
            if val > 0 or t == 'v99_BT':
                ada_bal_text += f"- {t} : {val:,}\n"

        # [계산] 지출 및 손익 로직
        ada_agent_fee = math.ceil((u_ada_in + u_ada_out) * 0.001)
        
        # 일지출 합계 (절대값 처리)
        tl_exp_total = abs(tl_agent) + abs(tl_gate) + abs(tl_virtual)
        ada_exp_total = ada_agent_fee

        # 은행 메모 파싱
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
                        if '기타' not in curr: total_bank_sum += to_int_clean(m_item.group(2))

        # 최종 리포트 텍스트
        report = f"""***{now_str} 티엘 현황***

[본사]
- 입금 : {data.get('b_in', 0):,}
- 출금 : {data.get('b_out', 0):,}
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
- 에이전트 : TL -{abs(tl_agent):,} / ADA -{ada_agent_fee:,}
- 게이트웨이 : TL -{abs(tl_gate):,}
- 가상 수수료 : -{abs(tl_virtual):,}
- 일매출 : TL {tl_rev:,} / ADA {u_ada_rev:,}
- 일지출 : TL -{tl_exp_total:,} / ADA -{ada_exp_total:,}
- 최종순익 : {tl_profit + u_ada_rev - ada_agent_fee:,}
- 시재금 : {total_bank_sum - (total_tl_bal + total_ada_bal):,}
"""
        h = max(500, report.count("\n") * 22 + 65)
        components.html(f"""
            <textarea id="rep" style="width:100%;height:{h}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
                <span style="font-family:'Courier New',monospace;font-size:11px;color:rgba(255,255,255,0.3);">✎ 직접 수정 가능</span>
                <button onclick="var t=document.getElementById('rep');t.select();document.execCommand('copy');this.innerText='✅ 복사완료';"
                style="padding:8px 18px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-weight:600;">📋 복사하기</button>
            </div>
        """, height=h+75)

        sijae = total_bank_sum - (total_tl_bal + total_ada_bal)
        risk_buy = max(0, math.floor((total_bank_sum - 30000000) / 10000000) * 10000000)
        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0;font-size:14px;color:#38bdf8;">원화시재 : {sijae:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">은행 잔고 합계 : {total_bank_sum:,}원</p>
            <p style="margin:0;font-size:14px;color:#38bdf8;">USDT 리스크 관리형 구매 : {risk_buy:,}원</p>
        </div>
        """, unsafe_allow_html=True)