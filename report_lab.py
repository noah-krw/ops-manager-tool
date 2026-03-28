# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.9.2", layout="wide")
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
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: rgba(220, 38, 38, 0.15) !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        color: #f87171 !important;
        font-size: 11px !important;
        padding: 3px 10px !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: rgba(220, 38, 38, 0.35) !important;
        border-color: #f87171 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.9.2")

def to_int(val):
    if not val: return 0
    num_str = re.sub(r'[^\d.-]', '', str(val))
    if not num_str: return 0
    try:
        return int(round(float(num_str)))
    except:
        return 0

SECTION_KEYS = ['앞장', '롤링장', '출금장', '중간장', '뒷장', '금고장', '기타']
today_str = datetime.now().strftime("%Y-%m-%d")

# ── session_state 초기화 ─────────────────────────────────
for k in ['raw_input', 'usdt_raw', 'bank_raw', 'mbd_raw']:
    if k not in st.session_state:
        st.session_state[k] = ""

if 'usdt_date' not in st.session_state:
    st.session_state['usdt_date'] = today_str

# 날짜 바뀌면 USDT 자동 초기화
if st.session_state['usdt_date'] != today_str:
    st.session_state['usdt_raw'] = ""
    st.session_state['usdt_date'] = today_str

# ── 삭제 버튼 처리 (위젯 렌더링 전에 먼저 처리) ──────────
if st.session_state.get('_clear_raw'):
    st.session_state['raw_input'] = ""
    st.session_state['_clear_raw'] = False
if st.session_state.get('_clear_usdt'):
    st.session_state['usdt_raw'] = ""
    st.session_state['_clear_usdt'] = False
if st.session_state.get('_clear_bank'):
    st.session_state['bank_raw'] = ""
    st.session_state['_clear_bank'] = False
if st.session_state.get('_clear_mbd'):
    st.session_state['mbd_raw'] = ""
    st.session_state['_clear_mbd'] = False

# ── 레이아웃 ────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.info("💡 텍스트 입력창 4개를 순서대로 활용하세요.")

    # 1. 어드민 텍스트
    raw_input = st.text_area("📋 1. 어드민 텍스트 (본사 손익 현황 + 머천트 관리)", height=180, key="raw_input")
    if st.button("🗑 삭제", key="clear_raw"):
        st.session_state['_clear_raw'] = True
        st.rerun()

    st.divider()

    # 2. USDT 내역
    usdt_raw = st.text_area("💱 2. USDT 내역", height=180, key="usdt_raw",
                              placeholder="[USDT 정산]- 업체명 : 금액\n[USDT 탑업]- 업체명 : 금액")
    if st.button("🗑 삭제", key="clear_usdt"):
        st.session_state['_clear_usdt'] = True
        st.rerun()
    if usdt_raw:
        st.caption("💾 삭제하지 않으면 오늘 하루 동안 유지됩니다. 날짜가 바뀌면 자동으로 초기화됩니다.")
    else:
        st.caption("ℹ️ USDT 내역을 입력하면 오늘 하루 유지됩니다.")

    st.divider()

    # 3. 은행 메모
    bank_raw = st.text_area("🏦 3. 은행 메모", height=180, key="bank_raw",
                             placeholder="[앞장]- 이름 : 금액...")
    if st.button("🗑 삭제", key="clear_bank"):
        st.session_state['_clear_bank'] = True
        st.rerun()

    st.divider()

    # 4. 머천트 통계
    mbd_raw = st.text_area("📊 4. 머천트 통계 (Merchant By Date)", height=180, key="mbd_raw",
                             placeholder="Merchant By Date Statistics 페이지를 복사해서 붙여넣으세요.")
    if st.button("🗑 삭제", key="clear_mbd"):
        st.session_state['_clear_mbd'] = True
        st.rerun()

# ── 은행 파싱 ────────────────────────────────────────────
bank_data = {k: [] for k in SECTION_KEYS}
total_bank_sum_for_sijae = 0

