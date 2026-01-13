# 📊 SWOT AI Analyzer

Ứng dụng phân tích SWOT thông minh từ đánh giá khách hàng F&B sử dụng AI (Google Gemini 2.5 Flash).

## ✨ Tính năng

- 🤖 **Phân tích SWOT tự động** bằng AI từ đánh giá khách hàng
- 📁 **Upload nhiều file** cùng lúc (Excel/CSV)
- 🔍 **Tự động phát hiện cột** đánh giá và nguồn (Source)
- 📊 **2 chế độ phân tích**: Tổng hợp hoặc Phân tích riêng (SWOT của mình và SWOT của đối thủ)
- 📈 **Biểu đồ trực quan** phân bố SWOT và mức độ ảnh hưởng
- 📥 **Export báo cáo Excel** với biểu đồ và format chuyên nghiệp
- 🎯 **Phân tích đa dạng**: Hỗ trợ giá cả, rating, menu, ngày, user

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.10 trở lên
- Google Gemini API Key

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Cấu hình API Key

1. Tạo file `.env` trong thư mục gốc
2. Thêm API key vào file:

```
GEMINI_API_KEY=your_api_key_here
```

**Lưu ý:** File `.env` phải được lưu với encoding UTF-8 (không có BOM).

## 📖 Hướng dẫn sử dụng

### 1. Chuẩn bị file dữ liệu

#### Cấu trúc file Excel/CSV:

**Tùy chọn 1: Có cột Source rõ ràng**
- **Cột đánh giá**: Chứa nội dung đánh giá khách hàng
  - Tên cột có thể là: `Review`, `Đánh giá`, `Comment`, `Content`, `Nội dung`, v.v.
- **Cột Source**: Chứa nguồn đánh giá
  - Giá trị: `MY_SHOP` hoặc `CỦA MÌNH` - Đánh giá về quán của bạn
  - Giá trị: `COMPETITOR` hoặc `ĐỐI THỦ` - Đánh giá về đối thủ

**Tùy chọn 2: Không có cột Source**
- Hệ thống sẽ tự động phát hiện Source từ **tên file**:
  - File có chứa: `my_shop`, `myshop`, `của mình` → MY_SHOP
  - File có chứa: `competitor`, `đối thủ`, `starbucks`, `highlands`, `phuc long`, `katinat`, v.v. → COMPETITOR
  - Nếu không phát hiện được → Mặc định là COMPETITOR

**Các cột bổ sung (tùy chọn):**
- `Price` / `Giá` - Giá cả sản phẩm
- `Rating` / `Điểm` - Điểm đánh giá/số sao
- `Menu` / `Món` - Tên món/sản phẩm
- `Date` / `Ngày` - Ngày đánh giá
- `User` / `Người dùng` - Tên người đánh giá

**Ví dụ file CSV:**

```csv
Review,Source,Price,Rating
"Cà phê ngon, giá hợp lý",MY_SHOP,45000,5
"Nhân viên phục vụ chậm",MY_SHOP,50000,3
"Starbucks có không gian đẹp",COMPETITOR,80000,4
```

### 2. Upload file

1. Mở ứng dụng: `streamlit run app.py`
2. Nhấn nút **"Browse files"** hoặc kéo thả file vào vùng upload
3. **Có thể upload nhiều file cùng lúc** - hệ thống sẽ tự động tổng hợp
4. Hệ thống sẽ:
   - Tự động phát hiện cột đánh giá và Source
   - Làm sạch dữ liệu (loại bỏ dòng trống, chuẩn hóa)
   - Hiển thị thống kê từng file và tổng hợp

### 3. Chọn chế độ phân tích

**Chế độ 1: Tổng hợp (Mặc định)**
- Phân tích tất cả dữ liệu cùng lúc
- Tạo 1 báo cáo SWOT tổng hợp
- Phù hợp khi có cả dữ liệu MY_SHOP và COMPETITOR

**Chế độ 2: Phân tích riêng**
- Phân tích riêng SWOT của mình và SWOT của đối thủ
- Hiển thị 2 cột cạnh nhau:
  - **Cột trái**: SWOT của mình (đầy đủ S, W, O, T)
  - **Cột phải**: SWOT của đối thủ (đầy đủ S, W, O, T)
- Mỗi cột có Executive Summary riêng
- Phù hợp để so sánh trực tiếp

### 4. Xem kết quả

Sau khi phân tích, bạn sẽ thấy:

- **📝 Tóm tắt điều hành**: Executive Summary
- **📈 Biểu đồ**:
  - Pie chart: Phân bố SWOT
  - Bar chart: Mức độ Ảnh hưởng/Rủi ro
- **📊 Bảng chi tiết**: Từng nhóm SWOT với:
  - Chủ đề (Topic)
  - Mô tả chi tiết (Description)
  - Mức độ ảnh hưởng/Rủi ro (Impact/Risk Level)
  - Gợi ý hành động (Action Ideas) - cho Opportunities
  - Nguyên nhân gốc rễ (Root Cause) - cho Weaknesses

