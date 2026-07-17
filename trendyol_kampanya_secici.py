import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
from io import BytesIO
from datetime import datetime, timedelta, date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- SAYFA YAPILANDIRMASI (WEB SİTESİ TARZI) ---
st.set_page_config(
    page_title="Avantajlı Ürün | E-Ticaret Yönetim Portalı",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"  # Yanal menüyü web stili için kapattık
)

# --- DOSYA YOLLARI ---
DB_FILE = 'urun_maliyet_veritabani.csv'
API_FILE = 'api_ayarlari.json'
AUTH_FILE = 'auth_config.json'

# --- KULLANICI YÖNETİMİ & DOĞRULAMA ---
def load_auth():
    default_auth = {"users": {"aliozer73": "Ayten136"}}
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if "username" in saved and "password" in saved and "users" not in saved:
                    default_auth["users"][saved["username"]] = saved["password"]
                elif "users" in saved and isinstance(saved["users"], dict):
                    default_auth["users"].update(saved["users"])
        except Exception:
            pass
    else:
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_auth, f, ensure_ascii=False, indent=4)
    return default_auth

def save_auth(auth_data):
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(auth_data, f, ensure_ascii=False, indent=4)

if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "current_user" not in st.session_state: st.session_state["current_user"] = ""
if "active_page" not in st.session_state: st.session_state["active_page"] = "📊 Kontrol Paneli"

if "captcha_num1" not in st.session_state or "captcha_num2" not in st.session_state:
    st.session_state["captcha_num1"] = np.random.randint(1, 10)
    st.session_state["captcha_num2"] = np.random.randint(1, 10)

def reset_captcha():
    st.session_state["captcha_num1"] = np.random.randint(1, 10)
    st.session_state["captcha_num2"] = np.random.randint(1, 10)

auth_data = load_auth()

