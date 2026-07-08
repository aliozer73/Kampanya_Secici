import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Sayfa yapılandırması
st.set_page_config(
    page_title="Avantajlı Ürün Fiyatlandırma",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS - Temiz ve Profesyonel Tarz
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #E74C3C; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .sub-title { font-size: 15px; color: #2E4053; margin-bottom: 25px; }
    .metric-box { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #2ECC71; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .hb-title { font-size: 32px; font-weight: bold; color: #FF6700; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .hb-metric { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #FF6700; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { background-color: #2ECC71; color: white; border-radius: 8px; border: none; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { background-color: #27AE60; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(46, 204, 113, 0.4); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f3f5; border-radius: 4px 4px 0 0; padding: 10px 20px; font-weight: 600; color: #495057; }
    .stTabs [aria-selected="true"] { background-color: #2ECC71 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Veritabanı dosya yolu
DB_FILE = 'urun_maliyet_veritabani.csv'

def temizle_ve_sayiya_donustur(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).strip()
    if not val_str: return 0.0
    
    # Hepsiburada/Trendyol format farklılıklarını güvenli çözümleme
    if '.' in val_str and ',' in val_str:
        if val_str.rfind('.') > val_str.rfind(','):
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try: return float(val_str)
    except ValueError: return 0.0

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Barkod': str})
    return pd.DataFrame(columns=['Barkod', 'Ürün Adı', 'Maliyet (TL)', 'Kargo (TL)', 'Komisyon (%)'])

# Otomatik sütun bulucu fonksiyon
def find_default_col(options, keywords, exclude_keywords=None):
    if exclude_keywords is None:
        exclude_keywords = []
    for opt in options:
        opt_lower = str(opt).lower()
        if any(kw in opt_lower for kw in keywords) and not any(ex_kw in opt_lower for ex_kw in exclude_keywords):
            return options.index(opt)
    return 0

# --- YAN MENÜ ---
st.sidebar.markdown("<h2 style='text-align: center; color: #E74C3C;'>🏷️ Avantajlı Ürün</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #2ECC71; font-weight: bold;'>Fiyatlandırma Sistemi</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Sayfa Seçimi:", ["📦 Maliyet Yönetimi", "🚀 Trendyol Yıldızlı Fiyat", "💜 Hepsiburada Avantajlı Teklif"])
st.sidebar.markdown("---")

# ==========================================
# SAYFA 1: MALİYET VERİTABANI YÖNETİMİ
# ==========================================
if menu == "📦 Maliyet Yönetimi":
    st.markdown('<div class="main-title">📦 Ortak Veritabanı Yönetimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Trendyol ve Hepsiburada hesaplamaları için ürün maliyetlerinizi, kargo ve komisyon oranlarınızı buradan düzenleyin.</div>', unsafe_allow_html=True)
    
    mevcut_db = load_db()
    
    if mevcut_db.empty:
        ornek_veri = pd.DataFrame({
            'Barkod': ['ORNEK_BARKOD_1'],
            'Ürün Adı': ['Örnek Ürün'],
            'Maliyet (TL)': [100.0],
            'Kargo (TL)': [45.0],
            'Komisyon (%)': [15.0]
        })
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        st.info("Sistemde ürün yok. Örnek satırın üzerine tıklayarak kendi ürünlerinizi girmeye başlayabilirsiniz.")
        
    edited_df = st.data_editor(
        mevcut_db,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Barkod": st.column_config.TextColumn("Barkod / SKU", required=True),
            "Ürün Adı": st.column_config.TextColumn("Ürün Adı"),
            "Maliyet (TL)": st.column_config.NumberColumn("Maliyet (TL)", min_value=0.0, format="%.2f"),
            "Kargo (TL)": st.column_config.NumberColumn("Kargo (TL)", min_value=0.0, format="%.2f"),
            "Komisyon (%)": st.column_config.NumberColumn("Komisyon (%)", min_value=0.0, max_value=100.0, format="%.2f"),
        },
        height=500
    )
    
    if st.button("💾 Değişiklikleri Sisteme Kaydet", use_container_width=True):
        edited_df['Barkod'] = edited_df['Barkod'].astype(str).str.strip()
        edited_df = edited_df[edited_df['Barkod'] != '']
        edited_df = edited_df[edited_df['Barkod'] != 'nan']
        edited_df.to_csv(DB_FILE, index=False)
        st.success("✅ Veritabanı başarıyla güncellendi!")

# ==========================================
# SAYFA 2: TRENDYOL KAMPANYA ANALİZİ
# ==========================================
elif menu == "🚀 Trendyol Yıldızlı Fiyat":
    st.markdown('<div class="main-title">📈 Trendyol Yıldızlı Ürün Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Trendyol\'dan indirdiğiniz "Yıldızlı Ürün Etiketleri" dosyasını yükleyin. Sistem 3 Yıldız > 2 Yıldız > 1 Yıldız sırasıyla kârı test eder.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty:
        st.error("❌ Lütfen önce sol menüden ürün maliyetlerinizi girin!")
        st.stop()
        
    st.markdown("### 🎯 Kârlılık Kriterleri")
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="ty_marj")
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="ty_tl")
    st.markdown("---")
    
    kampanya_file = st.file_uploader("Trendyol 'Yıldızlı Ürün Etiketleri' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="ty_file")
    
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        
        if orijinal_dosya_ismi.endswith('.csv'):
            try:
                df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except:
                kampanya_file.seek(0)
                df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else:
            df_kampanya = pd.read_excel(kampanya_file)
            
        cols = list(df_kampanya.columns)
        
        barkod_col = next((c for c in cols if 'BARKOD' in c.upper()), cols[1] if len(cols)>1 else cols[0])
        fiyat_1_yildiz = next((c for c in cols if '1 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_2_yildiz = next((c for c in cols if '2 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_3_yildiz = next((c for c in cols if '3 YILDIZ ÜST FİYAT' in c.upper()), None)
        yeni_fiyat_col = next((c for c in cols if 'YENİ TSF' in c.upper()), None)
        
        if st.button("⚡ Otomatik Fiyatlandır (Trendyol)", use_container_width=True):
            if not all([fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz, yeni_fiyat_col]):
                st.error("❌ Yüklediğiniz dosyada Yıldızlı Fiyat sütunları bulunamadı. Doğru şablonu yüklediğinizden emin olun.")
            else:
                with st.spinner("⏳ Fiyatlandırma senaryoları test ediliyor..."):
                    
                    islem_df = df_kampanya.copy()
                    islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                    
                    db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                    merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                    
                    for col in [fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz]:
                        merge_df[col + '_num'] = merge_df[col].apply(temizle_ve_sayiya_donustur)
                        
                    secilen_fiyatlar, secilen_yildizlar, hesaplanan_karlar, hesaplanan_marjlar = [], [], [], []
                    test_siralamasi = [("3 Yıldız", fiyat_3_yildiz+'_num'), ("2 Yıldız", fiyat_2_yildiz+'_num'), ("1 Yıldız", fiyat_1_yildiz+'_num')]
                    
                    for idx, row in merge_df.iterrows():
                        if pd.isna(row['_db_barkod']):
                            secilen_fiyatlar.append(np.nan)
                            secilen_yildizlar.append("Sistemde Yok")
                            hesaplanan_karlar.append(0)
                            hesaplanan_marjlar.append(0)
                            continue
                            
                        maliyet, kargo, kom_orani = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                        uygun_fiyat, secili_yildiz, net_kar, kar_marji = np.nan, "Elenmiş", 0, 0
                        
                        for yildiz_isim, f_col in test_siralamasi:
                            fiyat = row[f_col]
                            if fiyat <= 0: continue
                            komisyon_tl = fiyat * (kom_orani / 100)
                            n_kar = fiyat - (maliyet + kargo + komisyon_tl)
                            k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                            
                            if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                                uygun_fiyat, secili_yildiz, net_kar, kar_marji = fiyat, yildiz_isim, n_kar, k_marji
                                break 
                                
                        secilen_fiyatlar.append(uygun_fiyat)
                        secilen_yildizlar.append(secili_yildiz)
                        hesaplanan_karlar.append(net_kar)
                        hesaplanan_marjlar.append(kar_marji)
                        
                    islem_df['Seçilen Yıldız'] = secilen_yildizlar
                    islem_df['Net Kâr (TL)'] = hesaplanan_karlar
                    islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                    
                    def format_fiyat(val):
                        if pd.isna(val) or val == 0: return ""
                        return str(round(val, 2)).replace('.', ',')
                        
                    islem_df[yeni_fiyat_col] = [format_fiyat(f) for f in secilen_fiyatlar]
                    
                    basarili_df = islem_df[islem_df['Seçilen Yıldız'].isin(["1 Yıldız", "2 Yıldız", "3 Yıldız"])].copy()
                    elenen_df = islem_df[islem_df['Seçilen Yıldız'] == "Elenmiş"].copy()
                    db_yok_df = islem_df[islem_df['Seçilen Yıldız'] == "Sistemde Yok"].copy()
                    
                    st.markdown("### 📊 Analiz Özeti")
                    m1, m2, m3, m4 = st.columns(4)
                    with m1: st.markdown(f'<div class="metric-box" style="border-color:#3498DB;"><b>İncelenen Ürün:</b><br><span style="font-size:24px; font-weight:bold;">{len(islem_df)}</span></div>', unsafe_allow_html=True)
                    with m2: st.markdown(f'<div class="metric-box" style="border-color:#2ECC71;"><b>Fiyat Atanan:</b><br><span style="font-size:24px; font-weight:bold; color:#2ECC71;">{len(basarili_df)}</span></div>', unsafe_allow_html=True)
                    with m3: st.markdown(f'<div class="metric-box" style="border-color:#E74C3C;"><b>Zarar Sebebiyle Elenen:</b><br><span style="font-size:24px; font-weight:bold; color:#E74C3C;">{len(elenen_df)}</span></div>', unsafe_allow_html=True)
                    with m4: st.markdown(f'<div class="metric-box" style="border-color:#F39C12;"><b>Maliyeti Girilmeyen:</b><br><span style="font-size:24px; font-weight:bold; color:#F39C12;">{len(db_yok_df)}</span></div>', unsafe_allow_html=True)
                    
                    st.write("#### 🎯 Fiyat Ataması Yapılan Ürünler (Önizleme)")
                    if len(basarili_df) > 0:
                        orijinal_fiyat_col = next((c for c in cols if 'TRENDYOL SATIŞ FİYATI' in c.upper() or 'SATIŞ FİYATI' in c.upper()), None)
                        goster_cols = [barkod_col]
                        if orijinal_fiyat_col: goster_cols.append(orijinal_fiyat_col)
                        goster_cols.extend([yeni_fiyat_col, 'Seçilen Yıldız', 'Net Kâr (TL)', 'Kâr Marjı (%)'])
                        st.dataframe(basarili_df[goster_cols].style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                    else:
                        st.warning("Hiçbir ürün kriterleri karşılamadı.")
                    
                    output = BytesIO()
                    export_df = islem_df[cols].copy() 
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='Sheet1')
                        workbook = writer.book
                        worksheet = workbook.active
                        header_fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid")
                        header_font = Font(bold=True, color="FFFFFF")
                        p_col_idx = export_df.columns.get_loc(yeni_fiyat_col) + 1
                        
                        for col_idx, col_name in enumerate(export_df.columns, 1):
                            cell = worksheet.cell(row=1, column=col_idx)
                            cell.fill = header_fill
                            cell.font = header_font
                            if col_idx == p_col_idx: cell.fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
                        for col in worksheet.columns:
                            worksheet.column_dimensions[get_column_letter(col[0].column)].width = 15
                            
                    output.seek(0)
                    st.success("✅ Excel dosyanız yüklendiği orijinal isimle indirilmeye hazır!")
                    st.download_button(label="📥 Trendyol İçin Hazır Excel'i İndir", data=output, file_name=orijinal_dosya_ismi.rsplit('.', 1)[0] + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


# ==========================================
# SAYFA 3: HEPSİBURADA KAMPANYA ANALİZİ
# ==========================================
elif menu == "💜 Hepsiburada Avantajlı Teklif":
    st.markdown('<div class="hb-title">💜 Hepsiburada Kampanya Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Hepsiburada\'dan indirdiğiniz "Listelerim" dosyasını yükleyin. Sepet kampanyaları veya standart fiyat kampanyaları için uygun kârlılığı otomatik hesaplar.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty:
        st.error("❌ Lütfen önce sol menüden ürün maliyetlerinizi girin!")
        st.stop()
        
    st.markdown("### 🎯 Kârlılık Kriterleri")
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="hb_marj")
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="hb_tl")
    st.markdown("---")
    
    kampanya_file = st.file_uploader("Hepsiburada 'Listelerim' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="hb_file")
    
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        
        if orijinal_dosya_ismi.endswith('.csv'):
            try:
                df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except:
                kampanya_file.seek(0)
                df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else:
            df_kampanya = pd.read_excel(kampanya_file)
            
        cols = list(df_kampanya.columns)
        
        st.write("#### ⚙️ Sütun Eşleştirme (Hepsiburada Formatı İçin)")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            barkod_col = st.selectbox("Barkod / SKU Sütunu", cols, index=find_default_col(cols, ["barkod", "barcode", "sku", "stok", "merchant"]))
        with col2:
            eski_fiyat_col = st.selectbox("Mevcut Satış Fiyatı", cols, index=find_default_col(cols, ["satış", "satis", "psf"], exclude_keywords=["kampanya", "teklif", "max"]))
        with col3:
            # Kullanıcının "Standart Kampanya" olarak elden girmesini veya sepette indirim sonrası kârlılığı kontrol etmesini sağla
            is_normal_campaign = st.checkbox("🎯 Standart Kampanya (HB'nin Maksimum Fiyat Kuralına Göre Katılım)")
            if not is_normal_campaign:
                sepet_indirimi = st.number_input("🛒 Kampanyanın İstediği İndirim Oranı (%) (Örn: Sepette %15 İndirim için 15 yazın)", min_value=1.0, max_value=99.0, value=15.0, step=1.0)
            else:
                sepet_indirimi = 0.0
        with col4:
            # Excell'de boş olan ama yüklenmesi gereken sütun
            kampanya_fiyat_col = st.selectbox("Hepsiburada Paneline Yüklenecek Fiyat (Boş Sütun)", cols, index=find_default_col(cols, ["uygulanacağı", "kampanya", "önerilen", "teklif", "avantajlı"], exclude_keywords=["durum"]))
        
        if st.button("⚡ Otomatik Fiyatlandır (Hepsiburada)", use_container_width=True):
            with st.spinner("⏳ Hepsiburada teklifleri kârlılık testinden geçiriliyor..."):
                
                islem_df = df_kampanya.copy()
                islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                
                durum_list, hesaplanan_karlar, hesaplanan_marjlar, katilim_fiyati = [], [], [], []
                
                for idx, row in merge_df.iterrows():
                    if pd.isna(row['_db_barkod']):
                        durum_list.append("Sistemde Yok")
                        hesaplanan_karlar.append(0)
                        hesaplanan_marjlar.append(0)
                        katilim_fiyati.append(np.nan)
                        continue
                        
                    maliyet, kargo, kom_orani = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                    fiyat = temizle_ve_sayiya_donustur(row[eski_fiyat_col])
                    
                    if sepet_indirimi > 0:
                        # Sepet indirimini fiyattan düşüyoruz
                        fiyat = fiyat * (1 - (sepet_indirimi / 100))
                    
                    if fiyat <= 0:
                        durum_list.append("Elenmiş")
                        hesaplanan_karlar.append(0)
                        hesaplanan_marjlar.append(0)
                        katilim_fiyati.append(np.nan)
                        continue
                        
                    komisyon_tl = fiyat * (kom_orani / 100)
                    n_kar = fiyat - (maliyet + kargo + komisyon_tl)
                    k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                    
                    if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                        durum_list.append("Kabul Edildi")
                        hesaplanan_karlar.append(n_kar)
                        hesaplanan_marjlar.append(k_marji)
                        # Kullanıcı Standart Kampanya seçmişse HB paneline yüklenecek Excell'de fiyatı boş bırak.
                        katilim_fiyati.append(np.nan if is_normal_campaign else fiyat)
                    else:
                        durum_list.append("Elenmiş")
                        hesaplanan_karlar.append(n_kar)
                        hesaplanan_marjlar.append(k_marji)
                        katilim_fiyati.append(np.nan)
                        
                islem_df['Kampanya Durumu'] = durum_list
                islem_df['Net Kâr (TL)'] = hesaplanan_karlar
                islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                
                # Sadece kabul edilenler için formata uygun string fiyat yazılımı (Standart kampanyada boştur)
                def hb_format(val):
                    if pd.isna(val) or val == 0: return ""
                    return str(round(val, 2)).replace('.', ',')
                    
                islem_df[kampanya_fiyat_col] = [hb_format(f) for f in katilim_fiyati]
                
                basarili_df = islem_df[islem_df['Kampanya Durumu'] == "Kabul Edildi"].copy()
                elenen_df = islem_df[islem_df['Kampanya Durumu'] == "Elenmiş"].copy()
                db_yok_df = islem_df[islem_df['Kampanya Durumu'] == "Sistemde Yok"].copy()
                
                st.markdown("### 📊 Hepsiburada Analiz Özeti")
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f'<div class="hb-metric" style="border-color:#3498DB;"><b>İncelenen Ürün:</b><br><span style="font-size:24px; font-weight:bold;">{len(islem_df)}</span></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="hb-metric" style="border-color:#2ECC71;"><b>Teklifi Uygun Olan:</b><br><span style="font-size:24px; font-weight:bold; color:#2ECC71;">{len(basarili_df)}</span></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="hb-metric" style="border-color:#E74C3C;"><b>Zarar/Düşük Kâr:</b><br><span style="font-size:24px; font-weight:bold; color:#E74C3C;">{len(elenen_df)}</span></div>', unsafe_allow_html=True)
                with m4: st.markdown(f'<div class="hb-metric" style="border-color:#F39C12;"><b>Maliyeti Girilmeyen:</b><br><span style="font-size:24px; font-weight:bold; color:#F39C12;">{len(db_yok_df)}</span></div>', unsafe_allow_html=True)
                
                st.write("#### 🎯 Hepsiburada Kampanyasına Katılacak Ürünler")
                if len(basarili_df) > 0:
                    st.dataframe(basarili_df[[barkod_col, eski_fiyat_col, 'Net Kâr (TL)', 'Kâr Marjı (%)']].style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                else:
                    st.warning("Hedef kâr marjınızı karşılayan hiçbir HB teklifi bulunamadı.")
                
                output = BytesIO()
                export_df = islem_df[cols].copy() 
                
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # HB sistemine sadece kabul edilenleri temiz Excel'de veriyoruz
                    if len(basarili_df) > 0:
                        basarili_df[cols].to_excel(writer, index=False, sheet_name='Uygun Teklifler')
                    
                    # Tüm analiz geçmişi ayrı sekmede
                    islem_df[cols + ['Kampanya Durumu', 'Net Kâr (TL)', 'Kâr Marjı (%)']].to_excel(writer, index=False, sheet_name='Tüm Analiz Sonucu')
                    
                    workbook = writer.book
                    for sheetname in workbook.sheetnames:
                        worksheet = workbook[sheetname]
                        header_fill = PatternFill(start_color="FF6700", end_color="FF6700", fill_type="solid") # HB Turuncu
                        header_font = Font(bold=True, color="FFFFFF")
                        
                        # Uygun teklifler sekmesinde hedef sütunu farklı renk yap
                        if sheetname == 'Uygun Teklifler':
                            h_col_idx = export_df.columns.get_loc(kampanya_fiyat_col) + 1
                            for col_idx, col_name in enumerate(worksheet[1], 1):
                                col_name.fill = header_fill
                                col_name.font = header_font
                                if col_idx == h_col_idx and sepet_indirimi > 0:
                                    col_name.fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid") # Yeşil vurgu
                        else:
                            for col_idx, col_name in enumerate(worksheet[1], 1):
                                col_name.fill = header_fill
                                col_name.font = header_font
                                
                        for col in worksheet.columns:
                            worksheet.column_dimensions[get_column_letter(col[0].column)].width = 15
                            
                output.seek(0)
                st.success("✅ Hepsiburada dosyanız hazır! İndirdiğiniz dosyadaki 'Uygun Teklifler' sekmesini doğrudan panelinize yükleyebilirsiniz.")
                st.download_button(label="📥 Hepsiburada İçin Hazır Excel'i İndir", data=output, file_name="HB_Kampanya_Sonucu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
