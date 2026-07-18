import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from io import BytesIO
import utils

TURKCE_AYLAR = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

def turkce_tarih_formatla(dt):
    if pd.isna(dt): return ""
    try:
        return f"{dt.day} {TURKCE_AYLAR[dt.month]} {dt.year}"
    except:
        return str(dt)[:10]

def fetch_trendyol_orders_api(days_back=30):
    api = utils.load_api_settings()
    seller_id = api.get("ty_seller_id", "").strip()
    api_key = api.get("ty_api_key", "").strip()
    api_secret = api.get("ty_api_secret", "").strip()
    
    if not seller_id or not api_key or not api_secret:
        return None, "❌ Trendyol API bilgileri eksik! Lütfen '⚙️ Ayarlar & API' sayfasından Satıcı ID, API Key ve Secret bilgilerinizi kaydedin."
        
    end_date = int(datetime.now().timestamp() * 1000)
    start_date = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    
    url = f"https://api.trendyol.com/sapigw/suppliers/{seller_id}/orders?startDate={start_date}&endDate={end_date}&size=200"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, auth=(api_key, api_secret), timeout=15)
        if response.status_code == 200:
            data = response.json()
            orders = data.get("content", [])
            return orders, None
        elif response.status_code == 403:
            return None, "❌ Trendyol API Güvenlik Duvarı (403): Bulut sunucu IP'si engellendi. Lokal çalıştırın, Excel yükleyin veya XML/Simülasyon kullanın."
        else:
            return None, f"❌ Trendyol API Hatası ({response.status_code}): {response.text}"
    except Exception as e:
        return None, f"❌ Bağlantı Hatası: {str(e)}"

def ornek_satis_verisi_olustur():
    np.random.seed(42)
    bugun = datetime.now()
    tarihler = [bugun - timedelta(days=int(x), hours=np.random.randint(0, 24)) for x in np.random.exponential(scale=15, size=150)]
    
    urunler = [
        {"barkod": "AYT003IMT00540", "ad": "Zarif Şık Inci Kolye Seti", "satis": 499.90, "maliyet": 166.63},
        {"barkod": "AYT002BKR0007", "ad": "El Yapımı %100 Bakır Bilezik", "satis": 570.00, "maliyet": 190.00},
        {"barkod": "AYT-GLD-0089", "ad": "24K Altın Kaplama Baget Yüzük", "satis": 450.00, "maliyet": 150.00},
        {"barkod": "AYT-SLV-0102", "ad": "925 Ayar Gümüş İtalyan Zincir", "satis": 600.00, "maliyet": 200.00},
        {"barkod": "AYT-DES-0055", "ad": "Doğal Ametist Taşlı Küpe", "satis": 330.00, "maliyet": 110.00},
        {"barkod": "AYT-XML-001", "ad": "Doğal İnci Kolye - Özel Tasarım", "satis": 750.00, "maliyet": 250.00}
    ]
    
    veriler = []
    for i, trh in enumerate(sorted(tarihler)):
        u = np.random.choice(urunler)
        adet = np.random.choice([1, 1, 1, 2, 3], p=[0.7, 0.15, 0.05, 0.07, 0.03])
        satis_tutari = round(u["satis"] * adet, 2)
        maliyet_tutari = round(u["maliyet"] * adet, 2)
        komisyon_tutari = round(satis_tutari * 0.225, 2)
        kargo_tutari = 100.0 if satis_tutari < 500 else 75.0
        diger_masraf = round(satis_tutari * 0.01, 2)
        net_kar = round(satis_tutari - (maliyet_tutari + komisyon_tutari + kargo_tutari + diger_masraf), 2)
        kar_marji = round((net_kar / satis_tutari) * 100.0, 2) if satis_tutari > 0 else 0.0
        
        veriler.append({
            "Sipariş No": f"SP-{10000 + i}",
            "Tarih": trh,
            "Barkod": u["barkod"],
            "Ürün Adı": u["ad"],
            "Satış Adedi": adet,
            "Satış Tutarı (TL)": satis_tutari,
            "Maliyet (TL)": maliyet_tutari,
            "Komisyon (TL)": komisyon_tutari,
            "Kargo Gideri (TL)": kargo_tutari,
            "Diğer Masraflar (TL)": diger_masraf,
            "Net Kâr (TL)": net_kar,
            "Kâr Marjı (%)": kar_marji
        })
    return pd.DataFrame(veriler)

