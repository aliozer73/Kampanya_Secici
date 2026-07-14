import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Sayfa yapılandırması
st.set_page_config(
    page_title="Avantajlı Ürün & Satış Analizi Sistemi",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS - Temiz ve Profesyonel Tarz
st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #E74C3C; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .sub-title { font-size: 14px; color: #2E4053; margin-bottom: 25px; }
    .metric-box { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #2ECC71; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .hb-title { font-size: 30px; font-weight: bold; color: #FF6700; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .hb-metric { background-color: #fcfdfc; padding: 15px; border-radius: 10px; border-left: 6px solid #FF6700; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .sales-title { font-size: 30px; font-weight: bold; color: #2980B9; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .sales-metric { background-color: #f8fbfe; padding: 15px; border-radius: 10px; border-left: 6px solid #2980B9; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .highlight-card { background: linear-gradient(135deg, #f6f9fc 0%, #edf2f7 100%); padding: 15px; border-radius: 10px; border: 1px solid #cbd5e0; text-align: center; }
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
st.sidebar.markdown("<h2 style='text-align: center; color: #E74C3C;'>📈 E-Ticaret Yönetimi</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #2ECC71; font-weight: bold;'>Fiyatlandırma & Satış Analizi</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Sayfa Seçimi:", [
    "📦 Maliyet Yönetimi", 
    "🚀 Trendyol Yıldızlı Fiyat", 
    "💜 Hepsiburada Avantajlı Teklif",
    "📊 Trendyol Satış Analizi"
])
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
            try: df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except: kampanya_file.seek(0); df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else: df_kampanya = pd.read_excel(kampanya_file)
            
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
                    else: st.warning("Hiçbir ürün kriterleri karşılamadı.")
                    
                    output = BytesIO(); export_df = islem_df[cols].copy() 
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='Sheet1'); workbook = writer.book; worksheet = workbook.active
                        header_fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid"); header_font = Font(bold=True, color="FFFFFF")
                        p_col_idx = export_df.columns.get_loc(yeni_fiyat_col) + 1
                        for col_idx, col_name in enumerate(export_df.columns, 1):
                            cell = worksheet.cell(row=1, column=col_idx); cell.fill = header_fill; cell.font = header_font
                            if col_idx == p_col_idx: cell.fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
                        for col in worksheet.columns: worksheet.column_dimensions[get_column_letter(col[0].column)].width = 15
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
    if db.empty: st.error("❌ Lütfen önce sol menüden ürün maliyetlerinizi girin!"); st.stop()
        
    kampanya_tipi = st.radio("Kampanya Formatı:", ["🛒 Sepette % İndirim Kampanyası (Belirlediğiniz oranda indirimli fiyatı hedefler)", "🎯 Standart Kampanya (HB'nin Maksimum Fiyat Kuralına Göre Katılım)"])
    sepet_indirimi = st.number_input("🛒 Kampanyanın İstediği İndirim Oranı (%) (Örn: Sepette %15 İndirim için 15 yazın)", min_value=1.0, max_value=99.0, value=15.0, step=1.0) if "Sepette" in kampanya_tipi else 0.0

    st.markdown("### 🎯 Kârlılık Kriterleri")
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=35.0, step=1.0, key="hb_marj")
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=100.0, step=1.0, key="hb_tl")
    st.markdown("---")
    
    kampanya_file = st.file_uploader("Hepsiburada 'Listelerim' Dosyasını Yükleyin", type=['xlsx', 'csv'], key="hb_file")
    
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        if orijinal_dosya_ismi.endswith('.csv'):
            try: df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except: kampanya_file.seek(0); df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else: df_kampanya = pd.read_excel(kampanya_file)
            
        cols = list(df_kampanya.columns)
        st.write("#### ⚙️ Sütun Eşleştirme (Hepsiburada Formatı İçin)")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: barkod_col = st.selectbox("Barkod / SKU Sütunu", cols, index=find_default_col(cols, ["barkod", "barcode", "sku", "stok", "merchant"]))
        with col2: eski_fiyat_col = st.selectbox("Mevcut Satış Fiyatı", cols, index=find_default_col(cols, ["satış", "satis", "psf"], exclude_keywords=["kampanya", "teklif", "max"]))
        with col3:
            is_normal_campaign = st.checkbox("🎯 Standart Kampanya (HB Max Fiyat Kuralı)")
            if is_normal_campaign: sepet_indirimi = 0.0
            max_fiyat_col = st.selectbox("Girebileceğiniz Max. Fiyat", cols, index=find_default_col(cols, ["max", "maksimum", "girebileceğiniz"]))
        with col4: kampanya_fiyat_col = st.selectbox("Hepsiburada Paneline Yüklenecek Fiyat", cols, index=find_default_col(cols, ["uygulanacağı", "kampanya", "önerilen", "teklif", "avantajlı"], exclude_keywords=["durum"]))
        
        if st.button("⚡ Otomatik Fiyatlandır (Hepsiburada)", use_container_width=True):
            with st.spinner("⏳ Hepsiburada teklifleri kârlılık testinden geçiriliyor..."):
                islem_df = df_kampanya.copy()
                islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                
                durum_list, hesaplanan_karlar, hesaplanan_marjlar, katilim_fiyati = [], [], [], []
                for idx, row in merge_df.iterrows():
                    if pd.isna(row['_db_barkod']):
                        durum_list.append("Sistemde Yok"); hesaplanan_karlar.append(0); hesaplanan_marjlar.append(0); katilim_fiyati.append(np.nan); continue
                    maliyet, kargo, kom_orani = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                    fiyat = temizle_ve_sayiya_donustur(row[eski_fiyat_col])
                    if sepet_indirimi > 0: fiyat = fiyat * (1 - (sepet_indirimi / 100))
                    if fiyat <= 0:
                        durum_list.append("Elenmiş"); hesaplanan_karlar.append(0); hesaplanan_marjlar.append(0); katilim_fiyati.append(np.nan); continue
                    komisyon_tl = fiyat * (kom_orani / 100)
                    n_kar = fiyat - (maliyet + kargo + komisyon_tl)
                    k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                    if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                        durum_list.append("Kabul Edildi"); hesaplanan_karlar.append(n_kar); hesaplanan_marjlar.append(k_marji); katilim_fiyati.append(np.nan if is_normal_campaign else fiyat)
                    else:
                        durum_list.append("Elenmiş"); hesaplanan_karlar.append(n_kar); hesaplanan_marjlar.append(k_marji); katilim_fiyati.append(np.nan)
                        
                islem_df['Kampanya Durumu'] = durum_list; islem_df['Net Kâr (TL)'] = hesaplanan_karlar; islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                
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
                else: st.warning("Hedef kâr marjınızı karşılayan hiçbir HB teklifi bulunamadı.")
                
                output = BytesIO(); export_df = islem_df[cols].copy() 
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if len(basarili_df) > 0: basarili_df[cols].to_excel(writer, index=False, sheet_name='Uygun Teklifler')
                    islem_df[cols + ['Kampanya Durumu', 'Net Kâr (TL)', 'Kâr Marjı (%)']].to_excel(writer, index=False, sheet_name='Tüm Analiz Sonucu')
                    workbook = writer.book
                    for sheetname in workbook.sheetnames:
                        worksheet = workbook[sheetname]; header_fill = PatternFill(start_color="FF6700", end_color="FF6700", fill_type="solid"); header_font = Font(bold=True, color="FFFFFF")
                        if sheetname == 'Uygun Teklifler':
                            h_col_idx = export_df.columns.get_loc(kampanya_fiyat_col) + 1
                            for col_idx, col_name in enumerate(worksheet[1], 1):
                                col_name.fill = header_fill; col_name.font = header_font
                                if col_idx == h_col_idx and sepet_indirimi > 0: col_name.fill = PatternFill(start_color="2ECC71", end_color="2ECC71", fill_type="solid")
                        else:
                            for col_idx, col_name in enumerate(worksheet[1], 1): col_name.fill = header_fill; col_name.font = header_font
                        for col in worksheet.columns: worksheet.column_dimensions[get_column_letter(col[0].column)].width = 15
                output.seek(0)
                st.success("✅ Hepsiburada dosyanız hazır! İndirdiğiniz dosyadaki 'Uygun Teklifler' sekmesini doğrudan panelinize yükleyebilirsiniz.")
                st.download_button(label="📥 Hepsiburada İçin Hazır Excel'i İndir", data=output, file_name="HB_Kampanya_Sonucu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

# ==========================================
# SAYFA 4: TRENDYOL SATIŞ VE KÂRLILIK ANALİZİ
# ==========================================
elif menu == "📊 Trendyol Satış Analizi":
    st.markdown('<div class="sales-title">📊 Trendyol Detaylı Satış ve Kârlılık Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Trendyol panelinden aldığınız Sipariş / Satış raporunuzu yükleyin. Sistem, satışları maliyet veritabanınızla eşleştirip net kârınızı ve cironuzu hesaplar.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty:
        st.error("❌ Veritabanı boş! Maliyet kesintilerini doğru hesaplayabilmek için önce sol menüden 'Maliyet Yönetimi'ne girip ürün maliyetlerini kaydetmelisiniz.")
        st.stop()
        
    satis_file = st.file_uploader("Trendyol Sipariş / Satış Raporu Excel'ini Yükleyin (.xlsx veya .csv)", type=['xlsx', 'csv'], key="sales_upload")
    
    if satis_file:
        dosya_ismi = satis_file.name
        if dosya_ismi.endswith('.csv'):
            try: df_satis = pd.read_csv(satis_file, sep=None, engine='python')
            except: satis_file.seek(0); df_satis = pd.read_csv(satis_file, delimiter=';')
        else:
            df_satis = pd.read_excel(satis_file)
            
        cols_s = list(df_satis.columns)
        
        st.write("#### ⚙️ Rapor Sütunlarını Eşleştirin")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tarih_col = st.selectbox("Sipariş Tarihi Sütunu", cols_s, index=find_default_col(cols_s, ["tarih", "date", "zaman", "sipariş tarihi"]))
        with c2:
            barkod_s_col = st.selectbox("Barkod / SKU Sütunu", cols_s, index=find_default_col(cols_s, ["barkod", "barcode", "stok kodu", "sku"]))
        with c3:
            adet_col = st.selectbox("Satış Adedi Sütunu", cols_s, index=find_default_col(cols_s, ["adet", "miktar", "quantity", "sayı"]))
        with c4:
            fiyat_s_col = st.selectbox("Birim Satış Fiyatı (TL)", cols_s, index=find_default_col(cols_s, ["birim fiyat", "satış fiyatı", "fiyat", "tutar", "cüzdan"]))
            
        # Tarih Dönüştürme ve Zaman Filtreleri
        df_satis['_tarih_dt'] = pd.to_datetime(df_satis[tarih_col], errors='coerce', dayfirst=True)
        max_tarih = df_satis['_tarih_dt'].max()
        if pd.isna(max_tarih):
            max_tarih = datetime.now()
            
        st.markdown("### 🗓️ Zaman ve Tarih Filtresi")
        zaman_filtresi = st.radio("İncelemek İstediğiniz Dönemi Seçin:", [
            "⚡ Bugün (Anlık / Son Gün)", 
            "📅 Son 7 Gün (Haftalık)", 
            "🗓️ Son 30 Gün (Aylık)", 
            "🚀 Bu Yıl (Yıllık)", 
            "🔍 İki Tarih Arası (Özel Seçim)"
        ], horizontal=True)
        
        filtreli_df = df_satis.copy()
        
        if "Bugün" in zaman_filtresi:
            baslangic = max_tarih.replace(hour=0, minute=0, second=0)
            filtreli_df = filtreli_df[filtreli_df['_tarih_dt'] >= baslangic]
        elif "Son 7 Gün" in zaman_filtresi:
            baslangic = max_tarih - timedelta(days=7)
            filtreli_df = filtreli_df[filtreli_df['_tarih_dt'] >= baslangic]
        elif "Son 30 Gün" in zaman_filtresi:
            baslangic = max_tarih - timedelta(days=30)
            filtreli_df = filtreli_df[filtreli_df['_tarih_dt'] >= baslangic]
        elif "Bu Yıl" in zaman_filtresi:
            baslangic = datetime(max_tarih.year, 1, 1)
            filtreli_df = filtreli_df[filtreli_df['_tarih_dt'] >= baslangic]
        elif "İki Tarih" in zaman_filtresi:
            col_d1, col_d2 = st.columns(2)
            with col_d1: t_basla = st.date_input("Başlangıç Tarihi", value=(max_tarih - timedelta(days=15)).date())
            with col_d2: t_bitis = st.date_input("Bitiş Tarihi", value=max_tarih.date())
            filtreli_df = filtreli_df[(filtreli_df['_tarih_dt'].dt.date >= t_basla) & (filtreli_df['_tarih_dt'].dt.date <= t_bitis)]
            
        if len(filtreli_df) == 0:
            st.warning("⚠️ Seçilen tarih aralığında hiçbir satış kaydı bulunamadı. Lütfen filtreyi genişletin.")
        else:
            with st.spinner("⏳ Satışlar maliyet verilerinizle harmanlanıp kârlılık analiz ediliyor..."):
                # Sayısal alanları temizle
                filtreli_df['_adet'] = filtreli_df[adet_col].apply(temizle_ve_sayiya_donustur)
                filtreli_df['_birim_fiyat'] = filtreli_df[fiyat_s_col].apply(temizle_ve_sayiya_donustur)
                filtreli_df['_toplam_ciro'] = filtreli_df['_adet'] * filtreli_df['_birim_fiyat']
                filtreli_df['_barkod_clean'] = filtreli_df[barkod_s_col].astype(str).str.strip()
                
                # Veritabanı ile birleştir
                db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                merge_satis = pd.merge(filtreli_df, db, left_on='_barkod_clean', right_on='_db_barkod', how='left')
                
                # Maliyetleri Hesapla
                maliyet_tl_list, kargo_tl_list, komisyon_tl_list, net_kar_list, marj_list = [], [], [], [], []
                
                for idx, row in merge_satis.iterrows():
                    adet = row['_adet']
                    ciro = row['_toplam_ciro']
                    
                    if pd.isna(row['_db_barkod']):
                        # Sistemde yoksa masrafları 0 kabul et ve uyar
                        m_tl, kg_tl, kom_tl = 0.0, 0.0, 0.0
                    else:
                        m_tl = row['Maliyet (TL)'] * adet
                        kg_tl = row['Kargo (TL)'] * adet
                        kom_tl = ciro * (row['Komisyon (%)'] / 100)
                        
                    n_kar = ciro - (m_tl + kg_tl + kom_tl)
                    marj = (n_kar / ciro * 100) if ciro > 0 else 0.0
                    
                    maliyet_tl_list.append(m_tl)
                    kargo_tl_list.append(kg_tl)
                    komisyon_tl_list.append(kom_tl)
                    net_kar_list.append(n_kar)
                    marj_list.append(marj)
                    
                merge_satis['Top. Maliyet (TL)'] = maliyet_tl_list
                merge_satis['Top. Kargo (TL)'] = kargo_tl_list
                merge_satis['Top. Komisyon (TL)'] = komisyon_tl_list
                merge_satis['Net Kâr (TL)'] = net_kar_list
                merge_satis['Kâr Marjı (%)'] = marj_list
                
                # Genel KPI Değerleri
                top_adet = merge_satis['_adet'].sum()
                top_ciro = merge_satis['_toplam_ciro'].sum()
                top_maliyet = sum(maliyet_tl_list)
                top_kargo = sum(kargo_tl_list)
                top_komisyon = sum(komisyon_tl_list)
                top_masraf = top_maliyet + top_kargo + top_komisyon
                top_net_kar = sum(net_kar_list)
                ort_marj = (top_net_kar / top_ciro * 100) if top_ciro > 0 else 0.0
                
                st.markdown("---")
                st.markdown("### 📊 Seçilen Dönem Performans Özeti")
                
                kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
                with kpi1: st.markdown(f'<div class="sales-metric"><b>Satış Adedi:</b><br><span style="font-size:22px; font-weight:bold; color:#2980B9;">{int(top_adet):,} Adet</span></div>', unsafe_allow_html=True)
                with kpi2: st.markdown(f'<div class="sales-metric"><b>Toplam Ciro:</b><br><span style="font-size:22px; font-weight:bold; color:#27AE60;">{top_ciro:,.2f} TL</span></div>', unsafe_allow_html=True)
                with kpi3: st.markdown(f'<div class="sales-metric"><b>Toplam Masraf:</b><br><span style="font-size:22px; font-weight:bold; color:#E74C3C;">{top_masraf:,.2f} TL</span><br><small style="color:#7f8c8d;">Maliyet+Kargo+Kom.</small></div>', unsafe_allow_html=True)
                with kpi4: st.markdown(f'<div class="sales-metric" style="border-left-color: {"#2ECC71" if top_net_kar>=0 else "#E74C3C"};"><b>Net Kâr:</b><br><span style="font-size:22px; font-weight:bold; color:{"#2ECC71" if top_net_kar>=0 else "#E74C3C"};">{top_net_kar:,.2f} TL</span></div>', unsafe_allow_html=True)
                with kpi5: st.markdown(f'<div class="sales-metric"><b>Ort. Kâr Marjı:</b><br><span style="font-size:22px; font-weight:bold; color:#8E44AD;">% {ort_marj:.2f}</span></div>', unsafe_allow_html=True)
                
                # Masraf Kırılımı Detayı
                with st.expander("ℹ️ Toplam Masraf Kırılımı Detayını Göster"):
                    m_c1, m_c2, m_c3 = st.columns(3)
                    with m_c1: st.info(f"📦 **Ürün Geliş Maliyeti:** {top_maliyet:,.2f} TL (% {(top_maliyet/top_ciro*100) if top_ciro>0 else 0:.1f})")
                    with m_c2: st.warning(f"🚚 **Toplam Kargo Gideri:** {top_kargo:,.2f} TL (% {(top_kargo/top_ciro*100) if top_ciro>0 else 0:.1f})")
                    with m_c3: st.error(f"🤝 **Trendyol Komisyon Kesintisi:** {top_komisyon:,.2f} TL (% {(top_komisyon/top_ciro*100) if top_ciro>0 else 0:.1f})")

                # Şampiyonlar (Highlights) - En Çok Satan ve En Çok Kâr Getiren
                st.markdown("### 🏆 Dönemin Yıldız Ürünleri")
                urun_bazli = merge_satis.groupby('_barkod_clean').agg({
                    'Ürün Adı': 'first',
                    '_adet': 'sum',
                    '_toplam_ciro': 'sum',
                    'Net Kâr (TL)': 'sum'
                }).reset_index()
                
                en_cok_satan = urun_bazli.sort_values(by='_adet', ascending=False).iloc[0] if len(urun_bazli)>0 else None
                en_yuksek_ciro = urun_bazli.sort_values(by='_toplam_ciro', ascending=False).iloc[0] if len(urun_bazli)>0 else None
                en_cok_kar = urun_bazli.sort_values(by='Net Kâr (TL)', ascending=False).iloc[0] if len(urun_bazli)>0 else None
                
                h1, h2, h3 = st.columns(3)
                with h1:
                    if en_cok_satan is not None:
                        st.markdown(f'<div class="highlight-card">👑 <b>En Çok Satan Ürün</b><br><span style="color:#2980B9; font-weight:bold; font-size:16px;">{str(en_cok_satan["Ürün Adı"])[:35]}...</span><br><br><span style="font-size:20px; font-weight:800; color:#2C3E50;">{int(en_cok_satan["_adet"]):,} Adet</span> Satış</div>', unsafe_allow_html=True)
                with h2:
                    if en_yuksek_ciro is not None:
                        st.markdown(f'<div class="highlight-card">💎 <b>En Yüksek Ciro Getiren</b><br><span style="color:#27AE60; font-weight:bold; font-size:16px;">{str(en_yuksek_ciro["Ürün Adı"])[:35]}...</span><br><br><span style="font-size:20px; font-weight:800; color:#2C3E50;">{en_yuksek_ciro["_toplam_ciro"]:,.2f} TL</span> Ciro</div>', unsafe_allow_html=True)
                with h3:
                    if en_cok_kar is not None:
                        st.markdown(f'<div class="highlight-card">🚀 <b>En Çok Kâr Bırakan</b><br><span style="color:#8E44AD; font-weight:bold; font-size:16px;">{str(en_cok_kar["Ürün Adı"])[:35]}...</span><br><br><span style="font-size:20px; font-weight:800; color:#2ECC71;">{en_cok_kar["Net Kâr (TL)"]:,.2f} TL</span> Net Kâr</div>', unsafe_allow_html=True)

                st.markdown("---")
                
                # İki Sekmeli Gösterim: Ürün Bazlı Özet ve Detaylı Sipariş Listesi
                tab_ozet, tab_detay = st.tabs(["📦 Ürün Bazlı Performans Özet Tablosu", "📜 Detaylı Satış ve Masraf Listesi"])
                
                with tab_ozet:
                    st.write("Her bir ürününüzün seçilen tarihler arasında toplam kaç adet satıldığını, ne kadar masraf çıkardığını ve ne kadar kâr bıraktığını özetler:")
                    ozet_tablo = merge_satis.groupby('_barkod_clean').agg({
                        'Ürün Adı': 'first',
                        '_adet': 'sum',
                        '_toplam_ciro': 'sum',
                        'Top. Maliyet (TL)': 'sum',
                        'Top. Kargo (TL)': 'sum',
                        'Top. Komisyon (TL)': 'sum',
                        'Net Kâr (TL)': 'sum'
                    }).reset_index()
                    
                    ozet_tablo['Kâr Marjı (%)'] = np.where(ozet_tablo['_toplam_ciro']>0, (ozet_tablo['Net Kâr (TL)'] / ozet_tablo['_toplam_ciro'] * 100), 0.0)
                    ozet_tablo = ozet_tablo.rename(columns={'_barkod_clean': 'Barkod', '_adet': 'Top. Satış Adedi', '_toplam_ciro': 'Top. Ciro (TL)'})
                    
                    st.dataframe(ozet_tablo.style.format({
                        'Top. Satış Adedi': '{:,.0f}',
                        'Top. Ciro (TL)': '{:,.2f} TL',
                        'Top. Maliyet (TL)': '{:,.2f} TL',
                        'Top. Kargo (TL)': '{:,.2f} TL',
                        'Top. Komisyon (TL)': '{:,.2f} TL',
                        'Net Kâr (TL)': '{:,.2f} TL',
                        'Kâr Marjı (%)': '% {:.2f}'
                    }), use_container_width=True)
                    
                with tab_detay:
                    st.write("Satır satır tüm satış işlemleriniz ve hesaplanan kesintiler:")
                    goster_sutunlar = [tarih_col, barkod_s_col, adet_col, fiyat_s_col, 'Top. Maliyet (TL)', 'Top. Kargo (TL)', 'Top. Komisyon (TL)', 'Net Kâr (TL)', 'Kâr Marjı (%)']
                    st.dataframe(merge_satis[goster_sutunlar].style.format({
                        'Top. Maliyet (TL)': '{:,.2f} TL',
                        'Top. Kargo (TL)': '{:,.2f} TL',
                        'Top. Komisyon (TL)': '{:,.2f} TL',
                        'Net Kâr (TL)': '{:,.2f} TL',
                        'Kâr Marjı (%)': '% {:.2f}'
                    }), use_container_width=True)
                    
                # Excel Olarak İndirme
                out_excel = BytesIO()
                with pd.ExcelWriter(out_excel, engine='openpyxl') as wr:
                    ozet_tablo.to_excel(wr, index=False, sheet_name='Ürün Bazlı Özet')
                    merge_satis[goster_sutunlar].to_excel(wr, index=False, sheet_name='Detaylı Satış Listesi')
                    
                    wb = wr.book
                    for sh_name in wb.sheetnames:
                        ws = wb[sh_name]
                        fill = PatternFill(start_color="2980B9", end_color="2980B9", fill_type="solid")
                        font = Font(bold=True, color="FFFFFF")
                        for col_idx, cell in enumerate(ws[1], 1):
                            cell.fill = fill; cell.font = font
                        for col in ws.columns: ws.column_dimensions[get_column_letter(col[0].column)].width = 16
                out_excel.seek(0)
                
                st.download_button(
                    label="📥 Satış ve Kârlılık Analizini Excel Olarak İndir",
                    data=out_excel,
                    file_name=f"Trendyol_Satis_Analizi_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
