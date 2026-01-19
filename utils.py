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
        if file_extension == 'csv':
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)  # Reset file pointer
                    # Use separator sniffing
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=None, engine='python')
                    
                    # If sniffing returned 1 column, try fallback separators
                    if len(df.columns) == 1:
                         # Prioritize semicolon, then tab, then comma (explicitly)
                         for sep in [';', '\t', ',']:
                             try:
                                 uploaded_file.seek(0)
                                 df_temp = pd.read_csv(uploaded_file, encoding=encoding, sep=sep, engine='python')
                                 if len(df_temp.columns) > 1:
                                     df = df_temp
                                     break
                             except:
                                 pass
                    
                    break
                except UnicodeDecodeError:
                    continue
                except Exception:
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
                    
                    # Không phải cột ID, code, số hoặc Item/Menu (trừ khi có chữ review)
                    excluded_review_keywords = ['id', 'code', 'number', 'num', 'no', 'stt', 'index', 'item', 'menu', 'product', 'món', 'tên', 'category', 'sản phẩm']
                    has_review_keyword = any(k in col_lower for k in ['review', 'comment', 'feedback', 'đánh giá', 'nhận xét'])
                    
                    if any(keyword in col_lower for keyword in excluded_review_keywords) and not has_review_keyword:
                         score -= 100 # Penalize heavily
                    else:
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
        
        # Bước 5: Nếu vẫn không tìm thấy review, thử kiểm tra xem có phải là file Menu/Bảng giá không
        if review_col is None:
            # Check for Menu keywords
            item_keywords = ['product', 'item', 'dish', 'menu', 'món', 'tên món', 'sản phẩm']
            price_keywords = ['price', 'cost', 'amount', 'giá', 'đơn giá', 'tiền']
            
            item_col_name = None
            found_price = False
            
            for col in df.columns:
                col_lower = col.lower()
                # Exclude ID/Code columns
                if any(x in col_lower for x in ['code', 'id', 'mã', 'stt', 'no.', 'order']):
                    continue
                    
                if any(k in col_lower for k in item_keywords) and not item_col_name: 
                    item_col_name = col
                if any(k in col_lower for k in price_keywords): 
                    found_price = True
            
            if item_col_name and found_price:
                # Đây là file Menu -> Tạo cột review giả UNIQUE để tránh bị drop_duplicates lọc mất
                # Thêm index để đảm bảo unique 100%
                df['dummy_review'] = "Menu Item: " + df[item_col_name].astype(str) + " #" + df.index.astype(str)
                review_col = 'dummy_review'
            else:
                # Báo lỗi như cũ
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
            
            # Áp dụng kết quả phát hiện (lưu thông tin để hiển thị sau)
            file_detection_info = {
                'source': None,
                'method': None,
                'shop_name': None,
                'has_warning': False
            }
            
            if detected_source:
                file_detection_info['source'] = detected_source
                file_detection_info['method'] = detection_method
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
                    file_detection_info['source'] = 'COMPETITOR'
                    file_detection_info['shop_name'] = shop_name
                    file_detection_info['method'] = f"tên file '{file_name}'"
                    df['source'] = 'COMPETITOR'
                    source_col = 'source'
                else:
                    # Nếu không phát hiện được shop cụ thể
                    # Nếu là file Menu (có dummy_review), khả năng cao là file của User -> Mặc định MY_SHOP
                    if review_col == 'dummy_review' or 'dummy_review' in df.columns:
                         file_detection_info['source'] = 'MY_SHOP'
                         file_detection_info['method'] = "Mặc định (File Menu)"
                         df['source'] = 'MY_SHOP'
                    else:
                         # Nếu là file Review thông thường mà không rõ nguồn -> COMPETITOR
                         file_detection_info['source'] = 'COMPETITOR'
                         file_detection_info['has_warning'] = True
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
                # Lưu thông tin để hiển thị sau (không hiển thị ngay)
                if 'combined_cols_info' not in locals():
                    combined_cols_info = {}
                combined_cols_info['count'] = len(review_cols)
                combined_cols_info['cols'] = [column_mapping.get(c, c) for c in review_cols]
        
        # Bước 7: Tìm các cột bổ sung (giá, menu, rating, v.v.) - MỞ RỘNG
        additional_cols = {}
        
        # Tìm cột giá - MỞ RỘNG từ khóa
        price_keywords = [
            'price', 'giá', 'cost', 'chi phí', 'amount', 'số tiền', 'money', 'giá cả',
            'gia', 'don gia', 'đơn giá', 'gia_ban', 'gia ban', 'price_range', 'pricing',
            'giá bán', 'giá trị', 'value', 'cost_price', 'selling_price', 'unit_price',
            'giá tiền', 'tien', 'tiền', 'vnd', 'dong', 'đồng', 'usd', 'currency',
            'gia_hien_thi', 'gia hien thi', 'display_price', 'final_price', 'total_price'
        ]
        for col in df.columns:
            if col not in [review_col, source_col]:
                col_lower = col.lower().strip()
                # Kiểm tra chính xác hoặc chứa từ khóa
                if any(keyword in col_lower or col_lower == keyword for keyword in price_keywords):
                    # Kiểm tra xem cột có chứa giá trị số không
                    if df[col].dtype in ['int64', 'float64'] or pd.to_numeric(df[col], errors='coerce').notna().sum() > len(df) * 0.3:
                        additional_cols['price'] = col
                        break
        
        # Tìm cột rating/điểm đánh giá - MỞ RỘNG
        rating_keywords = [
            'rating', 'điểm', 'score', 'star', 'sao', 'đánh giá số', 'rate',
            'diem', 'danh gia', 'stars', 'rating_score', 'review_score', 'overall_rating',
            'customer_rating', 'user_rating', 'quality_score', 'satisfaction', 'mức độ hài lòng',
            'điểm số', 'diem so', 'đánh giá', 'danh gia', 'vote', 'votes', 'likes'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                if any(keyword in col_lower or col_lower == keyword for keyword in rating_keywords):
                    additional_cols['rating'] = col
                    break
        
        # Tìm cột menu/sản phẩm - MỞ RỘNG
        menu_keywords = [
            'menu', 'product', 'sản phẩm', 'item', 'món', 'dish', 'drink', 'đồ uống', 
            'food', 'thức ăn', 'san pham', 'ten mon', 'tên món', 'product_name', 
            'item_name', 'menu_item', 'dish_name', 'product_title', 'item_title',
            'tên sản phẩm', 'ten san pham', 'món ăn', 'mon an', 'đồ ăn', 'do an',
            'category', 'danh mục', 'danh muc', 'type', 'loại', 'loai', 'brand', 'thương hiệu'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                # Loại trừ các cột ID/code
                if any(x in col_lower for x in ['code', 'id', 'mã', 'stt', 'no.', 'order', '_no', '_id']):
                    continue
                if any(keyword in col_lower or col_lower == keyword for keyword in menu_keywords):
                    additional_cols['menu'] = col
                    break
        
        # Tìm cột ngày tháng - MỞ RỘNG
        date_keywords = [
            'date', 'ngày', 'time', 'thời gian', 'created', 'updated', 'timestamp',
            'ngay', 'thoi gian', 'created_at', 'updated_at', 'created_date', 'updated_date',
            'review_date', 'comment_date', 'post_date', 'publish_date', 'datetime', 'date_time',
            'ngày đánh giá', 'ngay danh gia', 'ngày tạo', 'ngay tao', 'thời điểm', 'thoi diem'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                if any(keyword in col_lower or col_lower == keyword for keyword in date_keywords):
                    additional_cols['date'] = col
                    break
        
        # Tìm cột tên khách hàng/user - MỞ RỘNG
        user_keywords = [
            'user', 'customer', 'khách hàng', 'name', 'tên', 'author', 'người đánh giá',
            'khach hang', 'nguoi danh gia', 'reviewer', 'reviewer_name', 'customer_name',
            'user_name', 'username', 'full_name', 'tên khách', 'ten khach', 'người dùng',
            'nguoi dung', 'buyer', 'purchaser', 'client', 'visitor', 'guest'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                # Loại trừ các cột có thể nhầm lẫn (như Restaurant Name, Address)
                if any(excluded in col_lower for excluded in ['restaurant', 'shop', 'store', 'address', 'location', 'link']):
                    continue
                if any(keyword in col_lower or col_lower == keyword for keyword in user_keywords):
                    additional_cols['user'] = col
                    break
        
        # Tìm thêm các cột khác có thể hữu ích
        # Cột địa chỉ/location
        location_keywords = [
            'location', 'address', 'địa chỉ', 'dia chi', 'place', 'venue', 'vị trí', 'vi tri',
            'city', 'thành phố', 'thanh pho', 'district', 'quận', 'quan', 'ward', 'phường', 'phuong',
            'street', 'đường', 'duong', 'area', 'khu vực', 'khu vuc'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                if any(keyword in col_lower or col_lower == keyword for keyword in location_keywords):
                    additional_cols['location'] = col
                    break
        
        # Cột số lượng/quantity
        quantity_keywords = [
            'quantity', 'qty', 'số lượng', 'so luong', 'amount', 'số', 'so', 'count',
            'quantity_ordered', 'qty_ordered', 'units', 'số đơn', 'so don', 'volume'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                if any(keyword in col_lower or col_lower == keyword for keyword in quantity_keywords):
                    additional_cols['quantity'] = col
                    break
        
        # Cột danh mục/category
        category_keywords = [
            'category', 'danh mục', 'danh muc', 'type', 'loại', 'loai', 'group', 'nhóm', 'nhom',
            'classification', 'class', 'tag', 'tags', 'label', 'labels', 'genre', 'thể loại', 'the loai'
        ]
        for col in df.columns:
            if col not in [review_col, source_col] and col not in additional_cols.values():
                col_lower = col.lower().strip()
                if any(keyword in col_lower or col_lower == keyword for keyword in category_keywords):
                    additional_cols['category'] = col
                    break
        
        # Giữ lại TẤT CẢ các cột để không bị mất dữ liệu quan trọng cho các bước sau (như extract_price_data)
        df_clean = df.copy()
        
        # Đổi tên các cột đã nhận diện được cho chuẩn format của App
        rename_dict = {review_col: 'review', source_col: 'source'}
        for key, col in additional_cols.items():
            rename_dict[col] = key
        
        # Thực hiện đổi tên
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
            # Fallback for Menu Files that might have been filtered out
            # Check if original df had Item and Price
            item_keywords = ['product', 'item', 'dish', 'menu', 'món', 'tên món', 'sản phẩm', 'ten mon', 'san pham']
            price_keywords = ['price', 'cost', 'amount', 'giá', 'đơn giá', 'tiền', 'gia', 'don gia']
            
            has_item = any(any(k in col.lower() for k in item_keywords) for col in df.columns)
            has_price = any(any(k in col.lower() for k in price_keywords) for col in df.columns)
            
            if has_item and has_price:
                 # Salvage: Force create dummy review
                 df_clean = df.copy()
                 # Find item col again
                 item_col = next((c for c in df.columns if any(k in c.lower() for k in item_keywords)), df.columns[0])
                 df_clean['review'] = "Menu Item: " + df_clean[item_col].astype(str) + " #" + df_clean.index.astype(str)
                 df_clean['source'] = 'MY_SHOP' # Default
                 return df_clean

            error_msg = f"Không có dữ liệu hợp lệ sau khi làm sạch. Vui lòng kiểm tra lại file.\nDebug Cols: {list(df.columns)}"
            raise ValueError(error_msg)
        
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
        
        # Lưu thông tin file để hiển thị sau (không hiển thị ngay)
        file_summary = {
            'name': file_name,
            'review_cols_count': len(review_cols),
            'source': source_col_display.split(':')[-1].strip(),
            'additional_cols_count': len(additional_cols),
            'total_cols': len(original_columns),
            'review_col': review_col_original,
            'other_cols': [column_mapping.get(c, c) for c in review_cols if c != review_col] if len(review_cols) > 1 else [],
            'combined_cols_info': combined_cols_info if 'combined_cols_info' in locals() else None,
            'additional_cols': {k: column_mapping.get(v, v) for k, v in additional_cols.items()} if additional_cols else {},
            'has_warning': file_detection_info.get('has_warning', False) if 'file_detection_info' in locals() else False
        }
        
        # Lưu vào session state để app.py hiển thị
        if 'file_summaries' not in st.session_state:
            st.session_state['file_summaries'] = []
        st.session_state['file_summaries'].append(file_summary)
        
        return df_clean.reset_index(drop=True)
    
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file: {str(e)}")


def prepare_reviews_for_ai(df: pd.DataFrame, max_reviews: int = 500) -> List[Dict[str, Any]]:
    """
    Chuyển đổi DataFrame thành format để gửi cho AI
    Tối ưu hóa để xử lý nhiều dữ liệu hơn, bao gồm cả các thông tin bổ sung
    CHỌN LỌC THÔNG MINH: Ưu tiên reviews có nhiều thông tin, đa dạng, và quan trọng
    
    Args:
        df: DataFrame đã làm sạch (có thể có thêm các cột: price, rating, menu, date, user)
        max_reviews: Số lượng review tối đa để gửi (500 để xử lý nhiều dữ liệu hơn)
    
    Returns:
        List các dict với keys: 'review', 'source', và các keys khác nếu có (price, rating, menu, v.v.)
    """
    total_reviews = len(df)
    
    # Nếu có quá nhiều reviews, sử dụng sampling thông minh với chọn lọc tốt hơn
    if total_reviews > max_reviews:
        # Tính điểm ưu tiên cho mỗi review (scoring system)
        df = df.copy()
        df['_priority_score'] = 0
        
        # 1. Điểm cho độ dài review (reviews dài thường có nhiều thông tin hơn)
        df['_review_length'] = df['review'].astype(str).str.len()
        df['_priority_score'] += df['_review_length'].apply(lambda x: min(x / 100, 5))  # Tối đa 5 điểm
        
        # 2. Điểm cho thông tin bổ sung (có price, rating, menu, date, user)
        info_columns = ['price', 'rating', 'menu', 'date', 'user', 'location', 'quantity', 'category']
        for col in info_columns:
            if col in df.columns:
                df['_priority_score'] += df[col].notna().astype(int) * 2  # Mỗi thông tin bổ sung = 2 điểm
        
        # 3. Điểm cho rating (reviews có rating cao hoặc thấp đều quan trọng)
        if 'rating' in df.columns:
            # Chuyển rating sang số nếu có thể
            df['_rating_num'] = pd.to_numeric(df['rating'], errors='coerce')
            # Ưu tiên rating cực cao (5) hoặc cực thấp (1-2) vì chúng có insights rõ ràng
            df['_priority_score'] += df['_rating_num'].apply(
                lambda x: 3 if pd.notna(x) and (x >= 4.5 or x <= 2) else (1 if pd.notna(x) else 0)
            )
        
        # 4. Điểm cho độ đa dạng (tránh chọn nhiều reviews giống nhau)
        # Sử dụng hash của review để nhóm các reviews tương tự
        df['_review_hash'] = df['review'].astype(str).str.lower().str.strip().apply(hash)
        
        # 5. Điểm cho từ khóa quan trọng (từ khóa liên quan đến SWOT)
        important_keywords = [
            'tốt', 'tuyệt', 'xuất sắc', 'tệ', 'kém', 'chậm', 'nhanh', 'đắt', 'rẻ', 'giá',
            'nhân viên', 'phục vụ', 'dịch vụ', 'chất lượng', 'ngon', 'dở', 'sạch', 'bẩn',
            'không gian', 'vị trí', 'thuận tiện', 'đông', 'vắng', 'yên tĩnh', 'ồn ào',
            'đề xuất', 'khuyên', 'không nên', 'tránh', 'nên thử', 'quay lại', 'không quay lại',
            'good', 'excellent', 'bad', 'poor', 'slow', 'fast', 'expensive', 'cheap', 'price',
            'staff', 'service', 'quality', 'delicious', 'dirty', 'clean', 'space', 'location'
        ]
        df['_keyword_count'] = df['review'].astype(str).str.lower().apply(
            lambda x: sum(1 for kw in important_keywords if kw in x)
        )
        df['_priority_score'] += df['_keyword_count'] * 0.5  # Mỗi từ khóa = 0.5 điểm
        
        # Tách MY_SHOP và COMPETITOR để chọn lọc riêng
        my_shop_df = df[df['source'] == 'MY_SHOP'].copy()
        competitor_df = df[df['source'] == 'COMPETITOR'].copy()
        
        # Tính tỷ lệ để giữ cân bằng
        my_shop_ratio = len(my_shop_df) / total_reviews if total_reviews > 0 else 0.5
        competitor_ratio = len(competitor_df) / total_reviews if total_reviews > 0 else 0.5
        
        # Lấy mẫu thông minh cho MY_SHOP
        my_shop_sample_size = int(max_reviews * my_shop_ratio)
        if len(my_shop_df) > 0 and my_shop_sample_size > 0:
            # Sắp xếp theo priority score và chọn đa dạng
            my_shop_df = my_shop_df.sort_values('_priority_score', ascending=False)
            
            # Chọn top reviews nhưng đảm bảo đa dạng (không chọn quá nhiều reviews giống nhau)
            selected_my_shop = []
            seen_hashes = set()
            
            for _, row in my_shop_df.iterrows():
                if len(selected_my_shop) >= my_shop_sample_size:
                    break
                # Chỉ thêm nếu chưa có review tương tự (hash khác)
                review_hash = row['_review_hash']
                if review_hash not in seen_hashes:
                    selected_my_shop.append(row)
                    seen_hashes.add(review_hash)
                elif len(selected_my_shop) < my_shop_sample_size * 0.8:  # Cho phép 20% trùng lặp
                    selected_my_shop.append(row)
            
            my_shop_sample = pd.DataFrame(selected_my_shop)
        else:
            my_shop_sample = pd.DataFrame()
        
        # Lấy mẫu thông minh cho COMPETITOR
        competitor_sample_size = max_reviews - len(my_shop_sample)
        if len(competitor_df) > 0 and competitor_sample_size > 0:
            # Sắp xếp theo priority score
            competitor_df = competitor_df.sort_values('_priority_score', ascending=False)
            
            # Chọn top reviews nhưng đảm bảo đa dạng
            selected_competitor = []
            seen_hashes = set()
            
            for _, row in competitor_df.iterrows():
                if len(selected_competitor) >= competitor_sample_size:
                    break
                review_hash = row['_review_hash']
                if review_hash not in seen_hashes:
                    selected_competitor.append(row)
                    seen_hashes.add(review_hash)
                elif len(selected_competitor) < competitor_sample_size * 0.8:
                    selected_competitor.append(row)
            
            competitor_sample = pd.DataFrame(selected_competitor)
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
            # Fallback: chọn top reviews theo priority score
            df = df.nlargest(max_reviews, '_priority_score')
        
        # Xóa các cột tạm
        df = df.drop(columns=[col for col in df.columns if col.startswith('_')])
        
        st.info(f"📊 Đã chọn lọc {len(df):,} reviews quan trọng nhất từ {total_reviews:,} reviews (ưu tiên reviews có nhiều thông tin, đa dạng, và có từ khóa quan trọng).")
    
    # Detect smart column mappings - MỞ RỘNG để nhận diện nhiều cột hơn
    col_mapping = {}
    
    # Keyword lists (enhanced - mở rộng để nhận diện nhiều cột hơn)
    price_keywords = [
        'price', 'cost', 'amount', 'giá', 'đơn giá', 'chi phí', 'tiền', 'gia', 'don gia', 'gia_ban',
        'gia hien thi', 'gia_hien_thi', 'display_price', 'final_price', 'total_price', 'selling_price',
        'unit_price', 'cost_price', 'price_range', 'pricing', 'giá bán', 'giá trị', 'value', 'vnd', 'dong'
    ]
    menu_keywords = [
        'product', 'item', 'dish', 'menu', 'món', 'tên món', 'sản phẩm', 'food', 'drink', 'name', 'tên', 
        'ten mon', 'san pham', 'product_name', 'item_name', 'menu_item', 'dish_name', 'product_title',
        'tên sản phẩm', 'ten san pham', 'món ăn', 'mon an', 'đồ ăn', 'do an', 'category', 'danh mục',
        'type', 'loại', 'loai', 'brand', 'thương hiệu'
    ]
    rating_keywords = [
        'rating', 'score', 'star', 'điểm', 'sao', 'đánh giá', 'danh gia', 'diem', 'stars', 'rating_score',
        'review_score', 'overall_rating', 'customer_rating', 'user_rating', 'quality_score', 'satisfaction',
        'điểm số', 'diem so', 'vote', 'votes', 'likes'
    ]
    date_keywords = [
        'date', 'time', 'ngày', 'giờ', 'thời gian', 'ngay', 'created_at', 'updated_at', 'created_date',
        'updated_date', 'review_date', 'comment_date', 'post_date', 'publish_date', 'datetime', 'date_time',
        'ngày đánh giá', 'ngay danh gia', 'ngày tạo', 'ngay tao', 'thời điểm', 'thoi diem'
    ]
    user_keywords = [
        'user', 'customer', 'name', 'khách', 'người dùng', 'tên khách', 'khach hang', 'nguoi danh gia',
        'reviewer', 'reviewer_name', 'customer_name', 'user_name', 'username', 'full_name', 'tên khách',
        'ten khach', 'người dùng', 'nguoi dung', 'buyer', 'purchaser', 'client', 'visitor', 'guest'
    ]
    location_keywords = [
        'location', 'address', 'địa chỉ', 'dia chi', 'place', 'venue', 'vị trí', 'vi tri',
        'city', 'thành phố', 'thanh pho', 'district', 'quận', 'quan', 'ward', 'phường', 'phuong'
    ]
    quantity_keywords = [
        'quantity', 'qty', 'số lượng', 'so luong', 'amount', 'số', 'so', 'count',
        'quantity_ordered', 'qty_ordered', 'units', 'số đơn', 'so don', 'volume'
    ]
    category_keywords = [
        'category', 'danh mục', 'danh muc', 'type', 'loại', 'loai', 'group', 'nhóm', 'nhom',
        'classification', 'class', 'tag', 'tags', 'label', 'labels', 'genre', 'thể loại', 'the loai'
    ]
    
    # Find best matching columns if standard names don't exist
    # Mở rộng để tìm nhiều loại cột hơn
    for target, keywords in [
        ('price', price_keywords), 
        ('menu', menu_keywords), 
        ('rating', rating_keywords),
        ('date', date_keywords), 
        ('user', user_keywords),
        ('location', location_keywords),
        ('quantity', quantity_keywords),
        ('category', category_keywords)
    ]:
        if target in df.columns:
             col_mapping[target] = target
        else:
             # Find first matching column (case-insensitive, flexible matching)
             match = next((c for c in df.columns if any(k in c.lower().strip() for k in keywords)), None)
             if match:
                 col_mapping[target] = match

    reviews_list = []
    for _, row in df.iterrows():
        review_dict = {
            'review': str(row['review']),
            'source': str(row['source'])
        }
        
        # Add additional info using mapped columns
        for target_key, df_col in col_mapping.items():
            if pd.notna(row[df_col]):
                review_dict[target_key] = row[df_col]
        
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
        
        # Thêm priority score nếu có
        if "priority_score" in item:
            formatted_item["Điểm ưu tiên"] = item.get("priority_score", "N/A")
        
        # Thêm các trường đặc biệt
        if category == "Strengths":
            formatted_item["Mức độ ảnh hưởng"] = item.get("impact", "N/A")
            formatted_item["Chiến lược tận dụng"] = item.get("leverage_strategy", "N/A")
        
        if category == "Weaknesses":
            formatted_item["Mức độ ảnh hưởng"] = item.get("impact", "N/A")
            formatted_item["Nguyên nhân gốc rễ"] = item.get("root_cause", "N/A")
            formatted_item["Kế hoạch khắc phục"] = item.get("mitigation_plan", "N/A")
        
        if category == "Opportunities":
            formatted_item["Gợi ý hành động"] = item.get("action_idea", "N/A")
            formatted_item["Quy mô thị trường"] = item.get("market_size", "N/A")
            formatted_item["Thời gian nắm bắt"] = item.get("time_to_capture", "N/A")
        
        if category == "Threats":
            formatted_item["Mức độ rủi ro"] = item.get("risk_level", "N/A")
            formatted_item["Xác suất"] = item.get("probability", "N/A")
            formatted_item["Mức độ nghiêm trọng"] = item.get("severity", "N/A")
            formatted_item["Kế hoạch ứng phó"] = item.get("contingency_plan", "N/A")
        
        formatted_items.append(formatted_item)
    
    return formatted_items


# ========== ENTERPRISE VISUALIZATIONS ==========

def create_tows_matrix_chart(tows_data: Dict[str, List]) -> go.Figure:
    """
    Tạo biểu đồ TOWS Matrix 2x2
    
    Args:
        tows_data: Dict chứa SO_Strategies, WO_Strategies, ST_Strategies, WT_Strategies
    
    Returns:
        Plotly Figure object
    """
    # Count strategies in each quadrant
    so_count = len(tows_data.get('SO_Strategies', []))
    wo_count = len(tows_data.get('WO_Strategies', []))
    st_count = len(tows_data.get('ST_Strategies', []))
    wt_count = len(tows_data.get('WT_Strategies', []))
    
    # Create heatmap data
    z = [[so_count, st_count],
         [wo_count, wt_count]]
    
    x_labels = ['Opportunities', 'Threats']
    y_labels = ['Strengths', 'Weaknesses']
    
    # Create text for each cell
    text = [
        [f"SO Strategies<br>{so_count} chiến lược<br>(Tấn công)", 
         f"ST Strategies<br>{st_count} chiến lược<br>(Đa dạng hóa)"],
        [f"WO Strategies<br>{wo_count} chiến lược<br>(Chuyển đổi)", 
         f"WT Strategies<br>{wt_count} chiến lược<br>(Phòng thủ)"]
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 12},
        colorscale=[[0, '#3498db'], [0.5, '#9b59b6'], [1, '#e74c3c']],
        showscale=True,
        hoverongaps=False
    ))
    
    fig.update_layout(
        title={
            'text': '📊 Ma trận TOWS - Chiến lược Kết hợp',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Yếu tố Bên ngoài',
        yaxis_title='Yếu tố Nội bộ',
        height=450,
        xaxis={'side': 'top'}
    )
    
    return fig


def create_priority_heatmap(swot_data: Dict[str, Any]) -> go.Figure:
    """
    Tạo Priority Matrix Heatmap (Impact vs Feasibility)
    
    Args:
        swot_data: Dict chứa SWOT_Analysis với priority_score
    
    Returns:
        Plotly Figure object
    """
    swot = swot_data.get("SWOT_Analysis", {})
    
    items = []
    for category in ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']:
        for item in swot.get(category, []):
            items.append({
                'topic': item.get('topic', 'N/A'),  # Full topic for hover
                'category': category,
                'priority_score': item.get('priority_score', 5),
                'impact': item.get('impact') or item.get('risk_level', 'Medium')
            })

    
    if not items:
        # Return empty figure if no data
        fig = go.Figure()
        fig.add_annotation(text="Không có dữ liệu", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    df_items = pd.DataFrame(items)
    
    # Map impact to numeric
    impact_map = {'High': 3, 'Medium': 2, 'Low': 1}
    df_items['impact_score'] = df_items['impact'].map(impact_map).fillna(2)
    
    # Map category to color
    color_map = {
        'Strengths': '#2ecc71',
        'Weaknesses': '#e74c3c', 
        'Opportunities': '#3498db',
        'Threats': '#f39c12'
    }
    df_items['color'] = df_items['category'].map(color_map)
    
    # Add jitter to avoid overlapping points
    import numpy as np
    np.random.seed(42)
    df_items['impact_jitter'] = df_items['impact_score'] + np.random.uniform(-0.15, 0.15, len(df_items))
    df_items['priority_jitter'] = df_items['priority_score'] + np.random.uniform(-0.2, 0.2, len(df_items))
    
    fig = go.Figure()
    
    for category in ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']:
        df_cat = df_items[df_items['category'] == category]
        if not df_cat.empty:
            fig.add_trace(go.Scatter(
                x=df_cat['impact_jitter'],
                y=df_cat['priority_jitter'],
                mode='markers',
                marker=dict(
                    size=16,
                    color=color_map[category],
                    line=dict(width=2, color='white'),
                    opacity=0.85
                ),
                name=category,
                customdata=df_cat['topic'],
                hovertemplate='<b>%{customdata}</b><br>Impact: %{x:.0f}<br>Priority: %{y:.1f}<extra></extra>'
            ))
    
    # Add quadrant lines
    fig.add_hline(y=5, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels - positioned inside chart area with smaller text
    fig.add_annotation(x=2.5, y=8.5, text="Ưu tiên cao", showarrow=False, font=dict(size=10, color="#27ae60"))
    fig.add_annotation(x=1.5, y=8.5, text="Theo dõi", showarrow=False, font=dict(size=10, color="#3498db"))
    fig.add_annotation(x=2.5, y=1.5, text="Quick Wins", showarrow=False, font=dict(size=10, color="#f39c12"))
    fig.add_annotation(x=1.5, y=1.5, text="Backlog", showarrow=False, font=dict(size=10, color="#95a5a6"))
    
    fig.update_layout(
        title={
            'text': 'Ma trận Ưu tiên (Impact vs Priority Score)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 14}
        },
        xaxis_title='Mức độ Ảnh hưởng',
        yaxis_title='Điểm Ưu tiên',
        xaxis=dict(
            tickmode='array', 
            tickvals=[1, 2, 3], 
            ticktext=['Low', 'Medium', 'High'], 
            range=[0.8, 3.2]  # Tighter range
        ),
        yaxis=dict(range=[0, 10]),
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),  # Better margins
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hovermode='closest'
    )
    
    return fig





def create_competitive_radar(competitive_data: Dict[str, Any]) -> go.Figure:
    """
    Tạo Radar Chart so sánh cạnh tranh
    
    Args:
        competitive_data: Dict chứa my_scores và competitor_scores
    
    Returns:
        Plotly Figure object
    """
    dimensions = competitive_data.get('dimensions', ['quality', 'price', 'service', 'location', 'brand', 'innovation'])
    my_scores = competitive_data.get('my_scores', {})
    competitor_scores = competitive_data.get('competitor_scores', {})
    
    # Vietnamese labels
    label_map = {
        'quality': 'Chất lượng',
        'price': 'Giá cả',
        'service': 'Dịch vụ',
        'location': 'Vị trí',
        'brand': 'Thương hiệu',
        'innovation': 'Đổi mới'
    }
    
    labels = [label_map.get(d, d) for d in dimensions]
    
    my_values = [my_scores.get(d, 5) for d in dimensions]
    comp_values = [competitor_scores.get(d, 5) for d in dimensions]
    
    # Close the radar chart
    labels.append(labels[0])
    my_values.append(my_values[0])
    comp_values.append(comp_values[0])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=my_values,
        theta=labels,
        fill='toself',
        fillcolor='rgba(46, 204, 113, 0.3)',
        line=dict(color='#2ecc71', width=2),
        name='Quán của bạn'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=comp_values,
        theta=labels,
        fill='toself',
        fillcolor='rgba(231, 76, 60, 0.3)',
        line=dict(color='#e74c3c', width=2),
        name='Đối thủ trung bình'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickmode='array',
                tickvals=[2, 4, 6, 8, 10]
            )
        ),
        title={
            'text': 'So sánh Vị thế Cạnh tranh',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        showlegend=True,
        height=500
    )
    
    return fig


def create_risk_matrix(risk_data: List[Dict]) -> go.Figure:
    """
    Tạo Risk Matrix (Probability vs Severity)
    
    Args:
        risk_data: List các threats với probability và severity
    
    Returns:
        Plotly Figure object
    """
    if not risk_data:
        fig = go.Figure()
        fig.add_annotation(text="Không có dữ liệu rủi ro", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Map levels to numeric
    level_map = {'High': 3, 'Medium': 2, 'Low': 1}
    
    x_vals = []
    y_vals = []
    texts = []
    colors = []
    
    for risk in risk_data:
        prob = level_map.get(risk.get('probability', 'Medium'), 2)
        sev = level_map.get(risk.get('severity', risk.get('risk_level', 'Medium')), 2)
        
        x_vals.append(prob)
        y_vals.append(sev)
        texts.append(risk.get('topic', 'N/A'))  # Full text for hover
        
        # Color based on composite risk
        risk_score = prob * sev
        if risk_score >= 6:
            colors.append('#e74c3c')  # Red - Critical
        elif risk_score >= 4:
            colors.append('#f39c12')  # Orange - High
        else:
            colors.append('#2ecc71')  # Green - Low
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers+text',
        marker=dict(
            size=20,
            color=colors,
            line=dict(width=2, color='white')
        ),
        text=texts,
        textposition='top center',
        hovertemplate='%{text}<br>Probability: %{x}<br>Severity: %{y}<extra></extra>'
    ))
    
    # Add background zones
    fig.add_shape(type="rect", x0=0.5, y0=2.5, x1=1.5, y1=3.5, fillcolor="rgba(46, 204, 113, 0.2)", line_width=0)
    fig.add_shape(type="rect", x0=2.5, y0=0.5, x1=3.5, y1=1.5, fillcolor="rgba(46, 204, 113, 0.2)", line_width=0)
    fig.add_shape(type="rect", x0=2.5, y0=2.5, x1=3.5, y1=3.5, fillcolor="rgba(231, 76, 60, 0.2)", line_width=0)
    
    fig.update_layout(
        title={
            'text': '⚠️ Ma trận Đánh giá Rủi ro',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Xác suất xảy ra',
        yaxis_title='Mức độ nghiêm trọng',
        xaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Thấp', 'Trung bình', 'Cao'], range=[0.5, 3.5]),
        yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Thấp', 'Trung bình', 'Cao'], range=[0.5, 3.5]),
        height=450
    )
    
    return fig


def create_action_timeline(action_plan: List[Dict]) -> go.Figure:
    """
    Tạo Timeline cho Action Plan
    
    Args:
        action_plan: List các actions với timeline
    
    Returns:
        Plotly Figure object
    """
    if not action_plan:
        fig = go.Figure()
        fig.add_annotation(text="Không có kế hoạch hành động", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Group actions by timeline
    timeline_groups = {}
    for action in action_plan:
        timeline = action.get('timeline', 'Q1 2026')
        if timeline not in timeline_groups:
            timeline_groups[timeline] = []
        timeline_groups[timeline].append(action)
    
    # Sort timelines
    sorted_timelines = sorted(timeline_groups.keys())
    
    # Create horizontal bar chart
    actions = []
    priorities = []
    colors = []
    timelines = []
    
    color_map = {
        'Leverage Strength': '#2ecc71',
        'Address Weakness': '#e74c3c',
        'Capture Opportunity': '#3498db',
        'Mitigate Threat': '#f39c12'
    }
    
    for action in action_plan[:15]:  # Limit to 15 actions
        actions.append(action.get('action', 'N/A'))  # Full text for display
        priorities.append(action.get('priority', 10))
        colors.append(color_map.get(action.get('type', ''), '#95a5a6'))
        timelines.append(action.get('timeline', 'N/A'))
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=actions[::-1],  # Reverse for proper display
        x=priorities[::-1],
        orientation='h',
        marker=dict(color=colors[::-1]),
        text=timelines[::-1],
        textposition='inside',
        hovertemplate='%{y}<br>Priority: %{x}<br>Timeline: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': 'Kế hoạch Hành động theo Ưu tiên',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis_title='Mức độ Ưu tiên',
        yaxis_title='',
        height=max(500, len(actions) * 40),
        margin=dict(l=350, r=40, t=60, b=60),  # Wide left margin for full text
        showlegend=False,
        xaxis=dict(range=[0, max(priorities) + 1])
    )

    
    return fig

def extract_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tự động trích xuất dữ liệu giá từ DataFrame nếu có
    
    Returns:
        DataFrame columns: ['Món', 'Giá của bạn', 'Giá đối thủ'] hoặc Empty DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    # 1. Tìm cột Item/Product
    # Thêm keywords 'name', 'desc' để fallback nếu cột 'Item' bị loại do là ID
    # Thêm unaccented keywords: 'ten mon', 'san pham'
    item_keywords = ['product', 'item', 'dish', 'menu', 'món', 'tên món', 'sản phẩm', 'food', 'drink', 'name', 'tên', 'desc', 'mô tả', 'ten mon', 'san pham']
    item_candidates = []
    
    debug_rejections = [] # DEBUG

    for col in df.columns:
        col_lower = col.lower()
        # Exclude ID/Code columns by Name
        exclude_match = [x for x in ['code', 'id', 'mã', 'stt', 'no.', 'order', '_no', '_id'] if x in col_lower]
        if exclude_match:
            debug_rejections.append(f"Col '{col}' rejected by name filter: {exclude_match}")
            continue
            
        if any(k in col_lower for k in item_keywords) and df[col].dtype == 'object':
            # Critical: Check CONTENT to avoid numeric IDs that escaped name filter
            try:
                # Sample 50 values (increased from 20)
                sample = df[col].dropna().head(50)
                if len(sample) > 0:
                    # Check if mostly numeric
                    numeric_ratio = pd.to_numeric(sample, errors='coerce').notna().mean()
                    
                    # Log debug info
                    # debug_rejections.append(f"Candidate '{col}': numeric_ratio={numeric_ratio:.2f}")
                    
                    if numeric_ratio > 0.5: # Strict threshold: If >50% numeric, it's NOT a name
                         debug_rejections.append(f"Col '{col}' rejected by content (numeric ratio {numeric_ratio:.2f})")
                         continue
                         
                    # Check overlap with ID patterns (uuid, long numbers)
                    if sample.astype(str).str.match(r'^[0-9a-fA-F\-]{10,}$').mean() > 0.5:
                         debug_rejections.append(f"Col '{col}' rejected by UUID pattern")
                         continue
                         
                else:
                    debug_rejections.append(f"Col '{col}' rejected: Empty sample")
            except Exception as e:
                debug_rejections.append(f"Col '{col}' error: {str(e)}")
                pass
            
            # Add to candidates
            item_candidates.append(col)
        else:
             pass
    
    # DEBUG: Show columns and rejections
    # st.write("DEBUG Columns:", df.columns.tolist())
    # st.write("DEBUG Rejections:", debug_rejections)
            
    # 2. Tìm cột Price Candidates
    # Thêm unaccented keywords: 'gia', 'don gia'
    price_keywords = ['price', 'cost', 'amount', 'giá', 'đơn giá', 'chi phí', 'tiền', 'gia', 'don gia', 'gia_ban']
    price_candidates = []
    
    for col in df.columns:
        if any(k in col.lower() for k in price_keywords):
             # Price column basic validation
             try:
                if df[col].dtype == 'object':
                     sample = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                     valid_count = pd.to_numeric(sample, errors='coerce').notna().sum()
                else:
                     valid_count = df[col].notna().sum()
                
                if valid_count > 0:
                     price_candidates.append(col)
             except:
                continue
                
    # 3. Enhanced Strategy: Coalesce Columns (Gộp cột)
    # Vì dữ liệu có thể đến từ nhiều nguồn (Menu file dùng 'Item', Competitor file dùng 'ten_mon')
    # Chúng ta sẽ tìm cặp tốt nhất, NHƯNG sau đó fillna bằng các cặp khác
    
    best_item = None
    best_price = None
    max_overlap = -1
    
    # 3a. Find Best Pair first (as primary)
    for i_col in item_candidates:
        for p_col in price_candidates:
            if i_col == p_col:
                continue
            overlap_count = (df[i_col].notna() & df[p_col].notna()).sum()
            if overlap_count > max_overlap:
                max_overlap = overlap_count
                best_item = i_col
                best_price = p_col
    
    if not best_item or not best_price:
        # Fallback info
        # if hasattr(st, 'warning'):
        #      st.warning(f"Không tìm thấy cặp cột Item-Price phù hợp. Candidates: Item={len(item_candidates)}, Price={len(price_candidates)}")
        return pd.DataFrame()

    # 3b. Create Coalesced Columns
    # Copy data from best pair
    df['_Final_Item'] = df[best_item]
    df['_Final_Price'] = df[best_price]
    
    # Try to fill gaps with other candidates
    # Sort other candidates by overlap density? Or just iterate
    for i_col in item_candidates:
        if i_col != best_item:
             df['_Final_Item'] = df['_Final_Item'].fillna(df[i_col])
             
    for p_col in price_candidates:
        if p_col != best_price:
             # Clean price before coalesce?
             # For simplicity, just coalesce raw values, cleaning happens later
             df['_Final_Price'] = df['_Final_Price'].fillna(df[p_col])
             
    item_col = '_Final_Item'
    price_col = '_Final_Price'
                
    if not item_col or not price_col:
        return pd.DataFrame()
        
    # 3. Clean Price Data
    df_clean = df.copy()
    
    # Convert price to numeric
    # Convert price to numeric
    if df_clean[price_col].dtype == 'object':
        # Handle 'k' suffix (e.g. 25k -> 25000)
        df_clean[price_col] = df_clean[price_col].astype(str).str.lower().str.replace('k', '000')
        
        df_clean[price_col] = pd.to_numeric(
            df_clean[price_col].str.replace(r'[^\d]', '', regex=True), 
            errors='coerce'
        )
    
    # Handle small numbers logic (e.g. 27 -> 27000)
    # If price is small (e.g. < 1000), assume it's in thousands
    if pd.api.types.is_numeric_dtype(df_clean[price_col]):
        df_clean[price_col] = df_clean[price_col].apply(lambda x: x * 1000 if 0 < x < 1000 else x)
    
    df_clean = df_clean.dropna(subset=[item_col, price_col])
    
    # --- 3.5 Heuristic: Override Source based on Item Name ---
    # User feedback: "tên sp nào có ten my_shop.... thì là của mình"
    # Logic: Check if item name contains keywords, if so, force update Source
    
    # Keywords
    myshop_keywords = r'my_shop|myshop|của mình|my store|shop mình'
    comp_keywords = r'competitor|đối thủ|thị trường|quán khác'
    
    item_series = df_clean[item_col].astype(str).str.lower()
    
    mask_myshop = item_series.str.contains(myshop_keywords, regex=True)
    if mask_myshop.any():
        df_clean.loc[mask_myshop, 'source'] = 'MY_SHOP'
        
    mask_competitor = item_series.str.contains(comp_keywords, regex=True)
    if mask_competitor.any():
        df_clean.loc[mask_competitor, 'source'] = 'COMPETITOR'
    # ---------------------------------------------------------
    
    # 4. Aggregate
    # Chuẩn hóa tên món (lowercase, strip)
    df_clean['item_norm'] = df_clean[item_col].astype(str).str.lower().str.strip()
    
    # Calculate avg price per item per source
    if 'source' in df_clean.columns:
        agg = df_clean.groupby(['item_norm', 'source'])[price_col].mean().reset_index()
        # Pivot to get My Shop vs Competitor
        pivot = agg.pivot(index='item_norm', columns='source', values=price_col).reset_index()
    else:
        # If no source, assume all is My Shop
        agg = df_clean.groupby('item_norm')[price_col].mean().reset_index()
        pivot = agg
        pivot['MY_SHOP'] = pivot[price_col]
        
    # Rename columns to match expected format
    result_df = pd.DataFrame()
    result_df['Món'] = pivot['item_norm'].str.title()
    
    # Robust Source Mapping using partial match
    # Pivot columns are the unique values from 'source' column
    pivot_cols = [c for c in pivot.columns if c != 'item_norm']
    
    my_price_col = None
    comp_price_col = None
    
    # 1. Try to find My Shop column
    for col in pivot_cols:
        col_str = str(col).lower()
        if any(freq in col_str for freq in ['my_shop', 'myshop', 'my shop', 'của mình', 'shop', 'store', 'me']):
            if not any(neg in col_str for neg in ['bạn', 'competitor', 'đối thủ', 'other']): # avoid false positives if needed
                 my_price_col = col
                 break
    
    # 2. Try to find Competitor column (STRICT)
    for col in pivot_cols:
        col_str = str(col).lower()
        if col != my_price_col:
            if any(freq in col_str for freq in ['competitor', 'đối thủ', 'thị trường', 'quán khác', 'other']):
                comp_price_col = col
                break
    
    # 3. Fallback strategies
    if not my_price_col and not comp_price_col:
        # If no keywords matched, default to My Shop for the first column
        # Assumption: User uploads their own data first/primarily
        if pivot_cols:
            my_price_col = pivot_cols[0]
            
    elif not my_price_col and comp_price_col:
        # If we have a Competitor column, check if there are others that could be My Shop
        remaining = [c for c in pivot_cols if c != comp_price_col]
        if remaining:
            my_price_col = remaining[0]

    # Assign values
    if my_price_col:
        result_df['Giá của bạn'] = pivot[my_price_col]
    else:
        result_df['Giá của bạn'] = 0
        
    if comp_price_col:
        result_df['Giá đối thủ'] = pivot[comp_price_col]
    else:
         result_df['Giá đối thủ'] = 0
        
    # Fill NaN with 0
    result_df = result_df.fillna(0)
    
    return result_df[['Món', 'Giá của bạn', 'Giá đối thủ']]

def create_price_comparison_chart(price_data: pd.DataFrame):
    """
    Tạo biểu đồ so sánh giá dạng Grouped Bar Chart
    
    Args:
        price_data: DataFrame với columns ['Món', 'Giá của bạn', 'Giá đối thủ']
    """
    if price_data is None or price_data.empty:
        return None
        
    fig = go.Figure()
    
    # Giá của bạn
    fig.add_trace(go.Bar(
        x=price_data['Món'],
        y=price_data['Giá của bạn'],
        name='Giá của bạn',
        marker_color='#3498db',
        text=price_data['Giá của bạn'].apply(lambda x: f"{x:,.0f}"),
        textposition='auto'
    ))
    
    # Giá đối thủ
    fig.add_trace(go.Bar(
        x=price_data['Món'],
        y=price_data['Giá đối thủ'],
        name='Giá đối thủ',
        marker_color='#e74c3c',
        text=price_data['Giá đối thủ'].apply(lambda x: f"{x:,.0f}"),
        textposition='auto'
    ))
    
    # Calculate % difference for tooltip
    # Safe division
    diff_pct = ((price_data['Giá của bạn'] - price_data['Giá đối thủ']) / price_data['Giá đối thủ'].replace(0, 1) * 100).round(1)
    
    fig.update_layout(
        title='So sánh Giá sản phẩm',
        xaxis_title='Sản phẩm',
        yaxis_title='Giá (VND)',
        barmode='group',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

