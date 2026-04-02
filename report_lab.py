# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="NOA SMART REPORT v4.9.3", layout="wide")

# 스타일 정의
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
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: rgba(220,38,38,0.35) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.3")

# 헬퍼 함수: 숫자만 추출 (한자 에러 방지를 위해 영문 이름으로 변경)
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

# ── session_state 초기화 ─────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state:
        st.session_state[k] = ""

# ── 삭제 플래그 처리 ────────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    flag = f'_clear_{k}'
    if st.session_state.get(flag):
        st.session_state[k] = ""
        st.session_state[flag] = False

# ── 레이아웃 ────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 텍스트 입력창을 순서대로 활용하세요.")

    # 1. TL 어드민
    raw_input = st.text_area("📋 1. TL 어드민 텍스트 (본사 손익 현황 + 머천트 관리)",
                              height=160, key="raw_input")
    if st.button("🗑 TL 삭제", key="clear_raw"):
        st.session_state['_clear_raw_input'] = True

    st.divider()

    # 2. ADA 어드민
    ada_input = st.text_area("📋 2. ADA 어드민 텍스트 (머천트 목록 페이지)",
                              height=160, key="ada_input",
                              placeholder="머천트 목록 페이지 전체를 복사해서 붙여넣으세요.")
    if st.button("🗑 ADA 삭제", key="clear_ada"):
        st.session_state['_clear_ada_input'] = True

    # ADA 데이터 자동 파싱
    parsed_ada_in = 0
    parsed_ada_out = 0
    if ada_input:
        in_match = re.search(r'입금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        out_match = re.search(r'출금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_input.replace('\n',' '))
        if in_match: parsed_ada_in = to_int_v2(in_match.group(1))
        if out_match: parsed_ada_out = to_int_v2(out_match.group(1))

    st.caption(f"✨ ADA 감지 결과: 입금 {parsed_ada_in:,} / 출금 {parsed_ada_out:,}")

    ada_col1, ada_col2, ada_col3 = st.columns(3)
    with ada_col1:
        u_ada_in = st.number_input("ADA 입금 수정", value=parsed_ada_in, step=100000)
    with ada_col2:
        u_ada_out = st.number_input("ADA 출금 수정", value=parsed_ada_out, step=100000)
    with ada_col3:
        u_ada_rev = math.ceil(u_ada_in * 0.035 + u_ada_out * 0.02)
        st.metric("ADA 매출 (자동)", f"{u_ada_rev:,}")

    st.divider()

    # 3. USDT 내역
    usdt_raw = st.text_area("💱 3. USDT 내역", height=120, key="usdt_raw",
        placeholder="정산 spfxm, 7000000\n탑업 dr188, 50000000")
    if st.button("🗑 USDT 삭제", key="clear_usdt"):
        st.session_state['_clear_usdt_raw'] = True

    st.divider()

    # 4. 은행 메모
    bank_raw = st.text_area("🏦 4. 은행 메모", height=120, key="bank_raw",
        placeholder="[앞장]- 이름 : 금액...")
    if st.button("🗑 은행 삭제", key="clear_bank"):
        st.session_state['_clear_bank_raw'] = True

    st.divider()

    # 5. 머천트 통계
    mbd_raw = st.text_area("📊 5. 머천트 통계 (Merchant By Date)", height=120, key="mbd_raw",
        placeholder="Merchant By Date Statistics 페이지를 복사해서 붙여넣으세요.")
    if st.button("🗑 MBD 삭제", key="clear_mbd"):
        st.session_state['_clear_mbd_raw'] = True

