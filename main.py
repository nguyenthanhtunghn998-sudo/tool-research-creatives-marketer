from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import io
import pandas as pd
import google.generativeai as genai
from fastapi.responses import StreamingResponse
import json
import re

app = FastAPI(title="CreativeOps AI Engine", version="2.2")

# Cấu hình CORS để Front-end và Back-end giao tiếp không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CẤU HÌNH GOOGLE GEMINI API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "THAY_API_KEY_CỦA_BẠN_VÀO_ĐÂY_NẾU_KHÔNG_DÙNG_ENV")
genai.configure(api_key=GEMINI_API_KEY)

# --- ĐỊNH NGHĨA STRUCTURAL DATA MODELS (PYDANTIC) ---
class HookModel(BaseModel):
    formula_type: str
    hook_text: str
    video_visual: str
    static_layout: str
    copy_direction: str
    image_prompt: str  # TRƯỜNG MỚI: Prompt tạo ảnh AI chuẩn chuyên sâu
    video_prompt: str  # TRƯỜNG MỚI: Prompt tạo video AI chuẩn chuyên sâu

class SmallIdeaModel(BaseModel):
    concept_code: str
    concept_name: str
    priority: str
    visual_direction: str
    suggested_hooks: List[HookModel]

class BigIdeaModel(BaseModel):
    idea_name: str
    small_ideas: List[SmallIdeaModel]

class PersonaModel(BaseModel):
    persona_name: str
    persona_code: str
    demographics: str
    description: str
    behavior: str
    insights: str
    motivation: str
    key_message: str
    suggested_formats: str
    big_ideas: List[BigIdeaModel]

class CreativeMatrixResponse(BaseModel):
    product_summary: str
    project_prefix: str
    personas: List[PersonaModel]

class NamingPayload(BaseModel):
    project_prefix: str
    audience_code: str
    audience_name: str
    concept_code: str
    concept_name: str
    idea_number: int
    format_code: str
    lang_code: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "CreativeOps AI Engine đã nâng cấp bản thực chiến 2.2 thành công!"}

