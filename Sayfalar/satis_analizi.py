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

# --- GERÇEK API ÇEKME FONKSİYONLARI ---

def fetch_all_trendyol_orders(days_back=365):
    api = utils.load_api_settings()
    seller_id = api.get("ty_seller_id", "").strip()
    api_key = api.get("ty_api_key", "").strip()
    api_secret = api.get("ty_api_secret", "").strip()
    
    if not seller_id or not api_key or not api_secret:
        return None, "❌ Trendyol API bilgileri eksik! Lütfen '⚙️ Ayarlar & API' sayfasından Satıcı ID, API Key ve Secret bilgilerinizi kaydedin."
        
    end_date = int(datetime.now().timestamp() * 1000)
    start_date = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
    
    all_orders = []
    page = 0
    max_pages = 50
    
    while page < max_pages:
        url = f"https://api.trendyol.com/sapigw/suppliers/{seller_id}/orders?startDate={start_date}&endDate={end_date}&page={page}&size=200"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers, auth=(api_key, api_secret), timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                if not content:
                    break
                all_orders.extend(content)
                if len(content) < 200 or page >= data.get("totalPages", 1) - 1:
                    break
                page += 1
            elif resp.status_code == 403:
                return None, "❌ Trendyol API Güvenlik Duvarı (403): Bulut sunucu IP adresi engellendi. Lokal çalıştırabilir veya Excel yükleme yöntemini kullanabilirsiniz."
            else:
                return None, f"❌ Trendyol API Hatası ({resp.status_code}): {resp.text}"
        except Exception as e:
            return None, f"❌ Bağlantı Hatası: {str(e)}"
            
    return all_orders, None

def fetch_all_hepsiburada_orders(days_back=365):
    api = utils.load_api_settings()
    merchant_id = api.get("hb_merchant_id", "").strip()
    api_key = api.get("hb_api_key", "").strip()
    
    if not merchant_id or not api_key:
        return None, "❌ Hepsiburada API bilgileri eksik! Lütfen '⚙️ Ayarlar & API' sayfasından Mağaza ID ve API Anahtarınızı kaydedin."
        
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    url = f"https://mpop.hepsiburada.com/orders/merchantid/{merchant_id}?beginDate={start_date}&endDate={end_date}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Authorization": f"Basic {api_key}",
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        elif resp.status_code in [401, 403]:
            return None, "❌ Hepsiburada API Yetkilendirme Hatası: API Anahtarı veya Mağaza ID geçersiz ya da IP erişim izni yok."
        else:
            return None, f"❌ Hepsiburada API Hatası ({resp.status_code}): {resp.text}"
    except Exception as e:
        return None, f"❌ Bağlantı Hatası: {str(e)}"

def fetch_all_woocommerce_orders(days_back=365):
    api = utils.load_api_settings()
    wc_url = api.get("wc_url", "").strip().rstrip('/')
    ck = api.get("wc_consumer_key", "").strip()
    cs = api.get("wc_consumer_secret", "").strip()
    
    if not wc_url or not ck or not cs:
        return None, "❌ aytens.com (WooCommerce) API bilgileri eksik! Lütfen '⚙️ Ayarlar & API' sayfasından Site URL, Consumer Key ve Secret bilgilerinizi kaydedin."
        
    start_date_iso = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")
    
    all_orders = []
    page = 1
    max_pages = 50
    
    while page <= max_pages:
        url = f"{wc_url}/wp-json/wc/v3/orders?after={start_date_iso}&page={page}&per_page=100"
        try:
            resp = requests.get(url, auth=(ck, cs), timeout=15)
            if resp.status_code == 200:
                orders = resp.json()
                if not orders:
                    break
                all_orders.extend(orders)
                if len(orders) < 100:
                    break
                page += 1
            elif resp.status_code in [401, 403]:
                return None, "❌ WooCommerce API Yetkilendirme Hatası: Consumer Key veya Secret geçersiz."
            else:
                return None, f"❌ WooCommerce API Hatası ({resp.status_code}): {resp.text}"
        except Exception as e:
            return None, f"❌ Bağlantı Hatası: {str(e)}"
            
    return all_orders, None

# --- ANA RENDER FONKSİYONU ---

