import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ==========================================
# 🔧 ส่วนตั้งค่าระบบ (USER CONFIGURATION)
# ==========================================

# 🔴 ใส่ลิงก์ของคุณที่นี่เหมือนเดิมครับ
CONFIG_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=0&single=true&output=csv"
SHEET_URLS = {
    "213": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=338894171&single=true&output=csv",
    "214": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=1135646679&single=true&output=csv",
    "407": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=2076773668&single=true&output=csv",
    "503-504, 515-516": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=1914767177&single=true&output=csv",
    "505-512": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=411570775&single=true&output=csv",
}

TEACHER_PASSWORD = "1234"

# ==========================================
# 🎨 ส่วนตกแต่ง UI (CSS STYLING)
# ==========================================
st.set_page_config(page_title="ระบบติดตามผลการเรียน", page_icon="🎓", layout="wide")

# ใส่ CSS เพื่อความสวยงาม (ฟอนต์ Prompt, การ์ดสวยๆ)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Prompt', sans-serif;
        }
        
        /* ตกแต่ง Header */
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 600;
        }
        
        /* การ์ดรายงานผล */
        .report-card {
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        
        /* สถานะผ่าน/ไม่ผ่าน */
        .status-pass {
            color: #27ae60;
            font-weight: bold;
            font-size: 1.2em;
        }
        .status-fail {
            color: #c0392b;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        /* ปรับแต่ง Table */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🚀 ระบบคำนวณ (LOGIC)
# ==========================================

@st.cache_data(ttl=300)
def load_data(room_id):
    try:
        if room_id not in SHEET_URLS: return None, None, "LinkNotFound"
        
        config_df = pd.read_csv(CONFIG_URL)
        config_df['SheetName'] = config_df['SheetName'].astype(str)
        
        scores_df = pd.read_csv(SHEET_URLS[room_id])
        scores_df['ห้อง'] = scores_df['ห้อง'].astype(str)
        scores_df['Student_ID'] = scores_df['Email'].apply(lambda x: str(x).split('@')[0])
        
        room_config = config_df[config_df['SheetName'] == room_id]
        if room_config.empty: return None, None, "ConfigNotFound"
            
        return room_config.iloc[0], scores_df, "OK"
    except Exception as e: return None, None, str(e)

def get_max_score(header):
    match = re.search(r'\[(\d+)\]', header)
    return int(match.group(1)) if match else 0

def calculate_score(student_row, config, mode="Pre+Mid"):
    total_score = 0.0
    total_full = 0
    
    # วนลูปตาม Keyword เพื่อคำนวณ
    keywords = []
    if "Pre" in mode: keywords.append(("Pre_", config['Scale_Pre']))
    if "Mid" in mode: keywords.append(("Mid_", config['Scale_Mid']))
    if "Post" in mode: keywords.append(("Post_", config['Scale_Post']))
    if "Final" in mode: keywords.append(("Final_", config['Scale_Final']))
    
    for prefix, scale in keywords:
        cols = [c for c in student_row.index if str(c).startswith(prefix)]
        if cols:
            raw = student_row[cols].fillna(0).sum()
            max_raw = sum([get_max_score(c) for c in cols])
            
            # คำนวณสัดส่วน
            if max_raw > 0:
                part_score = (raw / max_raw * scale)
            else:
                # กรณีไม่มี Max ในชื่อคอลัมน์ หรือ Max=0 ให้ใช้คะแนนดิบเลย (ระวังคะแนนเกิน Scale)
                part_score = raw 
            
            total_score += part_score
        total_full += scale

    # 🔥 ปัดเศษเป็นจำนวนเต็มตามที่ต้องการ (Round)
    # round(31.5) -> 32, round(31.4) -> 31
    final_score_int = int(round(total_score))
    
    return final_score_int, total_full

# ==========================================
# 🖥️ ส่วนแสดงผล (UI)
# ==========================================

with st.sidebar:
    st.title("🏫 ระบบวัดผล")
    user_type = st.radio("", ["👨‍🎓 นักเรียน", "👩‍🏫 ครูผู้สอน"])
    st.markdown("---")
    st.caption("Developed for Education")

# --- STUDENT VIEW ---
if user_type == "👨‍🎓 นักเรียน":
    st.markdown("<h2 style='text-align: center;'>ตรวจสอบผลการเรียนรายบุคคล</h2>", unsafe_allow_html=True)
    
    col_input1, col_input2 = st.columns([1, 2])
    with col_input1:
        selected_room = st.selectbox("เลือกห้องเรียน", list(SHEET_URLS.keys()))
    with col_input2:
        st_id = st.text_input("รหัสนักเรียน (5 หลัก)", max_chars=5)

    if st.button("🔍 ตรวจสอบคะแนน", use_container_width=True) and st_id:
        cfg, df, status = load_data(selected_room)
        
        if status == "OK":
            student = df[df['Student_ID'] == st_id]
            if not student.empty:
                row = student.iloc[0]
                # นักเรียนดูคะแนนสะสมปัจจุบัน
                score, full = calculate_score(row, cfg, mode="Pre+Mid+Post")
                threshold = 0.7 * full
                is_pass = score >= threshold
                
                # --- UI แสดงผลสวยๆ ---
                st.markdown("---")
                
                # Container การ์ดขาว
                with st.container():
                    st.markdown(f"""
                    <div class="report-card">
                        <h3 style="margin-bottom: 0;">{row['ชื่อ นามสกุล']}</h3>
                        <p style="color: gray;">รหัส: {row['Student_ID']} | ห้อง: {selected_room}</p>
                        <hr>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 3em; font-weight: bold; color: #2c3e50;">{score}</span>
                                <span style="font-size: 1.5em; color: gray;"> / {full}</span>
                                <br>คะแนนรวม (ปัดเศษ)
                            </div>
                            <div style="text-align: right;">
                                <span class="{ 'status-pass' if is_pass else 'status-fail' }">
                                    { '✅ ผ่านเกณฑ์' if is_pass else '⚠️ ยังไม่ผ่าน' }
                                </span>
                                <br>เกณฑ์ผ่าน: {int(threshold)} คะแนน
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Progress Bar แบบสี
                    percent = min(score / full, 1.0)
                    bar_color = "#27ae60" if is_pass else "#c0392b"
                    st.markdown(f"**ความคืบหน้าคะแนน:**")
                    st.progress(percent)
                    
                    # รายละเอียด
                    with st.expander("ดูรายละเอียดคะแนน"):
                        st.info("คะแนนที่แสดงเป็นคะแนนที่ปัดเศษทศนิยมแล้ว")
            else:
                st.error("❌ ไม่พบรหัสนักเรียนนี้")
        else:
            st.error(f"โหลดข้อมูลไม่ได้: {status}")

# --- TEACHER VIEW ---
elif user_type == "👩‍🏫 ครูผู้สอน":
    st.markdown("## 📊 Dashboard สำหรับครู")
    
    if st.sidebar.text_input("Password", type="password") == TEACHER_PASSWORD:
        c1, c2 = st.columns([1, 2])
        room_select = c1.selectbox("ห้องเรียน", list(SHEET_URLS.keys()))
        cycle_select = c2.selectbox("รอบรายงาน", ["รอบ 1 (Pre+Mid)", "รอบ 2 (Pre+Mid+Post)", "Final (Pre+Final)"])
        
        # Mapping Mode
        mode_map = {"รอบ 1": "Pre+Mid", "รอบ 2": "Pre+Mid+Post", "Final": "Pre+Final"}
        calc_mode = next(v for k, v in mode_map.items() if k in cycle_select)
        
        cfg, df, status = load_data(room_select)
        
        if status == "OK":
            # คำนวณทั้งห้อง
            data = []
            for _, r in df.iterrows():
                s, f = calculate_score(r, cfg, mode=calc_mode)
                # เช็คเกณฑ์จากคะแนนเต็มของช่วงนั้น (70%)
                threshold = 0.7 * f
                data.append({
                    "รหัส": r['Student_ID'],
                    "ชื่อ": r['ชื่อ นามสกุล'],
                    "คะแนน": s,
                    "เต็ม": f,
                    "ผล": "ผ่าน" if s >= threshold else "ไม่ผ่าน"
                })
            
            res_df = pd.DataFrame(data)
            
            # 1. Summary Cards
            st.markdown("### ภาพรวม")
            m1, m2, m3, m4 = st.columns(4)
            n_pass = sum(res_df['ผล'] == 'ผ่าน')
            
            # ใช้ container สร้างการ์ดตัวเลข
            def metric_card(col, title, value, sub="", color="black"):
                col.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; border:1px solid #ddd; text-align:center;">
                    <div style="color:gray; font-size:0.9em;">{title}</div>
                    <div style="font-size:2em; font-weight:bold; color:{color};">{value}</div>
                    <div style="font-size:0.8em; color:gray;">{sub}</div>
                </div>
                """, unsafe_allow_html=True)
            
            metric_card(m1, "นักเรียนทั้งหมด", len(res_df), "คน")
            metric_card(m2, "ผ่านเกณฑ์", n_pass, f"{n_pass/len(res_df)*100:.0f}%", "#27ae60")
            metric_card(m3, "ไม่ผ่านเกณฑ์", len(res_df)-n_pass, f"{(len(res_df)-n_pass)/len(res_df)*100:.0f}%", "#c0392b")
            metric_card(m4, "คะแนนเฉลี่ย", f"{res_df['คะแนน'].mean():.1f}", "คะแนน")
            
            # 2. รายชื่อ & กราฟ
            st.write("")
            c_left, c_right = st.columns([2, 1])
            
            with c_left:
                st.subheader("รายชื่อนักเรียน")
                st.dataframe(
                    res_df.style.applymap(lambda v: 'color: green; font-weight: bold;' if v=='ผ่าน' else 'color: red; font-weight: bold;' if v=='ไม่ผ่าน' else '', subset=['ผล']),
                    use_container_width=True, height=400
                )
                
            with c_right:
                st.subheader("สัดส่วน")
                fig = px.pie(res_df, names='ผล', color='ผล', color_discrete_map={'ผ่าน':'#2ecc71', 'ไม่ผ่าน':'#e74c3c'}, hole=0.5)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            
            # 3. Print Section (สวยงามเหมือน A4)
            st.markdown("---")
            st.subheader("🖨️ พิมพ์ใบรายงานผล")
            
            p_std = st.selectbox("เลือกนักเรียน", df['ชื่อ นามสกุล'])
            if p_std:
                std_row = df[df['ชื่อ นามสกุล'] == p_std].iloc[0]
                std_res = res_df[res_df['ชื่อ'] == p_std].iloc[0]
                
                # สร้างพื้นที่ HTML สำหรับ Print
                with st.container(border=True):
                    # Header
                    st.markdown(f"""
                        <div style="text-align:center; padding:20px;">
                            <h2 style="margin:0;">รายงานผลสัมฤทธิ์ทางการเรียน</h2>
                            <p style="margin:5px; color:gray;">วิชา {cfg['SubjectName']} | ภาคเรียนที่ 1/2567</p>
                        </div>
                        <div style="display:flex; justify-content:space-between; background:#f8f9fa; padding:15px; border-radius:8px;">
                            <div><b>ชื่อ-สกุล:</b> {std_row['ชื่อ นามสกุล']}</div>
                            <div><b>รหัส:</b> {std_row['Student_ID']}</div>
                            <div><b>ห้อง:</b> {room_select}</div>
                        </div>
                        <br>
                    """, unsafe_allow_html=True)
                    
                    # Table Detail
                    # หางานที่เกี่ยวข้อง
                    keywords = []
                    if "Pre" in calc_mode: keywords.append("Pre_")
                    if "Mid" in calc_mode: keywords.append("Mid_")
                    if "Post" in calc_mode: keywords.append("Post_")
                    if "Final" in calc_mode: keywords.append("Final_")
                    
                    items = []
                    for col in df.columns:
                        if any(k in str(col) for k in keywords) and "[" in str(col):
                            items.append([
                                col.split('[')[0].replace('Pre_', '').replace('Mid_', '').replace('HW.', ''), # ชื่อย่อ
                                std_row[col], # คะแนนดิบ
                                get_max_score(col) # เต็ม
                            ])
                    
                    df_items = pd.DataFrame(items, columns=["รายการประเมิน", "คะแนนดิบ", "คะแนนเต็ม"])
                    st.table(df_items)
                    
                    # Footer Score
                    status_color = "#27ae60" if std_res['ผล'] == "ผ่าน" else "#c0392b"
                    st.markdown(f"""
                        <div style="border-top:2px solid #eee; padding-top:20px; text-align:right;">
                            <span style="font-size:1.2em;">คะแนนรวม (สุทธิ): <b>{std_res['คะแนน']}</b> / {std_res['เต็ม']}</span><br>
                            <span style="font-size:1.5em; font-weight:bold; color:{status_color};">{std_res['ผล']} เกณฑ์ร้อยละ 70</span>
                        </div>
                        <br>
                        <div style="text-align:center; margin-top:30px; color:gray; font-size:0.8em;">
                            เอกสารฉบับนี้ออกโดยระบบอัตโนมัติ (ข้อมูล ณ วันที่รายงาน)
                        </div>
                    """, unsafe_allow_html=True)

        elif status == "LinkNotFound": st.error("ไม่พบลิงก์ห้องนี้")
        else: st.error(status)
