import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale
from google.oauth2.service_account import Credentials
import gspread

# --- 0. OTOMATIK PAKET KONTROLÜ ---
try:
    import plotly.express as px
except ImportError:
    os.system('pip install plotly')
    import plotly.express as px

# --- 1. BÖLGESEL AYAR ---
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR')
    except:
        pass

# --- 2. GÜVENLİK ---
PASSWORD = "klinik2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>
            .stApp { background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); }
            .login-container {
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                padding: 40px; background: white; border-radius: 24px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); margin-top: 10vh;
            }
            </style>
        """, unsafe_allow_html=True)

        _, col_mid, _ = st.columns([1, 2, 1])
        with col_mid:
            st.markdown("""
                <div class="login-container">
                    <h1 style='text-align: center; font-size: 50px; margin-bottom: 0;'>🏥</h1>
                    <h2 style='text-align: center; color: #1E3A8A; margin-top: 10px;'>Klinik 2026</h2>
                    <p style='text-align: center; color: #64748B; margin-bottom: 30px;'>Hoş geldiniz, şifrenizi giriniz.</p>
                </div>
            """, unsafe_allow_html=True)
            pwd = st.text_input("Şifre", type="password", placeholder="Şifre...", label_visibility="collapsed")
            if st.button("Sisteme Giriş", use_container_width=True):
                if pwd == PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")
        return False
    return True

# --- 3. FONKSİYONLAR ---
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
    df = df.sort_values(by=['Tarih_DT'], ascending=True)
    return df, sheet

def format_int(value):
    return f"{int(round(value)):,}".replace(",", ".")

def format_rate(value):
    return f"{value:.2f}".replace(".", ",")

# --- 4. ANA PANEL ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide", page_icon="🏥")

if check_password():
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; }
        [data-testid="stMetric"] {
            background-color: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-bottom: 4px solid #3B82F6;
        }
        .stButton>button { border-radius: 8px; font-weight: 600; }
        h1, h2, h3 { color: #1E3A8A !important; font-family: 'Inter', sans-serif; }
        </style>
    """, unsafe_allow_html=True)

    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()
    df['UPB_TRY'] = df.apply(lambda r: float(r['Tutar']) * kurlar.get(r['Para Birimi'], 1.0), axis=1)

    st.markdown("<h1>🏢 Yönetim Paneli</h1>", unsafe_allow_html=True)
    
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    col_sel, _ = st.columns([1, 4])
    with col_sel:
        secilen_ay_adi = st.selectbox("📅 Dönem:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    df_kumulatif = df[df['Tarih_DT'].dt.month <= secilen_ay_no].copy()
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['UPB_TRY'].sum()

    m = st.columns(5)
    m[0].metric("Toplam Gelir", f"{format_int(t_gelir)} ₺")
    m[1].metric("Toplam Gider", f"{format_int(t_gider)} ₺")
    m[2].metric("Net Kasa", f"{format_int(t_gelir - t_gider)} ₺")
    m[3].metric("USD Kuru", f"{format_rate(kurlar['USD'])} ₺")
    m[4].metric("EUR Kuru", f"{format_rate(kurlar['EUR'])} ₺")

    # Grafik Paneli (v24'teki 4 grafik düzeni)
    with st.expander("📊 Grafiksel Analizler"):
        df_trends = df.copy()
        df_trends['Ay'] = df_trends['Tarih_DT'].dt.strftime('%m-%B')
        ts = df_trends.groupby(['Ay', 'Islem Turu'])['UPB_TRY'].sum().reset_index()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.line(ts, x='Ay', y='UPB_TRY', color='Islem Turu', title="Trend", markers=True, color_discrete_map={"Gelir": "#10B981", "Gider": "#EF4444"}), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"], values='UPB_TRY', names='Kategori', title="Gelir Dağılımı", hole=0.4), use_container_width=True)

    st.divider()

    # Operasyonel Alan
    col_main, col_side = st.columns([4.2, 1.2])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Hareket Detayları")
        df_display = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
        search_term = st.text_input("🔍 Hızlı İşlem Arama...", "")
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        # Manuel Tablo Tasarımı (Hataları önlemek için sütun isimlerini index ile çekiyoruz)
        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 1.0, 0.8])
        heads = ["ID", "Tarih", "Tür", "Hasta/Cari", "Kat.", "Döv", "Tutar", "UPB", "Açıklama", "İşlem"]
        for col, h in zip(c, heads): col.markdown(f"**{h}**")
        st.write("---")

        for _, row in df_display.iterrows():
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 1.0, 0.8])
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")
            color = "#10B981" if row['Islem Turu'] == "Gelir" else "#EF4444"
            r[2].markdown(f"<span style='color:{color}; font-weight:600;'>{row.iloc[2]}</span>", unsafe_allow_html=True)
            r[3].write(row.iloc[3]); r[4].write(row.iloc[4]); r[5].write(row.iloc[5])
            r[6].write(format_int(float(row.iloc[6])))
            r[7].write(format_int(row['UPB_TRY']))
            r[8].write(row.iloc[8])
            
            be, bd = r[9].columns(2)
            if be.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog("Güncelle")
                def edit_modal(r_data):
                    n_hast = st.text_input("Ad", value=r_data.iloc[3])
                    n_tut = st.number_input("Tutar", value=int(float(r_data.iloc[6])))
                    if st.button("Kaydet"):
                        idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 4, n_hast)
                        worksheet.update_cell(idx, 7, int(n_tut))
                        st.rerun()
                edit_modal(row)
            if bd.button("🗑️", key=f"d_{row.iloc[0]}"):
                idx = df_raw[df_raw.iloc[:,0] == row.iloc[0]].index[0] + 2
                worksheet.update_cell(idx, 10, "X"); st.rerun()

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_islem_v27"):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari Adı")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0, step=1)
            f_acik = st.text_input("Açıklama")
            if st.form_submit_button("Sisteme Kaydet", use_container_width=True):
                if f_tut > 0:
                    worksheet.append_row([int(pd.to_numeric(df_raw.iloc[:, 0]).max() + 1), str(f_tar), f_tur, f_hast, f_kat, f_para, int(f_tut), "YOK", f_acik, "", datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")])
                    st.rerun()