# --- MODERN WEB SİTESİ (SaaS) CSS STİLLERİ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Üst Navigasyon Çubuğu (Navbar) */
    .top-navbar {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 18px 30px;
        border-radius: 16px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .nav-brand { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #38bdf8; }
    .nav-brand span { color: #f8fafc; font-weight: 400; }
    .nav-user { background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500; border: 1px solid rgba(255,255,255,0.15); }
    
    /* Modern Kartlar */
    .web-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .web-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.06);
        border-color: #cbd5e1;
    }
    
    /* İstatistik Badgeleri */
    .stat-badge {
        background: white;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stat-label { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }
    .stat-value { font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 4px; }
    
    /* Buton Özelleştirmeleri */
    .stButton>button {
        background: white;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 10px 16px;
        font-weight: 600;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        border-color: #0284c7;
        color: #0284c7;
        background: #f0f9ff;
        transform: translateY(-1px);
    }
    
    /* Tablo & Sekme Düzeni */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 8px; padding: 10px 20px; font-weight: 600; color: #64748b; border: none; }
    .stTabs [aria-selected="true"] { background-color: #e0f2fe !important; color: #0284c7 !important; }
    
    /* Başlık Stilleri */
    .section-title { font-size: 24px; font-weight: 800; color: #0f172a; margin-bottom: 4px; letter-spacing: -0.5px; }
    .section-subtitle { font-size: 14px; color: #64748b; margin-bottom: 22px; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ EKRANI (WEB PORTAL GİRİŞİ) ---
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
            kadi = st.text_input("Kullanıcı Adı", placeholder="Örn: aliozer73")
            sifre = st.text_input("Şifre", type="password", placeholder="••••••••")
            
            st.markdown("---")
            st.markdown("#### 🛡️ Güvenlik Doğrulaması")
            num1 = st.session_state["captcha_num1"]
            num2 = st.session_state["captcha_num2"]
            captcha_ans = st.text_input(f"🤖 Doğrulama: {num1} + {num2} kaçtır?", placeholder="Sonucu yazın")
            
            submit = st.form_submit_button("🚀 Giriş Yap ve Panele Git", use_container_width=True)
            
            if submit:
                try: user_ans = int(captcha_ans.strip())
                except ValueError: user_ans = -1
                    
                if user_ans != (num1 + num2):
                    st.error("❌ Güvenlik sorusunu yanlış cevapladınız!")
                    reset_captcha()
                elif kadi.strip() in auth_data["users"] and auth_data["users"][kadi.strip()] == sifre.strip():
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = kadi.strip()
                    st.success("✅ Giriş Başarılı! Yönlendiriliyorsunuz...")
                    st.rerun()
                else:
                    st.error("❌ Kullanıcı adı veya şifre hatalı!")
                    reset_captcha()
    st.stop()

# --- YARDIMCI FONKSİYONLAR ---
def tablayi_1den_baslat(df):
    df_copy = df.copy()
    df_copy.index = np.arange(1, len(df_copy) + 1)
    df_copy.index.name = "Sıra"
    return df_copy

def temizle_ve_sayiya_donustur(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).strip()
    if not val_str: return 0.0
    if '.' in val_str and ',' in val_str:
        if val_str.rfind('.') > val_str.rfind(','): val_str = val_str.replace(',', '')
        else: val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except ValueError: return 0.0

def load_db():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE, dtype={'Barkod': str})
    return pd.DataFrame(columns=['Barkod', 'Ürün Adı', 'Maliyet (TL)', 'Kargo (TL)', 'Komisyon (%)'])

def find_default_col(options, keywords, exclude_keywords=None):
    if exclude_keywords is None: exclude_keywords = []
    for opt in options:
        opt_lower = str(opt).lower()
        if any(kw in opt_lower for kw in keywords) and not any(ex_kw in opt_lower for ex_kw in exclude_keywords):
            return options.index(opt)
    return 0

def load_api_settings():
    default_settings = {"ty_seller_id": "", "ty_api_key": "", "ty_api_secret": ""}
    if os.path.exists(API_FILE):
        try:
            with open(API_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception: pass
    return default_settings

def save_api_settings(settings):
    with open(API_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

# --- WEB SİTESİ ÜST NAVİGASYON (TOP HEADER BANNER) ---
st.markdown(f"""
    <div class="top-navbar">
        <div class="nav-brand">🚀 AVANTAJLI<span>ÜRÜN</span> <span style="font-size:11px; background:#0284c7; color:white; padding:3px 8px; border-radius:6px; margin-left:8px; vertical-align:middle;">PRO SAAS</span></div>
        <div style="display:flex; align-items:center; gap:15px;">
            <div class="nav-user">👤 Aktif Kullanıcı: <b>{st.session_state['current_user']}</b></div>
            <div style="font-size:13px; color:#94a3b8;">📅 {datetime.now().strftime('%d.%m.%Y')}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- YATAY WEB MENÜSÜ ---
nav_cols = st.columns(6)
pages = ["📊 Kontrol Paneli", "📦 Maliyet Yönetimi", "🧮 İdeal Fiyatlama", "🚀 Trendyol Yıldız", "💜 Hepsiburada Teklif", "⚙️ Ayarlar & API"]

for idx, p_name in enumerate(pages):
    with nav_cols[idx]:
        if st.button(p_name, use_container_width=True, key=f"btn_{idx}"):
            st.session_state["active_page"] = p_name

active_page = st.session_state["active_page"]
st.markdown("---")

# ==========================================
# SAYFA 0: KONTROL PANELİ (WEB DASHBOARD)
# ==========================================
if active_page == "📊 Kontrol Paneli":
    st.markdown('<div class="section-title">📊 Mağaza Performans ve Durum Özeti</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Sistemdeki aktif ürünlerinizin, maliyet yapılarınızın ve API bağlantılarınızın genel durumu.</div>', unsafe_allow_html=True)
    
    db = load_db()
    api = load_api_settings()
    api_connected = bool(api["ty_seller_id"] and api["ty_api_key"] and api["ty_api_secret"])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-badge"><div class="stat-label">Kayıtlı Ürün Sayısı</div><div class="stat-value">{len(db)} Adet</div></div>', unsafe_allow_html=True)
    with c2: 
        ort_maliyet = db["Maliyet (TL)"].mean() if len(db)>0 else 0.0
        st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Ortalama Maliyet</div><div class="stat-value">{ort_maliyet:,.2f} TL</div></div>', unsafe_allow_html=True)
    with c3:
        ort_kom = db["Komisyon (%)"].mean() if len(db)>0 else 0.0
        st.markdown(f'<div class="stat-badge" style="border-left-color:#f59e0b;"><div class="stat-label">Ort. Komisyon Oranı</div><div class="stat-value">% {ort_kom:.1f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-badge" style="border-left-color:{"#10b981" if api_connected else "#ef4444"};"><div class="stat-label">Trendyol API Durumu</div><div class="stat-value" style="color:{"#10b981" if api_connected else "#ef4444"};">{"🟢 Bağlı" if api_connected else "🔴 Eksik"}</div></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Hızlı Erişim İşlemleri")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        st.markdown('<div class="web-card"><h4>📦 Yeni Ürün Maliyeti Ekle</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Pazaryeri hesaplamalarında kullanılmak üzere yeni ürün barkodu ve alış fiyatı tanımlayın.</p></div>', unsafe_allow_html=True)
        if st.button("Maliyet Tablosuna Git ➔", use_container_width=True, key="go_db"): st.session_state["active_page"] = "📦 Maliyet Yönetimi"; st.rerun()
    with hc2:
        st.markdown('<div class="web-card"><h4>🧮 Kâr Marjı Simülasyonu Yap</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Hedeflediğiniz net kârı veya yüzdelik marjı elde etmek için ideal satış fiyatınızı bulun.</p></div>', unsafe_allow_html=True)
        if st.button("Fiyat Hesaplayıcıya Git ➔", use_container_width=True, key="go_calc"): st.session_state["active_page"] = "🧮 İdeal Fiyatlama"; st.rerun()
    with hc3:
        st.markdown('<div class="web-card"><h4>📈 Kampanya Excel\'i Yükle</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Trendyol veya Hepsiburada kampanya dosyalarınızı yükleyerek zarar etmeyecek fiyatları bulun.</p></div>', unsafe_allow_html=True)
        if st.button("Trendyol Analizine Git ➔", use_container_width=True, key="go_ty"): st.session_state["active_page"] = "🚀 Trendyol Yıldız"; st.rerun()

# ==========================================
# SAYFA 1: MALİYET VERİTABANI YÖNETİMİ
# ==========================================
elif active_page == "📦 Maliyet Yönetimi":
    st.markdown('<div class="section-title">📦 Ürün Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm kampanya ve satış analizlerinde ortak kullanılacak olan ürün maliyet, kargo ve komisyon listeniz.</div>', unsafe_allow_html=True)
    
    mevcut_db = load_db()
    if mevcut_db.empty:
        ornek_veri = pd.DataFrame({'Barkod': ['ORNEK_BARKOD_1'], 'Ürün Adı': ['Örnek Ürün'], 'Maliyet (TL)': [100.0], 'Kargo (TL)': [45.0], 'Komisyon (%)': [15.0]})
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        st.info("💡 Sistemde henüz ürün bulunmuyor. Örnek satırın üzerine tıklayarak kendi barkod ve maliyetlerinizi yazmaya başlayabilirsiniz.")
        
    edited_df = st.data_editor(
        tablayi_1den_baslat(mevcut_db), num_rows="dynamic", use_container_width=True,
        column_config={
            "Barkod": st.column_config.TextColumn("Barkod / SKU", required=True),
            "Ürün Adı": st.column_config.TextColumn("Ürün Adı"),
            "Maliyet (TL)": st.column_config.NumberColumn("Maliyet (TL)", min_value=0.0, format="%.2f"),
            "Kargo (TL)": st.column_config.NumberColumn("Kargo (TL)", min_value=0.0, format="%.2f"),
            "Komisyon (%)": st.column_config.NumberColumn("Komisyon (%)", min_value=0.0, max_value=100.0, format="%.2f"),
        }, height=450
    )
    if st.button("💾 Değişiklikleri Veritabanına Kaydet", use_container_width=True):
        df_save = edited_df.reset_index(drop=True)
        df_save['Barkod'] = df_save['Barkod'].astype(str).str.strip()
        df_save = df_save[df_save['Barkod'] != '']; df_save = df_save[df_save['Barkod'] != 'nan']
        df_save.to_csv(DB_FILE, index=False)
        st.success("✅ Ürün veritabanınız başarıyla güncellendi!")

# ==========================================
# SAYFA 2: İDEAL SATIŞ FİYATI HESAPLAMA
# ==========================================
elif active_page == "🧮 İdeal Fiyatlama":
    st.markdown('<div class="section-title">🧮 Akıllı Satış Fiyatı & Kâr Marjı Simülatörü</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Ürün alış fiyatı, kargo ve pazaryeri komisyon kesintilerini hesaba katarak zarar etmemeniz için gereken satış fiyatını hesaplayın.</div>', unsafe_allow_html=True)
    
    tab_tekli, tab_toplu = st.tabs(["⚡ Hızlı Tekli Simülasyon", "📦 Tüm Ürünlere Toplu Fiyat Atama"])
    with tab_tekli:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        col_inp1, col_inp2, col_inp3 = st.columns(3)
        with col_inp1:
            in_maliyet = st.number_input("📦 Ürün Maliyeti (TL)", min_value=0.0, value=150.0, step=5.0, format="%.2f")
            in_kargo = st.number_input("🚚 Kargo Gideri (TL)", min_value=0.0, value=45.0, step=5.0, format="%.2f")
        with col_inp2:
            in_komisyon = st.number_input("🤝 Pazaryeri Komisyonu (%)", min_value=0.0, max_value=95.0, value=18.0, step=1.0, format="%.2f")
            hesap_yontemi = st.radio("Hedefleme Yöntemi:", ["📊 Yüzdelik Kâr Marjı (%)", "💵 Net Kâr Tutarı (TL)"], horizontal=True)
        with col_inp3:
            if "Yüzdelik" in hesap_yontemi: in_hedef_val = st.number_input("🎯 Hedef Kâr Marjı (%)", min_value=1.0, max_value=80.0, value=25.0, step=1.0, format="%.2f")
            else: in_hedef_val = st.number_input("🎯 Hedef Net Kâr Tutarı (TL)", min_value=1.0, value=100.0, step=10.0, format="%.2f")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if "Yüzdelik" in hesap_yontemi:
            toplam_kesinti_orani = (in_komisyon + in_hedef_val) / 100.0
            if toplam_kesinti_orani >= 1.0: st.error("❌ Komisyon ve Kâr Marjı toplamı %100 veya üstü olamaz!"); ideal_fiyat = 0.0
            else: ideal_fiyat = (in_maliyet + in_kargo) / (1.0 - toplam_kesinti_orani)
        else:
            kom_orani = in_komisyon / 100.0
            if kom_orani >= 1.0: st.error("❌ Komisyon oranı %100 olamaz!"); ideal_fiyat = 0.0
            else: ideal_fiyat = (in_maliyet + in_kargo + in_hedef_val) / (1.0 - kom_orani)
                
        if ideal_fiyat > 0:
            komisyon_tl = ideal_fiyat * (in_komisyon / 100.0)
            net_kar = ideal_fiyat - (in_maliyet + in_kargo + komisyon_tl)
            kar_marji = (net_kar / ideal_fiyat * 100.0) if ideal_fiyat > 0 else 0.0
            
            st.markdown("#### 💡 Önerilen Satış Fiyatı Özeti")
            r1, r2, r3, r4 = st.columns(4)
            with r1: st.markdown(f'<div class="stat-badge" style="border-left-color:#8e44ad;"><div class="stat-label">İdeal Satış Fiyatı</div><div class="stat-value" style="color:#8e44ad;">{ideal_fiyat:,.2f} TL</div></div>', unsafe_allow_html=True)
            with r2: st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Net Kâr Tutarı</div><div class="stat-value" style="color:#10b981;">{net_kar:,.2f} TL</div></div>', unsafe_allow_html=True)
            with r3: st.markdown(f'<div class="stat-badge" style="border-left-color:#0284c7;"><div class="stat-label">Gerçek Kâr Marjı</div><div class="stat-value" style="color:#0284c7;">% {kar_marji:.2f}</div></div>', unsafe_allow_html=True)
            with r4: st.markdown(f'<div class="stat-badge" style="border-left-color:#ef4444;"><div class="stat-label">Komisyon Kesintisi</div><div class="stat-value" style="color:#ef4444;">{komisyon_tl:,.2f} TL</div></div>', unsafe_allow_html=True)

    with tab_toplu:
        st.write("Veritabanındaki tüm ürünleriniz için istediğiniz hedefi belirleyip tek tuşla yeni satış fiyatı listesi oluşturun.")
        db = load_db()
        if db.empty: st.warning("⚠️ Önce Maliyet Yönetimi sayfasından ürün eklemelisiniz.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1: toplu_yontem = st.selectbox("Toplu Hesaplama Hedefi:", ["📊 Sabit Kâr Marjı (%) Uygula", "💵 Sabit Net Kâr Tutarı (TL) Uygula"])
            with col_b2:
                if "Marjı" in toplu_yontem: toplu_hedef_val = st.number_input("Tüm Ürünler İçin Hedef Kâr Marjı (%)", min_value=1.0, max_value=80.0, value=30.0, step=1.0)
                else: toplu_hedef_val = st.number_input("Tüm Ürünler İçin Hedef Net Kâr (TL)", min_value=1.0, value=120.0, step=10.0)
            if st.button("🚀 Tüm Ürünler İçin İdeal Fiyatları Hesapla", use_container_width=True):
                df_res = db.copy()
                ideal_fiyatlar, komisyonlar, net_karlar, marjlar = [], [], [], []
                for idx, row in df_res.iterrows():
                    m_val, k_val, kom_val = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                    if "Marjı" in toplu_yontem:
                        t_rate = (kom_val + toplu_hedef_val) / 100.0
                        i_fiyat = 0.0 if t_rate >= 1.0 else (m_val + k_val) / (1.0 - t_rate)
                    else:
                        k_rate = kom_val / 100.0
                        i_fiyat = 0.0 if k_rate >= 1.0 else (m_val + k_val + toplu_hedef_val) / (1.0 - k_rate)
                    kom_tl = i_fiyat * (kom_val / 100.0) if i_fiyat > 0 else 0.0
                    n_kar = i_fiyat - (m_val + k_val + kom_tl) if i_fiyat > 0 else 0.0
                    k_marji = (n_kar / i_fiyat * 100.0) if i_fiyat > 0 else 0.0
                    ideal_fiyatlar.append(i_fiyat); komisyonlar.append(kom_tl); net_karlar.append(n_kar); marjlar.append(k_marji)
                df_res['Önerilen Satış Fiyatı (TL)'] = ideal_fiyatlar; df_res['Komisyon Tutarı (TL)'] = komisyonlar; df_res['Net Kâr (TL)'] = net_karlar; df_res['Kâr Marjı (%)'] = marjlar
                st.success("✅ Toplu fiyatlandırma başarıyla tamamlandı!")
                st.dataframe(tablayi_1den_baslat(df_res).style.format({'Maliyet (TL)': '{:,.2f} TL', 'Kargo (TL)': '{:,.2f} TL', 'Komisyon (%)': '% {:.2f}', 'Önerilen Satış Fiyatı (TL)': '{:,.2f} TL', 'Komisyon Tutarı (TL)': '{:,.2f} TL', 'Net Kâr (TL)': '{:,.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                out_exc = BytesIO()
                with pd.ExcelWriter(out_exc, engine='openpyxl') as wr:
                    tablayi_1den_baslat(df_res).reset_index().to_excel(wr, index=False, sheet_name='İdeal Fiyat Listesi')
                out_exc.seek(0)
                st.download_button("📥 İdeal Fiyat Listesini Excel Olarak İndir", data=out_exc, file_name=f"Toplu_Ideal_Fiyat_Listesi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ==========================================
# SAYFA 3: TRENDYOL KAMPANYA ANALİZİ
# ==========================================
elif active_page == "🚀 Trendyol Yıldız":
    st.markdown('<div class="section-title">🚀 Trendyol Yıldızlı Ürün Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Trendyol\'dan indirdiğiniz "Yıldızlı Ürün Etiketleri" dosyasını yükleyin; 3 Yıldız > 2 Yıldız > 1 Yıldız sırasıyla kârınızı test edelim.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty: st.error("❌ Lütfen önce Maliyet Yönetimi sayfasından ürün ekleyin."); st.stop()
        
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0)
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0)
    kampanya_file = st.file_uploader("Trendyol 'Yıldızlı Ürün Etiketleri' Dosyasını Yükleyin", type=['xlsx', 'csv'])
    
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        if orijinal_dosya_ismi.endswith('.csv'):
            try: df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except: kampanya_file.seek(0); df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else: df_kampanya = pd.read_excel(kampanya_file)
        cols = list(df_kampanya.columns)
        barkod_col = next((c for c in cols if 'BARKOD' in c.upper()), cols[1] if len(cols)>1 else cols[0])
        fiyat_1_yildiz = next((c for c in cols if '1 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_2_yildiz = next((c for c in cols if '2 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_3_yildiz = next((c for c in cols if '3 YILDIZ ÜST FİYAT' in c.upper()), None)
        yeni_fiyat_col = next((c for c in cols if 'YENİ TSF' in c.upper()), None)
        
        if st.button("⚡ Trendyol Fiyatlarını Hesapla", use_container_width=True):
            if not all([fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz, yeni_fiyat_col]): st.error("❌ Yıldızlı fiyat sütunları bulunamadı.")
            else:
                islem_df = df_kampanya.copy()
                islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                for col in [fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz]: merge_df[col + '_num'] = merge_df[col].apply(temizle_ve_sayiya_donustur)
                secilen_fiyatlar, secilen_yildizlar, hesaplanan_karlar, hesaplanan_marjlar = [], [], [], []
                test_siralamasi = [("3 Yıldız", fiyat_3_yildiz+'_num'), ("2 Yıldız", fiyat_2_yildiz+'_num'), ("1 Yıldız", fiyat_1_yildiz+'_num')]
                for idx, row in merge_df.iterrows():
                    if pd.isna(row['_db_barkod']):
                        secilen_fiyatlar.append(np.nan); secilen_yildizlar.append("Sistemde Yok"); hesaplanan_karlar.append(0); hesaplanan_marjlar.append(0); continue
                    maliyet, kargo, kom_orani = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                    uygun_fiyat, secili_yildiz, net_kar, kar_marji = np.nan, "Elenmiş", 0, 0
                    for yildiz_isim, f_col in test_siralamasi:
                        fiyat = row[f_col]
                        if fiyat <= 0: continue
                        komisyon_tl = fiyat * (kom_orani / 100)
                        n_kar = fiyat - (maliyet + kargo + komisyon_tl)
                        k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                        if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                            uygun_fiyat, secili_yildiz, net_kar, kar_marji = fiyat, yildiz_isim, n_kar, k_marji; break 
                    secilen_fiyatlar.append(uygun_fiyat); secilen_yildizlar.append(secili_yildiz); hesaplanan_karlar.append(net_kar); hesaplanan_marjlar.append(kar_marji)
                islem_df['Seçilen Yıldız'] = secilen_yildizlar; islem_df['Net Kâr (TL)'] = hesaplanan_karlar; islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                islem_df[yeni_fiyat_col] = [str(round(val, 2)).replace('.', ',') if (not pd.isna(val) and val != 0) else "" for val in secilen_fiyatlar]
                basarili_df = islem_df[islem_df['Seçilen Yıldız'].isin(["1 Yıldız", "2 Yıldız", "3 Yıldız"])].copy()
                st.success(f"✅ Analiz Tamamlandı: {len(basarili_df)} ürüne kârlı yıldız fiyatı atandı!")
                st.dataframe(tablayi_1den_baslat(basarili_df[[barkod_col, yeni_fiyat_col, 'Seçilen Yıldız', 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer: islem_df[cols].to_excel(writer, index=False, sheet_name='Sheet1')
                output.seek(0)
                st.download_button("📥 Trendyol İçin Hazır Excel'i İndir", data=output, file_name=orijinal_dosya_ismi.rsplit('.', 1)[0] + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ==========================================
# SAYFA 4: HEPSİBURADA KAMPANYA ANALİZİ
# ==========================================
elif active_page == "💜 Hepsiburada Teklif":
    st.markdown('<div class="section-title" style="color:#ff6700;">💜 Hepsiburada Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Hepsiburada\'dan indirdiğiniz "Listelerim" dosyasını yükleyin; sepet indirimi veya standart kampanya kârlılığını hesaplayalım.</div>', unsafe_allow_html=True)
    db = load_db()
    if db.empty: st.error("❌ Lütfen önce Maliyet Yönetimi sayfasından ürün ekleyin."); st.stop()
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="hb_m")
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="hb_t")
    kampanya_file = st.file_uploader("Hepsiburada 'Listelerim' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="hb_up")
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        df_kampanya = pd.read_excel(kampanya_file) if not kampanya_file.name.endswith('.csv') else pd.read_csv(kampanya_file, sep=None, engine='python')
        cols = list(df_kampanya.columns)
        col1, col2, col3, col4 = st.columns(4)
        with col1: barkod_col = st.selectbox("Barkod / SKU Sütunu", cols, index=find_default_col(cols, ["barkod", "barcode", "sku"]))
        with col2: eski_fiyat_col = st.selectbox("Mevcut Satış Fiyatı", cols, index=find_default_col(cols, ["satış", "satis", "psf"], exclude_keywords=["kampanya"]))
        with col3:
            is_normal_campaign = st.checkbox("🎯 Standart Kampanya (HB Max Fiyat Kuralı)")
            sepet_indirimi = 0.0 if is_normal_campaign else st.number_input("🛒 Kampanya İndirim Oranı (%)", min_value=1.0, max_value=99.0, value=15.0, step=1.0)
            max_fiyat_col = st.selectbox("Girebileceğiniz Max. Fiyat", cols, index=find_default_col(cols, ["max", "maksimum"]))
        with col4: kampanya_fiyat_col = st.selectbox("HB Paneline Yüklenecek Fiyat", cols, index=find_default_col(cols, ["uygulanacağı", "kampanya", "önerilen"]))
        if st.button("⚡ Hepsiburada Tekliflerini Analiz Et", use_container_width=True):
            islem_df = df_kampanya.copy()
            islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
            db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
            merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
            durum_list, hesaplanan_karlar, hesaplanan_marjlar, katilim_fiyati = [], [], [], []
            for idx, row in merge_df.iterrows():
                if pd.isna(row['_db_barkod']):
                    durum_list.append("Sistemde Yok"); hesaplanan_karlar.append(0); hesaplanan_marjlar.append(0); katilim_fiyati.append(np.nan); continue
                maliyet, kargo, kom_orani = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                fiyat = temizle_ve_sayiya_donustur(row[eski_fiyat_col])
                if sepet_indirimi > 0: fiyat = fiyat * (1 - (sepet_indirimi / 100))
                if fiyat <= 0: durum_list.append("Elenmiş"); hesaplanan_karlar.append(0); hesaplanan_marjlar.append(0); katilim_fiyati.append(np.nan); continue
                komisyon_tl = fiyat * (kom_orani / 100)
                n_kar = fiyat - (maliyet + kargo + komisyon_tl)
                k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                    durum_list.append("Kabul Edildi"); hesaplanan_karlar.append(n_kar); hesaplanan_marjlar.append(k_marji); katilim_fiyati.append(np.nan if is_normal_campaign else fiyat)
                else: durum_list.append("Elenmiş"); hesaplanan_karlar.append(n_kar); hesaplanan_marjlar.append(k_marji); katilim_fiyati.append(np.nan)
            islem_df['Kampanya Durumu'] = durum_list; islem_df['Net Kâr (TL)'] = hesaplanan_karlar; islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
            islem_df[kampanya_fiyat_col] = [str(round(val, 2)).replace('.', ',') if (not pd.isna(val) and val != 0) else "" for val in katilim_fiyati]
            basarili_df = islem_df[islem_df['Kampanya Durumu'] == "Kabul Edildi"].copy()
            st.success(f"✅ Hepsiburada Analizi Tamamlandı: {len(basarili_df)} ürün kârlı bulundu!")
            if len(basarili_df) > 0: st.dataframe(tablayi_1den_baslat(basarili_df[[barkod_col, eski_fiyat_col, 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if len(basarili_df) > 0: basarili_df[cols].to_excel(writer, index=False, sheet_name='Uygun Teklifler')
                islem_df[cols + ['Kampanya Durumu', 'Net Kâr (TL)', 'Kâr Marjı (%)']].to_excel(writer, index=False, sheet_name='Tüm Analiz Sonucu')
            output.seek(0)
            st.download_button("📥 Hepsiburada Hazır Excel'i İndir", data=output, file_name="HB_Kampanya_Sonucu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ==========================================
# SAYFA 5: AYARLAR & API BİLGİLERİ
# ==========================================
elif active_page == "⚙️ Ayarlar & API":
    st.markdown('<div class="section-title">⚙️ Sistem Ayarları & API Yönetimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Mağaza entegrasyon bilgilerinizi ve panel kullanıcı hesaplarınızı buradan güvenle yönetin.</div>', unsafe_allow_html=True)
    
    api = load_api_settings()
    st.markdown("### 🟠 Trendyol API Anahtarları")
    with st.form("api_form"):
        ty_id = st.text_input("Satıcı ID (Seller ID)", value=api["ty_seller_id"])
        ty_key = st.text_input("API Key", value=api["ty_api_key"], type="password")
        ty_sec = st.text_input("API Secret", value=api["ty_api_secret"], type="password")
        if st.form_submit_button("💾 API Bilgilerini Kaydet", use_container_width=True):
            save_api_settings({"ty_seller_id": ty_id.strip(), "ty_api_key": ty_key.strip(), "ty_api_secret": ty_sec.strip()})
            st.success("✅ Trendyol API bilgileri kaydedildi!")
            
    st.markdown("---")
    st.markdown("### 👥 Kullanıcı ve Şifre Yönetimi")
    t1, t2, t3 = st.tabs(["🔑 Şifre Değiştir", "➕ Yeni Kullanıcı Oluştur", "📋 Mevcut Kullanıcılar"])
    with t1:
        with st.form("pass_form"):
            eski_sifre = st.text_input("Mevcut Şifre", type="password")
            yeni_sifre = st.text_input("Yeni Şifre", type="password")
            yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar)", type="password")
            if st.form_submit_button("💾 Şifreyi Güncelle", use_container_width=True):
                curr_u = st.session_state.get('current_user', '')
                if auth_data["users"].get(curr_u) != eski_sifre.strip(): st.error("❌ Mevcut şifreniz yanlış!")
                elif len(yeni_sifre.strip()) < 3 or yeni_sifre.strip() != yeni_sifre_tekrar.strip(): st.error("❌ Yeni şifreler uyuşmuyor veya çok kısa!")
                else: auth_data["users"][curr_u] = yeni_sifre.strip(); save_auth(auth_data); st.success("✅ Şifreniz güncellendi!")
    with t2:
        with st.form("new_user_form"):
            yeni_kadi = st.text_input("Yeni Kullanıcı Adı")
            yeni_kuser_sifre = st.text_input("Şifre", type="password")
            yeni_kuser_sifre_tekrar = st.text_input("Şifre (Tekrar)", type="password")
            if st.form_submit_button("➕ Kullanıcıyı Oluştur", use_container_width=True):
                k_adi_temiz = yeni_kadi.strip()
                if not k_adi_temiz or k_adi_temiz in auth_data["users"]: st.error("❌ Kullanıcı adı boş veya zaten mevcut!")
                elif len(yeni_kuser_sifre.strip()) < 3 or yeni_kuser_sifre.strip() != yeni_kuser_sifre_tekrar.strip(): st.error("❌ Şifreler uyuşmuyor veya çok kısa!")
                else: auth_data["users"][k_adi_temiz] = yeni_kuser_sifre.strip(); save_auth(auth_data); st.success(f"✅ `{k_adi_temiz}` kullanıcısı oluşturuldu!")
    with t3:
        for idx, u in enumerate(list(auth_data["users"].keys()), 1):
            st.markdown(f"**{idx}.** 👤 `{u}` {'*(Aktif Oturum)*' if u == st.session_state.get('current_user') else ''}")
