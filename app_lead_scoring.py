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
        margin-bottom: 1.5rem;
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
    
    /* CSS cho hộp Chi tiết & Duyệt nhanh (CRM Action Panel) */
    .crm-panel {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 16px;
        padding: 25px;
        margin-top: 10px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
    }
</style>
""", unsafe_allow_html=True)

# URL mặc định của Google Sheet dữ liệu
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1hRvHE6RXm1peVG07avfApPEHocOcPld9IA94hE3vUGE/export?format=csv"

# Tiêu đề ứng dụng
st.markdown('<div class="main-title">AI LEAD SCORING DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Bảng điều khiển phân tích & chấm điểm khách hàng tiềm năng tự động</div>', unsafe_allow_html=True)

# Sidebar thiết lập cấu hình
st.sidebar.markdown("### ⚙️ Điều khiển & Cấu hình")

sheet_url = st.sidebar.text_input(
    "Đường dẫn Google Sheets (CSV Export)",
    value=DEFAULT_SHEET_URL,
    help="Địa chỉ xuất CSV của bảng tính chứa thông tin khách hàng."
)

# Nút bấm tải dữ liệu từ Google Sheets được chuyển sang Sidebar để gọn trang chính
if st.sidebar.button("🔄 Tải dữ liệu từ Google Sheet", use_container_width=True):
    with st.sidebar.spinner("Đang tải dữ liệu..."):
        try:
            df_google = pd.read_csv(sheet_url)
            # Hàm xử lý DataFrame và chấm điểm
            def process_and_score_dataframe_local(df):
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
                
                df['Trạng thái duyệt'] = "Chưa phê duyệt"
                df['Điểm cuối (Chốt)'] = df['Điểm AI']
                df['Ghi chú của Sales'] = ""
                return df
                
            st.session_state.df_scored = process_and_score_dataframe_local(df_google)
            st.sidebar.success("🎉 Đã cập nhật dữ liệu từ Google Sheet!")
        except Exception as e:
            st.sidebar.error(f"⚠️ Lỗi kết nối Google Sheet: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Quy tắc chấm điểm chính:
- **Cộng 50đ (Khách VIP - Đạt 100đ):** Ngân sách ≥ 20 tỷ; Tìm biệt thự đơn lập, penthouse, shophouse mặt đường lớn, quỹ đất lớn; Vị trí đắc địa (Q1, ven sông, Phú Mỹ Hưng...); Yêu cầu pháp lý 100%, gặp trực tiếp CĐT.
- **Trừ 50đ (Khách Rác - Về 0đ):** Yêu cầu phi thực tế (giá rẻ vô lý); Không có nhu cầu/nhầm số; Spam/Quảng cáo; Thuê bao/không bắt máy.
- **Giữ nguyên 50đ:** Các phân khúc chung cư/nhà phố 3-10 tỷ, có nhu cầu thực cần tư vấn thêm.
""")

# Dữ liệu dự phòng mặc định (Dùng để hiển thị ngay khi load trang)
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
    
    df['Trạng thái duyệt'] = "Chưa phê duyệt"
    df['Điểm cuối (Chốt)'] = df['Điểm AI']
    df['Ghi chú của Sales'] = ""
    
    return df

# Khởi tạo dữ liệu mặc định vào session state nếu chưa có
if 'df_scored' not in st.session_state or st.session_state.df_scored is None:
    default_df = pd.DataFrame(MOCK_DATA_RECORDS)
    st.session_state.df_scored = process_and_score_dataframe(default_df)

# Đọc dữ liệu hiện tại
df_data = st.session_state.df_scored.copy()

# ------------------ PHÂN CHIA TABS ĐỂ GIAO DIỆN GỌN GÀNG, KHÔNG RỐI ------------------
tab_dashboard, tab_list = st.tabs([
    "📊 Báo cáo & Thống kê", 
    "📋 Danh sách Leads"
])

