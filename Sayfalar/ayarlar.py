import streamlit as st
import utils

def render():
    st.markdown('<div class="section-title">⚙️ Sistem Ayarları & API Yönetimi</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Mağaza entegrasyon bilgilerinizi ve panel kullanıcı hesaplarınızı buradan güvenle yönetin.</div>', unsafe_allow_html=True)
    
    api = utils.load_api_settings()
    auth_data = utils.load_auth()
    
    st.markdown("### 🟠 Trendyol API Anahtarları")
    with st.form("api_form"):
        ty_id = st.text_input("Satıcı ID (Seller ID)", value=api["ty_seller_id"])
        ty_key = st.text_input("API Key", value=api["ty_api_key"], type="password")
        ty_sec = st.text_input("API Secret", value=api["ty_api_secret"], type="password")
        if st.form_submit_button("💾 API Bilgilerini Kaydet", use_container_width=True):
            utils.save_api_settings({"ty_seller_id": ty_id.strip(), "ty_api_key": ty_key.strip(), "ty_api_secret": ty_sec.strip()})
            st.success("✅ Trendyol API bilgileri kaydedildi!")
            
    st.markdown("---")
    st.markdown("### 👥 Kullanıcı ve Şifre Yönetimi")
    t1, t2, t3 = st.tabs(["🔑 Şifre Değiştir", "➕ Yeni Kullanıcı Oluştur", "📋 Mevcut Kullanıcılar"])
    with t1:
        with st.form("pass_form"):
            eski_sifre = st.text_input("Mevcut Şifre", type="password")
            yeni_sifre = st.text_input("Yeni Şifre", type="password")
            yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar)", type="password")
            if st.form_submit_button("💾 Şifreyi Güncelle", use_container_width=True):
                curr_u = st.session_state.get('current_user', '')
                if auth_data["users"].get(curr_u) != eski_sifre.strip(): st.error("❌ Mevcut şifreniz yanlış!")
                elif len(yeni_sifre.strip()) < 3 or yeni_sifre.strip() != yeni_sifre_tekrar.strip(): st.error("❌ Yeni şifreler uyuşmuyor veya çok kısa!")
                else: auth_data["users"][curr_u] = yeni_sifre.strip(); utils.save_auth(auth_data); st.success("✅ Şifreniz güncellendi!")
    with t2:
        with st.form("new_user_form"):
            yeni_kadi = st.text_input("Yeni Kullanıcı Adı")
            yeni_kuser_sifre = st.text_input("Şifre", type="password")
            yeni_kuser_sifre_tekrar = st.text_input("Şifre (Tekrar)", type="password")
            if st.form_submit_button("➕ Kullanıcıyı Oluştur", use_container_width=True):
                k_adi_temiz = yeni_kadi.strip()
                if not k_adi_temiz or k_adi_temiz in auth_data["users"]: st.error("❌ Kullanıcı adı boş veya zaten mevcut!")
                elif len(yeni_kuser_sifre.strip()) < 3 or yeni_kuser_sifre.strip() != yeni_kuser_sifre_tekrar.strip(): st.error("❌ Şifreler uyuşmuyor veya çok kısa!")
                else: auth_data["users"][k_adi_temiz] = yeni_kuser_sifre.strip(); utils.save_auth(auth_data); st.success(f"✅ `{k_adi_temiz}` kullanıcısı oluşturuldu!")
    with t3:
        for idx, u in enumerate(list(auth_data["users"].keys()), 1):
            st.markdown(f"**{idx}.** 👤 `{u}` {'*(Aktif Oturum)*' if u == st.session_state.get('current_user') else ''}")
