import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale

# --- 0. BÖLGESEL AYAR ---
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR')
    except:
        pass

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

# --- 2. FONKSİYONLAR ---
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=5)
        root = ET.fromstring(response.content)
        rates = {'TRY': 1.0}
        for currency in root.findall('Currency'):
            code = currency.get('CurrencyCode')
            if code in ['USD', 'EUR']:
                rates[code] = float(currency.find('ForexBuying').text)
        return rates
    except:
        return {'TRY': 1.0, 'USD': 30.00, 'EUR': 33.00}

def get_gspread_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    df['Tarih_DT'] = pd.to_datetime(df['Tarih'], errors='coerce')
    df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
    
    sort_cols = ['Tarih_DT']
    if 'Yaratma Tarihi' in df.columns: sort_cols.append('Yaratma Tarihi')
    if 'Yaratma Saati' in df.columns: sort_cols.append('Yaratma Saati')
    df = df.sort_values(by=sort_cols, ascending=True)
    return df, sheet

def format_int(value):
    return f"{int(round(value)):,}".replace(",", ".")

def format_rate(value):
    return f"{value:.2f}".replace(".", ",")

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro v19", layout="wide")

if check_password():
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")
    
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    df['UPB_TRY'] = df.apply(lambda r: float(r['Tutar']) * kurlar.get(r['Para Birimi'], 1.0), axis=1)
    df_kumulatif = df[df['Tarih_DT'].dt.month <= secilen_ay_no].copy()
    
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['UPB_TRY'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"Ocak-{secilen_ay_adi} Gelir", f"{format_int(t_gelir)} ₺")
    m2.metric(f"Ocak-{secilen_ay_adi} Gider", f"{format_int(t_gider)} ₺")
    m3.metric("Net Kasa", f"{format_int(t_gelir - t_gider)} ₺")
    m4.metric("USD Kuru", f"{format_rate(kurlar['USD'])} ₺")
    m5.metric("EUR Kuru", f"{format_rate(kurlar['EUR'])} ₺")

    st.divider()

    col_main, col_side = st.columns([4.5, 1])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Detay Listesi")
        df_display = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
        
        search_term = st.text_input("🔍 Listede Ara:", "")
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
        heads = ["ID", "Tarih", "Tür", "Hasta Adi", "Kat.", "Döv", "Tutar", "UPB (TL)", "Tekn.", "Açıklama", "İşlem"]
        for col, h in zip(c, heads): col.markdown(f"**{h}**")
        st.write("---")

        for _, row in df_display.iterrows():
            color = "#2e7d32" if row['Islem Turu'] == "Gelir" else "#c62828"
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
            
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")
            r[2].markdown(f"<span style='color:{color}; font-weight:bold;'>{row.iloc[2]}</span>", unsafe_allow_html=True)
            r[3].write(row.iloc[3]); r[4].write(row.iloc[4]); r[5].write(row.iloc[5])
            r[6].write(format_int(float(row.iloc[6])))
            r[7].write(format_int(row['UPB_TRY']))
            r[8].write(row.iloc[7]); r[9].write(row.iloc[8])
            
            btn_e, btn_d = r[10].columns(2)
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Düzenle: {row.iloc[3]}")
                def edit_modal(r_data):
                    n_tar = st.date_input("Tarih", value=pd.to_datetime(r_data.iloc[1]), format="DD.MM.YYYY")
                    n_tur = st.selectbox("Tür", ["Gelir", "Gider"], index=0 if r_data.iloc[2]=="Gelir" else 1)
                    n_hast = st.text_input("Hasta/Cari", value=r_data.iloc[3])
                    n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
                    n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"], index=["TRY","USD","EUR"].index(r_data.iloc[5]))
                    n_tut = st.number_input("Tutar", value=int(float(r_data.iloc[6])), step=1)
                    n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
                    n_acik = st.text_area("Açıklama", value=r_data.iloc[8])
                    
                    if st.button("Kaydet"):
                        if n_tut <= 0: # 0 TUTAR KONTROLÜ
                            st.error("Tutar 0'dan büyük olmalıdır!")
                        else:
                            idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                            new_row = [r_data.iloc[0], str(n_tar), n_tur, n_hast, n_kat, n_para, int(n_tut), n_tekn, n_acik, ""]
                            worksheet.update(f"A{idx}:J{idx}", [new_row])
                            st.rerun()
                edit_modal(row)

            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                @st.dialog("Sil?")
                def delete_modal(r_data):
                    if st.button("Evet, Sil"):
                        idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 10, "X"); st.rerun()
                delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("form_v19", clear_on_submit=True):
            f_tar = st.date_input("Tarih", date.today(), format="DD.MM.YYYY")
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0, step=1)
            f_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
            f_acik = st.text_input("Açıklama")
            
            if st.form_submit_button("Ekle"):
                if f_tut <= 0: # 0 TUTAR KONTROLÜ
                    st.error("Tutar 0 olamaz!")
                else:
                    now = datetime.now()
                    y_tarih = now.strftime("%Y-%m-%d")
                    y_saat = now.strftime("%H:%M:%S")
                    try: next_id = int(pd.to_numeric(df_raw.iloc[:, 0]).max() + 1)
                    except: next_id = 1
                    worksheet.append_row([next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, int(f_tut), f_tekn, f_acik, "", y_tarih, y_saat])
                    st.success("Kaydedildi!"); st.rerun()
