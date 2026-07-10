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

app = FastAPI(title="CreativeOps AI Engine", version="2.1")

# Cấu hình CORS để Front-end và Back-end giao tiếp không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CẤU HÌNH GOOGLE GEMINI API ---
# Hệ thống sẽ tự động lấy API Key từ biến môi trường GEMINI_API_KEY của bạn
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "THAY_API_KEY_CỦA_BẠN_VÀO_ĐÂY_NẾU_KHÔNG_DÙNG_ENV")
genai.configure(api_key=GEMINI_API_KEY)

# --- ĐỊNH NGHĨA STRUCTURAL DATA MODELS (PYDANTIC) ---
class HookModel(BaseModel):
    formula_type: str
    hook_text: str
    video_visual: str
    static_layout: str
    copy_direction: str

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

# --- ENDPOINT 1: PHÂN RÃ MA TRẬN Ý TƯỞNG (ĐÃ FIX CHUẨN CHO GEMINI ĐỜI MỚI) ---
@app.post("/api/v1/generate-matrix", response_model=CreativeMatrixResponse)
async def generate_matrix(product_description: str, target_market: str = "Vietnam"):
    system_instruction = """
    Bạn là một Giám đốc sáng tạo (Creative Director) và Growth Marketer lão luyện theo trường phái CreativeOps.
    Nhiệm vụ của bạn là phân tích bản mô tả sản phẩm thô và bẻ gãy nó thành một Ma trận Sáng tạo thực chiến (Creative Matrix).
    
    Hãy chia sản phẩm thành 3 nhóm Persona khách hàng (Audience) độc lập. Đối với MỖI nhóm Persona, bạn phải phân tích sâu sắc các khía cạnh cốt lõi sau để điền vào đúng Schema:
    - demographics: Độ tuổi, giới tính, phân khúc (Ví dụ: "18-32, All (~70% Female)").
    - description: Mô tả chi tiết hành vi, phong cách sống, gu thẩm mỹ (Ví dụ: "Thích nhập vai tình cảm, quen với webtoon, manhua...").
    - behavior: Thói quen tiêu thụ nội dung trên MXH (Ví dụ: "Thường xuyên đọc, xem hoặc chơi game liên quan đến tình cảm giả tưởng...").
    - insights: Nỗi đau thầm kín hoặc khao khát sâu thẳm (Ví dụ: "Muốn cùng character viết ra 1 fantasy của riêng mình...").
    - motivation: Động lực cốt lõi thôi thúc họ hành động (Ví dụ: "Được sống trong một mối quan hệ mà ngoài đời không có...").
    - key_message: Thông điệp chí mạng (Ví dụ: "Câu chuyện của bạn. Nhân vật của bạn.").
    - suggested_formats: Các định dạng đề xuất hiển thị bằng văn bản viết liền hoặc xuống dòng (Ví dụ: "Static chat UI mockup, Video story reveal").

    Với mỗi Persona, hãy tạo ra 2 Big Ideas. Mỗi Big Idea có 2 Small Ideas (Concepts). Mỗi Small Idea sinh ra 2 Suggested Hooks cụ thể, thực chiến có kèm Layout ảnh tĩnh và Kịch bản video 3 giây đầu.
    Mã hóa project_prefix bằng 3 chữ cái viết hoa đại diện cho sản phẩm (Ví dụ sản phẩm Imely -> IML).
    """

    prompt = f"""
    Sản phẩm / Chiến dịch cần phân tích: {product_description}
    Thị trường mục tiêu: {target_market}
    
    Yêu cầu: Điền đầy đủ dữ liệu vào tất cả các trường cấu trúc bắt buộc của JSON Schema. Không để trống trường nào.
    """

    try:
        # Sử dụng cấu hình mạnh mẽ nhất của Gemini để ép tuân thủ Pydantic Schema
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
        
        response = model.generate_content(
            [system_instruction, prompt],
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": CreativeMatrixResponse # Ép Gemini trả về chuẩn cấu trúc Pydantic
            }
        )
        
        matrix_data = json.loads(response.text)
        return matrix_data
    except Exception as e:
        print(f"❌ Lỗi Gemini rã ma trận: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi AI khởi tạo ma trận: {str(e)}")

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- ENDPOINT 2: XUẤT EXCEL CHUẨN DESIGN ĐẸP CAO CẤP (CHỮA XẤU) ---
@app.post("/api/v1/export-matrix-excel")
async def export_matrix_excel(data: CreativeMatrixResponse):
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # --- SHEET 1: TARGET AUDIENCE ---
            attributes = ["DEMOGRAPHIC", "DESCRIPTION", "BEHAVIOR", "INSIGHTS", "MOTIVATION", "KEY MESSAGE", "FORMAT (gợi ý thôi)"]
            
            # Loại bỏ cột Unnamed thừa, map trực tiếp từ Thuộc tính sang các Persona
            ta_dict = {"Thuộc Tính / Trường Dữ Liệu": attributes}
            
            for p in data.personas:
                col_name = f"{p.persona_name} ({p.persona_code})"
                ta_dict[col_name] = [
                    p.demographics,
                    p.description,
                    p.behavior,
                    p.insights,
                    p.motivation,
                    p.key_message,
                    p.suggested_formats
                ]
                
            df_ta = pd.DataFrame(ta_dict)
            df_ta.to_excel(writer, sheet_name="Target Audience", index=False)
            
            # --- SHEET 2: CREATIVE PLAN & MANAGEMENT ---
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
                                "Body Copy Direction": h.copy_direction
                            })
                            global_hook_counter += 1
                            
            df_plan = pd.DataFrame(plan_rows)
            df_plan.to_excel(writer, sheet_name="Creative Matrix Management", index=False)
            
            # --- KHU VỰC ĐÚC KHUÔN STYLE ĐẸP (OPENPYXL MAGIC) ---
            workbook = writer.book
            
            # Định nghĩa bảng màu & font chuẩn Corporate UI
            font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            font_body = Font(name="Segoe UI", size=10, bold=False, color="1E293B")
            fill_header = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid") # Màu Indigo hoàng gia
            align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
            align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            thin_border = Border(
                left=Side(style='thin', color='E2E8F0'),
                right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'),
                bottom=Side(style='thin', color='E2E8F0')
            )
            
            # Style cho Sheet 1: Target Audience
            ws1 = workbook["Target Audience"]
            ws1.row_dimensions[1].height = 28
            for col_idx in range(1, ws1.max_column + 1):
                cell = ws1.cell(row=1, column=col_idx)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = align_center
            
            for row in ws1.iter_rows(min_row=2, max_row=ws1.max_row, min_col=1, max_col=ws1.max_column):
                for cell in row:
                    cell.font = font_body
                    cell.border = thin_border
                    if cell.column == 1:
                        cell.font = Font(name="Segoe UI", size=10, bold=True, color="475569")
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    else:
                        cell.alignment = align_left
            
            # Tự chỉnh độ rộng thông minh cho Sheet 1
            ws1.column_dimensions['A'].width = 25
            for col in range(2, ws1.max_column + 1):
                col_letter = get_column_letter(col)
                ws1.column_dimensions[col_letter].width = 40 # Cột thông tin rộng rãi để đọc Insight
                
            # Style cho Sheet 2: Creative Matrix Management
            ws2 = workbook["Creative Matrix Management"]
            ws2.row_dimensions[1].height = 28
            for col_idx in range(1, ws2.max_column + 1):
                cell = ws2.cell(row=1, column=col_idx)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = align_center
                
            for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, min_col=1, max_col=ws2.max_column):
                for cell in row:
                    cell.font = font_body
                    cell.border = thin_border
                    cell.alignment = align_left
                    
            # Tự chỉnh độ rộng tự động cho Sheet 2
            for col in ws2.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws2.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45) # Giới hạn không quá rộng, không quá hẹp

        output.seek(0)
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Creative_Ops_Matrix_{data.project_prefix}.xlsx"}
        )
    except Exception as e:
        print(f"❌ Lỗi xuất Excel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi xuất file Excel: {str(e)}")

