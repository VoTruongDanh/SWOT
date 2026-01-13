"""
AI Analyzer Module - Xử lý phân tích SWOT bằng Gemini API
"""
import json
import os
import pandas as pd
import google.generativeai as genai
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load API Key từ Streamlit Secrets (khi deploy) hoặc .env (khi chạy local)
# Thử đọc từ .env trước (cho local development)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Nếu không có trong .env, thử đọc từ Streamlit Secrets (khi deploy lên Streamlit Cloud)
if not GEMINI_API_KEY:
    try:
        import streamlit as st
        # Thử đọc từ Streamlit Secrets
        if hasattr(st, 'secrets') and hasattr(st.secrets, 'get'):
            GEMINI_API_KEY = st.secrets.get('GEMINI_API_KEY', None)
    except:
        # Nếu không có streamlit hoặc không có secrets, giữ None
        pass

# Cấu hình Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def build_system_prompt() -> str:
    """
    Xây dựng System Prompt cho AI theo yêu cầu của người dùng
    """
    return """# ROLE (VAI TRÒ)
Bạn là một Chuyên gia Phân tích Dữ liệu và Chiến lược Kinh doanh F&B (Data Analyst & Business Strategist) với 20 năm kinh nghiệm. Nhiệm vụ của bạn là đọc các đánh giá thô (raw reviews), phân tích cảm xúc, gom nhóm chủ đề và xây dựng mô hình SWOT.

# INPUT DATA (DỮ LIỆU ĐẦU VÀO)
Bạn sẽ nhận được một danh sách các đánh giá từ khách hàng với đầy đủ thông tin. Mỗi đánh giá có thể bao gồm:
- "SOURCE: MY_SHOP": Đánh giá về quán của tôi.
- "SOURCE: COMPETITOR": Đánh giá về đối thủ cạnh tranh.
- "CONTENT": Nội dung đánh giá (bắt buộc)
- "PRICE": Giá cả (nếu có)
- "RATING": Điểm đánh giá/số sao (nếu có)
- "MENU_ITEM": Tên món/sản phẩm (nếu có)
- "DATE": Ngày đánh giá (nếu có)
- "USER": Tên người đánh giá (nếu có)

Hãy sử dụng TẤT CẢ thông tin có sẵn để phân tích SWOT một cách toàn diện. Ví dụ:
- Nếu có thông tin về giá, hãy phân tích về giá cả và so sánh.
- Nếu có rating, hãy xem xét mối tương quan giữa rating và nội dung đánh giá.
- Nếu có menu item, hãy phân tích theo từng loại sản phẩm.

# LOGIC PHÂN TÍCH & XỬ LÝ (QUAN TRỌNG - TỐI ƯU HÓA)
Hãy thực hiện quy trình suy luận hiệu quả và chính xác:

1. **Phân tích Cảm xúc & Khía cạnh (Sentiment + Aspect):** 
   - Xác định cảm xúc (Tích cực/Tiêu cực) VÀ khía cạnh (Giá cả, Chất lượng, Dịch vụ, Không gian, Menu...) trong một bước.
   - Sử dụng thông tin bổ sung (PRICE, RATING, MENU) để phân tích sâu hơn.

2. **Gom nhóm thông minh (Smart Clustering):**
   - Gom các đánh giá có cùng khía cạnh VÀ cảm xúc lại.
   - Tạo mô tả tổng hợp ngắn gọn nhưng đầy đủ (1-2 câu).
   - Ưu tiên các vấn đề xuất hiện nhiều lần.
   - Nếu có thông tin về giá/rating/menu, hãy phân tích theo từng nhóm.

3. **Mapping SWOT (Quy tắc xếp loại):**
   
   **Khi phân tích đánh giá về MY_SHOP (quán của tôi):**
   - MY_SHOP + Tích cực -> STRENGTHS (Điểm mạnh của tôi).
   - MY_SHOP + Tiêu cực -> WEAKNESSES (Điểm yếu của tôi).
   - Từ đánh giá về MY_SHOP, cũng có thể suy ra:
     * OPPORTUNITIES: Cơ hội cải thiện dựa trên điểm yếu của tôi hoặc thị trường.
     * THREATS: Thách thức tiềm ẩn từ thị trường hoặc xu hướng.
   
   **Khi phân tích đánh giá về COMPETITOR (đối thủ):**
   - COMPETITOR + Tích cực -> THREATS (Thách thức - đối thủ làm tốt hơn).
   - COMPETITOR + Tiêu cực -> OPPORTUNITIES (Cơ hội - khai thác điểm yếu đối thủ).
   - Từ đánh giá về COMPETITOR, cũng có thể suy ra:
     * STRENGTHS: Điểm mạnh của đối thủ (để học hỏi hoặc cạnh tranh).
     * WEAKNESSES: Điểm yếu của đối thủ (để khai thác).
   
   **QUAN TRỌNG:** Khi phân tích một nguồn (MY_SHOP hoặc COMPETITOR), hãy phân tích đầy đủ 4 phần SWOT dựa trên context và insights từ dữ liệu đó.

4. **Phân tích sâu (Deep Analysis):**
   - Nếu có thông tin về giá: Phân tích về giá cả, so sánh giá trị.
   - Nếu có rating: Phân tích mối tương quan giữa rating và nội dung.
   - Nếu có menu: Phân tích theo từng loại sản phẩm/món.
   - Đưa ra insights cụ thể, không chỉ mô tả chung chung.

# OUTPUT FORMAT (ĐỊNH DẠNG ĐẦU RA)
Trả về kết quả duy nhất dưới dạng **JSON Object** (không kèm lời dẫn), với cấu trúc sau:

{
  "SWOT_Analysis": {
    "Strengths": [
      {"topic": "Tên chủ đề ngắn", "description": "Mô tả chi tiết và sâu sắc về điểm mạnh này dựa trên dữ liệu", "impact": "Mức độ ảnh hưởng (High/Medium/Low)"}
    ],
    "Weaknesses": [
      {"topic": "Tên chủ đề ngắn", "description": "Mô tả chi tiết vấn đề đang gặp phải", "root_cause": "Dự đoán nguyên nhân gốc rễ", "impact": "High/Medium/Low"}
    ],
    "Opportunities": [
      {"topic": "Tên chủ đề ngắn", "description": "Mô tả cơ hội từ thị trường hoặc điểm yếu đối thủ", "action_idea": "Gợi ý hành động ngắn gọn"}
    ],
    "Threats": [
      {"topic": "Tên chủ đề ngắn", "description": "Mô tả rủi ro từ đối thủ", "risk_level": "High/Medium/Low"}
    ]
  },
  "Executive_Summary": "Một đoạn văn ngắn khoảng 50 từ tổng kết tình hình chung."
}

QUAN TRỌNG: Chỉ trả về JSON, không thêm bất kỳ văn bản giải thích nào khác."""


