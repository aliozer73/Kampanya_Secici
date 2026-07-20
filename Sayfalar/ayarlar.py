import streamlit as st
import utils

def render():
    st.markdown('<div class="section-title">⚙️ Ayarlar & API Yapılandırması</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Mağazalarınızın API anahtarlarını buradan girin. Girdiğiniz bilgiler sistemde güvenle saklanır ve sayfa yenilense dahi asla silinmez.</div>', unsafe_allow_html=True)
    
    ayarlar = utils.load_api_settings()
    
    st.markdown("---")
    
    # --- TRENDYOL API AYARLARI ---
    st.markdown("### 🧡 Trendyol API Bilgileri")
    with st.container(): st.markdown("<div class='web-card'>", unsafe_allow_html=True)
    t_id = st.text_input("Trendyol Satıcı ID (Seller ID):", value=ayarlar.get("ty_seller_id", ""), key="input_ty_id", placeholder="Örn: 123456")
    t_key = st.text_input("Trendyol API Key:", value=ayarlar.get("ty_api_key", ""), key="input_ty_key", type="password", placeholder="API Anahtarınız...")
    t_sec = st.text_input("Trendyol API Secret:", value=ayarlar.get("ty_api_secret", ""), key="input_ty_sec", type="password", placeholder="API Gizli Anahtarınız...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # --- HEPSİBURADA API AYARLARI ---
    st.markdown("### 💜 Hepsiburada API Bilgileri")
    with st.container(): st.markdown("<div class='web-card'>", unsafe_allow_html=True)
    h_id = st.text_input("Hepsiburada Mağaza ID (Merchant ID):", value=ayarlar.get("hb_merchant_id", ""), key="input_hb_id", placeholder="Örn: xxx-yyy-zzz")
    h_key = st.text_input("Hepsiburada API Anahtarı (Authorization Token / Basic Auth):", value=ayarlar.get("hb_api_key", ""), key="input_hb_key", type="password", placeholder="API Anahtarınız...")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # --- WOOCOMMERCE / AYTENS.COM API AYARLARI ---
    st.markdown("### 🛍️ aytens.com (WooCommerce) API Bilgileri")
    with st.container(): st.markdown("<div class='web-card'>", unsafe_allow_html=True)
    w_url = st.text_input("E-Ticaret Site URL Address:", value=ayarlar.get("wc_url", ""), key="input_wc_url", placeholder="Örn: https://www.aytens.com")
    w_ck = st.text_input("Consumer Key (CK):", value=ayarlar.get("wc_consumer_key", ""), key="input_wc_ck", type="password", placeholder="ck_xxxxxxxxxxxxxxxxx")
    w_cs = st.text_input("Consumer Secret (CS):", value=ayarlar.get("wc_consumer_secret", ""), key="input_wc_cs", type="password", placeholder="cs_xxxxxxxxxxxxxxxxx")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("")
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        if st.button("💾 Tüm API Ayarlarını Güvenle Kaydet", type="primary", use_container_width=True):
            yeni_ayarlar = {
                "ty_seller_id": t_id.strip(),
                "ty_api_key": t_key.strip(),
                "ty_api_secret": t_sec.strip(),
                "hb_merchant_id": h_id.strip(),
                "hb_api_key": h_key.strip(),
                "wc_url": w_url.strip().rstrip('/'),
                "wc_consumer_key": w_ck.strip(),
                "wc_consumer_secret": w_cs.strip()
            }
            basarili = utils.save_api_settings(yeni_ayarlar)
            if basarili:
                st.success("✅ **API ve Key bilgileriniz başarıyla kaydedildi!** Sayfa yenilense dahi silinmez.")
            else:
                st.warning("⚠️ Ayarlar belleğe kaydedildi ancak dosya sistemine yazılırken bir kısıtlama oluştu. Oturum boyunca verileriniz aktif kalacaktır.")