# ==================== TAB 1: BÁO CÁO & THỐNG KÊ ====================
with tab_dashboard:
    # 1. METRICS TỔNG QUAN
    total_leads = len(df_data)
    vip_count = len(df_data[df_data['Phân loại AI'] == 'VIP'].index)
    medium_count = len(df_data[df_data['Phân loại AI'] == 'Tiềm năng trung bình'].index)
    low_count = len(df_data[df_data['Phân loại AI'] == 'Không tiềm năng'].index)
    
    col_t, col1, col2, col3 = st.columns(4)
    with col_t:
        st.markdown(f'<div class="metric-card"><div class="metric-value metric-total">{total_leads}</div><div class="metric-label">Tổng khách hàng</div></div>', unsafe_allow_html=True)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value metric-vip">{vip_count}</div><div class="metric-label">Khách hàng VIP</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value metric-medium">{medium_count}</div><div class="metric-label">Tiềm năng trung bình</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value metric-low">{low_count}</div><div class="metric-label">Không tiềm năng</div></div>', unsafe_allow_html=True)
        
    # 2. BIỂU ĐỒ TRỰC QUAN
    st.markdown("---")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("<div class='chart-container'><strong>📈 Tỉ lệ phân loại Khách hàng</strong></div>", unsafe_allow_html=True)
        class_df = pd.DataFrame({
            'Số lượng': [vip_count, medium_count, low_count]
        }, index=['VIP', 'Tiềm năng trung bình', 'Không tiềm năng'])
        st.bar_chart(class_df, height=260)
        
    with col_c2:
        st.markdown("<div class='chart-container'><strong>📉 Phân bố điểm số tiềm năng</strong></div>", unsafe_allow_html=True)
        score_counts = df_data['Điểm AI'].value_counts()
        for s in [0, 50, 100]:
            if s not in score_counts.index:
                score_counts[s] = 0
        score_counts = score_counts.sort_index()
        score_df = pd.DataFrame(score_counts).rename(columns={'count': 'Số khách hàng'})
        st.bar_chart(score_df, height=260)