# --- ENDPOINT 3: BỘ DẬP MÃ NAMING TỰ ĐỘNG ---
@app.post("/api/v1/generate-dynamic-naming")
async def generate_dynamic_naming(payload: NamingPayload):
    idea_str = str(payload.idea_number).zfill(3)
    # Tạo mã Code chuẩn cấu trúc: IML-ROM-DR-001-ST-EN
    creative_code = f"{payload.project_prefix}-{payload.audience_code}-{payload.concept_code}-{idea_str}-{payload.format_code}-{payload.lang_code}"
    
    # Tạo tên hiển thị tường minh để nghiệm thu nội bộ công việc
    file_name_display = f"{payload.project_prefix} · {payload.audience_name} · {payload.concept_name} · Idea {idea_str} · Form: {payload.format_code} · [{payload.lang_code}]"
    
    return {"creative_code": creative_code.upper(), "file_name_display": file_name_display}

# --- ENDPOINT 4: AI PHÂN TÍCH HIỆU SUẤT DATA-DRIVEN ---
@app.post("/api/v1/analyze-performance")
async def analyze_performance(report_data_table: str):
    system_instruction = """
    Bạn là một Lead Data Analyst kiêm Performance Marketing Expert chuyên tối ưu tài nguyên Ads.
    Bạn sẽ nhận được bảng dữ liệu Markdown chứa: Mã Creative Code, Chi phí (Spend), Số click, Số đơn hàng (Conversions), CTR, CPA.
    Nhiệm vụ của bạn là bóc tách dữ liệu để phân loại: Nhóm tài nguyên nào là Winner (giữ lại, scale up), nhóm nào là Loser (tắt, đổi hook).
    
    Hãy phân tích và trả về cấu trúc JSON chuẩn có các keys sau:
    1. overall_evaluation (Đánh giá chung toàn bộ chiến dịch)
    2. top_performing_persona (Mã/Tên nhóm đối tượng chuyển đổi tốt nhất)
    3. top_performing_concept (Mã/Tên concept sáng tạo mang lại hiệu quả cao nhất)
    4. detailed_insights (Mảng các object, mỗi object gồm: asset_group, status, metric_summary, ai_recommendation)
    5. next_action_steps (Mảng danh sách các hành động cần thực thi ngay lập tức)
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content([system_instruction, f"Dữ liệu báo cáo quảng cáo thực tế:\n{report_data_table}"])
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi AI phân tích dữ liệu: {str(e)}")