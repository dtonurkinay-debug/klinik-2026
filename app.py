import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import date

# --- 1. GÜVENLİK AYARI (Şifre) ---
PASSWORD = "klinik2026" # Burayı istediğin zaman değiştirebilirsin

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Klinik 2026 Girişi")
        pwd = st.text_input("Lütfen şifreyi giriniz:", type="password")
        if st.button("Giriş Yap"):
            if pwd == PASSWORD:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
        return False
    return True

# --- 2. GOOGLE SHEETS BAĞLANTISI ---
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
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

if check_password():
    try:
        df, worksheet = load_data()
        # Tarih kolonunu düzelt
        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
    except Exception as e:
        st.error("Veritabanına bağlanılamadı. Lütfen Sheets bağlantısını kontrol edin.")
        st.stop()

    # --- ÜST PANEL: ÖZET METRİKLER ---
    st.title("📊 Klinik 2026 Finansal Dashboard")
    
    # Hesaplamalar
    toplam_gelir = df[df['Islem Turu'] == 'Gelir']['Tutar'].sum()
    toplam_gider = df[df['Islem Turu'] == 'Gider']['Tutar'].sum()
    net_bakiye = toplam_gelir - toplam_gider

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} ₺", delta_color="normal")
    m2.metric("Toplam Gider", f"{toplam_gider:,.2f} ₺", delta="-", delta_color="inverse")
    m3.metric("Kasa Net Bakiye", f"{net_bakiye:,.2f} ₺")

    st.divider()

    # --- ORTA PANEL: FİLTRELEME VE TABLO ---
    col_tablo, col_form = st.columns([2, 1])

    with col_tablo:
        st.subheader("📑 Son İşlemler")
        # Ay filtresi
        df['Ay'] = pd.to_datetime(df['Tarih']).dt.strftime('%B')
        aylar = ["Hepsi"] + list(df['Ay'].unique())
        secilen_ay = st.selectbox("Ay Seçiniz:", aylar)
        
        filtered_df = df if secilen_ay == "Hepsi" else df[df['Ay'] == secilen_ay]
        st.dataframe(filtered_df.drop(columns=['Ay']), use_container_width=True, hide_index=True)

    with col_form:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_islem", clear_on_submit=True):
            f_tarih = st.date_input("İşlem Tarihi", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = st.text_input("Hasta / Cari Adı")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Kira", "Maaş", "Laboratuvar", "Diğer"])
            f_doviz = st.selectbox("Döviz", ["TRY", "USD", "EUR"])
            f_tutar = st.number_input("Tutar", min_value=0.0, step=100.0)
            f_tek = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
            
            if st.form_submit_button("Sisteme İşle"):
                new_row = [len(df)+1, str(f_tarih), f_tur, f_cari, f_kat, f_doviz, f_tutar, f_tek, " Uygulama üzerinden eklendi"]
                worksheet.append_row(new_row)
                st.success("Başarıyla kaydedildi!")
                st.rerun()

    st.info("💡 İpucu: Tablodaki sütun başlıklarına tıklayarak sıralama yapabilirsiniz.")
