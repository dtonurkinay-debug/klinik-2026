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

# --- 2. BAĞLANTI VE VERİ ---
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

SHEET_ID = "1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM" 

def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_values() # Tüm veriyi saf haliyle al
    df = pd.DataFrame(data[1:], columns=data[0]) # İlk satırı başlık yap
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

if check_password():
    df, worksheet = load_data()
    
    # Silindi sütunu kontrolü (J sütunu / 10. sütun)
    if "Silindi" not in df.columns:
        df["Silindi"] = ""
    
    # Filtreleme: Boş olanları veya 'X' olmayanları göster
    df_visible = df[df["Silindi"] != "X"].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")

    # ÜST METRİKLER
    try:
        df_visible["Tutar"] = pd.to_numeric(df_visible["Tutar"], errors='coerce').fillna(0)
        t_gelir = df_visible[df_visible["Islem Turu"] == "Gelir"]["Tutar"].sum()
        t_gider = df_visible[df_visible["Islem Turu"] == "Gider"]["Tutar"].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Gelir", f"{t_gelir:,.2f} ₺")
        m2.metric("Toplam Gider", f"{t_gider:,.2f} ₺")
        m3.metric("Net Kasa", f"{(t_gelir - t_gider):,.2f} ₺")
    except:
        st.warning("Rakamlar hesaplanırken bir hata oluştu, lütfen veri formatını kontrol edin.")

    st.divider()

    # ANA DÜZEN
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.subheader("📑 İşlem Listesi")
        
        # TABLO BAŞLIĞI
        h1, h2, h3, h4, h5 = st.columns([0.5, 2.5, 1, 1, 1])
        h1.markdown("**ID**")
        h2.markdown("**Hasta Adı**")
        h3.markdown("**Tutar**")
        h4.markdown("**Tür**")
        h5.markdown("**İşlemler**")
        st.write("---")

        # VERİ SATIRLARI
        for index, row in df_visible.iterrows():
            r1, r2, r3, r4, r5 = st.columns([0.5, 2.5, 1, 1, 1])
            
            # Verileri güvenli şekilde çek
            row_id = row.iloc[0] # ID her zaman ilk sütun
            h_adi = row.iloc[3]  # Hasta Adı genellikle 4. sütun
            tutar = row.iloc[6]  # Tutar genellikle 7. sütun
            tur = row.iloc[2]    # Tür genellikle 3. sütun
            
            r1.write(f"#{row_id}")
            r2.write(h_adi)
            r3.write(f"{tutar} ₺")
            r4.write(tur)
            
            # BUTONLAR (Yan Yana)
            btn_col_e, btn_col_d = r5.columns(2)
            
            if btn_col_e.button("✏️", key=f"edit_{row_id}"):
                @st.dialog(f"Düzenle: {h_adi}")
                def edit_row(current_row):
                    n_adi = st.text_input("Yeni Hasta Adı", value=current_row.iloc[3])
                    n_tutar = st.number_input("Yeni Tutar", value=float(current_row.iloc[6]))
                    if st.button("Güncellemeyi Kaydet"):
                        # Sheets'te ID'ye göre satırı bul (ID sütunu üzerinden)
                        row_idx = df[df.iloc[:, 0] == current_row.iloc[0]].index[0] + 2
                        worksheet.update_cell(row_idx, 4, n_adi) # 4. sütun Hasta Adı
                        worksheet.update_cell(row_idx, 7, n_tutar) # 7. sütun Tutar
                        st.success("Güncellendi!")
                        st.rerun()
                edit_row(row)

            if btn_col_d.button("🗑️", key=f"del_{row_id}"):
                @st.dialog("Kaydı Sil")
                def delete_row(current_row):
                    st.error(f"**{current_row.iloc[3]}** kaydını silmek istediğinize emin misiniz?")
                    if st.button("Evet, Silinsin"):
                        row_idx = df[df.iloc[:, 0] == current_row.iloc[0]].index[0] + 2
                        worksheet.update_cell(row_idx, 10, "X") # 10. sütun Silindi
                        st.success("Silindi işaretlendi!")
                        st.rerun()
                delete_row(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_islem_formu", clear_on_submit=True):
            f_tarih = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Diğer"])
            f_tutar = st.number_input("Tutar", min_value=0.0)
            f_doviz = st.selectbox("Döviz", ["TRY", "USD", "EUR"])
            
            if st.form_submit_button("Sisteme İşle"):
                # Yeni ID: Mevcut ID'lerin en büyüğü + 1
                try:
                    next_id = int(pd.to_numeric(df.iloc[:, 0]).max() + 1)
                except:
                    next_id = 1
                
                # Google Sheets'e 10 sütunluk tam satır gönder
                worksheet.append_row([next_id, str(f_tarih), f_tur, f_cari, f_kat, f_doviz, f_tutar, "", "Uygulama", ""])
                st.success("Kayıt Başarılı!")
                st.rerun()