# ==================== TAB 2: DANH SÁCH & BỘ LỌC LEADS ====================
with tab_list:
    st.markdown("### 🔍 Bộ lọc tìm kiếm")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        main_search_query = st.text_input("Tìm kiếm theo Tên hoặc Số điện thoại", value="", key="search_tab")
    with col_f2:
        main_filter_class = st.multiselect(
            "Lọc theo phân loại AI",
            options=["VIP", "Tiềm năng trung bình", "Không tiềm năng"],
            default=["VIP", "Tiềm năng trung bình", "Không tiềm năng"],
            key="filter_tab"
        )
        
    # Áp dụng bộ lọc
    filtered_df = df_data.copy()
    if main_search_query:
        filtered_df = filtered_df[
            filtered_df['Họ và tên'].str.contains(main_search_query, case=False, na=False) |
            filtered_df['Số điện thoại'].astype(str).str.contains(main_search_query, case=False, na=False)
        ]
    if main_filter_class:
        filtered_df = filtered_df[filtered_df['Phân loại AI'].isin(main_filter_class)]
        
    st.markdown(f"**Hiển thị:** {len(filtered_df)} / {len(df_data)} dòng dữ liệu")
    
    # Bảng dữ liệu chính
    st.dataframe(
        filtered_df[[
            "Họ và tên", "Số điện thoại", "Nhu cầu chi tiết", 
            "Điểm AI", "Phân loại AI", "Lý do chấm điểm", 
            "Trạng thái duyệt", "Điểm cuối (Chốt)", "Ghi chú của Sales"
        ]],
        width="stretch"
    )
    
    # Bàn giao dữ liệu (Xuất Excel)
    st.markdown("### 📤 Bàn giao dữ liệu")
    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Lead Scoring Results')
            workbook = writer.book
            worksheet = writer.sheets['Lead Scoring Results']
            header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'top',
                'fg_color': '#1f4e78', 'font_color': 'white', 'border': 1
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 3
                worksheet.set_column(i, i, min(max_len, 50))
        return output.getvalue()
        
    excel_data = to_excel_bytes(st.session_state.df_scored)
    st.download_button(
        label="📥 Tải xuống File Excel Bàn Giao",
        data=excel_data,
        file_name="Lead_Scoring_CRM_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ==================== CRM PANEL (DUYỆT & PHÊ DUYỆT NHANH) KHU VỰC DƯỚI TABS ====================
st.markdown("---")
st.markdown("### ⚡ Phê duyệt & Ghi chú hành động nhanh")
st.write("Chọn khách hàng từ menu thả xuống dưới đây để xem nhu cầu chi tiết và phê duyệt trạng thái nhanh chóng.")

if len(df_data) > 0:
    # Hộp chọn khách hàng
    customer_names = df_data['Họ và tên'].tolist()
    selected_customer = st.selectbox("👉 Chọn khách hàng xử lý:", options=customer_names, key="crm_selectbox")
    
    # Dữ liệu khách hàng
    customer_data = df_data[df_data['Họ và tên'] == selected_customer].iloc[0]
    
    # Bảng hiển thị CRM Panel
    st.markdown(f"""
    <div class="crm-panel">
        <h4>🏢 Khách hàng: {customer_data['Họ và tên']} ({customer_data['Số điện thoại']})</h4>
        <p style="margin-top: 10px;"><strong>Nhu cầu chi tiết:</strong> {customer_data['Nhu cầu chi tiết']}</p>
        <p><strong>Điểm AI chấm:</strong> <span style="color:#06b6d4;font-weight:bold;">{customer_data['Điểm AI']} điểm</span> ({customer_data['Phân loại AI']})</p>
        <p><strong>Lý do phân loại:</strong> <em>{customer_data['Lý do chấm điểm']}</em></p>
        <p><strong>Trạng thái phê duyệt:</strong> {customer_data['Trạng thái duyệt']} | <strong>Điểm cuối:</strong> {customer_data['Điểm cuối (Chốt)']}đ</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Ghi chú Note Action
    current_note = customer_data['Ghi chú của Sales'] if pd.notna(customer_data['Ghi chú của Sales']) else ""
    note_action = st.text_area("✍️ Ghi chú hành động (Note Action):", value=current_note, placeholder="Nhập hành động tiếp theo hoặc lý do phê duyệt...", key="crm_note")
    
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("✅ Phê duyệt Khách hàng Tiềm năng (VIP)", use_container_width=True, key="btn_approve"):
            main_df = st.session_state.df_scored
            idx = main_df[main_df['Số điện thoại'] == customer_data['Số điện thoại']].index[0]
            main_df.at[idx, 'Trạng thái duyệt'] = "Đã phê duyệt tiềm năng"
            main_df.at[idx, 'Phân loại AI'] = "VIP"
            main_df.at[idx, 'Điểm cuối (Chốt)'] = 100
            main_df.at[idx, 'Ghi chú của Sales'] = note_action
            st.session_state.df_scored = main_df
            st.success(f"🎉 Đã phê duyệt tiềm năng (100đ) cho **{selected_customer}**!")
            st.rerun()
            
    with col_act2:
        if st.button("❌ Đánh dấu Khách hàng Không Tiềm năng (Rác)", use_container_width=True, key="btn_reject"):
            main_df = st.session_state.df_scored
            idx = main_df[main_df['Số điện thoại'] == customer_data['Số điện thoại']].index[0]
            main_df.at[idx, 'Trạng thái duyệt'] = "Từ chối/Không tiềm năng"
            main_df.at[idx, 'Phân loại AI'] = "Không tiềm năng"
            main_df.at[idx, 'Điểm cuối (Chốt)'] = 0
            main_df.at[idx, 'Ghi chú của Sales'] = note_action
            st.session_state.df_scored = main_df
            st.success(f"⚠️ Đã đánh dấu không tiềm năng (0đ) cho **{selected_customer}**!")
            st.rerun()
else:
    st.write("Hiện tại chưa có dữ liệu để thực hiện phê duyệt.")
