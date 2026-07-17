import streamlit as st
import utils

def render():
    st.markdown('<div class="section-title">📊 Mağaza Performans ve Durum Özeti</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Sistemdeki aktif ürünlerinizin, maliyet yapılarınızın ve API bağlantılarınızın genel durumu.</div>', unsafe_allow_html=True)
    
    db = utils.load_db()
    api = utils.load_api_settings()
    api_connected = bool(api["ty_seller_id"] and api["ty_api_key"] and api["ty_api_secret"])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-badge"><div class="stat-label">Kayıtlı Ürün Sayısı</div><div class="stat-value">{len(db)} Adet</div></div>', unsafe_allow_html=True)
    with c2: 
        ort_maliyet = db["Maliyet (TL)"].mean() if len(db)>0 else 0.0
        st.markdown(f'<div class="stat-badge" style="border-left-color:#10b981;"><div class="stat-label">Ortalama Maliyet</div><div class="stat-value">{ort_maliyet:,.2f} TL</div></div>', unsafe_allow_html=True)
    with c3:
        ort_kom = db["Komisyon (%)"].mean() if len(db)>0 else 0.0
        st.markdown(f'<div class="stat-badge" style="border-left-color:#f59e0b;"><div class="stat-label">Ort. Komisyon Oranı</div><div class="stat-value">% {ort_kom:.1f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-badge" style="border-left-color:{"#10b981" if api_connected else "#ef4444"};"><div class="stat-label">Trendyol API Durumu</div><div class="stat-value" style="color:{"#10b981" if api_connected else "#ef4444"};">{"🟢 Bağlı" if api_connected else "🔴 Eksik"}</div></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Hızlı Erişim İşlemleri")
    hc1, hc2, hc3 = st.columns(3)
    with hc1:
        st.markdown('<div class="web-card"><h4>📦 Yeni Ürün Maliyeti Ekle</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Pazaryeri hesaplamalarında kullanılmak üzere yeni ürün barkodu ve alış fiyatı tanımlayın.</p></div>', unsafe_allow_html=True)
        if st.button("Maliyet Tablosuna Git ➔", use_container_width=True, key="go_db"): st.session_state["active_page"] = "📦 Maliyet Yönetimi"; st.rerun()
    with hc2:
        st.markdown('<div class="web-card"><h4>🧮 Kâr Marjı Simülasyonu Yap</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Hedeflediğiniz net kârı veya yüzdelik marjı elde etmek için ideal satış fiyatınızı bulun.</p></div>', unsafe_allow_html=True)
        if st.button("Fiyat Hesaplayıcıya Git ➔", use_container_width=True, key="go_calc"): st.session_state["active_page"] = "🧮 İdeal Fiyatlama"; st.rerun()
    with hc3:
        st.markdown('<div class="web-card"><h4>📈 Kampanya Excel\'i Yükle</h4><p style="color:#64748b; font-size:13px; min-height:40px;">Trendyol veya Hepsiburada kampanya dosyalarınızı yükleyerek zarar etmeyecek fiyatları bulun.</p></div>', unsafe_allow_html=True)
        if st.button("Trendyol Analizine Git ➔", use_container_width=True, key="go_ty"): st.session_state["active_page"] = "🚀 Trendyol Yıldız"; st.rerun()
