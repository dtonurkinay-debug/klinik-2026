import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import date
import requests
import xml.etree.ElementTree as ET

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

# --- 2. KUR VE BAĞLANTI FONKSİYONLARI ---
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml")
        root = ET.fromstring(response.content)
        rates = {'TRY': 1.0}
        for currency in root.findall('Currency'):
            code = currency.get('CurrencyCode')
            if code in ['USD', 'EUR']:
                rates[code] = float(currency.find('ForexBuying').text)
        return rates
    except:
        return {'TRY': 1.0, 'USD': 30.0, 'EUR': 33.0} # Hata anında yedek değerler

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce')
    df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
    return df, sheet

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro v13", layout="wide")

if check_password():
    df, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df.columns: df["Silindi"] = ""
    df = df[df["Silindi"] != "X"].copy()

    # --- HEADER / FİLTRELEME ---
    st.title("📊 Klinik 2026 Finans Yönetimi")
    
    # Ay Filtresi
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    mevcut_ay_idx = date.today().month - 1
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=mevcut_ay_idx)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    # Hesaplama: Seçilen aya kadar olan kümülatif veri (Örn: Ocak'tan Mayıs'a)
    df_kumulatif = df[df['Tarih'].dt.month <= secilen_ay_no].copy()
    
    # TRY Çevrimi ile Hesaplama
    def to_try(row):
        return row['Tutar'] * kurlar.get(row['Para Birimi'], 1.0)
    
    df_kumulatif['Tutar_TRY'] = df_kumulatif.apply(to_try, axis=1)
    
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['Tutar_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['Tutar_TRY'].sum()

    # METRİKLER (Header)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"Ocak-{secilen_ay_adi} Gelir", f"{t_gelir:,.2f} ₺")
    m2.metric(f"Ocak-{secilen_ay_adi} Gider", f"{t_gider:,.2f} ₺")
    m3.metric("Net Kasa (TRY)", f"{(t_gelir - t_gider):,.2f} ₺")
    m4.metric("USD Kuru", f"{kurlar['USD']} ₺")
    m5.metric("EUR Kuru", f"{kurlar['EUR']} ₺")

    st.divider()

    # --- LİSTELEME (Sadece Seçilen Ay) ---
    df_aylik = df[df['Tarih'].dt.month == secilen_ay_no].copy()

    col_main, col_side = st.columns([4, 1])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Hareketleri")
        cols = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
        headers = ["ID", "Tarih", "Tür", "Hasta Adi", "Kat.", "Döviz", "Tutar", "Tekn.", "Açıklama", "İşlem"]
        for col, head in zip(cols, headers): col.write(f"**{head}**")
        st.write("---")

        for index, row in df_aylik.iterrows():
            r = st.columns([0.4, 0.8, 0.7, 1.2, 0.8, 0.5, 0.7, 0.7, 1.2, 0.8])
            r[0].write(row.iloc[0])
            r[1].write(row.iloc[1].strftime('%Y-%m-%d') if pd.notnull(row.iloc[1]) else "")
            r[2].write(row.iloc[2]); r[3].write(row.iloc[3]); r[4].write(row.iloc[4])
            r[5].write(row.iloc[5]); r[6].write(row.iloc[6]); r[7].write(row.iloc[7]); r[8].write(row.iloc[8])
            
            btn_e, btn_d = r[9].columns(2)
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Düzenle: {row.iloc[3]}")
                def edit_modal(r_data):
                    n_tar = st.date_input("Tarih", value=pd.to_datetime(r_data.iloc[1]))
                    n_tur = st.selectbox("Tür", ["Gelir", "Gider"], index=0 if r_data.iloc[2]=="Gelir" else 1)
                    n_hast = st.text_input("Hasta/Cari", value=r_data.iloc[3])
                    n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Diğer"])
                    n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"], index=["TRY","USD","EUR"].index(r_data.iloc[5]))
                    n_tut = st.number_input("Tutar", value=float(r_data.iloc[6]))
                    n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
                    n_acik = st.text_area("Açıklama", value=r_data.iloc[8])
                    if st.button("Güncelle"):
                        idx = df[df.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        new_row = [r_data.iloc[0], str(n_tar), n_tur, n_hast, n_kat, n_para, n_tut, n_tekn, n_acik, ""]
                        worksheet.update(f"A{idx}:J{idx}", [new_row])
                        st.rerun()
                edit_modal(row)

            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                @st.dialog("Sil?")
                def delete_modal(r_data):
                    if st.button("Evet, Sil"):
                        idx = df[df.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 10, "X"); st.rerun()
                delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("form_v13", clear_on_submit=True):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0.0)
            f_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
            f_acik = st.text_input("Açıklama")
            if st.form_submit_button("Kaydet"):
                try: next_id = int(pd.to_numeric(df.iloc[:, 0]).max() + 1)
                except: next_id = 1
                worksheet.append_row([next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, f_tut, f_tekn, f_acik, ""])
                st.success("Eklendi!"); st.rerun()
