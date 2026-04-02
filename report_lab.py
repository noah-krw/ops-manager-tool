# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

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
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: rgba(220,38,38,0.15) !important;
        border: 1px solid rgba(220,38,38,0.6) !important;
        color: #f87171 !important;
        font-size: 11px !important;
        padding: 3px 10px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.15")

def to_int(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.-]', '', str(val))
    if not num_str: return 0
    try: return int(round(float(num_str)))
    except: return 0

today_str = datetime.now().strftime("%Y-%m-%d")

# ── session_state 초기화 ─────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state: st.session_state[k] = ""
if 'usdt_date' not in st.session_state: st.session_state['usdt_date'] = today_str
if st.session_state['usdt_date'] != today_str:
    st.session_state['usdt_raw'] = ""
    st.session_state['usdt_date'] = today_str

# ── 삭제 플래그 처리 ────────────────────────────────────
for k in ['raw_input', 'ada_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    flag = f'_clear_{k}'
    if st.session_state.get(flag):
        st.session_state[k] = ""
        st.session_state[flag] = False

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 텍스트 입력창을 순서대로 활용하세요.")

    # 1. TL 어드민
    raw_input = st.text_area("📋 1. TL 어드민 텍스트 (본사 손익 현황 + 머천트 관리)",
                              height=150, key="raw_input")
    if st.button("🗑 삭제", key="clear_raw"):
        st.session_state['_clear_raw_input'] = True

    st.divider()

    # 2. ADA 어드민
    ada_input = st.text_area("📋 2. ADA 어드민 텍스트 (머천트 목록 페이지)",
                              height=150, key="ada_input",
                              placeholder="머천트 목록 페이지 전체를 복사해서 붙여넣으세요.")
    if st.button("🗑 삭제", key="clear_ada"):
        st.session_state['_clear_ada_input'] = True

    # ADA 입출금 자동 감지
    p_ada_in, p_ada_out = 0, 0
    if ada_input:
        ada_cleaned = ada_input.replace('\n', ' ')
        in_m  = re.search(r'입금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_cleaned)
        out_m = re.search(r'출금\s*요청.+?금일완료\d+\s*([\d,]+)원', ada_cleaned)
        if in_m:  p_ada_in  = to_int(in_m.group(1))
        if out_m: p_ada_out = to_int(out_m.group(1))

    st.caption(f"✨ ADA 감지: 입금 {p_ada_in:,} / 출금 {p_ada_out:,}")
    a_col1, a_col2, a_col3 = st.columns(3)
    with a_col1: u_ada_in  = st.number_input("ADA 입금", value=p_ada_in,  step=100000)
    with a_col2: u_ada_out = st.number_input("ADA 출금", value=p_ada_out, step=100000)
    with a_col3:
        u_ada_rev = math.ceil(u_ada_in * 0.035 + u_ada_out * 0.02)
        st.metric("ADA 매출 (자동)", f"{u_ada_rev:,}")

    st.divider()

    # 3. USDT 내역
    usdt_raw = st.text_area("💱 3. USDT 내역", height=130, key="usdt_raw",
        placeholder="정산 spfxm, 7000000\n탑업 dr188, 50000000")
    if st.button("🗑 삭제", key="clear_usdt"):
        st.session_state['_clear_usdt_raw'] = True
    if usdt_raw:
        st.caption("💾 삭제하지 않으면 오늘 하루 유지됩니다.")
    else:
        st.caption("ℹ️ 예) 정산 spfxm, 7000000 / 탑업 dr188, 50000000")

    st.divider()

    # 4. 은행 메모
    bank_raw = st.text_area("🏦 4. 은행 메모", height=130, key="bank_raw",
        placeholder="[앞장]- 이름 : 금액...")
    if st.button("🗑 삭제", key="clear_bank"):
        st.session_state['_clear_bank_raw'] = True

    st.divider()

    # 5. 머천트 통계
    mbd_raw = st.text_area("📊 5. 머천트 통계 (Merchant By Date)", height=130, key="mbd_raw",
        placeholder="Merchant By Date Statistics 페이지를 복사해서 붙여넣으세요.")
    if st.button("🗑 삭제", key="clear_mbd"):
        st.session_state['_clear_mbd_raw'] = True

# ── 은행 파싱 ────────────────────────────────────────────
bank_data = {}
total_bank_sum = 0
if bank_raw:
    current_sec = None
    for line in bank_raw.split('\n'):
        sec_m = re.match(r'^\[([^\]]+)\]', line.strip())
        if sec_m:
            current_sec = sec_m.group(1).strip()
            if current_sec not in bank_data: bank_data[current_sec] = []
        elif current_sec and line.strip().startswith('-'):
            item_m = re.match(r'-\s*([^:]+?)\s*:\s*(.+)', line.strip())
            if item_m:
                name = item_m.group(1).strip()
                val  = item_m.group(2).strip()
                bank_data[current_sec].append((name, val))
                if '기타' not in current_sec:
                    total_bank_sum += to_int(val)

# ── USDT 파싱 ────────────────────────────────────────────
usdt_settle_lines = ""
usdt_topup_lines  = ""
if usdt_raw:
    u_parts = re.split(r'\[(USDT 정산|USDT 탑업)\]', usdt_raw)
    if len(u_parts) > 1:
        u_it = iter(u_parts[1:])
        for u_sec in u_it:
            u_content = next(u_it, '')
            for name, val in re.findall(r'-\s*([^:\n]+?)\s*:\s*([^\n\r]+)', u_content):
                if u_sec == "USDT 정산": usdt_settle_lines += f"- {name} : {val}\n"
                else: usdt_topup_lines += f"- {name} : {val}\n"
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
            nums = re.findall(r'[\d]+', amount_part)
            if not nums: continue
            amount = int(''.join(nums))
            if is_topup: usdt_topup_lines += f"- {merchant.strip()} : {amount:,}\n"
            else: usdt_settle_lines += f"- {merchant.strip()} : {amount:,}\n"

# ── 결과 ─────────────────────────────────────────────────
with col_right:
    if not raw_input and not ada_input:
        st.info("👈 데이터를 입력하면 정산표가 생성됩니다.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        tl_full  = raw_input.replace('\n', ' ')
        ada_full = ada_input.replace('\n', ' ')

        # 날짜
        date_m = re.search(r'(\d{4})-(\d{2})-(\d{2})', tl_full)
        now_str = f"{date_m.group(2)}월 {date_m.group(3)}일" if date_m else datetime.now().strftime("%m월 %d일")

        # TL 본사 수치
        tl_rev, tl_agent, tl_gate, tl_virtual, tl_profit = 0, 0, 0, 0, 0
        summary_m = re.search(r'Summary\s*(.*)', tl_full)
        if summary_m:
            nums = re.findall(r'[\d,.-]+', summary_m.group(1))
            if len(nums) >= 17:
                data['b_in']  = to_int(nums[0])
                data['b_out'] = to_int(nums[2])
                tl_rev        = to_int(nums[7])
                tl_agent      = to_int(nums[10])
                tl_gate       = to_int(nums[11])
                tl_virtual    = to_int(nums[14])
                data['b_other'] = to_int(nums[13])
                tl_profit     = to_int(nums[16])

        # TL 업체 밸런스 ← 날짜 패턴 포함으로 정확히 파싱
        tl_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_tl_bal = 0
        for t in tl_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원\s*\d{{4}}-\d{{2}}-\d{{2}}'
            m = re.search(pattern, tl_full)
            val = to_int(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_tl_bal += val

        # ADA 업체 밸런스 (v99_BT만, 정확한 패턴)
        total_ada_bal = 0
        ada_bal_lines = ""
        if ada_input:
            pattern = rf'v99_BT(?!_GAME|_GIFT).+?(\d{{1,3}}(?:,\d{{3}})+)'
            m = re.search(pattern, ada_full)
            val = to_int(m.group(1)) if m else 0
            data['merchants']['v99_BT'] = val
            total_ada_bal += val
            ada_bal_lines = f"- v99_BT : {val:,}\n"

        # Merchant By Date 파싱
        mbd_targets = ['spfxm', 'dr188', 'drgtssen', 'drbetssen', 'drSpinmama']
        for line in (mbd_raw.split('\n') if mbd_raw else []):
            cols = line.split('\t')
            if len(cols) >= 9:
                mid = cols[2].strip()
                if mid in mbd_targets:
                    data['merchant_in'][mid]  = data['merchant_in'].get(mid, 0)  + to_int(cols[5])
                    data['merchant_out'][mid] = data['merchant_out'].get(mid, 0) + to_int(cols[8])

        # 손익 계산
        ada_agent = math.ceil(u_ada_in * 0.001)
        tl_exp    = abs(tl_agent) + abs(tl_gate) + abs(tl_virtual)
        ada_exp   = ada_agent
        other_line = f"- 기타지출 : -{abs(data.get('b_other', 0)):,}\n" if data.get('b_other', 0) else ""
        sijae_val = total_bank_sum - (total_tl_bal + total_ada_bal)

        # 섹션 구성
        usdt_section = ""
        if usdt_settle_lines: usdt_section += f"[USDT 정산]\n{usdt_settle_lines}\n"
        if usdt_topup_lines:  usdt_section += f"[USDT 탑업]\n{usdt_topup_lines}\n"

        def get_bank_txt(k):
            items = bank_data.get(k, [])
            return f"[{k}]\n" + '\n'.join([f"- {n} : {v}" for n, v in items]) if items else ""
        bank_text = '\n\n'.join([p for p in [get_bank_txt(k) for k in bank_data.keys()] if p])

        tl_merchant_lines = '\n'.join([f"- {k} : {data['merchants'][k]:,}" for k in tl_targets if data['merchants'].get(k, 0) != 0])

        io_lines = [f"- {t} : {data['merchant_in'].get(t,0):,} / {data['merchant_out'].get(t,0):,}"
                    for t in mbd_targets if data['merchant_in'].get(t,0) or data['merchant_out'].get(t,0)]
        if u_ada_in > 0 or u_ada_out > 0:
            io_lines.append(f"- v99_BT : {int(u_ada_in):,} / {int(u_ada_out):,}")
        merchant_io_text = '\n'.join(io_lines)

        report = f"""***{now_str} 티엘 현황***

[본사]
- 입금 : {data.get('b_in', 0):,}
- 출금 : {data.get('b_out', 0):,}
- 매출 : {tl_rev:,}

[ADA]
- 입금 : {int(u_ada_in):,}
- 출금 : {int(u_ada_out):,}
- 매출 : {u_ada_rev:,}

[TL업체]
{tl_merchant_lines}

[ADA 업체]
{ada_bal_lines.strip()}

{usdt_section}{bank_text}

{"[업체별 입금/출금]" + chr(10) + merchant_io_text + chr(10) + chr(10) if merchant_io_text else ""}[손익]
- 에이전트 : TL -{abs(tl_agent):,} / ADA -{ada_agent:,}
- 게이트웨이 : TL -{abs(tl_gate):,} / ADA -0
- 가상 수수료 : -{abs(tl_virtual):,}
- 일매출 : TL {tl_rev:,} / ADA {u_ada_rev:,}
- 일지출 : TL -{tl_exp:,} / ADA -{ada_exp:,}
{other_line}- 최종순익 : {tl_profit + u_ada_rev - ada_agent:,}
- 시재금 : {sijae_val:,} (기타 제외)
"""
        h = max(600, report.count("\n") * 22 + 65)
        components.html(f"""
            <textarea id="rep" style="width:100%;height:{h}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
                <span style="font-family:'Courier New',monospace;font-size:11px;color:rgba(255,255,255,0.3);">✎ 직접 수정 가능</span>
                <button onclick="var t=document.getElementById('rep');t.select();t.setSelectionRange(0,99999);document.execCommand('copy');this.innerText='✅ 복사완료';var me=this;setTimeout(function(){{me.innerText='📋 복사하기';}},1500);"
                style="padding:8px 18px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-weight:600;">📋 복사하기</button>
            </div>
        """, height=h+50)

        risk_buy = max(0, math.floor((total_bank_sum - 30000000) / 10000000) * 10000000)
        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0;font-size:14px;color:#38bdf8;">원화시재 : {sijae_val:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">은행 잔고 합계 : {total_bank_sum:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">TL 머천트밸런스 : {total_tl_bal:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">ADA 머천트밸런스 : {total_ada_bal:,}원</p>
            <p style="margin:0;font-size:14px;color:#38bdf8;">리스크 관리형 USDT 구매 : {risk_buy:,}원</p>
            <p style="margin-top:5px;font-size:11px;color:rgba(255,255,255,0.4);">* 유지비 3,000만원 제외 전액 매입 기준</p>
        </div>
        """, unsafe_allow_html=True)