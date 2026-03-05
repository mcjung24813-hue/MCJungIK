import streamlit as st
import pandas as pd
import time
import os
import random
import re
import ast
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 0. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="Factory OS - Cloud DB")

# 🔒 관리자 비밀번호 설정
ADMIN_PASSWORD = "1234"

# -------------------------------------------------------------
# [매우 중요!] 아래 따옴표 안에 본인의 구글 시트 ID를 복사해서 넣으세요.
SHEET_ID = '1gDcLsO5PBfpG_9JCAWOWol_gJgubRU90STsZHGv9hq4' 
# -------------------------------------------------------------

# --- 💡 구글 시트 데이터베이스 연동 함수 ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def load_machine_data():
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Machine_DB")
        data_list = sheet.get_all_values()
        if len(data_list) <= 1: return {}
        return {row[0]: json.loads(row[1]) for row in data_list[1:] if len(row) >= 2}
    except Exception as e:
        return {}

def save_machine_data(data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Machine_DB")
        rows = [["Key", "Value"]] + [[str(k), json.dumps(v)] for k, v in data.items()]
        sheet.clear()
        sheet.update(values=rows, range_name="A1")
    except Exception as e:
        pass

def load_master_data():
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Master_DB")
        data_list = sheet.get_all_values()
        if len(data_list) <= 1: return {}
        return {row[0]: json.loads(row[1]) for row in data_list[1:] if len(row) >= 2}
    except:
        return {}

def save_master_data(data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Master_DB")
        rows = [["Key", "Value"]] + [[str(k), json.dumps(v)] for k, v in data.items()]
        sheet.clear()
        sheet.update(values=rows, range_name="A1")
    except:
        pass

def clear_widget_state(m_name=None):
    if m_name:
        for k in [f"det_p_{m_name}", f"det_t_{m_name}", f"det_c_{m_name}"]:
            if k in st.session_state: del st.session_state[k]

# --- 1. CSS 디자인 (애플 스타일 화이트 테마) ---
st.markdown("""
<style>
.stApp, .stApp > div, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"] {
opacity: 1 !important; filter: none !important; transition: none !important;
}
[data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
display: none !important; opacity: 0 !important; visibility: hidden !important;
}
.stApp { background-color: #fbfbfd; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1d1d1f; }
.modern-header { font-size: 28px; font-weight: 700; color: #1d1d1f; margin-bottom: 10px; padding-top: 20px; letter-spacing: -0.5px; }
.modern-card { background-color: #ffffff; border-radius: 18px; padding: 24px; margin-bottom: 20px; border: none; box-shadow: 0 4px 14px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; gap: 12px; transition: box-shadow 0.3s ease; }
.modern-card:hover { box-shadow: 0 10px 24px rgba(0,0,0,0.08); }
.card-title { font-size: 20px; font-weight: 800; color: #1d1d1f; display: flex; justify-content: space-between; align-items: center; }
.status-container { display: flex; align-items: center; gap: 6px; background: #f5f5f7; padding: 4px 12px; border-radius: 20px; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.status-running { background-color: #007aff; } .text-running { color: #007aff; font-size: 13px; font-weight: 700; }
.status-waiting { background-color: #ff3b30; } .text-waiting { color: #ff3b30; font-size: 13px; font-weight: 700; }
.status-completed { background-color: #34c759; } .text-completed { color: #34c759; font-size: 13px; font-weight: 700; }
.card-product { font-size: 22px; font-weight: 800; color: #1d1d1f; display: flex; align-items: center; flex-wrap: wrap; letter-spacing: -0.5px; margin-top: 4px; }
.product-tag { margin-left:8px; font-size:13px; color:#86868b; background-color:#f5f5f7; padding:4px 10px; border-radius:12px; font-weight:600;}
.card-memo { background-color: #fff8e6; color: #d08a00; padding: 12px; border-radius: 10px; font-size: 14px; margin-top: 5px; font-weight: 600; }
.next-color-tag { display: inline-block; margin-top: 4px; font-size: 14px; color: #ff9500; font-weight: 700; background-color: #fff2e6; padding: 4px 10px; border-radius: 8px; }
.card-metrics { display: flex; gap: 10px; margin-top: 8px; }
.modern-metric { flex: 1; background-color: #f5f5f7; padding: 12px; border-radius: 14px; text-align: left; border: none; }
.modern-metric .metric-label { font-size: 12px; color: #86868b; margin-bottom: 4px; font-weight: 600;}
.modern-metric .metric-value { font-size: 18px; font-weight: 800; color: #1d1d1f; letter-spacing: -0.5px;}
.time-value { color: #ff3b30 !important; }
.schedule-item { background: #ffffff; border: 1px solid #e5e5ea; padding: 12px; margin-bottom: 8px; border-radius: 12px; font-size: 14px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
.history-item { background: #fbfbfd; border: 1px solid #e5e5ea; padding: 12px; margin-bottom: 8px; border-radius: 12px; font-size: 14px; color: #86868b; }
.schedule-date { color: #86868b; font-size: 12px; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)

if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

if 'master_data' not in st.session_state:
    loaded_master = load_master_data()
    if not loaded_master:
        loaded_master = {"---": {"p_code": "-", "color_text": "-", "weight": 0.0, "cycle_time": 0}}
        save_master_data(loaded_master)
    st.session_state.master_data = loaded_master

def get_floor_from_machine(m_name):
    m_name_str = str(m_name)
    if m_name_str.startswith("F1"): return "F1"
    if m_name_str.startswith("F3"): return "F3"
    match = re.search(r'\d', m_name_str)
    if match:
        digit = int(match.group())
        if 1 <= digit <= 4: return "F3"
        elif 5 <= digit <= 8: return "F1"
    return "F1"

def get_machine_sort_key(m_name):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(m_name))]

if 'm_states' not in st.session_state:
    loaded_data = load_machine_data()
    for k, v in loaded_data.items():
        if 'floor' not in v: v['floor'] = get_floor_from_machine(k)
        raw_memo = v.get('memo', '')
        if pd.isna(raw_memo) or str(raw_memo).lower() == 'nan': v['memo'] = ""
        else: v['memo'] = str(raw_memo)
        current_p = str(v.get('p_name', '---'))
        if current_p.lower() == 'nan': current_p = '---'
        v['p_name'] = current_p
        for col in ['schedule', 'history']:
            raw_data = v.get(col, [])
            if isinstance(raw_data, str):
                try: v[col] = ast.literal_eval(raw_data)
                except: v[col] = []
            elif not isinstance(raw_data, list):
                v[col] = []
        if current_p not in st.session_state.master_data:
            st.session_state.master_data[current_p] = {"p_code": "", "color_text": "", "weight": 0.0, "cycle_time": 10}
            save_master_data(st.session_state.master_data)
    st.session_state.m_states = loaded_data

if not st.session_state.m_states:
    default_machines = ["E-IN 851AD", "E-IN 852AD", "E-IN 101ADS", "E-IN 102ADS"]
    for m_name in default_machines:
        st.session_state.m_states[m_name] = {'count': 0, 'last_time': time.time(), 'is_running': False, 'p_name': "---", 'target': 1000, 'schedule': [], 'history': [], 'floor': get_floor_from_machine(m_name), 'memo': ""}

if 'selected_machine' not in st.session_state:
    st.session_state.selected_machine = None

with st.sidebar:
    st.markdown("### ⚙️ 시스템 설정")
    auto_refresh = st.checkbox("실시간 자동 새로고침 켜기", value=True)

def render_details_panel(m_name, m):
    target_val = int(m.get('target', 0))
    count_val = int(m.get('count', 0))
    is_run_val = m.get('is_running', False)
    
    if target_val > 0 and count_val >= target_val:
        status_class = "status-completed"; status_text = "생산완료"; text_class = "text-completed"
    elif is_run_val:
        status_class = "status-running"; status_text = "생산중"; text_class = "text-running"
    else:
        status_class = "status-waiting"; status_text = "대기중"; text_class = "text-waiting"

    st.markdown(f"<div class='modern-card' style='border-left: 5px solid #34c759;'><div class='card-title'>🤖 {m_name} 상세 및 설정<div class='status-container'><span class='status-dot {status_class}'></span><span class='status-text {text_class}'>{status_text}</span></div></div></div>", unsafe_allow_html=True)
    
    st.subheader("📝 특이사항 메모")
    raw_memo = m.get('memo', '')
    safe_memo = str(raw_memo) if pd.notna(raw_memo) and str(raw_memo).lower() != 'nan' else ''
    new_memo = st.text_area("메모 입력 (작업 완료 시 자동 삭제)", value=safe_memo, height=80, key=f"det_memo_{m_name}")
    if st.button("메모 저장", key=f"det_save_memo_{m_name}"):
        m['memo'] = new_memo; save_machine_data(st.session_state.m_states); st.success("메모 반영 완료"); st.rerun()
        
    st.write("---")
    st.subheader("⚙️ 현재 제품 및 수량 설정")
    p_name = str(m.get('p_name', '---'))
    if p_name.lower() == 'nan': p_name = '---'
    if p_name not in st.session_state.master_data:
        st.session_state.master_data[p_name] = {"p_code": "", "color_text": "", "weight": 0.0, "cycle_time": 10}
        save_master_data(st.session_state.master_data)
    
    p_index = list(st.session_state.master_data.keys()).index(p_name)
    selected_p_name = st.selectbox("현재 제품", list(st.session_state.master_data.keys()), index=p_index, key=f"det_p_{m_name}")
    col_t, col_c = st.columns(2)
    with col_t: new_target = st.number_input("목표 수량", min_value=1, value=int(m.get('target', 1000)), key=f"det_t_{m_name}")
    with col_c: new_count = st.number_input("현재 생산량", min_value=0, value=int(m.get('count', 0)), key=f"det_c_{m_name}")
    
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("설정 적용", key=f"det_upd_p_{m_name}"):
            m['p_name'] = selected_p_name; m['target'] = new_target; m['count'] = new_count if new_count <= new_target else new_target; m['last_time'] = time.time()
            clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
    with c_btn2:
        if st.button("수량 리셋", key=f"det_rst_{m_name}"):
            m['count'] = 0; m['last_time'] = time.time()
            clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
    with c_btn3:
        if st.button("⏭️ 당겨오기", key=f"det_next_job_{m_name}"):
            if m['p_name'] != "---":
                if 'history' not in m: m['history'] = []
                m['history'].append({'p_name': m['p_name'], 'target': m['target'], 'count': m['count'], 'date': time.strftime("%H:%M")})
            if m.get('schedule'):
                first_job = m['schedule'].pop(0)
                m.update({'p_name': first_job['p_name'], 'target': first_job['target'], 'count': 0, 'is_running': False, 'last_time': time.time()})
            else:
                m.update({'p_name': "---", 'target': 1000, 'count': 0, 'is_running': False})
            clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()

    st.write("---")
    st.subheader("📋 대기열")
    schedule = m.get('schedule', [])
    if not schedule: st.info("등록된 대기 일정이 없습니다.")
    else:
        for idx, item in enumerate(schedule):
            date_str = f"[{item['date']}] " if 'date' in item and item['date'] else ""
            sch_col, del_col = st.columns([5, 1])
            with sch_col: st.markdown(f"<div class='schedule-item'><div><b>{idx+1}.</b> <span class='schedule-date'>{date_str}</span>{item['p_name']}</div><div>🎯 <b>{item['target']}</b> EA</div></div>", unsafe_allow_html=True)
            with del_col:
                if st.button("❌", key=f"del_sch_{m_name}_{idx}"):
                    m['schedule'].pop(idx); save_machine_data(st.session_state.m_states); st.rerun()

    st.write("---")
    st.subheader("✅ 생산 완료 내역")
    history = m.get('history', [])
    if not history: st.info("아직 내역이 없습니다.")
    else:
        for idx, item in enumerate(reversed(history)):
            real_idx = len(history) - 1 - idx
            hist_date = f"[{item.get('date', '')}]"
            hist_col, readd_col = st.columns([5, 1])
            with hist_col: st.markdown(f"<div class='history-item'><div><b>{real_idx+1}.</b> <span class='schedule-date'>{hist_date}</span>{item['p_name']}</div><div>✔️ <b>{item['count']}</b> / {item['target']} EA</div></div>", unsafe_allow_html=True)
            with readd_col:
                if st.button("🔄 추가", key=f"readd_hist_{m_name}_{real_idx}"):
                    if m.get('p_name', '---') == '---':
                        m.update({'p_name': item['p_name'], 'target': item['target'], 'count': 0, 'is_running': False, 'last_time': time.time()})
                        clear_widget_state(m_name); st.success("즉시 장착되었습니다!")
                    else:
                        if 'schedule' not in m: m['schedule'] = []
                        m['schedule'].append({'p_name': item['p_name'], 'target': item['target'], 'date': '추가생산'})
                        st.success("대기열 추가 완료")
                    save_machine_data(st.session_state.m_states); time.sleep(1); st.rerun()
        if st.button("🗑️ 내역 지우기", key=f"clear_hist_{m_name}"): m['history'] = []; save_machine_data(st.session_state.m_states); st.rerun()

def make_machine_card(m_name):
    now = time.time()
    m = st.session_state.m_states[m_name]
    is_run = m.get('is_running', False)
    safe_p_name = str(m.get('p_name', '---'))
    if safe_p_name.lower() == 'nan': safe_p_name = '---'
    
    master_info = st.session_state.master_data.get(safe_p_name, {})
    p_code = master_info.get("p_code", "")
    color_text = master_info.get("color_text", "")
    weight = master_info.get("weight", 0.0)
    cycle = master_info.get("cycle_time", 10)

    if is_run and cycle > 0:
        elapsed = now - float(m.get('last_time', now))
        if elapsed >= cycle:
            added = int(elapsed // cycle)
            m['count'] = int(m.get('count', 0)) + added
            m['last_time'] = float(m.get('last_time', now)) + (added * cycle)

    if int(m.get('target', 0)) > 0 and int(m.get('count', 0)) >= int(m.get('target', 0)):
        m['count'] = int(m.get('target', 0)); m['is_running'] = False  
        raw_memo = m.get('memo', '')
        if pd.notna(raw_memo) and str(raw_memo).strip() != "" and str(raw_memo).lower() != 'nan': m['memo'] = ""
        save_machine_data(st.session_state.m_states)

    target_val = int(m.get('target', 0)); count_val = int(m.get('count', 0))
    if count_val > target_val: count_val = target_val; m['count'] = count_val
    is_run_val = m.get('is_running', False)
    
    if target_val > 0 and count_val >= target_val: status_class = "status-completed"; status_text = "생산완료"; text_class = "text-completed"
    elif is_run_val: status_class = "status-running"; status_text = "생산중"; text_class = "text-running"
    else: status_class = "status-waiting"; status_text = "대기중"; text_class = "text-waiting"

    rate = round((count_val / target_val * 100), 1) if target_val > 0 else 0
    if rate > 100.0: rate = 100.0

    time_str = "00:00:00"
    if cycle > 0 and count_val < target_val:
        rem_sec = (target_val - count_val) * cycle
        h, rem = divmod(rem_sec, 3600); time_str = f"{int(h):02d}:{int(rem//60):02d}:{int(rem%60):02d}"
    elif count_val >= target_val and target_val > 0: time_str = "작업 완료"

    total_weight_kg = (weight * target_val) / 1000.0

    next_color_html = ""
    if m.get('schedule'):
        next_p = m['schedule'][0]['p_name']
        n_color = st.session_state.master_data.get(next_p, {}).get("color_text", "미지정")
        next_color_html = f"<div class='next-color-tag'>⏭️ NEXT 컬러: {n_color}</div>"

    raw_memo = m.get('memo', ''); memo_text = str(raw_memo).strip() if pd.notna(raw_memo) and str(raw_memo).lower() != 'nan' else ''
    memo_html = f"<div class='card-memo'>📌 {memo_text}</div>" if memo_text else ""
    p_code_html = f"<span style='color:#86868b; font-size:16px; margin-right:6px; font-weight:700;'>[{p_code}]</span>" if p_code else ""
    color_html = f"<span class='product-tag'>🎨 {color_text}</span>" if color_text else ""
    weight_html = f"<span class='product-tag'>⚖️ {weight}g</span>" if weight > 0 else ""

    st.markdown(f"""
<div class="modern-card">
<div class="card-title"><span>🤖 {m_name}</span><div class='status-container'><span class='status-dot {status_class}'></span><span class='status-text {text_class}'>{status_text}</span></div></div>
<div class="card-product">{p_code_html} {safe_p_name} {color_html} {weight_html}</div>
{next_color_html}{memo_html}
<div class="card-metrics">
<div class="modern-metric"><div class="metric-label">생산량(EA)</div><div class="metric-value">{count_val} / {target_val}</div></div>
<div class="modern-metric"><div class="metric-label">원료(kg)</div><div class="metric-value">{total_weight_kg:,.1f}</div></div>
<div class="modern-metric"><div class="metric-label">남은 시간</div><div class="metric-value time-value">{time_str}</div></div>
<div class="modern-metric"><div class="metric-label">달성률</div><div class="metric-value">{rate}%</div></div>
</div></div>
""", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    if target_val > 0 and count_val >= target_val:
        if c1.button("⏭️ NEXT", key=f"next_{m_name}"):
            if m['p_name'] != "---":
                if 'history' not in m: m['history'] = []
                m['history'].append({'p_name': m['p_name'], 'target': m['target'], 'count': m['count'], 'date': time.strftime("%H:%M")})
            if m.get('schedule'):
                first_job = m['schedule'].pop(0)
                m.update({'p_name': first_job['p_name'], 'target': first_job['target'], 'count': 0, 'is_running': False, 'last_time': time.time()})
            else: m.update({'p_name': "---", 'target': 1000, 'count': 0, 'is_running': False})
            clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
        if c2.button("🔄 리셋", key=f"reset_{m_name}"):
            m['count'] = 0; m['is_running'] = False; m['last_time'] = time.time()
            clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
    else:
        if c1.button("▶️ START", key=f"run_{m_name}"):
            if m.get('p_name', '---') == '---':
                if m.get('schedule'):
                    first_job = m['schedule'].pop(0)
                    m.update({'p_name': first_job['p_name'], 'target': first_job['target'], 'count': 0, 'is_running': True, 'last_time': time.time()})
                    clear_widget_state(m_name)
            else: m['is_running'] = True; m['last_time'] = time.time()
            save_machine_data(st.session_state.m_states); st.rerun()
        if c2.button("⏸️ STOP", key=f"stop_{m_name}"):
            m['is_running'] = False; save_machine_data(st.session_state.m_states); st.rerun()
    if c3.button("⚙️ Details", key=f"det_{m_name}"): st.session_state.selected_machine = m_name; st.rerun()

st.markdown("<div class='modern-header'>🤖 Factory OS: Production Line</div>", unsafe_allow_html=True)
t1, t3, t_plan, t_admin = st.tabs(["🏢 1층 생산라인", "🏢 3층 생산라인", "📅 공정계획표", "⚙️ 기준 정보 관리"])
current_selected = st.session_state.selected_machine
f1_machines = sorted([k for k, v in st.session_state.m_states.items() if v.get('floor', 'F1') == 'F1'], key=get_machine_sort_key)
f3_machines = sorted([k for k, v in st.session_state.m_states.items() if v.get('floor', 'F1') == 'F3'], key=get_machine_sort_key)

with t1:
    cols1 = st.columns([1.2, 1.2, 1]); mid1 = len(f1_machines) // 2 + (len(f1_machines) % 2 > 0)
    with cols1[0]:
        for m_name in f1_machines[:mid1]: make_machine_card(m_name)
    with cols1[1]:
        for m_name in f1_machines[mid1:]: make_machine_card(m_name)
    with cols1[2]:
        if current_selected and current_selected in f1_machines: render_details_panel(current_selected, st.session_state.m_states[current_selected])
        else: st.info("👈 기계 카드의 'Details' 버튼을 클릭하세요.")

with t3:
    cols3 = st.columns([1.2, 1.2, 1]); mid3 = len(f3_machines) // 2 + (len(f3_machines) % 2 > 0)
    with cols3[0]:
        for m_name in f3_machines[:mid3]: make_machine_card(m_name)
    with cols3[1]:
        for m_name in f3_machines[mid3:]: make_machine_card(m_name)
    with cols3[2]:
        if current_selected and current_selected in f3_machines: render_details_panel(current_selected, st.session_state.m_states[current_selected])
        else: st.info("👈 기계 카드의 'Details' 버튼을 클릭하세요.")

with t_plan:
    st.subheader("📅 스마트 공정 계획표 (엑셀 뷰)")
    st.info("✨ 표 오른쪽의 **빈칸을 더블클릭**하고 **제품코드**를 입력 후 엔터를 치면 일정이 쏙 들어갑니다! (수량 지정: `코드/수량`)")
    
    def build_table_data(machines_list):
        max_cols = 0; raw_table_data = []
        for m_name in machines_list:
            m = st.session_state.m_states[m_name]; tasks = []
            for h in m.get('history', []): tasks.append(f"✅[완료] {h['p_name']} ({h['count']}EA)")
            curr_p = m.get('p_name', '---')
            if curr_p != '---':
                status_text = "🔄[생산중]" if m.get('is_running', False) else "⏸️[대기중]"
                if m.get('count', 0) >= m.get('target', 1): status_text = "✅[완료대기]"
                tasks.append(f"{status_text} {curr_p} ({int(m.get('count',0))}/{m.get('target')}EA)")
            for sch in m.get('schedule', []): tasks.append(f"⏳[예정] {sch['p_name']} ({sch['target']}EA)")
            max_cols = max(max_cols, len(tasks)); raw_table_data.append({"기계명": m_name, "tasks": tasks})
        display_cols = max_cols + 3; df_list = []
        for row in raw_table_data:
            d = {"기계명": row["기계명"]}
            for i in range(display_cols): d[f"{i+1}순서"] = row["tasks"][i] if i < len(row["tasks"]) else ""
            df_list.append(d)
        return pd.DataFrame(df_list), display_cols

    st.markdown("### 🏢 1층 공정 계획표")
    df_f1, cols_f1 = build_table_data(f1_machines)
    edited_df_f1 = st.data_editor(df_f1, use_container_width=True, hide_index=True, key="editor_f1")

    st.markdown("### 🏢 3층 공정 계획표")
    df_f3, cols_f3 = build_table_data(f3_machines)
    edited_df_f3 = st.data_editor(df_f3, use_container_width=True, hide_index=True, key="editor_f3")
    
    changes_made = False
    for e_df, d_cols in [(edited_df_f1, cols_f1), (edited_df_f3, cols_f3)]:
        for idx, row in e_df.iterrows():
            m_name = str(row.get('기계명', ''))
            if m_name not in st.session_state.m_states: continue
            m = st.session_state.m_states[m_name]
            for i in range(d_cols):
                col_name = f"{i+1}순서"
                if col_name not in row: continue
                cell_val = str(row[col_name]).strip()
                if cell_val != "" and not any(marker in cell_val for marker in ["✅", "🔄", "⏸️", "⏳"]):
                    typed_str = cell_val; target_qty = 1000 
                    if "/" in typed_str:
                        parts = typed_str.split("/"); typed_str = parts[0].strip()
                        try: target_qty = int(parts[1].strip())
                        except: pass
                    matched_p_name = None
                    for p, info in st.session_state.master_data.items():
                        if info.get('p_code') == typed_str: matched_p_name = p; break
                    if not matched_p_name and typed_str in st.session_state.master_data: matched_p_name = typed_str
                    final_p_name = matched_p_name if matched_p_name else typed_str
                    if m.get('p_name', '---') == '---': m.update({'p_name': final_p_name, 'target': target_qty, 'count': 0, 'is_running': False, 'last_time': time.time()}); clear_widget_state(m_name)
                    else:
                        if 'schedule' not in m: m['schedule'] = []
                        m['schedule'].append({'p_name': final_p_name, 'target': target_qty, 'date': time.strftime("%Y-%m-%d")})
                    changes_made = True

    if changes_made: save_machine_data(st.session_state.m_states); st.success("✅ 일정이 자동 추가되었습니다!"); time.sleep(1); st.rerun()

with t_admin:
    st.subheader("⚙️ 시스템 기준 정보 관리")
    if not st.session_state.is_admin:
        st.info("🔒 데이터를 수정하려면 관리자 권한이 필요합니다.")
        col_login1, col_login2 = st.columns([1, 2])
        with col_login1:
            pwd = st.text_input("관리자 비밀번호", type="password")
            if st.button("로그인"):
                if pwd == ADMIN_PASSWORD: st.session_state.is_admin = True; st.success("✅ 로그인 성공!"); time.sleep(0.5); st.rerun()
                else: st.error("❌ 비밀번호가 틀렸습니다.")
        st.write("---"); st.markdown("#### 📋 현재 등록된 제품 목록")
        master_list = [{"제품코드": info.get("p_code", ""), "제품명": p_name, "컬러": info.get("color_text", ""), "무게(g)": info.get("weight", 0.0), "사이클속도(초)": info.get("cycle_time", 10)} for p_name, info in st.session_state.master_data.items()]
        st.dataframe(pd.DataFrame(master_list), use_container_width=True)
    else:
        if st.button("🔓 로그아웃"): st.session_state.is_admin = False; st.rerun()
        st.write("---")
        col_admin1, col_admin2 = st.columns(2)
        with col_admin1:
            st.markdown("#### 📦 제품 (Master Data) 관리")
            with st.expander("➕ 제품 등록 및 수정", expanded=True):
                col_m1, col_m2 = st.columns(2); col_m3, col_m4, col_m5 = st.columns(3)
                with col_m1: a_p_code = st.text_input("제품코드")
                with col_m2: a_p_name = st.text_input("제품명 (필수)")
                with col_m3: a_p_color = st.text_input("컬러 텍스트 (예: 투명)")
                with col_m4: a_p_weight = st.number_input("무게 (g)", min_value=0.0, value=0.0, step=0.1)
                with col_m5: a_p_cycle = st.number_input("사이클 (초)", min_value=0, value=10)
                if st.button("제품 적용하기"):
                    if a_p_name.strip(): st.session_state.master_data[a_p_name] = {"p_code": a_p_code, "color_text": a_p_color, "weight": a_p_weight, "cycle_time": a_p_cycle}; save_master_data(st.session_state.master_data); st.success("저장 완료!"); time.sleep(1); st.rerun()
                    else: st.warning("제품명은 필수입니다.")
            st.write("---"); master_list = [{"제품코드": info.get("p_code", ""), "제품명": p_name, "컬러": info.get("color_text", ""), "무게(g)": info.get("weight", 0.0), "사이클(초)": info.get("cycle_time", 10)} for p_name, info in st.session_state.master_data.items()]
            st.dataframe(pd.DataFrame(master_list), use_container_width=True); st.write("---")
            del_p_name = st.selectbox("삭제할 제품 선택", list(st.session_state.master_data.keys()))
            if st.button("선택 제품 영구 삭제"):
                if del_p_name != "---": del st.session_state.master_data[del_p_name]; save_master_data(st.session_state.master_data); st.success("삭제 완료!"); time.sleep(1); st.rerun()
        with col_admin2:
            st.markdown("#### 🤖 기계 (Machine) 관리")
            with st.expander("➕ 새 기계 라인 추가", expanded=True):
                new_m_name = st.text_input("추가할 기계 이름 (예: F1_5)")
                if st.button("기계 추가하기"):
                    if new_m_name.strip() and new_m_name not in st.session_state.m_states: st.session_state.m_states[new_m_name] = {'count': 0, 'last_time': time.time(), 'is_running': False, 'p_name': "---", 'target': 1000, 'schedule': [], 'history': [], 'floor': get_floor_from_machine(new_m_name), 'memo': ""}; save_machine_data(st.session_state.m_states); st.success("생성 완료!"); time.sleep(1); st.rerun()
            st.write("---"); del_m_name = st.selectbox("철거/삭제할 기계 선택", list(st.session_state.m_states.keys()))
            if st.button("선택 기계 영구 삭제"): del st.session_state.m_states[del_m_name]; save_machine_data(st.session_state.m_states); st.success("철거 완료!"); time.sleep(1); st.rerun()

save_machine_data(st.session_state.m_states)
if auto_refresh: time.sleep(60.0); st.rerun()