if bank_raw:
    sec_pattern = '|'.join(SECTION_KEYS)
    parts = re.split(rf'\[({sec_pattern})\]', bank_raw)
    it = iter(parts[1:])
    for sec in it:
        sec_content = next(it, '')
        items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([^\n\r]+)', sec_content)
        parsed_items = [(name.strip(), val.strip()) for name, val in items]
        bank_data[sec] = parsed_items
        if sec != '기타':
            total_bank_sum_for_sijae += sum(to_int(v) for n, v in parsed_items)

# ── USDT 파싱 (자유 형식 지원) ──────────────────────────
usdt_settle_lines = ""
usdt_topup_lines = ""
if usdt_raw:
    # 기존 형식 우선 시도 ([USDT 정산] / [USDT 탑업] 섹션)
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
        # 자유 형식: 줄 단위로 파싱
        # 예) "정산 spfxm 7,000,000" / "탑업 dr188 10000000" / "spfxm 정산 7000000"
        for line in usdt_raw.strip().split('\n'):
            line = line.strip()
            if not line: continue
            # 숫자 추출 (가장 큰 숫자 = 금액)
            nums = re.findall(r'[\d,]+', line)
            if not nums: continue
            amount_str = max(nums, key=lambda x: len(x.replace(',', '')))
            amount = int(amount_str.replace(',', ''))
            amount_fmt = f"{amount:,}"
            # 업체명 추출 (키워드/숫자 제거 후 남은 첫 단어)
            clean = re.sub(r'[\d,]+', '', line)
            keywords = {'정산', '탑업', 'usdt', 'USDT', '-', '[', ']'}
            words = [w for w in clean.split() if w not in keywords]
            merchant = words[0] if words else "unknown"
            # 정산/탑업 구분
            if '탑업' in line or 'topup' in line.lower():
                usdt_topup_lines += f"- {merchant} : {amount_fmt}\n"
            else:
                usdt_settle_lines += f"- {merchant} : {amount_fmt}\n"

