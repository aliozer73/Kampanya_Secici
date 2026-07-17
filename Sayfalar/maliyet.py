import streamlit as st
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
import utils

def parse_xml_feed(xml_content):
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        return None, f"❌ XML Ayrıştırma Hatası: {str(e)}"
        
    product_tags = ['Urun', 'urun', 'Product', 'product', 'item', 'Item', 'ProductItem', 'Urunler', 'Products', 'channel']
    items = []
    
    # Kök altındaki veya bir alt seviyedeki tüm ürün düğümlerini bul
    for child in root:
        if child.tag in product_tags or len(list(child)) >= 2:
            if child.tag.lower() == 'channel':
                for sub in child:
                    if sub.tag.lower() == 'item' or len(list(sub)) >= 2: items.append(sub)
            else:
                items.append(child)
                
    if not items:
        return None, "❌ XML dosyasında ürün düğümü (<Urun>, <item>, <Product> vb.) bulunamadı."
        
    def get_xml_val(node, possible_tags):
        for tag in possible_tags:
            val = node.find(tag)
            if val is not None and val.text: return val.text.strip()
            for c in node:
                if c.tag.lower() == tag.lower() and c.text: return c.text.strip()
        return ""

    parsed_products = []
    for item in items:
        barkod = get_xml_val(item, ['Barkod', 'barcode', 'Barcode', 'sku', 'SKU', 'StokKodu', 'stok_kodu', 'Stok_Kodu', 'ID', 'id', 'code', 'model', 'ModelKodu'])
        if not barkod: continue
        
        ad = get_xml_val(item, ['UrunAdi', 'urun_adi', 'Name', 'name', 'Title', 'title', 'Baslik', 'label', 'Urun_Adi'])
        satis_str = get_xml_val(item, ['SatisFiyati', 'satis_fiyati', 'Price', 'price', 'ListeFiyati', 'liste_fiyati', 'regular_price', 'Satis_Fiyati', 'guncel_fiyat', 'Fiyat'])
        alis_str = get_xml_val(item, ['AlisFiyati', 'alis_fiyati', 'Cost', 'cost', 'Maliyet', 'maliyet', 'purchase_price', 'Alis_Fiyati'])
        
        try: satis_fiyati = float(satis_str.replace(',', '.')) if satis_str else 0.0
        except: satis_fiyati = 0.0
        
        try: alis_fiyati = float(alis_str.replace(',', '.')) if alis_str else 0.0
        except: alis_fiyati = 0.0
        
        # Alış fiyatı XML'de yoksa veya 0 ise Satış Fiyatının 1/3'ünü al
        maliyet_val = alis_fiyati if alis_fiyati > 0 else round(satis_fiyati / 3.0, 2)
        
        parsed_products.append({
            'Barkod': str(barkod).strip(),
            'Ürün Adı': str(ad).strip(),
            'Satış Fiyatı (TL)': satis_fiyati,
            'Maliyet (TL)': maliyet_val,
            'Kargo (TL)': 100.0,
            'Komisyon (%)': 22.5,
            'Diğer Masraflar (%)': 1.0
        })
        
    return parsed_products, None

