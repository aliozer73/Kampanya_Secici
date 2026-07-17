import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import utils

def render():
    st.markdown('<div class="section-title">🧮 Akıllı Satış Fiyatı & Kâr Marjı Simülatörü</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Ürün alış fiyatı, kargo ve pazaryeri komisyon kesintilerini hesaba katarak zarar etmemeniz için gereken satış fiyatını hesaplayın.</div>', unsafe_allow_html=True)
    
    tab_tekli, tab_toplu = st.tabs(["⚡ Hızlı Tekli Simülasyon", "📦 Tüm Ürünlere Toplu Fiyat Atama"])
    with tab_tekli:
        st.markdown("<div class='web-card'>", unsafe_allow_html=True)
        col_inp1, col_inp2, col_inp3 = st.columns(3)
        with col_inp1:
            in_maliyet = st.number_input("📦 Ürün Maliyeti (TL)", min_value=0.0, value=150.0, step=5.0, format="%.2f")
            in_kargo = st.number_input("🚚 Kargo Gideri (TL)", min_value=0.0, value=45.0, step=5.0, format="%.2f")
        with col_inp2:
            in_komisyon = st.number_input("🤝 Pazaryeri Komisyonu (%)", min_value=0.0, max_value=95.0, value=18.0, step=1.0, format="%.2f")
            hesap_yontemi = st.radio("Hedefleme Yöntemi:", ["📊 Yüzdelik Kâr Marjı (%)", "💵 Net Kâr Tutarı (TL)"], horizontal=True)
        with col_inp3:
            if "Yüzdelik" in hesap_yontemi: in_hedef_val = st.number_input("🎯 Hedef Kâr Marjı (%)", min_value=1.0, max_value=80.0, value=25.0, step=1.0, format="%.2f")
            else: in_hedef_val = st.number_input("🎯 Hedef Net Kâr Tutarı (TL)", min_value=1.0, value=100.0, step=10.0, format="%.2f")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if "Yüzdelik" in hesap_yontemi:
            toplam_kesinti_orani = (in_komisyon + in_hedef_val) / 100.0
            if toplam_kesinti_orani >= 1.0: st.error("❌ Komisyon ve Kâr Marjı toplamı %100 veya üstü olamaz!"); ideal_fiyat = 0.0
            else: ideal_fiyat = (in_maliyet + in_kargo) / (1.0 - toplam_kesinti_orani)
        else:
            kom_orani = in_komisyon / 100.0
            if kom_orani >= 1.0: st.error("❌ Komisyon oranı %100 olamaz!"); ideal_fiyat = 0.0
            else: ideal_fiyat = (in_maliyet + in_kargo + in_hedef_val) / (1.0 - kom_orani)
                
        if ideal_fiyat > 0:
            komisyon_tl = ideal_fiyat * (in_komisyon / 100.0)
            net_kar = ideal_fiyat - (in_maliyet + in_kargo + komisyon_tl)
            kar_marji = (net_kar / ideal_fiyat * 100.0) if ideal_fiyat > 0 else 0.0
            
            st.markdown("#### 💡 Önerilen Satış Fiyatı Özeti")
            r1, r2, r3, r4 = st.columns(4)
            with r1: st.markdown(f'<div class="stat-badge" style="border-left-color:#8e44ad;"><div class="stat-label">İdeal Satış Fiyatı</div><div class="stat-value" style="color:#8e44ad;">{ideal_fiyat:,.2f} TL</div></div>', unsafe_allow_html=True)
            with r2: st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Net Kâr Tutarı</div><div class="stat-value" style="color:#10b981;">{net_kar:,.2f} TL</div></div>', unsafe_allow_html=True)
            with r3: st.markdown(f'<div class="stat-badge" style="border-left-color:#0284c7;"><div class="stat-label">Gerçek Kâr Marjı</div><div class="stat-value" style="color:#0284c7;">% {kar_marji:.2f}</div></div>', unsafe_allow_html=True)
            with r4: st.markdown(f'<div class="stat-badge" style="border-left-color:#ef4444;"><div class="stat-label">Komisyon Kesintisi</div><div class="stat-value" style="color:#ef4444;">{komisyon_tl:,.2f} TL</div></div>', unsafe_allow_html=True)

    with tab_toplu:
        st.write("Veritabanındaki tüm ürünleriniz için istediğiniz hedefi belirleyip tek tuşla yeni satış fiyatı listesi oluşturun.")
        db = utils.load_db()
        if db.empty: st.warning("⚠️ Önce Maliyet Yönetimi sayfasından ürün eklemelisiniz.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1: toplu_yontem = st.selectbox("Toplu Hesaplama Hedefi:", ["📊 Sabit Kâr Marjı (%) Uygula", "💵 Sabit Net Kâr Tutarı (TL) Uygula"])
            with col_b2:
                if "Marjı" in toplu_yontem: toplu_hedef_val = st.number_input("Tüm Ürünler İçin Hedef Kâr Marjı (%)", min_value=1.0, max_value=80.0, value=30.0, step=1.0)
                else: toplu_hedef_val = st.number_input("Tüm Ürünler İçin Hedef Net Kâr (TL)", min_value=1.0, value=120.0, step=10.0)
            if st.button("🚀 Tüm Ürünler İçin İdeal Fiyatları Hesapla", use_container_width=True):
                df_res = db.copy()
                ideal_fiyatlar, komisyonlar, net_karlar, marjlar = [], [], [], []
                for idx, row in df_res.iterrows():
                    m_val, k_val, kom_val = row['Maliyet (TL)'], row['Kargo (TL)'], row['Komisyon (%)']
                    if "Marjı" in toplu_yontem:
                        t_rate = (kom_val + toplu_hedef_val) / 100.0
                        i_fiyat = 0.0 if t_rate >= 1.0 else (m_val + k_val) / (1.0 - t_rate)
                    else:
                        k_rate = kom_val / 100.0
                        i_fiyat = 0.0 if k_rate >= 1.0 else (m_val + k_val + toplu_hedef_val) / (1.0 - k_rate)
                    kom_tl = i_fiyat * (kom_val / 100.0) if i_fiyat > 0 else 0.0
                    n_kar = i_fiyat - (m_val + k_val + kom_tl) if i_fiyat > 0 else 0.0
                    k_marji = (n_kar / i_fiyat * 100.0) if i_fiyat > 0 else 0.0
                    ideal_fiyatlar.append(i_fiyat); komisyonlar.append(kom_tl); net_karlar.append(n_kar); marjlar.append(k_marji)
                df_res['Önerilen Satış Fiyatı (TL)'] = ideal_fiyatlar; df_res['Komisyon Tutarı (TL)'] = komisyonlar; df_res['Net Kâr (TL)'] = net_karlar; df_res['Kâr Marjı (%)'] = marjlar
                st.success("✅ Toplu fiyatlandırma başarıyla tamamlandı!")
                st.dataframe(utils.tablayi_1den_baslat(df_res).style.format({'Maliyet (TL)': '{:,.2f} TL', 'Kargo (TL)': '{:,.2f} TL', 'Komisyon (%)': '% {:.2f}', 'Önerilen Satış Fiyatı (TL)': '{:,.2f} TL', 'Komisyon Tutarı (TL)': '{:,.2f} TL', 'Net Kâr (TL)': '{:,.2f} TL', 'Kâr Marjı (%)': '% {:.2f}'}), use_container_width=True)
                out_exc = BytesIO()
                with pd.ExcelWriter(out_exc, engine='openpyxl') as wr:
                    utils.tablayi_1den_baslat(df_res).reset_index().to_excel(wr, index=False, sheet_name='İdeal Fiyat Listesi')
                out_exc.seek(0)
                st.download_button("📥 İdeal Fiyat Listesini Excel Olarak İndir", data=out_exc, file_name=f"Toplu_Ideal_Fiyat_Listesi_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
