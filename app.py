import os
try:
    import plotly
except ImportError:
    os.system('pip install plotly')

import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale
import plotly.express as px 

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
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Klinik 2026 Girişi</h2>", unsafe_allow_html=True)
        pwd = st.text_input("Şifre:", type="password")
        if st.button("Giriş Yap"):
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
    df = df.sort_values(by=['Tarih_DT'], ascending=True)
    return df, sheet

def format_int(value):
    return f"{int(round(value)):,}".replace(",", ".")

def format_rate(value):
    return f"{value:.2f}".replace(".", ",")

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide")

# --- CUSTOM CSS (TASARIM KATMANI) ---
st.markdown("""
    <style>
    /* Genel Arka Plan ve Font */
    .stApp { background-color: #F8FAFC; }
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; color: #1E293B; }
    
    /* Metrik Kartları */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border-bottom: 4px solid #3B82F6;
    }
    
    /* Buton Tasarımları */
    .stButton>button {
        border-radius: 8px;
        background-color: #3B82F6;
        color: white;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        transform: translateY(-1px);
    }
    
    /* Başlıklar */
    h1, h2, h3 { color: #1E3A8A !important; font-weight: 700 !important; }
    
    /* Expander Tasarımı */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
    }
    </style>
    """, unsafe_allow_html=True)

if check_password():
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()
    df['UPB_TRY'] = df.apply(lambda r: float(r['Tutar']) * kurlar.get(r['Para Birimi'], 1.0), axis=1)

    # Başlık Alanı
    st.markdown("<h1 style='text-align: left; margin-bottom: 25px;'>🏢 Klinik 2026 Finansal Yönetim</h1>", unsafe_allow_html=True)
    
    # Ay Seçimi ve Metrikler
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    col_sel, col_empty = st.columns([1, 4])
    with col_sel:
        secilen_ay_adi = st.selectbox("📅 Dönem Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    df_kumulatif = df[df['Tarih_DT'].dt.month <= secilen_ay_no].copy()
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['UPB_TRY'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"Toplam Gelir", f"{format_int(t_gelir)} ₺")
    m2.metric(f"Toplam Gider", f"{format_int(t_gider)} ₺")
    m3.metric("Net Durum", f"{format_int(t_gelir - t_gider)} ₺")
    m4.metric("USD Buy", f"{format_rate(kurlar['USD'])} ₺")
    m5.metric("EUR Buy", f"{format_rate(kurlar['EUR'])} ₺")

    st.markdown("<br>", unsafe_allow_html=True)

    # Analiz Paneli
    with st.expander("📊 Grafiksel Analiz Paneli"):
        df_trends = df.copy()
        df_trends['Ay'] = df_trends['Tarih_DT'].dt.strftime('%m-%B')
        trend_summary = df_trends.groupby(['Ay', 'Islem Turu'])['UPB_TRY'].sum().reset_index()

        cg1, cg2 = st.columns(2)
        with cg1:
            fig_line = px.line(trend_summary, x='Ay', y='UPB_TRY', color='Islem Turu', 
                              title="Nakit Akış Trendi", markers=True, 
                              color_discrete_map={"Gelir": "#10B981", "Gider": "#EF4444"},
                              template="plotly_white")
            st.plotly_chart(fig_line, use_container_width=True)
        with cg2:
            df_gelir_kat = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]
            fig_pie = px.pie(df_gelir_kat, values='UPB_TRY', names='Kategori', title="Gelir Dağılımı",
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Operasyonel Alan
    col_main, col_side = st.columns([4.2, 1.2])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Hareketleri")
        df_display = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
        search_term = st.text_input("🔍 Hızlı İşlem Arama...", "")
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        # Tablo
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
            
            # Düzenle/Sil Butonları
            be, bd = r[9].columns(2)
            if be.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog("Kayıt Güncelleme")
                def edit_modal(r_data):
                    n_hast = st.text_input("Hasta/Cari Adı", value=r_data.iloc[3])
                    n_tar = st.date_input("Tarih", value=pd.to_datetime(r_data.iloc[1]))
                    n_tut = st.number_input("Tutar", value=int(float(r_data.iloc[6])), step=1)
                    if st.button("Değişiklikleri Kaydet"):
                        if n_tut <= 0: st.error("Tutar 0 olamaz!")
                        else:
                            idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                            worksheet.update_cell(idx, 4, n_hast)
                            worksheet.update_cell(idx, 2, str(n_tar))
                            worksheet.update_cell(idx, 7, int(n_tut))
                            st.rerun()
                edit_modal(row)
            if bd.button("🗑️", key=f"d_{row.iloc[0]}"):
                idx = df_raw[df_raw.iloc[:,0] == row.iloc[0]].index[0] + 2
                worksheet.update_cell(idx, 10, "X"); st.rerun()

    with col_side:
        st.markdown("<div style='background-color:#FFFFFF; padding:20px; border-radius:12px; border: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        st.subheader("➕ Yeni İşlem")
        with st.form("form_v23", clear_on_submit=True):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari Adı")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0, step=1)
            f_acik = st.text_input("Açıklama")
            if st.form_submit_button("Sisteme Kaydet", use_container_width=True):
                if f_tut <= 0: st.error("Tutar 0 olamaz!")
                else:
                    now = datetime.now()
                    worksheet.append_row([int(pd.to_numeric(df_raw.iloc[:, 0]).max() + 1), str(f_tar), f_tur, f_hast, f_kat, f_para, int(f_tut), "YOK", f_acik, "", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")])
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