def format_reviews_for_prompt(reviews_data: List[Dict[str, Any]], compact: bool = True) -> str:
    """
    Chuyển đổi dữ liệu reviews thành định dạng văn bản để gửi cho AI
    Tối ưu hóa format để giảm token và tăng hiệu quả
    
    Args:
        reviews_data: List các dict với keys: 'review', 'source', và các keys khác
        compact: Nếu True, sử dụng format compact để tiết kiệm token
    
    Returns:
        Chuỗi văn bản đã format
    """
    if compact:
        formatted_text = "\n# REVIEWS DATA (Format: SOURCE|CONTENT|PRICE|RATING|MENU|DATE)\n\n"
        
        for review in reviews_data:
            review_text = review.get('review', '').strip()
            if not review_text:
                continue
            
            source = review.get('source', 'UNKNOWN')
            parts = [source, review_text]
            
            # Thêm các thông tin bổ sung nếu có (chỉ giá trị không rỗng)
            for key in ['price', 'rating', 'menu', 'date']:
                if key in review and pd.notna(review.get(key)):
                    val = str(review.get(key)).strip()
                    if val and val.lower() != 'nan':
                        parts.append(val)
                    else:
                        parts.append('')
                else:
                    parts.append('')
            
            # Format: SOURCE|CONTENT|PRICE|RATING|MENU|DATE
            formatted_text += "|".join(parts) + "\n"
    else:
        # Format chi tiết (dùng khi cần)
        formatted_text = "\n# DANH SÁCH ĐÁNH GIÁ VÀ THÔNG TIN CHI TIẾT\n\n"
        
        for idx, review in enumerate(reviews_data, 1):
            source = review.get('source', 'UNKNOWN')
            review_text = review.get('review', '').strip()
            
            if review_text:
                formatted_text += f"#{idx} [{source}]: {review_text}"
                
                # Thêm thông tin bổ sung ngắn gọn
                extras = []
                for key, label in [('price', 'Giá'), ('rating', 'Điểm'), ('menu', 'Món'), ('date', 'Ngày')]:
                    if key in review and pd.notna(review.get(key)):
                        val = str(review.get(key)).strip()
                        if val and val.lower() != 'nan':
                            extras.append(f"{label}:{val}")
                
                if extras:
                    formatted_text += f" ({', '.join(extras)})"
                formatted_text += "\n"
    
    return formatted_text


