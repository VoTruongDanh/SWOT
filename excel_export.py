"""
Module xuất báo cáo SWOT ra file Excel với biểu đồ và format chuyên nghiệp
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter
from io import BytesIO
import base64
from typing import Dict, Any, List
import streamlit as st


def create_swot_charts(swot_data: Dict[str, Any]) -> Dict[str, BytesIO]:
    """
    Tạo các biểu đồ từ dữ liệu SWOT và lưu dưới dạng hình ảnh
    
    Args:
        swot_data: Dict chứa SWOT_Analysis
    
    Returns:
        Dict chứa các BytesIO object của biểu đồ
    """
    swot = swot_data.get("SWOT_Analysis", {})
    charts = {}
    
    # 1. Pie chart phân bố SWOT
    categories = ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']
    counts = [
        len(swot.get("Strengths", [])),
        len(swot.get("Weaknesses", [])),
        len(swot.get("Opportunities", [])),
        len(swot.get("Threats", []))
    ]
    
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12']
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=categories,
        values=counts,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent+value'
    )])
    fig_pie.update_layout(
        title='Phân bố SWOT Analysis',
        width=600,
        height=400,
        showlegend=True
    )
    
    # Export pie chart
    pie_img = fig_pie.to_image(format="png", width=600, height=400)
    charts['pie_chart'] = BytesIO(pie_img)
    
    # 2. Bar chart Impact/Risk Level
    impact_levels = {'High': 0, 'Medium': 0, 'Low': 0}
    
    for item in swot.get("Strengths", []) + swot.get("Weaknesses", []):
        impact = item.get("impact", "Medium")
        if impact in impact_levels:
            impact_levels[impact] += 1
    
    for item in swot.get("Threats", []):
        risk = item.get("risk_level", "Medium")
        if risk in impact_levels:
            impact_levels[risk] += 1
    
    fig_bar = go.Figure(data=[
        go.Bar(
            x=list(impact_levels.keys()),
            y=list(impact_levels.values()),
            marker_color=['#e74c3c', '#f39c12', '#2ecc71'],
            text=list(impact_levels.values()),
            textposition='auto'
        )
    ])
    fig_bar.update_layout(
        title='Phân bố Mức độ Ảnh hưởng/Rủi ro',
        xaxis_title='Mức độ',
        yaxis_title='Số lượng',
        width=600,
        height=400
    )
    
    # Export bar chart
    bar_img = fig_bar.to_image(format="png", width=600, height=400)
    charts['bar_chart'] = BytesIO(bar_img)
    
    return charts


def export_swot_to_excel(swot_data: Dict[str, Any], df: pd.DataFrame = None, 
                         file_info: List[Dict] = None) -> BytesIO:
    """
    Xuất báo cáo SWOT ra file Excel với format chuyên nghiệp
    
    Args:
        swot_data: Dict chứa SWOT_Analysis và Executive_Summary
        df: DataFrame chứa dữ liệu đánh giá (optional)
        file_info: List thông tin các file (optional)
    
    Returns:
        BytesIO object chứa file Excel
    """
    wb = Workbook()
    wb.remove(wb.active)  # Xóa sheet mặc định
    
    # Tạo các biểu đồ
    charts = create_swot_charts(swot_data)
    
    # ========== SHEET 1: EXECUTIVE SUMMARY ==========
    ws_summary = wb.create_sheet("Tóm tắt Điều hành", 0)
    
    # Header
    ws_summary.merge_cells('A1:D1')
    cell = ws_summary['A1']
    cell.value = "📊 BÁO CÁO PHÂN TÍCH SWOT"
    cell.font = Font(name='Arial', size=16, bold=True, color='FFFFFF')
    cell.fill = PatternFill(start_color='1f77b4', end_color='1f77b4', fill_type='solid')
    cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_summary.row_dimensions[1].height = 30
    
    # Executive Summary
    ws_summary['A3'] = "📝 TÓM TẮT ĐIỀU HÀNH"
    ws_summary['A3'].font = Font(name='Arial', size=14, bold=True)
    ws_summary.row_dimensions[3].height = 25
    
    ws_summary['A4'] = swot_data.get("Executive_Summary", "Không có tóm tắt")
    ws_summary['A4'].font = Font(name='Arial', size=11)
    ws_summary['A4'].alignment = Alignment(wrap_text=True, vertical='top')
    ws_summary.merge_cells('A4:D10')
    ws_summary.row_dimensions[4].height = 100
    
    # Thống kê tổng quan
    ws_summary['A12'] = "📊 THỐNG KÊ TỔNG QUAN"
    ws_summary['A12'].font = Font(name='Arial', size=14, bold=True)
    
    swot = swot_data.get("SWOT_Analysis", {})
    stats = [
        ["Chỉ số", "Số lượng"],
        ["Strengths (Điểm mạnh)", len(swot.get("Strengths", []))],
        ["Weaknesses (Điểm yếu)", len(swot.get("Weaknesses", []))],
        ["Opportunities (Cơ hội)", len(swot.get("Opportunities", []))],
        ["Threats (Thách thức)", len(swot.get("Threats", []))],
    ]
    
    for row_idx, row_data in enumerate(stats, start=13):
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws_summary.cell(row=row_idx, column=col_idx)
            cell.value = value
            if row_idx == 13:  # Header row
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
    
    # Chèn biểu đồ Pie
    if 'pie_chart' in charts:
        charts['pie_chart'].seek(0)
        img = Image(charts['pie_chart'])
        img.width = 400
        img.height = 300
        ws_summary.add_image(img, 'F3')
    
    # Chèn biểu đồ Bar
    if 'bar_chart' in charts:
        charts['bar_chart'].seek(0)
        img = Image(charts['bar_chart'])
        img.width = 400
        img.height = 300
        ws_summary.add_image(img, 'F13')
    
    # Điều chỉnh độ rộng cột
    ws_summary.column_dimensions['A'].width = 30
    ws_summary.column_dimensions['B'].width = 15
    ws_summary.column_dimensions['C'].width = 15
    ws_summary.column_dimensions['D'].width = 15
    
    # ========== SHEET 2: STRENGTHS ==========
    ws_strengths = wb.create_sheet("Strengths")
    _create_swot_sheet(ws_strengths, "💪 STRENGTHS (ĐIỂM MẠNH)", 
                       swot.get("Strengths", []), ['topic', 'description', 'impact'])
    
    # ========== SHEET 3: WEAKNESSES ==========
    ws_weaknesses = wb.create_sheet("Weaknesses")
    _create_swot_sheet(ws_weaknesses, "⚠️ WEAKNESSES (ĐIỂM YẾU)", 
                       swot.get("Weaknesses", []), ['topic', 'description', 'root_cause', 'impact'])
    
    # ========== SHEET 4: OPPORTUNITIES ==========
    ws_opportunities = wb.create_sheet("Opportunities")
    _create_swot_sheet(ws_opportunities, "🎯 OPPORTUNITIES (CƠ HỘI)", 
                       swot.get("Opportunities", []), ['topic', 'description', 'action_idea'])
    
    # ========== SHEET 5: THREATS ==========
    ws_threats = wb.create_sheet("Threats")
    _create_swot_sheet(ws_threats, "🔥 THREATS (THÁCH THỨC)", 
                       swot.get("Threats", []), ['topic', 'description', 'risk_level'])
    
    # ========== SHEET 6: DỮ LIỆU GỐC (nếu có) ==========
    if df is not None and len(df) > 0:
        ws_data = wb.create_sheet("Dữ liệu Gốc")
        
        # Header
        ws_data['A1'] = "📋 DỮ LIỆU ĐÁNH GIÁ GỐC"
        ws_data['A1'].font = Font(name='Arial', size=14, bold=True)
        ws_data.row_dimensions[1].height = 25
        
        # Ghi dữ liệu
        for col_idx, col_name in enumerate(df.columns, start=1):
            cell = ws_data.cell(row=2, column=col_idx)
            cell.value = col_name
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        
        for row_idx, row_data in enumerate(df.values, start=3):
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws_data.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # Điều chỉnh độ rộng cột
        from openpyxl.utils import get_column_letter
        for col_idx in range(1, len(df.columns) + 1):
            col_letter = get_column_letter(col_idx)
            ws_data.column_dimensions[col_letter].width = 30
    
    # ========== SHEET 7: THỐNG KÊ FILE (nếu có) ==========
    if file_info:
        ws_files = wb.create_sheet("Thống kê File")
        
        # Header
        ws_files['A1'] = "📁 THỐNG KÊ TỪNG FILE"
        ws_files['A1'].font = Font(name='Arial', size=14, bold=True)
        ws_files.row_dimensions[1].height = 25
        
        # Ghi dữ liệu
        files_df = pd.DataFrame(file_info)
        headers = ['Tên file', 'Số dòng', 'MY_SHOP', 'COMPETITOR']
        
        for col_idx, header in enumerate(headers, start=1):
            cell = ws_files.cell(row=2, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        
        for row_idx, (_, row_data) in enumerate(files_df.iterrows(), start=3):
            for col_idx, value in enumerate(row_data.values, start=1):
                cell = ws_files.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
        
        # Điều chỉnh độ rộng cột
        ws_files.column_dimensions['A'].width = 40
        for col in ['B', 'C', 'D']:
            ws_files.column_dimensions[col].width = 15
    
    # Lưu vào BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


def _create_swot_sheet(ws, title: str, items: List[Dict], columns: List[str]):
    """
    Tạo sheet cho một nhóm SWOT
    
    Args:
        ws: Worksheet object
        title: Tiêu đề sheet
        items: List các items
        columns: Danh sách các cột cần hiển thị
    """
    # Header
    ws['A1'] = title
    ws['A1'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
    ws['A1'].fill = PatternFill(start_color='1f77b4', end_color='1f77b4', fill_type='solid')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.merge_cells(f'A1:{chr(64 + len(columns))}1')
    ws.row_dimensions[1].height = 30
    
    # Column headers
    column_headers = {
        'topic': 'Chủ đề',
        'description': 'Mô tả',
        'impact': 'Mức độ ảnh hưởng',
        'root_cause': 'Nguyên nhân gốc rễ',
        'action_idea': 'Gợi ý hành động',
        'risk_level': 'Mức độ rủi ro'
    }
    
    for col_idx, col in enumerate(columns, start=1):
        cell = ws.cell(row=2, column=col_idx)
        cell.value = column_headers.get(col, col)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    # Data rows
    for row_idx, item in enumerate(items, start=3):
        for col_idx, col in enumerate(columns, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = item.get(col, '')
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
    
    # Điều chỉnh độ rộng cột
    ws.column_dimensions['A'].width = 25  # Chủ đề
    ws.column_dimensions['B'].width = 50  # Mô tả
    for col in ['C', 'D', 'E']:
        ws.column_dimensions[col].width = 25
    
    # Điều chỉnh chiều cao hàng
    for row in range(3, len(items) + 3):
        ws.row_dimensions[row].height = 60
