import streamlit as st

st.set_page_config(
    page_title="E-Ticaret & Karar Destek Paneli",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. BULLETPROOF OTURUM (AUTH) VE F5 YENİLEME KORUMASI ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Tarayıcı URL parametresini kontrol et (F5 yapıldığında URL'de auth anahtarı varsa girişi otomatik aç)
try:
    auth_token = st.query_params.get("auth")
except AttributeError:
    # Eski Streamlit sürümleri için uyumluluk
    params = st.experimental_get_query_params()
    auth_token = params.get("auth", [None])[0] if "auth" in params else None

if auth_token == "valid_admin_2026":
    st.session_state["logged_in"] = True

def login_screen():
    st.markdown("<h2 style='text-align: center; margin-top: 60px; color: #0f172a;'>🔐 Aytens Takı & Tasarım | Yönetim Girişi</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            sifre = st.text_input("Yönetici Şifresi", type="password", placeholder="Şifrenizi girin...")
            submit = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
            if submit:
                # Kolaylık sağlamak ve test için boş bırakmaya veya 123456/admin şifrelerine izin ver
                if sifre in ["123456", "admin", "aytens", ""]:
                    st.session_state["logged_in"] = True
                    try:
                        st.query_params["auth"] = "valid_admin_2026"
                    except AttributeError:
                        st.experimental_set_query_params(auth="valid_admin_2026")
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# Oturum açıkken her yenilemede veya buton tıklamasında URL parametresinin kaybolmasını kesin olarak engelle
try:
    if st.query_params.get("auth") != "valid_admin_2026":
        st.query_params["auth"] = "valid_admin_2026"
except AttributeError:
    pass

# --- 2. KESİNLİKLE EŞİT BOYUTLU VE NİZAMİ BUTON CSS'İ ---
st.markdown("""
<style>
/* Ana gövde boşluklarını ve genişliğini düzenle */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 98% !important;
}

/* Tüm menü butonlarını milimetrik olarak aynı yükseklik ve genişliğe zorla */
div[data-testid="column"] button,
div[data-testid="stButton"] button {
    width: 100% !important;
    height: 52px !important;
    min-height: 52px !important;
    max-height: 52px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    padding: 0px 4px !important;
    margin: 0px !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    box-sizing: border-box !important;
}

/* Buton içi metinlerin ve ikonların kaymasını engelle */
div[data-testid="column"] button p,
div[data-testid="stButton"] button p {
    margin: 0px !important;
    padding: 0px !important;
    line-height: 1 !important;
    font-size: 13.5px !important;
}

/* Web kartı ve başlık tasarımları */
.web-card {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 4px;
}
.section-subtitle {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 20px;
}
.stat-badge {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-left: 5px solid #3b82f6;
    border-radius: 8px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stat-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; }
.stat-value { font-size: 20px; font-weight: 800; color: #0f172a; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# --- 3. ÜST BİLGİ VE ÇIKIŞ BUTONU ---
top_c1, top_c2 = st.columns([8.5, 1])
with top_c1:
    st.markdown("### 💎 Aytens Takı & Tasarım | Karar Destek Sistemi")
with top_c2:
    if st.button("🚪 Çıkış Yap", key="logout_btn", type="secondary"):
        st.session_state["logged_in"] = False
        try:
            st.query_params.clear()
        except AttributeError:
            st.experimental_set_query_params()
        st.rerun()

st.markdown("---")

# --- 4. EŞİT VE NİZAMİ MENÜ SEKMELERİ ---
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "📈 Satış Analizi"

nav_cols = st.columns(7)
pages = ["📊 Kontrol Paneli", "📈 Satış Analizi", "📦 Maliyet Yönetimi", "🧮 İdeal Fiyatlama", "🚀 Trendyol Yıldız", "💜 Hepsiburada Teklif", "⚙️ Ayarlar & API"]

for idx, page_name in enumerate(pages):
    with nav_cols[idx]:
        is_active = (st.session_state["active_page"] == page_name)
        btn_type = "primary" if is_active else "secondary"
        if st.button(page_name, key=f"nav_{idx}", type=btn_type):
            st.session_state["active_page"] = page_name
            st.rerun()

st.write("")

# --- 5. SAYFA YÖNLENDİRİCİSİ ---
active = st.session_state["active_page"]
if active == "📊 Kontrol Paneli":
    st.info("Kontrol paneli modülü aktif.")
elif active == "📈 Satış Analizi":
    import Sayfalar.satis_analizi as satis_analizi
    satis_analizi.render()
elif active == "📦 Maliyet Yönetimi":
    st.info("Maliyet yönetimi modülü aktif.")
elif active == "🧮 İdeal Fiyatlama":
    st.info("İdeal fiyatlama modülü aktif.")
elif active == "🚀 Trendyol Yıldız":
    st.info("Trendyol yıldız modülü aktif.")
elif active == "💜 Hepsiburada Teklif":
    st.info("Hepsiburada teklif modülü aktif.")
elif active == "⚙️ Ayarlar & API":
    st.info("Ayarlar ve API yapılandırması.")
