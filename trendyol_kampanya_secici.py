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
    page_title="Trendyol Avantajlı Ürün Fiyatlandırma",
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
    val_str = str(val).strip().replace('.', '').replace(',', '.')
    try: return float(val_str)
    except ValueError:
        try: return float(str(val).strip().replace(',', '.'))
        except ValueError: return 0.0

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={'Barkod': str})
    return pd.DataFrame(columns=['Barkod', 'Ürün Adı', 'Maliyet (TL)', 'Kargo (TL)', 'Komisyon (%)'])

# --- YAN MENÜ ---
st.sidebar.markdown("<h2 style='text-align: center; color: #E74C3C;'>🏷️ Avantajlı Ürün</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #2ECC71; font-weight: bold;'>Fiyatlandırma Sistemi</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("Sayfa Seçimi:", ["📦 Maliyet Yönetimi", "🚀 Yıldızlı Fiyat Analizi"])
st.sidebar.markdown("---")

# ==========================================
# SAYFA 1: MALİYET VERİTABANI YÖNETİMİ
# ==========================================
if menu == "📦 Maliyet Yönetimi":
    st.markdown('<div class="main-title">📦 Veritabanı Yönetimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Canlı tabloda ürün maliyetlerinizi, kargo ve komisyon oranlarınızı hızlıca düzenleyin. Çift tıklayarak hücreyi değiştirebilirsiniz.</div>', unsafe_allow_html=True)
    
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
            "Barkod": st.column_config.TextColumn("Barkod", required=True),
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
# SAYFA 2: KAMPANYA ANALİZİ
# ==========================================
elif menu == "🚀 Yıldızlı Fiyat Analizi":
    st.markdown('<div class="main-title">📈 Yıldızlı Ürünler Akıllı Fiyatlandırma</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Trendyol\'dan indirdiğiniz "Yıldızlı Ürün Etiketleri" dosyasını yükleyin. Sistem, 3 Yıldız > 2 Yıldız > 1 Yıldız sırasıyla kâr marjınızı test eder ve size kâr sağlayan <b>en iyi fiyatı</b> otomatik yazar.</div>', unsafe_allow_html=True)
    
    db = load_db()
    if db.empty:
        st.error("❌ Lütfen önce sol menüden ürün maliyetlerinizi girin!")
        st.stop()
        
    st.markdown("### 🎯 Kârlılık Kriterleri")
    c1, c2 = st.columns(2)
    with c1: min_kar_marji = st.number_input("Minimum Hedef Kâr Marjı (%)", min_value=-50.0, value=15.0, step=1.0)
    with c2: min_net_kar_tl = st.number_input("Minimum Net Kâr Tutarı (TL)", min_value=0.0, value=20.0, step=1.0)
    st.markdown("---")
    
    kampanya_file = st.file_uploader("Trendyol 'Yıldızlı Ürün Etiketleri' Dosyasını Yükleyin", type=['xlsx', 'csv'])
    
    if kampanya_file:
        orijinal_dosya_ismi = kampanya_file.name
        
        # Dosya türüne göre oku
        if orijinal_dosya_ismi.endswith('.csv'):
            try:
                df_kampanya = pd.read_csv(kampanya_file, sep=None, engine='python')
            except:
                kampanya_file.seek(0)
                df_kampanya = pd.read_csv(kampanya_file, delimiter=';')
        else:
            df_kampanya = pd.read_excel(kampanya_file)
            
        cols = list(df_kampanya.columns)
        
        # Sütunları bul
        barkod_col = next((c for c in cols if 'BARKOD' in c.upper()), cols[1] if len(cols)>1 else cols[0])
        fiyat_1_yildiz = next((c for c in cols if '1 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_2_yildiz = next((c for c in cols if '2 YILDIZ ÜST FİYAT' in c.upper()), None)
        fiyat_3_yildiz = next((c for c in cols if '3 YILDIZ ÜST FİYAT' in c.upper()), None)
        yeni_fiyat_col = next((c for c in cols if 'YENİ TSF' in c.upper()), None)
        
        if st.button("⚡ Otomatik Fiyatlandır", use_container_width=True):
            if not all([fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz, yeni_fiyat_col]):
                st.error("❌ Yüklediğiniz dosyada Yıldızlı Fiyat sütunları (1/2/3 YILDIZ ÜST FİYAT veya YENİ TSF) bulunamadı. Doğru Trendyol şablonunu yüklediğinizden emin olun.")
            else:
                with st.spinner("⏳ Fiyatlandırma senaryoları test ediliyor... (Öncelik: 3 Yıldız > 2 Yıldız > 1 Yıldız)"):
                    
                    islem_df = df_kampanya.copy()
                    islem_df['_kamp_barkod'] = islem_df[barkod_col].astype(str).str.strip()
                    
                    db['_db_barkod'] = db['Barkod'].astype(str).str.strip()
                    merge_df = pd.merge(islem_df, db, left_on='_kamp_barkod', right_on='_db_barkod', how='left')
                    
                    # Sayısal çevrimler
                    for col in [fiyat_1_yildiz, fiyat_2_yildiz, fiyat_3_yildiz]:
                        merge_df[col + '_num'] = merge_df[col].apply(temizle_ve_sayiya_donustur)
                        
                    # Seçim Mantığı: 3 Yıldız'dan başlayarak kontrol et (en iyi indirim).
                    # Şartı sağlayan ilk fiyatı seç. 3 olmazsa 2'ye, 2 olmazsa 1'e bak.
                    
                    secilen_fiyatlar = []
                    secilen_yildizlar = []
                    hesaplanan_karlar = []
                    hesaplanan_marjlar = []
                    
                    # SIRALAMA DEĞİŞTİRİLDİ: 3 -> 2 -> 1
                    test_siralamasi = [
                        ("3 Yıldız", fiyat_3_yildiz+'_num'), 
                        ("2 Yıldız", fiyat_2_yildiz+'_num'), 
                        ("1 Yıldız", fiyat_1_yildiz+'_num')
                    ]
                    
                    for idx, row in merge_df.iterrows():
                        if pd.isna(row['_db_barkod']):
                            secilen_fiyatlar.append(np.nan)
                            secilen_yildizlar.append("Sistemde Yok")
                            hesaplanan_karlar.append(0)
                            hesaplanan_marjlar.append(0)
                            continue
                            
                        maliyet = row['Maliyet (TL)']
                        kargo = row['Kargo (TL)']
                        kom_orani = row['Komisyon (%)']
                        
                        uygun_fiyat = np.nan
                        secili_yildiz = "Elenmiş"
                        net_kar = 0
                        kar_marji = 0
                        
                        # Test döngüsü (3 Yıldızdan başlar)
                        for yildiz_isim, f_col in test_siralamasi:
                            fiyat = row[f_col]
                            if fiyat <= 0: continue
                            
                            komisyon_tl = fiyat * (kom_orani / 100)
                            toplam_maliyet = maliyet + kargo + komisyon_tl
                            n_kar = fiyat - toplam_maliyet
                            k_marji = (n_kar / fiyat) * 100 if fiyat > 0 else 0
                            
                            if n_kar >= min_net_kar_tl and k_marji >= min_kar_marji:
                                uygun_fiyat = fiyat
                                secili_yildiz = yildiz_isim
                                net_kar = n_kar
                                kar_marji = k_marji
                                break # Şartı sağlayan fiyatta dur
                                
                        secilen_fiyatlar.append(uygun_fiyat)
                        secilen_yildizlar.append(secili_yildiz)
                        hesaplanan_karlar.append(net_kar)
                        hesaplanan_marjlar.append(kar_marji)
                        
                    # Atamalar
                    islem_df['Seçilen Yıldız'] = secilen_yildizlar
                    islem_df['Net Kâr (TL)'] = hesaplanan_karlar
                    islem_df['Kâr Marjı (%)'] = hesaplanan_marjlar
                    
                    def format_fiyat(val):
                        if pd.isna(val) or val == 0: return ""
                        return str(val).replace('.', ',')
                        
                    islem_df[yeni_fiyat_col] = [format_fiyat(f) for f in secilen_fiyatlar]
                    
                    # Sonuçları ayır
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
                        goster_cols = [barkod_col, yeni_fiyat_col, 'Seçilen Yıldız', 'Net Kâr (TL)', 'Kâr Marjı (%)']
                        st.dataframe(basarili_df[goster_cols].style.format({'Net Kâr (TL)': '{:.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                    else:
                        st.warning("Hiçbir ürün kriterleri karşılamadı.")
                    
                    # Excel Çıktısı
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
                            if col_idx == p_col_idx:
                                cell.fill = PatternFill(start_color="E74C3C", end_color="E74C3C", fill_type="solid")
                                
                        for col in worksheet.columns:
                            col_letter = get_column_letter(col[0].column)
                            worksheet.column_dimensions[col_letter].width = 15
                            
                    output.seek(0)
                    
                    st.markdown("---")
                    st.success("✅ Excel dosyanız yüklendiği orijinal isimle indirilmeye hazır! Sadece P sütununa (YENİ TSF) kârlı olan fiyatlar girilmiştir.")
                    
                    download_name = orijinal_dosya_ismi.rsplit('.', 1)[0] + ".xlsx"
                    st.download_button(
                        label="📥 Trendyol İçin Hazır Excel'i İndir",
                        data=output,
                        file_name=download_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