def analyze_swot_with_gemini(reviews_data: List[Dict[str, Any]], batch_size: int = 500, 
                             analysis_type: str = 'FULL') -> Dict[str, Any]:
    """
    Gửi dữ liệu reviews đến Gemini API và nhận kết quả phân tích SWOT
    Hỗ trợ xử lý batch cho dữ liệu lớn
    
    Args:
        reviews_data: List các dict với keys: 'review', 'source'
        batch_size: Số lượng reviews tối đa mỗi batch (mặc định 500)
        analysis_type: 'FULL' (phân tích đầy đủ), 'MY_SHOP_ONLY' (chỉ Strengths/Weaknesses), 
                       'COMPETITOR_ONLY' (chỉ Opportunities/Threats)
    
    Returns:
        Dict chứa kết quả SWOT analysis
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY chưa được cấu hình. Vui lòng thêm vào file .env hoặc Streamlit Secrets")
    
    # Khởi tạo model Gemini 2.5 Flash
    # Thử các model name theo thứ tự ưu tiên
    model_names = ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash']
    model = None
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            break
        except Exception as e:
            continue
    
    if model is None:
        # Fallback cuối cùng
        model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Xử lý batch nếu dữ liệu quá lớn
    total_reviews = len(reviews_data)
    
    if total_reviews <= batch_size:
        # Xử lý một lần nếu dữ liệu nhỏ
        return _analyze_single_batch(model, reviews_data, analysis_type)
    else:
        # Xử lý nhiều batch và tổng hợp kết quả (TỐI ƯU HÓA)
        import streamlit as st
        
        st.info(f"📊 Dữ liệu lớn ({total_reviews:,} reviews). Đang phân tích theo batch tối ưu...")
        
        all_results = {
            "SWOT_Analysis": {
                "Strengths": [],
                "Weaknesses": [],
                "Opportunities": [],
                "Threats": []
            },
            "Executive_Summary": ""
        }
        
        # Tách MY_SHOP và COMPETITOR để xử lý hiệu quả hơn
        my_shop_data = [r for r in reviews_data if r.get('source') == 'MY_SHOP']
        competitor_data = [r for r in reviews_data if r.get('source') == 'COMPETITOR']
        
        all_summaries = []
        
        # Xử lý MY_SHOP (chỉ tạo Strengths và Weaknesses)
        if my_shop_data:
            num_batches_my_shop = (len(my_shop_data) + batch_size - 1) // batch_size
            for i in range(0, len(my_shop_data), batch_size):
                batch = my_shop_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                with st.spinner(f"🔄 MY_SHOP batch {batch_num}/{num_batches_my_shop} ({len(batch)} reviews)..."):
                    batch_result = _analyze_single_batch(model, batch, 'MY_SHOP_ONLY' if analysis_type == 'MY_SHOP_ONLY' else 'FULL')
                    
                    all_results["SWOT_Analysis"]["Strengths"].extend(
                        batch_result.get("SWOT_Analysis", {}).get("Strengths", [])
                    )
                    all_results["SWOT_Analysis"]["Weaknesses"].extend(
                        batch_result.get("SWOT_Analysis", {}).get("Weaknesses", [])
                    )
                    all_summaries.append(batch_result.get("Executive_Summary", ""))
        
        # Xử lý COMPETITOR (chỉ tạo Opportunities và Threats)
        if competitor_data:
            num_batches_competitor = (len(competitor_data) + batch_size - 1) // batch_size
            for i in range(0, len(competitor_data), batch_size):
                batch = competitor_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                with st.spinner(f"🔄 COMPETITOR batch {batch_num}/{num_batches_competitor} ({len(batch)} reviews)..."):
                    batch_result = _analyze_single_batch(model, batch, 'COMPETITOR_ONLY' if analysis_type == 'COMPETITOR_ONLY' else 'FULL')
                    
                    all_results["SWOT_Analysis"]["Opportunities"].extend(
                        batch_result.get("SWOT_Analysis", {}).get("Opportunities", [])
                    )
                    all_results["SWOT_Analysis"]["Threats"].extend(
                        batch_result.get("SWOT_Analysis", {}).get("Threats", [])
                    )
                    all_summaries.append(batch_result.get("Executive_Summary", ""))
        
        # Tổng hợp Executive Summary (tối ưu - chỉ lấy 5 summary đầu)
        if all_summaries:
            if len(all_summaries) > 1:
                # Tổng hợp bằng cách lấy summary đầu tiên và thêm thông tin từ các summary khác
                main_summary = all_summaries[0]
                if len(all_summaries) > 1:
                    additional_info = " | ".join(all_summaries[1:5])  # Lấy tối đa 4 summary còn lại
                    all_results["Executive_Summary"] = f"{main_summary} {additional_info}"[:500]  # Giới hạn độ dài
                else:
                    all_results["Executive_Summary"] = main_summary
            else:
                all_results["Executive_Summary"] = all_summaries[0]
        
        # Loại bỏ duplicate và merge items tương tự (tối ưu)
        for category in ["Strengths", "Weaknesses", "Opportunities", "Threats"]:
            seen_topics = {}
            for item in all_results["SWOT_Analysis"][category]:
                topic = item.get("topic", "").lower().strip()
                if topic:
                    if topic not in seen_topics:
                        seen_topics[topic] = item
                    else:
                        # Merge nếu trùng - ưu tiên impact cao hơn
                        existing = seen_topics[topic]
                        existing_impact = existing.get("impact", "Low") or existing.get("risk_level", "Low")
                        new_impact = item.get("impact", "Low") or item.get("risk_level", "Low")
                        impact_order = {"High": 3, "Medium": 2, "Low": 1}
                        if impact_order.get(new_impact, 1) > impact_order.get(existing_impact, 1):
                            seen_topics[topic] = item
            
            all_results["SWOT_Analysis"][category] = list(seen_topics.values())
        
        return all_results


def _analyze_single_batch(model, reviews_data: List[Dict[str, Any]], analysis_type: str = 'FULL') -> Dict[str, Any]:
    """
    Phân tích một batch reviews với tối ưu hóa
    
    Args:
        model: Gemini model instance
        reviews_data: List các dict với keys: 'review', 'source', và các keys khác
        analysis_type: 'FULL' (phân tích đầy đủ), 'MY_SHOP_ONLY' (chỉ Strengths/Weaknesses), 
                       'COMPETITOR_ONLY' (chỉ Opportunities/Threats)
    
    Returns:
        Dict chứa kết quả SWOT analysis
    """
    # Xây dựng prompt đầy đủ
    system_prompt = build_system_prompt()
    
    # Sử dụng format compact để tiết kiệm token
    reviews_text = format_reviews_for_prompt(reviews_data, compact=True)
    
    # Thống kê nhanh để AI hiểu context
    my_shop_count = sum(1 for r in reviews_data if r.get('source') == 'MY_SHOP')
    competitor_count = sum(1 for r in reviews_data if r.get('source') == 'COMPETITOR')
    
    # Tạo summary ngắn gọn
    summary = f"\n# THỐNG KÊ NHANH\n"
    summary += f"- Tổng số reviews: {len(reviews_data)}\n"
    summary += f"- MY_SHOP: {my_shop_count} reviews\n"
    summary += f"- COMPETITOR: {competitor_count} reviews\n"
    
    # Hướng dẫn phân tích theo context
    if my_shop_count > 0 and competitor_count == 0:
        # Chỉ có MY_SHOP reviews - phân tích SWOT của mình
        summary += f"\n**CONTEXT QUAN TRỌNG:** Đây là đánh giá về QUÁN CỦA TÔI. Hãy phân tích đầy đủ SWOT của mình:\n"
        summary += f"- **Strengths:** Từ đánh giá tích cực về quán của tôi\n"
        summary += f"- **Weaknesses:** Từ đánh giá tiêu cực về quán của tôi\n"
        summary += f"- **Opportunities:** Cơ hội cải thiện, mở rộng, hoặc thị trường dựa trên insights từ dữ liệu (ví dụ: nếu có nhiều phàn nàn về giá, đó là cơ hội tối ưu giá)\n"
        summary += f"- **Threats:** Thách thức tiềm ẩn, xu hướng, hoặc rủi ro từ thị trường (ví dụ: nếu khách hàng yêu cầu tính năng mới, đó là threat nếu không đáp ứng)\n"
        summary += f"**LƯU Ý:** Phải có ít nhất một số items trong mỗi phần SWOT, không được để trống hoàn toàn.\n"
    elif competitor_count > 0 and my_shop_count == 0:
        # Chỉ có COMPETITOR reviews - phân tích SWOT của đối thủ
        summary += f"\n**CONTEXT QUAN TRỌNG:** Đây là đánh giá về ĐỐI THỦ CẠNH TRANH. Hãy phân tích đầy đủ SWOT của đối thủ:\n"
        summary += f"- **Strengths:** Điểm mạnh của đối thủ (từ đánh giá tích cực về đối thủ)\n"
        summary += f"- **Weaknesses:** Điểm yếu của đối thủ (từ đánh giá tiêu cực về đối thủ)\n"
        summary += f"- **Opportunities:** Cơ hội cho tôi (khai thác điểm yếu đối thủ, thị trường)\n"
        summary += f"- **Threats:** Thách thức cho tôi (đối thủ làm tốt, cạnh tranh)\n"
        summary += f"**LƯU Ý:** Phải có ít nhất một số items trong mỗi phần SWOT, không được để trống hoàn toàn.\n"
    else:
        # Có cả 2 loại - phân tích tổng hợp
        summary += f"\n**CONTEXT:** Có cả đánh giá về quán của tôi và đối thủ. Phân tích SWOT tổng hợp:\n"
        summary += f"- **Strengths:** Từ đánh giá tích cực về quán của tôi\n"
        summary += f"- **Weaknesses:** Từ đánh giá tiêu cực về quán của tôi\n"
        summary += f"- **Opportunities:** Từ đánh giá tiêu cực về đối thủ + cơ hội thị trường\n"
        summary += f"- **Threats:** Từ đánh giá tích cực về đối thủ + thách thức cạnh tranh\n"
    
    # Kiểm tra có thông tin bổ sung không
    has_price = any('price' in r and pd.notna(r.get('price')) for r in reviews_data)
    has_rating = any('rating' in r and pd.notna(r.get('rating')) for r in reviews_data)
    has_menu = any('menu' in r and pd.notna(r.get('menu')) for r in reviews_data)
    
    if has_price or has_rating or has_menu:
        summary += f"- Thông tin bổ sung: "
        extras = []
        if has_price:
            extras.append("Giá cả")
        if has_rating:
            extras.append("Điểm đánh giá")
        if has_menu:
            extras.append("Menu/Sản phẩm")
        summary += ", ".join(extras) + "\n"
    
    full_prompt = f"""{system_prompt}

