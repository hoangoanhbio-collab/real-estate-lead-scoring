import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="AI Lead Scoring Dashboard",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện tối hiện đại (Dark-Teal Glassmorphic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
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
    
    /* Thiết kế tiêu đề phần */
    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 1.5rem;
        margin-bottom: 0.2rem;
    }
    
    .section-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Panel chứa bộ lọc và hành động */
    .filter-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #38bdf8;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Nút bấm của hành động nhanh */
    div.stButton > button {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.2);
        transition: all 0.2s ease;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
        transform: translateY(-1px);
    }
    
    /* Hộp thông tin chỉ số (Metric Box) Glassmorphism */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
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
    
    /* CSS cho hộp Chi tiết CRM Panel bên dưới */
    .crm-panel {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Tiêu đề ứng dụng
st.markdown('<div class="main-title">AI LEAD SCORING SYSTEM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống phân tích, chấm điểm khách hàng bất động sản tự động (Không dùng API)</div>', unsafe_allow_html=True)

# URL mặc định của Google Sheet dữ liệu
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1hRvHE6RXm1peVG07avfApPEHocOcPld9IA94hE3vUGE/export?format=csv"

# Sidebar thiết lập cấu hình Google Sheets
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5551/5551522.png", width=80)
st.sidebar.markdown("### ⚙️ Điều khiển & Cấu hình")

sheet_url = st.sidebar.text_input(
    "Đường dẫn Google Sheets (CSV Export)",
    value=DEFAULT_SHEET_URL,
    help="Địa chỉ xuất CSV của bảng tính chứa thông tin khách hàng."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 Quy tắc chấm điểm chính:
- **Cộng 50đ (Khách VIP - Nóng 🔥):** Ngân sách ≥ 20 tỷ; Tìm biệt thự đơn lập, penthouse, shophouse mặt đường lớn, quỹ đất lớn; Yêu cầu pháp lý 100%, gặp trực tiếp CĐT.
- **Trừ 50đ (Không Tiềm Năng - Rác 🗑️):** Yêu cầu phi thực tế (giá rẻ vô lý); Không có nhu cầu/nhầm số; Spam/Quảng cáo; Thuê bao/không bắt máy.
- **Giữ nguyên 50đ (Trung bình - Ấm ☀️):** Các phân khúc chung cư/nhà phố 3-10 tỷ, có nhu cầu thực cần tư vấn thêm.
""")

# Bộ phân tích dữ liệu quy tắc cục bộ (Không dùng API)
def local_lead_scoring(description):
    if not isinstance(description, str) or not description.strip():
        return 50, "Ấm", "🏠 Chung cư / Nhà phố", "Mô tả nhu cầu trống, mặc định 50đ"

    desc_lower = description.lower()
    score = 50
    reasons = []
    tags = []
    
    # 1. TIÊU CHÍ CỘNG 50 ĐIỂM (KHÁCH HÀNG NÓNG)
    is_vip = False
    
    # Kiểm tra ngân sách lớn
    has_large_budget = False
    if "tài chính mạnh" in desc_lower or "không thành vấn đề" in desc_lower:
        has_large_budget = True
        tags.append("💰 Tài chính mạnh")
        reasons.append("Tài chính mạnh / không thành vấn đề")
    else:
        budget_numbers = re.findall(r'(\d+(?:[\.,]\d+)?)\s*(?:tỷ|ty|tỉ)', desc_lower)
        for num in budget_numbers:
            try:
                val = float(num.replace(',', '.'))
                if val >= 20.0:
                    has_large_budget = True
                    tags.append(f"💰 Ngân sách lớn ({val} tỷ)")
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
        tags.append("🏰 Loại hình cao cấp")
        reasons.append(f"Loại hình cao cấp: {', '.join(matched_types)}")

    # Vị trí đắc địa
    vip_locations = ["quận 1", "ven sông", "vinhomes ocean park", "phú mỹ hưng"]
    matched_locations = [l for l in vip_locations if l in desc_lower]
    if matched_locations:
        is_vip = True
        tags.append("📍 Vị trí đắc địa")
        reasons.append(f"Vị trí đắc địa: {', '.join(matched_locations)}")

    # Đối tượng khách hàng VIP
    vip_targets = ["chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ", "mua số lượng lớn"]
    matched_targets = [tg for tg in vip_targets if tg in desc_lower]
    if matched_targets:
        is_vip = True
        tags.append("👑 Đối tượng VIP")
        reasons.append(f"Đối tượng khách hàng: {', '.join(matched_targets)}")

    # Tính cấp thiết & Minh bạch
    vip_urgency = ["pháp lý chuẩn 100%", "pháp lý chuẩn", "sổ hồng riêng", "gặp trực tiếp chủ đầu tư", "trực tiếp chủ đầu tư"]
    matched_urgency = [u for u in vip_urgency if u in desc_lower]
    if matched_urgency:
        is_vip = True
        tags.append("📜 Pháp lý chuẩn & Cấp thiết")
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
        tags.append("🔞 Sai số/Không nhu cầu")
        reasons.append(f"Không có nhu cầu: {', '.join(matched_no_need)}")

    # Khách không thiện chí
    not_serious = ["hỏi giá cho vui", "chưa có ý định mua", "thái độ không hợp tác"]
    matched_not_serious = [ns for ns in not_serious if ns in desc_lower]
    if matched_not_serious:
        is_trash = True
        tags.append("😷 Không thiện chí")
        reasons.append(f"Không thiện chí: {', '.join(matched_not_serious)}")

    # Spam/Quảng cáo
    spam_items = ["bảo hiểm", "vay vốn", "mời chào dịch vụ", "quảng cáo"]
    matched_spam = [s for s in spam_items if s in desc_lower]
    if matched_spam:
        is_trash = True
        tags.append("🚫 Spam / Quảng cáo")
        reasons.append(f"Spam/Quảng cáo: {', '.join(matched_spam)}")

    # Thông tin liên lạc lỗi
    comm_errors = ["thuê bao", "không bắt máy", "gọi nhiều lần không bắt máy", "không phản hồi zalo"]
    matched_comm_errors = [ce for ce in comm_errors if ce in desc_lower]
    if matched_comm_errors:
        is_trash = True
        tags.append("📉 Không liên lạc được")
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
        tags.append("🤖 Nhu cầu ảo (Q1 rẻ)")
        reasons.append("Yêu cầu phi thực tế: Nhà Quận 1 giá rẻ ≤ 2 tỷ")

    # Nhà trung tâm sân vườn hồ bơi vài trăm triệu
    has_garden_pool = "sân vườn" in desc_lower or "hồ bơi" in desc_lower
    has_million_price = "trăm triệu" in desc_lower or "vài trăm" in desc_lower or "triệu" in desc_lower
    has_ty = "tỷ" in desc_lower or "ty" in desc_lower or "tỉ" in desc_lower
    
    if has_garden_pool and has_million_price and not has_ty:
        is_trash = True
        tags.append("🤖 Nhu cầu ảo (Q1 rẻ)")
        reasons.append("Yêu cầu phi thực tế: Sân vườn hồ bơi giá vài trăm triệu")

    if is_trash:
        score = -50

    # 3. CÁC TRƯỜNG HỢP KHÁC
    if not is_vip and not is_trash:
        score = 50
        tags.append("🏠 Chung cư / Nhà phố")
        reasons.append("Phân khúc trung bình (3-10 tỷ)")

    classification = "Nóng" if score == 100 else ("Rác" if score == -50 else "Ấm")
    tag_str = " | ".join(tags)
    reason_str = " | ".join(reasons)
    
    return score, classification, tag_str, reason_str

# Hàm xử lý DataFrame và chấm điểm
def process_and_score_dataframe(df):
    if 'Số điện thoại' in df.columns:
        df['Số điện thoại'] = df['Số điện thoại'].fillna('').apply(lambda x: str(x).replace('.0', '') if str(x).endswith('.0') else str(x))
    
    scores = []
    classifications = []
    tags = []
    reasons = []
    
    for idx, row in df.iterrows():
        desc = row.get('Nhu cầu chi tiết', '')
        score_val, class_val, tag_val, reason_val = local_lead_scoring(desc)
        scores.append(score_val)
        classifications.append(class_val)
        tags.append(tag_val)
        reasons.append(reason_val)
    
    df['Điểm AI'] = scores
    df['Phân loại'] = classifications
    df['Từ khóa (Tags)'] = tags
    df['Lý do chấm điểm'] = reasons
    
    df['Trạng thái duyệt'] = "Chờ duyệt"
    df['Điểm cuối (Chốt)'] = df['Điểm AI']
    df['Ghi chú của Sales'] = ""
    
    return df

# Dữ liệu khách hàng mẫu mặc định để khởi tạo
MOCK_DATA_RECORDS = [
    {
        "Họ và tên": "Nguyễn Văn Hải",
        "Số điện thoại": "0912345678",
        "Nhu cầu chi tiết": "Cần mua biệt thự đơn lập Vinhomes Ocean Park 2 để đầu tư lâu dài, tài chính không thành vấn đề."
    },
    {
        "Họ và tên": "Trần Thị Bình",
        "Số điện thoại": "0987654321",
        "Nhu cầu chi tiết": "Tìm mua nhà Quận 1, yêu cầu nhà 3 tầng có sân vườn hồ bơi giá 1-2 tỷ."
    },
    {
        "Họ và tên": "Lê Hoàng Nam",
        "Số điện thoại": "0905123456",
        "Nhu cầu chi tiết": "Đang tìm hiểu căn hộ chung cư 2 phòng ngủ khu vực trung tâm giá tầm 3-5 tỷ."
    },
    {
        "Họ và tên": "Phạm Minh An",
        "Số điện thoại": "0934567890",
        "Nhu cầu chi tiết": "Nhầm số, không có nhu cầu mua bất động sản lúc này."
    },
    {
        "Họ và tên": "Hoàng Anh Đức",
        "Số điện thoại": "0978901234",
        "Nhu cầu chi tiết": "Cần thuê mặt bằng shophouse mặt đường lớn tại Phú Mỹ Hưng mở showroom nội thất."
    }
]

# Khởi tạo dữ liệu mặc định vào session state
if 'df_scored' not in st.session_state or st.session_state.df_scored is None:
    default_df = pd.DataFrame(MOCK_DATA_RECORDS)
    st.session_state.df_scored = process_and_score_dataframe(default_df)

# Nút bấm tải dữ liệu từ Google Sheets
if st.sidebar.button("🔄 Tải dữ liệu từ Google Sheet", use_container_width=True):
    with st.sidebar.spinner("Đang tải dữ liệu..."):
        try:
            df_google = pd.read_csv(sheet_url)
            st.session_state.df_scored = process_and_score_dataframe(df_google)
            st.sidebar.success("🎉 Đã cập nhật dữ liệu từ Google Sheet!")
        except Exception as e:
            st.sidebar.error(f"⚠️ Lỗi kết nối Google Sheet: {str(e)}")

# Đọc dữ liệu hiện tại
df_data = st.session_state.df_scored.copy()

# ==================== PHẦN HIỂN THỊ CHÍNH ====================

# ------------------ PHẦN 1: THỐNG KÊ TỔNG QUAN ------------------
st.markdown('<div class="section-title">📊 1. Thống Kê Tổng Quan</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Tóm tắt số liệu phân loại khách hàng tiềm năng tự động</div>', unsafe_allow_html=True)

# Tính toán các chỉ số thống kê
total_leads = len(df_data)
hot_count = len(df_data[df_data['Phân loại'] == 'Nóng'])
warm_count = len(df_data[df_data['Phân loại'] == 'Ấm'])
trash_count = len(df_data[df_data['Phân loại'] == 'Rác'])

approved_count = len(df_data[df_data['Trạng thái duyệt'] == 'Đã phê duyệt'])
rejected_count = len(df_data[df_data['Trạng thái duyệt'] == 'Loại bỏ'])
pending_count = len(df_data[df_data['Trạng thái duyệt'] == 'Chờ duyệt'])

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #38bdf8;">{total_leads}</div>
        <div class="metric-label">Tổng Lead</div>
    </div>
    """, unsafe_allow_html=True)
with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #10b981;">{hot_count}</div>
        <div class="metric-label">Lead Nóng 🔥</div>
    </div>
    """, unsafe_allow_html=True)
with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #f59e0b;">{warm_count}</div>
        <div class="metric-label">Lead Ấm ☀️</div>
    </div>
    """, unsafe_allow_html=True)