# ── 오른쪽: 결과 ─────────────────────────────────────────
with col_right:
    if not raw_input:
        st.info("👈 왼쪽에 데이터를 입력하면 정산표가 생성됩니다.")
    else:
        data = {'merchants': {}, 'merchant_in': {}, 'merchant_out': {}}
        full = raw_input.replace('\n', ' ')

        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', full)
        now_str = f"{date_match.group(2)}월 {date_match.group(3)}일" if date_match else datetime.now().strftime("%m월 %d일")

        summary_match = re.search(r'Summary\s*(.*)', full)
        if summary_match:
            nums = re.findall(r'[\d,.-]+', summary_match.group(1))
            if len(nums) >= 17:
                data['b_in'], data['b_out'], data['b_rev'] = to_int(nums[0]), to_int(nums[2]), to_int(nums[7])
                data['b_agent'], data['b_gate'], data['b_virtual'] = to_int(nums[10]), to_int(nums[11]), to_int(nums[14])
                data['b_other'], data['b_profit'] = to_int(nums[13]), to_int(nums[16])

        balance_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama', 'drbetssen']
        total_merchant_balance = 0
        for t in balance_targets:
            pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원\s*\d{{4}}-\d{{2}}-\d{{2}}'
            m = re.search(pattern, full)
            val = to_int(m.group(1)) if m else 0
            data['merchants'][t] = val
            total_merchant_balance += val

        mbd_targets = ['spfxm', 'dr188', 'drgtssen', 'drbetssen', 'drSpinmama', 'NextbetM']
        mbd_lines = mbd_raw.split('\n') if mbd_raw else []
        for line in mbd_lines:
            cols = line.split('\t')
            if len(cols) >= 9:
                mid = cols[2].strip()
                if mid in mbd_targets:
                    data['merchant_in'][mid] = data['merchant_in'].get(mid, 0) + to_int(cols[5])
                    data['merchant_out'][mid] = data['merchant_out'].get(mid, 0) + to_int(cols[8])

        rev_val = data.get('b_rev', 0)
        exp_val = abs(data.get('b_agent', 0)) + abs(data.get('b_gate', 0)) + abs(data.get('b_virtual', 0))

        usdt_section = ""
        if usdt_settle_lines: usdt_section += f"[USDT 정산]\n{usdt_settle_lines}\n"
        if usdt_topup_lines:  usdt_section += f"[USDT 탑업]\n{usdt_topup_lines}\n"

        def get_bank_txt(k):
            items = bank_data.get(k, [])
            return f"[{k}]\n" + '\n'.join([f"- {n} : {v}" for n, v in items]) if items else ""
        bank_text = '\n\n'.join([p for p in [get_bank_txt(k) for k in SECTION_KEYS] if p])

        merchant_lines = ""
        for key in balance_targets:
            val = data['merchants'].get(key, 0)
            if val != 0:
                merchant_lines += f"- {key} : {val:,}\n"

        other_line = f"- 기타지출 : -{abs(data.get('b_other', 0)):,}\n" if data.get('b_other', 0) else ""
        sijae_val = total_bank_sum_for_sijae - total_merchant_balance

        io_lines = [f"- {t} : {data['merchant_in'].get(t,0):,} / {data['merchant_out'].get(t,0):,}"
                    for t in mbd_targets
                    if data['merchant_in'].get(t,0) or data['merchant_out'].get(t,0)]
        merchant_io_text = '\n'.join(io_lines) if io_lines else ""

        report = f"""***{now_str} 티엘 현황***

[본사]
- 입금 : {data.get('b_in', 0):,}
- 출금 : {data.get('b_out', 0):,}
- 매출 : {data.get('b_rev', 0):,}

[업체]
{merchant_lines.strip()}

{usdt_section}{bank_text}

{"[업체별 입금/출금]" + chr(10) + merchant_io_text + chr(10) + chr(10) if merchant_io_text else ""}[손익]
- 에이전트 : -{abs(data.get('b_agent', 0)):,}
- 게이트웨이 : -{abs(data.get('b_gate', 0)):,}
- 가상 수수료 : -{abs(data.get('b_virtual', 0)):,}
- 일매출 및 일지출 : {rev_val:,} / -{exp_val:,}
{other_line}- 최종순익 : {data.get('b_profit', 0):,}
- 시재금 : {sijae_val:,} (기타 제외)
"""

        line_count = report.count("\n") + 1
        height = max(550, line_count * 22 + 60)
        components.html(f"""
            <textarea id="rep" style="width:100%;height:{height}px;background:#1e293b;color:#e2e8f0;border:1px solid #38bdf8;border-radius:8px;font-family:'Courier New',monospace;font-size:13px;padding:14px;box-sizing:border-box;outline:none;">{report}</textarea>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
                <span style="font-family:'Courier New',monospace;font-size:11px;color:rgba(255,255,255,0.3);">✎ 직접 수정 가능</span>
                <button onclick="var t=document.getElementById('rep');t.select();t.setSelectionRange(0,99999);document.execCommand('copy');this.innerText='✅ 복사완료';var me=this;setTimeout(function(){{me.innerText='📋 복사하기';}},1500);"
                style="padding:8px 18px;background:#1e3a5f;color:#e2e8f0;border:1px solid #38bdf8;border-radius:6px;cursor:pointer;font-weight:600;">📋 복사하기</button>
            </div>
        """, height=height+50)

        SAFE_MIN = 30000000
        risk_managed_buy = max(0, math.floor((total_bank_sum_for_sijae - SAFE_MIN) / 10000000) * 10000000)
        st.markdown(f"""
        <div class="summary-box">
            <p style="margin:0;font-size:14px;color:#38bdf8;">원화시재 : {sijae_val:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">은행 잔고 합계 : {total_bank_sum_for_sijae:,}원</p>
            <p style="margin:5px 0;font-size:14px;color:#38bdf8;">머천트밸런스 : {total_merchant_balance:,}원</p>
            <p style="margin:0;font-size:14px;color:#38bdf8;">리스크 관리형 USDT 구매 : {risk_managed_buy:,}원</p>
            <p style="margin-top:5px;font-size:11px;color:rgba(255,255,255,0.4);">* 유지비 {SAFE_MIN//10000:,}만원 제외 전액 매입 기준</p>
        </div>
        """, unsafe_allow_html=True)