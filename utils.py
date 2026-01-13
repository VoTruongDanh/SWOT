"""
Utility Functions - Xử lý dữ liệu và visualization
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Tuple
import streamlit as st


def load_and_clean_data(uploaded_file, file_name: str = None) -> pd.DataFrame:
    """
    Đọc và làm sạch dữ liệu từ file Excel/CSV
    Tự động phát hiện các cột cần thiết thông minh
    
    Args:
        uploaded_file: File object từ Streamlit uploader
        file_name: Tên file (optional, sẽ lấy từ uploaded_file.name nếu không có)
    
    Returns:
        DataFrame đã được làm sạch
    """
    # Lấy tên file nếu chưa có
    if file_name is None:
        file_name = getattr(uploaded_file, 'name', '')
    try:
        # Đọc file dựa trên extension
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Thử nhiều encoding phổ biến
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        
        if file_extension == 'csv':
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                raise ValueError("Không thể đọc file CSV với các encoding phổ biến")
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError(f"Định dạng file không được hỗ trợ: {file_extension}")
        
        # Làm sạch dữ liệu
        # Loại bỏ dòng trống
        df = df.dropna(how='all')
        
        if len(df) == 0:
            raise ValueError("File không chứa dữ liệu")
        
        # Lưu tên cột gốc để hiển thị (trước khi normalize)
        original_columns = df.columns.tolist()
        column_mapping = {col.strip().lower(): col for col in original_columns}
        
        # Chuẩn hóa tên cột (chuyển về lowercase, bỏ khoảng trắng)
        df.columns = df.columns.str.strip().str.lower()
        
        # Tìm cột chứa review và source
        review_cols = []  # Có thể có nhiều cột chứa review
        source_col = None
        
        # Bước 1: Tìm TẤT CẢ các cột có thể chứa review bằng từ khóa (mở rộng)
        possible_review_names = [
            # Tiếng Anh
            'review', 'reviews', 'comment', 'comments', 'content', 'text', 'feedback',
            'comment_text', 'review_text', 'review_content', 'comment_content',
            'description', 'desc', 'note', 'notes', 'remark', 'remarks',
            'opinion', 'opinions', 'thought', 'thoughts', 'experience', 'experiences',
            'rating_text', 'rating_comment', 'user_comment', 'customer_comment',
            'review_detail', 'comment_detail', 'detail', 'details',
            'message', 'messages', 'input', 'response', 'responses',
            # Tiếng Việt
            'đánh giá', 'đánh giá khách hàng', 'nhận xét', 'nội dung', 'mô tả',
            'bình luận', 'phản hồi', 'ý kiến', 'cảm nhận', 'trải nghiệm',
            'chi tiết', 'ghi chú', 'lời nhận xét', 'lời đánh giá',
            # Từ khóa chung
            'text', 'txt', 'content', 'data', 'info', 'information'
        ]
        
        for col in df.columns:
            col_lower = col.lower().strip()
            # Kiểm tra chính xác hoặc chứa từ khóa
            if any(name in col_lower or col_lower == name for name in possible_review_names):
                review_cols.append(col)
        
        # Bước 2: Nếu không tìm thấy bằng từ khóa, phân tích tất cả cột text
        if not review_cols:
            text_columns = []
            text_scores = {}
            
            for col in df.columns:
                if df[col].dtype == 'object':  # Chỉ xét cột text
                    # Tính điểm dựa trên nhiều yếu tố
                    col_lower = col.lower()
                    score = 0
                    
                    # Độ dài trung bình của text
                    avg_length = df[col].astype(str).str.len().mean()
                    if avg_length > 20:  # Text dài hơn 20 ký tự
                        score += avg_length / 10
                    
                    # Số từ trung bình
                    word_count = df[col].astype(str).str.split().str.len().mean()
                    if word_count > 3:  # Có nhiều hơn 3 từ
                        score += word_count * 2
                    
                    # Độ đa dạng của nội dung (không phải giá trị lặp lại)
                    unique_ratio = df[col].nunique() / len(df)
                    if unique_ratio > 0.5:  # Hơn 50% giá trị là unique
                        score += unique_ratio * 100
                    
                    # Không phải cột ID, code, số
                    if not any(keyword in col_lower for keyword in ['id', 'code', 'number', 'num', 'no', 'stt', 'index']):
                        score += 50
                    
                    if score > 30:  # Ngưỡng tối thiểu
                        text_columns.append(col)
                        text_scores[col] = score
            
            # Sắp xếp theo điểm và lấy các cột tốt nhất
            if text_columns:
                text_columns.sort(key=lambda x: text_scores[x], reverse=True)
                # Lấy tối đa 3 cột text tốt nhất
                review_cols = text_columns[:3]
        
        # Bước 3: Xác định cột review chính
        if review_cols:
            # Nếu có nhiều cột, ưu tiên cột có tên rõ ràng nhất
            review_col = review_cols[0]
            if len(review_cols) > 1:
                # Tìm cột có tên rõ ràng nhất
                for col in review_cols:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['review', 'comment', 'feedback', 'đánh giá', 'nhận xét']):
                        review_col = col
                        break
        else:
            review_col = None
        
        # Bước 3: Tìm cột source bằng từ khóa (CHỈ các từ khóa rõ ràng, không nhầm lẫn)
        # Loại trừ các cột có thể nhầm lẫn: "Link Source", "review_text", "address", v.v.
        excluded_keywords = ['link', 'url', 'review', 'text', 'address', 'name', 'description', 'content']
        
        possible_source_names = [
            'source', 'nguồn', 'shop_type', 'store_type', 'competitor', 'đối thủ'
        ]
        
        for col in df.columns:
            col_lower = col.lower().strip()
            
            # Bỏ qua nếu cột có từ khóa bị loại trừ (trừ khi là "source" chính xác)
            if any(excluded in col_lower for excluded in excluded_keywords) and col_lower != 'source':
                continue
            
            # Chỉ chấp nhận nếu tên cột khớp chính xác
            if col_lower == 'source' or col_lower == 'nguồn':
                source_col = col
                break
            # Hoặc các từ khóa rõ ràng khác
            elif col_lower in ['shop_type', 'store_type']:
                # Kiểm tra giá trị trong cột có phải là MY_SHOP/COMPETITOR không
                sample_vals = df[col].astype(str).str.upper().str.strip().unique()[:5]
                if any(val in ['MY_SHOP', 'COMPETITOR', 'MY SHOP', 'CỦA MÌNH', 'ĐỐI THỦ'] for val in sample_vals):
                    source_col = col
                    break
        
        # Bước 4: Nếu không tìm thấy source, thử phân tích giá trị trong các cột
        # QUAN TRỌNG: Loại trừ các cột có thể nhầm lẫn (review, text, link, address, name)
        if source_col is None:
            # Loại trừ các cột không phải source
            excluded_keywords_in_col = ['review', 'text', 'desc', 'content', 'comment', 
                                       'address', 'name', 'link', 'url', 'item', 'menu', 
                                       'price', 'rating', 'date', 'user', 'customer']
            
            for col in df.columns:
                col_lower = col.lower()
                
                # Bỏ qua nếu cột có từ khóa bị loại trừ
                if any(excluded in col_lower for excluded in excluded_keywords_in_col):
                    continue
                
                # Bỏ qua cột review đã chọn
                if col == review_col:
                    continue
                
                if df[col].dtype == 'object':
                    unique_vals = df[col].astype(str).str.upper().str.strip().unique()[:10]
                    # CHỈ chấp nhận nếu có giá trị CHÍNH XÁC là MY_SHOP hoặc COMPETITOR
                    exact_source_values = ['MY_SHOP', 'COMPETITOR', 'MY SHOP', 'CỦA MÌNH', 'ĐỐI THỦ', 'COMPETITORS']
                    matching_vals = [val for val in unique_vals if val in exact_source_values]
                    
                    # Phải có ít nhất 1 giá trị khớp và không phải tất cả giá trị đều giống nhau (trừ khi chỉ có 1 giá trị)
                    if matching_vals and (len(unique_vals) == 1 or len(set(unique_vals)) > 1):
                        source_col = col
                        break
        
        # Bước 5: Nếu vẫn không tìm thấy review, báo lỗi chi tiết
        if review_col is None:
            error_msg = f"Không tìm thấy cột chứa nội dung đánh giá.\n\n"
            error_msg += f"Các cột trong file: {', '.join(original_columns)}\n\n"
            error_msg += "Vui lòng đảm bảo file có cột chứa nội dung đánh giá (ví dụ: Review, Đánh giá, Comment, Content...)"
            raise ValueError(error_msg)
        
        # Bước 6: Nếu không có source, thử phát hiện thông minh
        if source_col is None:
            detected_source = None
            detection_method = None
            
            # Phương pháp 1: Phát hiện từ tên file (mở rộng từ khóa)
            file_name_lower = (file_name or '').lower()
            
            # Từ khóa đối thủ (mở rộng)
            competitor_keywords = [
                'competitor', 'đối thủ', 'rival', 'competitors',
                # Thương hiệu cà phê
                'starbucks', 'phuc long', 'phuclong', 'katinat', 'highlands', 'highland',
                'trung nguyen', 'trungnguyen', 'the coffee house', 'coffee house',
                'cong ca phe', 'congcaphe', 'passio', 'gong cha', 'gongcha',
                # Nền tảng
                'shopee', 'lazada', 'grab', 'now', 'baemin', 'gojek', 'go food',
                # Từ khóa khác
                'other', 'others', 'competition', 'market'
            ]
            
            # Từ khóa quán mình
            my_shop_keywords = [
                'my_shop', 'myshop', 'của mình', 'cua minh', 'my store', 'mystore',
                'our shop', 'ourshop', 'our store', 'ourstore', 'my_', 'my-',
                'own', 'self', 'internal', 'nội bộ', 'noi bo'
            ]
            
            if any(keyword in file_name_lower for keyword in competitor_keywords):
                detected_source = 'COMPETITOR'
                detection_method = f"tên file '{file_name}'"
            elif any(keyword in file_name_lower for keyword in my_shop_keywords):
                detected_source = 'MY_SHOP'
                detection_method = f"tên file '{file_name}'"
            
            # Phương pháp 2: Phân tích nội dung trong các cột text (nếu chưa phát hiện)
            if not detected_source and len(df) > 0:
                # Tìm các cột text có thể chứa thông tin về brand/shop
                for col in df.columns:
                    if col != review_col and df[col].dtype == 'object':
                        # Lấy mẫu giá trị để phân tích
                        sample_values = df[col].astype(str).str.lower().str.strip().dropna().unique()[:20]
                        
                        # Kiểm tra xem có chứa tên thương hiệu đối thủ không
                        competitor_brands_in_data = [
                            'starbucks', 'phuc long', 'highlands', 'katinat', 
                            'trung nguyen', 'coffee house', 'cong ca phe'
                        ]
                        
                        for val in sample_values:
                            if any(brand in val for brand in competitor_brands_in_data):
                                detected_source = 'COMPETITOR'
                                detection_method = f"nội dung cột '{column_mapping.get(col, col)}'"
                                break
                        
                        if detected_source:
                            break
            
            # Áp dụng kết quả phát hiện
            if detected_source:
                st.info(f"ℹ️ Phát hiện nguồn từ {detection_method}: **{detected_source}**")
                df['source'] = detected_source
                source_col = 'source'
            else:
                # Phân tích tên file để xác định shop/brand cụ thể
                shop_name = None
                file_name_lower = (file_name or '').lower()
                
                # Tìm tên shop từ tên file
                shop_keywords = {
                    'starbucks': 'STARBUCKS',
                    'phuc long': 'PHUC_LONG',
                    'phuclong': 'PHUC_LONG',
                    'highlands': 'HIGHLANDS',
                    'highland': 'HIGHLANDS',
                    'katinat': 'KATINAT',
                    'trung nguyen': 'TRUNG_NGUYEN',
                    'trungnguyen': 'TRUNG_NGUYEN',
                    'coffee house': 'COFFEE_HOUSE',
                    'cong ca phe': 'CONG_CA_PHE',
                    'congcaphe': 'CONG_CA_PHE',
                    'passio': 'PASSIO',
                    'gong cha': 'GONG_CHA',
                    'gongcha': 'GONG_CHA'
                }
                
                for keyword, shop in shop_keywords.items():
                    if keyword in file_name_lower:
                        shop_name = shop
                        break
                
                if shop_name:
                    st.info(f"ℹ️ Phát hiện shop từ tên file '{file_name}': **{shop_name}** (phân loại là COMPETITOR)")
                    df['source'] = 'COMPETITOR'
                    source_col = 'source'
                else:
                    # Nếu không phát hiện được shop cụ thể, hỏi người dùng hoặc mặc định COMPETITOR
                    st.warning(f"⚠️ Không tìm thấy cột phân loại nguồn (Source) và không phát hiện shop từ tên file.")
                    st.info(f"💡 File '{file_name}' sẽ được phân loại là **COMPETITOR** (đối thủ). Nếu đây là dữ liệu về quán của bạn, vui lòng đổi tên file có chứa 'my_shop' hoặc thêm cột Source vào file.")
                    # Mặc định là COMPETITOR thay vì MY_SHOP
                    df['source'] = 'COMPETITOR'
                    source_col = 'source'
        
        # Bước 7: Kết hợp nhiều cột review nếu có
        if review_cols and len(review_cols) > 1:
            # Kết hợp các cột review lại thành một
            review_parts = []
            for col in review_cols:
                if col != review_col:  # Bỏ qua cột chính đã chọn
                    review_parts.append(df[col].astype(str))
            
            if review_parts:
                # Kết hợp với cột chính
                combined_review = df[review_col].astype(str)
                for part in review_parts:
                    # Chỉ thêm phần không trống và không trùng với cột chính
                    part_clean = part.replace('nan', '').str.strip()
                    combined_review = combined_review + ' ' + part_clean
                    combined_review = combined_review.str.strip()
                
                df[review_col] = combined_review
                st.info(f"ℹ️ Đã kết hợp {len(review_cols)} cột đánh giá: {', '.join([column_mapping.get(c, c) for c in review_cols])}")
        
        # Bước 7: Tìm các cột bổ sung (giá, menu, rating, v.v.)
        additional_cols = {}
        
        # Tìm cột giá
        price_keywords = ['price', 'giá', 'cost', 'chi phí', 'amount', 'số tiền', 'money', 'giá cả']
        for col in df.columns:
            if col not in [review_col, source_col]:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in price_keywords):
                    additional_cols['price'] = col
                    break
        
        # Tìm cột rating/điểm đánh giá
        rating_keywords = ['rating', 'điểm', 'score', 'star', 'sao', 'đánh giá số', 'rate']
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in rating_keywords):
                    additional_cols['rating'] = col
                    break
        
        # Tìm cột menu/sản phẩm
        menu_keywords = ['menu', 'product', 'sản phẩm', 'item', 'món', 'dish', 'drink', 'đồ uống', 'food', 'thức ăn']
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in menu_keywords):
                    additional_cols['menu'] = col
                    break
        
        # Tìm cột ngày tháng
        date_keywords = ['date', 'ngày', 'time', 'thời gian', 'created', 'updated', 'timestamp']
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in date_keywords):
                    additional_cols['date'] = col
                    break
        
        # Tìm cột tên khách hàng/user
        user_keywords = ['user', 'customer', 'khách hàng', 'name', 'tên', 'author', 'người đánh giá']
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in user_keywords):
                    additional_cols['user'] = col
                    break
        
        # Chọn các cột cần thiết
        cols_to_keep = [review_col, source_col] + list(additional_cols.values())
        df_clean = df[cols_to_keep].copy()
        
        # Đổi tên cột
        rename_dict = {review_col: 'review', source_col: 'source'}
        for key, col in additional_cols.items():
            rename_dict[col] = key
        df_clean = df_clean.rename(columns=rename_dict)
        
        # Loại bỏ dòng có review trống hoặc chỉ có khoảng trắng
        df_clean = df_clean[df_clean['review'].notna()]
        df_clean['review'] = df_clean['review'].astype(str).str.strip()
        df_clean = df_clean[df_clean['review'] != '']
        df_clean = df_clean[df_clean['review'].str.lower() != 'nan']
        df_clean = df_clean[df_clean['review'].str.len() > 3]  # Ít nhất 3 ký tự
        
        # Chuẩn hóa source (MY_SHOP, COMPETITOR)
        df_clean['source'] = df_clean['source'].astype(str).str.strip().str.upper()
        
        # Mapping các giá trị source phổ biến
        source_mapping = {
            'MY_SHOP': 'MY_SHOP',
            'MY SHOP': 'MY_SHOP',
            'CỦA MÌNH': 'MY_SHOP',
            'CUA MINH': 'MY_SHOP',
            'SHOP': 'MY_SHOP',
            'STORE': 'MY_SHOP',
            'BRAND': 'MY_SHOP',
            'COMPETITOR': 'COMPETITOR',
            'COMPETITORS': 'COMPETITOR',
            'ĐỐI THỦ': 'COMPETITOR',
            'DOI THU': 'COMPETITOR',
            'COMPETITION': 'COMPETITOR',
            'RIVAL': 'COMPETITOR'
        }
        
        # Áp dụng mapping
        df_clean['source'] = df_clean['source'].replace(source_mapping)
        
        # Nếu giá trị không khớp, mặc định là MY_SHOP
        df_clean['source'] = df_clean['source'].apply(
            lambda x: 'MY_SHOP' if x not in ['MY_SHOP', 'COMPETITOR'] else x
        )
        
        if len(df_clean) == 0:
            raise ValueError("Không có dữ liệu hợp lệ sau khi làm sạch. Vui lòng kiểm tra lại file.")
        
        # Hiển thị thông tin debug chi tiết
        review_col_original = column_mapping.get(review_col, review_col)
        
        # Kiểm tra xem source có được phát hiện từ tên file không
        if source_col == 'source' and source_col not in column_mapping:
            # Kiểm tra giá trị source thực tế trong dataframe
            actual_source = df['source'].iloc[0] if len(df) > 0 else 'COMPETITOR'
            
            # Kiểm tra xem có phát hiện từ tên file không
            file_name_lower = (file_name or '').lower()
            competitor_keywords = ['competitor', 'đối thủ', 'starbucks', 'phuc long', 'katinat', 
                                 'highlands', 'trung nguyen', 'shopee', 'lazada', 'grab', 
                                 'now', 'baemin', 'gojek', 'competitors', 'rival']
            my_shop_keywords = ['my_shop', 'của mình', 'my store', 'our shop', 'our store', 'my_']
            
            if any(keyword in file_name_lower for keyword in competitor_keywords):
                source_col_display = f'Tự động từ tên file: COMPETITOR'
            elif any(keyword in file_name_lower for keyword in my_shop_keywords):
                source_col_display = f'Tự động từ tên file: MY_SHOP'
            else:
                # Hiển thị source thực tế (có thể là COMPETITOR nếu không phát hiện được MY_SHOP)
                source_col_display = f'Tự động: {actual_source}'
        else:
            source_col_display = column_mapping.get(source_col, source_col)
        
        info_text = f"✅ **Đã phát hiện:**\n"
        info_text += f"- Cột đánh giá chính: **{review_col_original}**\n"
        if len(review_cols) > 1:
            other_cols = [column_mapping.get(c, c) for c in review_cols if c != review_col]
            info_text += f"- Các cột đánh giá khác: {', '.join(other_cols)}\n"
        info_text += f"- Cột nguồn: **{source_col_display}**\n"
        
        # Hiển thị các cột bổ sung
        if additional_cols:
            info_text += f"- **Các thông tin bổ sung:**\n"
            for key, col in additional_cols.items():
                col_original = column_mapping.get(col, col)
                info_text += f"  • {key.upper()}: {col_original}\n"
        
        info_text += f"- Tổng số cột trong file: {len(original_columns)}"
        
        st.info(info_text)
        
        return df_clean.reset_index(drop=True)
    
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file: {str(e)}")


def prepare_reviews_for_ai(df: pd.DataFrame, max_reviews: int = 500) -> List[Dict[str, Any]]:
    """
    Chuyển đổi DataFrame thành format để gửi cho AI
    Tối ưu hóa để xử lý nhiều dữ liệu hơn, bao gồm cả các thông tin bổ sung
    
    Args:
        df: DataFrame đã làm sạch (có thể có thêm các cột: price, rating, menu, date, user)
        max_reviews: Số lượng review tối đa để gửi (tăng lên 500 để xử lý nhiều dữ liệu hơn)
    
    Returns:
        List các dict với keys: 'review', 'source', và các keys khác nếu có (price, rating, menu, v.v.)
    """
    total_reviews = len(df)
    
    # Nếu có quá nhiều reviews, sử dụng sampling thông minh
    if total_reviews > max_reviews:
        # Đảm bảo cân bằng giữa MY_SHOP và COMPETITOR
        my_shop_df = df[df['source'] == 'MY_SHOP']
        competitor_df = df[df['source'] == 'COMPETITOR']
        
        # Tính tỷ lệ
        my_shop_ratio = len(my_shop_df) / total_reviews if total_reviews > 0 else 0.5
        competitor_ratio = len(competitor_df) / total_reviews if total_reviews > 0 else 0.5
        
        # Lấy mẫu cân bằng
        my_shop_sample_size = int(max_reviews * my_shop_ratio)
        competitor_sample_size = max_reviews - my_shop_sample_size
        
        if len(my_shop_df) > 0:
            my_shop_sample = my_shop_df.sample(n=min(my_shop_sample_size, len(my_shop_df)), random_state=42)
        else:
            my_shop_sample = pd.DataFrame()
        
        if len(competitor_df) > 0:
            competitor_sample = competitor_df.sample(n=min(competitor_sample_size, len(competitor_df)), random_state=42)
        else:
            competitor_sample = pd.DataFrame()
        
        # Kết hợp lại
        if len(my_shop_sample) > 0 and len(competitor_sample) > 0:
            df = pd.concat([my_shop_sample, competitor_sample], ignore_index=True)
        elif len(my_shop_sample) > 0:
            df = my_shop_sample
        elif len(competitor_sample) > 0:
            df = competitor_sample
        else:
            df = df.sample(n=max_reviews, random_state=42)
        
        st.warning(f"⚠️ Có {total_reviews:,} reviews. Đang phân tích {len(df):,} reviews được chọn mẫu cân bằng để tối ưu hiệu suất.")
    
    reviews_list = []
    for _, row in df.iterrows():
        review_dict = {
            'review': str(row['review']),
            'source': str(row['source'])
        }
        
        # Thêm các thông tin bổ sung nếu có
        for col in ['price', 'rating', 'menu', 'date', 'user']:
            if col in df.columns:
                review_dict[col] = row[col]
        
        reviews_list.append(review_dict)
    
    return reviews_list


def create_swot_pie_chart(swot_data: Dict[str, Any]) -> go.Figure:
    """
    Tạo biểu đồ tròn hiển thị số lượng items trong mỗi nhóm SWOT
    
    Args:
        swot_data: Dict chứa SWOT_Analysis
    
    Returns:
        Plotly Figure object
    """
    swot = swot_data.get("SWOT_Analysis", {})
    
    categories = ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']
    counts = [
        len(swot.get("Strengths", [])),
        len(swot.get("Weaknesses", [])),
        len(swot.get("Opportunities", [])),
        len(swot.get("Threats", []))
    ]
    
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12']  # Xanh lá, Đỏ, Xanh dương, Vàng
    
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=counts,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent+value',
        textfont_size=12
    )])
    
    fig.update_layout(
        title={
            'text': 'Phân bố SWOT Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        showlegend=True,
        height=400
    )
    
    return fig


def create_impact_bar_chart(swot_data: Dict[str, Any]) -> go.Figure:
    """
    Tạo biểu đồ cột hiển thị phân bố Impact/Risk Level
    
    Args:
        swot_data: Dict chứa SWOT_Analysis
    
    Returns:
        Plotly Figure object
    """
    swot = swot_data.get("SWOT_Analysis", {})
    
    impact_levels = {'High': 0, 'Medium': 0, 'Low': 0}
    
    # Đếm Strengths và Weaknesses theo impact
    for item in swot.get("Strengths", []):
        impact = item.get("impact", "Medium")
        if impact in impact_levels:
            impact_levels[impact] += 1
    
    for item in swot.get("Weaknesses", []):
        impact = item.get("impact", "Medium")
        if impact in impact_levels:
            impact_levels[impact] += 1
    
    # Đếm Threats theo risk_level
    for item in swot.get("Threats", []):
        risk = item.get("risk_level", "Medium")
        if risk in impact_levels:
            impact_levels[risk] += 1
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(impact_levels.keys()),
            y=list(impact_levels.values()),
            marker_color=['#e74c3c', '#f39c12', '#2ecc71'],  # Đỏ, Vàng, Xanh lá
            text=list(impact_levels.values()),
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title={
            'text': 'Phân bố Mức độ Ảnh hưởng/Rủi ro',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Mức độ',
        yaxis_title='Số lượng',
        height=400
    )
    
    return fig


def format_swot_table_data(swot_data: Dict[str, Any], category: str) -> List[Dict[str, str]]:
    """
    Format dữ liệu SWOT để hiển thị trong bảng Streamlit
    
    Args:
        swot_data: Dict chứa SWOT_Analysis
        category: 'Strengths', 'Weaknesses', 'Opportunities', hoặc 'Threats'
    
    Returns:
        List các dict đã format
    """
    swot = swot_data.get("SWOT_Analysis", {})
    items = swot.get(category, [])
    
    formatted_items = []
    for item in items:
        formatted_item = {
            "Chủ đề": item.get("topic", "N/A"),
            "Mô tả": item.get("description", "N/A")
        }
        
        # Thêm các trường đặc biệt
        if category == "Strengths" or category == "Weaknesses":
            formatted_item["Mức độ ảnh hưởng"] = item.get("impact", "N/A")
            if category == "Weaknesses":
                formatted_item["Nguyên nhân gốc rễ"] = item.get("root_cause", "N/A")
        
        if category == "Opportunities":
            formatted_item["Gợi ý hành động"] = item.get("action_idea", "N/A")
        
        if category == "Threats":
            formatted_item["Mức độ rủi ro"] = item.get("risk_level", "N/A")
        
        formatted_items.append(formatted_item)
    
    return formatted_items
