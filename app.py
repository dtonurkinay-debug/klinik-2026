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
st.set_page_config(page_title="Klinik 2026 Pro v11", layout="wide")

if check_password():
    df, worksheet = load_data()
    
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

    col_main, col_side = st.columns([4, 1])

    with col_main:
        st.subheader("📑 İşlem Listesi")
        cols = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
        headers = ["ID", "Tarih", "Tür", "Hasta Adi", "Kat.", "Döviz", "Tutar", "Tekn.", "Açıklama", "İşlem"]
        for col, head in zip(cols, headers):
            col.write(f"**{head}**")
        st.write("---")

        for index, row in df_visible.iterrows():
            r = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
            r[0].write(row.iloc[0])
            r[1].write(row.iloc[1])
            r[2].write(row.iloc[2])
            r[3].write(row.iloc[3])
            r[4].write(row.iloc[4])
            r[5].write(row.iloc[5])
            r[6].write(row.iloc[6])
            r[7].write(row.iloc[7])
            r[8].write(row.iloc[8])
            
            btn_e, btn_d = r[9].columns(2)
            
            # --- DÜZENLEME POP-UP (TAM LİSTE) ---
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Kayıt Düzenle (ID: {row.iloc[0]})")
                def edit_modal(r_data):
                    st.info(f"Düzenlenen Kayıt ID: {r_data.iloc[0]}") # Only-view ID
                    
                    # Düzenlenebilir Alanlar
                    n_tarih = st.date_input("Tarih", value=pd.to_datetime(r_data.iloc[1]))
                    n_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], index=0 if r_data.iloc[2]=="Gelir" else 1)
                    n_hasta = st.text_input("Hasta/Cari Adı", value=r_data.iloc[3])
                    n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"], index=0)
                    n_doviz = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"], index=0 if r_data.iloc[5]=="TRY" else 1)
                    n_tutar = st.number_input("Tutar", value=float(r_data.iloc[6]))
                    n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"], index=0)
                    n_acik = st.text_area("Açıklama", value=r_data.iloc[8])
                    
                    if st.button("✅ Değişiklikleri Kaydet"):
                        idx = df[df.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        # Google Sheets Sütun Güncellemeleri
                        updates = [
                            {'range': f'B{idx}', 'values': [[str(n_tarih)]]},
                            {'range': f'C{idx}', 'values': [[n_tur]]},
                            {'range': f'D{idx}', 'values': [[n_hasta]]},
                            {'range': f'E{idx}', 'values': [[n_kat]]},
                            {'range': f'F{idx}', 'values': [[n_doviz]]},
                            {'range': f'G{idx}', 'values': [[n_tutar]]},
                            {'range': f'H{idx}', 'values': [[n_tekn]]},
                            {'range': f'I{idx}', 'values': [[n_acik]]}
                        ]
                        for update in updates:
                            worksheet.update(update['range'], update['values'])
                        st.success("Kayıt başarıyla güncellendi!")
                        st.rerun()
                edit_modal(row)

            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                @st.dialog("Silme Onayı")
                def delete_modal(r_data):
                    st.warning(f"{r_data.iloc[3]} (ID: {r_data.iloc[0]}) kaydı silinecek?")
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
                worksheet.append_row([next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, f_tut, f_tekn, f_acik
