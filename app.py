import streamlit as st
import numpy as np
from datetime import datetime
import utils

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Avantajlı Ürün | E-Ticaret Yönetim Portalı",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- OTURUM (SESSION) KONTROLLERİ ---
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "current_user" not in st.session_state: st.session_state["current_user"] = ""
if "active_page" not in st.session_state: st.session_state["active_page"] = "📊 Kontrol Paneli"

if "captcha_num1" not in st.session_state or "captcha_num2" not in st.session_state:
    st.session_state["captcha_num1"] = np.random.randint(1, 10)
    st.session_state["captcha_num2"] = np.random.randint(1, 10)

def reset_captcha():
    st.session_state["captcha_num1"] = np.random.randint(1, 10)
    st.session_state["captcha_num2"] = np.random.randint(1, 10)

auth_data = utils.load_auth()

# --- WEB SİTESİ (SaaS) CSS STİLLERİ ---
st.markdown("""
    <style>
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
    
    .top-navbar {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 18px 30px; border-radius: 16px; color: white; display: flex;
        justify-content: space-between; align-items: center; margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .nav-brand { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #38bdf8; }
    .nav-brand span { color: #f8fafc; font-weight: 400; }
    .nav-user { background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500; border: 1px solid rgba(255,255,255,0.15); }
    
    .web-card { background: white; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); margin-bottom: 20px; transition: all 0.3s ease; }
    .web-card:hover { box-shadow: 0 10px 15px -3px rgba(0,0,0,0.06); border-color: #cbd5e1; }
    
    .stat-badge { background: white; padding: 18px; border-radius: 14px; border: 1px solid #e2e8f0; border-left: 5px solid #0284c7; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .stat-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }
    .stat-value { font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 4px; }
    
    .stButton>button { background: white; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px 16px; font-weight: 600; transition: all 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .stButton>button:hover { border-color: #0284c7; color: #0284c7; background: #f0f9ff; transform: translateY(-1px); }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; padding: 10px 20px; font-weight: 600; color: #64748b; border: none; }
    .stTabs [aria-selected="true"] { background-color: #e0f2fe !important; color: #0284c7 !important; }
    
    .section-title { font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px; letter-spacing: -0.5px; }
    .section-subtitle { font-size: 14px; color: #64748b; margin-bottom: 22px; }
    </style>
""", unsafe_allow_html=True)

# --- PORTAL GİRİŞ EKRANI ---
if not st.session_state["logged_in"]:
    st.markdown("""
        <div style="max-width: 440px; margin: 80px auto 20px auto; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 10px;">🔐</div>
            <h1 style="font-size: 28px; font-weight: 800; color: #0f172a;">Avantajlı Ürün <span style="color:#0284c7; font-weight:400;">Portal</span></h1>
            <p style="color: #64748b; font-size: 14px;">E-Ticaret Satış, Kârlılık ve Otomasyon Paneli</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔑 Oturum Açın")
            kadi = st.text_input("Kullanıcı Adı", placeholder="Örn: admin")
            sifre = st.text_input("Şifre", type="password", placeholder="••••••••")
            
            st.markdown("---")
            st.markdown("#### 🛡️ Güvenlik Doğrulaması")
            num1 = st.session_state["captcha_num1"]
            num2 = st.session_state["captcha_num2"]
            captcha_ans = st.text_input(f"🤖 Doğrulama: {num1} + {num2} kaçtır?", placeholder="Sonucu yazın")
            
            if st.form_submit_button("🚀 Giriş Yap ve Panele Git", use_container_width=True):
                try: user_ans = int(captcha_ans.strip())
                except ValueError: user_ans = -1
                if user_ans != (num1 + num2):
                    st.error("❌ Güvenlik sorusunu yanlış cevapladınız!"); reset_captcha()
                elif kadi.strip() in auth_data["users"] and auth_data["users"][kadi.strip()] == sifre.strip():
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = kadi.strip()
                    st.success("✅ Giriş Başarılı! Yönlendiriliyorsunuz..."); st.rerun()
                else:
                    st.error("❌ Kullanıcı adı veya şifre hatalı!"); reset_captcha()
    st.stop()

# --- ÜST WEB NAVİGASYON BAR ---
st.markdown(f"""
    <div class="top-navbar">
        <div class="nav-brand">🚀 AVANTAJLI<span>ÜRÜN</span> <span style="font-size:11px; background:#0284c7; color:white; padding:3px 8px; border-radius:6px; margin-left:8px;">PRO SAAS</span></div>
        <div style="display:flex; align-items:center; gap:15px;">
            <div class="nav-user">👤 Aktif Kullanıcı: <b>{st.session_state['current_user']}</b></div>
            <div style="font-size:13px; color:#94a3b8;">📅 {datetime.now().strftime('%d.%m.%Y')}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- YATAY WEB MENÜSÜ ---
nav_cols = st.columns(7)
pages = ["📊 Kontrol Paneli", "📈 Satış Analizi", "📦 Maliyet Yönetimi", "🧮 İdeal Fiyatlama", "🚀 Trendyol Yıldız", "💜 Hepsiburada Teklif", "⚙️ Ayarlar & API"]
for idx, p_name in enumerate(pages):
    with nav_cols[idx]:
        if st.button(p_name, use_container_width=True, key=f"btn_{idx}"):
            st.session_state["active_page"] = p_name

active_page = st.session_state["active_page"]
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

# --- MODÜLER SAYFA YÖNLENDİRİCİSİ ---
if active_page == "📊 Kontrol Paneli":
    from Sayfalar import dashboard
    dashboard.render()
elif active_page == "📦 Maliyet Yönetimi":
    from Sayfalar import maliyet
    maliyet.render()
elif active_page == "🧮 İdeal Fiyatlama":
    from Sayfalar import fiyatlama
    fiyatlama.render()
elif active_page == "🚀 Trendyol Yıldız":
    from Sayfalar import trendyol
    trendyol.render()
elif active_page == "💜 Hepsiburada Teklif":
    from Sayfalar import hepsiburada
    hepsiburada.render()
elif active_page == "⚙️ Ayarlar & API":
    from Sayfalar import ayarlar
    ayarlar.render()
elif active_page == "📈 Satış Analizi":
    from Sayfalar import satis_analizi
    satis_analizi.render()
