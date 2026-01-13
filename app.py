"""
SWOT AI Analyzer - Ứng dụng phân tích SWOT từ đánh giá khách hàng F&B
Sử dụng Streamlit và Google Gemini 2.5 Flash
"""
import streamlit as st
import pandas as pd
from ai_analyzer import analyze_swot_with_gemini, validate_swot_result
from utils import (
    load_and_clean_data,
    prepare_reviews_for_ai,
    create_swot_pie_chart,
    create_impact_bar_chart,
    format_swot_table_data
)
from excel_export import export_swot_to_excel
import json
import time

# Cấu hình trang
st.set_page_config(
    page_title="SWOT AI Analyzer",
    page_icon="📊",
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
    </style>
""", unsafe_allow_html=True)


def main():
    """Hàm chính của ứng dụng"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 SWOT AI Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Phân tích SWOT thông minh từ đánh giá khách hàng F&B</p>', unsafe_allow_html=True)
    
    # Sidebar - Hướng dẫn
    with st.sidebar:
        with st.expander("📖 Hướng dẫn sử dụng", expanded=False):
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
                
                progress_bar.progress(1.0)
                status_text.empty()
                progress_bar.empty()
                
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
                                my_shop_result = analyze_swot_with_gemini(my_shop_data, analysis_type='FULL')
                                results['my_shop'] = my_shop_result
                            
                            # Phân tích COMPETITOR (đầy đủ SWOT từ đánh giá về đối thủ)
                            if competitor_data:
                                status_text.text(f"📊 Đang phân tích SWOT đầy đủ của đối thủ ({len(competitor_data)} reviews)...")
                                progress_bar.progress(60)
                                competitor_result = analyze_swot_with_gemini(competitor_data, analysis_type='FULL')
                                results['competitor'] = competitor_result
                            
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
                            
                            result = analyze_swot_with_gemini(reviews_list)
                            st.session_state['analysis_mode'] = 'combined'
                        
                        progress_bar.progress(60)
                        
                        # Validate kết quả
                        if not validate_swot_result(result):
                            st.error("❌ Kết quả từ AI không đúng định dạng. Vui lòng thử lại.")
                            st.json(result)  # Hiển thị để debug
                            return
                        
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
        
        st.markdown("---")
        st.header("📊 Kết quả phân tích SWOT")
        
        # Executive Summary
        st.subheader("📝 Tóm tắt điều hành")
        st.info(result.get("Executive_Summary", "Không có tóm tắt"))
        
        # Biểu đồ
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Phân bố SWOT")
            pie_chart = create_swot_pie_chart(result)
            st.plotly_chart(pie_chart, use_container_width=True)
        
        with col2:
            st.subheader("📊 Mức độ Ảnh hưởng/Rủi ro")
            bar_chart = create_impact_bar_chart(result)
            st.plotly_chart(bar_chart, use_container_width=True)
        
        # Chi tiết từng nhóm SWOT
        swot = result.get("SWOT_Analysis", {})
        analysis_mode = st.session_state.get('analysis_mode', 'combined')
        
        if analysis_mode == 'separate':
            # Hiển thị 2 cột: SWOT đầy đủ của mình và SWOT đầy đủ của đối thủ
            st.markdown("---")
            st.subheader("📊 SWOT Phân tích riêng biệt")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🏪 SWOT CỦA MÌNH")
                
                my_shop_swot = result.get("My_Shop_SWOT", {})
                
                # Strengths
                st.markdown("#### 💪 Strengths (Điểm mạnh)")
                my_strengths = my_shop_swot.get("Strengths", [])
                if my_strengths:
                    st.dataframe(
                        pd.DataFrame(my_strengths),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có điểm mạnh nào được xác định")
                
                # Weaknesses
                st.markdown("#### ⚠️ Weaknesses (Điểm yếu)")
                my_weaknesses = my_shop_swot.get("Weaknesses", [])
                if my_weaknesses:
                    st.dataframe(
                        pd.DataFrame(my_weaknesses),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có điểm yếu nào được xác định")
                
                # Opportunities
                st.markdown("#### 🎯 Opportunities (Cơ hội)")
                my_opportunities = my_shop_swot.get("Opportunities", [])
                if my_opportunities:
                    st.dataframe(
                        pd.DataFrame(my_opportunities),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có cơ hội nào được xác định")
                
                # Threats
                st.markdown("#### 🔥 Threats (Thách thức)")
                my_threats = my_shop_swot.get("Threats", [])
                if my_threats:
                    st.dataframe(
                        pd.DataFrame(my_threats),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có thách thức nào được xác định")
            
            with col2:
                st.markdown("### ⚔️ SWOT CỦA ĐỐI THỦ")
                
                competitor_swot = result.get("Competitor_SWOT", {})
                
                # Strengths
                st.markdown("#### 💪 Strengths (Điểm mạnh)")
                comp_strengths = competitor_swot.get("Strengths", [])
                if comp_strengths:
                    st.dataframe(
                        pd.DataFrame(comp_strengths),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có điểm mạnh nào được xác định")
                
                # Weaknesses
                st.markdown("#### ⚠️ Weaknesses (Điểm yếu)")
                comp_weaknesses = competitor_swot.get("Weaknesses", [])
                if comp_weaknesses:
                    st.dataframe(
                        pd.DataFrame(comp_weaknesses),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có điểm yếu nào được xác định")
                
                # Opportunities
                st.markdown("#### 🎯 Opportunities (Cơ hội)")
                comp_opportunities = competitor_swot.get("Opportunities", [])
                if comp_opportunities:
                    st.dataframe(
                        pd.DataFrame(comp_opportunities),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có cơ hội nào được xác định")
                
                # Threats
                st.markdown("#### 🔥 Threats (Thách thức)")
                comp_threats = competitor_swot.get("Threats", [])
                if comp_threats:
                    st.dataframe(
                        pd.DataFrame(comp_threats),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Không có thách thức nào được xác định")
        else:
            # Hiển thị dạng tổng hợp (như cũ)
            # Strengths
            st.markdown("---")
            st.subheader("💪 Strengths (Điểm mạnh)")
            strengths = format_swot_table_data(result, "Strengths")
            if strengths:
                st.dataframe(
                    pd.DataFrame(strengths),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Không có điểm mạnh nào được xác định")
            
            # Weaknesses
            st.subheader("⚠️ Weaknesses (Điểm yếu)")
            weaknesses = format_swot_table_data(result, "Weaknesses")
            if weaknesses:
                st.dataframe(
                    pd.DataFrame(weaknesses),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Không có điểm yếu nào được xác định")
            
            # Opportunities
            st.subheader("🎯 Opportunities (Cơ hội)")
            opportunities = format_swot_table_data(result, "Opportunities")
            if opportunities:
                st.dataframe(
                    pd.DataFrame(opportunities),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Không có cơ hội nào được xác định")
            
            # Threats
            st.subheader("🔥 Threats (Thách thức)")
            threats = format_swot_table_data(result, "Threats")
            if threats:
                st.dataframe(
                    pd.DataFrame(threats),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Không có thách thức nào được xác định")
        
        # Export kết quả
        st.markdown("---")
        st.subheader("💾 Export kết quả")
        
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
                    label="📊 Tải xuống báo cáo Excel (có biểu đồ)",
                    data=excel_file,
                    file_name="swot_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo file Excel: {str(e)}")
                st.exception(e)
        
        with col2:
            # Export JSON
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Tải xuống kết quả JSON",
                data=json_str,
                file_name="swot_analysis_result.json",
                mime="application/json"
            )
        
        # Nút phân tích lại
        if st.button("🔄 Phân tích lại với dữ liệu mới", use_container_width=True):
            if 'swot_result' in st.session_state:
                del st.session_state['swot_result']
            if 'df' in st.session_state:
                del st.session_state['df']
            st.rerun()


if __name__ == "__main__":
    main()
