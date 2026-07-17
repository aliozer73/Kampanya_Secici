import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import utils

def render():
    st.markdown('<div class="section-title" style="color:#ff6700;">💜 Hepsiburada Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Hepsiburada\'dan indirdiğiniz "Listelerim" dosyasını yükleyin; sepet indirimi veya standart kampanya kârlılığını hesaplayalım.</div>', unsafe_allow_html=True)
    db = utils.load_db()
    if db.empty: st.error("❌ Lütfen önce Maliyet Yönetimi sayfasından ürün ekleyin."); return
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="hb_m")
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="hb_t")
    kampanya_file = st.file_uploader("Hepsiburada 'Listelerim' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="hb_up")
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        df_kampanya = pd.read_excel(kampanya_file) if not kampanya_file.name.endswith('.csv') else pd.read_csv(kampanya_file, sep=None, engine='python')
        cols = list(df_kampanya.columns)
        col1, col2, col3, col4 = st.columns(4)
        with col1: barkod_col = st.selectbox("Barkod / SKU Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku"]))
        with col2: eski_fiyat_col = st.selectbox("Mevcut Satış Fiyatı", cols, index=utils.find_default_col(cols, ["satış", "satis", "psf"], exclude_keywords=["kampanya"]))
        with col3:
            is_normal_campaign = st.checkbox("🎯 Standart Kampanya (HB Max Fiyat Kuralı)")
            sepet_indirimi = 0.0 if is_normal_campaign else st.number_input("🛒 Kampanya İndirim Oranı (%)", min_value=1.0, max_value=99.0, value=15.0, step=1.0)
            max_fiyat_col = st.selectbox("Girebileceğiniz Max. Fiyat", cols, index=utils.find_default_col(cols, ["max", "maksimum"]))
        with col4: kampanya_fiyat_col = st.selectbox("HB Paneline Yüklenecek Fiyat", cols, index=utils.find_default_col(cols, ["uygulanacağı", "kampanya", "önerilen"]))
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
                fiyat = utils.temizle_ve_sayiya_donustur(row[eski_fiyat_col])
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
            if len(basarili_df) > 0: st.dataframe(utils.tablayi_1den_baslat(basarili_df[[barkod_col, eski_fiyat_col, 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if len(basarili_df) > 0: basarili_df[cols].to_excel(writer, index=False, sheet_name='Uygun Teklifler')
                islem_df[cols + ['Kampanya Durumu', 'Net Kâr (TL)', 'Kâr Marjı (%)']].to_excel(writer, index=False, sheet_name='Tüm Analiz Sonucu')
            output.seek(0)
            st.download_button("📥 Hepsiburada Hazır Excel'i İndir", data=output, file_name="HB_Kampanya_Sonucu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
