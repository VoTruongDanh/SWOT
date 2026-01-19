"""
SWOT AI Analyzer - Ứng dụng phân tích SWOT từ đánh giá khách hàng F&B
Sử dụng Streamlit và Google Gemini 2.5 Flash
Enterprise Edition - Phân tích chiến lược toàn diện
"""
import streamlit as st
import pandas as pd
from ai_analyzer import analyze_swot_with_gemini, validate_swot_result
from utils import (
    load_and_clean_data,
    prepare_reviews_for_ai,
    create_swot_pie_chart,
    create_impact_bar_chart,
    format_swot_table_data,
    # Enterprise visualizations
    create_tows_matrix_chart,
    create_priority_heatmap,
    create_competitive_radar,
    create_risk_matrix,
    create_action_timeline,
    create_price_comparison_chart,
    extract_price_data
)
from strategic_analyzer import StrategicAnalyzer, enrich_swot_with_scores
from excel_export import export_swot_to_excel
import json
import time


# Cấu hình trang
st.set_page_config(
    page_title="SWOT AI Analyzer",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .swot-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .strength { border-left: 5px solid #2ecc71; }
    .weakness { border-left: 5px solid #e74c3c; }
    .opportunity { border-left: 5px solid #3498db; }
    .threat { border-left: 5px solid #f39c12; }
    
    /* CSS cho dataframe - text wrapping */
    .stDataFrame div[data-testid="stDataFrameResizable"] {
        width: 100% !important;
    }
    .stDataFrame [data-testid="StyledDataFrame"] td {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        max-width: 300px !important;
    }
    .stDataFrame [data-testid="StyledDataFrame"] th {
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)



def main():
    """Hàm chính của ứng dụng"""
    
    # Header
    st.markdown('<h1 class="main-header">SWOT AI Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Phân tích SWOT thông minh từ đánh giá khách hàng F&B</p>', unsafe_allow_html=True)
    
    # Sidebar - Hướng dẫn
    with st.sidebar:
        with st.expander("Hướng dẫn sử dụng", expanded=False):
            st.markdown("""
            ### 1. Chuẩn bị file dữ liệu
            
            **Tùy chọn 1: Có cột Source rõ ràng**
            - **Cột đánh giá**: `Review`, `Đánh giá`, `Comment`, `Content`, v.v.
            - **Cột Source**: 
              - `MY_SHOP` hoặc `CỦA MÌNH` - Đánh giá về quán của bạn
              - `COMPETITOR` hoặc `ĐỐI THỦ` - Đánh giá về đối thủ
            
            **Tùy chọn 2: Không có cột Source**
            - Hệ thống **tự động phát hiện từ tên file**:
              - `my_shop`, `myshop`, `của mình` → MY_SHOP
              - `competitor`, `đối thủ`, `starbucks`, `highlands` → COMPETITOR
              - Không phát hiện được → Mặc định COMPETITOR
            
            **Cột bổ sung (tùy chọn):**
            - `Price`, `Rating`, `Menu`, `Date`, `User`
            
            ### 2. Upload file
            
            - Nhấn **"Browse files"** hoặc kéo thả file
            - **Có thể upload nhiều file cùng lúc**
            - Hệ thống tự động phát hiện và làm sạch dữ liệu
            
            ### 3. Chọn chế độ phân tích
            
            **Tổng hợp**: 1 báo cáo SWOT gộp chung
            
            **Phân tích riêng**: 2 cột SWOT riêng biệt
            - Cột trái: SWOT của mình (S, W, O, T)
            - Cột phải: SWOT của đối thủ (S, W, O, T)
            
            ### 4. Xem kết quả
            
            - 📝 Tóm tắt điều hành
            - 📈 Biểu đồ phân bố SWOT
            - 📊 Bảng chi tiết từng nhóm
            
            ### 5. Export kết quả
            
            - 📊 **Excel**: Báo cáo đầy đủ với biểu đồ (7 sheets)
            - 📥 **JSON**: Dữ liệu thô
            """)
        
        st.markdown("---")
        
        with st.expander("⚙️ Cài đặt", expanded=False):
            st.markdown("""
            **Yêu cầu:**
            - Python 3.10+
            - Google Gemini API Key
            
            **Cài đặt:**
            ```bash
            pip install -r requirements.txt
            ```
            
            **Cấu hình API Key:**
            
            **Khi chạy local:**
            - Tạo file `.env`:
            ```
            GEMINI_API_KEY=your_api_key_here
            ```
            - Hoặc tạo file `.streamlit/secrets.toml`:
            ```
            GEMINI_API_KEY = "your_api_key_here"
            ```
            
            **Khi deploy lên Streamlit Cloud:**
            1. Vào Settings > Secrets trong Streamlit Cloud
            2. Thêm secret:
            ```
            GEMINI_API_KEY = "your_api_key_here"
            ```
            
            **Lưu ý:** 
            - File `.env` phải UTF-8 (không BOM)
            - Không commit API key lên Git
            
            Lấy API key: https://makersuite.google.com/app/apikey
            """)
    
    # Upload file
    st.header("📁 Upload dữ liệu")
    
    # Cho phép upload nhiều file
    uploaded_files = st.file_uploader(
        "Chọn một hoặc nhiều file Excel/CSV chứa đánh giá khách hàng",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Bạn có thể upload nhiều file cùng lúc. Hệ thống sẽ tự động tổng hợp tất cả dữ liệu. Hệ thống sẽ tự động phát hiện cột đánh giá. Nếu không có cột Source, tất cả đánh giá sẽ được coi là về quán của bạn."
    )
    
    # --- Price Comparison Input ---
    # Disabled by user request
    # with st.expander("💰 Nhập liệu So sánh Giá (Menu Pricing)", expanded=False):
    #     st.info("Nhập danh sách các món chính để so sánh giá với đối thủ. Dữ liệu này sẽ được dùng để vẽ biểu đồ so sánh.")
        
    #     # Initialize session state for price data if not exists
    #     if 'price_comparison_data' not in st.session_state:
    #         st.session_state['price_comparison_data'] = pd.DataFrame(
    #             columns=['Món', 'Giá của bạn', 'Giá đối thủ']
    #         )
        
    #     # Data Editor
    #     edited_price_df = st.data_editor(
    #         st.session_state['price_comparison_data'],
    #         num_rows="dynamic",
    #         column_config={
    #             "Món": st.column_config.TextColumn(
    #                 "Tên món",
    #                 help="Ví dụ: Cà phê sữa, Trà đào...",
    #                 required=True
    #             ),
    #             "Giá của bạn": st.column_config.NumberColumn(
    #                 "Giá của bạn (VNĐ)",
    #                 min_value=0,
    #                 step=1000,
    #                 format="%d"
    #             ),
    #             "Giá đối thủ": st.column_config.NumberColumn(
    #                 "Giá đối thủ (VNĐ)",
    #                 min_value=0,
    #                 step=1000,
    #                 format="%d"
    #             )
    #         },
    #         hide_index=True,
    #         use_container_width=True
    #     )
        
    #     # Update session state
    #     st.session_state['price_comparison_data'] = edited_price_df
        
    #     if st.button("🔄 Quét lại giá từ dữ liệu đã tải"):
    #         if 'df' in st.session_state and not st.session_state['df'].empty:
    #             price_df = extract_price_data(st.session_state['df'])
    #             if not price_df.empty:
    #                 st.session_state['price_comparison_data'] = price_df
    #                 st.success(f"✅ Đã tìm thấy {len(price_df)} món!")
    #                 st.rerun()
    #             else:
    #                 st.warning("⚠️ Không tìm thấy thông tin giá trong dữ liệu hiện tại.")
    #         else:
    #             st.warning("⚠️ Vui lòng upload file dữ liệu trước.")

    # ------------------------------
    
    if uploaded_files and len(uploaded_files) > 0:
        try:
            # Load và tổng hợp dữ liệu từ nhiều file
            all_dataframes = []
            file_info = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"🔄 Đang xử lý file {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                progress_bar.progress((idx) / len(uploaded_files))
                
                try:
                    df_file = load_and_clean_data(uploaded_file, file_name=uploaded_file.name)
                    all_dataframes.append(df_file)
                    file_info.append({
                        'name': uploaded_file.name,
                        'rows': len(df_file),
                        'my_shop': len(df_file[df_file['source'] == 'MY_SHOP']),
                        'competitor': len(df_file[df_file['source'] == 'COMPETITOR'])
                    })
                except Exception as e:
                    st.warning(f"⚠️ Lỗi khi xử lý file {uploaded_file.name}: {str(e)}")
                    continue
            
            # Lưu file_info vào session state để dùng cho export
            if file_info:
                st.session_state['file_info'] = file_info
            
            # Xóa file_summaries cũ nếu có
            if 'file_summaries' in st.session_state:
                st.session_state['file_summaries'] = []
            
            # Tổng hợp tất cả dữ liệu
            if all_dataframes:
                status_text.text("🔄 Đang tổng hợp dữ liệu từ tất cả các file...")
                progress_bar.progress(0.9)
                
                df = pd.concat(all_dataframes, ignore_index=True)
                
                # Loại bỏ duplicate nếu có (dựa trên nội dung review)
                df = df.drop_duplicates(subset=['review'], keep='first')
                st.session_state['df'] = df
                
                progress_bar.empty()
                
                # --- Auto Extract Prices ---
                # Disabled by user request
                # try:
                #     price_df = extract_price_data(df)
                #     if not price_df.empty:
                #         # Only update if current data is empty or user wants to overwrite?
                #         # For now, let's Auto-Fill if empty, or merge?
                #         # Simplest: Update and notify
                #         st.session_state['price_comparison_data'] = price_df
                #         st.success(f"✅ Đã tự động trích xuất giá của {len(price_df)} món từ file! Kiểm tra tab 'So sánh Giá' hoặc phần 'Nhập liệu' ở trên.")
                # except Exception as ex:
                #     print(f"Error extracting prices: {ex}")
                # ---------------------------
                
                st.success(f"✅ Đã tải thành công {len(df)} đánh giá từ {len(uploaded_files)} file(s)")
                
                # Hiển thị thông tin file trong một expander gọn gàng
                file_summaries = st.session_state.get('file_summaries', [])
                if file_summaries:
                    with st.expander(f"📋 Chi tiết {len(file_summaries)} file đã tải", expanded=False):
                        # Tạo bảng tóm tắt
                        summary_data = []
                        for fs in file_summaries:
                            review_info = f"{fs['review_cols_count']} cột" if fs['review_cols_count'] > 1 else "1 cột"
                            additional_info = f"{fs['additional_cols_count']} cột bổ sung" if fs['additional_cols_count'] > 0 else "-"
                            summary_data.append({
                                '📄 Tên file': fs['name'],
                                '📊 Cột đánh giá': review_info,
                                '🏷️ Source': fs['source'],
                                '➕ Cột bổ sung': additional_info if additional_info else '-'
                            })
                        
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        # Hiển thị chi tiết từng file trong expander con
                        st.markdown("---")
                        st.markdown("### 📄 Chi tiết từng file")
                        for fs in file_summaries:
                            with st.expander(f"📄 {fs['name']}", expanded=False):
                                info_text = f"✅ **Đã phát hiện:**\n"
                                info_text += f"- Cột đánh giá chính: **{fs['review_col']}**\n"
                                
                                if fs.get('combined_cols_info'):
                                    info_text += f"- ℹ️ Đã kết hợp {fs['combined_cols_info']['count']} cột đánh giá: {', '.join(fs['combined_cols_info']['cols'])}\n"
                                elif fs.get('other_cols'):
                                    info_text += f"- Các cột đánh giá khác: {', '.join(fs['other_cols'])}\n"
                                
                                info_text += f"- Cột nguồn: **{fs['source']}**\n"
                                
                                if fs.get('additional_cols'):
                                    info_text += f"- **Các thông tin bổ sung:**\n"
                                    for key, col in fs['additional_cols'].items():
                                        info_text += f"  • {key.upper()}: {col}\n"
                                
                                info_text += f"- Tổng số cột trong file: {fs['total_cols']}"
                                st.markdown(info_text)
                                
                                if fs.get('has_warning'):
                                    st.warning(f"⚠️ Không tìm thấy cột phân loại nguồn (Source) và không phát hiện shop từ tên file.")
                                    st.info(f"💡 File sẽ được phân loại là **COMPETITOR** (đối thủ). Nếu đây là dữ liệu về quán của bạn, vui lòng đổi tên file có chứa 'my_shop' hoặc thêm cột Source vào file.")
                
                # Hiển thị thống kê từng file (tối ưu)
                with st.expander(f"📊 Thống kê từng file ({len(file_info)} file)", expanded=False):
                    stats_df = pd.DataFrame(file_info)
                    
                    # Tính tổng
                    total_rows = stats_df['rows'].sum()
                    total_my_shop = stats_df['my_shop'].sum()
                    total_competitor = stats_df['competitor'].sum()
                    
                    # Hiển thị tổng quan
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📁 Tổng số file", len(file_info))
                    with col2:
                        st.metric("📝 Tổng đánh giá", f"{total_rows:,}")
                    with col3:
                        st.metric("🏪 MY_SHOP", f"{total_my_shop:,}", 
                                 delta=f"{total_my_shop/total_rows*100:.1f}%" if total_rows > 0 else "0%")
                    with col4:
                        st.metric("⚔️ COMPETITOR", f"{total_competitor:,}",
                                 delta=f"{total_competitor/total_rows*100:.1f}%" if total_rows > 0 else "0%")
                    
                    st.markdown("---")
                    
                    # Hiển thị bảng chi tiết với format đẹp hơn
                    stats_df_display = stats_df.copy()
                    stats_df_display.columns = ['📄 Tên file', '📊 Số dòng', '🏪 MY_SHOP', '⚔️ COMPETITOR']
                    
                    # Thêm cột tỷ lệ
                    stats_df_display['📈 Tỷ lệ MY_SHOP'] = stats_df_display.apply(
                        lambda row: f"{row['🏪 MY_SHOP']/row['📊 Số dòng']*100:.1f}%" if row['📊 Số dòng'] > 0 else "0%",
                        axis=1
                    )
                    stats_df_display['📈 Tỷ lệ COMPETITOR'] = stats_df_display.apply(
                        lambda row: f"{row['⚔️ COMPETITOR']/row['📊 Số dòng']*100:.1f}%" if row['📊 Số dòng'] > 0 else "0%",
                        axis=1
                    )
                    
                    # Sắp xếp theo số dòng giảm dần
                    stats_df_display = stats_df_display.sort_values('📊 Số dòng', ascending=False)
                    
                    st.dataframe(
                        stats_df_display,
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                    
                    # Biểu đồ phân bố
                    st.markdown("### 📊 Biểu đồ phân bố")
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        # Pie chart phân bố MY_SHOP vs COMPETITOR
                        import plotly.express as px
                        pie_data = pd.DataFrame({
                            'Loại': ['MY_SHOP', 'COMPETITOR'],
                            'Số lượng': [total_my_shop, total_competitor]
                        })
                        fig_pie = px.pie(
                            pie_data, 
                            values='Số lượng', 
                            names='Loại',
                            title='Phân bố MY_SHOP vs COMPETITOR',
                            color_discrete_map={'MY_SHOP': '#2ecc71', 'COMPETITOR': '#e74c3c'}
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with chart_col2:
                        # Bar chart số lượng theo file
                        top_files = stats_df.head(10).copy()  # Top 10 file
                        # Rút ngắn tên file nếu quá dài
                        top_files['name_short'] = top_files['name'].apply(
                            lambda x: x[:30] + '...' if len(x) > 30 else x
                        )
                        
                        fig_bar = px.bar(
                            top_files,
                            x='name_short',
                            y='rows',
                            title='Top 10 file có nhiều đánh giá nhất',
                            labels={'name_short': 'Tên file', 'rows': 'Số đánh giá'},
                            color='rows',
                            color_continuous_scale='Blues'
                        )
                        fig_bar.update_layout(
                            xaxis=dict(tickangle=-45),
                            height=400
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
            
                # Hiển thị preview dữ liệu
                with st.expander("👀 Xem trước dữ liệu tổng hợp", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tổng số đánh giá", f"{len(df):,}")
                    with col2:
                        my_shop_count = len(df[df['source'] == 'MY_SHOP'])
                        st.metric("Đánh giá về quán mình", f"{my_shop_count:,}")
                    with col3:
                        competitor_count = len(df[df['source'] == 'COMPETITOR'])
                        st.metric("Đánh giá về đối thủ", f"{competitor_count:,}")
                
                # Tùy chọn phân tích
                st.markdown("### ⚙️ Tùy chọn phân tích")
                analysis_mode = st.radio(
                    "Chọn chế độ phân tích:",
                    ["Tổng hợp (SWOT của mình + Đối thủ)", "Phân tích riêng (SWOT của mình và SWOT của đối thủ)"],
                    help="Tổng hợp: Tạo 1 báo cáo SWOT. Phân tích riêng: Tạo 2 báo cáo SWOT riêng biệt."
                )
                
                # Nút phân tích
                if st.button("🚀 Bắt đầu phân tích SWOT", type="primary", use_container_width=True):
                    # Chuẩn bị dữ liệu cho AI
                    reviews_list = prepare_reviews_for_ai(df)
                    
                    # Tạo progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        if "Phân tích riêng" in analysis_mode:
                            # Phân tích riêng: SWOT đầy đủ của mình và SWOT đầy đủ của đối thủ
                            status_text.text("🤖 AI đang phân tích SWOT đầy đủ của mình và đối thủ riêng biệt...")
                            progress_bar.progress(10)
                            
                            # Tách dữ liệu
                            my_shop_data = [r for r in reviews_list if r.get('source') == 'MY_SHOP']
                            competitor_data = [r for r in reviews_list if r.get('source') == 'COMPETITOR']
                            
                            results = {}
                            
                            # Phân tích MY_SHOP (đầy đủ SWOT từ đánh giá về mình)
                            if my_shop_data:
                                status_text.text(f"📊 Đang phân tích SWOT đầy đủ của mình ({len(my_shop_data)} reviews)...")
                                progress_bar.progress(30)
                                try:
                                    my_shop_result = analyze_swot_with_gemini(my_shop_data, analysis_type='FULL', batch_size=500)
                                    results['my_shop'] = my_shop_result
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi phân tích MY_SHOP: {str(e)}")
                                    raise
                            
                            # Phân tích COMPETITOR (đầy đủ SWOT từ đánh giá về đối thủ)
                            if competitor_data:
                                status_text.text(f"📊 Đang phân tích SWOT đầy đủ của đối thủ ({len(competitor_data)} reviews)...")
                                progress_bar.progress(60)
                                try:
                                    competitor_result = analyze_swot_with_gemini(competitor_data, analysis_type='FULL', batch_size=500)
                                    results['competitor'] = competitor_result
                                except Exception as e:
                                    st.error(f"❌ Lỗi khi phân tích COMPETITOR: {str(e)}")
                                    raise
                            
                            # Kết hợp kết quả - giữ nguyên cả 2 SWOT riêng biệt
                            progress_bar.progress(80)
                            status_text.text("🔄 Đang tổng hợp kết quả...")
                            
                            combined_result = {
                                "SWOT_Analysis": {
                                    # Gộp tất cả để hiển thị biểu đồ tổng hợp
                                    "Strengths": results.get('my_shop', {}).get('SWOT_Analysis', {}).get('Strengths', []) + 
                                                results.get('competitor', {}).get('SWOT_Analysis', {}).get('Strengths', []),
                                    "Weaknesses": results.get('my_shop', {}).get('SWOT_Analysis', {}).get('Weaknesses', []) + 
                                                 results.get('competitor', {}).get('SWOT_Analysis', {}).get('Weaknesses', []),
                                    "Opportunities": results.get('my_shop', {}).get('SWOT_Analysis', {}).get('Opportunities', []) + 
                                                     results.get('competitor', {}).get('SWOT_Analysis', {}).get('Opportunities', []),
                                    "Threats": results.get('my_shop', {}).get('SWOT_Analysis', {}).get('Threats', []) + 
                                              results.get('competitor', {}).get('SWOT_Analysis', {}).get('Threats', [])
                                },
                                "Executive_Summary": "",
                                # Lưu SWOT riêng biệt để hiển thị 2 cột
                                "My_Shop_SWOT": results.get('my_shop', {}).get('SWOT_Analysis', {}),
                                "Competitor_SWOT": results.get('competitor', {}).get('SWOT_Analysis', {}),
                                "My_Shop_Summary": results.get('my_shop', {}).get('Executive_Summary', ''),
                                "Competitor_Summary": results.get('competitor', {}).get('Executive_Summary', '')
                            }
                            
                            # Tổng hợp Executive Summary
                            summaries = []
                            if combined_result["My_Shop_Summary"]:
                                summaries.append(f"SWOT của mình: {combined_result['My_Shop_Summary']}")
                            if combined_result["Competitor_Summary"]:
                                summaries.append(f"SWOT của đối thủ: {combined_result['Competitor_Summary']}")
                            
                            if summaries:
                                combined_result["Executive_Summary"] = " | ".join(summaries)
                            
                            result = combined_result
                            st.session_state['analysis_mode'] = 'separate'
                        else:
                            # Phân tích tổng hợp (như cũ)
                            status_text.text("🤖 AI đang phân tích dữ liệu tổng hợp...")
                            progress_bar.progress(20)
                            
                            # Thêm timeout cho toàn bộ quá trình
                            import signal
                            import threading
                            
                            result = None
                            error_occurred = [False]
                            error_message = [None]
                            
                            def analyze_with_timeout():
                                try:
                                    nonlocal result
                                    result = analyze_swot_with_gemini(reviews_list)
                                except Exception as e:
                                    error_occurred[0] = True
                                    error_message[0] = str(e)
                            
                            # Chạy trong thread với timeout
                            thread = threading.Thread(target=analyze_with_timeout)
                            thread.daemon = True
                            thread.start()
                            
                            # Đợi với timeout 5 phút
                            thread.join(timeout=300)
                            
                            if thread.is_alive():
                                raise TimeoutError(
                                    "⏱️ Phân tích mất quá nhiều thời gian (>5 phút). "
                                    "Vui lòng thử lại với ít dữ liệu hơn hoặc kiểm tra kết nối mạng."
                                )
                            
                            if error_occurred[0]:
                                raise Exception(f"Lỗi khi phân tích: {error_message[0]}")
                            
                            if result is None:
                                raise Exception("Không nhận được kết quả từ AI. Vui lòng thử lại.")
                            
                            st.session_state['analysis_mode'] = 'combined'
                        
                        progress_bar.progress(60)
                        
                        # Validate kết quả
                        if not validate_swot_result(result):
                            st.error("❌ Kết quả từ AI không đúng định dạng. Vui lòng thử lại.")
                            st.json(result)  # Hiển thị để debug
                            return
                        
                        # Enterprise: Enrich SWOT with strategic analysis
                        progress_bar.progress(70)
                        status_text.text("🔄 Đang tạo phân tích chiến lược enterprise...")
                        
                        try:
                            result = enrich_swot_with_scores(result)
                            st.session_state['enterprise_mode'] = True
                        except Exception as e:
                            st.warning(f"⚠️ Không thể tạo phân tích enterprise: {str(e)}")
                            st.session_state['enterprise_mode'] = False
                        
                        progress_bar.progress(80)
                        status_text.text("✅ Phân tích hoàn tất!")
                        progress_bar.progress(100)
                        time.sleep(0.5)
                        
                        # Lưu kết quả vào session state
                        st.session_state['swot_result'] = result
                        st.session_state['df'] = df
                        
                        # Reload để hiển thị kết quả
                        st.rerun()

                    
                    except Exception as e:
                        st.error(f"❌ Lỗi khi phân tích: {str(e)}")
                        st.exception(e)
                        progress_bar.empty()
                        status_text.empty()
        
        except Exception as e:
            st.error(f"❌ Lỗi khi xử lý file: {str(e)}")
            st.exception(e)
    
    # Hiển thị kết quả SWOT
    if 'swot_result' in st.session_state:
        result = st.session_state['swot_result']
        df = st.session_state.get('df', pd.DataFrame())
        enterprise_mode = st.session_state.get('enterprise_mode', False)
        
        st.markdown("---")
        st.header("📊 Kết quả phân tích SWOT Enterprise")
        
        # Executive Summary
        st.subheader("📝 Tóm tắt điều hành")
        st.info(result.get("Executive_Summary", "Không có tóm tắt"))
        
        # Key Insights (Enterprise)
        key_insights = result.get("Key_Insights", [])
        if key_insights:
            st.subheader("Key Insights")
            for idx, insight in enumerate(key_insights, 1):
                st.markdown(f"**{idx}.** {insight}")
        
        # Biểu đồ cơ bản
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Phân bố SWOT")
            pie_chart = create_swot_pie_chart(result)
            st.plotly_chart(pie_chart, use_container_width=True)
        
        with col2:
            st.subheader("Mức độ Ảnh hưởng/Rủi ro")
            bar_chart = create_impact_bar_chart(result)
            st.plotly_chart(bar_chart, use_container_width=True)
        
        # ========== ENTERPRISE ANALYTICS TABS ==========
        if enterprise_mode:
            st.markdown("---")
            st.header("Phân tích Chiến lược Enterprise")
            
            enterprise_tabs = st.tabs([
                "Ma trận TOWS", 
                "Ma trận Ưu tiên",
                "Kế hoạch Hành động",
                "So sánh Cạnh tranh",
                "Đánh giá Rủi ro",
                # "So sánh Giá"
            ])
            
            # Tab 1: TOWS Matrix
            with enterprise_tabs[0]:
                st.subheader("Ma trận TOWS - Chiến lược Kết hợp")
                
                tows = result.get('TOWS_Matrix', {})
                
                if tows:
                    tows_chart = create_tows_matrix_chart(tows)
                    st.plotly_chart(tows_chart, use_container_width=True)
                    
                    # Display strategies in 2x2 grid
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### SO Strategies (Tấn công)")
                        so_strategies = tows.get('SO_Strategies', [])
                        if so_strategies:
                            for s in so_strategies[:5]:
                                st.markdown(f"• {s.get('strategy', '')}")
                        else:
                            st.info("Không có chiến lược SO")
                        
                        st.markdown("#### WO Strategies (Chuyển đổi)")
                        wo_strategies = tows.get('WO_Strategies', [])
                        if wo_strategies:
                            for s in wo_strategies[:5]:
                                st.markdown(f"• {s.get('strategy', '')}")
                        else:
                            st.info("Không có chiến lược WO")
                    
                    with col2:
                        st.markdown("#### ST Strategies (Đa dạng hóa)")
                        st_strategies = tows.get('ST_Strategies', [])
                        if st_strategies:
                            for s in st_strategies[:5]:
                                st.markdown(f"• {s.get('strategy', '')}")
                        else:
                            st.info("Không có chiến lược ST")
                        
                        st.markdown("#### WT Strategies (Phòng thủ)")
                        wt_strategies = tows.get('WT_Strategies', [])
                        if wt_strategies:
                            for s in wt_strategies[:5]:
                                st.markdown(f"• {s.get('strategy', '')}")
                        else:
                            st.info("Không có chiến lược WT")
                else:
                    st.info("Không có dữ liệu TOWS Matrix")
            
            # Tab 2: Priority Matrix
            with enterprise_tabs[1]:
                st.subheader("Ma trận Ưu tiên")
                
                priority_chart = create_priority_heatmap(result)
                st.plotly_chart(priority_chart, use_container_width=True)
                
                st.markdown("""
                **Hướng dẫn đọc biểu đồ:**
                - **Ưu tiên cao** (góc trên phải): Impact cao + Priority score cao → Cần hành động ngay
                - **Quick Wins** (góc dưới phải): Impact cao + Priority thấp → Dễ thực hiện, tác động lớn
                - **Theo dõi** (góc trên trái): Impact thấp + Priority cao → Theo dõi và đánh giá lại
                - **Backlog** (góc dưới trái): Impact thấp + Priority thấp → Đưa vào backlog
                """)
            
            # Tab 3: Action Plan
            with enterprise_tabs[2]:
                st.subheader("Kế hoạch Hành động Chiến lược")
                
                action_plan = result.get('Strategic_Action_Plan', [])
                
                if action_plan:
                    action_chart = create_action_timeline(action_plan)
                    st.plotly_chart(action_chart, use_container_width=True)
                    
                    # Display action table
                    st.markdown("### Chi tiết Kế hoạch")
                    
                    action_df = pd.DataFrame([{
                        'Ưu tiên': a.get('priority', ''),
                        'Hành động': a.get('action', ''),
                        'Loại': a.get('type', ''),
                        'Timeline': a.get('timeline', ''),
                        'Người phụ trách': a.get('owner_role', ''),
                        'Đầu tư': a.get('estimated_investment', ''),
                        'Trạng thái': a.get('status', 'Planned')
                    } for a in action_plan])
                    
                    st.dataframe(
                        action_df,
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                else:
                    st.info("Không có kế hoạch hành động")
            
            # Tab 4: Competitive Analysis
            with enterprise_tabs[3]:
                st.subheader("So sánh Vị thế Cạnh tranh")
                
                competitive = result.get('Competitive_Analysis', {})
                
                if competitive:
                    radar_chart = create_competitive_radar(competitive)
                    st.plotly_chart(radar_chart, use_container_width=True)
                    
                    # Show scores comparison
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        my_overall = competitive.get('my_overall', 5)
                        st.metric("Điểm tổng thể của bạn", f"{my_overall}/10")
                    
                    with col2:
                        comp_overall = competitive.get('competitor_overall', 5)
                        st.metric("Điểm đối thủ trung bình", f"{comp_overall}/10")
                    
                    with col3:
                        advantage = competitive.get('competitive_advantage', False)
                        if advantage:
                            st.success("Bạn đang có lợi thế cạnh tranh!")
                        else:
                            st.warning("Đối thủ đang có lợi thế")
                    
                    # Advantage gaps
                    st.markdown("### Khoảng cách theo Tiêu chí")
                    gaps = competitive.get('advantage_gaps', {})
                    if gaps:
                        gap_df = pd.DataFrame([{
                            'Tiêu chí': k.capitalize(),
                            'Khoảng cách': v,
                            'Đánh giá': 'Bạn dẫn' if v > 0 else ('Đối thủ dẫn' if v < 0 else 'Ngang bằng')
                        } for k, v in gaps.items()])
                        st.dataframe(gap_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Không có dữ liệu cạnh tranh")
            
            # Tab 5: Risk Assessment
            with enterprise_tabs[4]:
                st.subheader("Ma trận Đánh giá Rủi ro")
                
                risk_data = result.get('Risk_Assessment', result.get('SWOT_Analysis', {}).get('Threats', []))
                
                if risk_data:
                    risk_chart = create_risk_matrix(risk_data)
                    st.plotly_chart(risk_chart, use_container_width=True)
                    
                    # Risk table
                    st.markdown("### Chi tiết Rủi ro")
                    risk_df = pd.DataFrame([{
                        'Rủi ro': r.get('topic', ''),
                        'Xác suất': r.get('probability', r.get('risk_level', 'Medium')),
                        'Mức độ': r.get('severity', r.get('risk_level', 'Medium')),
                        'Điểm rủi ro': r.get('composite_risk_score', 'N/A'),
                        'Phân loại': r.get('risk_category', 'Medium'),
                        'Khuyến nghị': r.get('recommendation', r.get('contingency_plan', 'N/A'))
                    } for r in risk_data])
                    
                    st.dataframe(
                        risk_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có dữ liệu rủi ro")
            
            # Tab 6: Price Comparisons
            # with enterprise_tabs[5]:
            #     st.subheader("So sánh Giá Sản phẩm")
                
            #     price_data = st.session_state.get('price_comparison_data')
                
            #     if price_data is not None and not price_data.empty:
            #         # Remove empty rows
            #         valid_price_data = price_data.dropna(subset=['Món'])
            #         valid_price_data = valid_price_data[valid_price_data['Món'] != '']
                    
            #         if not valid_price_data.empty:
            #             price_chart = create_price_comparison_chart(valid_price_data)
            #             st.plotly_chart(price_chart, use_container_width=True)
                        
            #             # Simple insights
            #             avg_diff = ((valid_price_data['Giá của bạn'].sum() - valid_price_data['Giá đối thủ'].sum()) / valid_price_data['Giá đối thủ'].sum() * 100) if valid_price_data['Giá đối thủ'].sum() > 0 else 0
                        
            #             if avg_diff < -5:
            #                 st.success(f"💡 Giá của bạn thấp hơn đối thủ trung bình **{abs(avg_diff):.1f}%** - Lợi thế cạnh tranh về chi phí!")
            #             elif avg_diff > 5:
            #                 st.warning(f"💡 Giá của bạn cao hơn đối thủ trung bình **{avg_diff:.1f}%** - Cần chứng minh giá trị vượt trội (Premium positioning).")
            #             else:
            #                 st.info(f"💡 Giá của bạn tương đương đối thủ (chênh lệch **{avg_diff:.1f}%**) - Cạnh tranh trực tiếp.")
            #         else:
            #             st.info("Vui lòng nhập dữ liệu giá trong phần 'Nhập liệu So sánh Giá' ở trên.")
            #     else:
            #         st.info("Vui lòng nhập dữ liệu giá trong phần 'Nhập liệu So sánh Giá' ở trên để xem biểu đồ.")
        
        st.markdown("---")
        
        # Chi tiết từng nhóm SWOT
        swot = result.get("SWOT_Analysis", {})
        analysis_mode = st.session_state.get('analysis_mode', 'combined')

        
        if analysis_mode == 'separate':
            # Hiển thị 2 cột: SWOT đầy đủ của mình và SWOT đầy đủ của đối thủ
            st.markdown("---")
            st.subheader("SWOT Phân tích riêng biệt")
            
            # Helper function để tạo card cho mỗi SWOT item (dùng cho cả 2 cột)
            def display_swot_item_cards(items: list, category: str):
                """Hiển thị SWOT items dạng expandable cards"""
                if not items:
                    st.info(f"Không có {category.lower()} nào được xác định")
                    return
                
                for item in items:
                    topic = item.get('topic', 'N/A')
                    description = item.get('description', 'N/A')
                    priority = item.get('priority_score', '')
                    impact = item.get('impact') or item.get('risk_level', '')
                    
                    title = f"**{topic}**"
                    if priority:
                        title += f" ({priority})"
                    if impact:
                        title += f" • {impact}"
                    
                    with st.expander(title, expanded=False):
                        st.markdown(f"**Mô tả:** {description}")
                        
                        if category == "Strengths" and item.get('leverage_strategy'):
                            st.markdown(f"**Chiến lược tận dụng:** {item.get('leverage_strategy')}")
                        
                        if category == "Weaknesses":
                            if item.get('root_cause'):
                                st.markdown(f"**Nguyên nhân:** {item.get('root_cause')}")
                            if item.get('mitigation_plan'):
                                st.markdown(f"**Kế hoạch khắc phục:** {item.get('mitigation_plan')}")
                        
                        if category == "Opportunities" and item.get('action_idea'):
                            st.markdown(f"**Gợi ý hành động:** {item.get('action_idea')}")
                        
                        if category == "Threats" and item.get('contingency_plan'):
                            st.markdown(f"**Kế hoạch ứng phó:** {item.get('contingency_plan')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### SWOT CỦA MÌNH")
                my_shop_swot = result.get("My_Shop_SWOT", {})
                
                st.markdown("#### Strengths (Điểm mạnh)")
                display_swot_item_cards(my_shop_swot.get("Strengths", []), "Strengths")
                
                st.markdown("#### Weaknesses (Điểm yếu)")
                display_swot_item_cards(my_shop_swot.get("Weaknesses", []), "Weaknesses")
                
                st.markdown("#### Opportunities (Cơ hội)")
                display_swot_item_cards(my_shop_swot.get("Opportunities", []), "Opportunities")
                
                st.markdown("#### Threats (Thách thức)")
                display_swot_item_cards(my_shop_swot.get("Threats", []), "Threats")
            
            with col2:
                st.markdown("### SWOT CỦA ĐỐI THỦ")
                competitor_swot = result.get("Competitor_SWOT", {})
                
                st.markdown("#### Strengths (Điểm mạnh)")
                display_swot_item_cards(competitor_swot.get("Strengths", []), "Strengths")
                
                st.markdown("#### Weaknesses (Điểm yếu)")
                display_swot_item_cards(competitor_swot.get("Weaknesses", []), "Weaknesses")
                
                st.markdown("#### Opportunities (Cơ hội)")
                display_swot_item_cards(competitor_swot.get("Opportunities", []), "Opportunities")
                
                st.markdown("#### Threats (Thách thức)")
                display_swot_item_cards(competitor_swot.get("Threats", []), "Threats")

        else:
            # Hiển thị dạng tổng hợp với Cards (để text wrap đúng)
            swot_data = result.get("SWOT_Analysis", {})
            
            # Helper function để tạo card cho mỗi SWOT item
            def display_swot_cards(items: list, category: str):
                """Hiển thị SWOT items dạng expandable cards"""
                if not items:
                    st.info(f"Không có {category.lower()} nào được xác định")
                    return
                
                for idx, item in enumerate(items, 1):
                    topic = item.get('topic', 'N/A')
                    description = item.get('description', 'N/A')
                    priority = item.get('priority_score', '')
                    impact = item.get('impact') or item.get('risk_level', '')
                    
                    # Tạo title ngắn gọn - clean version
                    title = f"**{topic}**"
                    if priority:
                        title += f" ({priority})"
                    if impact:
                        title += f" • {impact}"
                    
                    with st.expander(title, expanded=False):
                        st.markdown(f"**Mô tả:** {description}")
                        
                        # Hiển thị các fields khác tùy theo category
                        if category == "Strengths":
                            if item.get('leverage_strategy'):
                                st.markdown(f"**Chiến lược tận dụng:** {item.get('leverage_strategy')}")
                            if item.get('kpi_metrics'):
                                kpis = item.get('kpi_metrics')
                                if isinstance(kpis, list):
                                    st.markdown(f"**KPIs:** {', '.join(kpis)}")
                        
                        elif category == "Weaknesses":
                            if item.get('root_cause'):
                                st.markdown(f"**Nguyên nhân gốc rễ:** {item.get('root_cause')}")
                            if item.get('mitigation_plan'):
                                st.markdown(f"**Kế hoạch khắc phục:** {item.get('mitigation_plan')}")
                            if item.get('improvement_cost'):
                                st.markdown(f"**Chi phí cải thiện:** {item.get('improvement_cost')}")
                        
                        elif category == "Opportunities":
                            if item.get('action_idea'):
                                st.markdown(f"**Gợi ý hành động:** {item.get('action_idea')}")
                            col1, col2 = st.columns(2)
                            with col1:
                                if item.get('market_size'):
                                    st.markdown(f"**Quy mô:** {item.get('market_size')}")
                            with col2:
                                if item.get('time_to_capture'):
                                    st.markdown(f"**Thời gian:** {item.get('time_to_capture')}")
                        
                        elif category == "Threats":
                            col1, col2 = st.columns(2)
                            with col1:
                                if item.get('probability'):
                                    st.markdown(f"**Xác suất:** {item.get('probability')}")
                            with col2:
                                if item.get('severity'):
                                    st.markdown(f"**Mức độ:** {item.get('severity')}")
                            if item.get('contingency_plan'):
                                st.markdown(f"**Kế hoạch ứng phó:** {item.get('contingency_plan')}")
            
            # Strengths
            st.markdown("---")
            st.subheader("Strengths (Điểm mạnh)")
            display_swot_cards(swot_data.get("Strengths", []), "Strengths")
            
            # Weaknesses
            st.subheader("Weaknesses (Điểm yếu)")
            display_swot_cards(swot_data.get("Weaknesses", []), "Weaknesses")
            
            # Opportunities
            st.subheader("Opportunities (Cơ hội)")
            display_swot_cards(swot_data.get("Opportunities", []), "Opportunities")
            
            # Threats
            st.subheader("Threats (Thách thức)")
            display_swot_cards(swot_data.get("Threats", []), "Threats")




        
        # Export kết quả
        st.markdown("---")
        st.subheader("Export kết quả")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export Excel với biểu đồ
            try:
                excel_file = export_swot_to_excel(
                    result, 
                    df=df if 'df' in st.session_state else None,
                    file_info=st.session_state.get('file_info', None)
                )
                st.download_button(
                    label="Tải xuống báo cáo Excel (có biểu đồ)",
                    data=excel_file,
                    file_name="swot_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Lỗi khi tạo file Excel: {str(e)}")
                st.exception(e)
        
        with col2:
            # Export JSON
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            st.download_button(
                label="Tải xuống kết quả JSON",
                data=json_str,
                file_name="swot_analysis_result.json",
                mime="application/json"
            )
        
        # Nút phân tích lại
        if st.button("Phân tích lại với dữ liệu mới", use_container_width=True):
            if 'swot_result' in st.session_state:
                del st.session_state['swot_result']
            if 'df' in st.session_state:
                del st.session_state['df']
            st.rerun()


if __name__ == "__main__":
    main()