def render():
    st.markdown('<div class="section-title">📈 Gelişmiş Satış & Kârlılık Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm satış kanallarınızdan sadece <b>gerçek zamanlı API verilerini</b> veya Excel yüklemelerini analiz eder. Örnek/simüle edilmiş sahte veri kesinlikle gösterilmez.</div>', unsafe_allow_html=True)
    
    tab_all, tab_ty, tab_hb, tab_wc = st.tabs([
        "🌐 Tüm Platformlar (Birleşik Gerçek Veri)",
        "🧡 Trendyol Satışları",
        "💜 Hepsiburada Satışları",
        "🛍️ aytens.com (WooCommerce)"
    ])
    
    api_ayarlar = utils.load_api_settings()
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

    def analiz_ekrani_goster(df_satis, platform_etiketi):
        if df_satis.empty:
            st.info(f"💡 **{platform_etiketi} için henüz sipariş verisi yüklenmedi.** Lütfen üstteki butona basarak gerçek API verilerini indirin veya Excel yükleyin.")
            return
            
        df_satis["Tarih"] = pd.to_datetime(df_satis["Tarih"])
        min_t = df_satis["Tarih"].min().date()
        max_t = df_satis["Tarih"].max().date()
        
        st.markdown("### 🗓️ Zaman Aralığı ve Filtreleme")
        col_f1, col_f2 = st.columns([1.8, 1.2])
        with col_f1:
            periyot = st.radio(
                f"⏱️ {platform_etiketi} Periyot Seçimi:",
                ["Tüm Zamanlar", "Bugün (Anlık)", "Bu Hafta (Son 7 Gün)", "Bu Ay (Son 30 Gün)", "Bu Yıl (Son 365 Gün)", "📅 İki Tarih Arası Belirle"],
                horizontal=True, key=f"per_{platform_etiketi}"
            )
        with col_f2:
            if periyot == "📅 İki Tarih Arası Belirle":
                secilen_tarihler = st.date_input("Tarih Aralığı Seçin:", value=[min_t, max_t], min_value=min_t, max_value=max_t, key=f"dt_{platform_etiketi}")
            else:
                st.write("")
                
        bugun_dt = datetime.now()
        if periyot == "Bugün (Anlık)": filt_df = df_satis[df_satis["Tarih"].dt.date == bugun_dt.date()]
        elif periyot == "Bu Hafta (Son 7 Gün)": filt_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=7))]
        elif periyot == "Bu Ay (Son 30 Gün)": filt_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=30))]
        elif periyot == "Bu Yıl (Son 365 Gün)": filt_df = df_satis[df_satis["Tarih"] >= (bugun_dt - timedelta(days=365))]
        elif periyot == "📅 İki Tarih Arası Belirle" and isinstance(secilen_tarihler, (list, tuple)) and len(secilen_tarihler) == 2:
            t1, t2 = secilen_tarihler[0], secilen_tarihler[1]
            filt_df = df_satis[(df_satis["Tarih"].dt.date >= t1) & (df_satis["Tarih"].dt.date <= t2)]
        else:
            filt_df = df_satis.copy()
            
        if filt_df.empty:
            st.warning("⚠️ Seçilen tarih aralığında sipariş kaydı bulunamadı.")
            return
            
        top_adet = int(filt_df["Satış Adedi"].sum())
        top_ciro = filt_df["Satış Tutarı (TL)"].sum()
        top_mal = filt_df["Maliyet (TL)"].sum()
        top_kom = filt_df["Komisyon (TL)"].sum()
        top_kar_gider = filt_df["Kargo Gideri (TL)"].sum()
        top_dig = filt_df["Diğer Masraflar (TL)"].sum()
        top_net = filt_df["Net Kâr (TL)"].sum()
        ort_marj = (top_net / top_ciro * 100.0) if top_ciro > 0 else 0.0
        
        st.markdown(f"#### 💰 {platform_etiketi} Gerçek Finansal Özet")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="stat-badge" style="border-left-color:#0284c7;"><div class="stat-label">Toplam Satış Hacmi</div><div class="stat-value" style="color:#0284c7;">{top_ciro:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">📦 {top_adet} Adet Ürün Satıldı</div></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Net Kâr Tutarı</div><div class="stat-value" style="color:#10b981;">{top_net:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🎯 Ort. Kâr Marjı: <b>%{ort_marj:.1f}</b></div></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="stat-badge" style="border-left-color:#f59e0b;"><div class="stat-label">Pazaryeri Kesintileri</div><div class="stat-value" style="color:#f59e0b;">{top_kom:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🤝 Komisyon + Diğer: {(top_kom+top_dig):,.2f} TL</div></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="stat-badge" style="border-left-color:#ef4444;"><div class="stat-label">Kargo Giderleri</div><div class="stat-value" style="color:#ef4444;">{top_kar_gider:,.2f} TL</div><div style="font-size:12px; color:#64748b; margin-top:4px;">🚚 Ürün Maliyeti: {top_mal:,.2f} TL</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        col_g1, col_g2 = st.columns([1.3, 1])
        urun_grup = filt_df.groupby(["Barkod", "Ürün Adı"]).agg(
            toplam_adet=("Satış Adedi", "sum"),
            toplam_ciro=("Satış Tutarı (TL)", "sum"),
            toplam_kar=("Net Kâr (TL)", "sum"),
            ort_marj=("Kâr Marjı (%)", "mean")
        ).reset_index()
        
        with col_g1:
            st.markdown("#### 🏆 En Çok Satılan ve En Kârlı Ürünler")
            sirala = st.selectbox("Sıralama Ölçütü:", ["🔥 En Çok Kâr Getirenler (TL)", "📦 En Çok Satılanlar (Adet)", "💎 En Yüksek Ciro Yapanlar (TL)"], key=f"sort_{platform_etiketi}")
            if "Kâr" in sirala: gos_df = urun_grup.sort_values("toplam_kar", ascending=False)
            elif "Satılanlar" in sirala: gos_df = urun_grup.sort_values("toplam_adet", ascending=False)
            else: gos_df = urun_grup.sort_values("toplam_ciro", ascending=False)
                
            st.dataframe(
                utils.tablayi_1den_baslat(gos_df).style.format({
                    'toplam_adet': '{:,.0f} Adet', 'toplam_ciro': '{:,.2f} TL', 'toplam_kar': '{:,.2f} TL', 'ort_marj': '% {:.1f}'
                }), use_container_width=True, height=320,
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
            st.markdown("#### 📊 Gider Dağılımı")
            gider_data = pd.DataFrame({
                "Kalem": ["Ürün Maliyeti", "Komisyon", "Kargo", "Diğer", "Net Kâr"],
                "Tutar (TL)": [top_mal, top_kom, top_kar_gider, top_dig, top_net]
            })
            st.bar_chart(gider_data.set_index("Kalem"), use_container_width=True, height=320, color="#0284c7")

        st.markdown("---")
        st.markdown("#### 📋 Detaylı Gerçek Sipariş Dökümü")
        detay_gos = filt_df.copy()
        detay_gos["Tarih (Türkçe)"] = detay_gos["Tarih"].apply(turkce_tarih_formatla)
        gor_sutunlar = ["Platform", "Kargo Şirketi", "Sipariş No", "Tarih (Türkçe)", "Barkod", "Ürün Adı", "Satış Adedi", "Satış Tutarı (TL)", "Maliyet (TL)", "Komisyon (TL)", "Kargo Gideri (TL)", "Diğer Masraflar (TL)", "Net Kâr (TL)", "Kâr Marjı (%)"] if "Kargo Şirketi" in detay_gos.columns else ["Platform", "Sipariş No", "Tarih (Türkçe)", "Barkod", "Ürün Adı", "Satış Adedi", "Satış Tutarı (TL)", "Maliyet (TL)", "Komisyon (TL)", "Kargo Gideri (TL)", "Diğer Masraflar (TL)", "Net Kâr (TL)", "Kâr Marjı (%)"]
        
        st.dataframe(
            utils.tablayi_1den_baslat(detay_gos[gor_sutunlar if all(col in detay_gos.columns for col in gor_sutunlar) else list(detay_gos.columns)]).style.format({
                'Satış Adedi': '{:,.0f}', 'Satış Tutarı (TL)': '{:,.2f} TL', 'Maliyet (TL)': '{:,.2f} TL',
                'Komisyon (TL)': '{:,.2f} TL', 'Kargo Gideri (TL)': '{:,.2f} TL', 'Diğer Masraflar (TL)': '{:,.2f} TL',
                'Net Kâr (TL)': '{:,.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'
            }), use_container_width=True, height=400
        )
        
        out_ex = BytesIO()
        with pd.ExcelWriter(out_ex, engine='openpyxl') as wr:
            utils.tablayi_1den_baslat(detay_gos).reset_index().to_excel(wr, index=False, sheet_name='Detaylı Satış Analizi')
            utils.tablayi_1den_baslat(gos_df).reset_index().to_excel(wr, index=False, sheet_name='Ürün Bazlı Performans')
        out_ex.seek(0)
        
        st.download_button(
            f"📥 {platform_etiketi} Raporunu Excel Olarak İndir",
            data=out_ex, file_name=f"{platform_etiketi}_Gercek_Analiz_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key=f"dl_{platform_etiketi}"
        )

    # --- TRENDYOL SEKME İÇERİĞİ ---
    with tab_ty:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        t_id = api_ayarlar.get("ty_seller_id", "").strip()
        t_key = api_ayarlar.get("ty_api_key", "").strip()
        t_sec = api_ayarlar.get("ty_api_secret", "").strip()
        
        if not t_id or not t_key or not t_sec:
            st.warning("⚠️ **Trendyol API Bağlantısı Yapılandırılmamış!**")
            st.write("Trendyol mağazanızı gerçek zamanlı analiz etmek için **'⚙️ Ayarlar & API'** sayfasından **Satıcı ID (Seller ID)**, **API Key** ve **API Secret** bilgilerinizi kaydetmelisiniz.")
            
            with st.expander("📂 Veya API Olmadan Trendyol Sipariş Exceli Yükle"):
                satis_file = st.file_uploader("Trendyol Sipariş Excel / CSV Dosyası Seçin", type=['xlsx', 'xls', 'csv'], key="ty_up")
                if satis_file:
                    try:
                        df_raw = pd.read_excel(satis_file) if not satis_file.name.endswith('.csv') else pd.read_csv(satis_file, sep=None, engine='python')
                        cols = list(df_raw.columns)
                        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                        with sc1: t_col = st.selectbox("Tarih Sütunu", cols, index=utils.find_default_col(cols, ["tarih", "date"]))
                        with sc2: b_col = st.selectbox("Barkod Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku"]))
                        with sc3: a_col = st.selectbox("Ürün Adı Sütunu", cols, index=utils.find_default_col(cols, ["ürün adı", "ad", "title"]))
                        with sc4: ad_col = st.selectbox("Adet Sütunu", cols, index=utils.find_default_col(cols, ["adet", "miktar", "sayı"]))
                        with sc5: f_col = st.selectbox("Tutar Sütunu", cols, index=utils.find_default_col(cols, ["tutar", "fiyat", "satış", "total"]))
                        
                        if st.button("🚀 Excel'den Siparişleri İşle", type="primary", use_container_width=True):
                            islenen = []
                            for idx, row in df_raw.iterrows():
                                brk = str(row[b_col]).strip() if pd.notna(row[b_col]) else ""
                                if not brk or brk == 'nan': continue
                                trh_val = pd.to_datetime(row[t_col], errors='coerce', dayfirst=True)
                                if pd.isna(trh_val): trh_val = datetime.now()
                                adet = int(utils.temizle_ve_sayiya_donustur(row[ad_col])) if pd.notna(row[ad_col]) else 1
                                if adet <= 0: adet = 1
                                satis_t = utils.temizle_ve_sayiya_donustur(row[f_col])
                                
                                if brk in maliyet_dict:
                                    m_birim = maliyet_dict[brk]['maliyet']; kom_y = maliyet_dict[brk]['komisyon_yuzde']; kargo_b = maliyet_dict[brk]['kargo']; diger_y = maliyet_dict[brk]['diger_yuzde']
                                else:
                                    m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2); kom_y, kargo_b, diger_y = 22.5, 100.0, 1.0
                                m_top = round(m_birim * adet, 2); kom_top = round(satis_t * (kom_y / 100.0), 2); kar_top = round(kargo_b, 2); dig_top = round(satis_t * (diger_y / 100.0), 2)
                                n_kar = round(satis_t - (m_top + kom_top + kar_top + dig_top), 2); k_marj = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                                islenen.append({"Platform": "Trendyol", "Kargo Şirketi": "Trendyol Express", "Sipariş No": f"TY-EX-{idx+1}", "Tarih": trh_val, "Barkod": brk, "Ürün Adı": str(row[a_col]).strip(), "Satış Adedi": adet, "Satış Tutarı (TL)": satis_t, "Maliyet (TL)": m_top, "Komisyon (TL)": kom_top, "Kargo Gideri (TL)": kar_top, "Diğer Masraflar (TL)": dig_top, "Net Kâr (TL)": n_kar, "Kâr Marjı (%)": k_marj})
                            st.session_state['ty_satis_df'] = pd.DataFrame(islenen)
                            st.success("✅ Excel siparişleriniz başarıyla analiz edildi!")
                    except Exception as e: st.error(f"❌ Dosya hatası: {str(e)}")
        else:
            t_c1, t_c2 = st.columns([2.5, 1])
            with t_c1:
                st.success("✅ **Trendyol API Bağlantısı Yapılandırılmış:** Mağazanızdaki tüm geçmiş gerçek siparişleri tek tıkla çekip inceleyebilirsiniz.")
            with t_c2:
                cek_ty = st.button("🔄 Trendyol Tüm Siparişleri Çek", type="primary", use_container_width=True, key="btn_ty_fetch")
                
            if cek_ty:
                with st.spinner("🌐 Trendyol API üzerinden tüm siparişler ve sayfalar taranıyor..."):
                    orders, err = fetch_all_trendyol_orders(days_back=365)
                    if err:
                        st.error(err)
                    elif not orders:
                        st.warning("⚠️ Belirtilen sürede API üzerinde sipariş kaydı bulunamadı.")
                    else:
                        islenen_ty = []
                        for ord_idx, o in enumerate(orders):
                            ord_no = o.get("orderNumber", f"TY-{ord_idx+1}")
                            ord_date_ms = o.get("orderDate", 0)
                            trh_val = datetime.fromtimestamp(ord_date_ms / 1000.0) if ord_date_ms > 0 else datetime.now()
                            cargo_name = str(o.get("cargoProviderName", "Trendyol Express")).strip()
                            for line in o.get("lines", []):
                                brk = str(line.get("barcode", "") or line.get("sku", "")).strip()
                                if not brk: continue
                                ad = str(line.get("productName", "")).strip()
                                adet = int(line.get("quantity", 1))
                                satis_t = float(line.get("price", 0) or line.get("amount", 0)) * adet
                                
                                if brk in maliyet_dict:
                                    m_birim = maliyet_dict[brk]['maliyet']; kom_y = maliyet_dict[brk]['komisyon_yuzde']; kargo_b = maliyet_dict[brk]['kargo']; diger_y = maliyet_dict[brk]['diger_yuzde']
                                else:
                                    m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2); kom_y, kargo_b, diger_y = 22.5, 100.0, 1.0
                                m_toplam = round(m_birim * adet, 2); kom_toplam = round(satis_t * (kom_y / 100.0), 2); kargo_toplam = round(kargo_b, 2); diger_toplam = round(satis_t * (diger_y / 100.0), 2)
                                n_kar = round(satis_t - (m_toplam + kom_toplam + kargo_toplam + diger_toplam), 2); k_marji = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                                islenen_ty.append({"Platform": "Trendyol", "Kargo Şirketi": cargo_name, "Sipariş No": ord_no, "Tarih": trh_val, "Barkod": brk, "Ürün Adı": ad, "Satış Adedi": adet, "Satış Tutarı (TL)": satis_t, "Maliyet (TL)": m_toplam, "Komisyon (TL)": kom_toplam, "Kargo Gideri (TL)": kargo_toplam, "Diğer Masraflar (TL)": diger_toplam, "Net Kâr (TL)": n_kar, "Kâr Marjı (%)": k_marji})
                        st.session_state['ty_satis_df'] = pd.DataFrame(islenen_ty)
                        st.success(f"✅ Trendyol API'den toplam {len(islenen_ty)} adet gerçek sipariş kalemi çekildi!")
        st.markdown("</div>", unsafe_allow_html=True)
        df_ty = st.session_state.get('ty_satis_df', pd.DataFrame())
        analiz_ekrani_goster(df_ty, "Trendyol")

    # --- HEPSİBURADA SEKME İÇERİĞİ ---
    with tab_hb:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        h_id = api_ayarlar.get("hb_merchant_id", "").strip()
        h_key = api_ayarlar.get("hb_api_key", "").strip()
        
        if not h_id or not h_key:
            st.warning("⚠️ **Hepsiburada API Bağlantısı Yapılandırılmamış!**")
            st.write("Hepsiburada siparişlerinizi ve kârlılığınızı görmek için **'⚙️ Ayarlar & API'** sayfasından **Mağaza ID (Merchant ID)** ve **API Anahtarınızı** tanımlamalısınız. Sistemde örnek veya sahte veriler kesinlikle gösterilmez.")
            
            with st.expander("📂 Veya API Olmadan Hepsiburada Sipariş Exceli Yükle"):
                satis_file_hb = st.file_uploader("Hepsiburada Sipariş Excel / CSV Dosyası Seçin", type=['xlsx', 'xls', 'csv'], key="hb_up")
                if satis_file_hb:
                    try:
                        df_raw_hb = pd.read_excel(satis_file_hb) if not satis_file_hb.name.endswith('.csv') else pd.read_csv(satis_file_hb, sep=None, engine='python')
                        cols_hb = list(df_raw_hb.columns)
                        hc1, hc2, hc3, hc4, hc5 = st.columns(5)
                        with hc1: ht_col = st.selectbox("Tarih Sütunu", cols_hb, index=utils.find_default_col(cols_hb, ["tarih", "date"]))
                        with hc2: hb_col = st.selectbox("Barkod Sütunu", cols_hb, index=utils.find_default_col(cols_hb, ["barkod", "barcode", "sku", "merchantsku"]))
                        with hc3: ha_col = st.selectbox("Ürün Adı Sütunu", cols_hb, index=utils.find_default_col(cols_hb, ["ürün adı", "ad", "title", "productname"]))
                        with hc4: had_col = st.selectbox("Adet Sütunu", cols_hb, index=utils.find_default_col(cols_hb, ["adet", "miktar", "sayı", "quantity"]))
                        with hc5: hf_col = st.selectbox("Tutar Sütunu", cols_hb, index=utils.find_default_col(cols_hb, ["tutar", "fiyat", "satış", "total"]))
                        
                        if st.button("🚀 Hepsiburada Excel'den Siparişleri İşle", type="primary", use_container_width=True):
                            islenen_hb_ex = []
                            for idx, row in df_raw_hb.iterrows():
                                brk = str(row[hb_col]).strip() if pd.notna(row[hb_col]) else ""
                                if not brk or brk == 'nan': continue
                                trh_val = pd.to_datetime(row[ht_col], errors='coerce', dayfirst=True)
                                if pd.isna(trh_val): trh_val = datetime.now()
                                adet = int(utils.temizle_ve_sayiya_donustur(row[had_col])) if pd.notna(row[had_col]) else 1
                                if adet <= 0: adet = 1
                                satis_t = utils.temizle_ve_sayiya_donustur(row[hf_col])
                                
                                if brk in maliyet_dict:
                                    m_birim = maliyet_dict[brk]['maliyet']; kom_y = maliyet_dict[brk]['komisyon_yuzde']; kargo_b = maliyet_dict[brk]['kargo']; diger_y = maliyet_dict[brk]['diger_yuzde']
                                else:
                                    m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2); kom_y, kargo_b, diger_y = 18.0, 100.0, 1.0
                                m_top = round(m_birim * adet, 2); kom_top = round(satis_t * (kom_y / 100.0), 2); kar_top = round(kargo_b, 2); dig_top = round(satis_t * (diger_y / 100.0), 2)
                                n_kar = round(satis_t - (m_top + kom_top + kar_top + dig_top), 2); k_marj = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                                islenen_hb_ex.append({"Platform": "Hepsiburada", "Kargo Şirketi": "HepsiJet", "Sipariş No": f"HB-EX-{idx+1}", "Tarih": trh_val, "Barkod": brk, "Ürün Adı": str(row[ha_col]).strip(), "Satış Adedi": adet, "Satış Tutarı (TL)": satis_t, "Maliyet (TL)": m_top, "Komisyon (TL)": kom_top, "Kargo Gideri (TL)": kar_top, "Diğer Masraflar (TL)": dig_top, "Net Kâr (TL)": n_kar, "Kâr Marjı (%)": k_marj})
                            st.session_state['hb_satis_df'] = pd.DataFrame(islenen_hb_ex)
                            st.success("✅ Hepsiburada Excel siparişleriniz başarıyla analiz edildi!")
                    except Exception as e: st.error(f"❌ Dosya hatası: {str(e)}")
        else:
            h_c1, h_c2 = st.columns([2.5, 1])
            with h_c1:
                st.success("✅ **Hepsiburada API Bağlantısı Yapılandırılmış:** Mağazanızdaki aktif siparişleri hemen çekebilirsiniz.")
            with h_c2:
                cek_hb = st.button("🔄 Hepsiburada Siparişleri Çek", type="primary", use_container_width=True, key="btn_hb_fetch")
                if cek_hb:
                    with st.spinner("🌐 Hepsiburada servisleriyle senkronizasyon sağlanıyor..."):
                        orders, err = fetch_all_hepsiburada_orders(days_back=365)
                        if err: st.error(err)
                        else:
                            islenen_hb = []
                            for ord_idx, o in enumerate(orders if isinstance(orders, list) else []):
                                ord_no = o.get("ordernumber", f"HB-{ord_idx+1}")
                                trh_val = pd.to_datetime(o.get("orderdate", datetime.now()), errors='coerce')
                                cargo_name = str(o.get("cargocompany", "HepsiJet")).strip()
                                brk = str(o.get("merchantsku", "") or o.get("sku", "")).strip()
                                if not brk: continue
                                ad = str(o.get("productname", "")).strip()
                                adet = int(o.get("quantity", 1))
                                satis_t = float(o.get("totalprice", 0) or o.get("price", 0))
                                
                                if brk in maliyet_dict:
                                    m_birim = maliyet_dict[brk]['maliyet']; kom_y = maliyet_dict[brk]['komisyon_yuzde']; kargo_b = maliyet_dict[brk]['kargo']; diger_y = maliyet_dict[brk]['diger_yuzde']
                                else:
                                    m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2); kom_y, kargo_b, diger_y = 18.0, 100.0, 1.0
                                m_toplam = round(m_birim * adet, 2); kom_toplam = round(satis_t * (kom_y / 100.0), 2); kargo_toplam = round(kargo_b, 2); diger_toplam = round(satis_t * (diger_y / 100.0), 2)
                                n_kar = round(satis_t - (m_toplam + kom_toplam + kargo_toplam + diger_toplam), 2); k_marji = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                                islenen_hb.append({"Platform": "Hepsiburada", "Kargo Şirketi": cargo_name, "Sipariş No": ord_no, "Tarih": trh_val, "Barkod": brk, "Ürün Adı": ad, "Satış Adedi": adet, "Satış Tutarı (TL)": satis_t, "Maliyet (TL)": m_toplam, "Komisyon (TL)": kom_toplam, "Kargo Gideri (TL)": kargo_toplam, "Diğer Masraflar (TL)": diger_toplam, "Net Kâr (TL)": n_kar, "Kâr Marjı (%)": k_marji})
                            st.session_state['hb_satis_df'] = pd.DataFrame(islenen_hb)
                            st.success(f"✅ Hepsiburada'dan {len(islenen_hb)} sipariş çekildi!")
        st.markdown("</div>", unsafe_allow_html=True)
        df_hb = st.session_state.get('hb_satis_df', pd.DataFrame())
        analiz_ekrani_goster(df_hb, "Hepsiburada")

    # --- WOOCOMMERCE / AYTENS.COM SEKME İÇERİĞİ ---
    with tab_wc:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        w_url = api_ayarlar.get("wc_url", "").strip()
        w_key = api_ayarlar.get("wc_consumer_key", "").strip()
        w_sec = api_ayarlar.get("wc_consumer_secret", "").strip()
        
        if not w_url or not w_key or not w_sec:
            st.warning("⚠️ **aytens.com (WooCommerce) API Bağlantısı Yapılandırılmamış!**")
            st.write("Kendi e-ticaret sitenizin siparişlerini çekmek için **'⚙️ Ayarlar & API'** sayfasından **Site URL**, **Consumer Key** ve **Consumer Secret** bilgilerinizi girmelisiniz.")
        else:
            w_c1, w_c2 = st.columns([2.5, 1])
            with w_c1:
                st.success("✅ **aytens.com API Bağlantısı Yapılandırılmış:** Web sitenizin siparişleri hazır.")
            with w_c2:
                cek_wc = st.button("🔄 aytens.com Senkronize Et", type="primary", use_container_width=True, key="btn_wc_fetch")
                if cek_wc:
                    with st.spinner("🌐 aytens.com Rest API üzerinden siparişler çekiliyor..."):
                        orders, err = fetch_all_woocommerce_orders(days_back=365)
                        if err: st.error(err)
                        else:
                            islenen_wc = []
                            for o in (orders if isinstance(orders, list) else []):
                                ord_no = str(o.get("id", ""))
                                trh_val = pd.to_datetime(o.get("date_created", datetime.now()), errors='coerce')
                                for line in o.get("line_items", []):
                                    brk = str(line.get("sku", "") or line.get("name", "")).strip()
                                    if not brk: continue
                                    ad = str(line.get("name", "")).strip()
                                    adet = int(line.get("quantity", 1))
                                    satis_t = float(line.get("total", 0))
                                    
                                    if brk in maliyet_dict:
                                        m_birim = maliyet_dict[brk]['maliyet']; kom_y = maliyet_dict[brk]['komisyon_yuzde']; kargo_b = maliyet_dict[brk]['kargo']; diger_y = maliyet_dict[brk]['diger_yuzde']
                                    else:
                                        m_birim = round((satis_t / adet) / 3.0, 2) if adet > 0 else round(satis_t / 3.0, 2); kom_y, kargo_b, diger_y = 3.5, 75.0, 1.0
                                    m_toplam = round(m_birim * adet, 2); kom_toplam = round(satis_t * (kom_y / 100.0), 2); kargo_toplam = round(kargo_b, 2); diger_toplam = round(satis_t * (diger_y / 100.0), 2)
                                    n_kar = round(satis_t - (m_toplam + kom_toplam + kargo_toplam + diger_toplam), 2); k_marji = round((n_kar / satis_t) * 100.0, 2) if satis_t > 0 else 0.0
                                    # Kural: Satış platformu aytens.com, kargo şirketi Kargonomi
                                    islenen_wc.append({"Platform": "aytens.com", "Kargo Şirketi": "Kargonomi", "Sipariş No": ord_no, "Tarih": trh_val, "Barkod": brk, "Ürün Adı": ad, "Satış Adedi": adet, "Satış Tutarı (TL)": satis_t, "Maliyet (TL)": m_toplam, "Komisyon (TL)": kom_toplam, "Kargo Gideri (TL)": kargo_toplam, "Diğer Masraflar (TL)": diger_toplam, "Net Kâr (TL)": n_kar, "Kâr Marjı (%)": k_marji})
                            st.session_state['wc_satis_df'] = pd.DataFrame(islenen_wc)
                            st.success(f"✅ aytens.com üzerinden {len(islenen_wc)} ürün kalemi çekildi!")
        st.markdown("</div>", unsafe_allow_html=True)
        df_wc = st.session_state.get('wc_satis_df', pd.DataFrame())
        analiz_ekrani_goster(df_wc, "aytens.com (WooCommerce)")

    # --- TÜM PLATFORMLAR (BİRLEŞİK GERÇEK VERİ ÖZETİ) ---
    with tab_all:
        st.markdown("#### 🌐 Tüm Pazaryeri ve Satış Kanallarının Birleşik Gerçek Analizi")
        st.write("Yalnızca API üzerinden veya Excel ile yüklenmiş olan **gerçek siparişlerinizin** birleştirilmiş finansal tablosu.")
        
        gercek_df_list = []
        if 'ty_satis_df' in st.session_state and not st.session_state['ty_satis_df'].empty: gercek_df_list.append(st.session_state['ty_satis_df'])
        if 'hb_satis_df' in st.session_state and not st.session_state['hb_satis_df'].empty: gercek_df_list.append(st.session_state['hb_satis_df'])
        if 'wc_satis_df' in st.session_state and not st.session_state['wc_satis_df'].empty: gercek_df_list.append(st.session_state['wc_satis_df'])
        
        if not gercek_df_list:
            st.info("💡 **Görüntülenecek Gerçek Veri Yok:** Birleşik tabloyu görmek için lütfen diğer sekmelerden gerçek API bağlantısı kurup siparişlerinizi çekin.")
        else:
            df_all = pd.concat(gercek_df_list, ignore_index=True)
            plat_ciro = df_all.groupby("Platform")["Satış Tutarı (TL)"].sum().reset_index()
            st.bar_chart(plat_ciro.set_index("Platform"), color="#10b981", height=220, use_container_width=True)
            analiz_ekrani_goster(df_all, "Birleşik Gerçek Platformlar")
