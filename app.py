import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="E-Ticaret & Karar Destek Paneli",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ÇIKIŞ YAPMAYI ENGELLEYEN OTURUM (AUTH) YÖNETİMİ ---
# Sayfa yenilendiğinde (F5) oturumun düşmemesi için tarayıcının URL parametrelerinde (st.query_params) güvenlik anahtarı tutuyoruz.
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# URL'de geçerli bir oturum anahtarı varsa otomatik giriş yap
if st.query_params.get("auth") == "sec_valid_token_2026":
    st.session_state["logged_in"] = True

def login_screen():
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔐 E-Ticaret Yönetim Paneli Giriş</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            sifre = st.text_input("Yönetici Şifresi", type="password", placeholder="••••••••")
            submit = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)
            if submit:
                if sifre == "123456" or sifre == "admin" or sifre == "": # Kolay test için boş geçişe de izin verildi
                    st.session_state["logged_in"] = True
                    st.query_params["auth"] = "sec_valid_token_2026"
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# --- BUTONLARIN KESİNLİKLE AYNI BOYUTTA OLMASINI SAĞLAYAN BULLETPROOF CSS ---
st.markdown("""
<style>
/* Ana gövde boşluklarını düzenle */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 98% !important;
}

/* Üst navigasyon sütunlarındaki TÜM butonları zorla eşitle */
div[data-testid="column"] > div > div > div > div > button,
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
    font-size: 13px !important;
    font-weight: 700 !important;
    padding: 0px 2px !important;
    margin: 0px !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    box-sizing: border-box !important;
}

/* Buton içindeki paragrafların satır yüksekliğini ve marginlerini sıfırla */
div[data-testid="column"] button p {
    margin: 0px !important;
    padding: 0px !important;
    line-height: 1 !important;
    font-size: 13px !important;
}

/* Kart tasarımları */
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

# --- ÜST BİLGİ VE ÇIKIŞ BUTONU ---
top_c1, top_c2 = st.columns([8, 1])
with top_c1:
    st.markdown("### 💎 Aytens Takı & Tasarım | Karar Destek Sistemi")
with top_c2:
    if st.button("🚪 Çıkış", key="logout_btn"):
        st.session_state["logged_in"] = False
        st.query_params.clear()
        st.rerun()

st.markdown("---")

# --- YATAY WEB MENÜSÜ (EŞİT BOYUTLU BUTONLAR) ---
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "📊 Kontrol Paneli"

nav_cols = st.columns(7)
pages = ["📊 Kontrol Paneli", "📈 Satış Analizi", "📦 Maliyet Yönetimi", "🧮 İdeal Fiyatlama", "🚀 Trendyol Yıldız", "💜 Hepsiburada Teklif", "⚙️ Ayarlar & API"]

for idx, page_name in enumerate(pages):
    with nav_cols[idx]:
        is_active = (st.session_state["active_page"] == page_name)
        btn_type = "primary" if is_active else "secondary"
        if st.button(page_name, key=f"nav_{idx}", type=btn_type):
            st.session_state["active_page"] = page_name
            st.rerun()

st.write("") # Boşluk

# --- SAYFA YÖNLENDİRİCİSİ ---
active = st.session_state["active_page"]
if active == "📊 Kontrol Paneli":
    st.info("Kontrol paneli yükleniyor...")
elif active == "📈 Satış Analizi":
    from Sayfalar import satis_analizi
    satis_analizi.render()
elif active == "📦 Maliyet Yönetimi":
    st.info("Maliyet yönetimi yükleniyor...")
elif active == "🧮 İdeal Fiyatlama":
    st.info("İdeal fiyatlama yükleniyor...")
elif active == "🚀 Trendyol Yıldız":
    st.info("Trendyol yıldız yükleniyor...")
elif active == "💜 Hepsiburada Teklif":
    st.info("Hepsiburada teklif yükleniyor...")
elif active == "⚙️ Ayarlar & API":
    st.info("Ayarlar yükleniyor...")
