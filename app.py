import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ==========================================
# 🔧 ส่วนตั้งค่าระบบ (USER CONFIGURATION)
# ==========================================

# 1. วางลิงก์ Config ที่ได้จาก Google Sheets ตรงนี้
CONFIG_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=0&single=true&output=csv"

# 2. วางลิงก์คะแนนของแต่ละห้องที่นี่ (เพิ่มห้องได้เรื่อยๆ ตามรูปแบบ)
SHEET_URLS = {
    "213": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=338894171&single=true&output=csv",
    "214": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=1135646679&single=true&output=csv",
    "407": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=2076773668&single=true&output=csv",
    "503-504, 515-516": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=1914767177&single=true&output=csv",
    "505-512": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=411570775&single=true&output=csv",
}

# รหัสผ่านสำหรับครู
TEACHER_PASSWORD = "1234" 

# ==========================================
# 🚀 ส่วนการทำงานระบบ (SYSTEM LOGIC)
# ==========================================

st.set_page_config(page_title="ระบบติดตามผลการเรียน", page_icon="🏫", layout="wide")

# ฟังก์ชันโหลดข้อมูล
@st.cache_data(ttl=300)
def load_data(room_id):
    try:
        # โหลด Config
        config_df = pd.read_csv(CONFIG_URL)
        config_df['SheetName'] = config_df['SheetName'].astype(str)
        
        # ตรวจสอบว่ามีลิงก์ห้องนี้ไหม
        if room_id not in SHEET_URLS:
            return None, None, "LinkNotFound"

        # โหลดคะแนน
        url = SHEET_URLS[room_id]
        scores_df = pd.read_csv(url)
        scores_df['ห้อง'] = scores_df['ห้อง'].astype(str)
        scores_df['Student_ID'] = scores_df['Email'].apply(lambda x: str(x).split('@')[0])
        
        # ดึง Config ของห้องนี้
        room_config = config_df[config_df['SheetName'] == room_id]
        if room_config.empty:
            return None, None, "ConfigNotFound"
            
        return room_config.iloc[0], scores_df, "OK"
        
    except Exception as e:
        return None, None, str(e)

def get_max_score(header):
    match = re.search(r'\[(\d+)\]', header)
    return int(match.group(1)) if match else 0

