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

# --- 2. GÜVENLİK (GERÇEK MİNİMALİST GİRİŞ) ---
PASSWORD = "klinik2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>
            /* Arka plan gradyanı */
            .stApp {
                background: linear-gradient(135deg, #E0F2FE 0%, #F8FAFC 100%);
            }
            /* Giriş Kartı Konteynırı */
            .login-wrapper {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 60vh;
            }
            .login-card {
                background-color: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                width: 380px; /* Pencere genişliğini daralttık */
                text-align: center;
            }
            /* Input alanını güzelleştirme */
            .stTextInput input {
                border-radius: 10px !important;
                border: 1px solid #E2E8F0 !important;
                padding: 10px !important;
            }
            /* Butonu daraltma ve güzelleştirme */
            .stButton button {
                width: 100% !important;
                border-radius: 10px !important;
                background-color: #3B82F6 !important;
                color: white !important;
                height: 45px;
                font-weight: 600;
            }
            /* Streamlit varsayılan başlıklarını gizle (Giriş ekranında) */
            header {visibility: hidden;}
            </style>
        """, unsafe_allow_html=True)

        # Görseli tam ortalamak için boşluk kullanıyoruz
        st.write("<div class='login-wrapper'>", unsafe_allow_html=True)
        
        # Sadece orta sütunu kullanıp içeriği HTML kartına gömüyoruz
        _, col_mid, _ = st.columns([1, 1, 1])
        with col_mid:
            st.markdown("""
                <div class="login-card">
                    <span style='font-size: 50px;'>🏥</span>
                    <h2 style='color: #1E3A8A; margin-bottom: 5px; font-family: sans-serif;'>Klinik 2026</h2>
                    <p style='color: #64748B; font-size: 14px; margin-bottom: 25px;'>Lütfen erişim şifrenizi girin.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Form alanı (Kartın hemen altında bütünleşik görünür)
            pwd = st.text_input("Şifre", type="password", placeholder="Şifre...", label_visibility="collapsed")
            if st.button("Sisteme Giriş"):
                if pwd == PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("Hatalı şifre!")
        
        st.write("</div>", unsafe_allow_html=True)
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
    # Ana Panel İçin Temiz CSS
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; }
        [data-testid="stMetric"] {
            background-color: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-bottom: 4px solid #3B82F6;
        }
        header {visibility: visible;}
        </style>
    """, unsafe_allow_html=True)

    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()
    df['UPB_TRY'] = df.apply(lambda r: float(r['Tutar']) * kurlar.get(r['Para Birimi'], 1.0), axis=1)

    st.markdown("<h1 style='color: #1E3A8A;'>🏢 Yönetim Paneli</h1>", unsafe_allow_html=True)
    
    # ... (Buradan sonrası v28'deki çalışan kısımlar: Metrikler, Grafikler ve Tablo) ...
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    col_sel, _ = st.columns([1, 4])
    with col_sel:
        secilen_ay_adi = st.selectbox("📅 Dönem Seçin:", aylar, index=datetime.now().month - 1)
    
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

    # Tablo ve Operasyon Alanı
    st.divider()
    df_disp = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
    st.subheader(f"📑 {secilen_ay_adi} Hareketleri")
    
    # Güvenli Tablo (KeyError'u önlemek için iloc kullanıyoruz)
    c = st.columns([0.5, 1, 0.8, 1.5, 1, 0.6, 1, 1, 0.8])
    heads = ["ID", "Tarih", "Tür", "Hasta/Cari", "Kategori", "Döviz", "Tutar", "UPB", "İşlem"]
    for col, h in zip(c, heads): col.markdown(f"**{h}**")
    
    for _, row in df_disp.iterrows():
        r = st.columns([0.5, 1, 0.8, 1.5, 1, 0.6, 1, 1, 0.8])
        r[0].write(row.iloc[0])
        r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")
        r[2].write(row.iloc[2])
        r[3].write(row.iloc[3]); r[4].write(row.iloc[4]); r[5].write(row.iloc[5])
        r[6].write(format_int(float(row.iloc[6])))
        r[7].write(format_int(row['UPB_TRY']))
        if r[8].button("🗑️", key=f"del_{row.iloc[0]}"):
            idx = df_raw[df_raw.iloc[:,0] == row.iloc[0]].index[0] + 2
            worksheet.update_cell(idx, 10, "X"); st.rerun()
