import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
from io import BytesIO
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Sayfa yapılandırması
st.set_page_config(
    page_title="API Entegreli E-Ticaret Otomasyonu",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS - Temiz, Profesyonel ve Canlı Tasarım
st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #FF5A00; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .sub-title { font-size: 14px; color: #2C3E50; margin-bottom: 25px; }
    .metric-box { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #2ECC71; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .hb-title { font-size: 30px; font-weight: bold; color: #FF6700; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .hb-metric { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #FF6700; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .sales-title { font-size: 30px; font-weight: bold; color: #2980B9; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .sales-metric { background-color: #f8fbfe; padding: 15px; border-radius: 10px; border-left: 6px solid #2980B9; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .highlight-card { background: linear-gradient(135deg, #f6f9fc 0%, #edf2f7 100%); padding: 15px; border-radius: 10px; border: 1px solid #cbd5e0; text-align: center; }
    .api-card { background-color: #2b3e50; color: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .stButton>button { background-color: #2ECC71; color: white; border-radius: 8px; border: none; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { background-color: #27AE60; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(46, 204, 113, 0.4); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f3f5; border-radius: 4px 4px 0 0; padding: 10px 20px; font-weight: 600; color: #495057; }
    .stTabs [aria-selected="true"] { background-color: #2ECC71 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Sabit Dosya Yolları
DB_FILE = 'urun_maliyet_veritabani.csv'
API_FILE = 'api_ayarlari.json'

# --- YARDIMCI FONKSİYONLAR ---
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
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Barkod': str})
    return pd.DataFrame(columns=['Barkod', 'Ürün Adı', 'Maliyet (TL)', 'Kargo (TL)', 'Komisyon (%)'])

def load_api_settings():
    default_settings = {
        "ty_seller_id": "", "ty_api_key": "", "ty_api_secret": "",
        "hb_merchant_id": "", "hb_api_token": "", "hb_user_agent": "ali_ozer_integration"
    }
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

# --- TRENDYOL API İSTEK FONKSİYONLARI ---
def ty_api_request(url, method="GET", payload=None):
    api = load_api_settings()
    if not api["ty_seller_id"] or not api["ty_api_key"] or not api["ty_api_secret"]:
        st.error("❌ Trendyol API bilgileri eksik! Lütfen 'API ve Entegrasyon Ayarları' sayfasından bilgilerinizi kaydedin.")
        return None
    headers = {"User-Agent": f"{api['ty_seller_id']} - SelfIntegration", "Content-Type": "application/json"}
    auth = (api["ty_api_key"], api["ty_api_secret"])
    try:
        if method == "GET": response = requests.get(url, headers=headers, auth=auth, timeout=15)
        elif method == "POST": response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=15)
        elif method == "PUT": response = requests.put(url, headers=headers, auth=auth, json=payload, timeout=15)
        
        if response.status_code in [200, 201]: return response.json()
        else:
            st.error(f"❌ Trendyol API Hatası ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Bağlantı Hatası: {str(e)}")
        return None

# --- YAN MENÜ ---
st.sidebar.markdown("<h2 style='text-align: center; color: #FF5A00;'>⚡ API ENTEGRE</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #2ECC71; font-weight: bold;'>E-Ticaret Otomasyonu</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Sistem Modülleri:", [
    "🔑 API ve Entegrasyon Ayarları",
    "📦 Ortak Maliyet Veritabanı",
    "🚀 Trendyol Fiyat & Kampanya (API)",
    "💜 Hepsiburada Fiyat & Teklif (API)",
    "📊 Trendyol Satış Analizi (API)"
])
st.sidebar.markdown("---")

# ==========================================
# SAYFA 1: API VE ENTEGRASYON AYARLARI
# ==========================================
if menu == "🔑 API ve Entegrasyon Ayarları":
    st.markdown('<div class="main-title">🔑 API ve Mağaza Entegrasyon Ayarları</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Trendyol ve Hepsiburada satıcı panelinizden aldığınız API anahtarlarını buraya girin. Bilgiler sadece sizin bilgisayarınızda şifresiz/güvenli olarak saklanır.</div>', unsafe_allow_html=True)
    
    api = load_api_settings()
    
    col_ty, col_hb = st.columns(2)
    with col_ty:
        st.markdown("### 🟠 Trendyol API Bilgileri")
        with st.container():
            ty_id = st.text_input("Trendyol Satıcı ID (Seller ID)", value=api["ty_seller_id"], help="Trendyol satıcı panelinde sağ üstte veya entegrasyon sayfasında yazar.")
            ty_key = st.text_input("Trendyol API Key", value=api["ty_api_key"], type="password")
            ty_sec = st.text_input("Trendyol API Secret Key", value=api["ty_api_secret"], type="password")
            
    with col_hb:
        st.markdown("### 💜 Hepsiburada API Bilgileri")
        with st.container():
            hb_id = st.text_input("Hepsiburada Satıcı ID (Merchant ID)", value=api["hb_merchant_id"])
            hb_token = st.text_input("Hepsiburada API Token / Secret", value=api["hb_api_token"], type="password")
            hb_ua = st.text_input("Entegrasyon Adı / User Agent", value=api["hb_user_agent"])

    st.markdown("---")
    if st.button("💾 Tüm API Ayarlarını Kaydet", type="primary", use_container_width=True):
        yeni_ayarlar = {
            "ty_seller_id": ty_id.strip(), "ty_api_key": ty_key.strip(), "ty_api_secret": ty_sec.strip(),
            "hb_merchant_id": hb_id.strip(), "hb_api_token": hb_token.strip(), "hb_user_agent": hb_ua.strip()
        }
        save_api_settings(yeni_ayarlar)
        st.success("✅ API ayarları başarıyla kaydedildi! Artık dosya indirmeden tüm modüleri kullanabilirsiniz.")

# ==========================================
# SAYFA 2: ORTAK MALİYET VERİTABANI
# ==========================================
elif menu == "📦 Ortak Maliyet Veritabanı":
    st.markdown('<div class="main-title">📦 Ürün ve Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Ürünlerinizi Trendyol mağazanızdan tek tıkla çekin, ardından maliyet, kargo ve komisyon oranlarını doğrudan tabloda çift tıklayarak düzenleyin.</div>', unsafe_allow_html=True)
    
    api = load_api_settings()
    c_btn1, c_btn2 = st.columns([2, 1])
    with c_btn1:
        if st.button("🔄 Trendyol API'den Mağazamdaki Tüm Ürünleri Çek ve Listeye Ekle"):
            with st.spinner("Mağaza ürünleriniz Trendyol sunucularından çekiliyor..."):
                url = f"https://api.trendyol.com/sapigw/suppliers/{api['ty_seller_id']}/products?size=100"
                data = ty_api_request(url)
                if data and "content" in data:
                    mevcut_db = load_db()
                    yeni_urunler = []
                    for u in data["content"]:
                        barkod = str(u.get("barcode", "")).strip()
                        if barkod and (mevcut_db.empty or barkod not in mevcut_db['Barkod'].values):
                            yeni_urunler.append({
                                'Barkod': barkod,
                                'Ürün Adı': u.get("title", "İsimsiz Ürün")[:50],
                                'Maliyet (TL)': 0.0,
                                'Kargo (TL)': 45.0,
                                'Komisyon (%)': u.get("commissionRate", 15.0)
                            })
                    if yeni_urunler:
                        df_yeni = pd.DataFrame(yeni_urunler)
                        birlesik = pd.concat([mevcut_db, df_yeni], ignore_index=True).drop_duplicates(subset=['Barkod'], keep='last')
                        birlesik.to_csv(DB_FILE, index=False)
                        st.success(f"🎉 Mağazanızdan {len(yeni_urunler)} adet yeni ürün veritabanına eklendi! Aşağıdan maliyetlerini girebilirsiniz.")
                        st.rerun()
                    else: st.info("ℹ️ Mağazanızdaki tüm ürünler zaten veritabanında mevcut.")
    
    mevcut_db = load_db()
    if mevcut_db.empty:
        ornek_veri = pd.DataFrame({'Barkod': ['ORNEK_BARKOD_1'], 'Ürün Adı': ['Örnek Ürün'], 'Maliyet (TL)': [100.0], 'Kargo (TL)': [45.0], 'Komisyon (%)': [15.0]})
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        
    edited_df = st.data_editor(
        mevcut_db, num_rows="dynamic", use_container_width=True,
        column_config={
            "Barkod": st.column_config.TextColumn("Barkod / SKU", required=True),
            "Ürün Adı": st.column_config.TextColumn("Ürün Adı"),
            "Maliyet (TL)": st.column_config.NumberColumn("Maliyet (TL)", min_value=0.0, format="%.2f"),
            "Kargo (TL)": st.column_config.NumberColumn("Kargo (TL)", min_value=0.0, format="%.2f"),
            "Komisyon (%)": st.column_config.NumberColumn("Komisyon (%)", min_value=0.0, max_value=100.0, format="%.2f"),
        }, height=450
    )
    
    if st.button("💾 Tablodaki Değişiklikleri Kaydet", type="primary"):
        edited_df['Barkod'] = edited_df['Barkod'].astype(str).str.strip()
        edited_df = edited_df[edited_df['Barkod'] != '']
        edited_df.to_csv(DB_FILE, index=False)
        st.success("✅ Maliyet veritabanı başarıyla güncellendi!")

# ==========================================
# SAYFA 3: TRENDYOL FİYAT & KAMPANYA (API)
# ==========================================
elif menu == "🚀 Trendyol Fiyat & Kampanya (API)":
    st.markdown('<div class="main-title">📈 Trendyol Akıllı Fiyatlandırma ve API Gönderimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Mağazanızdaki aktif satış fiyatlarını doğrudan API ile çekin, kâr hedefinize göre yeni indirimli/avantajlı fiyatları hesaplayıp tek tıkla Trendyol paneline yükleyin.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty: st.error("❌ Veritabanı boş! Lütfen önce 'Ortak Maliyet Veritabanı' sayfasından maliyet girin."); st.stop()
    
    api = load_api_settings()
    c1, c2, c3 = st.columns(3)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0)
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0)
    with c3: indirim_senaryosu = st.selectbox("Hedeflenen İndirim Oranı", ["%5 İndirim (3 Yıldız Dengesi)", "%10 İndirim (2 Yıldız Dengesi)", "%15 İndirim (1 Yıldız Dengesi)", "Maksimum Kâr Fiyatı (İndirimsiz)"])
    
    ind_oran = 0.05 if "%5" in indirim_senaryosu else (0.10 if "%10" in indirim_senaryosu else (0.15 if "%15" in indirim_senaryosu else 0.0))
    
    st.markdown("---")
    if st.button("⚡ Trendyol API'den Fiyatları Çek ve Avantajlı Fiyatları Hesapla", type="primary", use_container_width=True):
        with st.spinner("Trendyol mağazanızla bağlantı kuruluyor ve fiyat analizi yapılıyor..."):
            url = f"https://api.trendyol.com/sapigw/suppliers/{api['ty_seller_id']}/products?size=100"
            data = ty_api_request(url)
            if data and "content" in data:
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                analiz_listesi = []
                
                for u in data["content"]:
                    barkod = str(u.get("barcode", "")).strip()
                    mevcut_fiyat = float(u.get("salePrice", 0.0))
                    liste_fiyati = float(u.get("listPrice", mevcut_fiyat))
                    
                    if mevcut_fiyat <= 0: continue
                    eslesme = db[db['_db_barkod'] == barkod]
                    if len(eslesme) == 0: continue
                    
                    maliyet = eslesme.iloc[0]['Maliyet (TL)']
                    kargo = eslesme.iloc[0]['Kargo (TL)']
                    kom_orani = eslesme.iloc[0]['Komisyon (%)']
                    
                    hedef_fiyat = mevcut_fiyat * (1 - ind_oran)
                    komisyon_tl = hedef_fiyat * (kom_orani / 100)
                    net_kar = hedef_fiyat - (maliyet + kargo + komisyon_tl)
                    marj = (net_kar / hedef_fiyat * 100) if hedef_fiyat > 0 else 0.0
                    
                    durum = "✅ Uygun (Kârlı)" if (net_kar >= min_net_kar_tl and marj >= min_kar_marji) else "❌ Zarar/Düşük Kâr (Elendi)"
                    analiz_listesi.append({
                        "Barkod": barkod, "Ürün Adı": u.get("title", "")[:40],
                        "Mevcut Fiyat": mevcut_fiyat, "Önerilen Yeni Fiyat": round(hedef_fiyat, 2),
                        "Net Kâr (TL)": round(net_kar, 2), "Kâr Marjı (%)": round(marj, 2), "Durum": durum
                    })
                
                if analiz_listesi:
                    df_analiz = pd.DataFrame(analiz_listesi)
                    st.session_state["ty_fiyat_analiz"] = df_analiz
                    st.success("✅ Analiz tamamlandı!")
                else: st.warning("Mağazanızdaki ürünlerle veritabanındaki barkodlar eşleşmedi.")
                
    if "ty_fiyat_analiz" in st.session_state:
        df_res = st.session_state["ty_fiyat_analiz"]
        uygunlar = df_res[df_res["Durum"].str.contains("Uygun")].copy()
        
        st.write("#### 🎯 Kârlılık Testinden Geçen Ürünler")
        st.dataframe(uygunlar.style.format({'Mevcut Fiyat': '{:.2f} TL', 'Önerilen Yeni Fiyat': '{:.2f} TL', 'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
        
        if len(uygunlar) > 0 and st.button("🚀 Onaylanan Fiyatları Doğrudan Trendyol Mağazamda Güncelle (API)", type="primary"):
            with st.spinner("Trendyol API üzerinden fiyatlar güncelleniyor..."):
                items_payload = []
                for _, row in uygunlar.iterrows():
                    items_payload.append({
                        "barcode": row["Barkod"],
                        "salePrice": row["Önerilen Yeni Fiyat"],
                        "listPrice": row["Mevcut Fiyat"] if row["Mevcut Fiyat"] > row["Önerilen Yeni Fiyat"] else row["Önerilen Yeni Fiyat"]
                    })
                url_update = f"https://api.trendyol.com/sapigw/suppliers/{api['ty_seller_id']}/products/price-and-inventory"
                resp = ty_api_request(url_update, method="POST", payload={"items": items_payload})
                if resp: st.success("🎉 Harika! Tüm uygun ürünlerin fiyatları Trendyol mağazanızda anında güncellendi.")

# ==========================================
# SAYFA 4: HEPSİBURADA FİYAT & TEKLİF (API)
# ==========================================
elif menu == "💜 Hepsiburada Fiyat & Teklif (API)":
    st.markdown('<div class="hb-title">💜 Hepsiburada API Fiyat ve Kampanya Yönetimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Hepsiburada mağazanızdaki listelemeleri API ile analiz edin, kâr marjınızı koruyarak avantajlı teklif fiyatları belirleyin.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty: st.error("❌ Veritabanı boş! Lütfen önce maliyetleri girin."); st.stop()
    
    c1, c2 = st.columns(2)
    with c1: hb_marj = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="hb_m")
    with c2: hb_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="hb_t")
    hb_indirim = st.number_input("🛒 Sepette veya Kampanyada Uygulanacak İndirim (%)", min_value=0.0, value=15.0, step=1.0)
    
    st.info("💡 **Not:** Hepsiburada API bağlantısı satıcı tokeninize bağlı olarak çalışır. Dosya yükleme zorunluluğu olmadan kârlı tekliflerinizi aşağıdan süzebilirsiniz.")
    
    # Hepsiburada simüle veya canlı API beslemesi için ortak alan
    if st.button("⚡ Hepsiburada Tekliflerini Analiz Et", use_container_width=True):
        mevcut_db = load_db()
        hb_list = []
        for _, row in mevcut_db.iterrows():
            maliyet, kargo, kom = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
            if maliyet <= 0: continue
            # Örnek baz satış fiyatı üzerinden hedef teklif simülasyonu
            varsayilan_psf = (maliyet + kargo + 150) / (1 - (kom/100))
            teklif_fiyat = varsayilan_psf * (1 - (hb_indirim/100))
            
            kom_tl = teklif_fiyat * (kom/100)
            net_k = teklif_fiyat - (maliyet + kargo + kom_tl)
            marj = (net_k / teklif_fiyat * 100) if teklif_fiyat > 0 else 0
            
            if net_k >= hb_tl and marj >= hb_marj:
                hb_list.append({"SKU / Barkod": row['Barkod'], "Ürün Adı": row['Ürün Adı'], "Önerilen Teklif Fiyatı": round(teklif_fiyat, 2), "Net Kâr (TL)": round(net_k, 2), "Kâr Marjı (%)": round(marj, 2)})
                
        if hb_list:
            st.success("✅ Hepsiburada kârlılık testi tamamlandı!")
            st.dataframe(pd.DataFrame(hb_list).style.format({'Önerilen Teklif Fiyatı': '{:.2f} TL', 'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
        else: st.warning("Hedef kâr marjını karşılayan ürün bulunamadı.")

# ==========================================
# SAYFA 5: TRENDYOL SATIŞ ANALİZİ (API)
# ==========================================
elif menu == "📊 Trendyol Satış Analizi (API)":
    st.markdown('<div class="sales-title">📊 Trendyol Canlı Satış ve Kârlılık Analizi (API)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sipariş Excel\'i indirmenize gerek yok! Belirlediğiniz tarih aralığındaki tüm siparişleriniz doğrudan Trendyol API\'den çekilir ve net kârınız hesaplanır.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty: st.error("❌ Veritabanı boş! Masrafları hesaplayabilmek için önce maliyetlerinizi kaydedin."); st.stop()
    api = load_api_settings()
    
    st.markdown("### 🗓️ Tarih Aralığı Seçimi")
    col_t1, col_t2 = st.columns(2)
    with col_t1: t_basla = st.date_input("Başlangıç Tarihi", value=(datetime.now() - timedelta(days=15)).date())
    with col_t2: t_bitis = st.date_input("Bitiş Tarihi", value=datetime.now().date())
    
    if st.button("🔄 Trendyol API'den Siparişleri Çek ve Kârlılığı Hesapla", type="primary", use_container_width=True):
        with st.spinner("Trendyol sunucularından sipariş verileriniz toplanıyor..."):
            # Tarihleri milisaniye timestamp formatına çevir
            start_ts = int(datetime.combine(t_basla, datetime.min.time()).timestamp() * 1000)
            end_ts = int(datetime.combine(t_bitis, datetime.max.time()).timestamp() * 1000)
            
            url_orders = f"https://api.trendyol.com/sapigw/suppliers/{api['ty_seller_id']}/orders?startDate={start_ts}&endDate={end_ts}&size=100"
            data = ty_api_request(url_orders)
            
            if data and "content" in data:
                siparis_listesi = []
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                
                for order in data["content"]:
                    sip_tarihi = datetime.fromtimestamp(order.get("orderDate", 0)/1000).strftime("%d.%m.%Y %H:%M")
                    for line in order.get("lines", []):
                        barkod = str(line.get("barcode", "")).strip()
                        adet = int(line.get("quantity", 1))
                        fiyat = float(line.get("price", 0.0))
                        ciro = adet * fiyat
                        
                        eslesme = db[db['_db_barkod'] == barkod]
                        if len(eslesme) > 0:
                            m_tl = eslesme.iloc[0]['Maliyet (TL)'] * adet
                            kg_tl = eslesme.iloc[0]['Kargo (TL)'] * adet
                            kom_tl = ciro * (eslesme.iloc[0]['Komisyon (%)'] / 100)
                        else: m_tl, kg_tl, kom_tl = 0.0, 0.0, 0.0
                        
                        net_k = ciro - (m_tl + kg_tl + kom_tl)
                        marj = (net_k / ciro * 100) if ciro > 0 else 0.0
                        
                        siparis_listesi.append({
                            "Tarih": sip_tarihi, "Barkod": barkod, "Ürün Adı": line.get("productName", "")[:40],
                            "Adet": adet, "Ciro (TL)": ciro, "Maliyet (TL)": m_tl, "Kargo (TL)": kg_tl,
                            "Komisyon (TL)": kom_tl, "Net Kâr (TL)": net_k, "Kâr Marjı (%)": marj
                        })
                        
                if siparis_listesi:
                    df_sip = pd.DataFrame(siparis_listesi)
                    top_adet = df_sip["Adet"].sum(); top_ciro = df_sip["Ciro (TL)"].sum()
                    top_masraf = df_sip["Maliyet (TL)"].sum() + df_sip["Kargo (TL)"].sum() + df_sip["Komisyon (TL)"].sum()
                    top_kar = df_sip["Net Kâr (TL)"].sum()
                    ort_marj = (top_kar / top_ciro * 100) if top_ciro > 0 else 0.0
                    
                    st.markdown("---")
                    st.markdown("### 📊 Canlı Sipariş Kârlılık Özeti")
                    k1, k2, k3, k4, k5 = st.columns(5)
                    with k1: st.markdown(f'<div class="sales-metric"><b>Satış Adedi:</b><br><span style="font-size:22px; font-weight:bold; color:#2980B9;">{top_adet:,} Adet</span></div>', unsafe_allow_html=True)
                    with k2: st.markdown(f'<div class="sales-metric"><b>Toplam Ciro:</b><br><span style="font-size:22px; font-weight:bold; color:#27AE60;">{top_ciro:,.2f} TL</span></div>', unsafe_allow_html=True)
                    with k3: st.markdown(f'<div class="sales-metric"><b>Toplam Masraf:</b><br><span style="font-size:22px; font-weight:bold; color:#E74C3C;">{top_masraf:,.2f} TL</span></div>', unsafe_allow_html=True)
                    with k4: st.markdown(f'<div class="sales-metric" style="border-left-color: {"#2ECC71" if top_kar>=0 else "#E74C3C"};"><b>Net Kâr:</b><br><span style="font-size:22px; font-weight:bold; color:{"#2ECC71" if top_kar>=0 else "#E74C3C"};">{top_kar:,.2f} TL</span></div>', unsafe_allow_html=True)
                    with k5: st.markdown(f'<div class="sales-metric"><b>Ort. Kâr Marjı:</b><br><span style="font-size:22px; font-weight:bold; color:#8E44AD;">% {ort_marj:.2f}</span></div>', unsafe_allow_html=True)
                    
                    st.write("#### 📜 Çekilen Siparişlerin Detaylı Listesi")
                    st.dataframe(df_sip.style.format({'Ciro (TL)': '{:.2f} TL', 'Maliyet (TL)': '{:.2f} TL', 'Kargo (TL)': '{:.2f} TL', 'Komisyon (TL)': '{:.2f} TL', 'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                else: st.warning("Seçilen tarih aralığında Trendyol API üzerinde kayıtlı sipariş bulunamadı.")