with col_m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #ef4444;">{trash_count}</div>
        <div class="metric-label">Lead Rác 🗑️</div>
    </div>
    """, unsafe_allow_html=True)

# Thống kê phê duyệt hàng nhỏ hơn bên dưới
col_m5, col_m6, col_m7 = st.columns(3)
with col_m5:
    st.markdown(f"""
    <div class="metric-card" style="padding: 12px; margin-top: 10px;">
        <div class="metric-value" style="color: #10b981; font-size: 1.6rem;">{approved_count}</div>
        <div class="metric-label" style="font-size: 0.8rem;">Đã phê duyệt</div>
    </div>
    """, unsafe_allow_html=True)
with col_m6:
    st.markdown(f"""
    <div class="metric-card" style="padding: 12px; margin-top: 10px;">
        <div class="metric-value" style="color: #ef4444; font-size: 1.6rem;">{rejected_count}</div>
        <div class="metric-label" style="font-size: 0.8rem;">Đã loại bỏ</div>
    </div>
    """, unsafe_allow_html=True)
with col_m7:
    st.markdown(f"""
    <div class="metric-card" style="padding: 12px; margin-top: 10px;">
        <div class="metric-value" style="color: #f59e0b; font-size: 1.6rem;">{pending_count}</div>
        <div class="metric-label" style="font-size: 0.8rem;">Chờ kiểm duyệt</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Vẽ biểu đồ thống kê phân bổ lead