### 5. Export kết quả

**Export Excel (Khuyến nghị):**
- Nhấn **"📊 Tải xuống báo cáo Excel (có biểu đồ)"**
- File Excel bao gồm:
  - Sheet 1: Tóm tắt Điều hành + Biểu đồ
  - Sheet 2-5: Chi tiết từng nhóm SWOT (Strengths, Weaknesses, Opportunities, Threats)
  - Sheet 6: Dữ liệu gốc (nếu có)
  - Sheet 7: Thống kê từng file (nếu có)
  - Format chuyên nghiệp, sẵn sàng trình bày

**Export JSON:**
- Nhấn **"📥 Tải xuống kết quả JSON"**
- Dữ liệu thô dạng JSON để xử lý tiếp

## 🔍 Tính năng tự động phát hiện

### Phát hiện cột đánh giá

Hệ thống tự động tìm cột chứa nội dung đánh giá bằng cách:
1. Tìm theo từ khóa: `review`, `đánh giá`, `comment`, `content`, `nội dung`
2. Phân tích nội dung: Cột có nhiều text dài nhất
3. Kết hợp nhiều cột text thành 1 cột đánh giá

### Phát hiện cột Source

Hệ thống tự động tìm cột Source bằng cách:
1. Tìm theo tên cột: `source`, `nguồn`, `shop_type`, `store_type`
2. Phân tích giá trị: Tìm cột có giá trị `MY_SHOP`, `COMPETITOR`
3. Phát hiện từ tên file: Nếu không có cột Source, phân tích tên file

### Phát hiện Source từ tên file

Các từ khóa được nhận diện:

**MY_SHOP:**
- `my_shop`, `myshop`, `của mình`, `my store`, `our shop`

**COMPETITOR:**
- `competitor`, `đối thủ`, `starbucks`, `phuc long`, `highlands`, `katinat`, `trung nguyen`, v.v.

## 📊 Logic phân tích SWOT

### Chế độ Tổng hợp:
- **MY_SHOP + Tích cực** → Strengths (Điểm mạnh)
- **MY_SHOP + Tiêu cực** → Weaknesses (Điểm yếu)
- **COMPETITOR + Tiêu cực** → Opportunities (Cơ hội)
- **COMPETITOR + Tích cực** → Threats (Thách thức)

### Chế độ Phân tích riêng:

**SWOT của mình:**
- Phân tích đầy đủ S, W, O, T từ đánh giá về quán của bạn
- Strengths: Từ đánh giá tích cực
- Weaknesses: Từ đánh giá tiêu cực
- Opportunities: Cơ hội cải thiện, mở rộng
- Threats: Thách thức từ thị trường

**SWOT của đối thủ:**
- Phân tích đầy đủ S, W, O, T từ đánh giá về đối thủ
- Strengths: Điểm mạnh của đối thủ
- Weaknesses: Điểm yếu của đối thủ
- Opportunities: Cơ hội khai thác điểm yếu đối thủ
- Threats: Thách thức từ điểm mạnh đối thủ

## 🛠️ Cấu trúc dự án

```
SWOT/
├── app.py                 # Ứng dụng Streamlit chính
├── ai_analyzer.py         # Module phân tích AI với Gemini
├── utils.py               # Utilities: load data, clean data
├── excel_export.py        # Module export Excel với biểu đồ
├── requirements.txt       # Dependencies
├── .env                   # API Key (không commit lên Git)
└── README.md             # Hướng dẫn này
```

## 📝 Lưu ý

1. **API Key**: Đảm bảo file `.env` được lưu với encoding UTF-8
2. **Dữ liệu lớn**: Hệ thống tự động xử lý batch cho dữ liệu lớn (>500 reviews)
3. **Nhiều file**: Có thể upload tối đa 200MB/file, không giới hạn số file
4. **Encoding**: Hệ thống tự động thử nhiều encoding (UTF-8, Latin-1, CP1252) để đọc file CSV

## 🐛 Xử lý lỗi

### Lỗi "Không tìm thấy cột Source"
- **Giải pháp**: Đổi tên file có chứa `my_shop` hoặc tên đối thủ (ví dụ: `starbucks`, `highlands`)
- Hoặc thêm cột `Source` vào file với giá trị `MY_SHOP` hoặc `COMPETITOR`

### Lỗi "Không tìm thấy cột đánh giá"
- **Giải pháp**: Đảm bảo file có ít nhất 1 cột chứa text dài (nội dung đánh giá)
- Đổi tên cột thành: `Review`, `Đánh giá`, `Comment`, `Content`

### Lỗi JSON parsing
- Hệ thống tự động xử lý và làm sạch JSON response từ AI
- Nếu vẫn lỗi, thử giảm số lượng reviews hoặc chia nhỏ file

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng kiểm tra:
1. File `.env` có đúng format và encoding UTF-8
2. API Key có hợp lệ
3. File dữ liệu có đúng cấu trúc
4. Đã cài đặt đầy đủ dependencies

## 📄 License

MIT License
