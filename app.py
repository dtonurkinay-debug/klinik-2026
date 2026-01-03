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
    # Eğer "Silindi" sütunu yoksa oluştur (Sheets'te J sütunu olarak düşünelim)
    if 'Silindi' not in df.columns:
        df['Silindi'] = ""
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 V4", layout="wide")

if check_password():
    df, worksheet = load_data()
    # Sadece silinmemiş kayıtları göster
    df_visible = df[df['Silindi'] != 'X'].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")

    # METRİKLER
    t_gelir = df_visible[df_visible['Islem Turu'] == 'Gelir']['Tutar'].sum()
    t_gider = df_visible[df_visible['Islem Turu'] == 'Gider']['Tutar'].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{t_gelir:,.2f} ₺")
    m2.metric("Toplam Gider", f"{t_gider:,.2f} ₺")
    m3.metric("Net Kasa", f"{(t_gelir - t_gider):,.2f} ₺")

    st.divider()

    # ANA DÜZEN: SOLDA TABLO VE ARAÇLAR, SAĞDA YENİ KAYIT
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.subheader("📑 İşlem Listesi")
        
        # Tablodan Satır Seçme Özelliği
        event = st.dataframe(
            df_visible, 
            use_container_width=True, 
            hide_index=True, 
            selection_mode="single_row", # Satır seçimine izin ver
            on_select="rerun"
        )
        
        selected_rows = event.selection.rows
        
        if len(selected_rows) > 0:
            selected_index = selected_rows[0]
            selected_data = df_visible.iloc[selected_index]
            
            st.write(f"👉 **Seçili:** {selected_data['Hasta Adi']} - {selected_data['Tutar']} ₺")
            
            btn_col1, btn_col2 = st.columns(2)
            
            # DÜZENLEME POP-UP (Modal)
            if btn_col1.button("✏️ Kaydı Düzenle"):
                @st.dialog("Kayıt Düzenle")
                def edit_dialog(item):
                    st.write(f"ID: {item['ID']} numaralı kaydı gün