{summary}

{reviews_text}

**YÊU CẦU:**
1. Phân tích nhanh và chính xác
2. Gom nhóm các đánh giá tương tự
3. Trả về JSON đúng định dạng
4. Không lặp lại thông tin
5. Ưu tiên các insights quan trọng nhất
6. Tuân thủ hướng dẫn phân tích theo loại ở trên"""
    
    try:
        # Gọi API Gemini
        response = model.generate_content(full_prompt)
        
        # Lấy text response
        response_text = response.text.strip()
        
        # Loại bỏ markdown code blocks nếu có
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Bỏ "```json"
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Bỏ "```"
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Bỏ "```" ở cuối
        
        response_text = response_text.strip()
        
        # Làm sạch JSON: loại bỏ ký tự control character không hợp lệ
        import re
        # Thay thế các ký tự control character (ngoại trừ \n, \r, \t) bằng khoảng trắng
        response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', ' ', response_text)
        
        # Thử parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as json_error:
            # Nếu lỗi, thử sửa một số vấn đề phổ biến
            # Tìm JSON object trong response (có thể có text thêm)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
                # Thử lại với JSON đã extract
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    # Nếu vẫn lỗi, thử fix các vấn đề phổ biến
                    # Fix: escape các ký tự đặc biệt trong string
                    response_text = response_text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    # Fix: loại bỏ trailing comma
                    response_text = re.sub(r',\s*}', '}', response_text)
                    response_text = re.sub(r',\s*]', ']', response_text)
                    # Thử parse lại
                    result = json.loads(response_text)
            else:
                raise ValueError(f"Không tìm thấy JSON trong response. Lỗi: {json_error}\nResponse: {response_text[:500]}")
        
        return result
        
    except json.JSONDecodeError as e:
        # Lưu response để debug
        error_msg = f"Lỗi parse JSON từ AI response: {e}\n"
        error_msg += f"Vị trí lỗi: line {e.lineno}, column {e.colno}\n"
        error_msg += f"Response text (500 ký tự đầu): {response_text[:500]}\n"
        if len(response_text) > 500:
            error_msg += f"Response text (500 ký tự cuối): ...{response_text[-500:]}"
        raise ValueError(error_msg)
    except Exception as e:
        error_str = str(e)
        
        # Xử lý các lỗi phổ biến với thông báo thân thiện
        if "Insufficient Balance" in error_str or "402" in error_str:
            raise Exception(
                "❌ **Lỗi: Tài khoản Gemini không đủ số dư**\n\n"
                "Vui lòng:\n"
                "1. Kiểm tra số dư tài khoản tại: https://makersuite.google.com/app/apikey\n"
                "2. Nạp thêm tiền vào tài khoản Gemini\n"
                "3. Hoặc sử dụng API key khác có đủ số dư\n\n"
                f"Chi tiết lỗi: {error_str}"
            )
        elif "401" in error_str or "Invalid API key" in error_str or "Unauthorized" in error_str:
            raise Exception(
                "❌ **Lỗi: API Key không hợp lệ**\n\n"
                "Vui lòng:\n"
                "1. Kiểm tra lại API key trong file .env hoặc Streamlit Secrets\n"
                "2. Đảm bảo API key đúng format\n"
                "3. Lấy API key mới tại: https://makersuite.google.com/app/apikey\n\n"
                f"Chi tiết lỗi: {error_str}"
            )
        elif "429" in error_str or "rate limit" in error_str.lower():
            raise Exception(
                "❌ **Lỗi: Vượt quá giới hạn rate limit**\n\n"
                "Vui lòng:\n"
                "1. Đợi một chút rồi thử lại\n"
                "2. Giảm số lượng reviews trong mỗi lần phân tích\n"
                "3. Hoặc nâng cấp gói API của Gemini\n\n"
                f"Chi tiết lỗi: {error_str}"
            )
        else:
            raise Exception(f"Lỗi khi gọi Gemini API: {error_str}")


def validate_swot_result(result: Dict[str, Any]) -> bool:
    """
    Kiểm tra tính hợp lệ của kết quả SWOT
    
    Args:
        result: Dict chứa kết quả SWOT
    
    Returns:
        True nếu hợp lệ, False nếu không
    """
    if not isinstance(result, dict):
        return False
    
    if "SWOT_Analysis" not in result:
        return False
    
    swot = result.get("SWOT_Analysis", {})
    required_keys = ["Strengths", "Weaknesses", "Opportunities", "Threats"]
    
    for key in required_keys:
        if key not in swot:
            return False
        if not isinstance(swot[key], list):
            return False
    
    return True
