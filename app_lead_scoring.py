import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="AI Lead Scoring Dashboard",
    page_icon="📊",
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
        background: radial-gradient(circle at top right, #131e31, #090e17);
        color: #e2e8f0;
    }
    
    /* Làm đẹp Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #060b13;
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
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(6, 182, 212, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 2px;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Thiết lập màu cho từng loại khách hàng */
    .metric-vip { color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
    .metric-medium { color: #f59e0b; text-shadow: 0 0 10px rgba(245, 158, 11, 0.2); }
    .metric-low { color: #ef4444; text-shadow: 0 0 10px rgba(239, 68, 68, 0.2); }
    .metric-total { color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
    
    /* Làm đẹp các khối chứa biểu đồ */
    .chart-container {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# URL mặc định của Google Sheet dữ liệu
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1hRvHE6RXm1peVG07avfApPEHocOcPld9IA94hE3vUGE/export?format=csv"

# Tiêu đề ứng dụng
st.markdown('<div class="main-title">AI LEAD SCORING DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Bảng điều khiển phân tích & chấm điểm khách hàng tiềm năng tự động</div>', unsafe_allow_html=True)

# Sidebar thiết lập cấu hình
st.sidebar.markdown("### ⚙️ Cấu hình hệ thống")

sheet_url = st.sidebar.text_input(
    "Đường dẫn Google Sheets (CSV Export)",
    value=DEFAULT_SHEET_URL,
    help="Địa chỉ xuất CSV của bảng tính chứa thông tin khách hàng."
)

# Thêm bộ lọc tìm kiếm nâng cao vào Sidebar
st.sidebar.markdown("### 🔍 Bộ lọc hiển thị")
search_query = st.sidebar.text_input("Tìm kiếm theo Tên / Số điện thoại", value="", help="Nhập tên hoặc số điện thoại để lọc nhanh")
filter_class = st.sidebar.multiselect(
    "Phân loại của AI",
    options=["VIP", "Tiềm năng trung bình", "Không tiềm năng"],
    default=["VIP", "Tiềm năng trung bình", "Không tiềm năng"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Quy tắc chấm điểm chính:
- **Cộng 50đ (Khách VIP - Đạt 100đ):** Ngân sách ≥ 20 tỷ; Tìm biệt thự đơn lập, penthouse, shophouse mặt đường lớn, quỹ đất lớn; Vị trí đắc địa (Q1, ven sông, Phú Mỹ Hưng...); Yêu cầu pháp lý 100%, gặp trực tiếp CĐT.
- **Trừ 50đ (Khách Rác - Về 0đ):** Yêu cầu phi thực tế (giá rẻ vô lý); Không có nhu cầu/nhầm số; Spam/Quảng cáo; Thuê bao/không bắt máy.
- **Giữ nguyên 50đ:** Các phân khúc chung cư/nhà phố 3-10 tỷ, có nhu cầu thực cần tư vấn thêm.
""")

# Khởi tạo trạng thái lưu trữ dữ liệu
if 'df_scored' not in st.session_state:
    st.session_state.df_scored = None

# Dữ liệu dự phòng mặc định (Dùng để hiển thị ngay khi load trang hoặc khi Google Sheet lỗi 404)
MOCK_DATA_RECORDS = [
    {"Họ và tên": "Nguyễn Văn Hải", "Số điện thoại": "0912345678", "Nhu cầu chi tiết": "Cần mua biệt thự đơn lập Vinhomes Ocean Park 2 để đầu tư lâu dài, tài chính không thành vấn đề."},
    {"Họ và tên": "Trần Thị Bình", "Số điện thoại": "0987654321", "Nhu cầu chi tiết": "Tìm mua nhà Quận 1, yêu cầu nhà 3 tầng có sân vườn hồ bơi giá 1-2 tỷ."},
    {"Họ và tên": "Lê Hoàng Nam", "Số điện thoại": "0905123456", "Nhu cầu chi tiết": "Đang tìm hiểu căn hộ chung cư 2 phòng ngủ khu vực trung tâm giá tầm 3-5 tỷ."},
    {"Họ và tên": "Phạm Minh An", "Số điện thoại": "0934567890", "Nhu cầu chi tiết": "Nhầm số, không có nhu cầu mua bất động sản lúc này."},
    {"Họ và tên": "Hoàng Anh Đức", "Số điện thoại": "0978901234", "Nhu cầu chi tiết": "Cần thuê mặt bằng shophouse mặt đường lớn tại Phú Mỹ Hưng mở showroom nội thất."}
]

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
        reasons.append("Tài chính mạnh")
    else:
        budget_numbers = re.findall(r'(\d+(?:[\.,]\d+)?)\s*(?:tỷ|ty|tỉ)', desc_lower)
        for num in budget_numbers:
            try:
                val = float(num.replace(',', '.'))
                if val >= 20.0:
                    has_large_budget = True
                    reasons.append(f"Ngân sách lớn ({val} tỷ >= 20 tỷ)")
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
        reasons.append(f"Loại hình cao cấp: {', '.join(matched_types)}")

    # Vị trí đắc địa
    vip_locations = ["quận 1", "ven sông", "vinhomes ocean park", "phú mỹ hưng"]
    matched_locations = [l for l in vip_locations if l in desc_lower]
    if matched_locations:
        is_vip = True
        reasons.append(f"Vị trí đắc địa: {', '.join(matched_locations)}")

    # Đối tượng khách hàng VIP
    vip_targets = ["chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ", "mua số lượng lớn"]
    matched_targets = [tg for tg in vip_targets if tg in desc_lower]
    if matched_targets:
        is_vip = True
        reasons.append(f"Đối tượng khách hàng: {', '.join(matched_targets)}")

    # Tính cấp thiết & Minh bạch
    vip_urgency = ["pháp lý chuẩn 100%", "pháp lý chuẩn", "sổ hồng riêng", "gặp trực tiếp chủ đầu tư", "trực tiếp chủ đầu tư"]
    matched_urgency = [u for u in vip_urgency if u in desc_lower]
    if matched_urgency:
        is_vip = True
        reasons.append(f"Tính cấp thiết & minh bạch: {', '.join(matched_urgency)}")

    if is_vip:
        score = 100

    # 2. TIÊU CHÍ TRỪ 50 ĐIỂM (KHÁCH HÀNG RÁC)
    is_trash = False
    
    # Không có nhu cầu
    no_need = ["nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành"]
    matched_no_need = [n for n in no_need if n in desc_lower]
    if matched_no_need:
        is_trash = True
        reasons.append(f"Không có nhu cầu: {', '.join(matched_no_need)}")

    # Khách không thiện chí
    not_serious = ["hỏi giá cho vui", "chưa có ý định mua", "thái độ không hợp tác"]
    matched_not_serious = [ns for ns in not_serious if ns in desc_lower]
    if matched_not_serious:
        is_trash = True
        reasons.append(f"Không thiện chí: {', '.join(matched_not_serious)}")

    # Spam/Quảng cáo
    spam_items = ["bảo hiểm", "vay vốn", "mời chào dịch vụ", "quảng cáo"]
    matched_spam = [s for s in spam_items if s in desc_lower]
    if matched_spam:
        is_trash = True
        reasons.append(f"Spam/Quảng cáo: {', '.join(matched_spam)}")

    # Thông tin liên lạc lỗi
    comm_errors = ["thuê bao", "không bắt máy", "gọi nhiều lần không bắt máy", "không phản hồi zalo"]
    matched_comm_errors = [ce for ce in comm_errors if ce in desc_lower]
    if matched_comm_errors:
        is_trash = True
        reasons.append(f"Thông tin liên lạc lỗi: {', '.join(matched_comm_errors)}")

    # Yêu cầu phi thực tế
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
        reasons.append("Yêu cầu phi thực tế: Nhà Quận 1 giá rẻ ≤ 2 tỷ")

    # Nhà trung tâm sân vườn hồ bơi vài trăm triệu
    has_garden_pool = "sân vườn" in desc_lower or "hồ bơi" in desc_lower
    has_million_price = "trăm triệu" in desc_lower or "vài trăm" in desc_lower or "triệu" in desc_lower
    has_ty = "tỷ" in desc_lower or "ty" in desc_lower or "tỉ" in desc_lower
    
    if has_garden_pool and has_million_price and not has_ty:
        is_trash = True
        reasons.append("Yêu cầu phi thực tế: Sân vườn hồ bơi giá vài trăm triệu")

    if is_trash:
        score = 0

    # 3. CÁC TRƯỜNG HỢP KHÁC
    if not is_vip and not is_trash:
        score = 50
        reasons.append("Phân khúc trung bình (3-10 tỷ)")

    classification = "VIP" if score == 100 else ("Không tiềm năng" if score == 0 else "Tiềm năng trung bình")
    reason_str = " | ".join(reasons)
    
    return score, classification, reason_str

# Hàm xử lý DataFrame và chấm điểm
def process_and_score_dataframe(df):
    if 'Số điện thoại' in df.columns:
        df['Số điện thoại'] = df['Số điện thoại'].fillna('').apply(lambda x: str(x).replace('.0', '') if str(x).endswith('.0') else str(x))
    
    scores = []
    classifications = []
    reasons = []
    
    for idx, row in df.iterrows():
        desc = row.get('Nhu cầu chi tiết', '')
        score_val, class_val, reason_val = local_lead_scoring(desc)
        scores.append(score_val)
        classifications.append(class_val)
        reasons.append(reason_val)
    
    df['Điểm AI'] = scores
    df['Phân loại AI'] = classifications
    df['Lý do chấm điểm'] = reasons
    
    # Cột phê duyệt dành cho Human-in-the-loop
    df['Trạng thái duyệt'] = "Đồng ý với AI"
    df['Điểm cuối (Chốt)'] = df['Điểm AI']
    df['Ghi chú của Sales'] = ""
    
    return df

# TỰ ĐỘNG CHẠY KHI MỞ TRANG (Hiển thị ngay số liệu lên Web)
if st.session_state.df_scored is None:
    # Mặc định chạy chấm điểm dữ liệu dự phòng để trang luôn có dữ liệu hiển thị ngay lập tức
    default_df = pd.DataFrame(MOCK_DATA_RECORDS)
    st.session_state.df_scored = process_and_score_dataframe(default_df)

# Nút bấm tải dữ liệu từ Google Sheets
if st.button("🔄 Tải dữ liệu & Chấm điểm từ Google Sheet"):
    with st.spinner("Đang tải dữ liệu từ Google Sheets..."):
        try:
            # Tải dữ liệu từ URL Google Sheets
            df_google = pd.read_csv(sheet_url)
            st.session_state.df_scored = process_and_score_dataframe(df_google)
            st.success("🎉 Đã tải và chấm điểm thành công dữ liệu từ Google Sheet!")
        except Exception as e:
            st.error(f"⚠️ Không thể kết nối hoặc tải dữ liệu từ Google Sheet (Lỗi: {str(e)}). Hệ thống tiếp tục giữ dữ liệu hiện tại.")

# Hiển thị và xử lý dữ liệu (Human-in-the-loop)
if st.session_state.df_scored is not None:
    df_data = st.session_state.df_scored.copy()
    
    # ------------------ PHẦN 1: THỐNG KÊ TỔNG QUAN (METRICS) ------------------
    total_leads = len(df_data)
    vip_count = len(df_data[df_data['Phân loại AI'] == 'VIP'].index)
    medium_count = len(df_data[df_data['Phân loại AI'] == 'Tiềm năng trung bình'].index)
    low_count = len(df_data[df_data['Phân loại AI'] == 'Không tiềm năng'].index)
    
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
        
    # ------------------ PHẦN 2: BIỂU ĐỒ TRỰC QUAN (CHARTS) ------------------
    st.markdown("---")
    st.markdown("### 📊 Biểu đồ phân tích trực quan")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("<div class='chart-container'><strong>📈 Tỉ lệ phân loại Khách hàng</strong></div>", unsafe_allow_html=True)
        class_df = pd.DataFrame({
            'Số lượng': [vip_count, medium_count, low_count]
        }, index=['VIP', 'Tiềm năng trung bình', 'Không tiềm năng'])
        st.bar_chart(class_df, height=250)
        
    with col_c2:
        st.markdown("<div class='chart-container'><strong>📉 Phân bố điểm số tiềm năng</strong></div>", unsafe_allow_html=True)
        score_counts = df_data['Điểm AI'].value_counts()
        # Đảm bảo điểm số 0, 50, 100 luôn có mặt trên biểu đồ
        for s in [0, 50, 100]:
            if s not in score_counts.index:
                score_counts[s] = 0
        score_counts = score_counts.sort_index()
        score_df = pd.DataFrame(score_counts).rename(columns={'count': 'Số khách hàng'})
        st.bar_chart(score_df, height=250)

    # ------------------ PHẦN 3: BỘ LỌC TƯƠNG TÁC (INTERACTIVE FILTER) ------------------
    st.markdown("---")
    st.markdown("### 📋 Bảng Kiểm Duyệt Dữ Liệu (Human-in-the-Loop)")
    
    # Áp dụng bộ lọc từ Sidebar
    filtered_df = df_data.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['Họ và tên'].str.contains(search_query, case=False, na=False) |
            filtered_df['Số điện thoại'].astype(str).str.contains(search_query, case=False, na=False)
        ]
    if filter_class:
        filtered_df = filtered_df[filtered_df['Phân loại AI'].isin(filter_class)]
        
    st.info(f"💡 Đang hiển thị {len(filtered_df)} / {total_leads} khách hàng. Bạn có thể tự do chỉnh sửa và nhấn Enter ở bất cứ ô nào dưới đây.")
    
    # Cho phép người dùng chỉnh sửa dữ liệu trên bảng
    # ĐỂ CHO PHÉP NHẬP TỰ DO VÀ NHẤN ENTER:
    # Thay đổi kiểu cột 'Trạng thái duyệt' và 'Phân loại AI' thành TextColumn thay vì SelectboxColumn để người dùng có thể thoải mái gõ rồi nhấn Enter lưu lại.
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "Trạng thái duyệt": st.column_config.TextColumn(
                "Trạng thái duyệt",
                help="Gõ trạng thái duyệt của bạn (Ví dụ: Đồng ý với AI, Thay đổi điểm, v.v.) rồi nhấn Enter"
            ),
            "Phân loại AI": st.column_config.TextColumn(
                "Phân loại AI",
                help="Phân loại của AI (VIP, Tiềm năng trung bình, Không tiềm năng). Bạn có thể sửa trực tiếp rồi nhấn Enter"
            ),
            "Điểm cuối (Chốt)": st.column_config.NumberColumn(
                "Điểm cuối (Chốt)",
                min_value=0,
                max_value=100,
                step=5
            ),
            "Số điện thoại": st.column_config.TextColumn("Số điện thoại")
        },
        disabled=["Họ và tên", "Nhu cầu chi tiết", "Lý do chấm điểm"],
        width="stretch",
        num_rows="fixed"
    )
    
    # Lưu lại thay đổi của người dùng vào session state chính
    if st.button("💾 Lưu thay đổi kiểm duyệt"):
        main_df = st.session_state.df_scored
        for idx, row in edited_df.iterrows():
            # Đồng bộ thay đổi
            main_df.loc[main_df['Số điện thoại'] == row['Số điện thoại'], 'Trạng thái duyệt'] = row['Trạng thái duyệt']
            main_df.loc[main_df['Số điện thoại'] == row['Số điện thoại'], 'Phân loại AI'] = row['Phân loại AI']
            main_df.loc[main_df['Số điện thoại'] == row['Số điện thoại'], 'Điểm cuối (Chốt)'] = row['Điểm cuối (Chốt)']
            main_df.loc[main_df['Số điện thoại'] == row['Số điện thoại'], 'Ghi chú của Sales'] = row['Ghi chú của Sales']
        st.session_state.df_scored = main_df
        st.success("✅ Đã lưu các thay đổi kiểm duyệt từ con người!")
        
    # ------------------ PHẦN 4: BÀN GIAO DỮ LIỆU (EXPORT) ------------------
    st.markdown("### 📤 Bàn giao dữ liệu")
    
    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Lead Scoring Results')
            workbook = writer.book
            worksheet = writer.sheets['Lead Scoring Results']
            
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
                
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 3
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
