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
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro v10", layout="wide")

if check_password():
    df, worksheet = load_data()
    
    # "Silindi" sütunu J (10.) sütundur.
    if "Silindi" not in df.columns:
        df["Silindi"] = ""
    
    df_visible = df[df["Silindi"] != "X"].copy()

    st.title("📊 Klinik 2026 Finans Yönetimi")

    # ÜST METRİKLER
    df_visible["Tutar"] = pd.to_numeric(df_visible["Tutar"], errors='coerce').fillna(0)
    t_gelir = df_visible[df_visible["Islem Turu"] == "Gelir"]["Tutar"].sum()
    t_gider = df_visible[df_visible["Islem Turu"] == "Gider"]["Tutar"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Gelir", f"{t_gelir:,.2f} ₺")
    m2.metric("Toplam Gider", f"{t_gider:,.2f} ₺")
    m3.metric("Net Kasa", f"{(t_gelir - t_gider):,.2f} ₺")

    st.divider()

    # ANA DÜZEN
    col_main, col_side = st.columns([4, 1]) # Tabloya daha fazla alan ayırdık

    with col_main:
        st.subheader("📑 İşlem Listesi")
        
        # TÜM ALANLARI İÇEREN BAŞLIKLAR (Sütun Genişlikleri Ayarlandı)
        # ID, Tarih, Tür, Hasta, Kat, Para, Tutar, Tek, Aciklama, İşlem
        cols = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
        headers = ["ID", "Tarih", "Tür", "Hasta Adi", "Kat.", "Döviz", "Tutar", "Tekn.", "Açıklama", "İşlem"]
        for col, head in zip(cols, headers):
            col.write(f"**{head}**")
        st.write("---")

        for index, row in df_visible.iterrows():
            r = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
            
            # Veri Gösterimi
            r[0].write(row.iloc[0]) # ID
            r[1].write(row.iloc[1]) # Tarih
            r[2].write(row.iloc[2]) # Tür
            r[3].write(row.iloc[3]) # Hasta Adi
            r[4].write(row.iloc[4]) # Kategori
            r[5].write(row.iloc[5]) # Para Birimi
            r[6].write(row.iloc[6]) # Tutar
            r[7].write(row.iloc[7]) # Teknisyen
            r[8].write(row.iloc[8]) # Aciklama
            
            # BUTONLAR (✏️ ve 🗑️)
            btn_e, btn_d = r[9].columns(2)
            
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Düzenle: {row.iloc[3]}")
                def edit_modal(r_data):
                    new_h = st.text_input("Hasta Adi", value=r_data.iloc[3])
                    new_t = st.number_input("Tutar", value=float(r_data.iloc[6]))
                    new_a = st.text_area("Açıklama", value=r_data.iloc[8])
                    if st.button("Kaydet"):
                        idx = df[df.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 4, new_h)
                        worksheet.update_cell(idx, 7, new_t)
                        worksheet.update_cell(idx, 9, new_a)
                        st.rerun()
                edit_modal(row)

            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                @st.dialog("Silme Onayı")
                def delete_modal(r_data):
                    st.warning(f"{r_data.iloc[3]} kaydı silinecek?")
                    if st.button("Evet, Sil"):
                        idx = df[df.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 10, "X")
                        st.rerun()
                delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("main_form", clear_on_submit=True):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Diğer"])
            f_para = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0.0)
            f_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
            f_acik = st.text_input("Açıklama")
            
            if st.form_submit_button("Sisteme Yaz"):
                try:
                    next_id = int(pd.to_numeric(df.iloc[:, 0]).max() + 1)
                except:
                    next_id = 1
                worksheet.append_row([next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, f_tut, f_tekn, f_acik, ""])
                st.success("Eklendi!")
                st.rerun()
