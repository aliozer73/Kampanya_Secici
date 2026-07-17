import streamlit as st
import pandas as pd
import numpy as np
import utils

def render():
    st.markdown('<div class="section-title">📦 Ürün Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm kampanya ve satış analizlerinde ortak kullanılacak olan ürün maliyet, kargo ve komisyon listeniz.</div>', unsafe_allow_html=True)
    
    mevcut_db = utils.load_db()
    
    # Üst Bölüm: Tekil Ekleme veya Toplu Dosya Yükleme Sekmeleri
    tab_tekli, tab_toplu = st.tabs(["➕ Tekil Ürün Ekle", "📂 Excel / CSV ile Toplu Yükle"])
    
    with tab_tekli:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        with st.form("tekil_ekle_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 2, 1])
            with c1:
                yeni_barkod = st.text_input("Barkod / SKU *", placeholder="Örn: TR-890123")
                yeni_kargo = st.number_input("Kargo Gideri (TL)", min_value=0.0, value=45.0, step=5.0, format="%.2f")
            with c2:
                yeni_ad = st.text_input("Ürün Adı", placeholder="Örn: Altın Kaplama Kolye")
                yeni_komisyon = st.number_input("Pazaryeri Komisyonu (%)", min_value=0.0, max_value=100.0, value=18.0, step=1.0, format="%.2f")
            with c3:
                yeni_maliyet = st.number_input("Maliyet (TL) *", min_value=0.0, value=100.0, step=5.0, format="%.2f")
                st.write("") # Boşluk hizalaması
                submit_tekil = st.form_submit_button("➕ Listeye Ekle", use_container_width=True)
                
            if submit_tekil:
                barkod_temiz = str(yeni_barkod).strip()
                if not barkod_temiz or barkod_temiz == 'nan':
                    st.error("❌ Barkod alanı zorunludur!")
                else:
                    yeni_satir = pd.DataFrame([{
                        'Barkod': barkod_temiz,
                        'Ürün Adı': str(yeni_ad).strip(),
                        'Maliyet (TL)': float(yeni_maliyet),
                        'Kargo (TL)': float(yeni_kargo),
                        'Komisyon (%)': float(yeni_komisyon)
                    }])
                    # Eğer barkod zaten varsa güncelle, yoksa ekle
                    if not mevcut_db.empty and barkod_temiz in mevcut_db['Barkod'].astype(str).values:
                        idx = mevcut_db[mevcut_db['Barkod'].astype(str) == barkod_temiz].index[0]
                        mevcut_db.loc[idx] = yeni_satir.iloc[0]
                        st.success(f"🔄 `{barkod_temiz}` barkodlu ürün başarıyla güncellendi!")
                    else:
                        mevcut_db = pd.concat([yeni_satir, mevcut_db], ignore_index=True)
                        st.success(f"✅ `{barkod_temiz}` listeye eklendi!")
                    mevcut_db.to_csv(utils.DB_FILE, index=False)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

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
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                with sc1: b_col = st.selectbox("Barkod Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku"]))
                with sc2: a_col = st.selectbox("Ürün Adı Sütunu", cols, index=utils.find_default_col(cols, ["ad", "name", "ürün"]))
                with sc3: m_col = st.selectbox("Maliyet Sütunu", cols, index=utils.find_default_col(cols, ["maliyet", "cost", "alış"]))
                with sc4: k_col = st.selectbox("Kargo Sütunu", cols, index=utils.find_default_col(cols, ["kargo", "shipping"]))
                with sc5: kom_col = st.selectbox("Komisyon Sütunu", cols, index=utils.find_default_col(cols, ["komisyon", "commission"]))
                
                islemi_sec = st.radio("Aktarım Yöntemi:", [
                    "🔄 Mevcut listeyle birleştir (Aynı barkodları güncelle, yenileri ekle)",
                    "⚠️ Mevcut listeyi sil ve tamamen bu dosyayı yükle"
                ], horizontal=True)
                
                if st.button("🚀 Dosyadaki Ürünleri Veritabanına Aktar", type="primary", use_container_width=True):
                    yeni_liste = []
                    for _, row in df_yuklenen.iterrows():
                        brk = str(row[b_col]).strip() if pd.notna(row[b_col]) else ""
                        if not brk or brk == 'nan': continue
                        yeni_liste.append({
                            'Barkod': brk,
                            'Ürün Adı': str(row[a_col]).strip() if pd.notna(row[a_col]) else "",
                            'Maliyet (TL)': utils.temizle_ve_sayiya_donustur(row[m_col]),
                            'Kargo (TL)': utils.temizle_ve_sayiya_donustur(row[k_col]),
                            'Komisyon (%)': utils.temizle_ve_sayiya_donustur(row[kom_col])
                        })
                    
                    df_yeni_aktarim = pd.DataFrame(yeni_liste)
                    
                    if "sil ve tamamen" in islemi_sec:
                        son_db = df_yeni_aktarim
                    else:
                        if not mevcut_db.empty:
                            # Aynı barkodları yeni listeden gelenlerle ez
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

    st.markdown("---")
    st.markdown("### 📋 Mevcut Ürün Listesi ve Anlık Düzenleme")
    
    if mevcut_db.empty:
        st.info("💡 Sistemde henüz kayıtlı ürün bulunmuyor. Yukarıdaki sekmelerden ürün ekleyebilir veya aşağıdaki tablodan yazmaya başlayabilirsiniz.")
        ornek_veri = pd.DataFrame({'Barkod': ['ORNEK_BARKOD_1'], 'Ürün Adı': ['Örnek Ürün'], 'Maliyet (TL)': [100.0], 'Kargo (TL)': [45.0], 'Komisyon (%)': [15.0]})
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        
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
    if st.button("💾 Tablodaki Değişiklikleri Veritabanına Kaydet", use_container_width=True):
        df_save = edited_df.reset_index(drop=True)
        df_save['Barkod'] = df_save['Barkod'].astype(str).str.strip()
        df_save = df_save[df_save['Barkod'] != '']; df_save = df_save[df_save['Barkod'] != 'nan']
        df_save.to_csv(utils.DB_FILE, index=False)
        st.success("✅ Ürün veritabanınız başarıyla güncellendi!")
