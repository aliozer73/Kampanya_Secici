import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import utils

# =====================================================================
# SİSTEM SÜRÜM BİLGİSİ
# Versiyon: v2.0.0 (Çift Modüllü Trendyol Analizi: Yıldızlı & Plus)
# =====================================================================

def render():
    st.markdown('<div class="section-title">🚀 Trendyol Fiyat & Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Yıldızlı ürün kampanyaları ve Plus komisyon tarifelerini birbirinden bağımsız modüllerde test edip kârlılığınızı garantileyin.</div>', unsafe_allow_html=True)
    
    # Versiyon Bilgi ve Geri Dönüş Paneli
    with st.expander("ℹ️ Versiyon v2.0.0 Bilgisi & Geri Dönüş (Rollback) Rehberi", expanded=False):
        st.markdown("""
        - **Aktif Sürüm:** `v2.0.0` (Yıldızlı Ürün ve Plus Komisyon tarifeleri sekmeleri ayrıldı).
        - **Format Koruma:** Her iki modül de yüklenen Excel dosyasının sütun ve sayfa yapısını %100 koruyarak Trendyol'un istediği formatta çıktı üretir.
        - **Önceki Versiyona Dönüş:** Eğer eski sürümünüze geri dönmek isterseniz, terminalinizden `git checkout v1.0.0` komutunu çalıştırmanız veya yedeklediğiniz eski `trendyol.py` dosyasını `Sayfalar/` klasörüne yapıştırmanız yeterlidir.
        """)
    
    db = utils.load_db()
    if db.empty:
        st.error("❌ Lütfen önce '📦 Maliyet Yönetimi' sayfasından ürün maliyetlerinizi ekleyin.")
        return
        
    tab_yildiz, tab_plus = st.tabs(["⭐ Yıldızlı Ürün Kampanya Analizi", "➕ Plus Komisyon Tarifeleri Analizi"])
    
    # -----------------------------------------------------------------
    # SEKME 1: YILDIZLI ÜRÜN KAMPANYA ANALİZİ
    # -----------------------------------------------------------------
    with tab_yildiz:
        st.markdown("#### ⭐ Yıldızlı Ürün Fiyat ve Kâr Simülasyonu")
        st.write("Trendyol'dan indirdiğiniz 'Yıldızlı Ürün Etiketleri' dosyasını yükleyerek 3 Yıldız > 2 Yıldız > 1 Yıldız sırasıyla kârlılığınızı test edin.")
        
        c1, c2 = st.columns(2)
        with c1: y_min_marj = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="y_marj")
        with c2: y_min_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="y_tl")
        
        yildiz_file = st.file_uploader("Trendyol 'Yıldızlı Ürün Etiketleri' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="yildiz_up")
        
        if yildiz_file:
            orijinal_dosya_ismi = yildiz_file.name
            if orijinal_dosya_ismi.endswith('.csv'):
                try: df_yildiz = pd.read_csv(yildiz_file, sep=None, engine='python')
                except: yildiz_file.seek(0); df_yildiz = pd.read_csv(yildiz_file, delimiter=';')
            else:
                df_yildiz = pd.read_excel(yildiz_file)
                
            cols = list(df_yildiz.columns)
            barkod_col = next((c for c in cols if 'BARKOD' in c.upper()), cols[1] if len(cols)>1 else cols[0])
            fiyat_1_yildiz = next((c for c in cols if '1 YILDIZ ÜST FİYAT' in c.upper()), None)
            fiyat_2_yildiz = next((c for c in cols if '2 YILDIZ ÜST FİYAT' in c.upper()), None)
            fiyat_3_yildiz = next((c for c in cols if '3 YILDIZ ÜST FİYAT' in c.upper()), None)
            yeni_fiyat_col = next((c for c in cols if 'YENİ TSF' in c.upper()), None)
            
            if st.button("⚡ Yıldızlı Ürün Fiyatlarını Hesapla", type="primary", use_container_width=True, key="btn_yildiz"):
                if not all([fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz, yeni_fiyat_col]):
                    st.error("❌ Yıldızlı fiyat sütunları bulunamadı. Lütfen doğru dosyayı yüklediğinizden emin olun.")
                else:
                    islem_df = df_yildiz.copy()
                    islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                    db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                    merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                    for col in [fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz]:
                        merge_df[col + '_num'] = merge_df[col].apply(utils.temizle_ve_sayiya_donustur)
                        
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
                            if n_kar >= y_min_tl and k_marji >= y_min_marj:
                                uygun_fiyat, secili_yildiz, net_kar, kar_marji = fiyat, yildiz_isim, n_kar, k_marji; break 
                        secilen_fiyatlar.append(uygun_fiyat); secilen_yildizlar.append(secili_yildiz); hesaplanan_karlar.append(net_kar); hesaplanan_marjlar.append(kar_marji)
                        
                    islem_df['Seçilen Yıldız'] = secilen_yildizlar; islem_df['Net Kâr (TL)'] = hesaplanan_karlar; islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                    islem_df[yeni_fiyat_col] = [str(round(val, 2)).replace('.', ',') if (not pd.isna(val) and val != 0) else "" for val in secilen_fiyatlar]
                    basarili_df = islem_df[islem_df['Seçilen Yıldız'].isin(["1 Yıldız", "2 Yıldız", "3 Yıldız"])].copy()
                    
                    st.success(f"✅ Yıldız Analizi Tamamlandı: {len(basarili_df)} ürüne kârlı yıldız fiyatı atandı!")
                    st.dataframe(utils.tablayi_1den_baslat(basarili_df[[barkod_col, yeni_fiyat_col, 'Seçilen Yıldız', 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        islem_df[cols].to_excel(writer, index=False, sheet_name='Sheet1')
                    output.seek(0)
                    st.download_button("📥 Trendyol İçin Hazır Excel'i İndir (Yıldız)", data=output, file_name=orijinal_dosya_ismi.rsplit('.', 1)[0] + "_Yildiz_Hazir.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_yildiz")

    # -----------------------------------------------------------------
    # SEKME 2: PLUS KOMİSYON TARİFELERİ ANALİZİ
    # -----------------------------------------------------------------
    with tab_plus:
        st.markdown("#### ➕ Plus Komisyon Tarifeleri ve Fiyat Limit Analizi")
        st.write("Trendyol 'Plus Fiyatlandırma' dosyanızı yükleyin. Ürün fiyatınızı Plus limitine çekip indirimli komisyon oranıyla satmanın kârlılığını test edelim.")
        
        pc1, pc2, pc3 = st.columns(3)
        with pc1: p_min_marj = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=30.0, step=1.0, key="p_marj")
        with pc2: p_min_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=75.0, step=1.0, key="p_tl")
        with pc3: tarife_secimi = st.selectbox("🎯 Test Edilecek Tarife Süresi:", ["En Kârlı Tarifeyi Otomatik Seç (3 veya 4 Günlük)", "Sadece 3 Günlük Tarifeyi Test Et", "Sadece 4 Günlük Tarifeyi Test Et"], key="p_tarife")
        
        plus_file = st.file_uploader("Trendyol 'Plus Ürünleri' Excel Dosyasını Yükleyin", type=['xlsx', 'xls', 'csv'], key="plus_up")
        
        if plus_file:
            orijinal_p_ismi = plus_file.name
            if orijinal_p_ismi.endswith('.csv'):
                try: df_plus = pd.read_csv(plus_file, sep=None, engine='python')
                except: plus_file.seek(0); df_plus = pd.read_csv(plus_file, delimiter=';')
                sheet_adi = "TyPlusÜrünleri"
            else:
                xls_obj = pd.ExcelFile(plus_file)
                sheet_adi = xls_obj.sheet_names[0]
                df_plus = pd.read_excel(plus_file, sheet_name=sheet_adi)
                
            cols_plus = list(df_plus.columns)
            barkod_p_col = next((c for c in cols_plus if 'BARKOD' in c.upper()), cols_plus[2] if len(cols_plus)>2 else cols_plus[0])
            
            if st.button("⚡ Plus Tarifelerini Analiz Et ve Excel Üret", type="primary", use_container_width=True, key="btn_plus"):
                islem_p_df = df_plus.copy()
                islem_p_df['_kamp_barkod'] = islem_p_df[barkod_p_col].astype(str).str.strip()
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                merged_p = pd.merge(islem_p_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                
                secilen_fiyatlar_p, secilen_tarifeler_p, durumlar_p, net_karlar_p, marjlar_p = [], [], [], [], []
                
                for idx, row in merged_p.iterrows():
                    if pd.isna(row['_db_barkod']):
                        secilen_fiyatlar_p.append(np.nan); secilen_tarifeler_p.append(np.nan); durumlar_p.append("Sistemde Yok"); net_karlar_p.append(0); marjlar_p.append(0); continue
                        
                    maliyet_toplam = row['Maliyet (TL)'] + row['Kargo (TL)']
                    guncel_fiyat = utils.temizle_ve_sayiya_donustur(row.get('Güncel TSF', 0))
                    guncel_kom = utils.temizle_ve_sayiya_donustur(row.get('Güncel Komisyon', 0)) / 100.0
                    guncel_kar = guncel_fiyat - (maliyet_toplam + (guncel_fiyat * guncel_kom)) if guncel_fiyat > 0 else 0
                    
                    plus_limit = utils.temizle_ve_sayiya_donustur(row.get('Plus Fiyat Üst Limiti', 0))
                    
                    # 3 Günlük Analiz
                    kom_3g = utils.temizle_ve_sayiya_donustur(row.get('Plus Komisyon Teklifi', 0)) / 100.0
                    kar_3g = plus_limit - (maliyet_toplam + (plus_limit * kom_3g)) if plus_limit > 0 else 0
                    marj_3g = (kar_3g / plus_limit * 100.0) if plus_limit > 0 else 0
                    str_3g = str(row.get('3 Gün Tarih Aralığı', '3 Günlük Fiyat')) if pd.notna(row.get('3 Gün Tarih Aralığı')) else '3 Günlük Fiyat'
                    
                    # 4 Günlük Analiz
                    kom_4g = utils.temizle_ve_sayiya_donustur(row.get('Plus Komisyon Teklifi.1', 0)) / 100.0
                    kar_4g = plus_limit - (maliyet_toplam + (plus_limit * kom_4g)) if plus_limit > 0 else 0
                    marj_4g = (kar_4g / plus_limit * 100.0) if plus_limit > 0 else 0
                    str_4g = str(row.get('4 Gün Tarih Aralığı', '4 Günlük Fiyat')) if pd.notna(row.get('4 Gün Tarih Aralığı')) else '4 Günlük Fiyat'
                    
                    best_fiyat, best_tarife = np.nan, np.nan
                    best_kar = guncel_kar
                    best_marj = (guncel_kar / guncel_fiyat * 100.0) if guncel_fiyat > 0 else 0
                    durum = "Standartta Kal"
                    
                    uygun_3g = (kar_3g >= p_min_tl) and (marj_3g >= p_min_marj)
                    uygun_4g = (kar_4g >= p_min_tl) and (marj_4g >= p_min_marj)
                    
                    if "3 Günlük" in tarife_secimi and uygun_3g:
                        best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_3g, kar_3g, marj_3g, "✅ 3 Günlük Plus Seçildi"
                    elif "4 Günlük" in tarife_secimi and uygun_4g:
                        best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_4g, kar_4g, marj_4g, "✅ 4 Günlük Plus Seçildi"
                    elif "Otomatik" in tarife_secimi:
                        if uygun_3g and uygun_4g:
                            if kar_4g >= kar_3g:
                                best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_4g, kar_4g, marj_4g, "✅ 4 Günlük Plus Seçildi"
                            else:
                                best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_3g, kar_3g, marj_3g, "✅ 3 Günlük Plus Seçildi"
                        elif uygun_4g:
                            best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_4g, kar_4g, marj_4g, "✅ 4 Günlük Plus Seçildi"
                        elif uygun_3g:
                            best_fiyat, best_tarife, best_kar, best_marj, durum = plus_limit, str_3g, kar_3g, marj_3g, "✅ 3 Günlük Plus Seçildi"
                            
                    secilen_fiyatlar_p.append(best_fiyat)
                    secilen_tarifeler_p.append(best_tarife)
                    durumlar_p.append(durum)
                    net_karlar_p.append(best_kar)
                    marjlar_p.append(best_marj)
                    
                islem_p_df['Analiz Durumu'] = durumlar_p
                islem_p_df['Net Kâr (TL)'] = net_karlar_p
                islem_p_df['Kâr Marjı (%)'] = marjlar_p
                
                # Orijinal sütunlara formatlı olarak aktar (Trendyol şablonuna 100% uyum)
                if 'Plus Fiyat Seçimi' in cols_plus:
                    islem_p_df['Plus Fiyat Seçimi'] = [val if pd.notna(val) else "" for val in secilen_fiyatlar_p]
                if 'Tarife Seçimi' in cols_plus:
                    islem_p_df['Tarife Seçimi'] = [val if pd.notna(val) else "" for val in secilen_tarifeler_p]
                    
                basarili_p_df = islem_p_df[islem_p_df['Analiz Durumu'].str.contains("Seçildi")].copy()
                st.success(f"✅ Plus Analizi Tamamlandı: Toplam {len(islem_p_df)} üründen {len(basarili_p_df)} tanesi Plus tarifeleri için kârlı bulundu!")
                
                st.dataframe(utils.tablayi_1den_baslat(islem_p_df[[barkod_p_col, 'Ürün İsmi', 'Güncel TSF', 'Plus Fiyat Üst Limiti', 'Analiz Durumu', 'Net Kâr (TL)', 'Kâr Marjı (%)']]).style.format({'Güncel TSF': '{:.2f} TL', 'Plus Fiyat Üst Limiti': '{:.2f} TL', 'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                
                output_p = BytesIO()
                with pd.ExcelWriter(output_p, engine='openpyxl') as writer:
                    islem_p_df[cols_plus].to_excel(writer, index=False, sheet_name=sheet_adi)
                output_p.seek(0)
                st.download_button("📥 Trendyol Plus İçin Hazır Excel'i İndir", data=output_p, file_name=orijinal_p_ismi.rsplit('.', 1)[0] + "_Plus_Hazir.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="dl_plus")
