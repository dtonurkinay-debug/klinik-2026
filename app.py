import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import date

# --- GOOGLE SHEETS BAĞLANTISI ---
# Bu kısım GitHub Secrets üzerinden gelecek, şimdilik altyapıyı kuruyoruz
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    # Streamlit Cloud üzerinde 'secrets' kısmına JSON içeriğini yapıştıracağız
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# Google Sheet ID'nizi buraya yazacağız
SHEET_ID = "1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM" 

def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data), sheet

# --- ARAYÜZ ---
st.set_page_config(page_title="Klinik 2026 Canlı Panel", layout="wide")

try:
    df, worksheet = load_data()
    st.success("Veritabanı Bağlantısı Başarılı!")
except Exception as e:
    st.error(f"Bağlantı Bekleniyor... Lütfen kurulum adımlarını tamamlayın.")
    st.stop()

# --- TASARIM VE MANTIK ---
st.title("📊 Klinik 2026 Finans Yönetimi")

# Yan Panel: Veri Girişi
st.sidebar.header("🦷 Yeni İşlem Kaydı")
with st.sidebar.form("islem_formu"):
    f_tarih = st.date_input("Tarih", date.today())
    f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"])
    f_cari = st.text_input("Hasta / Cari Adı")
    f_kat = st.selectbox("Kategori", ["İmplant", "Kira", "Maaş", "Laboratuvar", "Yemek", "Diğer"])
    f_doviz = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
    f_tutar = st.number_input("Tutar", min_value=0.0)
    f_tek = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
    submit = st.form_submit_button("Google Sheets'e Kaydet")

    if submit:
        # Yeni satırı hazırla (Sheets'teki sütun sırasına göre)
        # ID, Tarih, Islem Turu, Hasta veya Cari Adi, Kategori, Para Birimi, Tutar, Teknisyen, Aciklama
        new_row = [
            len(df) + 1, 
            str(f_tarih), 
            f_tur, 
            f_cari, 
            f_kat, 
            f_doviz, 
            float(f_tutar), 
            f_tek, 
            "" # Açıklama boş
        ]
        worksheet.append_row(new_row)
        st.sidebar.success("Veri Sheets'e işlendi!")
        st.rerun()

# Ana Tablo Gösterimi
st.subheader("📑 Güncel Hareketler")
st.dataframe(df.tail(20), use_container_width=True, hide_index=True)
