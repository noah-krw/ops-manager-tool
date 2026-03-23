# -*- coding: utf-8 -*-
import streamlit as st
import re
import math
from datetime import datetime

st.set_page_config(page_title="NOA SMART REPORT v4.0", layout="centered")
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f172a; color: #e2e8f0; }
    .stTextArea textarea { 
        background-color: #1e293b !important; 
        color: #38bdf8 !important; 
        font-family: 'Courier New', monospace; 
    }
    .report-box {
        background-color: #1e293b;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.8;
        white-space: pre-wrap;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 노아 스마트 정산기 v4.0")
st.info("💡 본사 손익 현황 + Merchant By Date + 업체 관리 페이지를 모두 붙여넣으세요.")

raw_input = st.text_area("어드민 복사 텍스트 전체", height=400, 
                          placeholder="본사 손익 현황, Merchant By Date Statistics, Merchant 관리 페이지 텍스트를 모두 복사해서 붙여넣으세요.")

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

if raw_input:
    data = {
        'merchants': {},
        'merchant_in': {},
        'merchant_out': {},
    }

    full = raw_input.replace('\n', ' ')
    lines = raw_input.split('\n')

    # ── 1. 본사 손익 현황 추출 ─────────────────────────────
    # '본사순이익' 키워드로 본사 블록만 정확히 찾기
    hq_block = re.search(r'본사순이익(.+?)(?:List|Merchant|$)', full)
    if hq_block:
        block = hq_block.group(1)
        # Summary 이후 숫자만 추출
        sum_m = re.search(r'Summary(.+?)(?:List|$)', block)
        b = sum_m.group(1) if sum_m else block

        int_nums = re.findall(r'\d{1,3}(?:,\d{3})+', b)
        dec_nums = re.findall(r'\d{1,3}(?:,\d{3})*\.\d+', b)

        # 컬럼순서: 입금(0),입금수수료(1),출금(2),출금수수료(3),수수료합계(4)
        # 에이젼시(dec[0]), 게이트(int[6]), 순이익(dec[-1])
        if len(int_nums) >= 5:
            data['b_in']     = to_int(int_nums[0])
            data['b_out']    = to_int(int_nums[2])
            data['b_rev']    = to_int(int_nums[4])
        if len(dec_nums) >= 1:
            data['b_agent']  = to_float(dec_nums[0])
        if len(int_nums) >= 7:
            data['b_gate']   = to_int(int_nums[6])
        if dec_nums:
            data['b_profit'] = to_float(dec_nums[-1])

    # ── 2. 업체 보유밸런스 (Merchant 관리 페이지) ──────────
    balance_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama']
    for t in balance_targets:
        pattern = rf'\t{re.escape(t)}\t.*?([\d,]+)\s*원\s*\d{{4}}-\d{{2}}-\d{{2}}'
        m = re.search(pattern, full)
        if m:
            data['merchants'][t] = to_int(m.group(1))
        else:
            data['merchants'][t] = 0

    # ── 3. Merchant By Date: 업체별 입금/출금 ─────────────
    # 탭 구분: 번호|상태|머천트아이디|닉네임|입금수수료%|입금|입금수수료|출금수수료%|출금|출금수수료|...
    date_targets = ['spfxm', 'Dpinnacle', 'dr188', 'drgtssen', 'drSpinmama',
                    'NextbetM', 'NextbetG', 'DafabetM', 'DafabetG']
    for line in lines:
        cols = line.split('\t')
        if len(cols) >= 9:
            mid = cols[2].strip()
            if mid in date_targets:
                try:
                    data['merchant_in'][mid]  = to_int(cols[5])   # 입금
                    data['merchant_out'][mid] = to_int(cols[8])   # 출금
                except:
                    pass

    # ── 4. USDT 정산/탑업 수동 입력 ───────────────────────
    st.divider()
    st.subheader("💱 USDT 정산 / 탑업 입력")
    col1, col2 = st.columns(2)
    with col1:
        usdt_settle_merchant = st.selectbox("USDT 정산 업체", balance_targets, key="usdt_s_m")
        usdt_settle_amount   = st.number_input("USDT 정산 금액 (KRW)", min_value=0, step=1000000, key="usdt_s_a")
    with col2:
        usdt_topup_merchant  = st.selectbox("USDT 탑업 업체", balance_targets, key="usdt_t_m")
        usdt_topup_amount    = st.number_input("USDT 탑업 금액 (KRW)", min_value=0, step=1000000, key="usdt_t_a")

    # ── 5. 은행 메모 붙여넣기 ──────────────────────────────
    st.divider()
    st.subheader("🏦 은행 메모 붙여넣기")
    bank_raw = st.text_area("메모장 텍스트 붙여넣기", height=200, key="bank_raw",
        placeholder="[앞장]- 이름 : 금액\n[롤링장]- 이름 : 금액\n...")

    # 파싱
    SECTION_KEYS = ['앞장', '롤링장', '출금장', '중간장', '뒷장', '금고장', '기타']
    bank_data = {k: [] for k in SECTION_KEYS}

    if bank_raw:
        sec_pattern = '|'.join(SECTION_KEYS)
        parts = re.split(rf'\[({sec_pattern})\]', bank_raw.replace('\n', ''))
        it = iter(parts[1:])
        for sec in it:
            sec_content = next(it, '')
            items = re.findall(r'-\s*([^:\n]+?)\s*:\s*([\d,]+)', sec_content)
            bank_data[sec] = [(name.strip(), int(val.replace(',',''))) for name, val in items]

    # ── 6. 손익 계산 ──────────────────────────────────────
    # 일매출: 수수료합계
    daily_rev    = data.get('b_rev', 0)
    # 일지출: 에이전트 + 게이트 + 가상수수료
    daily_exp    = abs(data.get('b_agent', 0)) + abs(data.get('b_gate', 0)) + abs(data.get('b_virtual', 0))
    final_profit = data.get('b_profit', 0)

    # ── 7. 정산표 생성 ────────────────────────────────────
    now = datetime.now().strftime("%m월 %d일")

    # 업체별 입금/출금 텍스트
    merchant_io_lines = []
    io_targets = ['spfxm', 'dr188', 'drgtssen', 'NextbetM']
    for t in io_targets:
        in_v  = data['merchant_in'].get(t, 0)
        out_v = data['merchant_out'].get(t, 0)
        if in_v > 0 or out_v > 0:
            merchant_io_lines.append(f"- {t} : {in_v:,} / {out_v:,}")
    merchant_io_text = '\n'.join(merchant_io_lines) if merchant_io_lines else "- (데이터 없음)"


    # 은행 섹션 텍스트 생성
    def bank_section_text(sec_name):
        items = bank_data.get(sec_name, [])
        if not items:
            return f"[{sec_name}]\n- (없음)"
        lines_txt = '\n'.join([f"- {n} : {v:,}" for n, v in items])
        return f"[{sec_name}]\n{lines_txt}"

    bank_sections_text = '\n\n'.join([bank_section_text(k) for k in SECTION_KEYS])

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

[USDT 정산]
- {usdt_settle_merchant} : {int(usdt_settle_amount):,}

[USDT 탑업]
- {usdt_topup_merchant} : {int(usdt_topup_amount):,}

{bank_sections_text}

[업체별 입금/출금]
{merchant_io_text}

[손익]
- 에이전트 : -{abs(data.get('b_agent', 0)):,.2f}
- 게이트 : -{abs(data.get('b_gate', 0)):,.2f}
- 가상 수수료 : -{abs(data.get('b_virtual', 0)):,.2f}
- 일매출 및 일지출 : {daily_rev:,} / -{daily_exp:,.2f}
- 최종순익 : {final_profit:,.2f}
"""

    st.divider()
    st.subheader("📋 완성된 정산표")

    import streamlit.components.v1 as components
    line_count = report.count("\n") + 1
    height = max(400, line_count * 22 + 60)
    escaped = report.replace("\\", "\\\\").replace("`", "\\`")
    components.html(f"""
    <div style="position:relative;margin-bottom:10px;">
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

    # 디버그
    with st.expander("🔍 디버그"):
        st.write("**본사**")
        st.write(f"입금: {data.get('b_in',0):,} | 출금: {data.get('b_out',0):,} | 수수료합계: {data.get('b_rev',0):,}")
        st.write(f"에이젼시: {data.get('b_agent',0)} | 게이트: {data.get('b_gate',0)} | 가상: {data.get('b_virtual',0)} | 순이익: {data.get('b_profit',0)}")
        st.write("**업체 밸런스**")
        for t in balance_targets:
            st.write(f"{t}: {data['merchants'].get(t,0):,}")
        st.write("**업체별 입금/출금 (By Date)**")
        for t in date_targets:
            if t in data['merchant_in'] or t in data['merchant_out']:
                st.write(f"{t}: {data['merchant_in'].get(t,0):,} / {data['merchant_out'].get(t,0):,}")