def render():
    st.markdown('<div class="section-title">📦 Ürün Maliyet Veritabanı</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tüm kampanya ve satış analizlerinde ortak kullanılacak olan ürün maliyet, kargo ve komisyon listeniz.</div>', unsafe_allow_html=True)
    
    mevcut_db = utils.load_db()
    api_ayarlar = utils.load_api_settings()
    
    # Eksik sütun kontrolü
    if 'Satış Fiyatı (TL)' not in mevcut_db.columns: mevcut_db['Satış Fiyatı (TL)'] = 0.0
    if 'Diğer Masraflar (%)' not in mevcut_db.columns: mevcut_db['Diğer Masraflar (%)'] = 1.0
    
    # Üst Bölüm: 3 Sekmeli Yönetim Alanı
    tab_tekli, tab_toplu, tab_xml = st.tabs(["➕ Tekil Ürün Ekle", "📂 Excel / CSV Toplu Yükle", "🔗 XML Linki ile Otomatik Güncelleme"])
    
    # -----------------------------------------------------------------
    # SEKME 1: TEKİL ÜRÜN EKLE
    # -----------------------------------------------------------------
    with tab_tekli:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        with st.form("tekil_ekle_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 2, 1.2])
            with c1:
                yeni_barkod = st.text_input("Barkod / SKU *", placeholder="Örn: TR-890123")
                yeni_kargo = st.number_input("Kargo Gideri (TL)", min_value=0.0, value=100.0, step=5.0, format="%.2f")
                yeni_diger = st.number_input("Diğer Masraflar (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.5, format="%.2f")
            with c2:
                yeni_ad = st.text_input("Ürün Adı", placeholder="Örn: Altın Kaplama Kolye")
                yeni_satis = st.number_input("Satış Fiyatı (TL)", min_value=0.0, value=300.0, step=10.0, format="%.2f")
                yeni_komisyon = st.number_input("Pazaryeri Komisyonu (%)", min_value=0.0, max_value=100.0, value=22.5, step=0.5, format="%.2f")
            with c3:
                yeni_maliyet = st.number_input("Maliyet (TL) *", min_value=0.0, value=100.0, step=5.0, format="%.2f", help="Varsayılan olarak 100 TL gelmektedir.")
                st.write("") # Boşluk
                submit_tekil = st.form_submit_button("➕ Listeye Ekle", use_container_width=True)
                
            if submit_tekil:
                barkod_temiz = str(yeni_barkod).strip()
                if not barkod_temiz or barkod_temiz == 'nan':
                    st.error("❌ Barkod alanı zorunludur!")
                else:
                    yeni_satir = pd.DataFrame([{
                        'Barkod': barkod_temiz,
                        'Ürün Adı': str(yeni_ad).strip(),
                        'Satış Fiyatı (TL)': float(yeni_satis),
                        'Maliyet (TL)': float(yeni_maliyet),
                        'Kargo (TL)': float(yeni_kargo),
                        'Komisyon (%)': float(yeni_komisyon),
                        'Diğer Masraflar (%)': float(yeni_diger)
                    }])
                    if not mevcut_db.empty and barkod_temiz in mevcut_db['Barkod'].astype(str).values:
                        idx = mevcut_db[mevcut_db['Barkod'].astype(str) == barkod_temiz].index[0]
                        for col in yeni_satir.columns: mevcut_db.loc[idx, col] = yeni_satir.iloc[0][col]
                        st.success(f"🔄 `{barkod_temiz}` barkodlu ürün güncellendi!")
                    else:
                        mevcut_db = pd.concat([yeni_satir, mevcut_db], ignore_index=True)
                        st.success(f"✅ `{barkod_temiz}` listeye eklendi!")
                    mevcut_db.to_csv(utils.DB_FILE, index=False)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # SEKME 2: EXCEL / CSV TOPLU YÜKLE
    # -----------------------------------------------------------------
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
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: b_col = st.selectbox("Barkod Sütunu", cols, index=utils.find_default_col(cols, ["barkod", "barcode", "sku"]))
                with sc2: a_col = st.selectbox("Ürün Adı Sütunu", cols, index=utils.find_default_col(cols, ["ad", "name", "ürün"]))
                with sc3: s_col = st.selectbox("Satış Fiyatı Sütunu", cols, index=utils.find_default_col(cols, ["satış", "satis", "tsf", "fiyat", "price"]))
                with sc4: m_col = st.selectbox("Maliyet Sütunu (Yoksa 1/3 Hesaplanır)", ["-- Otomatik (Satış / 3) --"] + cols, index=0)
                
                islemi_sec = st.radio("Aktarım Yöntemi:", [
                    "🔄 Mevcut listeyle birleştir (Aynı barkodları güncelle, yenileri ekle)",
                    "⚠️ Mevcut listeyi sil ve tamamen bu dosyayı yükle"
                ], horizontal=True)
                
                if st.button("🚀 Dosyadaki Ürünleri Veritabanına Aktar", type="primary", use_container_width=True):
                    yeni_liste = []
                    for _, row in df_yuklenen.iterrows():
                        brk = str(row[b_col]).strip() if pd.notna(row[b_col]) else ""
                        if not brk or brk == 'nan': continue
                        
                        satis_val = utils.temizle_ve_sayiya_donustur(row[s_col])
                        if m_col == "-- Otomatik (Satış / 3) --":
                            maliyet_val = round(satis_val / 3.0, 2)
                        else:
                            maliyet_val = utils.temizle_ve_sayiya_donustur(row[m_col])
                            
                        yeni_liste.append({
                            'Barkod': brk,
                            'Ürün Adı': str(row[a_col]).strip() if pd.notna(row[a_col]) else "",
                            'Satış Fiyatı (TL)': satis_val,
                            'Maliyet (TL)': maliyet_val,
                            'Kargo (TL)': 100.0,
                            'Komisyon (%)': 22.5,
                            'Diğer Masraflar (%)': 1.0
                        })
                    
                    df_yeni_aktarim = pd.DataFrame(yeni_liste)
                    
                    if "sil ve tamamen" in islemi_sec:
                        son_db = df_yeni_aktarim
                    else:
                        if not mevcut_db.empty:
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

    # -----------------------------------------------------------------
    # SEKME 3: XML LİNKİ İLE OTOMATİK GÜNCELLEME
    # -----------------------------------------------------------------
    with tab_xml:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        st.markdown("#### 🔗 XML Linki ile Canlı Ürün Entegrasyonu ve Senkronizasyon")
        st.write("Streamlit gibi bulut sunucular Trendyol API IP adreslerini engellediği (403 hatası) için, e-ticaret sitenizin veya tedarikçinizin **XML ürün beslemesi (Feed URL)** üzerinden tüm ürünleri, satış fiyatlarını ve maliyetleri tek tıkla senkronize edebilirsiniz.")
        
        st.info("💡 **Otomatik Atanan Kurallar:** Alış Fiyatı XML'de yoksa Maliyet = **Satış Fiyatının 1/3'ü**, Komisyon = **%22.5**, Kargo = **100 TL**, Diğer Masraflar = **%1.0** olarak işlenir.")
        
        kayitli_xml = api_ayarlar.get("xml_url", "")
        xml_url_input = st.text_input("🌐 XML Ürün Besleme Linkiniz (URL):", value=kayitli_xml, placeholder="https://www.siteadiniz.com/xml/urunler.xml")
        
        col_x1, col_x2 = st.columns([1.5, 1])
        with col_x1:
            senkron_yontemi = st.radio("🔄 Senkronizasyon Yöntemi:", [
                "➕🔄 Hem Yeni Ürünleri Ekle Hem de Mevcutların Fiyatlarını Güncelle (Önerilen)",
                "🔄 Sadece Sistemde Mevcut Olan Ürünlerin Fiyatlarını Güncelle",
                "⚠️ Tabloyu Tamamen Temizle ve Sadece XML'den Gelenleri Yükle"
            ])
        with col_x2:
            st.write("") # Boşluk
            test_xml_yukle = st.checkbox("🧪 Örnek XML Linki ile Test Et (URL Boşsa Simülasyon Çalıştır)")
            
        if st.button("🚀 XML Linkinden Ürünleri Çek ve Senkronize Et", type="primary", use_container_width=True, key="btn_xml_sync"):
            url_target = xml_url_input.strip()
            
            if test_xml_yukle or not url_target:
                # Simülasyon XML verisi
                sample_xml_data = """<?xml version="1.0" encoding="UTF-8"?>
                <Urunler>
                    <Urun><Barkod>AYT003IMT00540</Barkod><UrunAdi>Zarif Şık Inci Kolye Seti (XML Güncel)</UrunAdi><SatisFiyati>540.00</SatisFiyati><AlisFiyati>180.00</AlisFiyati></Urun>
                    <Urun><Barkod>AYT002BKR0007</Barkod><UrunAdi>El Yapımı %100 Bakır Bilezik</UrunAdi><SatisFiyati>600.00</SatisFiyati><AlisFiyati>200.00</AlisFiyati></Urun>
                    <Urun><Barkod>AYT-XML-9901</Barkod><UrunAdi>925 Ayar Gümüş İtalyan Zincir (Yeni XML Ürün)</UrunAdi><SatisFiyati>750.00</SatisFiyati><AlisFiyati>250.00</AlisFiyati></Urun>
                    <Urun><Barkod>AYT-XML-9902</Barkod><UrunAdi>24K Altın Kaplama Baget Yüzük</UrunAdi><SatisFiyati>450.00</SatisFiyati></Urun>
                </Urunler>"""
                items, err = parse_xml_feed(sample_xml_data)
                st.toast("🧪 Örnek simülasyon XML verisi kullanılıyor...", icon="ℹ️")
            else:
                with st.spinner("🌐 XML adresi üzerinden veriler indiriliyor ve ayrıştırılıyor..."):
                    try:
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                        resp = requests.get(url_target, headers=headers, timeout=25)
                        if resp.status_code == 200:
                            # URL'yi kaydet
                            api_ayarlar["xml_url"] = url_target
                            utils.save_api_settings(api_ayarlar)
                            items, err = parse_xml_feed(resp.content)
                        else:
                            items, err = None, f"❌ XML adresine ulaşılamadı (HTTP {resp.status_code})"
                    except Exception as e:
                        items, err = None, f"❌ Bağlantı Hatası: {str(e)}"
                        
            if err:
                st.error(err)
            elif not items:
                st.warning("⚠️ XML beslemesinden geçerli ürün verisi çekilemedi.")
            else:
                df_xml = pd.DataFrame(items)
                
                if "Tamamen Temizle" in senkron_yontemi or mevcut_db.empty:
                    yeni_db = df_xml
                    st.success(f"✅ Tablo sıfırlandı ve XML'den {len(yeni_db)} ürün aktarıldı!")
                elif "Sadece Sistemde Mevcut Olan" in senkron_yontemi:
                    guncellenen_sayisi = 0
                    for idx, row in mevcut_db.iterrows():
                        brk = str(row['Barkod']).strip()
                        eslesen = df_xml[df_xml['Barkod'] == brk]
                        if not eslesen.empty:
                            mevcut_db.loc[idx, 'Satış Fiyatı (TL)'] = eslesen.iloc[0]['Satış Fiyatı (TL)']
                            mevcut_db.loc[idx, 'Maliyet (TL)'] = eslesen.iloc[0]['Maliyet (TL)']
                            mevcut_db.loc[idx, 'Ürün Adı'] = eslesen.iloc[0]['Ürün Adı']
                            guncellenen_sayisi += 1
                    yeni_db = mevcut_db
                    st.success(f"🔄 Sistemdeki {guncellenen_sayisi} ürünün satış fiyatı ve maliyeti XML'den canlı güncellendi!")
                else:
                    # Hem ekle hem güncelle
                    eski_olmayanlar = mevcut_db[~mevcut_db['Barkod'].astype(str).isin(df_xml['Barkod'])].copy()
                    yeni_db = pd.concat([df_xml, eski_olmayanlar], ignore_index=True)
                    st.success(f"✅ XML senkronizasyonu başarılı! Toplam {len(df_xml)} ürün işlendi (Güncellenenler + Yeni Eklenenler).")
                    
                yeni_db.to_csv(utils.DB_FILE, index=False)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Mevcut Ürün Maliyet Listesi ve Anlık Düzenleme")
    
    if mevcut_db.empty:
        st.info("💡 Sistemde henüz kayıtlı ürün bulunmuyor. Yukarıdaki sekmelerden ürün ekleyebilir veya XML linkinizden senkronize edebilirsiniz.")
        ornek_veri = pd.DataFrame([{
            'Barkod': 'AYT003IMT00540',
            'Ürün Adı': 'Zarif Şık Inci Kolye Seti',
            'Satış Fiyatı (TL)': 499.90,
            'Maliyet (TL)': 166.63,
            'Kargo (TL)': 100.0,
            'Komisyon (%)': 22.5,
            'Diğer Masraflar (%)': 1.0
        }])
        mevcut_db = pd.concat([mevcut_db, ornek_veri], ignore_index=True)
        
    edited_df = st.data_editor(
        utils.tablayi_1den_baslat(mevcut_db),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Barkod": st.column_config.TextColumn("Barkod / SKU", required=True),
            "Ürün Adı": st.column_config.TextColumn("Ürün Adı", width="large"),
            "Satış Fiyatı (TL)": st.column_config.NumberColumn("Satış Fiyatı (TL)", min_value=0.0, format="%.2f"),
            "Maliyet (TL)": st.column_config.NumberColumn("Maliyet (TL)", min_value=0.0, format="%.2f"),
            "Kargo (TL)": st.column_config.NumberColumn("Kargo (TL)", min_value=0.0, format="%.2f"),
            "Komisyon (%)": st.column_config.NumberColumn("Komisyon (%)", min_value=0.0, max_value=100.0, format="%.2f"),
            "Diğer Masraflar (%)": st.column_config.NumberColumn("Diğer Masraflar (%)", min_value=0.0, max_value=100.0, format="%.2f"),
        },
        height=480
    )
    
    if st.button("💾 Tablodaki Değişiklikleri Veritabanına Kaydet", type="primary", use_container_width=True):
        df_save = edited_df.reset_index(drop=True)
        df_save['Barkod'] = df_save['Barkod'].astype(str).str.strip()
        df_save = df_save[df_save['Barkod'] != '']; df_save = df_save[df_save['Barkod'] != 'nan']
        df_save.to_csv(utils.DB_FILE, index=False)
        st.success("✅ Ürün veritabanınız başarıyla güncellendi!")
