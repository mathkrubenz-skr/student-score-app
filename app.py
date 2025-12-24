import streamlit as st
import pandas as pd
import re
import plotly.express as px

# -------------------------------------------------------------------
# ส่วนที่คุณต้องแก้ไข: เอาลิงก์จาก Google Sheets มาวางแทนที่ตรงนี้
# -------------------------------------------------------------------

# 1. วางลิงก์ของแท็บ Scores_213 ในเครื่องหมายคำพูดด้านล่าง
SHEET_URL_213 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=338894171&single=true&output=csv" 

# 2. วางลิงก์ของแท็บ Config ในเครื่องหมายคำพูดด้านล่าง
CONFIG_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcVvVYZJXwfVOjEbb-wgg0tB5AYKNOJb6soJaP1oJSKnWxSNYrI4FxwYgqJKStaSALsv6FvePLlbE1/pub?gid=0&single=true&output=csv"

# -------------------------------------------------------------------

st.set_page_config(page_title="ระบบประมวลผลคะแนน", layout="wide", page_icon="🏫")

@st.cache_data(ttl=600) # อัปเดตข้อมูลทุก 10 นาที
def load_data():
    try:
        config_df = pd.read_csv(CONFIG_URL)
        config_df['SheetName'] = config_df['SheetName'].astype(str)
        
        scores_df = pd.read_csv(SHEET_URL_213)
        scores_df['ห้อง'] = scores_df['ห้อง'].astype(str)
        scores_df['Student_ID'] = scores_df['Email'].apply(lambda x: str(x).split('@')[0])
        
        return config_df, scores_df
    except Exception as e:
        return None, None

def get_max_score(header):
    match = re.search(r'\[(\d+)\]', header)
    return int(match.group(1)) if match else 0

