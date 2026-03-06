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

# --- 💡 완벽한 다국어(번역) 딕셔너리 ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'KO'

LANG_DICT = {
    "대기중": "待機中", "생산중": "生産中", "생산완료": "生産完了", "작업 완료": "作業完了",
    "생산량(EA)": "生産量(EA)", "원료(kg)": "原料(kg)", "남은 시간": "残り時間", "달성률": "達成率",
    "▶️ START": "▶️ スタート", "⏸️ STOP": "⏸️ ストップ", "⏭️ NEXT": "⏭️ 次へ", "🔄 리셋": "🔄 リセット",
    "🔽 더보기": "🔽 詳細", "🔼 닫기": "🔼 閉じる",
    "📝 특이사항 메모": "📝 特記事項", "메모 입력": "メモ入力", "메모 저장": "保存",
    "⚙️ 현재 제품 및 수량 설정": "⚙️ 現在の製品及び数量設定",
    "현재 제품": "現在の製品", "목표 수량": "目標数量", "현재 생산량": "現在の生産量",
    "설정 적용": "適用", "수량 리셋": "数量リセット", "⏭️ 당겨오기": "⏭️ 前倒し",
    "📋 대기열": "📋 待機列", "✅ 완료 내역": "✅ 完了履歴", "🗑️ 모두 지우기": "🗑️ 全て消去",
    "대기 일정이 없습니다.": "待機日程がありません。", "아직 내역이 없습니다.": "まだ履歴がありません。",
    "장착 완료!": "装着完了!", "대기열 추가 완료": "待機列に追加完了",
    "🏢 1층 생산라인": "🏢 1階 生産ライン", "🏢 3층 생산라인": "🏢 3階 生産ライン",
    "📅 공정계획표": "📅 工程計画表", "⚙️ 기준 정보 관리": "⚙️ 基準情報管理",
    "🔄 실시간 동기화 (PC ↔ 폰 상태 맞추기)": "🔄 リアルタイム同期 (PC ↔ スマホ)",
    "시스템 설정": "システム設定", "실시간 자동 새로고침 켜기": "自動更新をオンにする",
    "🔄 최신 데이터 동기화 (Sync)": "🔄 最新データ同期 (Sync)",
    "※ 1층 도면 배치도에 포함되지 않은 기계들": "※ 1階配置図に含まれていない機械",
    "스마트 공정 계획표 (엑셀 뷰)": "スマート工程計画表 (Excel View)",
    "☑️ 완료된 공정 기록 숨기기 (진행/예정 항목만 앞으로 당겨서 보기)": "☑️ 完了した工程記録を隠す (進行/予定項目のみ表示)",
    "✨ 표 오른쪽의 빈칸을 더블클릭하고 **완제품코드 또는 부품코드**를 입력 후 엔터를 치면 일정이 쏙 들어갑니다! (수량 지정: `코드/수량`)": "✨ 表の右側の空白をダブルクリックし、**完成品コードまたは部品コード**を入力してEnterを押すと日程が追加されます！ (数量指定: `コード/数量`)",
    "💡 일정이나 기록을 삭제하려면 칸의 글씨를 전부 지우고(백스페이스) 아래의 [저장] 버튼을 누르세요!": "💡 日程や記録を削除するには、マスの文字を全て消して下の[保存]ボタンを押してください！",
    "💾 공정계획표 변경사항 저장 및 적용": "💾 工程計画表の変更を保存・適用",
    "✅ 성공적으로 저장되었습니다!": "✅ 正常に保存されました！",
    "변경된 내용이 없습니다.": "変更された内容がありません。",
    "✅ 일정이 자동 추가되었습니다!": "✅ 日程が自動追加されました！",
    "로그인": "ログイン", "🔓 로그아웃": "🔓 ログアウト", "제품명 (필수)": "製品名 (必須)",
    "제품 적용하기": "製品適用", "기계 추가하기": "機械追加", "선택 기계 영구 삭제": "選択機械の完全削除",
    "기계명": "機械名", "순서": "番目", "완제품코드": "完成品コード", "부품코드": "部品コード",
    "제품명": "製品名", "컬러": "カラー", "무게(g)": "重量(g)", "사이클속도(초)": "サイクル速度(秒)",
    "사이클(초)": "サイクル(秒)", "컬러 텍스트 (예: 투명)": "カラーテキスト (例: 透明)",
    "삭제할 제품 선택": "削除する製品を選択", "선택 제품 영구 삭제": "選択した製品を完全に削除",
    "기계 이름 (예: E-IN 851AD)": "機械名 (例: E-IN 851AD)", "설치 층수": "設置階",
    "철거/삭제할 기계 선택": "撤去/削除する機械を選択", "➕ 제품 등록 및 수정": "➕ 製品の登録と修正",
    "➕ 새 기계 라인 추가": "➕ 新しい機械ラインの追加", "Password": "パスワード",
    "📋 제품 목록 (Product List)": "📋 製品リスト (Product List)",
    "📦 Master Data": "📦 マスターデータ (Master Data)",
    "완료": "完了", "예정": "予定", "완": "完", "부": "部",
    "🔒 데이터를 수정하려면 관리자 권한이 필요합니다.": "🔒 データを修正するには管理者権限が必要です。"
}