def render():
    st.markdown('<div class="section-title">📈 Gelişmiş Satış & Kârlılık Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Sipariş verilerinizi API ile platformlardan anlık çekin, Excel yükleyin veya simülasyonla detaylı finansal göstergeleri inceleyin.</div>', unsafe_allow_html=True)
    
    # Veri Kaynağı Seçimi
    st.markdown("<div class='web-card'>", unsafe_allow_html=True)
    veri_kaynagi = st.radio("📊 Analiz Edilecek Veri Kaynağı:", [
        "🌐 Satış Platformlarından API ile Çek (Trendyol Entegrasyonu)",
        "📂 Trendyol / Pazaryeri Satış Exceli Yükle",
        "🧪 Örnek Mağaza Satış Simülasyonu (Anlık 150 Sipariş Testi)"
    ], horizontal=True)
    
    df_satis = pd.DataFrame()
    db_maliyet = utils.load_db()
    maliyet_dict = {}
    if not db_maliyet.empty:
        for _, r in db_maliyet.iterrows():
            brk = str(r['Barkod']).strip()
            maliyet_dict[brk] = {
                'maliyet': utils.temizle_ve_sayiya_donustur(r.get('Maliyet (TL)', 0)),
                'kargo': utils.temizle_ve_sayiya_donustur(r.get('Kargo (TL)', 100)),
                'komisyon_yuzde': utils.temizle_ve_sayiya_donustur(r.get('Komisyon (%)', 22.5)),
                'diger_yuzde': utils.temizle_ve_sayiya_donustur(r.get('Diğer Masraflar (%)', 1.0))
            }
    
    if "API ile Çek" in veri_kaynagi:
        c_api1, c_api2 = st.columns([2, 1])
        with c_api1:
            gun_sec = st.slider("📅 Kaç Günlük Sipariş Geçmişi Çekilsin?", min_value=1, max_value=90, value=30, step=1)
        with c_api2:
            st.write("") # Boşluk
            api_cek_btn = st.button("🚀 API'den Siparişleri İndir", type="primary", use_container_width=True)
            
        if api_cek_btn:
            with st.spinner(f"🌐 Trendyol sunucularından son {gun_sec} günün sipariş verisi çekiliyor..."):
                orders, err = fetch_trendyol_orders_api(days_back=gun_sec)
                if err:
                    st.error(err)
                    st.info("💡 API IP engeli yaşıyorsanız, örnek simülasyona veya Excel yükleme moduna geçebilirsiniz.")
                elif not orders:
                    st.warning("⚠️ Seçilen zaman aralığında aktif sipariş bulunamadı.")
                else:
                    islenen_api = []
                    for ord_idx, o in enumerate(orders):
                        ord_no = o.get("orderNumber", f"API-{ord_idx+1}")
                        ord_date_ms = o.get("orderDate", 0)
                        trh_val = datetime.fromtimestamp(ord_date_ms / 1000.0) if ord_date_ms > 0 else datetime.now()
                        
                        lines = o.get("lines", [])
                        for line in lines:
                            brk = str(line.get("barcode", "") or line.get("sku", "")).strip()
                            if not brk: continue
                            
                            ad = str(line.get("productName", "")).strip()
                            adet = int(line.get("quantity", 1))
                            satis_t = float(line.get("price", 0) or line.get("amount", 0)) * adet
                            
                            if brk in maliyet_dict:
                                m_birim = maliyet_dict[brk]['maliyet']
                                kom_y = maliyet_dict[brk]['komisyon_yuzde']
                                kargo_b = maliyet_dict[brk]['kargo']
                                diger_y = maliyet_dict[brk]['diger_yuzde']
                            else:
                                m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2)
                                kom_y, kargo_b, diger_y = 22.5, 100.0, 1.0
                                
                            m_toplam = round(m_birim * adet, 2)
                            kom_toplam = round(satis_t * (kom_y / 100.0), 2)
                            kargo_toplam = round(kargo_b, 2)
                            diger_toplam = round(satis_t * (diger_y / 100.0), 2)
                            n_kar = round(satis_t - (m_toplam + kom_toplam + kargo_toplam + diger_toplam), 2)
                            k_marji = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                            
                            islenen_api.append({
                                "Sipariş No": ord_no,
                                "Tarih": trh_val,
                                "Barkod": brk,
                                "Ürün Adı": ad,
                                "Satış Adedi": adet,
                                "Satış Tutarı (TL)": satis_t,
                                "Maliyet (TL)": m_toplam,
                                "Komisyon (TL)": kom_toplam,
                                "Kargo Gideri (TL)": kargo_toplam,
                                "Diğer Masraflar (TL)": diger_toplam,
                                "Net Kâr (TL)": n_kar,
                                "Kâr Marjı (%)": k_marji
                            })
                    st.session_state['api_satis_df'] = pd.DataFrame(islenen_api)
                    st.success(f"✅ API'den {len(islenen_api)} sipariş kalemi başarıyla aktarıldı ve maliyet tablonuzla eşleştirildi!")
        df_satis = st.session_state.get('api_satis_df', pd.DataFrame())

    elif "Exceli Yükle" in veri_kaynagi:
        satis_file = st.file_uploader("Trendyol Sipariş Listesi Excel/CSV Yükleyin", type=['xlsx', 'xls', 'csv'], key="satis_up")
        if satis_file:
            try:
                if satis_file.name.endswith('.csv'):
                    try: df_raw = pd.read_csv(satis_file, sep=None, engine='python')
                    except: satis_file.seek(0); df_raw = pd.read_csv(satis_file, delimiter=';')
                else:
                    df_raw = pd.read_excel(satis_file)
                    
                cols = list(df_raw.columns)
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                with sc1: t_col = st.selectbox("Tarih Sütunu", cols, index=utils.find_default_col(cols, ["tarih", "date", "zaman", "sipariş tarihi"]))
                with sc2: b_col = st.selectbox("Barkod Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku", "stok kodu"]))
                with sc3: a_col = st.selectbox("Ürün Adı Sütunu", cols, index=utils.find_default_col(cols, ["ürün adı", "ad", "title", "name", "ürün"]))
                with sc4: ad_col = st.selectbox("Adet Sütunu", cols, index=utils.find_default_col(cols, ["adet", "miktar", "quantity", "sayı"]))
                with sc5: f_col = st.selectbox("Satış Tutarı Sütunu", cols, index=utils.find_default_col(cols, ["tutar", "fiyat", "satış", "total", "toplam", "ödeme"]))
                
                if st.button("🚀 Siparişleri Analiz Et ve Finansal Metrikleri Hesapla", type="primary", use_container_width=True):
                    islenen_veriler = []
                    for idx, row in df_raw.iterrows():
                        brk = str(row[b_col]).strip() if pd.notna(row[b_col]) else ""
                        if not brk or brk == 'nan': continue
                        
                        trh_val = pd.to_datetime(row[t_col], errors='coerce', dayfirst=True)
                        if pd.isna(trh_val): trh_val = datetime.now()
                        
                        adet = int(utils.temizle_ve_sayiya_donustur(row[ad_col])) if pd.notna(row[ad_col]) else 1
                        if adet <= 0: adet = 1
                        
                        satis_t = utils.temizle_ve_sayiya_donustur(row[f_col])
                        
                        if brk in maliyet_dict:
                            m_birim = maliyet_dict[brk]['maliyet']
                            kom_y = maliyet_dict[brk]['komisyon_yuzde']
                            kargo_b = maliyet_dict[brk]['kargo']
                            diger_y = maliyet_dict[brk]['diger_yuzde']
                        else:
                            m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2)
                            kom_y, kargo_b, diger_y = 22.5, 100.0, 1.0
                            
                        m_toplam = round(m_birim * adet, 2)
                        kom_toplam = round(satis_t * (kom_y / 100.0), 2)
                        kargo_toplam = round(kargo_b, 2)
                        diger_toplam = round(satis_t * (diger_y / 100.0), 2)
                        n_kar = round(satis_t - (m_toplam + kom_toplam + kargo_toplam + diger_toplam), 2)
                        k_marji = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                        
                        islenen_veriler.append({
                            "Sipariş No": f"EX-{idx+1}",
                            "Tarih": trh_val,
                            "Barkod": brk,
                            "Ürün Adı": str(row[a_col]).strip() if pd.notna(row[a_col]) else "",
                            "Satış Adedi": adet,
                            "Satış Tutarı (TL)": satis_t,
                            "Maliyet (TL)": m_toplam,
                            "Komisyon (TL)": kom_toplam,
                            "Kargo Gideri (TL)": kargo_toplam,
                            "Diğer Masraflar (TL)": diger_toplam,
                            "Net Kâr (TL)": n_kar,
                            "Kâr Marjı (%)": k_marji
                        })
                    st.session_state['yuklenen_satis_df'] = pd.DataFrame(islenen_veriler)
                    st.success("✅ Excel başarıyla işlendi ve maliyet verileri eşleştirildi!")
            except Exception as e:
                st.error(f"❌ Dosya işleme hatası: {str(e)}")
        df_satis = st.session_state.get('yuklenen_satis_df', pd.DataFrame())
    else:
        df_satis = ornek_satis_verisi_olustur()
        
    st.markdown("</div>", unsafe_allow_html=True)
        
    if df_satis.empty:
        st.info("💡 Analiz verilerini görmek için yukarıdaki seçeneklerden API ile çekme yapabilir, Excel yükleyebilir veya Simülasyon modunu seçebilirsiniz.")
        return
        
    # Tarih formatlaması
    df_satis["Tarih"] = pd.to_datetime(df_satis["Tarih"])
    min_tarih = df_satis["Tarih"].min().date()
    max_tarih = df_satis["Tarih"].max().date()
    
    st.markdown("---")
    st.markdown("### 🗓️ Zaman Aralığı ve Filtreleme")
    
    col_f1, col_f2 = st.columns([1.8, 1.2])
    with col_f1:
        periyot_secimi = st.radio(
            "⏱️ Hızlı Periyot Seçimi:",
            ["Tüm Zamanlar", "Bugün (Anlık)", "Bu Hafta (Son 7 Gün)", "Bu Ay (Son 30 Gün)", "Bu Yıl (Son 365 Gün)", "📅 İki Tarih Arası Belirle"],
            horizontal=True
        )
    with col_f2:
        if periyot_secimi == "📅 İki Tarih Arası Belirle":
            secilen_tarihler = st.date_input("Tarih Aralığı Seçin:", value=[min_tarih, max_tarih], min_value=min_tarih, max_value=max_tarih)
        else:
            st.write("") # Boşluk
            
    # Filtreleme Mantığı
    bugun_dt = datetime.now()
    if periyot_secimi == "Bugün (Anlık)":
        filtrelenmis_df = df_satis[df_satis["Tarih"].dt.date == bugun_dt.date()]
    elif periyot_secimi == "Bu Hafta (Son 7 Gün)":
        filtrelenmis_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=7))]
    elif periyot_secimi == "Bu Ay (Son 30 Gün)":
        filtrelenmis_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=30))]
    elif periyot_secimi == "Bu Yıl (Son 365 Gün)":
        filtrelenmis_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=365))]
    elif periyot_secimi == "📅 İki Tarih Arası Belirle" and isinstance(secilen_tarihler, (list, tuple)) and len(secilen_tarihler) == 2:
        t1, t2 = secilen_tarihler[0], secilen_tarihler[1]
        filtrelenmis_df = df_satis[(df_satis["Tarih"].dt.date >= t1) & (df_satis["Tarih"].dt.date <= t2)]
    else:
        filtrelenmis_df = df_satis.copy()
        
    if filtrelenmis_df.empty:
        st.warning("⚠️ Seçilen tarih aralığında sipariş kaydı bulunamadı.")
        return
        
    # -----------------------------------------------------------------
    # FİNANSAL GÖSTERGELER (METRİKLER)
    # -----------------------------------------------------------------
    top_satis_adet = int(filtrelenmis_df["Satış Adedi"].sum())
    top_ciro = filtrelenmis_df["Satış Tutarı (TL)"].sum()
    top_maliyet = filtrelenmis_df["Maliyet (TL)"].sum()
    top_komisyon = filtrelenmis_df["Komisyon (TL)"].sum()
    top_kargo = filtrelenmis_df["Kargo Gideri (TL)"].sum()
    top_diger = filtrelenmis_df["Diğer Masraflar (TL)"].sum()
    top_net_kar = filtrelenmis_df["Net Kâr (TL)"].sum()
    ort_kar_marji = (top_net_kar / top_ciro * 100.0) if top_ciro > 0 else 0.0
    
    st.markdown("#### 💰 Özet Finansal Göstergeler (Seçilen Dönem)")
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div class="stat-badge" style="border-left-color:#0284c7;"><div class="stat-label">Toplam Satış Hacmi</div><div class="stat-value" style="color:#0284c7;">{top_ciro:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">📦 {top_satis_adet} Adet Ürün Satıldı</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Net Kâr Tutarı</div><div class="stat-value" style="color:#10b981;">{top_net_kar:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🎯 Ort. Kâr Marjı: <b>%{ort_kar_marji:.1f}</b></div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="stat-badge" style="border-left-color:#f59e0b;"><div class="stat-label">Pazaryeri Kesintileri</div><div class="stat-value" style="color:#f59e0b;">{top_komisyon:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🤝 Komisyon + Diğer: {(top_komisyon+top_diger):,.2f} TL</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="stat-badge" style="border-left-color:#ef4444;"><div class="stat-label">Kargo Giderleri</div><div class="stat-value" style="color:#ef4444;">{top_kargo:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🚚 Ürün Maliyeti: {top_maliyet:,.2f} TL</div></div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # GÖRSELLEŞTİRME VE EN ÇOK SATANLAR
    # -----------------------------------------------------------------
    st.markdown("---")
    col_g1, col_g2 = st.columns([1.3, 1])
    
    urun_grup = filtrelenmis_df.groupby(["Barkod", "Ürün Adı"]).agg(
        toplam_adet=("Satış Adedi", "sum"),
        toplam_ciro=("Satış Tutarı (TL)", "sum"),
        toplam_kar=("Net Kâr (TL)", "sum"),
        ort_marj=("Kâr Marjı (%)", "mean")
    ).reset_index()
    
    with col_g1:
        st.markdown("#### 🏆 En Çok Satılan ve En Kârlı Ürünler")
        siralamayi_sec = st.selectbox("Sıralama Ölçütü:", ["🔥 En Çok Kâr Getirenler (TL)", "📦 En Çok Satılanlar (Adet)", "💎 En Yüksek Ciro Yapanlar (TL)"], key="sort_box")
        
        if "Kâr" in siralamayi_sec:
            gosterim_df = urun_grup.sort_values("toplam_kar", ascending=False)
        elif "Satılanlar" in siralamayi_sec:
            gosterim_df = urun_grup.sort_values("toplam_adet", ascending=False)
        else:
            gosterim_df = urun_grup.sort_values("toplam_ciro", ascending=False)
            
        st.dataframe(
            utils.tablayi_1den_baslat(gosterim_df).style.format({
                'toplam_adet': '{:,.0f} Adet',
                'toplam_ciro': '{:,.2f} TL',
                'toplam_kar': '{:,.2f} TL',
                'ort_marj': '% {:.1f}'
            }),
            use_container_width=True,
            height=320,
            column_config={
                "Barkod": st.column_config.TextColumn("Barkod"),
                "Ürün Adı": st.column_config.TextColumn("Ürün Adı", width="medium"),
                "toplam_adet": st.column_config.NumberColumn("Satış Adedi"),
                "toplam_ciro": st.column_config.NumberColumn("Toplam Ciro"),
                "toplam_kar": st.column_config.NumberColumn("Net Kâr"),
                "ort_marj": st.column_config.NumberColumn("Ort. Marj"),
            }
        )
        
    with col_g2:
        st.markdown("#### 📊 Toplam Satışın Gider Dağılımı")
        gider_data = pd.DataFrame({
            "Kalem": ["Ürün Maliyeti", "Komisyon Kesintisi", "Kargo Ücretleri", "Diğer Masraflar", "Net Kâr"],
            "Tutar (TL)": [top_maliyet, top_komisyon, top_kargo, top_diger, top_net_kar]
        })
        st.bar_chart(gider_data.set_index("Kalem"), use_container_width=True, height=320, color="#0284c7")

    # -----------------------------------------------------------------
    # DETAYLI SİPARİŞ VERİTABANI TABLOSU
    # -----------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 📋 Detaylı Sipariş ve Masraf Dökümü")
    st.write("Seçilen dönemdeki her siparişin kuruşu kuruşuna maliyet, kargo, komisyon ve net kâr dökümünü inceleyebilir ve Excel olarak indirebilirsiniz.")
    
    detay_gosterim = filtrelenmis_df.copy()
    detay_gosterim["Tarih (Türkçe)"] = detay_gosterim["Tarih"].apply(turkce_tarih_formatla)
    
    gorunen_sutunlar = ["Sipariş No", "Tarih (Türkçe)", "Barkod", "Ürün Adı", "Satış Adedi", "Satış Tutarı (TL)", "Maliyet (TL)", "Komisyon (TL)", "Kargo Gideri (TL)", "Diğer Masraflar (TL)", "Net Kâr (TL)", "Kâr Marjı (%)"]
    
    st.dataframe(
        utils.tablayi_1den_baslat(detay_gosterim[gorunen_sutunlar]).style.format({
            'Satış Adedi': '{:,.0f}',
            'Satış Tutarı (TL)': '{:,.2f} TL',
            'Maliyet (TL)': '{:,.2f} TL',
            'Komisyon (TL)': '{:,.2f} TL',
            'Kargo Gideri (TL)': '{:,.2f} TL',
            'Diğer Masraflar (TL)': '{:,.2f} TL',
            'Net Kâr (TL)': '{:,.2f} TL',
            'Kâr Marjı (%)': '% {:.2f}'
        }),
        use_container_width=True,
        height=400
    )
    
    out_excel = BytesIO()
    with pd.ExcelWriter(out_excel, engine='openpyxl') as wr:
        utils.tablayi_1den_baslat(detay_gosterim[gorunen_sutunlar]).reset_index().to_excel(wr, index=False, sheet_name='Detaylı Satış Analizi')
        utils.tablayi_1den_baslat(gosterim_df).reset_index().to_excel(wr, index=False, sheet_name='Ürün Bazlı Performans')
    out_excel.seek(0)
    
    st.download_button(
        "📥 Seçilen Dönemin Analiz Raporunu Excel Olarak İndir",
        data=out_excel,
        file_name=f"Satis_ve_Karlilik_Analizi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
