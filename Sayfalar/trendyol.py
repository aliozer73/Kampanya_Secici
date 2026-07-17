import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO  # <-- EKSİK OLAN SATIR BU
import utils

def render():
    st.markdown('<div class="section-title">🚀 Trendyol Plus & Yıldızlı Ürün Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Trendyol\'dan indirdiğiniz "Plus Fiyatlandırma" veya "Yıldızlı Ürün" dosyasını yükleyin. Standart vs Plus komisyon kârlılığını kıyaslayalım.</div>', unsafe_allow_html=True)
    
    db = utils.load_db()
    if db.empty: st.error("❌ Lütfen önce Maliyet Yönetimi sayfasından ürün ekleyin."); return
        
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0)
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=50.0, step=1.0)
    
    kampanya_file = st.file_uploader("Trendyol Excel Dosyasını Yükleyin", type=['xlsx', 'csv'])
    
    if kampanya_file:
        df = pd.read_excel(kampanya_file) if not kampanya_file.name.endswith('.csv') else pd.read_csv(kampanya_file, sep=None, engine='python')
        
        if st.button("⚡ Plus vs Standart Analizini Çalıştır", type="primary", use_container_width=True):
            # Verileri eşle
            db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
            df['_file_barkod'] = df['Barkod'].astype(str).str.strip()
            merge_df = pd.merge(df, db, left_on='_file_barkod', right_on='_db_barkod', how='left')
            
            sonuclar = []
            for _, row in merge_df.iterrows():
                if pd.isna(row['_db_barkod']): continue
                
                maliyet = row['Maliyet (TL)'] + row['Kargo (TL)']
                # Standart Analiz
                standart_fiyat = row['Güncel TSF']
                std_kom_orani = row['Güncel Komisyon'] / 100
                std_net_kar = standart_fiyat - (maliyet + (standart_fiyat * std_kom_orani))
                
                # Plus Analiz
                plus_limit = row.get('Plus Fiyat Üst Limiti', 0)
                plus_kom_orani = row.get('Plus Komisyon Teklifi', 0) / 100
                plus_net_kar = plus_limit - (maliyet + (plus_limit * plus_kom_orani))
                
                # Karar Mekanizması
                durum = "Standartta Kal"
                secilen_fiyat = standart_fiyat
                kullanilan_kar = std_net_kar
                
                if plus_net_kar >= min_net_kar_tl and (plus_net_kar / plus_limit) >= (min_kar_marji / 100):
                    durum = "Plus Fiyata Geç"
                    secilen_fiyat = plus_limit
                    kullanilan_kar = plus_net_kar
                
                sonuclar.append({
                    'Barkod': row['_file_barkod'],
                    'Ürün İsmi': row['Ürün İsmi'],
                    'Önerilen Aksiyon': durum,
                    'Yeni Fiyat': secilen_fiyat,
                    'Net Kâr (TL)': kullanilan_kar
                })
            
            res_df = pd.DataFrame(sonuclar)
            st.dataframe(res_df.style.format({'Yeni Fiyat': '{:.2f} TL', 'Net Kâr (TL)': '{:.2f} TL'}), use_container_width=True)
            
            # Excel İndirme
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer: res_df.to_excel(writer, index=False)
            st.download_button("📥 Analiz Sonucunu İndir", data=output.getvalue(), file_name="Plus_Analiz_Sonuc.xlsx")
