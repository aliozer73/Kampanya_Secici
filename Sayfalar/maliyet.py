import streamlit as st
import pandas as pd
import utils

def render():
    st.markdown('<div class="section-title">📦 Ürün Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm kampanya ve satış analizlerinde ortak kullanılacak olan ürün maliyet, kargo ve komisyon listeniz.</div>', unsafe_allow_html=True)
    
    mevcut_db = utils.load_db()
    if mevcut_db.empty:
        ornek_veri = pd.DataFrame({'Barkod': ['ORNEK_BARKOD_1'], 'Ürün Adı': ['Örnek Ürün'], 'Maliyet (TL)': [100.0], 'Kargo (TL)': [45.0], 'Komisyon (%)': [15.0]})
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        st.info("💡 Sistemde henüz ürün bulunmuyor. Örnek satırın üzerine tıklayarak kendi barkod ve maliyetlerinizi yazmaya başlayabilirsiniz.")
        
    edited_df = st.data_editor(
        utils.tablayi_1den_baslat(mevcut_db), num_rows="dynamic", use_container_width=True,
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
        df_save.to_csv(utils.DB_FILE, index=False)
        st.success("✅ Ürün veritabanınız başarıyla güncellendi!")