st.markdown("##### 📈 Biểu đồ phân bổ phân loại Lead")
chart_df = pd.DataFrame({
    'Số lượng': [hot_count, warm_count, trash_count]
}, index=['Nóng 🔥', 'Ấm ☀️', 'Rác 🗑️'])
st.bar_chart(chart_df)

st.write("")

# ------------------ PHẦN 2: BẢN KIỂM DUYỆT ------------------
st.markdown('<div class="section-title">📝 2. Bản Kiểm Duyệt (Dành cho Kế Toán / Sales)</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Hệ thống đã tự động gán Từ khóa (Tags) và Gợi ý hành động. Bạn có thể dùng bộ lọc dưới đây để tìm và phê duyệt khách hàng nhanh chóng.</div>', unsafe_allow_html=True)

# ------------------ PHẦN 1: BỘ LỌC DỮ LIỆU THÔNG MINH ------------------
st.markdown('<div class="filter-header">🔎 Bộ Lọc Dữ Liệu Thông Minh</div>', unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
with col_f1:
    filter_class = st.multiselect(
        "Lọc theo Phân loại AI:",
        options=["Nóng", "Ấm", "Rác"],
        default=["Nóng", "Ấm", "Rác"],
        key="main_filter_class"
    )
with col_f2:
    # Lấy các trạng thái duyệt hiện có trong dữ liệu để làm option
    status_options = list(df_data['Trạng thái duyệt'].unique())
    if "Chờ duyệt" not in status_options:
        status_options.append("Chờ duyệt")
    filter_status = st.multiselect(
        "Lọc theo Trạng thái duyệt:",
        options=status_options,
        default=["Chờ duyệt"] if "Chờ duyệt" in status_options else [status_options[0]],
        key="main_filter_status"
    )
with col_f3:
    search_name = st.text_input(
        "Tìm kiếm theo Tên / SĐT:",
        value="",
        placeholder="Nhập từ khóa tìm kiếm...",
        key="main_search_name"
    )

# Áp dụng bộ lọc
filtered_df = df_data.copy()
if filter_class:
    filtered_df = filtered_df[filtered_df['Phân loại'].isin(filter_class)]
if filter_status:
    filtered_df = filtered_df[filtered_df['Trạng thái duyệt'].isin(filter_status)]
if search_name:
    filtered_df = filtered_df[
        filtered_df['Họ và tên'].str.contains(search_name, case=False, na=False) |
        filtered_df['Số điện thoại'].astype(str).str.contains(search_name, case=False, na=False)
    ]

# ------------------ PHẦN 2: HÀNH ĐỘNG NHANH (BATCH ACTIONS) ------------------
st.markdown("---")
st.markdown('<div class="filter-header">⚡ Hành Động Nhanh</div>', unsafe_allow_html=True)

col_act1, col_act2, col_act_space = st.columns([3, 3, 4])
with col_act1:
    # Button phê duyệt toàn bộ Nóng & Ấm trong danh sách đang lọc
    if st.button("✅ Phê duyệt toàn bộ khách Nóng & Ấm", use_container_width=True):
        main_df = st.session_state.df_scored
        # Tìm các dòng thỏa mãn trong danh sách đang lọc
        target_sdt_list = filtered_df[filtered_df['Phân loại'].isin(["Nóng", "Ấm"])]['Số điện thoại'].tolist()
        if target_sdt_list:
            main_df.loc[main_df['Số điện thoại'].isin(target_sdt_list), 'Trạng thái duyệt'] = "Đã phê duyệt"
            main_df.loc[main_df['Số điện thoại'].isin(target_sdt_list), 'Điểm cuối (Chốt)'] = main_df['Điểm AI']
            st.session_state.df_scored = main_df
            st.success(f"🎉 Đã phê duyệt trạng thái cho {len(target_sdt_list)} khách hàng Nóng & Ấm!")
            st.rerun()
        else:
            st.warning("Không tìm thấy khách hàng Nóng/Ấm nào trong danh sách đang lọc.")

with col_act2:
    # Button loại bỏ toàn bộ khách Rác trong danh sách đang lọc
    if st.button("🗑️ Loại bỏ toàn bộ khách Rác", use_container_width=True):
        main_df = st.session_state.df_scored
        target_sdt_list = filtered_df[filtered_df['Phân loại'] == "Rác"]['Số điện thoại'].tolist()
        if target_sdt_list:
            main_df.loc[main_df['Số điện thoại'].isin(target_sdt_list), 'Trạng thái duyệt'] = "Loại bỏ"
            main_df.loc[main_df['Số điện thoại'].isin(target_sdt_list), 'Điểm cuối (Chốt)'] = -50
            st.session_state.df_scored = main_df
            st.success(f"🗑️ Đã đánh dấu loại bỏ {len(target_sdt_list)} khách hàng phân loại Rác!")
            st.rerun()
        else:
            st.warning("Không tìm thấy khách hàng Rác nào trong danh sách đang lọc.")

# ------------------ PHẦN 3: BẢNG KIỂM DUYỆT CHÍNH ------------------
st.write("")
# Format cột hiển thị tương tự ảnh mẫu
display_df = filtered_df.copy()
display_df = display_df.reset_index(drop=True)
display_df['Mã KH'] = display_df.index + 1

# Rename các cột cho giống ảnh mẫu
display_df = display_df.rename(columns={
    "Họ và tên": "Tên Khách Hàng",
    "Số điện thoại": "Số Điện Thoại",
    "Nhu cầu chi tiết": "Ghi chú Nhu cầu",
    "Phân loại": "Phân loại"
})

# Sắp xếp thứ tự cột
columns_order = [
    "Mã KH", "Tên Khách Hàng", "Số Điện Thoại", "Ghi chú Nhu cầu", 
    "Điểm AI", "Phân loại", "Từ khóa (Tags)", "Trạng thái duyệt", "Ghi chú của Sales"
]
# Đảm bảo các cột tồn tại đầy đủ
for col in columns_order:
    if col not in display_df.columns:
        display_df[col] = ""

st.dataframe(
    display_df[columns_order],
    width="stretch"
)

# ------------------ PHẦN 4: CRM PANEL - DUYỆT TỪNG DÒNG CHI TIẾT ------------------
st.markdown("---")
st.markdown('### ⚡ CRM Action Panel - Chi tiết hành động & Duyệt đơn lẻ')

if len(filtered_df) > 0:
    customer_names = filtered_df['Họ và tên'].tolist()
    selected_customer = st.selectbox("👉 Chọn tên khách hàng xử lý:", options=customer_names, key="crm_selectbox")
    
    # Lấy thông tin khách hàng được chọn
    customer_data = filtered_df[filtered_df['Họ và tên'] == selected_customer].iloc[0]
    
    # Thẻ CRM Panel
    st.markdown(f"""
    <div class="crm-panel">
        <h4 style="color:#38bdf8;margin-bottom:10px;margin-top:0;">🏢 Khách hàng: {customer_data['Họ và tên']} ({customer_data['Số điện thoại']})</h4>
        <p style="margin-bottom:8px;"><strong>Nhu cầu chi tiết:</strong> {customer_data['Nhu cầu chi tiết']}</p>
        <p style="margin-bottom:8px;"><strong>Phân loại AI:</strong> <span style="color:#10b981;font-weight:bold;">{customer_data['Phân loại']}</span> (Điểm: {customer_data['Điểm AI']})</p>
        <p style="margin-bottom:8px;"><strong>Từ khóa nhận diện:</strong> <em>{customer_data['Từ khóa (Tags)']}</em></p>
        <p style="margin-bottom:0;"><strong>Trạng thái duyệt:</strong> <span style="color:#f59e0b;font-weight:bold;">{customer_data['Trạng thái duyệt']}</span> | <strong>Điểm chốt cuối:</strong> {customer_data['Điểm cuối (Chốt)']}đ</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Ghi chú Note Action
    current_note = customer_data['Ghi chú của Sales'] if pd.notna(customer_data['Ghi chú của Sales']) else ""
    note_action = st.text_area("✍️ Ghi chú hành động / Note Action:", value=current_note, placeholder="Nhập ghi chú hành động hoặc lý do phê duyệt...", key="crm_note")
    
    col_single1, col_single2 = st.columns(2)
    with col_single1:
        if st.button("✅ Phê duyệt Khách hàng này", use_container_width=True, key="btn_single_approve"):
            main_df = st.session_state.df_scored
            idx_in_main = main_df[main_df['Số điện thoại'] == customer_data['Số điện thoại']].index[0]
            main_df.at[idx_in_main, 'Trạng thái duyệt'] = "Đã phê duyệt"
            main_df.at[idx_in_main, 'Điểm cuối (Chốt)'] = customer_data['Điểm AI']
            main_df.at[idx_in_main, 'Ghi chú của Sales'] = note_action
            st.session_state.df_scored = main_df
            st.success(f"🎉 Đã phê duyệt cho khách hàng: **{selected_customer}**!")
            st.rerun()
            
    with col_single2:
        if st.button("❌ Loại bỏ Khách hàng này", use_container_width=True, key="btn_single_reject"):
            main_df = st.session_state.df_scored
            idx_in_main = main_df[main_df['Số điện thoại'] == customer_data['Số điện thoại']].index[0]
            main_df.at[idx_in_main, 'Trạng thái duyệt'] = "Loại bỏ"
            main_df.at[idx_in_main, 'Điểm cuối (Chốt)'] = -50
            main_df.at[idx_in_main, 'Ghi chú của Sales'] = note_action
            st.session_state.df_scored = main_df
            st.success(f"⚠️ Đã đánh dấu loại bỏ đối với khách hàng: **{selected_customer}**!")
            st.rerun()
else:
    st.write("Không tìm thấy khách hàng nào khớp bộ lọc.")

# ------------------ PHẦN 5: BÀN GIAO DỮ LIỆU (EXPORT) ------------------
st.markdown("---")
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

col_dl, col_space = st.columns([1, 3])
with col_dl:
    st.download_button(
        label="📥 Tải xuống File Excel Bàn Giao",
        data=excel_data,
        file_name="Lead_Scoring_CRM_Final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
