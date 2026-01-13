# 📊 SWOT AI Analyzer

Ứng dụng Web phân tích SWOT thông minh từ đánh giá khách hàng F&B, sử dụng Streamlit và Google Gemini 2.5 Flash.

## 🎯 Tính năng

- ✅ Upload và xử lý file Excel/CSV chứa đánh giá khách hàng
- ✅ Phân tích cảm xúc tự động (Sentiment Analysis)
- ✅ Trích xuất và gom nhóm chủ đề (Aspect Extraction & Clustering)
- ✅ Xây dựng mô hình SWOT tự động
- ✅ Trực quan hóa kết quả với biểu đồ tương tác
- ✅ Export kết quả dưới dạng JSON

## 🏗️ Kiến trúc

Ứng dụng được chia thành 3 lớp chính:

1. **Frontend (Giao diện)**: Streamlit UI
2. **Backend (Xử lý)**: Python với Pandas
3. **AI Layer (Trí tuệ nhân tạo)**: Google Gemini 2.5 Flash API

### Luồng dữ liệu

```
User Upload → Data Cleaning → Prompt Engineering → Gemini API → JSON Parsing → Visualization
```

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Google Gemini API Key

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd SWOT
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình API Key

Tạo file `.env` và thêm Gemini API Key của bạn:

```bash
# Tạo file .env
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

Hoặc tạo file `.env` thủ công với nội dung:

```
GEMINI_API_KEY=your_actual_api_key_here
```

Lấy API key tại: https://makersuite.google.com/app/apikey

### 4. (Tùy chọn) Kiểm tra setup

Chạy script kiểm tra:

```bash
python setup.py
```

### 5. Chạy ứng dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

### 6. Test với dữ liệu mẫu

File `sample_data.csv` đã được cung cấp sẵn để test. Bạn có thể upload file này để thử nghiệm ứng dụng.

## 📁 Cấu trúc dữ liệu đầu vào

File Excel/CSV cần có 2 cột:

| Review | Source |
|--------|--------|
| "Đồ uống rất ngon, giá hợp lý" | MY_SHOP |
| "Nhân viên phục vụ chậm" | MY_SHOP |
| "Quán đối thủ có wifi tốt hơn" | COMPETITOR |

### Quy ước Source:

- `MY_SHOP` hoặc `CỦA MÌNH`: Đánh giá về quán của bạn
- `COMPETITOR` hoặc `ĐỐI THỦ`: Đánh giá về đối thủ cạnh tranh

## 🔍 Logic phân tích SWOT

Ứng dụng tự động phân loại đánh giá theo quy tắc:

- **MY_SHOP + Tích cực** → **STRENGTHS** (Điểm mạnh)
- **MY_SHOP + Tiêu cực** → **WEAKNESSES** (Điểm yếu)
- **COMPETITOR + Tiêu cực** → **OPPORTUNITIES** (Cơ hội)
- **COMPETITOR + Tích cực** → **THREATS** (Thách thức)

## 📊 Định dạng kết quả

Kết quả được trả về dưới dạng JSON với cấu trúc:

```json
{
  "SWOT_Analysis": {
    "Strengths": [
      {
        "topic": "Chất lượng đồ uống",
        "description": "Mô tả chi tiết...",
        "impact": "High"
      }
    ],
    "Weaknesses": [
      {
        "topic": "Thái độ nhân viên",
        "description": "Mô tả chi tiết...",
        "root_cause": "Nguyên nhân gốc rễ",
        "impact": "Medium"
      }
    ],
    "Opportunities": [
      {
        "topic": "Điểm yếu đối thủ",
        "description": "Mô tả chi tiết...",
        "action_idea": "Gợi ý hành động"
      }
    ],
    "Threats": [
      {
        "topic": "Điểm mạnh đối thủ",
        "description": "Mô tả chi tiết...",
        "risk_level": "High"
      }
    ]
  },
  "Executive_Summary": "Tóm tắt ngắn gọn..."
}
```

## 📂 Cấu trúc project

```
SWOT/
├── app.py                 # File chính Streamlit
├── ai_analyzer.py         # Module xử lý Gemini API
├── utils.py               # Utility functions (data processing, visualization)
├── requirements.txt       # Dependencies
├── .env.example          # Template cho API key
├── .env                  # File chứa API key (không commit)
└── README.md             # Tài liệu này
```

## 🛠️ Công nghệ sử dụng

- **Streamlit**: Framework web app
- **Google Gemini 2.5 Flash**: LLM cho phân tích SWOT
- **Pandas**: Xử lý dữ liệu
- **Plotly**: Trực quan hóa biểu đồ
- **Python-dotenv**: Quản lý environment variables

## ⚙️ Cấu hình Model

Ứng dụng tự động thử các model theo thứ tự ưu tiên:
1. `gemini-2.5-flash` (mới nhất)
2. `gemini-2.0-flash-exp`
3. `gemini-1.5-flash` (fallback)

Nếu bạn muốn chỉ định model cụ thể, mở file `ai_analyzer.py` và sửa danh sách `model_names`.

## ⚠️ Lưu ý

- File dữ liệu lớn (>200 reviews) sẽ được lấy mẫu ngẫu nhiên để tối ưu hiệu suất
- Đảm bảo file `.env` không được commit lên Git (đã có trong `.gitignore`)
- API key có giới hạn rate limit, vui lòng sử dụng hợp lý
- Model `gemini-1.5-flash` là model ổn định và nhanh, phù hợp cho ứng dụng này

## 📝 License

MIT License

## 👤 Tác giả

SWOT AI Analyzer - Phân tích SWOT thông minh cho F&B