# --- ENDPOINT 1: PHÂN RÃ MA TRẬN Ý TƯỞNG (THỰC CHIẾN & LOGIC PROMPT CHUẨN) ---
@app.post("/api/v1/generate-matrix", response_model=CreativeMatrixResponse)
async def generate_matrix(product_description: str, target_market: str = "Vietnam"):
    system_instruction = """
    Bạn là một Giám đốc sáng tạo (Creative Director) và Growth Marketer lão luyện theo trường phái CreativeOps thực chiến.
    Nhiệm vụ của bạn là bẻ gãy mô tả sản phẩm thô thành Ma trận Sáng tạo có thể mang đi thực thi, thiết kế và viết bài được ngay lập tức.
    
    BẮT BUỘC TUÂN THỦ NGUYÊN TẮC NỘI DUNG:
    1. KHÔNG VIẾT LÝ THUYẾT SUÔNG (Ví dụ thay vì viết "Ngắn gọn, tò mò", hãy viết hẳn câu caption mẫu: "Bí mật động trời phía sau giao diện chat của app này...").
    2. Hook và kịch bản phải cụ thể, mô tả rõ hành động diễn ra, text gì sẽ xuất hiện trên màn hình.
    3. Đối với 'image_prompt' và 'video_prompt': Đây là những prompt viết bằng TIẾNG ANH CHUYÊN SÂU dùng để nạp vào các AI tạo ảnh/video (như Imagen 3, Midjourney, Runway, Sora). Phải mô tả rõ bối cảnh (setting), phong cách nghệ thuật (art style), góc máy (camera angle), ánh sáng (lighting) liên quan trực tiếp đến Concept đó, KHÔNG được copy text tiếng Việt hay ghép thô sơ các trường dữ liệu khác sang.

    Hãy chia sản phẩm thành 3 nhóm Persona khách hàng độc lập. Với mỗi Persona, tạo ra 2 Big Ideas. Mỗi Big Idea có 2 Small Ideas (Concepts). Mỗi Small Idea sinh ra 2 Suggested Hooks cụ thể kèm đầy đủ prompt AI.
    Mã hóa project_prefix bằng 3 chữ cái viết hoa đại diện cho sản phẩm.

    BẮT BUỘC TRẢ VỀ THEO ĐÚNG ĐỊNH DẠNG JSON SCHEMA VÀ ĐIỀN ĐẦY ĐỦ CÁC TRƯỜNG DỮ LIỆU.
    """

    prompt = f"""
    Sản phẩm / Chiến dịch cần phân tích: {product_description}
    Thị trường mục tiêu: {target_market}
    """

    try:
        model = genai.GenerativeModel(model_name="gemini-3.5-flash")
        response = model.generate_content(
            [system_instruction, prompt],
            generation_config={
                "temperature": 0.5,
                "max_output_tokens": 8192
            }
        )
        
        text_response = response.text.strip()
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        clean_json_str = match.group(0) if match else text_response
            
        matrix_data = json.loads(clean_json_str)
        return matrix_data
    except Exception as e:
        print(f"❌ Lỗi Gemini rã ma trận: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi AI khởi tạo ma trận: {str(e)}")

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- ENDPOINT 2: XUẤT EXCEL CHUẨN DESIGN ĐẸP (ĐÃ THÊM CỘT PROMPT AI) ---
@app.post("/api/v1/export-matrix-excel")
async def export_matrix_excel(data: CreativeMatrixResponse):
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1
            attributes = ["DEMOGRAPHIC", "DESCRIPTION", "BEHAVIOR", "INSIGHTS", "MOTIVATION", "KEY MESSAGE", "FORMAT (gợi ý thôi)"]
            ta_dict = {"Thuộc Tính / Trường Dữ Liệu": attributes}
            for p in data.personas:
                col_name = f"{p.persona_name} ({p.persona_code})"
                ta_dict[col_name] = [p.demographics, p.description, p.behavior, p.insights, p.motivation, p.key_message, p.suggested_formats]
            df_ta = pd.DataFrame(ta_dict)
            df_ta.to_excel(writer, sheet_name="Target Audience", index=False)
            
            # Sheet 2 (Thêm cột Prompt AI phục vụ sản xuất thực tế)
            plan_rows = []
            global_hook_counter = 1
            for p in data.personas:
                for b_idea in p.big_ideas:
                    for s_idea in b_idea.small_ideas:
                        for h in s_idea.suggested_hooks:
                            idea_str_num = str(global_hook_counter).zfill(3)
                            creative_code = f"{data.project_prefix}-{p.persona_code}-{s_idea.concept_code}-{idea_str_num}-ST-VN"
                            
                            plan_rows.append({
                                "Creative Code": creative_code,
                                "Audience Persona": p.persona_name,
                                "Big Idea": b_idea.idea_name,
                                "Small Idea / Concept": s_idea.concept_name,
                                "Concept Code": s_idea.concept_code,
                                "Priority": s_idea.priority,
                                "Hook Formula": h.formula_type,
                                "Hook Text": h.hook_text,
                                "Visual Direction": s_idea.visual_direction,
                                "Video Visual (3s Đầu)": h.video_visual,
                                "Static Layout Composition": h.static_layout,
                                "Body Copy Direction": h.copy_direction,
                                "AI Image Prompt (Tiếng Anh)": h.image_prompt,
                                "AI Video Prompt (Tiếng Anh)": h.video_prompt
                            })
                            global_hook_counter += 1
                            
            df_plan = pd.DataFrame(plan_rows)
            df_plan.to_excel(writer, sheet_name="Creative Matrix Management", index=False)
            
            # Decorate Excel Openpyxl
            workbook = writer.book
            font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            font_body = Font(name="Segoe UI", size=10, bold=False, color="1E293B")
            fill_header = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid") 
            align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
            align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
            thin_border = Border(
                left=Side(style='thin', color='E2E8F0'), right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'), bottom=Side(style='thin', color='E2E8F0')
            )
            
            ws1 = workbook["Target Audience"]
            ws1.row_dimensions[1].height = 28
            for col_idx in range(1, ws1.max_column + 1):
                cell = ws1.cell(row=1, column=col_idx)
                cell.font = font_header; cell.fill = fill_header; cell.alignment = align_center
            
            for row in ws1.iter_rows(min_row=2, max_row=ws1.max_row, min_col=1, max_col=ws1.max_column):
                for cell in row:
                    cell.font = font_body; cell.border = thin_border
                    cell.alignment = align_center if cell.column == 1 else align_left
            ws1.column_dimensions['A'].width = 25
            for col in range(2, ws1.max_column + 1):
                ws1.column_dimensions[get_column_letter(col)].width = 40 
                
            ws2 = workbook["Creative Matrix Management"]
            ws2.row_dimensions[1].height = 28
            for col_idx in range(1, ws2.max_column + 1):
                cell = ws2.cell(row=1, column=col_idx)
                cell.font = font_header; cell.fill = fill_header; cell.alignment = align_center
                
            for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, min_col=1, max_col=ws2.max_column):
                for cell in row:
                    cell.font = font_body; cell.border = thin_border; cell.alignment = align_left
                    
            for col in ws2.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                ws2.column_dimensions[get_column_letter(col[0].column)].width = min(max(max_len + 3, 14), 45)

        output.seek(0)
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Creative_Ops_Matrix_{data.project_prefix}.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất Excel: {str(e)}")

# --- ENDPOINT 3 & 4 GIỮ NGUYÊN ---
@app.post("/api/v1/generate-dynamic-naming")
async def generate_dynamic_naming(payload: NamingPayload):
    idea_str = str(payload.idea_number).zfill(3)
    creative_code = f"{payload.project_prefix}-{payload.audience_code}-{payload.concept_code}-{idea_str}-{payload.format_code}-{payload.lang_code}"
    file_name_display = f"{payload.project_prefix} · {payload.audience_name} · {payload.concept_name} · Idea {idea_str} · Form: {payload.format_code} · [{payload.lang_code}]"
    return {"creative_code": creative_code.upper(), "file_name_display": file_name_display}

@app.post("/api/v1/analyze-performance")
async def analyze_performance(report_data_table: str):
    system_instruction = "Bạn là một Lead Data Analyst kiêm Performance Marketing Expert chuyên tối ưu tài nguyên Ads..."
    try:
        model = genai.GenerativeModel(model_name="gemini-3.5-flash")
        response = model.generate_content([system_instruction, f"Dữ liệu báo cáo quảng cáo thực tế:\n{report_data_table}"])
        text_response = response.text.strip()
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        clean_json_str = match.group(0) if match else text_response
        return json.loads(clean_json_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi AI phân tích dữ liệu: {str(e)}")
