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
        load_custom_css()
        
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🦷 Klinik 2026</div>
            <div class="login-subtitle">Diş Kliniği Yönetim Sistemi</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("🔐 Şifre", type="password", placeholder="Şifrenizi girin...")
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                if pwd == PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre! Lütfen tekrar deneyin.")
        return False
    return True

# --- 2. FONKSİYONLAR ---
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        rates = {'TRY': 1.0}
        for currency in root.findall('Currency'):
            code = currency.get('CurrencyCode')
            if code in ['USD', 'EUR', 'GBP']:
                buying_text = currency.find('ForexBuying').text
                if buying_text:
                    rates[code] = float(buying_text)
        return rates
    except Exception as e:
        st.warning(f"⚠️ Döviz kurları yüklenemedi, varsayılan değerler kullanılıyor")
        return {'TRY': 1.0, 'USD': 30.00, 'EUR': 33.00, 'GBP': 36.00}

def get_fresh_worksheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        return client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
    except Exception as e:
        st.error(f"❌ Worksheet bağlantısı başarısız: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data():
    try:
        sheet = get_fresh_worksheet()
        if sheet is None:
            return pd.DataFrame(), None
            
        data = sheet.get_all_values()
        
        if len(data) < 2:
            st.warning("⚠️ Tabloda veri bulunamadı.")
            return pd.DataFrame(), sheet
        
        df = pd.DataFrame(data[1:], columns=data[0])
        df['Tarih_DT'] = pd.to_datetime(df['Tarih'], format='%Y-%m-%d', errors='coerce')
        df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
        
        sort_cols = ['Tarih_DT']
        if 'Yaratma Tarihi' in df.columns: 
            sort_cols.append('Yaratma Tarihi')
        if 'Yaratma Saati' in df.columns: 
            sort_cols.append('Yaratma Saati')
        df = df.sort_values(by=sort_cols, ascending=True)
        return df, sheet
    except Exception as e:
        st.error(f"❌ Veri yükleme hatası: {str(e)}")
        st.stop()

def format_int(value):
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except:
        return "0"

def format_rate(value):
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except:
        return "0,00"

def load_custom_css():
    st.markdown("""
    <style>
        :root {
            --primary: #2C3E50;
            --success: #27AE60;
            --danger: #E74C3C;
            --accent: #3498DB;
            --bg-main: #F5F7FA;
            --bg-card: #FFFFFF;
            --text-dark: #2C3E50;
            --text-light: #546E7A;
            --border: #E0E6ED;
        }
        
        .stApp {
            background: linear-gradient(to bottom, #FFFFFF 0%, #F5F7FA 100%);
        }
        
        .login-container {
            max-width: 420px;
            margin: 100px auto;
            padding: 50px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            border: 1px solid var(--border);
            text-align: center;
        }
        
        .login-title {
            font-size: 36px;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 8px;
        }
        
        .login-subtitle {
            color: var(--text-light);
            margin-bottom: 30px;
            font-size: 15px;
        }
        
        [data-testid="metric-container"] {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        [data-testid="stMetricLabel"] {
            color: var(--text-light) !important;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        [data-testid="stMetricValue"] {
            color: var(--primary) !important;
            font-size: 28px;
            font-weight: 700;
        }
        
        h1 {
            color: var(--primary) !important;
            font-weight: 800;
            margin-bottom: 30px;
        }
        
        h2, h3 {
            color: var(--primary) !important;
            font-weight: 700;
        }
        
        [data-baseweb="select"] {
            border-radius: 10px;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        
        input:not([role="combobox"]), 
        textarea {
            border-radius: 8px !important;
            border: 1.5px solid var(--border) !important;
            padding: 12px !important;
            transition: all 0.3s ease;
            background: white !important;
        }
        
        input:not([role="combobox"]):focus, 
        textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.08) !important;
        }
        
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            padding: 10px 20px;
            border: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);
            color: white;
        }
        
        .stButton button[type="submit"] {
            background: linear-gradient(135deg, #27AE60 0%, #229954 100%);
            color: white;
            width: 100%;
        }
        
        button[key*="e_"] {
            background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%) !important;
            color: white !important;
            padding: 6px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
        }
        
        button[key*="d_"] {
            background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%) !important;
            color: white !important;
            padding: 6px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
        }
        
        [data-testid="stExpander"] {
            background: white;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            padding: 10px;
        }
        
        [data-testid="stMarkdownContainer"] strong {
            color: var(--primary);
            background: #F8F9FA;
            padding: 10px 0px 10px 12px;
            border-radius: 8px;
            display: inline-block;
            width: 100%;
            text-align: left;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid var(--border);
            margin: 0;
        }
        
        [data-testid="column"] > div {
            padding: 8px 0px 8px 2mm;
            text-align: left;
        }
        
        hr {
            border: none;
            height: 1px;
            background: var(--border);
            margin: 20px 0;
        }
        
        [data-testid="stForm"] {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }
        
        .element-container:has([data-testid="stForm"]) {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        
        .stAlert {
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }
        
        .gelir-badge {
            background: linear-gradient(135deg, #27AE60 0%, #229954 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 6px rgba(39, 174, 96, 0.3);
        }
        
        .gider-badge {
            background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 6px rgba(231, 76, 60, 0.3);
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .stApp > div {
            animation: fadeIn 0.4s ease-out;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #F5F7FA;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #CBD5E0;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #A0AEC0;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Analitik", layout="wide", page_icon="🦷")

if check_password():
    load_custom_css()
    
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: 
        df_raw["Silindi"] = ""
    
    df_acilis = df_raw[(df_raw["Islem Turu"] == "ACILIS") & (df_raw["Silindi"] != "X")].copy()
    df = df_raw[(df_raw["Islem Turu"] != "ACILIS") & (df_raw["Silindi"] != "X")].copy()
    
    def calculate_acilis_bakiye():
        if len(df_acilis) > 0:
            total_try = 0
            for _, row in df_acilis.iterrows():
                try:
                    tutar = float(row['Tutar'])
                    para = row['Para Birimi']
                    kur = kurlar.get(para, 1.0)
                    total_try += tutar * kur
                except:
                    pass
            return total_try
        return 0
    
    acilis_bakiye = calculate_acilis_bakiye()
    
    def safe_upb_calc(row):
        try:
            tutar = float(row['Tutar'])
            para = row['Para Birimi']
            kur = kurlar.get(para, 1.0)
            return tutar * kur
        except:
            return 0.0
    
    df['UPB_TRY'] = df.apply(safe_upb_calc, axis=1)

    st.title("🦷 Klinik 2026 Yönetim Paneli")
    
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    if secilen_ay_no == 1:
        acilis_bakiye_ay = acilis_bakiye
        acilis_detay = {}
        for _, row in df_acilis.iterrows():
            para = row['Para Birimi']
            try:
                tutar = float(row['Tutar'])
                acilis_detay[para] = acilis_detay.get(para, 0) + tutar
            except:
                pass
    else:
        df_onceki_aylar = df[df['Tarih_DT'].dt.month < secilen_ay_no].copy()
        onceki_gelir = df_onceki_aylar[df_onceki_aylar["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
        onceki_gider = df_onceki_aylar[df_onceki_aylar["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
        acilis_bakiye_ay = acilis_bakiye + onceki_gelir - onceki_gider
        
        acilis_detay = {}
        for _, row in df_acilis.iterrows():
            para = row['Para Birimi']
            try:
                tutar = float(row['Tutar'])
                acilis_detay[para] = acilis_detay.get(para, 0) + tutar
            except:
                pass
        
        for _, row in df_onceki_aylar.iterrows():
            para = row['Para Birimi']
            try:
                tutar = float(row['Tutar'])
                if row['Islem Turu'] == 'Gelir':
                    acilis_detay[para] = acilis_detay.get(para, 0) + tutar
                elif row['Islem Turu'] == 'Gider':
                    acilis_detay[para] = acilis_detay.get(para, 0) - tutar
            except:
                pass
    
    df_secilen_ay = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
    t_gelir = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
    
    gelir_detay = {}
    gider_detay = {}
    for _, row in df_secilen_ay.iterrows():
        para = row['Para Birimi']
        try:
            tutar = float(row['Tutar'])
            if row['Islem Turu'] == 'Gelir':
                gelir_detay[para] = gelir_detay.get(para, 0) + tutar
            elif row['Islem Turu'] == 'Gider':
                gider_detay[para] = gider_detay.get(para, 0) + tutar
        except:
            pass
    
    net_detay = {}
    for para in ['TRY', 'USD', 'EUR', 'GBP']:
        net_detay[para] = acilis_detay.get(para, 0) + gelir_detay.get(para, 0) - gider_detay.get(para, 0)
    
    net_kasa = acilis_bakiye_ay + t_gelir - t_gider

    m1, m2, m3, m4, m5 = st.columns(5)
    
    with m1:
        st.metric("💼 Açılış Bakiyesi", f"{format_int(acilis_bakiye_ay)} TL")
        with st.expander("Detaylar"):
            st.write(f"TRY: {format_int(acilis_detay.get('TRY', 0))} TL")
            miktar_usd = acilis_detay.get('USD', 0)
            upb_usd = miktar_usd * kurlar.get('USD', 1.0)
            st.write(f"USD: {format_int(miktar_usd)} $ ({format_int(upb_usd)} TL)")
            miktar_eur = acilis_detay.get('EUR', 0)
            upb_eur = miktar_eur * kurlar.get('EUR', 1.0)
            st.write(f"EUR: {format_int(miktar_eur)} € ({format_int(upb_eur)} TL)")
            miktar_gbp = acilis_detay.get('GBP', 0)
            upb_gbp = miktar_gbp * kurlar.get('GBP', 1.0)
            st.write(f"GBP: {format_int(miktar_gbp)} £ ({format_int(upb_gbp)} TL)")
    
    with m2:
        st.metric(f"💰 Gelir ({secilen_ay_adi})", f"{format_int(t_gelir)} TL")
        with st.expander("Detaylar"):
            st.write(f"TRY: {format_int(gelir_detay.get('TRY', 0))} TL")
            miktar_usd = gelir_detay.get('USD', 0)
            upb_usd = miktar_usd * kurlar.get('USD', 1.0)
            st.write(f"USD: {format_int(miktar_usd)} $ ({format_int(upb_usd)} TL)")
            miktar_eur = gelir_detay.get('EUR', 0)
            upb_eur = miktar_eur * kurlar.get('EUR', 1.0)
            st.write(f"EUR: {format_int(miktar_eur)} € ({format_int(upb_eur)} TL)")
            miktar_gbp = gelir_detay.get('GBP', 0)
            upb_gbp = miktar_gbp * kurlar.get('GBP', 1.0)
            st.write(f"GBP: {format_int(miktar_gbp)} £ ({format_int(upb_gbp)} TL)")
    
    with m3:
        st.metric(f"💸 Gider ({secilen_ay_adi})", f"{format_int(t_gider)} TL")
        with st.expander("Detaylar"):
            st.write(f"TRY: {format_int(gider_detay.get('TRY', 0))} TL")
            miktar_usd = gider_detay.get('USD', 0)
            upb_usd = miktar_usd * kurlar.get('USD', 1.0)
            st.write(f"USD: {format_int(miktar_usd)} $ ({format_int(upb_usd)} TL)")
            miktar_eur = gider_detay.get('EUR', 0)
            upb_eur = miktar_eur * kurlar.get('EUR', 1.0)
            st.write(f"EUR: {format_int(miktar_eur)} € ({format_int(upb_eur)} TL)")
            miktar_gbp = gider_detay.get('GBP', 0)
            upb_gbp = miktar_gbp * kurlar.get('GBP', 1.0)
            st.write(f"GBP: {format_int(miktar_gbp)} £ ({format_int(upb_gbp)} TL)")
    
    with m4:
        st.metric("💵 Net Kasa", f"{format_int(net_kasa)} TL")
        with st.expander("Detaylar"):
            st.write(f"TRY: {format_int(net_detay.get('TRY', 0))} TL")
            miktar_usd = net_detay.get('USD', 0)
            upb_usd = miktar_usd * kurlar.get('USD', 1.0)
            st.write(f"USD: {format_int(miktar_usd)} $ ({format_int(upb_usd)} TL)")
            miktar_eur = net_detay.get('EUR', 0)
            upb_eur = miktar_eur * kurlar.get('EUR', 1.0)
            st.write(f"EUR: {format_int(miktar_eur)} € ({format_int(upb_eur)} TL)")
            miktar_gbp = net_detay.get('GBP', 0)
            upb_gbp = miktar_gbp * kurlar.get('GBP', 1.0)
            st.write(f"GBP: {format_int(miktar_gbp)} £ ({format_int(upb_gbp)} TL)")
    
    with m5:
        st.metric("💱 Döviz Kurları", "TCMB")
        with st.expander("Detaylar"):
            st.write(f"USD: {format_rate(kurlar.get('USD', 0))} TL")
            st.write(f"EUR: {format_rate(kurlar.get('EUR', 0))} TL")
            st.write(f"GBP: {format_rate(kurlar.get('GBP', 0))} TL")

    with st.expander("📊 Grafiksel Analizleri Göster/Gizle", expanded=False):
        df_trends = df.copy()
        df_trends['Ay_No'] = df_trends['Tarih_DT'].dt.month
        df_trends['Ay_Ad'] = df_trends['Tarih_DT'].dt.strftime('%B')
        
        trend_summary = df_trends.groupby(['Ay_No', 'Ay_Ad', 'Islem Turu'])['UPB_TRY'].sum().reset_index()
        trend_summary = trend_summary.sort_values('Ay_No')

        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.line(trend_summary, x='Ay_Ad', y='UPB_TRY', color='Islem Turu', 
                          title="Aylık Gelir/Gider Trendi", markers=True)
            fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = px.pie(df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gelir"], 
                         values='UPB_TRY', names='Kategori', 
                         title=f"Gelir Dağılımı ({secilen_ay_adi})", hole=0.4)
            fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig2, use_container_width=True)

        g3, g4 = st.columns(2)
        with g3:
            df_kasa = trend_summary.pivot(index='Ay_Ad', columns='Islem Turu', values='UPB_TRY').fillna(0)
            if 'Gelir' in df_kasa and 'Gider' in df_kasa:
                df_kasa['Net'] = df_kasa['Gelir'] - df_kasa['Gider']
                df_kasa['Kumulatif'] = df_kasa['Net'].cumsum()
                fig3 = px.area(df_kasa.reset_index(), x='Ay_Ad', y='Kumulatif', title="Kasa Büyüme Trendi")
                fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                st.plotly_chart(fig3, use_container_width=True)
        with g4:
            fig4 = px.pie(df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gider"], 
                         values='UPB_TRY', names='Kategori', 
                         title=f"Gider Dağılımı ({secilen_ay_adi})", hole=0.4)
            fig4.update_layout(plot_bgcolor='white', paper_bgcolor='white')
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    col_main, col_side = st.columns([4.5, 1])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Hareketleri")
        df_display = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
        
        search_term = st.text_input("🔍 Hızlı Arama:", "", placeholder="Hasta adı, kategori veya tutar...")
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
        heads = ["ID", "Tarih", "Tür", "Hasta Adı", "Kat.", "Döv", "Tutar", "UPB", "Tekn.", "Açıklama", "İşlem"]
        for col, h in zip(c, heads): 
            col.markdown(f"**{h}**")
        st.write("---")

        def show_edit_modal(row_data):
            @st.dialog(f"✏️ Düzenle: {row_data.get('Hasta Adi', 'Kayıt')}")
            def edit_modal():
                n_hast = st.text_input("Hasta/Cari Adı", value=str(row_data.get('Hasta
