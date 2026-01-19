"""
AI Analyzer Module - Xử lý phân tích SWOT bằng Gemini API
"""
import json
import os
import time
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


def build_system_prompt(analysis_level: str = 'enterprise') -> str:
    """
    Xây dựng System Prompt cho AI theo yêu cầu của người dùng
    
    Args:
        analysis_level: 'basic', 'standard', hoặc 'enterprise'
    """
    
    base_prompt = """# ROLE (VAI TRÒ)
Bạn là một Chuyên gia Phân tích Dữ liệu và Chiến lược Kinh doanh F&B (Data Analyst & Business Strategist) với 20 năm kinh nghiệm. Nhiệm vụ của bạn là đọc các đánh giá thô (raw reviews), phân tích cảm xúc, gom nhóm chủ đề và xây dựng mô hình SWOT CHUYÊN SÂU cấp doanh nghiệp.

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

Hãy sử dụng TẤT CẢ thông tin có sẵn để phân tích SWOT một cách toàn diện.

# LOGIC PHÂN TÍCH & XỬ LÝ (ENTERPRISE-LEVEL)
Hãy thực hiện quy trình suy luận hiệu quả và chính xác:

1. **Phân tích Cảm xúc & Khía cạnh (Sentiment + Aspect):** 
   - Xác định cảm xúc (Tích cực/Tiêu cực) VÀ khía cạnh (Giá cả, Chất lượng, Dịch vụ, Không gian, Menu...) trong một bước.
   - Sử dụng thông tin bổ sung (PRICE, RATING, MENU) để phân tích sâu hơn.

2. **Gom nhóm thông minh (Smart Clustering):**
   - Gom các đánh giá có cùng khía cạnh VÀ cảm xúc lại.
   - Tạo mô tả tổng hợp ngắn gọn nhưng đầy đủ (1-2 câu).
   - Ưu tiên các vấn đề xuất hiện nhiều lần.

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

4. **PHÂN TÍCH CHIẾN LƯỢC DOANH NGHIỆP (QUAN TRỌNG):**
   - Đánh giá MỨC ĐỘ ẢNH HƯỞNG (Impact): High/Medium/Low
   - Đánh giá MỨC ĐỘ KHẢ THI để cải thiện (Feasibility): High/Medium/Low
   - Đánh giá MỨC ĐỘ KHẨN CẤP (Urgency): High/Medium/Low
   - Đề xuất HÀNH ĐỘNG CỤ THỂ cho mỗi item
   - Xác định KPIs để đo lường kết quả"""

    enterprise_output = """
# OUTPUT FORMAT (ĐỊNH DẠNG ĐẦU RA - ENTERPRISE LEVEL)
Trả về kết quả duy nhất dưới dạng **JSON Object** (không kèm lời dẫn), với cấu trúc sau:

{
  "SWOT_Analysis": {
    "Strengths": [
      {
        "topic": "Tên chủ đề ngắn gọn",
        "description": "Mô tả chi tiết và sâu sắc về điểm mạnh này",
        "impact": "High/Medium/Low",
        "priority_score": 8.5,
        "kpi_metrics": ["KPI cụ thể 1", "KPI cụ thể 2"],
        "leverage_strategy": "Cách tận dụng điểm mạnh này để tăng trưởng"
      }
    ],
    "Weaknesses": [
      {
        "topic": "Tên chủ đề ngắn gọn",
        "description": "Mô tả chi tiết vấn đề đang gặp phải",
        "impact": "High/Medium/Low",
        "root_cause": "Nguyên nhân gốc rễ của vấn đề",
        "priority_score": 7.0,
        "improvement_cost": "High/Medium/Low",
        "mitigation_plan": "Kế hoạch khắc phục ngắn gọn với bước cụ thể"
      }
    ],
    "Opportunities": [
      {
        "topic": "Tên cơ hội ngắn gọn",
        "description": "Mô tả cơ hội từ thị trường hoặc điểm yếu đối thủ",
        "action_idea": "Gợi ý hành động cụ thể",
        "priority_score": 9.0,
        "market_size": "Large/Medium/Small",
        "time_to_capture": "Short term/Medium term/Long term",
        "required_investment": "High/Medium/Low"
      }
    ],
    "Threats": [
      {
        "topic": "Tên thách thức ngắn gọn",
        "description": "Mô tả rủi ro từ đối thủ hoặc thị trường",
        "risk_level": "High/Medium/Low",
        "probability": "High/Medium/Low",
        "severity": "High/Medium/Low",
        "contingency_plan": "Kế hoạch ứng phó nếu rủi ro xảy ra"
      }
    ]
  },
  "Key_Insights": [
    "Insight quan trọng 1 từ phân tích",
    "Insight quan trọng 2 từ phân tích",
    "Insight quan trọng 3 từ phân tích"
  ],
  "Competitive_Analysis": {
      "my_scores": {
          "quality": 8, "price": 7, "service": 6, "location": 9, "brand": 7, "innovation": 5
      },
      "competitor_scores": {
          "quality": 7, "price": 6, "service": 8, "location": 8, "brand": 9, "innovation": 6
      },
      "justification": "Giải thích ngắn gọn tại sao chấm điểm như vậy (ví dụ: Đối thủ có thương hiệu mạnh nhưng giá cao...)"
  },
  "Executive_Summary": "Một đoạn văn ngắn khoảng 100 từ tổng kết tình hình chung, bao gồm: tình trạng hiện tại, điểm nổi bật nhất, và khuyến nghị ưu tiên hàng đầu."
}

QUAN TRỌNG: 
1. Chỉ trả về JSON, không thêm bất kỳ văn bản giải thích nào khác.
2. priority_score là số từ 1-10, càng cao càng quan trọng.
3. Mỗi category phải có ít nhất 1 item nếu có dữ liệu liên quan.
4. Đảm bảo mỗi item có đầy đủ các trường như định dạng trên."""

    return base_prompt + enterprise_output




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
        import streamlit as st
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Đang gửi dữ liệu đến AI...")
            progress_bar.progress(0.3)
            
            result = _analyze_single_batch(model, reviews_data, analysis_type)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Hoàn thành phân tích!")
            time.sleep(0.5)  # Hiển thị thông báo thành công một chút
            progress_bar.empty()
            status_text.empty()
            
            return result
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            raise
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
                
                # Progress indicator chi tiết
                progress_value = (batch_num - 1) / num_batches_my_shop
                progress_text = f"🔄 MY_SHOP batch {batch_num}/{num_batches_my_shop} ({len(batch)} reviews)..."
                
                with st.spinner(progress_text):
                    try:
                        batch_result = _analyze_single_batch(model, batch, 'MY_SHOP_ONLY' if analysis_type == 'MY_SHOP_ONLY' else 'FULL')
                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý MY_SHOP batch {batch_num}: {str(e)}")
                        # Tiếp tục với batch tiếp theo thay vì dừng hoàn toàn
                        continue
                    
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
                
                # Progress indicator chi tiết
                progress_text = f"🔄 COMPETITOR batch {batch_num}/{num_batches_competitor} ({len(batch)} reviews)..."
                
                with st.spinner(progress_text):
                    try:
                        batch_result = _analyze_single_batch(model, batch, 'COMPETITOR_ONLY' if analysis_type == 'COMPETITOR_ONLY' else 'FULL')
                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý COMPETITOR batch {batch_num}: {str(e)}")
                        # Tiếp tục với batch tiếp theo thay vì dừng hoàn toàn
                        continue
                    
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
        # Gọi API Gemini với timeout và retry
        import time
        max_retries = 3
        timeout_seconds = 120  # 2 phút timeout
        
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Gọi API với timeout (sử dụng generation_config)
                # Tăng max_output_tokens để tránh JSON bị cắt cụt
                generation_config = {
                    'max_output_tokens': 16384,  # Tăng từ 8192 lên 16384 để đủ cho response dài
                    'temperature': 0.7,
                }
                
                # Thử gọi API
                start_time = time.time()
                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                elapsed_time = time.time() - start_time
                
                # Kiểm tra timeout
                if elapsed_time > timeout_seconds:
                    raise TimeoutError(f"API call mất hơn {timeout_seconds} giây")
                
                break  # Thành công, thoát khỏi retry loop
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise
        
        if response is None:
            raise Exception(f"Không thể nhận phản hồi từ API sau {max_retries} lần thử. Lỗi cuối: {last_error}")
        
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
        
        # QUAN TRỌNG: Xử lý escape sequences trong JSON string
        # Response có thể chứa \n literal (2 ký tự: backslash + n) thay vì newline thực sự
        import re
        import codecs
        
        # Kiểm tra xem có chứa escape sequences literal không
        if '\\n' in response_text or '\\t' in response_text or '\\r' in response_text:
            # Decode escape sequences: chuyển \n literal thành newline thực sự
            # Nhưng phải cẩn thận: chỉ decode trong JSON structure, không decode trong string values
            # Cách đơn giản nhất: decode toàn bộ, vì JSON cho phép newline trong string values
            try:
                # Thử decode escape sequences
                response_text = codecs.decode(response_text, 'unicode_escape')
            except Exception:
                # Nếu decode không được (có thể do có escape sequences không hợp lệ), thử thay thế thủ công
                # Chỉ thay thế các escape sequences hợp lệ trong JSON
                response_text = response_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                # Không thay thế \\" và \\\\ vì có thể là escape trong string values
        
        # Làm sạch JSON: loại bỏ ký tự control character không hợp lệ (nhưng giữ \n, \r, \t hợp lệ)
        # Chỉ loại bỏ các ký tự control không hợp lệ trong JSON
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
                except json.JSONDecodeError as e2:
                    # Nếu vẫn lỗi, thử fix các vấn đề phổ biến
                    # Fix 1: Loại bỏ trailing comma
                    response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
                    
                    # Fix 2: Xử lý JSON bị cắt cụt - đóng các brackets/braces chưa đóng
                    error_pos = getattr(e2, 'pos', None)
                    error_line = getattr(e2, 'lineno', None)
                    error_col = getattr(e2, 'colno', None)
                    
                    # Đếm số lượng {, }, [, ] để xem có thiếu không
                    open_braces = response_text.count('{')
                    close_braces = response_text.count('}')
                    open_brackets = response_text.count('[')
                    close_brackets = response_text.count(']')
                    
                    # Nếu JSON bị cắt cụt (thiếu closing brackets/braces), thử đóng chúng
                    if open_braces > close_braces or open_brackets > close_brackets:
                        fixed_text = response_text
                        
                        # Tìm vị trí cuối cùng có thể chèn closing brackets
                        # Tìm vị trí sau dấu phẩy hoặc sau giá trị cuối cùng
                        last_comma_pos = response_text.rfind(',')
                        if last_comma_pos > 0:
                            # Loại bỏ dấu phẩy cuối và đóng các cấu trúc
                            fixed_text = response_text[:last_comma_pos]
                        
                        # Đóng arrays trước
                        for _ in range(open_brackets - close_brackets):
                            fixed_text += ']'
                        
                        # Đóng objects sau
                        for _ in range(open_braces - close_braces):
                            fixed_text += '}'
                        
                        # Thử parse với text đã fix
                        try:
                            result = json.loads(fixed_text)
                        except:
                            # Nếu vẫn không được, tiếp tục với các fix khác
                            pass
                    
                    # Fix 3: Tìm JSON hợp lệ bằng cách đếm braces từ đầu (xử lý string trong JSON)
                    brace_count = 0
                    bracket_count = 0
                    last_valid_pos = len(response_text)
                    in_string = False
                    escape_next = False
                    
                    for i, char in enumerate(response_text):
                        if escape_next:
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0 and bracket_count == 0:
                                    last_valid_pos = i + 1
                                    break
                            elif char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                    
                    # Thử parse với JSON đã extract và đóng các cấu trúc còn thiếu
                    if last_valid_pos < len(response_text) or brace_count > 0 or bracket_count > 0:
                        try:
                            extract_text = response_text[:last_valid_pos] if last_valid_pos < len(response_text) else response_text
                            
                            # Đóng arrays
                            for _ in range(bracket_count):
                                extract_text += ']'
                            
                            # Đóng objects
                            for _ in range(brace_count):
                                extract_text += '}'
                            
                            result = json.loads(extract_text)
                        except json.JSONDecodeError as e3:
                            # Nếu vẫn lỗi, thử parse lại với text gốc đã fix trailing comma
                            try:
                                result = json.loads(response_text)
                            except json.JSONDecodeError:
                                raise ValueError(
                                    f"Không thể parse JSON sau nhiều lần thử. "
                                    f"Lỗi cuối: {e3}\n"
                                    f"Vị trí: line {error_line or '?'}, column {error_col or '?'}\n"
                                    f"Response (500 ký tự đầu): {response_text[:500]}\n"
                                    f"Response (500 ký tự cuối): ...{response_text[-500:]}"
                                )
                    else:
                        # Nếu không tìm được vị trí hợp lệ, thử parse lại với text gốc
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError as e3:
                            raise ValueError(
                                f"Không thể parse JSON. Lỗi: {e3}\n"
                                f"Vị trí: line {error_line or '?'}, column {error_col or '?'}\n"
                                f"Response (500 ký tự đầu): {response_text[:500]}"
                            )
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
