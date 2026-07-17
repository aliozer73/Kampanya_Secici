import os
import json
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

DB_FILE = 'urun_maliyet_veritabani.csv'
API_FILE = 'api_ayarlari.json'
AUTH_FILE = 'auth_config.json'

def load_auth():
    default_auth = {"users": {"aliozer73": "Ayten136"}}
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                if "username" in saved and "password" in saved and "users" not in saved:
                    default_auth["users"][saved["username"]] = saved["password"]
                elif "users" in saved and isinstance(saved["users"], dict):
                    default_auth["users"].update(saved["users"])
        except Exception: pass
    else:
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_auth, f, ensure_ascii=False, indent=4)
    return default_auth

def save_auth(auth_data):
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(auth_data, f, ensure_ascii=False, indent=4)

def load_db():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE, dtype={'Barkod': str})
    return pd.DataFrame(columns=['Barkod', 'Ürün Adı', 'Maliyet (TL)', 'Kargo (TL)', 'Komisyon (%)'])

def tablayi_1den_baslat(df):
    df_copy = df.copy()
    df_copy.index = np.arange(1, len(df_copy) + 1)
    df_copy.index.name = "Sıra"
    return df_copy

def temizle_ve_sayiya_donustur(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).strip()
    if not val_str: return 0.0
    if '.' in val_str and ',' in val_str:
        if val_str.rfind('.') > val_str.rfind(','): val_str = val_str.replace(',', '')
        else: val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except ValueError: return 0.0

def find_default_col(options, keywords, exclude_keywords=None):
    if exclude_keywords is None: exclude_keywords = []
    for opt in options:
        opt_lower = str(opt).lower()
        if any(kw in opt_lower for kw in keywords) and not any(ex_kw in opt_lower for ex_kw in exclude_keywords):
            return options.index(opt)
    return 0

def load_api_settings():
    default_settings = {"ty_seller_id": "", "ty_api_key": "", "ty_api_secret": ""}
    if os.path.exists(API_FILE):
        try:
            with open(API_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception: pass
    return default_settings

def save_api_settings(settings):
    with open(API_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)
