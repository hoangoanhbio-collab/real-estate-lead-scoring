import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
from io import BytesIO

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="AI Lead Scoring & Automation",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện thêm lung linh & hiện đại (Dark-Teal Glassmorphic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Giao diện nền tối hiện đại */
    .stApp {
        background: radial-gradient(circle at top right, #1a2536, #0e1622);
        color: #e2e8f0;
    }
    
    /* Làm đẹp Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b111e;
        border-right: 1px solid #1e293b;
    }
    
    /* Tiêu đề lớn */
    .main-title {
        background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.2rem;
        text-shadow: 0 10px 20px rgba(6, 182, 212, 0.15);
    }
    
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Hộp thông tin chỉ số (Metric Box) Glassmorphism */
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(6, 182, 212, 0.4);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Thiết lập màu cho từng loại khách hàng */
    .metric-vip { color: #10b981; }
    .metric-medium { color: #f59e0b; }
    .metric-low { color: #ef4444; }
    .metric-total { color: #38bdf8; }
    
    /* Căn chỉnh lại nút bấm */
    div.stButton > button {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
        transition: all 0.2s ease;
        width: 100%;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# URL mặc định của Google Sheet dữ liệu
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1hRvHE6RXm1peVG07avfApPEHocOcPld9IA94hE3vUGE/export?format=csv"

# Tiêu đề ứng dụng
st.markdown('<div class="main-title">AI LEAD SCORING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống phân tích, chấm điểm khách hàng bất động sản tự động (Human-in-the-loop)</div>', unsafe_allow_html=True)

# Sidebar thiết lập cấu hình
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5551/5551522.png", width=80)
st.sidebar.markdown("### ⚙️ Cấu hình hệ thống")

# Lấy API Key từ môi trường hoặc người dùng nhập
env_api_key = os.environ.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=env_api_key,
    type="password",
    help="Nhập Gemini API Key của bạn để bắt đầu chấm điểm khách hàng."
)

sheet_url = st.sidebar.text_input(
    "Đường dẫn Google Sheets (CSV Export)",
    value=DEFAULT_SHEET_URL,
    help="Địa chỉ xuất CSV của bảng tính chứa thông tin khách hàng."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Quy tắc chấm điểm chính:
- **Cộng 50đ (Khách VIP):** Ngân sách ≥ 20 tỷ; Tìm biệt thự đơn lập, penthouse, shophouse mặt đường lớn, quỹ đất lớn; Yêu cầu pháp lý 100%, gặp trực tiếp CĐT.
- **Trừ 50đ (Khách Không Tiềm Năng):** Yêu cầu phi thực tế (giá rẻ vô lý); Không có nhu cầu/nhầm số; Spam/Quảng cáo; Thuê bao/không bắt máy.
- **Giữ nguyên 50đ:** Các phân khúc chung cư/nhà phố 3-10 tỷ, có nhu cầu thực cần tư vấn thêm.
""")

# Trạng thái Session State để lưu trữ dữ liệu đã chấm điểm
if 'df_scored' not in st.session_state:
    st.session_state.df_scored = None

# Hàm gọi Gemini API để chấm điểm một mô tả nhu cầu
def get_ai_score(client, customer_name, description):
    if not description or pd.isna(description) or str(description).strip() == "":
        return {
            "diem_so": 50,
            "phan_loai": "Tiềm năng trung bình",
            "ly_do": "Không có mô tả nhu cầu cụ thể."
        }
        
    prompt = f"""
Bạn là một chuyên gia phân tích dữ liệu và đánh giá khách hàng tiềm năng trong lĩnh vực Bất động sản tại Việt Nam.
Hãy đọc tên khách hàng "{customer_name}" và "Mô tả nhu cầu" dưới đây, sau đó chấm điểm tiềm năng của họ dựa trên các quy tắc nghiệp vụ.

Nhu cầu khách hàng: "{description}"

QUY TẮC CHẤM ĐIỂM (Mặc định bắt đầu là 50 điểm):

1. CỘNG VÀO 50 ĐIỂM (Tối đa 100 điểm - Phân loại: VIP) nếu có các dấu hiệu:
- Ngân sách lớn: Có đề cập đến số tiền cụ thể từ 20 tỷ trở lên hoặc các cụm từ "tài chính mạnh", "không thành vấn đề".
- Loại hình cao cấp: Tìm kiếm "Biệt thự đơn lập", "Penthouse", "Shophouse mặt đường lớn", "Quỹ đất công nghiệp", "Sàn văn phòng diện tích lớn".
- Vị trí đắc địa: Yêu cầu các khu vực như "Quận 1", "Ven sông", "Vinhomes Ocean Park", "Phú Mỹ Hưng".
- Đối tượng khách hàng: Đề cập là "Chủ doanh nghiệp", "Nhà đầu tư chuyên nghiệp", "Mua sỉ", "Mua số lượng lớn".
- Tính cấp thiết & Minh bạch: Yêu cầu "Pháp lý chuẩn 100%", "Sổ hồng riêng", "Muốn gặp trực tiếp chủ đầu tư để đàm phán".

2. TRỪ ĐI 50 ĐIỂM (Tối thiểu 0 điểm - Phân loại: Không tiềm năng) nếu có các dấu hiệu:
- Yêu cầu phi thực tế: Tìm mua bất động sản với giá thấp vô lý so với thị trường (VD: Nhà Quận 1 giá 1-2 tỷ, nhà trung tâm có sân vườn hồ bơi giá vài trăm triệu).
- Không có nhu cầu: "Nhầm số", "Không có nhu cầu", "Dữ liệu cũ", "Nhầm ngành".
- Khách hàng không thiện chí: "Hỏi giá cho vui", "Chưa có ý định mua", "Thái độ không hợp tác".
- Spam/Quảng cáo: Nội dung chứa các dịch vụ khác như "Bảo hiểm", "Vay vốn", "Mời chào dịch vụ".
- Thông tin liên lạc lỗi: "Thuê bao", "Gọi nhiều lần không bắt máy", "Không phản hồi Zalo".

3. GIỮ NGUYÊN HOẶC CỘNG NHẸ (Mức 50-60 điểm - Phân loại: Tiềm năng trung bình) cho các trường hợp khác:
- Khách hàng tìm mua chung cư, nhà phố tầm trung (3-10 tỷ).
- Khách hàng cần vay ngân hàng, đang cân nhắc chính sách.
- Khách hàng có nhu cầu thực nhưng cần tư vấn thêm về pháp lý hoặc vị trí.

Hãy trả về kết quả chính xác dưới dạng JSON format như dưới đây. Không thêm bớt bất kỳ từ ngữ nào ngoài JSON block:
{{
  "diem_so": <số nguyên từ 0 đến 100>,
  "phan_loai": "<VIP | Tiềm năng trung bình | Không tiềm năng>",
  "ly_do": "<Giải thích cụ thể lý do tại sao lại chấm mức điểm này dựa trên các từ khóa và ngữ cảnh đã nhận diện>"
}}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=dict(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        # Fallback trong trường hợp lỗi API hoặc parse lỗi
        return {
            "diem_so": 50,
            "phan_loai": "Chưa xác định",
            "ly_do": f"Lỗi gọi AI: {str(e)}"
        }

# Logic chính khi chạy app
if st.button("🔄 Tải dữ liệu & Chấm điểm bằng AI"):
    if not api_key:
        st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên (Sidebar) trước khi tiếp tục!")
    else:
        with st.spinner("Đang tải dữ liệu từ Google Sheets và chạy AI chấm điểm..."):
            try:
                # 1. Tải Google Sheet
                df = pd.read_csv(sheet_url)
                
                # Làm sạch cột số điện thoại hiển thị đẹp hơn
                if 'Số điện thoại' in df.columns:
                    df['Số điện thoại'] = df['Số điện thoại'].fillna('').apply(lambda x: str(x).replace('.0', '') if str(x).endswith('.0') else str(x))
                
                # 2. Khởi tạo Gemini Client
                # Dùng thư viện google-generativeai bản mới
                genai.configure(api_key=api_key)
                # Client cho genai 2.5
                client = genai.Client(api_key=api_key) if hasattr(genai, 'Client') else None
                
                # Dự phòng nếu không có genai.Client
                class LegacyClient:
                    def __init__(self, key):
                        genai.configure(api_key=key)
                    class models:
                        @staticmethod
                        def generate_content(model, contents, config=None):
                            m = genai.GenerativeModel(model)
                            # Convert config to format required by model
                            generation_config = {}
                            if config:
                                generation_config['response_mime_type'] = config.get('response_mime_type')
                                generation_config['temperature'] = config.get('temperature')
                            return m.generate_content(contents, generation_config=generation_config)
                
                if not client:
                    client = LegacyClient(api_key)
                
                # 3. Duyệt và chấm điểm
                scores = []
                classifications = []
                reasons = []
                
                # Tạo progress bar trực quan
                progress_bar = st.progress(0)
                status_text = st.empty()
                total_rows = len(df)
                
                for idx, row in df.iterrows():
                    cust_name = row.get('Họ và tên', f'Khách hàng #{idx+1}')
                    desc = row.get('Nhu cầu chi tiết', '')
                    
                    status_text.text(f"Đang xử lý khách hàng {idx+1}/{total_rows}: {cust_name}...")
                    
                    result = get_ai_score(client, cust_name, desc)
                    scores.append(result.get("diem_so", 50))
                    classifications.append(result.get("phan_loai", "Tiềm năng trung bình"))
                    reasons.append(result.get("ly_do", ""))
                    
                    progress_bar.progress((idx + 1) / total_rows)
                
                # Cập nhật kết quả vào DataFrame
                df['Điểm AI'] = scores
                df['Phân loại AI'] = classifications
                df['Lý do chấm điểm'] = reasons
                
                # Cột phê duyệt dành cho Human-in-the-loop
                df['Trạng thái duyệt'] = "Đồng ý với AI"
                df['Điểm cuối (Chốt)'] = df['Điểm AI']
                df['Ghi chú của Sales'] = ""
                
                # Lưu vào session state
                st.session_state.df_scored = df
                status_text.success("🎉 Đã chấm điểm và phân loại hoàn tất cho toàn bộ danh sách!")
                
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}")

# Hiển thị và xử lý dữ liệu (Human-in-the-loop)
if st.session_state.df_scored is not None:
    df_data = st.session_state.df_scored
    
    # Tính toán các chỉ số thống kê tổng hợp (Metrics Overview)
    total_leads = len(df_data)
    vip_count = len(df_data[df_data['Phân loại AI'] == 'VIP'])
    medium_count = len(df_data[df_data['Phân loại AI'] == 'Tiềm năng trung bình'])
    low_count = len(df_data[df_data['Phân loại AI'] == 'Không tiềm năng'])
    
    col_t, col1, col2, col3 = st.columns(4)
    with col_t:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value metric-total">{total_leads}</div>
            <div class="metric-label">Tổng khách hàng</div>
        </div>
        """, unsafe_allow_html=True)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value metric-vip">{vip_count}</div>
            <div class="metric-label">Khách hàng VIP</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value metric-medium">{medium_count}</div>
            <div class="metric-label">Tiềm năng trung bình</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value metric-low">{low_count}</div>
            <div class="metric-label">Không tiềm năng</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### 📋 Bảng Kiểm Duyệt Dữ Liệu (Human-in-the-Loop)")
    st.info("💡 Bạn có thể click trực tiếp vào ô bất kỳ trong bảng dưới đây để sửa đổi thông tin (như chỉnh lại 'Điểm cuối (Chốt)', thay đổi 'Trạng thái duyệt' hoặc điền thêm 'Ghi chú của Sales').")
    
    # Cho phép người dùng chỉnh sửa dữ liệu trên bảng
    # Cấu hình định dạng các cột để người dùng chọn thuận tiện
    edited_df = st.data_editor(
        df_data,
        column_config={
            "Trạng thái duyệt": st.column_config.SelectboxColumn(
                "Trạng thái duyệt",
                help="Kiểm duyệt kết quả từ AI",
                options=["Đồng ý với AI", "Thay đổi điểm", "Từ chối/Hủy"],
                required=True
            ),
            "Điểm cuối (Chốt)": st.column_config.NumberColumn(
                "Điểm cuối (Chốt)",
                help="Điểm số chốt cuối cùng dùng để lọc chăm sóc",
                min_value=0,
                max_value=100,
                step=5
            ),
            "Số điện thoại": st.column_config.TextColumn("Số điện thoại")
        },
        disabled=["Họ và tên", "Nhu cầu chi tiết", "Điểm AI", "Phân loại AI", "Lý do chấm điểm"],
        use_container_width=True,
        num_rows="fixed"
    )
    
    # Lưu lại thay đổi của người dùng
    if st.button("💾 Lưu thay đổi kiểm duyệt"):
        st.session_state.df_scored = edited_df
        st.success("✅ Đã lưu các thay đổi kiểm duyệt từ con người!")
        
    # Tạo nút Xuất Excel
    st.markdown("### 📤 Bàn giao dữ liệu")
    
    def to_excel_bytes(df):
        output = BytesIO()
        # Sử dụng xlsxwriter để xuất excel đẹp hơn
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Lead Scoring Results')
            
            # Format sheet excel cho chuyên nghiệp
            workbook = writer.book
            worksheet = writer.sheets['Lead Scoring Results']
            
            # Định dạng tiêu đề cột
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1f4e78',
                'font_color': 'white',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Thiết lập độ rộng cột tự động
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 3
                # Giới hạn độ rộng cột tránh quá dài
                worksheet.set_column(i, i, min(max_len, 50))
                
        return output.getvalue()
        
    excel_data = to_excel_bytes(edited_df)
    
    col_dl, col_space = st.columns([1, 3])
    with col_dl:
        st.download_button(
            label="📥 Tải xuống File Excel",
            data=excel_data,
            file_name="Lead_Scoring_AI_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    # Trạng thái ban đầu khi chưa tải dữ liệu
    st.warning("👈 Nhập API Key ở sidebar bên trái và nhấn nút 'Tải dữ liệu & Chấm điểm bằng AI' ở trên để khởi chạy hệ thống!")
    
    # Hiển thị cấu trúc mẫu dữ liệu sẽ đọc
    st.markdown("### 📋 Cấu trúc dữ liệu mẫu sẽ được tải từ Google Sheets:")
    mock_data = pd.DataFrame({
        "Họ và tên": ["Nguyễn Văn Hải", "Trần Thị Bình", "Lê Hoàng Nam", "Phạm Minh An", "Hoàng Anh Đức"],
        "Số điện thoại": ["0912345678", "0987654321", "0905123456", "0934567890", "0978901234"],
        "Nhu cầu chi tiết": [
            "Cần mua biệt thự đơn lập Vinhomes Ocean Park 2 để đầu tư lâu dài, tài chính không thành vấn đề.",
            "Tìm mua nhà Quận 1, yêu cầu nhà 3 tầng có sân vườn hồ bơi giá 1-2 tỷ.",
            "Đang tìm hiểu căn hộ chung cư 2 phòng ngủ khu vực trung tâm giá tầm 3-5 tỷ.",
            "Nhầm số, không có nhu cầu mua bất động sản lúc này.",
            "Cần thuê mặt bằng shophouse mặt đường lớn tại Phú Mỹ Hưng mở showroom nội thất."
        ]
    })
    st.dataframe(mock_data, use_container_width=True)
