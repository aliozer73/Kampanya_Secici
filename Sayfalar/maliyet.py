import streamlit as st
import pandas as pd
import numpy as np
import requests
import utils

def fetch_trendyol_products_api():
    api = utils.load_api_settings()
    seller_id = api.get("ty_seller_id", "").strip()
    api_key = api.get("ty_api_key", "").strip()
    api_secret = api.get("ty_api_secret", "").strip()
    
    if not seller_id or not api_key or not api_secret:
        return None, "❌ Trendyol API bilgileri eksik! Lütfen '⚙️ Ayarlar & API' sayfasından Satıcı ID, API Key ve Secret bilgilerinizi kaydedin."
        
    url = f"https://api.trendyol.com/sapigw/suppliers/{seller_id}/products?approved=True&size=200"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, auth=(api_key, api_secret), timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = data.get("content", [])
            return items, None
        elif response.status_code == 403:
            return None, "❌ Trendyol API Güvenlik Duvarı (403): Bulut sunucu IP'si engellendi. Lokal çalıştırın veya Excel yüklemeyi kullanın."
        else:
            return None, f"❌ Trendyol API Hatası ({response.status_code}): {response.text}"
    except Exception as e:
        return None, f"❌ Bağlantı Hatası: {str(e)}"

def render():
    st.markdown('<div class="section-title">📦 Ürün Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm kampanya ve satış analizlerinde ortak kullanılacak olan ürün maliyet, kargo ve komisyon listeniz.</div>', unsafe_allow_html=True)
    
    mevcut_db = utils.load_db()
    
    # Eksik sütun kontrolü (Yeni eklenen Diğer Masraflar ve Satış Fiyatı için)
    if 'Satış Fiyatı (TL)' not in mevcut_db.columns: mevcut_db['Satış Fiyatı (TL)'] = 0.0
    if 'Diğer Masraflar (%)' not in mevcut_db.columns: mevcut_db['Diğer Masraflar (%)'] = 1.0
    
    # Üst Bölüm: 3 Sekmeli Ekleme ve İndirme Alanı
    tab_tekli, tab_toplu, tab_api = st.tabs(["➕ Tekil Ürün Ekle", "📂 Excel / CSV ile Toplu Yükle", "🌐 Satış Platformlarından İndir (API)"])
    
    # -----------------------------------------------------------------
    # SEKME 1: TEKİL ÜRÜN EKLE
    # -----------------------------------------------------------------
    with tab_tekli:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        with st.form("tekil_ekle_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 2, 1.2])
            with c1:
                yeni_barkod = st.text_input("Barkod / SKU *", placeholder="Örn: TR-890123")
                yeni_kargo = st.number_input("Kargo Gideri (TL)", min_value=0.0, value=100.0, step=5.0, format="%.2f")
                yeni_diger = st.number_input("Diğer Masraflar (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.5, format="%.2f")
            with c2:
                yeni_ad = st.text_input("Ürün Adı", placeholder="Örn: Altın Kaplama Kolye")
                yeni_satis = st.number_input("Satış Fiyatı (TL)", min_value=0.0, value=300.0, step=10.0, format="%.2f")
                yeni_komisyon = st.number_input("Pazaryeri Komisyonu (%)", min_value=0.0, max_value=100.0, value=22.5, step=0.5, format="%.2f")
            with c3:
                # Satış fiyatının 1/3'ünü varsayılan maliyet öner
                yeni_maliyet = st.number_input("Maliyet (TL) *", min_value=0.0, value=100.0, step=5.0, format="%.2f", help="Varsayılan olarak 100 TL gelmektedir.")
                st.write("") # Boşluk
                submit_tekil = st.form_submit_button("➕ Listeye Ekle", use_container_width=True)
                
            if submit_tekil:
                barkod_temiz = str(yeni_barkod).strip()
                if not barkod_temiz or barkod_temiz == 'nan':
                    st.error("❌ Barkod alanı zorunludur!")
                else:
                    yeni_satir = pd.DataFrame([{
                        'Barkod': barkod_temiz,
                        'Ürün Adı': str(yeni_ad).strip(),
                        'Satış Fiyatı (TL)': float(yeni_satis),
                        'Maliyet (TL)': float(yeni_maliyet),
                        'Kargo (TL)': float(yeni_kargo),
                        'Komisyon (%)': float(yeni_komisyon),
                        'Diğer Masraflar (%)': float(yeni_diger)
                    }])
                    if not mevcut_db.empty and barkod_temiz in mevcut_db['Barkod'].astype(str).values:
                        idx = mevcut_db[mevcut_db['Barkod'].astype(str) == barkod_temiz].index[0]
                        for col in yeni_satir.columns: mevcut_db.loc[idx, col] = yeni_satir.iloc[0][col]
                        st.success(f"🔄 `{barkod_temiz}` barkodlu ürün güncellendi!")
                    else:
                        mevcut_db = pd.concat([yeni_satir, mevcut_db], ignore_index=True)
                        st.success(f"✅ `{barkod_temiz}` listeye eklendi!")
                    mevcut_db.to_csv(utils.DB_FILE, index=False)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # SEKME 2: EXCEL / CSV İLE TOPLU YÜKLE
    # -----------------------------------------------------------------
    with tab_toplu:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        st.write("Daha önce hazırladığınız ürün listesini Excel veya CSV formatında yükleyerek veritabanınıza topluca aktarabilirsiniz.")
        yuklenen_dosya = st.file_uploader("Excel veya CSV Dosyası Seçin", type=['xlsx', 'xls', 'csv'], key="maliyet_uploader")
        
        if yuklenen_dosya:
            try:
                if yuklenen_dosya.name.endswith('.csv'):
                    try: df_yuklenen = pd.read_csv(yuklenen_dosya, sep=None, engine='python', dtype=str)
                    except: yuklenen_dosya.seek(0); df_yuklenen = pd.read_csv(yuklenen_dosya, delimiter=';', dtype=str)
                else:
                    df_yuklenen = pd.read_excel(yuklenen_dosya, dtype=str)
                
                cols = list(df_yuklenen.columns)
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: b_col = st.selectbox("Barkod Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku"]))
                with sc2: a_col = st.selectbox("Ürün Adı Sütunu", cols, index=utils.find_default_col(cols, ["ad", "name", "ürün"]))
                with sc3: s_col = st.selectbox("Satış Fiyatı Sütunu", cols, index=utils.find_default_col(cols, ["satış", "satis", "tsf", "fiyat", "price"]))
                with sc4: m_col = st.selectbox("Maliyet Sütunu (Yoksa 1/3 Hesaplanır)", ["-- Otomatik (Satış / 3) --"] + cols, index=0)
                
                islemi_sec = st.radio("Aktarım Yöntemi:", [
                    "🔄 Mevcut listeyle birleştir (Aynı barkodları güncelle, yenileri ekle)",
                    "⚠️ Mevcut listeyi sil ve tamamen bu dosyayı yükle"
                ], horizontal=True)
                
                if st.button("🚀 Dosyadaki Ürünleri Veritabanına Aktar", type="primary", use_container_width=True):
                    yeni_liste = []
                    for _, row in df_yuklenen.iterrows():
                        brk = str(row[b_col]).strip() if pd.notna(row[b_col]) else ""
                        if not brk or brk == 'nan': continue
                        
                        satis_val = utils.temizle_ve_sayiya_donustur(row[s_col])
                        if m_col == "-- Otomatik (Satış / 3) --":
                            maliyet_val = round(satis_val / 3.0, 2)
                        else:
                            maliyet_val = utils.temizle_ve_sayiya_donustur(row[m_col])
                            
                        yeni_liste.append({
                            'Barkod': brk,
                            'Ürün Adı': str(row[a_col]).strip() if pd.notna(row[a_col]) else "",
                            'Satış Fiyatı (TL)': satis_val,
                            'Maliyet (TL)': maliyet_val,
                            'Kargo (TL)': 100.0,
                            'Komisyon (%)': 22.5,
                            'Diğer Masraflar (%)': 1.0
                        })
                    
                    df_yeni_aktarim = pd.DataFrame(yeni_liste)
                    
                    if "sil ve tamamen" in islemi_sec:
                        son_db = df_yeni_aktarim
                    else:
                        if not mevcut_db.empty:
                            eski_yoksa = mevcut_db[~mevcut_db['Barkod'].astype(str).isin(df_yeni_aktarim['Barkod'])].copy()
                            son_db = pd.concat([df_yeni_aktarim, eski_yoksa], ignore_index=True)
                        else:
                            son_db = df_yeni_aktarim
                            
                    son_db.to_csv(utils.DB_FILE, index=False)
                    st.success(f"✅ Başarıyla {len(df_yeni_aktarim)} ürün işlendi ve veritabanına kaydedildi!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Dosya okuma hatası: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # SEKME 3: SATIŞ PLATFORMLARINDAN İNDİR (API & SİMÜLASYON)
    # -----------------------------------------------------------------
    with tab_api:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        st.markdown("#### 🛒 Trendyol / Satış Platformu Entegrasyonu")
        st.write("Mağazanızdaki aktif ürünleri API üzerinden veya simülasyon moduyla anında çekerek maliyet tablonuza aktarabilirsiniz.")
        
        # Ayarlar özeti ve bilgi
        st.info("💡 **Otomatik Atanan Varsayılan Değerler:** Ürün Maliyeti = **Satış Fiyatının 1/3'ü**, Komisyon Oranı = **%22.5**, Kargo Ücreti = **100 TL**, Diğer Masraflar = **%1.0**")
        
        col_api1, col_api2 = st.columns(2)
        with col_api1:
            platform_sec = st.selectbox("🌐 Platform Seçin", ["🧡 Trendyol Mağazam (API Bağlantılı)", "🧪 Örnek Mağaza Simülasyonu (Test Verisi Çek)"])
        with col_api2:
            aktarim_turu = st.radio("İndirme Yöntemi:", ["🔄 Listeyi Güncelle ve Eksikleri Ekle", "⚠️ Tabloyu Temizle ve Sadece İndirilenleri Koy"])
            
        if st.button("🚀 Ürünleri Platformdan İndir ve Tabloya Aktar", type="primary", use_container_width=True, key="btn_api_fetch"):
            with st.spinner("📦 Platformdan ürün listesi ve güncel satış fiyatları çekiliyor..."):
                items = []
                err_msg = None
                
                if "Trendyol Mağazam" in platform_sec:
                    items, err_msg = fetch_trendyol_products_api()
                else:
                    # Test / Simülasyon Verisi (API bağlı değilse anında denemek için)
                    items = [
                        {"barcode": "AYT003IMT00540", "title": "Zarif Şık Inci Kolye Bileklik Seti", "salePrice": 499.90},
                        {"barcode": "AYT002BKR0007", "title": "El Yapımı %100 Bakır Bilezik", "salePrice": 570.00},
                        {"barcode": "AYT-GLD-0089", "title": "24K Altın Kaplama Baget Yüzük", "salePrice": 450.00},
                        {"barcode": "AYT-SLV-0102", "title": "925 Ayar Gümüş İtalyan Zincir", "salePrice": 600.00},
                        {"barcode": "AYT-DES-0055", "title": "Doğal Ametist Taşlı Küpe", "salePrice": 330.00}
                    ]
                
                if err_msg:
                    st.error(err_msg)
                elif not items:
                    st.warning("⚠️ Mağazanızda çekilecek aktif ürün bulunamadı.")
                else:
                    api_list = []
                    for p in items:
                        brk = str(p.get("barcode", "") or p.get("stockCode", "")).strip()
                        if not brk: continue
                        
                        ad = str(p.get("title", "") or p.get("name", "")).strip()
                        satis_fiyati = float(p.get("salePrice", 0) or p.get("listPrice", 0) or 0.0)
                        
                        # Kural: Ürün maliyeti = Satış Fiyatının 1/3'ü
                        maliyet_hesaplanan = round(satis_fiyati / 3.0, 2)
                        
                        api_list.append({
                            'Barkod': brk,
                            'Ürün Adı': ad,
                            'Satış Fiyatı (TL)': satis_fiyati,
                            'Maliyet (TL)': maliyet_hesaplanan,
                            'Kargo (TL)': 100.0,
                            'Komisyon (%)': 22.5,
                            'Diğer Masraflar (%)': 1.0
                        })
                        
                    df_api = pd.DataFrame(api_list)
                    
                    if "Temizle ve Sadece" in aktarim_turu or mevcut_db.empty:
                        yeni_sonuc_db = df_api
                    else:
                        # Var olanları güncelle, yenileri üstüne ekle
                        eski_olmayanlar = mevcut_db[~mevcut_db['Barkod'].astype(str).isin(df_api['Barkod'])].copy()
                        yeni_sonuc_db = pd.concat([df_api, eski_olmayanlar], ignore_index=True)
                        
                    yeni_sonuc_db.to_csv(utils.DB_FILE, index=False)
                    st.success(f"✅ Başarıyla {len(df_api)} ürün platformdan indirildi! (Maliyet: 1/3, Komisyon: %22.5, Kargo: 100 TL, Diğer: %1 uygulanarak kaydedildi).")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Mevcut Ürün Maliyet Listesi ve Anlık Düzenleme")
    
    if mevcut_db.empty:
        st.info("💡 Sistemde henüz kayıtlı ürün bulunmuyor. Yukarıdaki sekmelerden ürün ekleyebilir veya platformdan indirebilirsiniz.")
        ornek_veri = pd.DataFrame([{
            'Barkod': 'AYT003IMT00540',
            'Ürün Adı': 'Zarif Şık Inci Kolye Seti',
            'Satış Fiyatı (TL)': 499.90,
            'Maliyet (TL)': 166.63,
            'Kargo (TL)': 100.0,
            'Komisyon (%)': 22.5,
            'Diğer Masraflar (%)': 1.0
        }])
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        
    edited_df = st.data_editor(
        utils.tablayi_1den_baslat(mevcut_db),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Barkod": st.column_config.TextColumn("Barkod / SKU", required=True),
            "Ürün Adı": st.column_config.TextColumn("Ürün Adı", width="large"),
            "Satış Fiyatı (TL)": st.column_config.NumberColumn("Satış Fiyatı (TL)", min_value=0.0, format="%.2f"),
            "Maliyet (TL)": st.column_config.NumberColumn("Maliyet (TL)", min_value=0.0, format="%.2f"),
            "Kargo (TL)": st.column_config.NumberColumn("Kargo (TL)", min_value=0.0, format="%.2f"),
            "Komisyon (%)": st.column_config.NumberColumn("Komisyon (%)", min_value=0.0, max_value=100.0, format="%.2f"),
            "Diğer Masraflar (%)": st.column_config.NumberColumn("Diğer Masraflar (%)", min_value=0.0, max_value=100.0, format="%.2f"),
        },
        height=480
    )
    
    if st.button("💾 Tablodaki Değişiklikleri Veritabanına Kaydet", type="primary", use_container_width=True):
        df_save = edited_df.reset_index(drop=True)
        df_save['Barkod'] = df_save['Barkod'].astype(str).str.strip()
        df_save = df_save[df_save['Barkod'] != '']; df_save = df_save[df_save['Barkod'] != 'nan']
        df_save.to_csv(utils.DB_FILE, index=False)
        st.success("✅ Ürün veritabanınız başarıyla güncellendi!")
