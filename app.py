import streamlit as st
import utils
import sys
import os

st.set_page_config(
    page_title="Aytens Takı & Tasarım - E-Ticaret Otomasyonu",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .web-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    .section-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .section-subtitle {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

auth_data = utils.load_auth()

# --- ŞİFRELİ GİRİŞ EKRANI ---
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        st.write("")
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>🔒 Yönetici Girişi</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px;'>Aytens Takı & Tasarım Yönetim Paneli</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form", clear_on_submit=False):
            kadi = st.text_input("Kullanıcı Adı:", placeholder="Kullanıcı adınızı girin...")
            sifre = st.text_input("Şifre:", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("🚀 Giriş Yap", use_container_width=True, type="primary")
            
            if submit_btn:
                clean_kadi = kadi.strip()
                clean_sifre = sifre.strip()
                
                if clean_kadi == auth_data.get("username", "") and clean_sifre == auth_data.get("password", ""):
                    st.session_state["logged_in"] = True
                    st.rerun()
                elif clean_kadi in auth_data.get("users", {}) and str(auth_data.get("users", {})[clean_kadi]) == clean_sifre:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- YÖNETİM PANELİ ANA EKRANI ---
with st.sidebar:
    st.markdown("### 💎 Aytens Takı & Tasarım")
    st.markdown("<p style='font-size:12px; color:#64748b;'>E-Ticaret & Otomasyon Paneli</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    secilen_sayfa = st.radio(
        "📌 Menü Navigasyonu:",
        ["🏠 Ana Sayfa", "📈 Satış & Kârlılık Analizi", "⚙️ Ayarlar & API"],
        index=0
    )
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# --- SAYFA YÖNLENDİRİCİSİ ---
if secilen_sayfa == "🏠 Ana Sayfa":
    st.markdown('<div class="section-title">🏠 Yönetim Paneline Hoş Geldiniz</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Sol menüyü kullanarak mağaza analizlerinize ulaşabilir veya API ayarlarınızı yapılandırabilirsiniz.</div>', unsafe_allow_html=True)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("""
        <div class="web-card">
            <h4>📈 Hızlı Satış Analizi</h4>
            <p style="color:#64748b; font-size:13px;">Trendyol, Hepsiburada ve aytens.com (WooCommerce) mağazalarınızdan gerçek zamanlı API verilerini çekerek net kâr, komisyon ve kargo giderlerinizi inceleyin.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown("""
        <div class="web-card">
            <h4>⚙️ Güvenli API Yönetimi</h4>
            <p style="color:#64748b; font-size:13px;">Pazaryeri ve e-ticaret sitenizin API anahtarlarını, mağaza ID'lerini ve bağlantı sırlarını kalıcı olarak kaydedin ve yönetin.</p>
        </div>
        """, unsafe_allow_html=True)

elif secilen_sayfa == "📈 Satış & Kârlılık Analizi":
    try:
        from Sayfalar import satis_analizi
        satis_analizi.render()
    except ImportError as e:
        st.error(f"❌ Sayfalar/satis_analizi.py dosyası bulunamadı veya yüklenemedi: {str(e)}")
        st.info("💡 Lütfen projenizde `Sayfalar` klasörünün ve içinde `satis_analizi.py` dosyasının oluşturulduğundan emin olun.")

elif secilen_sayfa == "⚙️ Ayarlar & API":
    try:
        from Sayfalar import ayarlar_api
        ayarlar_api.render()
    except ImportError as e:
        st.error(f"❌ Sayfalar/ayarlar_api.py dosyası bulunamadı veya yüklenemedi: {str(e)}")
        st.info("💡 Lütfen projenizde `Sayfalar` klasörünün ve içinde `ayarlar_api.py` dosyasının oluşturulduğundan emin olun.")
