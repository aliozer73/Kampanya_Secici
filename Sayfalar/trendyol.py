import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import utils

def render():
    st.markdown('<div class="section-title">🚀 Trendyol Yıldızlı Ürün Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Trendyol\'dan indirdiğiniz "Yıldızlı Ürün Etiketleri" dosyasını yükleyin; 3 Yıldız > 2 Yıldız > 1 Yıldız sırasıyla kârınızı test edelim.</div>', unsafe_allow_html=True)
    
    db = utils.load_db()
    if db.empty: st.error("❌ Lütfen önce Maliyet Yönetimi sayfasından ürün ekleyin."); return
        
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
                for col in [fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz]: merge_df[col + '_num'] = merge_df[col].apply(utils.temizle_ve_sayiya_donustur)
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
                st.dataframe(utils.tablayi_1den_baslat(basarili_df[[barkod_col, yeni_fiyat_col, 'Seçilen Yıldız', 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer: islem_df[cols].to_excel(writer, index=False, sheet_name='Sheet1')
                output.seek(0)
                st.download_button("📥 Trendyol İçin Hazır Excel'i İndir", data=output, file_name=orijinal_dosya_ismi.rsplit('.', 1)[0] + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
