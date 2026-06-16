---
name: real-estate-lead-scoring
description: Kỹ năng xử lý, chấm điểm khách hàng tiềm năng bất động sản bằng AI và xây dựng hệ thống tự động hóa có Human-in-the-loop.
---

# HƯỚNG DẪN XÂY DỰNG HỆ THỐNG AI LEAD SCORING & AUTOMATION

Kỹ năng này hướng dẫn Agent cách thực hiện bài tập xây dựng hệ thống Lead Scoring tự động hóa cho ngành Bất Động Sản theo đúng yêu cầu đề bài.

## 1. Mục tiêu (Mô tả hệ thống)
Hệ thống cần đạt được 4 chức năng chính:
1. **Fetch Data:** Tự động hóa việc lấy dữ liệu từ Google Sheets.
2. **AI Lead Scoring:** Sử dụng AI (ví dụ: Gemini/OpenAI API) để chấm điểm (Scoring) cho từng khách hàng dựa trên "Mô tả nhu cầu" của họ, áp dụng bộ quy tắc kinh doanh.
3. **Web App (Human-in-the-loop):** Giao diện web hiển thị danh sách khách hàng, điểm số AI đề xuất, lý do chấm điểm để con người (Sales/Admin) có thể kiểm duyệt và chỉnh sửa trạng thái.
4. **Export Data:** Xuất dữ liệu đã kiểm duyệt ra file Excel (.xlsx).

---

## 2. SYSTEM PROMPT CHO AI SCORING (Dùng để gọi API)

Dưới đây là Prompt chuẩn để đưa vào model AI nhằm phân tích và chấm điểm từng khách hàng:

```text
Bạn là một chuyên gia phân tích dữ liệu và đánh giá khách hàng tiềm năng trong lĩnh vực Bất động sản.
Nhiệm vụ của bạn là đọc "Mô tả nhu cầu" của khách hàng và chấm điểm tiềm năng của họ dựa trên các quy tắc sau.

QUY TẮC CHẤM ĐIỂM:
Điểm mặc định ban đầu là 50 điểm.

1. CỘNG 50 ĐIỂM (Tối đa 100 điểm - Khách VIP) nếu có các dấu hiệu sau:
- Ngân sách lớn: >20 tỷ, "tài chính mạnh", "không thành vấn đề".
- Loại hình cao cấp: Biệt thự đơn lập, Penthouse, Shophouse mặt đường lớn, Quỹ đất công nghiệp, Sàn văn phòng diện tích lớn.
- Vị trí đắc địa: Quận 1, Ven sông, Vinhomes Ocean Park, Phú Mỹ Hưng.
- Đối tượng: Chủ doanh nghiệp, Nhà đầu tư chuyên nghiệp, Mua sỉ/số lượng lớn.
- Tính cấp thiết & Minh bạch: Pháp lý chuẩn 100%, Sổ hồng riêng, Muốn gặp trực tiếp chủ đầu tư.

2. TRỪ 50 ĐIỂM (Tối thiểu 0 điểm - Khách rác/Không tiềm năng) nếu có các dấu hiệu sau:
- Yêu cầu phi thực tế: Giá quá thấp so với thị trường (vd: nhà Quận 1 giá 1-2 tỷ).
- Không có nhu cầu: "Nhầm số", "Dữ liệu cũ", "Nhầm ngành".
- Không thiện chí: "Hỏi giá cho vui", "Chưa có ý định mua", "Thái độ không hợp tác".
- Spam/Quảng cáo: Bán bảo hiểm, cho vay vốn, mời chào dịch vụ.
- Thông tin lỗi: "Thuê bao", "Không bắt máy", "Không phản hồi Zalo".

3. CÁC TRƯỜNG HỢP KHÁC (Giữ nguyên điểm 50 hoặc cộng ít):
- Mua chung cư, nhà phố tầm trung (3-10 tỷ).
- Cần vay ngân hàng, cân nhắc chính sách.
- Có nhu cầu thực nhưng cần tư vấn thêm pháp lý/vị trí.

YÊU CẦU ĐẦU RA (Định dạng JSON):
{
  "diem_so": <số nguyên từ 0 đến 100>,
  "phan_loai": "<VIP | Tiềm năng trung bình | Không tiềm năng>",
  "ly_do": "<Giải thích ngắn gọn lý do tại sao lại chấm mức điểm này dựa trên các từ khóa nhận diện được>"
}
```

---

## 3. HƯỚNG DẪN TRIỂN KHAI MÃ NGUỒN (PYTHON + STREAMLIT)

Để xây dựng Web App, Agent cần tạo một file Python (ví dụ: `app.py`) sử dụng thư viện **Streamlit** và **Pandas**. 

### Bước 3.1: Lấy dữ liệu từ Google Sheets
Sử dụng ID của Google Sheet và Pandas để đọc dữ liệu CSV:
```python
import pandas as pd

# Thay đổi gid tương ứng nếu cần
sheet_url = "https://docs.google.com/spreadsheets/d/1hRvHE6RXm1peVG07avfApPEHocOcPld9IA94hE3vUGE/export?format=csv&gid=0"
df = pd.read_csv(sheet_url)
```

### Bước 3.2: Tích hợp AI để chấm điểm
Sử dụng thư viện `google-generativeai` hoặc `openai` để duyệt qua từng dòng của DataFrame và gửi cột mô tả (Ví dụ: cột "Nhu cầu" / "Ghi chú") vào System Prompt ở phần 2.
Parse kết quả JSON trả về để tạo ra 3 cột mới: `Điểm AI`, `Phân loại AI`, `Lý do AI`.

### Bước 3.3: Giao diện Web App (Human-in-the-loop)
Sử dụng `st.data_editor` của Streamlit để hiển thị bảng dữ liệu. Người dùng có thể trực tiếp click vào các ô trạng thái hoặc điểm số để chỉnh sửa trước khi chốt.

```python
import streamlit as st

st.title("Hệ thống AI Lead Scoring - Bất Động Sản")
st.write("Kiểm duyệt và chỉnh sửa kết quả chấm điểm của AI.")

# df_scored là DataFrame sau khi đã được AI chấm điểm
edited_df = st.data_editor(df_scored, num_rows="dynamic")
```

### Bước 3.4: Xuất dữ liệu ra file Excel
Cung cấp nút bấm để người dùng tải file Excel xuống sau khi đã chỉnh sửa xong.

```python
from io import BytesIO

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    processed_data = output.getvalue()
    return processed_data

excel_data = to_excel(edited_df)
st.download_button(label='📥 Tải xuống File Excel',
                   data=excel_data,
                   file_name='lead_scoring_result.xlsx')
```

## 4. CÁC THƯ VIỆN CẦN THIẾT
Cần cài đặt các thư viện sau (requirements.txt):
- streamlit
- pandas
- openpyxl
- xlsxwriter
- google-generativeai (hoặc openai tùy chọn)