def calculate_score(student_row, config, mode="Pre+Mid"):
    total_score = 0
    total_full = 0
    
    # 1. ส่วน Pre
    if "Pre" in mode:
        cols = [c for c in student_row.index if str(c).startswith('Pre_')]
        raw = student_row[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Pre']
        score = (raw / max_raw * scale) if max_raw > 0 else 0
        total_score += score
        total_full += scale

    # 2. ส่วน Mid
    if "Mid" in mode:
        cols = [c for c in student_row.index if str(c).startswith('Mid_')]
        raw = student_row[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Mid']
        # ถ้าไม่มีคะแนนเต็มระบุในชื่อ ให้ใช้คะแนนดิบเลย (หรือเทียบสัดส่วนถ้ามี Max)
        score = (raw / max_raw * scale) if max_raw > 0 else raw 
        total_score += score
        total_full += scale

    # 3. ส่วน Post
    if "Post" in mode:
        cols = [c for c in student_row.index if str(c).startswith('Post_')]
        raw = student_row[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Post']
        score = (raw / max_raw * scale) if max_raw > 0 else 0
        total_score += score
        total_full += scale

    # 4. ส่วน Final (เผื่อไว้)
    if "Final" in mode:
        cols = [c for c in student_row.index if str(c).startswith('Final_')]
        raw = student_row[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Final']
        score = (raw / max_raw * scale) if max_raw > 0 else 0
        total_score += score
        total_full += scale
        
    return total_score, total_full

# ==========================================
# 🖥️ ส่วนแสดงผลหน้าเว็บ (UI)
# ==========================================

# Sidebar Menu
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
    st.title("ระบบวัดผลการเรียน")
    user_type = st.radio("เลือกกลุ่มผู้ใช้งาน", ["👨‍🎓 นักเรียน", "👩‍🏫 ครูผู้สอน"])
    st.markdown("---")

# --- โหมดนักเรียน ---
if user_type == "👨‍🎓 นักเรียน":
    st.header("🎓 ตรวจสอบผลการเรียนรายบุคคล")
    
    # เลือกห้องก่อน
    selected_room = st.selectbox("เลือกห้องเรียน", list(SHEET_URLS.keys()))
    
    # กรอกรหัส
    st_id = st.text_input("รหัสนักเรียน (5 หลัก)", max_chars=5)
    
    if st.button("ดูผลคะแนน") and st_id:
        cfg, df, status = load_data(selected_room)
        
        if status == "OK":
            student = df[df['Student_ID'] == st_id]
            if not student.empty:
                row = student.iloc[0]
                # นักเรียนดูคะแนนสะสมปัจจุบัน (Pre+Mid+Post)
                score, full = calculate_score(row, cfg, mode="Pre+Mid+Post") 
                threshold = 0.7 * full
                
                st.success(f"พบคะแนนของ: **{row['ชื่อ นามสกุล']}**")
                
                # แสดง Card คะแนน
                col1, col2 = st.columns(2)
                col1.metric("คะแนนสะสม", f"{score:.2f}", f"เต็ม {full}")
                
                if score >= threshold:
                    st.balloons()
                    st.info(f"✅ **ผ่านเกณฑ์** (ทำได้ {score:.2f} จากเกณฑ์ {threshold:.2f})")
                else:
                    st.error(f"⚠️ **ต้องปรับปรุง** (ทำได้ {score:.2f} จากเกณฑ์ {threshold:.2f})")
            else:
                st.warning("❌ ไม่พบรหัสนักเรียนนี้ในห้องที่เลือก")
        else:
            st.error(f"ไม่สามารถโหลดข้อมูลห้อง {selected_room} ได้ ({status})")

# --- โหมดครู ---
elif user_type == "👩‍🏫 ครูผู้สอน":
    st.header("📊 Dashboard สำหรับครู")
    
    pwd = st.sidebar.text_input("รหัสผ่าน", type="password")
    
    if pwd == TEACHER_PASSWORD:
        # 1. แถบเครื่องมือครู
        c1, c2 = st.columns([1, 2])
        with c1:
            room_select = st.selectbox("📂 เลือกห้องเรียนที่ต้องการดู", list(SHEET_URLS.keys()))
        with c2:
            cycle_select = st.selectbox("⏱️ เลือกรอบการรายงาน", 
                                      ["รอบที่ 1 (Pre + Mid)", 
                                       "รอบที่ 2 (Pre + Mid + Post)",
                                       "รอบพิเศษ (Pre + Final)"])
        
        # แปลงตัวเลือกเป็น Mode การคำนวณ
        calc_mode = "Pre+Mid"
        if "รอบที่ 2" in cycle_select: calc_mode = "Pre+Mid+Post"
        if "รอบพิเศษ" in cycle_select: calc_mode = "Pre+Final"

        st.markdown("---")
        
        # โหลดข้อมูล
        cfg, df, status = load_data(room_select)
        
        if status == "OK":
            # คำนวณคะแนนทั้งห้อง
            report_list = []
            for idx, row in df.iterrows():
                sc, full = calculate_score(row, cfg, mode=calc_mode)
                is_pass = sc >= (0.7 * full)
                report_list.append({
                    "รหัส": row['Student_ID'],
                    "ชื่อ-สกุล": row['ชื่อ นามสกุล'],
                    "คะแนนที่ได้": sc,
                    "คะแนนเต็ม": full,
                    "ผลการประเมิน": "ผ่าน" if is_pass else "ไม่ผ่าน"
                })
            
            report_df = pd.DataFrame(report_list)
            
            # --- ส่วน Dashboard ---
            # 1. สรุปตัวเลข
            t1, t2, t3, t4 = st.columns(4)
            n_pass = len(report_df[report_df['ผลการประเมิน']=='ผ่าน'])
            n_fail = len(report_df) - n_pass
            
            t1.metric("นักเรียนทั้งหมด", f"{len(report_df)} คน")
            t2.metric("ผ่านเกณฑ์", f"{n_pass} คน", f"{n_pass/len(report_df)*100:.1f}%")
            t3.metric("ไม่ผ่านเกณฑ์", f"{n_fail} คน", f"{n_fail/len(report_df)*100:.1f}%", delta_color="inverse")
            t4.metric("คะแนนเฉลี่ย", f"{report_df['คะแนนที่ได้'].mean():.2f}")
            
            # 2. กราฟ
            fig = px.pie(report_df, names='ผลการประเมิน', title=f'สัดส่วนผลการเรียน ห้อง {room_select}', 
                         color='ผลการประเมิน', color_discrete_map={'ผ่าน':'#66bb6a', 'ไม่ผ่าน':'#ef5350'},
                         hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            # 3. ตารางรายชื่อ
            st.subheader("📋 รายชื่อและสถานะ")
            
            # ตัวกรอง
            filter_opt = st.radio("แสดงข้อมูล:", ["ทั้งหมด", "เฉพาะคนไม่ผ่าน", "เฉพาะคนผ่าน"], horizontal=True)
            display_df = report_df
            if filter_opt == "เฉพาะคนไม่ผ่าน": display_df = report_df[report_df['ผลการประเมิน']=='ไม่ผ่าน']
            elif filter_opt == "เฉพาะคนผ่าน": display_df = report_df[report_df['ผลการประเมิน']=='ผ่าน']
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # 4. ส่วนพิมพ์รายงาน
            st.markdown("---")
            st.subheader("🖨️ พิมพ์รายงานรายบุคคล")
            st.info("💡 เลือกชื่อนักเรียนด้านล่าง แล้วกด Ctrl+P เพื่อพิมพ์")
            
            print_student = st.selectbox("ค้นหาชื่อนักเรียนเพื่อพิมพ์", df['ชื่อ นามสกุล'])
            
            if print_student:
                # ดึงข้อมูลดิบ
                std_row = df[df['ชื่อ นามสกุล'] == print_student].iloc[0]
                std_res = report_df[report_df['ชื่อ-สกุล'] == print_student].iloc[0]
                
                # สร้างหน้ากระดาษจำลอง
                with st.container(border=True):
                    st.markdown(f"""
                        <div style='text-align: center'>
                            <h2>รายงานผลสัมฤทธิ์ทางการเรียน</h2>
                            <p><b>รายวิชา:</b> {cfg['SubjectName']} | <b>ห้อง:</b> {room_select} | <b>รอบ:</b> {cycle_select}</p>
                        </div>
                        <hr>
                        <div style='font-size: 18px; margin-bottom: 20px;'>
                            <b>ชื่อ-สกุล:</b> {std_row['ชื่อ นามสกุล']} <br>
                            <b>รหัสนักเรียน:</b> {std_row['Student_ID']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # ตารางคะแนนละเอียด
                    # หาคอลัมน์ที่เกี่ยวข้องกับรอบนี้
                    keywords = []
                    if "Pre" in calc_mode: keywords.append("Pre_")
                    if "Mid" in calc_mode: keywords.append("Mid_")
                    if "Post" in calc_mode: keywords.append("Post_")
                    if "Final" in calc_mode: keywords.append("Final_")
                    
                    detail_data = []
                    for col in df.columns:
                        if any(k in str(col) for k in keywords) and "[" in str(col):
                            raw_val = std_row[col]
                            max_val = get_max_score(col)
                            # ตัดชื่อให้สวยงาม
                            task_name = col.split('[')[0].replace('Pre_', '').replace('Mid_', '').replace('Post_', '').replace('Final_', '').replace('HW.', '')
                            detail_data.append([task_name, raw_val, max_val])
                            
                    st.table(pd.DataFrame(detail_data, columns=["รายการประเมิน", "คะแนนที่ได้", "คะแนนเต็ม"]))
                    
                    # สรุปผล
                    st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;'>
                            <h4>สรุปผลการประเมิน</h4>
                            <p>คะแนนรวม: <b>{std_res['คะแนนที่ได้']:.2f}</b> / {std_res['คะแนนเต็ม']}</p>
                            <p>สถานะ: <b style='color: {"green" if std_res["ผลการประเมิน"]=="ผ่าน" else "red"}'>{std_res['ผลการประเมิน']} เกณฑ์ร้อยละ 70</b></p>
                        </div>
                    """, unsafe_allow_html=True)

        elif status == "ConfigNotFound":
            st.error(f"ไม่พบข้อมูลการตั้งค่า (Config) ของห้อง {room_select} ในไฟล์ Config.csv")
        else:
            st.error(f"เกิดข้อผิดพลาด: {status}")
            
    else:
        st.warning("กรุณากรอกรหัสผ่านครูเพื่อเข้าถึงข้อมูล")
