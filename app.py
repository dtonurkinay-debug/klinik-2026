import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import date

# --- 1. GÜVENLİK ---
PASSWORD = "klinik2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Klinik 2026 Girişi")
        pwd = st.text_input("Şifre:", type="password")
        if st.button("Giriş"):
            if pwd == PASSWORD:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
        return False
    return True

# --- 2. BAĞLANTI ---
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

SHEET_ID = "1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM" 

def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # Sütun isimlerini standardize et (Boşlukları sil)
    df.columns = df.columns.str.strip()
    if 'Silindi' not in df.columns: df['Silindi'] = ""
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

if check_password():
    df, worksheet = load_data()
    df_visible = df[df['Silindi'] != 'X'].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")

    # METRİKLER
    t_gelir = pd.to_numeric(df_visible[df_visible['Islem Turu'] == 'Gelir']['Tutar'], errors='coerce').sum()
    t_gider = pd.to_numeric(df_visible[df_visible['Islem Turu'] == 'Gider']['Tutar'], errors='coerce').sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{t_gelir:,.2f} ₺")
    m2.metric("Toplam Gider", f"{t_gider:,.2f} ₺")
    m3.metric("Net Kasa", f"{(t_gelir - t_gider):,.2f} ₺")

    st.divider()

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.subheader("📑 İşlem Listesi")
        
        # TABLO BAŞLIKLARI
        c1, c2, c3, c4, c5 = st.columns([0.5, 2.5, 1.2, 1, 1.5])
        c1.write("**ID**")
        c2.write("**Hasta Adı**")
        c3.write("**Tutar**")
        c4.write("**Tür**")
        c5.write("**İşlemler**")
        st.divider()

        # HER SATIR İÇİN DÖNGÜ VE BUTONLAR
        for index, row in df_visible.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([0.5, 2.5, 1.2, 1, 0.7, 0.8])
            
            r1.write(f"#{row['ID']}")
            # Sütun ismi 'Hasta Adi' mi yoksa 'Hasta Adı' mı kontrolü
            h_adi = row.get('Hasta Adi', row.get('Hasta Adı', 'Belirtilmedi'))
            r2.write(h_adi)
