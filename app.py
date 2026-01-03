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
    return pd.DataFrame(data), sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro v3", layout="wide")

if check_password():
    df, worksheet = load_data()
    
    st.title("📊 Klinik 2026 Finansal Yönetim")
    
    # --- ÖZET METRİKLER ---
    toplam_gelir = df[df['Islem Turu'] == 'Gelir']['Tutar'].sum()
    toplam_gider = df[df['Islem Turu'] == 'Gider']['Tutar'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} ₺")
    m2.metric("Toplam Gider", f"{toplam_gider:,.2f} ₺")
    m3.metric("Net Kasa", f"{(toplam_gelir - toplam_gider):,.2f} ₺")

    # --- İŞLEMLER ---
    tab1, tab2 = st.tabs(["📋 İşlem Listesi & Silme", "➕ Yeni Kayıt Ekle"])

    with tab1:
        st.subheader("Güncel Hareketler")
        # Silme Bölümü
        with st.expander("🗑️ Kayıt Sil / Düzenle"):
            sil_id = st.selectbox("Silinecek İşlem ID (En soldaki rakam):", df['ID'].tolist())
            if st.button("❌ Seçili Kaydı Kalıcı Olarak Sil"):
                # Sheets'te ID'ye göre satırı bul (Başlık satırı + 1)
                row_to_delete = df[df['ID'] == sil_id].index[0] + 2
                worksheet.delete_rows(int(row_to_delete))
                st.warning(f"ID {sil_id} başarıyla silindi!")
                st.rerun()

        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form("yeni_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            f_tarih = col1.date_input("Tarih", date.today())
            f_tur = col2.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = col1.text_input("Hasta/Cari")
            f_kat = col2.selectbox("Kategori", ["İmplant", "Dolgu", "Kira", "Maaş", "Lab", "Diğer"])
            f_tutar = col1.number_input("Tutar", min_value=0.0)
            f_doviz = col2.selectbox("Döviz", ["TRY", "USD", "EUR"])
            
            if st.form_submit_button("Kaydet"):
                yeni_id = int(df['ID'].max() + 1) if not df.empty else 1
                worksheet.append_row([yeni_id, str(f_tarih), f_tur, f_cari, f_kat, f_doviz, f_tutar, "", "Uygulama Girişi"])
                st.success("Kayıt eklendi!")
                st.rerun()
