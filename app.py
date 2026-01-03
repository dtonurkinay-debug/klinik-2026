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
    if 'Silindi' not in df.columns:
        df['Silindi'] = ""
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

if check_password():
    df, worksheet = load_data()
    # Sadece silinmemişleri filtrele
    df_visible = df[df['Silindi'] != 'X'].copy()

    st.title("📊 Klinik 2026 Finansal Yönetim")

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
        # Tablo ve Seçim
        event = st.dataframe(
            df_visible, 
            use_container_width=True, 
            hide_index=True, 
            selection_mode="single_row",
            on_select="rerun"
        )
        
        selected_rows = event.selection.rows
        
        if len(selected_rows) > 0:
            selected_index = selected_rows[0]
            item = df_visible.iloc[selected_index]
            
            st.info(f"Seçili: **{item['Hasta Adi']}** | {item['Tutar']} ₺")
            b_col1, b_col2 = st.columns(2)

            # DÜZENLEME MODAL
            if b_col1.button("✏️ Kaydı Düzenle", use_container_width=True):
                @st.dialog("Kayıt Düzenle")
                def edit_modal(data_row):
                    e_cari = st.text_input("Hasta/Cari Adı", value=data_row['Hasta Adi'])
                    e_tutar = st.number_input("Tutar", value=float(data_row['Tutar']))
                    e_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Kira", "Maaş", "Lab", "Diğer"])
                    if st.button("Güncellemeyi Kaydet"):
                        row_idx = df[df['ID'] == data_row['ID']].index[0] + 2
                        worksheet.update_cell(row_idx, 4, e_cari)
                        worksheet.update_cell(row_idx, 5, e_kat)
                        worksheet.update_cell(row_idx, 7, e_tutar)
                        st.success("Başarıyla güncellendi!")
                        st.rerun()
                edit_modal(item)

            # SİLME MODAL
            if b_col2.button("🗑️ Kaydı Sil", use_container_width=True):
                @st.dialog("Kaydı Sil")
                def delete_modal(data_row):
                    st.warning(f"'{data_row['Hasta Adi']}' kaydı silinecek. Emin misiniz?")
                    if st.button("Evet, Silinmiş İşaretle"):
                        row_idx = df[df['ID'] == data_row['ID']].index[0] + 2
                        worksheet.update_cell(row_idx, 10, "X") # J sütunu
                        st.success("Kayıt silindi!")
                        st.rerun()
                delete_modal(item)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_giris", clear_on_submit=True):
            f_tarih = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Kira", "Maaş", "Lab", "Diğer"])
            f_tutar = st.number_input("Tutar", min_value=0.0)
            f_doviz = st.selectbox("Döviz", ["TRY", "USD", "EUR"])
            if st.form_submit_button("Kaydet"):
                yeni_id = int(df['ID'].max() + 1) if not df.empty else 1
                worksheet.append_row([yeni_id, str(f_tarih), f_tur, f_cari, f_kat, f_doviz, f_tutar, "", "Yeni Kayıt", ""])
                st.success("Eklendi!")
                st.rerun()
