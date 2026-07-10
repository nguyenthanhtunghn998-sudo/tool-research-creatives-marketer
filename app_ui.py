import streamlit as st
import requests
import pandas as pd
import io

st.set_page_config(page_title="CreativeOps AI Workspace", page_icon="🎯", layout="wide")

# --- CSS CAO CẤP CHUẨN SAAS ENGINE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    button[data-baseweb="tab"] { font-size: 15px !important; font-weight: 600 !important; color: #64748B !important; padding: 12px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #4F46E5 !important; border-bottom-color: #4F46E5 !important; }
    .stTextArea textarea, .stTextInput input { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; padding: 12px !important; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 12px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important; width: 100% !important; }
    .summary-box { background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border-left: 5px solid #22C55E; padding: 18px; border-radius: 12px; margin-bottom: 20px; }
    .card-info { background: #EFF6FF; border-radius: 12px; padding: 14px; border-left: 4px solid #3B82F6; height:100%; margin-bottom: 10px; }
    .card-warning { background: #FFFBEB; border-radius: 12px; padding: 14px; border-left: 4px solid #F59E0B; height:100%; margin-bottom: 10px; }
    .card-success { background: #F5F3FF; border-radius: 12px; padding: 14px; border-left: 4px solid #8B5CF6; height:100%; margin-bottom: 10px; }
    .perf-card { background-color: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

BACKEND_URL = "https://tool-research-creatives-marketer.onrender.com/api/v1"

st.markdown("""
    <div style='text-align: center; padding: 15px 0;'>
        <h1 style='color: #1E293B; font-size: 32px; font-weight: 700; margin-bottom: 5px;'>🎯 CreativeOps AI Workspace v2.1</h1>
        <p style='color: #64748B; font-size: 15px;'>Định dạng Prompt Gemini Ảnh Độc Quyền & Đồng Bộ Hóa Ma Trận Excel Gốc</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚀 Ý TƯỞNG & LOCAL AI PROMPT", "🏷️ BỘ DẬP MÃ FILE ĐỘNG", "📈 ĐO LƯỜNG & TỐI ƯU PERFORMANCE"])

# --- TAB 1: MA TRẬN VÀ AI PROMPT ---
with tab1:
    st.markdown("<h4 style='color: #334155;'>Bước 1: Cấu hình chiến dịch sản phẩm thực chiến</h4>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        product_desc = st.text_area("Mô tả sản phẩm / Dự án (Bản thô từ Marketer):", placeholder="Ví dụ: Tính năng, điểm ưu việt, bài toán khách hàng...", height=120)
    with col2:
        target_market = st.text_input("Thị trường mục tiêu:", value="Vietnam")
        st.write("")
        run_btn = st.button("Kích Hoạt Bộ Não AI Gemini ✨", type="primary")

    if run_btn and product_desc:
        with st.spinner("🧠 Hệ thống đang phân tích sâu và phân rã ma trận sản xuất..."):
            try:
                res = requests.post(f"{BACKEND_URL}/generate-matrix", params={"product_description": product_desc, "target_market": target_market})
                if res.status_code == 200:
                    st.session_state["matrix_data"] = res.json()
                    st.toast('Khởi tạo ma trận thành công!', icon='🎉')
                else: st.error(f"Lỗi: {res.text}")
            except Exception as e: st.error(f"Lỗi kết nối máy chủ: {str(e)}")

    st.divider()

    if "matrix_data" in st.session_state:
        data = st.session_state["matrix_data"]
        st.markdown(f"<div class='summary-box'><b>📊 TÓM TẮT THẾ MẠNH SẢN PHẨM:</b><br>{data['product_summary']}</div>", unsafe_allow_html=True)
        st.markdown(f"### 🏷️ Mã Dự Án Đề Xuất: <span style='color: #4F46E5;'>{data['project_prefix']}</span>", unsafe_allow_html=True)
        
        # HIỂN THỊ ĐẦY ĐỦ CÁC TRƯỜNG THÔNG TIN THEO FILE EXCEL GỐC
        for p_idx, persona in enumerate(data["personas"]):
            with st.expander(f"👤 {p_idx+1}. NHÓM KHÁCH HÀNG: {persona['persona_name'].upper()} ({persona['persona_code']})", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"<div class='card-info'><strong>📋 DEMOGRAPHIC:</strong><br>{persona.get('demographics', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-info'><strong>📝 DESCRIPTION:</strong><br>{persona.get('description', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-info'><strong>⚡ BEHAVIOR:</strong><br>{persona.get('behavior', 'N/A')}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='card-warning'><strong>💡 INSIGHTS:</strong><br>\"{persona.get('insights', 'N/A')}\"</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-warning'><strong>🎯 MOTIVATION:</strong><br>{persona.get('motivation', 'N/A')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='card-success'><strong>🔥 KEY MESSAGE:</strong><br>\"{persona.get('key_message', 'N/A')}\"</div>", unsafe_allow_html=True)
                
                st.write("")
                for b_idx, b_idea in enumerate(persona.get("big_ideas", [])):
                    st.markdown(f"<div style='background-color:#F1F5F9; padding: 8px 12px; border-radius: 6px; font-weight:600; color:#334155; margin: 10px 0;'>💡 Big Idea: {b_idea['idea_name']}</div>", unsafe_allow_html=True)
                    
                    for s_idx, s_idea in enumerate(b_idea.get("small_ideas", [])):
                        st.markdown(f"🔹 **Concept:** `{s_idea['concept_code']}` - **{s_idea['concept_name']}** — *Ưu tiên: {s_idea['priority']}*")
                        st.caption(f"🎨 Visual Direction: {s_idea['visual_direction']}")
                        
                        for h_idx, h in enumerate(s_idea.get("suggested_hooks", [])):
                            col_content, col_prompt = st.columns([3, 2])
                            with col_content:
                                st.markdown(f"**Hook ({h['formula_type']}):** *\"{h['hook_text']}\"*")
                                st.markdown(f"🎥 **Kịch bản Video (3s đầu):** {h['video_visual']}")
                                st.markdown(f"🖼️ **Layout Bố cục Ảnh (Static):** {h['static_layout']}")
                                st.markdown(f"✍️ **Hướng captions (Body Copy):** {h['copy_direction']}")
                            with col_prompt:
                                st.markdown("🤖 **Gemini Image Prompt Format Optimized:**")
                                
                                # CẤU TRÚC PROMPT MỚI THEO FORMAT FORMAT YÊU CẦU CỦA USER
                                sd_prompt = f"A cinematic TikTok-style commercial ad for {data.get('project_prefix', 'Brand')}\n\nStyle:\n- Fast-paced commercial aesthetic\n- High production value advertising\n- Blue-green accents\n- Style: {s_idea['visual_direction']}\n\nScene:\n- {h['static_layout']}\n- High detail composition, studio lighting\n\nLarge text:\n\"{h['hook_text']}\"\n\nSecond text:\n\"Concept: {s_idea['concept_name']}\"\n\nSubtext:\n\"{h['copy_direction']}\"\n\nAspect ratio 1080x1080"
                                video_prompt = f"Commercial dynamic video scene, high production value. Visual action for first 3 seconds: {h['video_visual']}, smooth motion, stunning colors, studio grade."
                                
                                t_sd, t_vid = st.tabs(["🖼️ Image Prompt", "🎥 Video Prompt"])
                                with t_sd: st.text_area("Gemini / Imagen 3 Prompt Structure:", value=sd_prompt, height=220, key=f"sd_{p_idx}_{b_idx}_{s_idx}_{h_idx}")
                                with t_vid: st.text_area("Kling AI / Runway / Luma:", value=video_prompt, height=120, key=f"vid_{p_idx}_{b_idx}_{s_idx}_{h_idx}")
                            st.markdown("<hr style='margin:10px 0; border-top: 1px dashed #CBD5E1;'>", unsafe_allow_html=True)

        st.markdown("<h4 style='color: #334155;'>Bước 2: Đóng gói và xuất bản tài nguyên</h4>", unsafe_allow_html=True)
        if st.button("📥 XUẤT FILE EXCEL PHÂN TẬP THEO FILE GỐC (.XLSX)", type="primary"):
            with st.spinner("Đang biên dịch cấu trúc nhiều Sheet..."):
                res_excel = requests.post(f"{BACKEND_URL}/export-matrix-excel", json=st.session_state["matrix_data"])
                if res_excel.status_code == 200:
                    st.download_button("BẤM ĐỂ TẢI XUỐNG FILE EXCEL", data=res_excel.content, file_name=f"Creative_Matrix_{data.get('project_prefix', 'OUTPUT')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- TAB 2 & 3 GIỮ NGUYÊN HOẠT ĐỘNG ---
with tab2:
    st.header("🏷️ Công Cụ Định Danh & Tạo Mã Naming Tự Động")
    with st.form("naming_form_v2"):
        ca, cb, cc = st.columns(3)
        with ca:
            p_pref = st.text_input("Mã Dự Án (Project Prefix):", value="FIN")
            a_code = st.text_input("Mã Đối Tượng (Audience Code):", value="YPI")
            a_name = st.text_input("Tên Đối Tượng đầy đủ:", value="Young Passive Investors")
        with cb:
            c_code = st.text_input("Mã Concept (Concept Code):", value="EA")
            c_name = st.text_input("Tên Concept đầy đủ:", value="Easy Accumulation")
            i_num = st.number_input("Số thứ tự Ý tưởng (Idea #):", min_value=1, value=1)
        with cc:
            f_code = st.selectbox("Định dạng sản xuất (Format):", ["VD", "ST", "CR", "CP"])
            l_code = st.selectbox("Ngôn ngữ (Language):", ["VN", "EN", "TH"])
        
        if st.form_submit_button("🔨 DẬP MÃ FILE NGAY", type="primary"):
            payload = {"project_prefix": p_pref, "audience_code": a_code, "audience_name": a_name, "concept_code": c_code, "concept_name": c_name, "idea_number": i_num, "format_code": f_code, "lang_code": l_code}
            res_n = requests.post(f"{BACKEND_URL}/generate-dynamic-naming", json=payload)
            if res_n.status_code == 200:
                out = res_n.json()
                st.info(f"**MÃ FILE CHUẨN SẢN XUẤT:** `{out['creative_code']}`")
                st.success(f"**Tên hiển thị nội bộ:** {out['file_name_display']}")

with tab3:
    st.header("📈 Phân Tích Hiệu Suất Quảng Cáo")
    uploaded_file = st.file_uploader("Kéo thả file số liệu tại đây:", type=["csv", "xlsx"])
    if uploaded_file is not None:
        st.success("File uploaded successfully! Đã cấu trúc sẵn sàng để đọc data-driven.")