# ── 은행 파싱 ────────────────────────────────────────────
bank_data = {}
total_bank_sum_for_sijae = 0
if bank_raw:
    current_sec = None
    for line in bank_raw.split('\n'):
        sec_match = re.match(r'^\[([^\]]+)\]', line.strip())
        if sec_match:
            current_sec = sec_match.group(1).strip()
            if current_sec not in bank_data:
                bank_data[current_sec] = []
        elif current_sec and line.strip().startswith('-'):
            item_match = re.match(r'-\s*([^:]+?)\s*:\s*(.+)', line.strip())
            if item_match:
                name = item_match.group(1).strip()
                val_str = item_match.group(2).strip()
                bank_data[current_sec].append((name, val_str))
                if '기타' not in current_sec:
                    total_bank_sum_for_sijae += to_int_v2(val_str)

# ── USDT 파싱 ────────────────────────────────────────────
usdt_settle_lines = ""
usdt_topup_lines = ""
if usdt_raw:
    u_parts = re.split(r'\[(USDT 정산|USDT 탑업)\]', usdt_raw)
    if len(u_parts) > 1:
        u_it = iter(u_parts[1:])
        for u_sec in u_it:
            u_content = next(u_it, '')
            u_items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([^\n\r]+)', u_content)
            for name, val in u_items:
                if u_sec == "USDT 정산":
                    usdt_settle_lines += f"- {name} : {val}\n"
                else:
                    usdt_topup_lines += f"- {name} : {val}\n"
    else:
        for line in usdt_raw.strip().split('\n'):
            line = line.strip()
            if not line: continue
            m = re.match(r'(정산|탑업)\s+(.*)', line)
            if not m: continue
            is_topup = m.group(1) == '탑업'
            rest = m.group(2).strip()
            if ',' not in rest: continue
            merchant, amount_part = rest.split(',', 1)
            merchant = merchant.strip()
            nums = re.findall(r'[\d]+', amount_part)
            if not nums: continue
            amount = int(''.join(nums))
            if is_topup:
                usdt_topup_lines += f"- {merchant} : {amount:,}\n"
            else:
                usdt_settle_lines += f"- {merchant} : {amount:,}\n"