def calculate_student_score(student, config, score_columns):
    total_weighted = 0
    total_scale = 0
    
    # Pre
    if 'Pre' in score_columns:
        cols = [c for c in student.index if str(c).startswith('Pre_')]
        raw = student[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Pre']
        weighted = (raw / max_raw * scale) if max_raw > 0 else 0
        total_weighted += weighted
        total_scale += scale
        
    # Mid
    if 'Mid' in score_columns:
        cols = [c for c in student.index if str(c).startswith('Mid_')]
        raw = student[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Mid']
        weighted = (raw / max_raw * scale) if max_raw > 0 else raw 
        total_weighted += weighted
        total_scale += scale

    # Post
    if 'Post' in score_columns:
        cols = [c for c in student.index if str(c).startswith('Post_')]
        raw = student[cols].fillna(0).sum()
        max_raw = sum([get_max_score(c) for c in cols])
        scale = config['Scale_Post']
        weighted = (raw / max_raw * scale) if max_raw > 0 else 0
        total_weighted += weighted
        total_scale += scale
        
    return total_weighted, total_scale

# --- Main App ---
df_config, df_scores = load_data()

if df_config is not None and df_scores is not None:
    with st.sidebar:
        st.title("เมนูใช้งาน")
        mode = st.radio("เลือกผู้ใช้งาน", ["👨‍🎓 นักเรียน", "👩‍🏫 ครูผู้สอน"])
    
    if mode == "👨‍🎓 นักเรียน":
        st.title("🎓 ตรวจสอบผลคะแนนรายบุคคล")
        student_id = st.text_input("กรอกรหัสนักเรียน (5 หลัก)", max_chars=5)
        if st.button("ตรวจสอบ") and student_id:
            student_data = df_scores[df_scores['Student_ID'] == student_id]
            if not student_data.empty:
                student = student_data.iloc[0]
                room_config = df_config[df_config['SheetName'] == str(student['ห้อง'])]
                if not room_config.empty:
                    cfg = room_config.iloc[0]
                    score, full = calculate_student_score(student, cfg, ['Pre', 'Mid', 'Post'])
                    threshold = 0.7 * full
                    st.markdown(f"### ผลการเรียน: {student['ชื่อ นามสกุล']}")
                    if score >= threshold:
                        st.success(f"🎉 **ผ่านเกณฑ์** ({score:.2f}/{full})")
                    else:
                        st.error(f"⚠️ **ไม่ผ่านเกณฑ์** ({score:.2f}/{full})")
                else:
                    st.warning("ไม่พบ Config ห้องเรียน")
            else:
                st.warning("ไม่พบรหัสนักเรียน")

    elif mode == "👩‍🏫 ครูผู้สอน":
        st.title("📊 ระบบบริหารจัดการและรายงานผล")
        pwd = st.sidebar.text_input("รหัสผ่านครู", type="password")
        if pwd == "1234":
            st.sidebar.markdown("---")
            report_cycle = st.sidebar.selectbox("เลือกรอบการรายงาน", ["รอบที่ 1 (Pre + Mid)", "รอบที่ 2 (Pre + Mid + Post)"])
            target_cols = ['Pre', 'Mid'] if "รอบที่ 1" in report_cycle else ['Pre', 'Mid', 'Post']
            
            room_id = "213" 
            room_config = df_config[df_config['SheetName'] == room_id].iloc[0]
            
            report_data = []
            for _, student in df_scores[df_scores['ห้อง']==room_id].iterrows():
                score, full = calculate_student_score(student, room_config, target_cols)
                is_pass = score >= (0.7 * full)
                report_data.append({"รหัส": student['Student_ID'], "ชื่อ-สกุล": student['ชื่อ นามสกุล'], "คะแนนรวม": score, "คะแนนเต็ม": full, "สถานะ": "ผ่าน" if is_pass else "ไม่ผ่าน"})
            
            df_report = pd.DataFrame(report_data)
            col1, col2, col3 = st.columns(3)
            pass_std = len(df_report[df_report['สถานะ']=="ผ่าน"])
            col1.metric("นักเรียนทั้งหมด", f"{len(df_report)} คน")
            col2.metric("ผ่านเกณฑ์", f"{pass_std} คน")
            col3.metric("ไม่ผ่านเกณฑ์", f"{len(df_report)-pass_std} คน", delta_color="inverse")
            
            st.plotly_chart(px.pie(df_report, names='สถานะ', title=f'สัดส่วนผลการประเมิน', color='สถานะ', color_discrete_map={'ผ่าน':'#66bb6a', 'ไม่ผ่าน':'#ef5350'}), use_container_width=True)
            
            st.subheader("📋 รายชื่อนักเรียน")
            st.dataframe(df_report, use_container_width=True)
            
            st.subheader("🖨️ พิมพ์รายงานรายบุคคล")
            selected_student_name = st.selectbox("เลือกนักเรียน", df_report['ชื่อ-สกุล'])
            if selected_student_name:
                student_row = df_scores[df_scores['ชื่อ นามสกุล'] == selected_student_name].iloc[0]
                std_stats = df_report[df_report['ชื่อ-สกุล'] == selected_student_name].iloc[0]
                with st.container(border=True):
                    st.markdown(f"<div style='text-align: center;'><h2>รายงานผลสัมฤทธิ์</h2><h3>{room_config['SubjectName']}</h3></div><hr><div><b>ชื่อ:</b> {student_row['ชื่อ นามสกุล']} ({student_row['Student_ID']})</div><br>", unsafe_allow_html=True)
                    relevant_headers = [c for c in df_scores.columns if any(x in str(c) for x in target_cols) and '[' in str(c)]
                    detail_data = [[h.split('[')[0].strip(), student_row[h], get_max_score(h)] for h in relevant_headers]
                    st.table(pd.DataFrame(detail_data, columns=["งาน", "คะแนน", "เต็ม"]))
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px;'><b>สรุป: {std_stats['คะแนนรวม']:.2f}/{std_stats['คะแนนเต็ม']} ({std_stats['สถานะ']})</b></div>", unsafe_allow_html=True)
        else:
            st.error("รหัสผ่านไม่ถูกต้อง")

else:
    st.error("ไม่สามารถโหลดข้อมูลได้ กรุณาตรวจสอบลิงก์ CSV ในโค้ด")
