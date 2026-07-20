import os
import json
import sqlite3
import pandas as pd
import streamlit as st

API_FILE = "api_ayarlar.json"
DB_FILE = "maliyet_vt.db"
AUTH_FILE = "auth.json"

# --- YETKİLENDİRME (AUTH) FONKSİYONLARI ---

def load_auth():
    if "auth_cache" in st.session_state and isinstance(st.session_state["auth_cache"], dict):
        if "users" not in st.session_state["auth_cache"]:
            st.session_state["auth_cache"]["users"] = {
                "aliozer73": "Ayten136",
                "admin": "123",
                "aytens": "123456",
                "yonetici": "admin2026"
            }
        return st.session_state["auth_cache"]
        
    defaults = {
        "username": "aliozer73",
        "password": "Ayten136",
        "is_logged_in": False,
        "users": {
            "aliozer73": "Ayten136",
            
        }
    }
    
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                if "users" not in defaults or not isinstance(defaults["users"], dict):
                    defaults["users"] = {
                        "aliozer73": "Ayten136",
                        "admin": "123",
                        "aytens": "123456",
                        "yonetici": "admin2026"
                    }
                else:
                    defaults["users"]["aliozer73"] = "Ayten136"
                    defaults["username"] = "aliozer73"
                    defaults["password"] = "Ayten136"
        except Exception:
            pass
            
    st.session_state["auth_cache"] = defaults
    return defaults

def save_auth(new_auth):
    current = load_auth()
    current.update(new_auth)
    st.session_state["auth_cache"] = current
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

# --- API AYARLARI YÖNETİMİ ---

def load_api_settings():
    if "api_settings_cache" in st.session_state and isinstance(st.session_state["api_settings_cache"], dict):
        return st.session_state["api_settings_cache"]
        
    defaults = {
        "ty_seller_id": "", "ty_api_key": "", "ty_api_secret": "",
        "hb_merchant_id": "", "hb_api_key": "", "hb_api_secret": "",
        "wc_url": "", "wc_consumer_key": "", "wc_consumer_secret": ""
    }
    if os.path.exists(API_FILE):
        try:
            with open(API_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
            
    st.session_state["api_settings_cache"] = defaults
    return defaults

def save_api_settings(new_settings):
    current = load_api_settings()
    current.update(new_settings)
    st.session_state["api_settings_cache"] = current
    try:
        with open(API_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

# --- VERİTABANI VE YARDIMCI ARAÇLAR ---

def load_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["Barkod", "Ürün Adı", "Maliyet (TL)", "Kargo (TL)", "Komisyon (%)", "Diğer Masraflar (%)"])
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM urun_maliyetleri", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["Barkod", "Ürün Adı", "Maliyet (TL)", "Kargo (TL)", "Komisyon (%)", "Diğer Masraflar (%)"])

def save_db(df):
    try:
        conn = sqlite3.connect(DB_FILE)
        df.to_sql("urun_maliyetleri", conn, if_exists="replace", index=False)
        conn.close()
        return True
    except Exception:
        return False

def temizle_ve_sayiya_donustur(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).replace("TL", "").replace("%", "").replace(" ", "").strip()
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    try:
        return float(val_str)
    except:
        return 0.0

def find_default_col(cols, keywords):
    for i, c in enumerate(cols):
        for kw in keywords:
            if kw.lower() in str(c).lower():
                return i
    return 0

def tablayi_1den_baslat(df):
    df_copy = df.copy()
    df_copy.index = range(1, len(df_copy) + 1)
    return df_copy