# ── 오른쪽: 결과 ─────────────────────────────────────────
with col_right:
    if not raw_input and not ada_input:
        st.info("👈 왼쪽에 데이터를 입력하면 정산표가 생성됩니다.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        full = raw_input.replace('\n', ' ')
        ada_full = ada_input.replace('\n', ' ')

        # 날짜 추출
        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', full)
        now_str = f"{date_match.group(2)}월 {date_match.group(3)}일" if date_match else datetime.now().strftime("%m월 %d일")

        # TL 본사 수치 파싱
        summary_match = re.search(r'Summary\s*(.*)', full)
        tl_profit = 0
        if summary_match:
            nums = re.findall(r'[\d,.-]+', summary_match.group(1))
            if len(nums) >= 17:
                data['b_in'], data['b_out'], data['b_rev'] = to_int_signed(nums[0]), to_int_signed(nums[2]), to_int_signed(nums[7])
                data['b_agent'], data['b_gate'], data['b_virtual'] = to_int_signed(nums[10]), to_int_signed(nums[11]), to_int_signed(nums[14])
                data['b_other'], data['b_profit'] = to_int_signed(nums[13]), to_int_signed(nums[16])
                tl_profit = data['b_profit']

        # TL 업체 밸런스
        tl_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_tl_balance = 0
        for t in tl_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원'
            m = re.search(pattern, full)
            val = to_int_v2(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_tl_balance += val

        # ADA 업체 밸런스 (날짜 결합 대응)
        ada_targets = ['v99_BT', 'v99_GAME_BT', 'v99_GIFT']
        total_ada_balance = 0
        ada_bal_text = ""
        for t in ada_targets:
            pattern = rf'{re.escape(t)}.+?live[NY]([\d,]+)'
            m = re.search(pattern, ada_full)
            if m:
                raw_val = m.group(1).replace(',', '')
                if len(raw_val) >= 10: val = int(raw_val[:-6])
                else: val = int(raw_val)
            else: val = 0
            
            data['merchants'][t] = val
            total_ada_balance += val
            if val > 0 or t == 'v99_BT':
                ada_bal_text += f"- {t} : {val:,}\n"

        # MBD 파싱
        mbd_targets = ['spfxm', 'dr188', 'drgtssen', 'drbetssen', 'drSpinmama', 'NextbetM', 'v99_BT']
        for line in (mbd_raw.split('\n') if mbd_raw else []):
            cols = line.split('\t')
            if len(cols) >= 9:
                mid = cols[2].strip()
                if mid in mbd_targets:
                    data['merchant_in'][mid] = data['merchant_in'].get(mid, 0) + to_int_signed(cols[5])
                    data['merchant_out'][mid] = data['merchant_out'].get(mid, 0) + to_int_signed(cols[8])

        # 손익 최종 계산
        tl_rev = data.get('b_rev', 0)
        tl_agent = abs(data.get('b_agent', 0))
        tl_gate = abs(data.get('b_gate', 0))
        ada_agent_fee = math.ceil(u_ada_in * 0.001) # ADA 에이전트 0.1%
        
        sijae_val = total_bank_sum_for_sijae - (total_tl_balance + total_ada_balance)

        # 리포트 텍스트 생성
        report = f"""***{now_str} 티엘 현황***

[본사]
- 입금 : {data.get('b_in', 0):,}
- 출금 : {data.get('b_out', 0):,}
- 매출 : {tl_rev:,,}

[ADA]
- 입금 : {u_ada_in:,}
- 출금 : {u_ada_out:,}
- 매출 : {u_ada_rev:,}

[TL업체]
{chr(10).join([f"- {k} : {v:,}" for k, v in data['merchants'].items() if k in tl_targets and v > 0])}

[ADA 업체]
{ada_bal_text.strip()}

{"[USDT 정산]" + chr(10) + usdt_settle_lines if usdt_settle_lines else ""}
{"[USDT 탑업]" + chr(10) + usdt_topup_lines if usdt_topup_lines else ""}
{chr(10).join([f"[{k}]" + chr(10) + chr(10).join([f"- {n} : {v}" for n, v in items]) for k, items in bank_data.items()])}

[손익]
- 에이전트 : TL -{tl_agent:,} / ADA -{ada_agent_fee:,}
- 게이트웨이 : TL -{tl_gate:,}
- 가상 수수료 : -{abs(data.get('b_virtual', 0)):,}
- 일매출 : TL {tl_rev:,} / ADA {u_ada_rev:,}
- 최종순익 : {tl_profit + u_ada_rev - ada_agent_fee:,}
- 시재금 : {sijae_val:,} (기타 제외)
"""
        # 결과물 출력 및 복사 버튼
        line_count = report.count("\n") + 1
        height = max(550, line_count * 22 + 60)
        components.html(f"""
            <textarea id="rep" style="width:100%;height:{height}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
                <span style="font-family:'Courier New',monospace;font-size:11px;color:rgba(255,255,255,0.3);">✎ 직접 수정 가능</span>
                <button onclick="var t=document.getElementById('rep');t.select();document.execCommand('copy');this.innerText='✅ 복사완료';var me=this;setTimeout(function(){{me.innerText='📋 복사하기';}},1500);"
                style="padding:8px 18px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-weight:600;">📋 복사하기</button>
            </div>
        """, height=height+50)

        # 하단 요약 박스
        SAFE_MIN = 30000000
        risk_managed_buy = max(0, math.floor((total_bank_sum_for_sijae - SAFE_MIN) / 10000000) * 10000000)
        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0;font-size:14px;color:#38bdf8;">원화시재 : {sijae_val:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">은행 잔고 합계 : {total_bank_sum_for_sijae:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">TL 밸런스 : {total_tl_balance:,}원 | ADA 밸런스 : {total_ada_balance:,}원</p>
            <p style="margin:0;font-size:14px;color:#38bdf8;">리스크 관리형 USDT 구매 : {risk_managed_buy:,}원</p>
        </div>
        """, unsafe_allow_html=True)