import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="AI Lead Scoring (Local Rules)",
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
    
    /* Căn chỉnh nút bấm */
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
st.markdown('<div class="main-title">AI LEAD SCORING SYSTEM (LOCAL ENGINE)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Công cụ tự động chấm điểm khách hàng tiềm năng Bất Động Sản (Không sử dụng API Key)</div>', unsafe_allow_html=True)

# Sidebar thiết lập cấu hình
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5551/5551522.png", width=80)
st.sidebar.markdown("### ⚙️ Cấu hình hệ thống")

sheet_url = st.sidebar.text_input(
    "Đường dẫn Google Sheets (CSV Export)",
    value=DEFAULT_SHEET_URL,
    help="Địa chỉ xuất CSV của bảng tính chứa thông tin khách hàng."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Quy tắc chấm điểm chính:
- **Cộng 50đ (Khách VIP - Đạt 100đ):** Ngân sách ≥ 20 tỷ; Tìm biệt thự đơn lập, penthouse, shophouse mặt đường lớn, quỹ đất lớn; Vị trí đắc địa (Q1, ven sông, Phú Mỹ Hưng...); Yêu cầu pháp lý 100%, gặp trực tiếp CĐT.
- **Trừ 50đ (Khách Rác - Về 0đ):** Yêu cầu phi thực tế (giá rẻ vô lý); Không có nhu cầu/nhầm số; Spam/Quảng cáo; Thuê bao/không bắt máy.
- **Giữ nguyên 50đ:** Các phân khúc chung cư/nhà phố 3-10 tỷ, có nhu cầu thực cần tư vấn thêm.
""")

# Trạng thái Session State để lưu trữ dữ liệu đã chấm điểm
if 'df_scored' not in st.session_state:
    st.session_state.df_scored = None

# Bộ phân tích dữ liệu quy tắc cục bộ (Không dùng API)
def local_lead_scoring(description):
    if not isinstance(description, str) or not description.strip():
        return 50, "Tiềm năng trung bình", "Mô tả nhu cầu trống, giữ nguyên 50đ"

    desc_lower = description.lower()
    score = 50
    reasons = []
    
    # 1. TIÊU CHÍ CỘNG 50 ĐIỂM (KHÁCH HÀNG VIP)
    is_vip = False
    
    # Kiểm tra ngân sách lớn
    has_large_budget = False
    if "tài chính mạnh" in desc_lower or "không thành vấn đề" in desc_lower:
        has_large_budget = True
        reasons.append("Tài chính mạnh / không thành vấn đề (+50đ)")
    else:
        # Tìm số tiền cụ thể >= 20 tỷ
        budget_numbers = re.findall(r'(\d+(?:[\.,]\d+)?)\s*(?:tỷ|ty|tỉ)', desc_lower)
        for num in budget_numbers:
            try:
                val = float(num.replace(',', '.'))
                if val >= 20.0:
                    has_large_budget = True
                    reasons.append(f"Ngân sách lớn ({val} tỷ >= 20 tỷ) (+50đ)")
                    break
            except ValueError:
                continue
    
    if has_large_budget:
        is_vip = True

    # Loại hình cao cấp
    vip_types = ["biệt thự đơn lập", "penthouse", "shophouse mặt đường", "shophouse mặt đường lớn", "quỹ đất công nghiệp", "sàn văn phòng diện tích lớn"]
    matched_types = [t for t in vip_types if t in desc_lower]
    if matched_types:
        is_vip = True
        reasons.append(f"Loại hình cao cấp: {', '.join(matched_types)} (+50đ)")

    # Vị trí đắc địa
    vip_locations = ["quận 1", "ven sông", "vinhomes ocean park", "phú mỹ hưng"]
    matched_locations = [l for l in vip_locations if l in desc_lower]
    if matched_locations:
        is_vip = True
        reasons.append(f"Vị trí đắc địa: {', '.join(matched_locations)} (+50đ)")

    # Đối tượng khách hàng VIP
    vip_targets = ["chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ", "mua số lượng lớn"]
    matched_targets = [tg for tg in vip_targets if tg in desc_lower]
    if matched_targets:
        is_vip = True
        reasons.append(f"Đối tượng khách hàng: {', '.join(matched_targets)} (+50đ)")

    # Tính cấp thiết & Minh bạch
    vip_urgency = ["pháp lý chuẩn 100%", "pháp lý chuẩn", "sổ hồng riêng", "gặp trực tiếp chủ đầu tư", "trực tiếp chủ đầu tư"]
    matched_urgency = [u for u in vip_urgency if u in desc_lower]
    if matched_urgency:
        is_vip = True
        reasons.append(f"Tính cấp thiết & minh bạch: {', '.join(matched_urgency)} (+50đ)")

    if is_vip:
        score = 100

    # 2. TIÊU CHÍ TRỪ 50 ĐIỂM (KHÁCH HÀNG RÁC)
    is_trash = False
    
    # Không có nhu cầu
    no_need = ["nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành"]
    matched_no_need = [n for n in no_need if n in desc_lower]
    if matched_no_need:
        is_trash = True
        reasons.append(f"Không có nhu cầu: {', '.join(matched_no_need)} (-50đ)")

    # Khách không thiện chí
    not_serious = ["hỏi giá cho vui", "chưa có ý định mua", "thái độ không hợp tác"]
    matched_not_serious = [ns for ns in not_serious if ns in desc_lower]
    if matched_not_serious:
        is_trash = True
        reasons.append(f"Không thiện chí: {', '.join(matched_not_serious)} (-50đ)")

    # Spam/Quảng cáo
    spam_items = ["bảo hiểm", "vay vốn", "mời chào dịch vụ", "quảng cáo"]
    matched_spam = [s for s in spam_items if s in desc_lower]
    if matched_spam:
        is_trash = True
        reasons.append(f"Spam/Quảng cáo: {', '.join(matched_spam)} (-50đ)")

    # Thông tin liên lạc lỗi
    comm_errors = ["thuê bao", "không bắt máy", "gọi nhiều lần không bắt máy", "không phản hồi zalo"]
    matched_comm_errors = [ce for ce in comm_errors if ce in desc_lower]
    if matched_comm_errors:
        is_trash = True
        reasons.append(f"Thông tin liên lạc lỗi: {', '.join(matched_comm_errors)} (-50đ)")

    # Yêu cầu phi thực tế (Ví dụ: Quận 1 giá 1-2 tỷ)
    has_q1 = "quận 1" in desc_lower or "q1" in desc_lower
    has_low_price = False
    price_numbers = re.findall(r'(\d+(?:[\.,]\d+)?)\s*(?:tỷ|ty|tỉ)', desc_lower)
    for p_num in price_numbers:
        try:
            p_val = float(p_num.replace(',', '.'))
            if p_val <= 2.0:
                has_low_price = True
                break
        except ValueError:
            continue
            
    if has_q1 and has_low_price:
        is_trash = True
        reasons.append("Yêu cầu phi thực tế: Nhà Quận 1 giá rẻ ≤ 2 tỷ (-50đ)")

    # Nhà trung tâm sân vườn hồ bơi vài trăm triệu
    has_garden_pool = "sân vườn" in desc_lower or "hồ bơi" in desc_lower
    has_million_price = "trăm triệu" in desc_lower or "vài trăm" in desc_lower or "triệu" in desc_lower
    has_ty = "tỷ" in desc_lower or "ty" in desc_lower or "tỉ" in desc_lower
    
    if has_garden_pool and has_million_price and not has_ty:
        is_trash = True
        reasons.append("Yêu cầu phi thực tế: Sân vườn hồ bơi giá vài trăm triệu (-50đ)")

    if is_trash:
        score = 0

    # 3. CÁC TRƯỜNG HỢP KHÁC
    if not is_vip and not is_trash:
        score = 50
        reasons.append("Phân khúc trung bình (chung cư/nhà phố 3-10 tỷ, cần tư vấn thêm) (Giữ nguyên 50đ)")

    classification = "VIP" if score == 100 else ("Không tiềm năng" if score == 0 else "Tiềm năng trung bình")
    reason_str = " | ".join(reasons)
    
    return score, classification, reason_str


# Logic chính khi chạy app
if st.button("🔄 Tải dữ liệu & Chấm điểm tự động"):
    with st.spinner("Đang tải dữ liệu từ Google Sheets và chạy bộ quy tắc chấm điểm..."):
        try:
            # 1. Tải Google Sheet
            df = pd.read_csv(sheet_url)
            
            # Làm sạch cột số điện thoại hiển thị đẹp hơn
            if 'Số điện thoại' in df.columns:
                df['Số điện thoại'] = df['Số điện thoại'].fillna('').apply(lambda x: str(x).replace('.0', '') if str(x).endswith('.0') else str(x))
            
            # 2. Duyệt và chấm điểm bằng Local Engine
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
                
                score_val, class_val, reason_val = local_lead_scoring(desc)
                scores.append(score_val)
                classifications.append(class_val)
                reasons.append(reason_val)
                
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
            status_text.success("🎉 Đã tự động chấm điểm và phân loại hoàn tất cho toàn bộ danh sách!")
            
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
                help="Kiểm duyệt kết quả tự động",
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
        width="stretch",
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
            file_name="Lead_Scoring_Local_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    # Trạng thái ban đầu khi chưa tải dữ liệu
    st.warning("👈 Nhấp nút 'Tải dữ liệu & Chấm điểm tự động' ở trên để khởi chạy hệ thống phân tích!")
    
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
    st.dataframe(mock_data, width="stretch")
