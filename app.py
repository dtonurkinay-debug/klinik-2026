import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import date

# --- GÜVENLİK ---
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

# --- BAĞLANTI ---
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
    if 'Silindi' not in df.columns: df['Silindi'] = ""
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

if check_password():
    df, worksheet = load_data()
    df_visible = df[df['Silindi'] != 'X'].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")

    # METRİKLER
    t_gelir = pd.to_numeric(df_visible[df_visible['Islem Turu'] == 'Gelir']['Tutar']).sum()
    t_gider = pd.to_numeric(df_visible[df_visible['Islem Turu'] == 'Gider']['Tutar']).sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{t_gelir:,.2f} ₺")
    m2.metric("Toplam Gider", f"{t_gider:,.2f} ₺")
    m3.metric("Net Kasa", f"{(t_gelir - t_gider):,.2f} ₺")

    st.divider()

    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.subheader("📑 Güncel Hareketler")
        
        # BAŞLIK SATIRI
        h1, h2, h3, h4, h5 = st.columns([0.5, 2, 1, 1, 1.5])
        h1.write("**ID**")
        h2.write("**Hasta Adı**")
        h3.write("**Tutar**")
        h4.write("**Tür**")
        h5.write("**İşlemler**")
        st.divider()

        # SATIRLAR VE BUTONLAR
        for index, row in df_visible.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([0.5, 2, 1, 1, 0.7, 0.8])
            r1.write(row['ID'])
            r2.write(row['Hasta Adi'])
            r3.write(f"{row['Tutar']} {row['Para Birimi']}")
            r4.write(row['Islem Turu'])
            
            # DÜZENLEME BUTONU
            if r5.button("✏️", key=f"edit_{row['ID']}"):
                @st.dialog(f"Düzenle: ID {row['ID']}")
                def edit_dialog(item):
                    new_cari = st.text_input("Hasta/Cari", value=item['Hasta Adi'])
                    new_tutar = st.number_input("Tutar", value=float(item['Tutar']))
                    if st.button("Kaydet"):
                        row_idx = df[df['ID'] == item['ID']].index[0] + 2
                        worksheet.update_cell(row_idx, 4, new_cari)
                        worksheet.update_cell(row_idx, 7, new_tutar)
                        st.success("Güncellendi!")
                        st.rerun()
                edit_dialog(row)

            # SİLME BUTONU
            if r6.button("🗑️", key=f"del_{row['ID']}"):
                @st.dialog("Kaydı Sil")
                def delete_dialog(item):
                    st.warning(f"{item['Hasta Adi']} silinecek. Emin misiniz?")
                    if st.button("Evet, Sil"):
                        row_idx = df[df['ID'] == item['ID']].index[0] + 2
                        worksheet.update_cell(row_idx, 10, "X")
                        st.rerun()
                delete_dialog(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_form", clear_on_submit=True):
            f_tarih = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Diğer"])