def _(text):
    if st.session_state.lang == 'JA':
        return LANG_DICT.get(text, text)
    return text

# --- 💡 구글 시트 연동 ---
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
    except Exception as e: return {}

def save_machine_data(data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Machine_DB")
        rows = [["Key", "Value"]] + [[str(k), json.dumps(v)] for k, v in data.items()]
        sheet.clear()
        sheet.update(values=rows, range_name="A1")
    except Exception as e:
        st.error(f"🚨 기계 DB 저장 에러: {e}")
        st.stop()

def load_master_data():
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Master_DB")
        data_list = sheet.get_all_values()
        if len(data_list) <= 1: return {}
        return {row[0]: json.loads(row[1]) for row in data_list[1:] if len(row) >= 2}
    except: return {}

def save_master_data(data):
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        sheet = sh.worksheet("Master_DB")
        rows = [["Key", "Value"]] + [[str(k), json.dumps(v)] for k, v in data.items()]
        sheet.clear()
        sheet.update(values=rows, range_name="A1")
    except Exception as e:
        st.error(f"🚨 마스터 DB 저장 에러: {e}")
        st.stop()

def clear_widget_state(m_name=None):
    if m_name:
        for k in [f"det_p_{m_name}", f"det_t_{m_name}", f"det_c_{m_name}", f"det_memo_{m_name}"]:
            if k in st.session_state: del st.session_state[k]

# --- 1. 정밀 타겟팅 CSS 디자인 ---
st.markdown("""
<style>
.stApp, .stApp > div, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"] {
opacity: 1 !important; filter: none !important; transition: none !important;
}
[data-testid="stStatusWidget"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
display: none !important; opacity: 0 !important; visibility: hidden !important;
}
.stApp { background-color: #fbfbfd; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1d1d1f; }
.modern-header { font-size: 28px; font-weight: 700; color: #1d1d1f; margin-bottom: 10px; padding-top: 20px; letter-spacing: -0.5px; }

.machine-title { font-size: 20px; font-weight: 800; color: #1d1d1f; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.status-container { display: flex; align-items: center; gap: 6px; background: #f5f5f7; padding: 4px 12px; border-radius: 20px; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.status-running { background-color: #007aff; } .text-running { color: #007aff; font-size: 13px; font-weight: 700; }
.status-waiting { background-color: #ff3b30; } .text-waiting { color: #ff3b30; font-size: 13px; font-weight: 700; }
.status-completed { background-color: #34c759; } .text-completed { color: #34c759; font-size: 13px; font-weight: 700; }
.card-product { font-size: 21px; font-weight: 800; color: #1d1d1f; display: flex; align-items: center; flex-wrap: wrap; letter-spacing: -0.5px; margin-bottom: 8px; line-height: 1.3;}
.product-tag { margin-left:8px; font-size:13px; color:#86868b; background-color:#f5f5f7; padding:4px 10px; border-radius:12px; font-weight:600; margin-top:4px;}
.card-memo { background-color: #fff8e6; color: #d08a00; padding: 10px 12px; border-radius: 10px; font-size: 14px; margin-bottom: 10px; font-weight: 600; }
.next-color-tag { display: inline-block; font-size: 13px; color: #ff9500; font-weight: 700; background-color: #fff2e6; padding: 4px 10px; border-radius: 8px; margin-bottom: 10px; }
.card-metrics { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.modern-metric { flex: 1; min-width: 80px; background-color: #f5f5f7; padding: 12px; border-radius: 14px; text-align: left; }
.metric-label { font-size: 11px; color: #86868b; margin-bottom: 4px; font-weight: 600;}
.metric-value { font-size: 17px; font-weight: 800; color: #1d1d1f; letter-spacing: -0.5px;}
.time-value { color: #ff3b30 !important; }
.schedule-item { background: #fbfbfd; border: 1px solid #e5e5ea; padding: 10px; margin-bottom: 6px; border-radius: 10px; font-size: 13px; font-weight: 500;}
.history-item { background: #fbfbfd; border: 1px solid #e5e5ea; padding: 10px; margin-bottom: 6px; border-radius: 10px; font-size: 13px; color: #86868b; }

/* 📱 모바일 강제 2열 최적화 (버튼 박스 깨짐 완벽 방지) */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"]:has(.grid-marker) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.3rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.grid-marker) > div[data-testid="column"] {
        width: 50% !important;
        min-width: 50% !important;
    }
    .machine-title { font-size: 15px !important; margin-bottom: 5px !important; }
    .status-container { padding: 2px 6px !important; }
    .status-text { font-size: 10px !important; }
    .card-product { font-size: 13px !important; }
    .modern-metric { padding: 6px !important; min-width: 45px !important; }
    .metric-value { font-size: 14px !important; }
    .metric-label { font-size: 9px !important; margin-bottom: 2px !important; }
    span[style*="font-size:14px"] { font-size: 10px !important; }
    .stButton>button { padding: 2px 4px !important; font-size: 12px !important; min-height: 35px !important; }
}
</style>
""", unsafe_allow_html=True)

if 'is_admin' not in st.session_state: st.session_state.is_admin = False

if 'master_data' not in st.session_state:
    loaded_master = load_master_data()
    if not loaded_master:
        loaded_master = {"---": {"p_code": "-", "p_part_code": "-", "color_text": "-", "weight": 0.0, "cycle_time": 0}}
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
        v['memo'] = "" if pd.isna(raw_memo) or str(raw_memo).lower() == 'nan' else str(raw_memo)
        current_p = str(v.get('p_name', '---'))
        v['p_name'] = '---' if current_p.lower() == 'nan' else current_p
        for col in ['schedule', 'history']:
            raw_data = v.get(col, [])
            if isinstance(raw_data, str):
                try: v[col] = ast.literal_eval(raw_data)
                except: v[col] = []
            elif not isinstance(raw_data, list): v[col] = []
        if current_p not in st.session_state.master_data:
            st.session_state.master_data[current_p] = {"p_code": "", "p_part_code": "", "color_text": "", "weight": 0.0, "cycle_time": 10}
            save_master_data(st.session_state.master_data)
    st.session_state.m_states = loaded_data

if not st.session_state.m_states:
    default_machines = ["851", "854"]
    for m_name in default_machines:
        st.session_state.m_states[m_name] = {'count': 0, 'last_time': time.time(), 'is_running': False, 'p_name': "---", 'target': 1000, 'schedule': [], 'history': [], 'floor': get_floor_from_machine(m_name), 'memo': ""}

if 'selected_machine' not in st.session_state:
    st.session_state.selected_machine = None

def render_unified_machine_card(m_name):
    now = time.time()
    m = st.session_state.m_states[m_name]
    is_run = m.get('is_running', False)
    safe_p_name = str(m.get('p_name', '---'))
    if safe_p_name.lower() == 'nan': safe_p_name = '---'
    
    master_info = st.session_state.master_data.get(safe_p_name, {})
    p_code = master_info.get("p_code", "")
    p_part_code = master_info.get("p_part_code", "")
    color_text = master_info.get("color_text", "")
    weight = master_info.get("weight", 0.0)
    cycle = master_info.get("cycle_time", 10)

    if is_run and cycle > 0:
        elapsed = now - float(m.get('last_time', now))
        if elapsed >= cycle:
            added = int(elapsed // cycle)
            m['count'] = int(m.get('count', 0)) + added
            m['last_time'] = float(m.get('last_time', now)) + (added * cycle)
            save_machine_data(st.session_state.m_states)

    if int(m.get('target', 0)) > 0 and int(m.get('count', 0)) >= int(m.get('target', 0)):
        m['count'] = int(m.get('target', 0)); m['is_running'] = False  
        raw_memo = m.get('memo', '')
        if pd.notna(raw_memo) and str(raw_memo).strip() != "" and str(raw_memo).lower() != 'nan': m['memo'] = ""
        save_machine_data(st.session_state.m_states)

    target_val = int(m.get('target', 0)); count_val = int(m.get('count', 0))
    if count_val > target_val: count_val = target_val; m['count'] = count_val
    is_run_val = m.get('is_running', False)
    
    if target_val > 0 and count_val >= target_val: status_class = "status-completed"; status_text = _("생산완료"); text_class = "text-completed"
    elif is_run_val: status_class = "status-running"; status_text = _("생산중"); text_class = "text-running"
    else: status_class = "status-waiting"; status_text = _("대기중"); text_class = "text-waiting"

    rate = round((count_val / target_val * 100), 1) if target_val > 0 else 0
    if rate > 100.0: rate = 100.0

    time_str = "00:00:00"
    if cycle > 0 and count_val < target_val:
        rem_sec = (target_val - count_val) * cycle
        h, rem = divmod(rem_sec, 3600); time_str = f"{int(h):02d}:{int(rem//60):02d}:{int(rem%60):02d}"
    elif count_val >= target_val and target_val > 0: time_str = _("작업 완료")

    total_weight_kg = (weight * target_val) / 1000.0

    next_color_html = ""
    if m.get('schedule'):
        next_p = m['schedule'][0]['p_name']
        n_color = st.session_state.master_data.get(next_p, {}).get("color_text", "미지정")
        next_color_html = f"<div class='next-color-tag'>⏭️ NEXT 컬러: {n_color}</div>"

    raw_memo = m.get('memo', ''); memo_text = str(raw_memo).strip() if pd.notna(raw_memo) and str(raw_memo).lower() != 'nan' else ''
    memo_html = f"<div class='card-memo'>📌 {memo_text}</div>" if memo_text else ""
    
    p_code_html = f"<span style='color:#007aff; font-size:14px; margin-right:4px; font-weight:700;'>[{_('완')}: {p_code}]</span>" if p_code else ""
    p_part_code_html = f"<span style='color:#ff9500; font-size:14px; margin-right:6px; font-weight:700;'>[{_('부')}: {p_part_code}]</span>" if p_part_code else ""
    color_html = f"<span class='product-tag'>🎨 {color_text}</span>" if color_text else ""
    weight_html = f"<span class='product-tag'>⚖️ {weight}g</span>" if weight > 0 else ""

    is_open = (st.session_state.selected_machine == m_name)

    with st.container(border=True):
        st.markdown(f"""
        <div class="machine-title"><span>🤖 {m_name}</span><div class='status-container'><span class='status-dot {status_class}'></span><span class='status-text {text_class}'>{status_text}</span></div></div>
        <div class="card-product"><div>{p_code_html}{p_part_code_html} {safe_p_name}</div> {color_html} {weight_html}</div>
        {next_color_html}{memo_html}
        <div class="card-metrics">
        <div class="modern-metric"><div class="metric-label">{_('생산량(EA)')}</div><div class="metric-value">{count_val} / {target_val}</div></div>
        <div class="modern-metric"><div class="metric-label">{_('원료(kg)')}</div><div class="metric-value">{total_weight_kg:,.1f}</div></div>
        <div class="modern-metric"><div class="metric-label">{_('남은 시간')}</div><div class="metric-value time-value">{time_str}</div></div>
        <div class="modern-metric"><div class="metric-label">{_('달성률')}</div><div class="metric-value">{rate}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        c_btn1, c_btn2 = st.columns(2)
        if target_val > 0 and count_val >= target_val:
            with c_btn1:
                if st.button(_("⏭️ NEXT"), key=f"next_{m_name}", use_container_width=True):
                    if m['p_name'] != "---":
                        if 'history' not in m: m['history'] = []
                        m['history'].append({'p_name': m['p_name'], 'target': m['target'], 'count': m['count'], 'date': time.strftime("%H:%M")})
                    if m.get('schedule'):
                        first_job = m['schedule'].pop(0)
                        m.update({'p_name': first_job['p_name'], 'target': first_job['target'], 'count': 0, 'is_running': False, 'last_time': time.time()})
                    else: m.update({'p_name': "---", 'target': 1000, 'count': 0, 'is_running': False})
                    clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
            with c_btn2:
                if st.button(_("🔄 리셋"), key=f"reset_{m_name}", use_container_width=True):
                    m['count'] = 0; m['is_running'] = False; m['last_time'] = time.time()
                    clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
        else:
            with c_btn1:
                if st.button(_("▶️ START"), key=f"run_{m_name}", use_container_width=True):
                    if m.get('p_name', '---') == '---':
                        if m.get('schedule'):
                            first_job = m['schedule'].pop(0)
                            m.update({'p_name': first_job['p_name'], 'target': first_job['target'], 'count': 0, 'is_running': True, 'last_time': time.time()})
                            clear_widget_state(m_name)
                    else: m['is_running'] = True; m['last_time'] = time.time()
                    save_machine_data(st.session_state.m_states); st.rerun()
            with c_btn2:
                if st.button(_("⏸️ STOP"), key=f"stop_{m_name}", use_container_width=True):
                    m['is_running'] = False; save_machine_data(st.session_state.m_states); st.rerun()
        
        btn_text = _("🔼 닫기") if is_open else _("🔽 더보기")
        if st.button(btn_text, key=f"det_toggle_{m_name}", use_container_width=True):
            if is_open: st.session_state.selected_machine = None
            else: st.session_state.selected_machine = m_name
            st.rerun()

        if is_open:
            st.divider() 
            st.markdown(f"**{_('📝 특이사항 메모')}**")
            raw_memo = m.get('memo', '')
            safe_memo = str(raw_memo) if pd.notna(raw_memo) and str(raw_memo).lower() != 'nan' else ''
            new_memo = st.text_area(_("메모 입력"), value=safe_memo, height=68, key=f"det_memo_{m_name}", label_visibility="collapsed")
            if st.button(_("메모 저장"), key=f"det_save_memo_{m_name}", use_container_width=True):
                m['memo'] = new_memo; save_machine_data(st.session_state.m_states); st.success("OK"); st.rerun()
                
            st.write("---")
            st.markdown(f"**{_('⚙️ 현재 제품 및 수량 설정')}**")
            p_name = str(m.get('p_name', '---'))
            if p_name.lower() == 'nan': p_name = '---'
            if p_name not in st.session_state.master_data:
                st.session_state.master_data[p_name] = {"p_code": "", "p_part_code": "", "color_text": "", "weight": 0.0, "cycle_time": 10}
                save_master_data(st.session_state.master_data)
            
            p_index = list(st.session_state.master_data.keys()).index(p_name)
            selected_p_name = st.selectbox(_("현재 제품"), list(st.session_state.master_data.keys()), index=p_index, key=f"det_p_{m_name}")
            col_t, col_c = st.columns(2)
            with col_t: new_target = st.number_input(_("목표 수량"), min_value=1, value=int(m.get('target', 1000)), key=f"det_t_{m_name}")
            with col_c: new_count = st.number_input(_("현재 생산량"), min_value=0, value=int(m.get('count', 0)), key=f"det_c_{m_name}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(_("설정 적용"), key=f"det_upd_p_{m_name}", use_container_width=True):
                m['p_name'] = selected_p_name; m['target'] = new_target; m['count'] = new_count if new_count <= new_target else new_target; m['last_time'] = time.time()
                clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
            if st.button(_("수량 리셋"), key=f"det_rst_{m_name}", use_container_width=True):
                m['count'] = 0; m['last_time'] = time.time()
                clear_widget_state(m_name); save_machine_data(st.session_state.m_states); st.rerun()
            if st.button(_("⏭️ 당겨오기"), key=f"det_next_job_{m_name}", use_container_width=True):
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
            st.markdown(f"**{_('📋 대기열')}**")
            schedule = m.get('schedule', [])
            if not schedule: st.info(_("대기 일정이 없습니다."))
            else:
                for idx, item in enumerate(schedule):
                    date_str = f"[{item['date']}] " if 'date' in item and item['date'] else ""
                    sch_col, del_col = st.columns([5, 1])
                    with sch_col: st.markdown(f"<div class='schedule-item'><div><b>{idx+1}.</b> <span class='schedule-date'>{date_str}</span>{item['p_name']}</div><div>🎯 <b>{item['target']}</b> EA</div></div>", unsafe_allow_html=True)
                    with del_col:
                        if st.button("❌", key=f"del_sch_{m_name}_{idx}"):
                            m['schedule'].pop(idx); save_machine_data(st.session_state.m_states); st.rerun()

            st.write("---")
            st.markdown(f"**{_('✅ 완료 내역')}**")
            history = m.get('history', [])
            if not history: st.info(_("아직 내역이 없습니다."))
            else:
                for idx, item in enumerate(reversed(history)):
                    real_idx = len(history) - 1 - idx
                    hist_date = f"[{item.get('date', '')}]"
                    hist_col, readd_col = st.columns([5, 1])
                    with hist_col: st.markdown(f"<div class='history-item'><div><b>{real_idx+1}.</b> <span class='schedule-date'>{hist_date}</span>{item['p_name']}</div><div>✔️ <b>{item['count']}</b> / {item['target']} EA</div></div>", unsafe_allow_html=True)
                    with readd_col:
                        if st.button("🔄", key=f"readd_hist_{m_name}_{real_idx}"):
                            if m.get('p_name', '---') == '---':
                                m.update({'p_name': item['p_name'], 'target': item['target'], 'count': 0, 'is_running': False, 'last_time': time.time()})
                                clear_widget_state(m_name); st.success(_("장착 완료!"))
                            else:
                                if 'schedule' not in m: m['schedule'] = []
                                m['schedule'].append({'p_name': item['p_name'], 'target': item['target'], 'date': '추가생산'})
                                st.success(_("대기열 추가 완료"))
                            save_machine_data(st.session_state.m_states); time.sleep(1); st.rerun()
                if st.button(_("🗑️ 모두 지우기"), key=f"clear_hist_{m_name}", use_container_width=True): m['history'] = []; save_machine_data(st.session_state.m_states); st.rerun()

# --- 사이드바 번역 설정 ---
with st.sidebar:
    st.markdown(f"### ⚙️ {_('시스템 설정')}")
    lang_mode = st.radio("🌐 언어 / 言語", ["🇰🇷 한국어", "🇯🇵 日本語"], horizontal=True)
    if "日本語" in lang_mode and st.session_state.lang != 'JA':
        st.session_state.lang = 'JA'
        st.rerun()
    elif "한국어" in lang_mode and st.session_state.lang != 'KO':
        st.session_state.lang = 'KO'
        st.rerun()
        
    auto_refresh = st.checkbox(_("실시간 자동 새로고침 켜기"), value=True)
    st.markdown("---")
    if st.button(_("🔄 최신 데이터 동기화 (Sync)")):
        st.session_state.m_states = load_machine_data()
        st.session_state.master_data = load_master_data()
        st.rerun()

st.markdown("<div class='modern-header'>🤖 Factory OS: Production Line</div>", unsafe_allow_html=True)

if st.button(_("🔄 실시간 동기화 (PC ↔ 폰 상태 맞추기)"), use_container_width=True):
    st.session_state.m_states = load_machine_data()
    st.session_state.master_data = load_master_data()
    st.rerun()

t1, t3, t_plan, t_admin = st.tabs([_("🏢 1층 생산라인"), _("🏢 3층 생산라인"), _("📅 공정계획표"), _("⚙️ 기준 정보 관리")])

f1_machines = sorted([k for k, v in st.session_state.m_states.items() if v.get('floor', 'F1') == 'F1'], key=get_machine_sort_key)
f3_machines = sorted([k for k, v in st.session_state.m_states.items() if v.get('floor', 'F1') == 'F3'], key=get_machine_sort_key)

with t1:
    f1_layout_pairs = [
        ("851", "854"), ("852", "853"), ("651", "654"), ("652", "653"),
        ("551", "5510"), ("552", "559"), ("553", "558"), ("554", "557"),
        ("655", "556"), ("656", "555")
    ]
    layout_all_set = set()

    def find_real_name(target_num_str):
        for m_name in f1_machines:
            extracted_nums = re.findall(r'\d+', m_name) 
            if target_num_str in extracted_nums: return m_name
        return None

    for left_num, right_num in f1_layout_pairs:
        real_left_m = find_real_name(left_num)
        real_right_m = find_real_name(right_num)
        if real_left_m: layout_all_set.add(real_left_m)
        if real_right_m: layout_all_set.add(real_right_m)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<span class='grid-marker'></span>", unsafe_allow_html=True)
            if real_left_m: render_unified_machine_card(real_left_m)
        with c2:
            st.markdown("<span class='grid-marker'></span>", unsafe_allow_html=True)
            if real_right_m: render_unified_machine_card(real_right_m)
                
    leftovers = [m for m in f1_machines if m not in layout_all_set]
    if leftovers:
        st.markdown("---")
        st.caption(_("※ 1층 도면 배치도에 포함되지 않은 기계들"))
        leftover_cols = st.columns(2)
        for idx, m_name in enumerate(leftovers):
            with leftover_cols[idx % 2]:
                st.markdown("<span class='grid-marker'></span>", unsafe_allow_html=True)
                render_unified_machine_card(m_name)

with t3:
    cols3 = st.columns(2)
    mid3 = len(f3_machines) // 2 + (len(f3_machines) % 2 > 0)
    with cols3[0]:
        st.markdown("<span class='grid-marker'></span>", unsafe_allow_html=True)
        for m_name in f3_machines[:mid3]: render_unified_machine_card(m_name)
    with cols3[1]:
        st.markdown("<span class='grid-marker'></span>", unsafe_allow_html=True)
        for m_name in f3_machines[mid3:]: render_unified_machine_card(m_name)

# --- 💡 공정계획표 탭 (마스터 삭제/저장 기능 적용) ---
with t_plan:
    st.subheader(f"📅 {_('스마트 공정 계획표 (엑셀 뷰)')}")
    hide_history = st.checkbox(_("☑️ 완료된 공정 기록 숨기기 (진행/예정 항목만 앞으로 당겨서 보기)"), value=True)
    st.info(_("✨ 표 오른쪽의 빈칸을 더블클릭하고 **완제품코드 또는 부품코드**를 입력 후 엔터를 치면 일정이 쏙 들어갑니다! (수량 지정: `코드/수량`)"))
    st.warning(_("💡 일정이나 기록을 삭제하려면 칸의 글씨를 전부 지우고(백스페이스) 아래의 [저장] 버튼을 누르세요!"))
    
    def build_table_data(machines_list, hide_hist):
        max_cols = 0; raw_table_data = []
        for m_name in machines_list:
            m = st.session_state.m_states[m_name]; tasks = []
            if not hide_hist:
                for h in m.get('history', []): tasks.append(f"✅[{_('완료')}] {h['p_name']} ({h['count']}EA)")
            curr_p = m.get('p_name', '---')
            if curr_p != '---':
                status_text = f"🔄[{_('생산중')}]" if m.get('is_running', False) else f"⏸️[{_('대기중')}]"
                if int(m.get('count', 0)) >= int(m.get('target', 1)): status_text = f"✅[{_('생산완료')}]"
                tasks.append(f"{status_text} {curr_p} ({int(m.get('count',0))}/{m.get('target')}EA)")
            for sch in m.get('schedule', []): tasks.append(f"⏳[{_('예정')}] {sch['p_name']} ({sch['target']}EA)")
            max_cols = max(max_cols, len(tasks)); raw_table_data.append({"기계명": m_name, "tasks": tasks})
            
        display_cols = max_cols + 3; df_list = []
        for row in raw_table_data:
            d = {_("기계명"): row["기계명"]}
            for i in range(display_cols): d[f"{i+1}{_('순서')}"] = row["tasks"][i] if i < len(row["tasks"]) else ""
            df_list.append(d)
        return pd.DataFrame(df_list), display_cols

    st.markdown(f"### {_('🏢 1층 생산라인')}")
    df_f1, cols_f1 = build_table_data(f1_machines, hide_history)
    edited_df_f1 = st.data_editor(df_f1, use_container_width=True, hide_index=True, key="editor_f1")

    st.markdown(f"### {_('🏢 3층 생산라인')}")
    df_f3, cols_f3 = build_table_data(f3_machines, hide_history)
    edited_df_f3 = st.data_editor(df_f3, use_container_width=True, hide_index=True, key="editor_f3")
    
    # 💡 한 번에 전체를 분석해서 삭제와 추가를 동시에 처리하는 강력한 저장 버튼!
    if st.button(_("💾 공정계획표 변경사항 저장 및 적용"), use_container_width=True):
        def process_df(e_df, m_list):
            changes = False
            for idx, row in e_df.iterrows():
                m_name = str(row.get(_('기계명'), ''))
                if m_name not in st.session_state.m_states: continue
                m = st.session_state.m_states[m_name]
                
                # 표에 남아있는 글씨들만 긁어모읍니다 (지운 칸은 제외됨)
                edited_cells = [str(row[col]).strip() for col in e_df.columns if col != _('기계명') and str(row[col]).strip() != ""]
                
                # 1. 완료 기록 삭제 확인 (숨기기 모드가 아닐 때만 작동)
                if not hide_history:
                    kept_history = []
                    for h in m.get('history', []):
                        h_str = f"✅[{_('완료')}] {h['p_name']} ({h['count']}EA)"
                        if h_str in edited_cells:
                            kept_history.append(h)
                            edited_cells.remove(h_str)
                    if len(kept_history) != len(m.get('history', [])): changes = True
                    m['history'] = kept_history
                    
                # 2. 현재 작업 삭제 확인
                curr_p = m.get('p_name', '---')
                if curr_p != '---':
                    status_text = f"🔄[{_('생산중')}]" if m.get('is_running', False) else f"⏸️[{_('대기중')}]"
                    if int(m.get('count', 0)) >= int(m.get('target', 1)): status_text = f"✅[{_('생산완료')}]"
                    c_str = f"{status_text} {curr_p} ({int(m.get('count',0))}/{m.get('target')}EA)"
                    
                    if c_str in edited_cells:
                        edited_cells.remove(c_str)
                    else:
                        m['p_name'] = "---"; m['target'] = 1000; m['count'] = 0; m['is_running'] = False
                        changes = True
                        
                # 3. 대기열(예정) 삭제 확인
                kept_schedule = []
                for sch in m.get('schedule', []):
                    s_str = f"⏳[{_('예정')}] {sch['p_name']} ({sch['target']}EA)"
                    if s_str in edited_cells:
                        kept_schedule.append(sch)
                        edited_cells.remove(s_str)
                if len(kept_schedule) != len(m.get('schedule', [])): changes = True
                m['schedule'] = kept_schedule
                
                # 4. 새롭게 추가된 작업들 등록 (코드 치고 엔터친 부분)
                for cell_val in edited_cells:
                    if not any(marker in cell_val for marker in ["✅", "🔄", "⏸️", "⏳"]):
                        typed_str = cell_val; target_qty = 1000 
                        if "/" in typed_str:
                            parts = typed_str.split("/")
                            typed_str = parts[0].strip()
                            try: target_qty = int(parts[1].strip())
                            except: pass
                            
                        matched_p_name = None
                        for p, info in st.session_state.master_data.items():
                            if info.get('p_code') == typed_str or info.get('p_part_code') == typed_str: 
                                matched_p_name = p; break
                        final_p_name = matched_p_name if matched_p_name else typed_str
                        
                        if m.get('p_name', '---') == '---': 
                            m.update({'p_name': final_p_name, 'target': target_qty, 'count': 0, 'is_running': False, 'last_time': time.time()})
                            clear_widget_state(m_name)
                        else:
                            if 'schedule' not in m: m['schedule'] = []
                            m['schedule'].append({'p_name': final_p_name, 'target': target_qty, 'date': time.strftime("%Y-%m-%d")})
                        changes = True
            return changes
            
        c1_changed = process_df(edited_df_f1, f1_machines)
        c3_changed = process_df(edited_df_f3, f3_machines)
        
        if c1_changed or c3_changed:
            save_machine_data(st.session_state.m_states)
            st.success(_("✅ 성공적으로 저장되었습니다!"))
            time.sleep(1)
            st.rerun()
        else:
            st.info(_("변경된 내용이 없습니다."))

with t_admin:
    st.subheader(f"⚙️ {_('시스템 설정')}")
    if not st.session_state.is_admin:
        st.info(_("🔒 데이터를 수정하려면 관리자 권한이 필요합니다."))
        col_login1, col_login2 = st.columns([1, 2])
        with col_login1:
            pwd = st.text_input(_("Password"), type="password")
            if st.button(_("로그인")):
                if pwd == ADMIN_PASSWORD: st.session_state.is_admin = True; st.success("OK"); time.sleep(0.5); st.rerun()
        st.write("---"); st.markdown(f"#### {_('📋 제품 목록 (Product List)')}")
        master_list = [{_("완제품코드"): info.get("p_code", ""), _("부품코드"): info.get("p_part_code", ""), _("제품명"): p_name, _("컬러"): info.get("color_text", ""), _("무게(g)"): info.get("weight", 0.0), _("사이클속도(초)"): info.get("cycle_time", 10)} for p_name, info in st.session_state.master_data.items()]
        st.dataframe(pd.DataFrame(master_list), use_container_width=True)
    else:
        if st.button(_("🔓 로그아웃")): st.session_state.is_admin = False; st.rerun()
        st.write("---")
        
        st.markdown(f"#### {_('📦 Master Data')}")
        with st.expander(_("➕ 제품 등록 및 수정"), expanded=True):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1: a_p_code = st.text_input(_("완제품코드"))
            with col_m2: a_p_part_code = st.text_input(_("부품코드"))
            with col_m3: a_p_name = st.text_input(_("제품명 (필수)"))
            
            col_m4, col_m5, col_m6 = st.columns(3)
            with col_m4: a_p_color = st.text_input(_("컬러 텍스트 (예: 투명)"))
            with col_m5: a_p_number = st.number_input(_("무게(g)"), min_value=0.0, value=0.0, step=0.1)
            with col_m6: a_p_cycle = st.number_input(_("사이클(초)"), min_value=0, value=10)
            
            if st.button(_("제품 적용하기")):
                if a_p_name.strip(): 
                    st.session_state.master_data[a_p_name] = {"p_code": a_p_code, "p_part_code": a_p_part_code, "color_text": a_p_color, "weight": a_p_number, "cycle_time": a_p_cycle}
                    save_master_data(st.session_state.master_data)
                    st.success("OK")
                    time.sleep(1)
                    st.rerun()
                
        st.write("---")
        master_list = [{_("완제품코드"): info.get("p_code", ""), _("부품코드"): info.get("p_part_code", ""), _("제품명"): p_name, _("컬러"): info.get("color_text", ""), _("무게(g)"): info.get("weight", 0.0), _("사이클(초)"): info.get("cycle_time", 10)} for p_name, info in st.session_state.master_data.items()]
        st.dataframe(pd.DataFrame(master_list), use_container_width=True)
        
        st.write("---")
        col_admin1, col_admin2 = st.columns(2)
        with col_admin1:
            del_p_name = st.selectbox(_("삭제할 제품 선택"), list(st.session_state.master_data.keys()))
            if st.button(_("선택 제품 영구 삭제")):
                if del_p_name != "---": del st.session_state.master_data[del_p_name]; save_master_data(st.session_state.master_data); st.success("OK"); time.sleep(1); st.rerun()
        with col_admin2:
            with st.expander(_("➕ 새 기계 라인 추가"), expanded=False):
                new_m_name = st.text_input(_("기계 이름 (예: E-IN 851AD)"))
                new_m_floor = st.radio(_("설치 층수"), ["F1", "F3"], horizontal=True)
                if st.button(_("기계 추가하기")):
                    if new_m_name.strip() and new_m_name not in st.session_state.m_states:
                        st.session_state.m_states[new_m_name] = {
                            'count': 0, 'last_time': time.time(), 'is_running': False, 
                            'p_name': "---", 'target': 1000, 'schedule': [], 'history': [], 
                            'floor': new_m_floor, 'memo': ""
                        }
                        save_machine_data(st.session_state.m_states)
                        st.success("OK")
                        time.sleep(1)
                        st.rerun()
            del_m_name = st.selectbox(_("철거/삭제할 기계 선택"), list(st.session_state.m_states.keys()))
            if st.button(_("선택 기계 영구 삭제")): del st.session_state.m_states[del_m_name]; save_machine_data(st.session_state.m_states); st.success("OK"); time.sleep(1); st.rerun()

if auto_refresh:
    time.sleep(15.0) 
    st.session_state.m_states = load_machine_data()
    st.session_state.master_data = load_master_data()
    st.rerun()
