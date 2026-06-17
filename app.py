import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale
import plotly.express as px

# --- 0. MODERN CSS STİLLERİ ---
def load_custom_css():
    st.markdown("""
    <style>
        /* Ana Tema Renkleri - Minimal Beyaz Dental */
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
        
        /* Genel Arkaplan - Temiz Beyaz */
        .stApp {
            background: linear-gradient(to bottom, #FFFFFF 0%, #F5F7FA 100%);
        }
        
        /* Login Ekranı */
        .login-container {
            max-width: 380px;
            margin: 80px auto;
            padding: 35px 40px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            border: 1px solid var(--border);
            text-align: center;
        }
        
        .login-title {
            font-size: 28px;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 6px;
        }
        
        .login-subtitle {
            color: var(--text-light);
            margin-bottom: 24px;
            font-size: 14px;
        }
        
        /* Metrik Kartları - Beyaz Kartlar */
        [data-testid="metric-container"] {
            background: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        /* Para Birimi Detay Kutusu */
        .currency-detail {
            background: #F8F9FA;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
            transition: max-height 0.4s ease-in-out, opacity 0.4s ease-in-out;
        }
        
        .currency-detail.collapsed {
            max-height: 0;
            opacity: 0;
            padding: 0;
            margin: 0;
        }
        
        .currency-detail.expanded {
            max-height: 300px;
            opacity: 1;
        }
        
        .currency-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 14px;
            color: var(--text-dark);
        }
        
        .currency-label {
            font-weight: 600;
        }
        
        /* Mini Toggle Button */
        .mini-toggle {
            background: transparent !important;
            border: none !important;
            cursor: pointer;
            font-size: 18px;
            padding: 0 !important;
            margin: 0 !important;
            transition: transform 0.3s ease;
            box-shadow: none !important;
        }
        
        .mini-toggle:hover {
            transform: scale(1.3);
            background: transparent !important;
        }
        
        .mini-toggle:focus {
            outline: none !important;
            box-shadow: none !important;
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
        
        /* Başlıklar */
        h1 {
            color: var(--primary) !important;
            font-weight: 700 !important;
            font-size: 20px !important;
            margin-bottom: 5px !important;
            margin-top: 0px !important;
        }
        
        h2 {
            color: var(--primary) !important;
            font-weight: 700 !important;
            font-size: 18px !important;
            margin-bottom: 10px !important;
        }
        
        h3 {
            color: var(--primary) !important;
            font-weight: 700;
            font-size: 16px !important;
        }
        
        /* Selectbox */
        [data-baseweb="select"] {
            border-radius: 8px;
            border: 1px solid var(--border) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            max-width: 250px;
        }
        
        /* Input Alanları - Selectbox hariç */
        input:not([role="combobox"]), 
        textarea {
            border-radius: 8px !important;
            border: 1.5px solid var(--border) !important;
            padding: 8px 12px !important;
            transition: all 0.3s ease;
            background: white !important;
            font-size: 14px !important;
        }
        
        input:not([role="combobox"]):focus, 
        textarea:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.08) !important;
        }
        
        /* Butonlar - Genel */
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
        
        /* Toggle Butonu - Özel stil */
        button[key="toggle_kurlar"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 4px 8px !important;
            font-size: 18px !important;
        }
        
        button[key="toggle_kurlar"]:hover {
            transform: scale(1.15) !important;
            box-shadow: none !important;
        }
        
        /* Giriş Butonu */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);
            color: white;
        }
        
        /* Form Submit Butonu */
        .stButton button[type="submit"] {
            background: linear-gradient(135deg, #27AE60 0%, #229954 100%);
            color: white;
            width: 100%;
        }
        
        /* Düzenle Butonu */
        button[key*="e_"] {
            background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%) !important;
            color: white !important;
            padding: 6px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
        }
        
        /* Sil Butonu */
        button[key*="d_"] {
            background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%) !important;
            color: white !important;
            padding: 6px 14px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
        }
        
        /* Expander */
        [data-testid="stExpander"] {
            background: white;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            padding: 10px;
        }
        
        /* Tablo Başlıkları - Sol padding eklendi */
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
        
        /* Tablo satırları için tutarlı padding */
        [data-testid="column"] > div {
            padding: 4px 0px 4px 2mm;
            text-align: left;
        }
        
        /* Divider */
        hr {
            border: none;
            height: 1px;
            background: var(--border);
            margin: 10px 0;
        }
        
        /* Form Container */
        [data-testid="stForm"] {
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }
        
        /* Yan Panel (Yeni Kayıt) - STICKY */
        .element-container:has([data-testid="stForm"]) {
            background: white;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            position: sticky;
            top: 20px;
            max-height: calc(100vh - 40px);
            overflow-y: auto;
        }
        
        /* Uyarı Mesajları */
        .stAlert {
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }
        
        /* Success Badge - Gelir */
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
        
        /* Yellow Badge - Döviz Dönüşümü */
        .doviz-badge {
            background: linear-gradient(135deg, #F39C12 0%, #D68910 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 12px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 6px rgba(243, 156, 18, 0.3);
        }
        
        /* Danger Badge - Gider */
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
        
        /* Tablo Satırları */
        .element-container {
            padding: 2px 0;
        }
        
        /* Veri Satırları Hover */
        .element-container:hover {
            background: #F8F9FA;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        /* Animasyonlar */
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
        
        /* Scrollbar Styling */
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

# --- 1. BÖLGESEL AYAR ---
try:
    locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR')
    except:
        pass  # Sessizce geç, uyarı gösterme

# --- 2. GÜVENLİK VE YETKİLENDİRME ---
def check_password():
    """Kullanıcı girişi ve yetkilendirme"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        load_custom_css()
        
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🦷 Gelir-Gider Takip 2026</div>
            <div class="login-subtitle">Diş Kliniği Yönetim Sistemi</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Login formu
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("👤 Kullanıcı Adı", placeholder="admin, desk1 veya desk2")
            pwd = st.text_input("🔐 Şifre", type="password", placeholder="Şifrenizi girin...")
            
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                # Kullanıcı kontrolü
                if username in st.secrets["users"]:
                    if pwd == st.secrets["users"][username]:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = st.secrets["roles"][username]
                        st.success(f"✅ Hoş geldiniz, {username.upper()}!")
                        st.rerun()
                    else:
                        st.error("❌ Hatalı şifre!")
                else:
                    st.error("❌ Kullanıcı bulunamadı!")
        return False
    return True

def logout():
    """Çıkış yap"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# --- 3. FONKSİYONLAR ---
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        rates = {'TRY': 1.0}
        for currency in root.findall('Currency'):
            code = currency.get('CurrencyCode')
            if code in ['USD', 'EUR', 'GBP']:  # GBP eklendi
                buying_text = currency.find('ForexBuying').text
                if buying_text:
                    rates[code] = float(buying_text)
        return rates
    except Exception as e:
        st.warning(f"⚠️ Döviz kurları yüklenemedi, varsayılan değerler kullanılıyor")
        return {'TRY': 1.0, 'USD': 30.00, 'EUR': 33.00, 'GBP': 36.00}  # GBP default

def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Google Sheets bağlantısı başarısız: {str(e)}")
        st.stop()

@st.cache_data(ttl=60)  # Cache süresini 5 dakikadan 1 dakikaya düşürdüm
def load_data():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
        data = sheet.get_all_values()
        
        if len(data) < 2:
            st.warning("⚠️ Tabloda veri bulunamadı.")
            return pd.DataFrame(), sheet
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Tarih parse - ISO format için özel
        df['Tarih_DT'] = pd.to_datetime(df['Tarih'], format='%Y-%m-%d', errors='coerce')
        
        df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
        
        sort_cols = ['Tarih_DT']
        if 'Yaratma Tarihi' in df.columns: sort_cols.append('Yaratma Tarihi')
        if 'Yaratma Saati' in df.columns: sort_cols.append('Yaratma Saati')
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

# --- KATEGORI FONKSİYONLARI ---
def get_gelir_kategorileri():
    """Gelir kategorilerini döndür (alfabetik sıralı, prefix ile)"""
    base = ["Klinik Hastası", "Teknisyen Hastası"]
    return sorted([f"{k} (Gelir)" for k in base])

def get_gider_kategorileri():
    """Gider kategorilerini döndür (alfabetik sıralı, prefix ile)"""
    base = ["Kira", "Aidat", "E-Ödeme", "Personel Maaşı", "Laboratuvar", 
            "Implant", "Malzeme", "Mutfak", "Yemek", "Onur", "Birikim", 
            "Komisyon", "Diğer"]
    return sorted([f"{k} (Gider)" for k in base])

def get_teknisyen_listesi():
    """Teknisyen listesini döndür (alfabetik sıralı)"""
    return sorted(["Ali", "Cihat", "Murat", "Onur", "Diğer"])

def clean_kategori(kat_with_prefix):
    """Kategori isminden (Gelir)/(Gider) prefix'ini temizle"""
    if " (Gelir)" in kat_with_prefix:
        return kat_with_prefix.replace(" (Gelir)", "")
    elif " (Gider)" in kat_with_prefix:
        return kat_with_prefix.replace(" (Gider)", "")
    return kat_with_prefix

# --- ANA PROGRAM ---
st.set_page_config(page_title="2026 Gelir-Gider Takip", layout="wide", page_icon="🦷")

if check_password():
    load_custom_css()  # CSS yükle
    
    # Üst bar: Kullanıcı bilgisi ve logout
    col_title, col_user = st.columns([0.8, 0.2])
    with col_title:
        st.markdown("### 🦷 Gelir-Gider Takip 2026")
    with col_user:
        user_display = f"**{st.session_state.username.upper()}**"
        if st.session_state.role == "admin":
            user_display += " 🔑"
        st.markdown(f'<div style="text-align: right; margin-top: 8px; font-size: 13px;">{user_display}</div>', unsafe_allow_html=True)
        if st.button("🚪 Çıkış", key="logout_btn"):
            logout()
    
    st.markdown('<hr style="margin: 8px 0;">', unsafe_allow_html=True)
    
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    
    # Açılış bakiyelerini ayır
    df_acilis = df_raw[(df_raw["Islem Turu"] == "ACILIS") & (df_raw["Silindi"] != "X")].copy()
    
    # Normal işlemleri filtrele (Açılış, Döviz Dönüşümü ve Silindi hariç)
    df = df_raw[(df_raw["Islem Turu"] != "ACILIS") & (df_raw["Islem Turu"] != "Döviz Dönüşümü") & (df_raw["Silindi"] != "X")].copy()
    
    # Açılış bakiyesini TRY'ye çevir
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
    
    # Güvenli UPB hesaplama
    def safe_upb_calc(row):
        try:
            tutar = float(row['Tutar'])
            para = row['Para Birimi']
            kur = kurlar.get(para, 1.0)
            return tutar * kur
        except:
            return 0.0
    
    df['UPB_TRY'] = df.apply(safe_upb_calc, axis=1)
    
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    
    col_ay, col_doviz_btn, col_spacer = st.columns([0.3, 0.22, 0.48])
    with col_ay:
        secilen_ay_adi = st.selectbox("📅 Ay:", aylar, index=datetime.now().month - 1, label_visibility="visible")
    with col_doviz_btn:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        if st.button("💱 Döviz Dönüşümü", key="btn_doviz_donusum", use_container_width=True):
            st.session_state.show_doviz_modal = True
    
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1
    
    st.markdown('<div style="margin: 10px 0;"></div>', unsafe_allow_html=True)

    # Açılış bakiyesini hesapla
    if secilen_ay_no == 1:
        # Ocak: Excel'deki ACILIS kayıtlarından al
        acilis_bakiye_ay = acilis_bakiye
    else:
        # Diğer aylar: Önceki ayın net kasası
        df_onceki_aylar = df[df['Tarih_DT'].dt.month < secilen_ay_no].copy()
        onceki_gelir = df_onceki_aylar[df_onceki_aylar["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
        onceki_gider = df_onceki_aylar[df_onceki_aylar["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
        # Önceki aylardaki döviz dönüşümü etkisi (TRY karşılığı üzerinden)
        df_onceki_konv = df_raw[
            (df_raw["Islem Turu"] == "Döviz Dönüşümü") &
            (df_raw["Silindi"] != "X") &
            (df_raw['Tarih_DT'].dt.month < secilen_ay_no)
        ].copy()
        onceki_konv_giris = 0.0
        onceki_konv_cikis = 0.0
        if len(df_onceki_konv) > 0:
            for _, krow in df_onceki_konv.iterrows():
                kur_k = kurlar.get(krow['Para Birimi'], 1.0)
                tutar_try = float(krow['Tutar']) * kur_k
                if "KONV_GIRIS" in str(krow.get('Aciklama', '')):
                    onceki_konv_giris += tutar_try
                elif "KONV_CIKIS" in str(krow.get('Aciklama', '')):
                    onceki_konv_cikis += tutar_try
        acilis_bakiye_ay = acilis_bakiye + onceki_gelir - onceki_gider + onceki_konv_giris - onceki_konv_cikis
    
    # Sadece seçilen ayın gelir/gideri
    df_secilen_ay = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
    t_gelir = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
    
    # Net kasa = Açılış + Gelir - Gider
    net_kasa = acilis_bakiye_ay + t_gelir - t_gider

    # --- YENİ: PARA BİRİMİ BAZINDA HESAPLAMALAR ---
    # Toggle state
    if "show_currency_detail" not in st.session_state:
        st.session_state.show_currency_detail = False
    
    # Para birimi bazında açılış bakiyesi (seçilen ay için)
    def calc_acilis_by_currency(ay_no):
        currencies = {'TRY': 0, 'USD': 0, 'EUR': 0, 'GBP': 0}
        
        if ay_no == 1:
            # Ocak: Excel'deki ACILIS kayıtlarından al
            if len(df_acilis) > 0:
                for curr in currencies.keys():
                    currencies[curr] = df_acilis[df_acilis['Para Birimi'] == curr]['Tutar'].sum()
        else:
            # Diğer aylar: Önceki ayın net kasası
            df_onceki = df[df['Tarih_DT'].dt.month < ay_no].copy()
            
            # Önce Excel ACILIS'i al
            acilis_base = {'TRY': 0, 'USD': 0, 'EUR': 0, 'GBP': 0}
            if len(df_acilis) > 0:
                for curr in acilis_base.keys():
                    acilis_base[curr] = df_acilis[df_acilis['Para Birimi'] == curr]['Tutar'].sum()
            
            # Önceki ayların gelir - gider
            for curr in currencies.keys():
                gelir = df_onceki[(df_onceki["Islem Turu"] == "Gelir") & (df_onceki['Para Birimi'] == curr)]['Tutar'].sum()
                gider = df_onceki[(df_onceki["Islem Turu"] == "Gider") & (df_onceki['Para Birimi'] == curr)]['Tutar'].sum()
                currencies[curr] = acilis_base[curr] + gelir - gider
            
            # Önceki ayların döviz dönüşümü etkisi (para birimi bazında)
            df_onceki_konv_curr = df_raw[
                (df_raw["Islem Turu"] == "Döviz Dönüşümü") &
                (df_raw["Silindi"] != "X") &
                (df_raw['Tarih_DT'].dt.month < ay_no)
            ].copy()
            for curr in currencies.keys():
                konv_giris = df_onceki_konv_curr[(df_onceki_konv_curr["Aciklama"].str.contains("KONV_GIRIS", na=False)) & (df_onceki_konv_curr['Para Birimi'] == curr)]['Tutar'].sum()
                konv_cikis = df_onceki_konv_curr[(df_onceki_konv_curr["Aciklama"].str.contains("KONV_CIKIS", na=False)) & (df_onceki_konv_curr['Para Birimi'] == curr)]['Tutar'].sum()
                currencies[curr] = currencies[curr] + konv_giris - konv_cikis
        
        return currencies
    
    # Para birimi bazında gelir/gider (seçilen ay için)
    def calc_gelir_gider_by_currency(df_filtered, islem_turu):
        currencies = {'TRY': 0, 'USD': 0, 'EUR': 0, 'GBP': 0}
        df_temp = df_filtered[df_filtered["Islem Turu"] == islem_turu]
        for curr in currencies.keys():
            currencies[curr] = df_temp[df_temp['Para Birimi'] == curr]['Tutar'].sum()
        return currencies
    
    # Para birimi bazında net kasa (kümülatif - seçilen aya kadar)
    def calc_net_by_currency(ay_no):
        currencies = {'TRY': 0, 'USD': 0, 'EUR': 0, 'GBP': 0}
        
        # Açılış bakiyesi (seçilen ay için)
        acilis_curr = calc_acilis_by_currency(ay_no)
        
        # Sadece seçilen ayın hareketleri
        df_konv = df_raw[(df_raw["Islem Turu"] == "Döviz Dönüşümü") & (df_raw["Silindi"] != "X") & (df_raw['Tarih_DT'].dt.month == ay_no)].copy()
        for curr in currencies.keys():
            gelir = df_secilen_ay[(df_secilen_ay["Islem Turu"] == "Gelir") & (df_secilen_ay['Para Birimi'] == curr)]['Tutar'].sum()
            gider = df_secilen_ay[(df_secilen_ay["Islem Turu"] == "Gider") & (df_secilen_ay['Para Birimi'] == curr)]['Tutar'].sum()
            konv_giris = df_konv[(df_konv["Aciklama"].str.contains("KONV_GIRIS", na=False)) & (df_konv['Para Birimi'] == curr)]['Tutar'].sum()
            konv_cikis = df_konv[(df_konv["Aciklama"].str.contains("KONV_CIKIS", na=False)) & (df_konv['Para Birimi'] == curr)]['Tutar'].sum()
            currencies[curr] = acilis_curr[curr] + gelir - gider + konv_giris - konv_cikis
        
        return currencies
    
    acilis_curr = calc_acilis_by_currency(secilen_ay_no)
    gelir_curr = calc_gelir_gider_by_currency(df_secilen_ay, "Gelir")
    gider_curr = calc_gelir_gider_by_currency(df_secilen_ay, "Gider")
    net_curr = calc_net_by_currency(secilen_ay_no)
    
    # Helper function: Para birimi detay HTML
    def render_currency_detail(currencies, show):
        detail_class = "expanded" if show else "collapsed"
        html = f'<div class="currency-detail {detail_class}">'
        for symbol, curr in [("💵", "TRY"), ("💲", "USD"), ("💶", "EUR"), ("💷", "GBP")]:
            value = format_int(currencies[curr])
            currency_symbol = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}[curr]
            html += f'<div class="currency-row"><span class="currency-label">{symbol} {curr}:</span><span>{value} {currency_symbol}</span></div>'
        html += '</div>'
        return html
    
    # Helper function: Kurlar detay HTML
    def render_rates_detail(show):
        detail_class = "expanded" if show else "collapsed"
        html = f'<div class="currency-detail {detail_class}">'
        for symbol, curr in [("💲", "USD"), ("💶", "EUR"), ("💷", "GBP")]:
            rate = format_rate(kurlar[curr])
            html += f'<div class="currency-row"><span class="currency-label">{symbol} {curr}:</span><span>{rate} ₺</span></div>'
        html += '</div>'
        return html
    
    # Metrikleri göster - Sadece ADMIN için
    if st.session_state.role == "admin":
        m1, m2, m3, m4, m5 = st.columns(5)
        
        with m1:
            st.metric("💼 Açılış Bakiyesi", f"{format_int(acilis_bakiye_ay)} ₺")
            if st.session_state.show_currency_detail:
                st.markdown(render_currency_detail(acilis_curr, True), unsafe_allow_html=True)
        
        with m2:
            st.metric(f"💰 Gelir ({secilen_ay_adi})", f"{format_int(t_gelir)} ₺")
            if st.session_state.show_currency_detail:
                st.markdown(render_currency_detail(gelir_curr, True), unsafe_allow_html=True)
        
        with m3:
            st.metric(f"💸 Gider ({secilen_ay_adi})", f"{format_int(t_gider)} ₺")
            if st.session_state.show_currency_detail:
                st.markdown(render_currency_detail(gider_curr, True), unsafe_allow_html=True)
        
        with m4:
            st.metric("💵 Net Kasa", f"{format_int(net_kasa)} ₺")
            if st.session_state.show_currency_detail:
                st.markdown(render_currency_detail(net_curr, True), unsafe_allow_html=True)
        
        with m5:
            # Kurlar başlığına mini toggle ekle
            toggle_icon = "🔼" if st.session_state.show_currency_detail else "🔽"
            col_title2, col_toggle2 = st.columns([0.85, 0.15])
            with col_title2:
                st.metric("💱 Kurlar", "")
            with col_toggle2:
                # Butonu aşağı hizala
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                if st.button(toggle_icon, key="toggle_kurlar", help="Detayları göster/gizle"):
                    st.session_state.show_currency_detail = not st.session_state.show_currency_detail
                    st.rerun()
            
            if st.session_state.show_currency_detail:
                st.markdown(render_rates_detail(True), unsafe_allow_html=True)

    # --- ANALİZ PANELİ - Sadece ADMIN için ---
    if st.session_state.role == "admin":
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
        st.markdown(f"### 📑 {secilen_ay_adi} Ayı Hareketleri")
        st.markdown('<div style="margin: 8px 0;"></div>', unsafe_allow_html=True)
        
        df_display = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()

        # Döviz dönüşümü satırlarını da listeye dahil et (header/grafiklere dahil edilmeden, sadece görünüm için)
        df_konv_rows = df_raw[
            (df_raw["Islem Turu"] == "Döviz Dönüşümü") &
            (df_raw["Silindi"] != "X") &
            (df_raw['Tarih_DT'].dt.month == secilen_ay_no)
        ].copy()
        if len(df_konv_rows) > 0:
            df_display = pd.concat([df_display, df_konv_rows], ignore_index=False)
        df_display = df_display.sort_values(by=df_display.columns[0], key=lambda s: pd.to_numeric(s, errors='coerce'))
        
        search_term = st.text_input("🔍 Hızlı Arama:", "", placeholder="Hasta adı, kategori veya tutar...")
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]
        
        st.markdown('<div style="margin: 5px 0;"></div>', unsafe_allow_html=True)

        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
        heads = ["ID", "Tarih", "Tür", "Hasta Adı", "Kat.", "Döv", "Tutar", "UPB", "Tekn.", "Açıklama", "İşlem"]
        for col, h in zip(c, heads): col.markdown(f"**{h}**")
        st.write("---")

        # Modal fonksiyonları
        def show_edit_modal(row_data):
            @st.dialog(f"✏️ Düzenle: {row_data.get('Hasta Adi', 'Kayıt')}")
            def edit_modal():
                n_hast = st.text_input("Hasta/Cari Adı", value=str(row_data.get('Hasta Adi', '')))
                
                try:
                    default_date = pd.to_datetime(row_data['Tarih']).date()
                except:
                    default_date = date.today()
                n_tar = st.date_input("İşlem Tarihi", value=default_date)
                
                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    # Tür - Selectbox
                    current_tur = row_data.get('Islem Turu', '')
                    tur_options = ["Seçiniz...", "Gelir", "Gider"]
                    tur_index = tur_options.index(current_tur) if current_tur in tur_options else 0
                    n_tur = st.selectbox("İşlem Türü *", tur_options, index=tur_index)
                    
                    curr_para = row_data.get('Para Birimi', 'TRY')
                    para_idx = ["TRY","USD","EUR","GBP"].index(curr_para) if curr_para in ["TRY","USD","EUR","GBP"] else 0
                    n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR", "GBP"], index=para_idx)
                
                with c_m2:
                    # Kategori - TÜM kategoriler
                    all_kategoriler = ["Seçiniz..."] + get_gelir_kategorileri() + get_gider_kategorileri()
                    current_kat = row_data.get('Kategori', '')
                    
                    # Mevcut kategoriyi prefix ile eşleştir
                    current_tur = row_data.get('Islem Turu', '')
                    if current_tur == "Gelir" and current_kat:
                        current_kat_display = f"{current_kat} (Gelir)"
                    elif current_tur == "Gider" and current_kat:
                        current_kat_display = f"{current_kat} (Gider)"
                    else:
                        current_kat_display = current_kat
                    
                    kat_index = all_kategoriler.index(current_kat_display) if current_kat_display in all_kategoriler else 0
                    n_kat = st.selectbox("Kategori *", all_kategoriler, index=kat_index)
                    
                    # Teknisyen - Sabit liste (boş bırakılabilir)
                    current_tekn = row_data.get('Teknisyen', '')
                    tekn_options = ["", "Ali", "Cihat", "Onur", "Diğer"]
                    tekn_index = tekn_options.index(current_tekn) if current_tekn in tekn_options else 0
                    n_tekn = st.selectbox("Teknisyen", tekn_options, index=tekn_index)
                
                try:
                    default_tutar = int(float(row_data.get('Tutar', 0)))
                except:
                    default_tutar = 0
                n_tut = st.number_input("Tutar", value=default_tutar, step=1)
                n_acik = st.text_area("Açıklama", value=str(row_data.get('Aciklama', '')))
                
                if st.button("💾 Güncelle", use_container_width=True):
                    # Validasyon
                    errors = []
                    
                    # Tür boş kontrolü
                    if n_tur == "Seçiniz...":
                        errors.append("Tür seçimi zorunludur")
                    
                    # Kategori boş kontrolü
                    if n_kat == "Seçiniz...":
                        errors.append("Kategori seçimi zorunludur")
                    
                    # Klinik Hastası için Hasta adı zorunlu
                    if n_kat == "Klinik Hastası (Gelir)" and not n_hast.strip():
                        errors.append("Klinik Hastası için Hasta/Cari Adı zorunludur")
                    
                    # Tür-Kategori uyum kontrolü
                    gelir_kategoriler = get_gelir_kategorileri()
                    gider_kategoriler = get_gider_kategorileri()
                    
                    if n_tur == "Gelir" and n_kat in gider_kategoriler:
                        errors.append(f"'{n_kat}' bir Gider kategorisidir. Lütfen Gelir kategorisi seçin.")
                    
                    if n_tur == "Gider" and n_kat in gelir_kategoriler:
                        errors.append(f"'{n_kat}' bir Gelir kategorisidir. Lütfen Gider kategorisi seçin.")
                    
                    # Teknisyen Hastası kontrolü (prefix ile)
                    if n_kat == "Teknisyen Hastası (Gelir)" and not n_tekn:
                        errors.append("Teknisyen Hastası için Teknisyen seçimi zorunludur")
                    
                    # Tutar kontrolü
                    if n_tut <= 0:
                        errors.append("Tutar 0'dan büyük olmalıdır")
                    
                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")
                    else:
                        try:
                            row_id = row_data.get('ID', '')
                            matching_rows = df_raw[df_raw.iloc[:,0] == row_id]
                            if len(matching_rows) > 0:
                                idx = matching_rows.index[0] + 2
                                
                                # Direkt bağlantı aç
                                creds = Credentials.from_service_account_info(
                                    st.secrets["gcp_service_account"], 
                                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                                )
                                client = gspread.authorize(creds)
                                sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
                                
                                # Mevcut yaratma bilgilerini al
                                existing_row = sheet.row_values(idx)
                                yaratma_tarihi = existing_row[10] if len(existing_row) > 10 else ""
                                yaratma_saati = existing_row[11] if len(existing_row) > 11 else ""
                                
                                sheet.update(f"A{idx}:L{idx}", 
                                          [[row_id, n_tar.strftime('%Y-%m-%d'), n_tur, n_hast,
                                            clean_kategori(n_kat), n_para, int(n_tut), n_tekn, n_acik, "",  # Prefix temizlendi
                                            yaratma_tarihi, yaratma_saati]])
                                st.cache_data.clear()
                                st.success("✅ Güncelleme başarılı!")
                                st.rerun()
                            else:
                                st.error("❌ Kayıt bulunamadı!")
                        except Exception as e:
                            st.error(f"❌ Güncelleme hatası: {str(e)}")
            edit_modal()

        # --- DÖVİZ DÖNÜŞÜMÜ MODAL ---
        if "show_doviz_modal" not in st.session_state:
            st.session_state.show_doviz_modal = False

        if st.session_state.get("show_doviz_modal", False):
            st.session_state.show_doviz_modal = False
            @st.dialog("💱 Döviz Dönüşümü")
            def doviz_modal():
                net_curr_modal = calc_net_by_currency(secilen_ay_no)
                para_birimleri = ["TRY", "USD", "EUR", "GBP"]
                semboller = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}

                st.date_input("📅 Tarih", value=date.today(), disabled=True, key="d_tarih")

                st.markdown("#### Çıkış")
                c1, c2 = st.columns(2)
                with c1:
                    cikis_para = st.selectbox("Para Birimi", para_birimleri, key="d_cikis_para")
                with c2:
                    cikis_tutar = st.number_input("Çıkış Tutarı", min_value=0, step=1, key="d_cikis_tutar")
                mevcut_bakiye = net_curr_modal.get(cikis_para, 0)
                st.markdown(f"<div style='font-size:12px;color:#888;margin-top:-8px;'>Mevcut: {format_int(mevcut_bakiye)} {semboller[cikis_para]}</div>", unsafe_allow_html=True)

                st.markdown("#### Giriş")
                g1, g2, g3 = st.columns(3)
                with g1:
                    giris_para_options = [p for p in para_birimleri]
                    giris_para = st.selectbox("Para Birimi", giris_para_options, key="d_giris_para", index=1)
                with g2:
                    # Kur hesabı: her para biriminin TRY karşılığı üzerinden çapraz kur
                    cikis_try_kuru = kurlar.get(cikis_para, 1.0)
                    giris_try_kuru = kurlar.get(giris_para, 1.0)
                    default_kur = cikis_try_kuru / giris_try_kuru
                    kur = st.number_input("Kur", min_value=0.0001, value=float(round(default_kur, 4)), format="%.4f", key=f"d_kur_{cikis_para}_{giris_para}")
                with g3:
                    giris_tutar = int(cikis_tutar * kur)
                    st.markdown(f"<div style='margin-top:28px; font-size:20px; font-weight:700; color:#27AE60;'>{format_int(giris_tutar)} {semboller[giris_para]}</div>", unsafe_allow_html=True)

                st.markdown("---")
                if st.button("💾 Kaydet", use_container_width=True, type="primary"):
                    errors = []
                    if cikis_para == giris_para:
                        errors.append("Çıkış ve giriş para birimi aynı olamaz.")
                    if cikis_tutar <= 0:
                        errors.append("Çıkış tutarı 0'dan büyük olmalıdır.")
                    if cikis_tutar > mevcut_bakiye:
                        errors.append(f"Çıkış tutarı mevcut bakiyeyi ({format_int(mevcut_bakiye)} {semboller[cikis_para]}) aşamaz.")
                    if errors:
                        for e in errors:
                            st.error(f"❌ {e}")
                    else:
                        try:
                            now = datetime.now()
                            bugun = date.today().strftime('%Y-%m-%d')
                            
                            # ID hesapla
                            if len(df_raw) > 0:
                                normal_rows = df_raw[df_raw["Islem Turu"] != 'ACILIS']
                                existing_ids = pd.to_numeric(normal_rows.iloc[:, 0], errors='coerce').dropna()
                                next_id = int(existing_ids.max() + 1) if len(existing_ids) > 0 else 1
                            else:
                                next_id = 1

                            # Sütun sırası: ID, Tarih, Islem Turu, Hasta Adi, Kategori, Para Birimi, Tutar, Teknisyen, Aciklama, Silindi, Yaratma Tarihi, Yaratma Saati
                            row_cikis = [next_id,     bugun, "Döviz Dönüşümü", "", "Döviz Dönüşümü", cikis_para, int(cikis_tutar), "", "KONV_CIKIS", "", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")]
                            row_giris = [next_id + 1, bugun, "Döviz Dönüşümü", "", "Döviz Dönüşümü", giris_para, int(giris_tutar), "", "KONV_GIRIS", "", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")]

                            creds = Credentials.from_service_account_info(
                                st.secrets["gcp_service_account"],
                                scopes=["https://www.googleapis.com/auth/spreadsheets"]
                            )
                            client = gspread.authorize(creds)
                            sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
                            sheet.append_row(row_cikis)
                            sheet.append_row(row_giris)

                            st.cache_data.clear()
                            st.session_state.show_doviz_modal = False
                            st.success("✅ Döviz dönüşümü kaydedildi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Kayıt hatası: {str(e)}")
            doviz_modal()

        def show_delete_modal(row_data):
            @st.dialog("⚠️ Kayıt Silme Onayı")
            def delete_modal():
                row_id = row_data.get('ID', '')
                hasta = row_data.get('Hasta Adi', '')
                tutar = row_data.get('Tutar', '0')
                para = row_data.get('Para Birimi', 'TRY')
                
                st.error(f"**SİLİNECEK:** {row_id} | {hasta} | {tutar} {para}")
                if st.button("🗑️ Evet, Sil", use_container_width=True, type="primary"):
                    try:
                        matching_rows = df_raw[df_raw.iloc[:,0] == row_id]
                        if len(matching_rows) > 0:
                            idx = matching_rows.index[0] + 2
                            
                            # Direkt bağlantı aç
                            creds = Credentials.from_service_account_info(
                                st.secrets["gcp_service_account"], 
                                scopes=["https://www.googleapis.com/auth/spreadsheets"]
                            )
                            client = gspread.authorize(creds)
                            sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
                            
                            sheet.update_cell(idx, 10, "X")
                            st.cache_data.clear()
                            st.success("✅ Silme başarılı!")
                            st.rerun()
                        else:
                            st.error("❌ Kayıt bulunamadı!")
                    except Exception as e:
                        st.error(f"❌ Silme hatası: {str(e)}")
            delete_modal()

        # Satırları göster
        for _, row in df_display.iterrows():
            is_doviz = row.get('Islem Turu') == "Döviz Dönüşümü"
            is_gelir = row.get('Islem Turu') == "Gelir"
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
            
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")

            if is_doviz:
                tip = "🔴 Çıkış" if "KONV_CIKIS" in str(row.get('Aciklama', '')) else "🟢 Giriş"
                r[2].markdown("<span class='doviz-badge'>Döviz</span>", unsafe_allow_html=True)
                r[3].write("")
                r[4].write(tip)
            else:
                badge_class = "gelir-badge" if is_gelir else "gider-badge"
                r[2].markdown(f"<span class='{badge_class}'>{row.get('Islem Turu', '')}</span>", unsafe_allow_html=True)
                r[3].write(row.get('Hasta Adi', ''))
                r[4].write(row.get('Kategori', ''))

            r[5].write(row.get('Para Birimi', ''))
            r[6].write(format_int(row.get('Tutar', 0)))
            r[7].write(format_int(row.get('UPB_TRY', 0)) if not is_doviz else "")
            r[8].write(row.get('Teknisyen', '') if not is_doviz else "")
            r[9].write(row.get('Aciklama', '') if not is_doviz else "")
            
            if is_doviz:
                if r[10].button("🗑️", key=f"dk_{row.iloc[0]}"):
                    show_delete_modal(row)
            else:
                btn_e, btn_d = r[10].columns(2)
                if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                    show_edit_modal(row)
                if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                    show_delete_modal(row)

    with col_side:
        st.markdown("### ➕ Yeni Kayıt")
        st.markdown('<div style="margin: 5px 0;"></div>', unsafe_allow_html=True)
        
        # Form key'ini session state'te tut, başarılı kayıt sonrası değiştir
        if "form_key" not in st.session_state:
            st.session_state.form_key = 0
        
        with st.form(f"form_v22_final_{st.session_state.form_key}", clear_on_submit=False):
            f_tar = st.date_input("📅 Tarih", date.today())
            
            # Tür - Selectbox
            f_tur = st.selectbox("📊 Tür *", ["Seçiniz...", "Gelir", "Gider"])
            
            # Kategori - TÜM kategoriler (Gelir önce, sonra Gider - alfabetik)
            all_kategoriler = ["Seçiniz..."] + get_gelir_kategorileri() + get_gider_kategorileri()
            f_kat = st.selectbox("📁 Kategori *", all_kategoriler)
            
            f_hast = st.text_input("👤 Hasta/Cari", placeholder="Ad Soyad...")
            f_para = st.selectbox("💱 Para Birimi", ["TRY", "USD", "EUR", "GBP"])
            f_tut = st.number_input("💰 Tutar", min_value=0, step=1)
            
            # Teknisyen - Sabit liste (boş bırakılabilir)
            f_tekn = st.selectbox("👨‍⚕️ Teknisyen", ["", "Ali", "Cihat", "Onur", "Diğer"])
            
            f_acik = st.text_input("📝 Açıklama", placeholder="Not ekle...")
            
            submitted = st.form_submit_button("✅ Ekle", use_container_width=True)
            if submitted:
                # Validasyon
                errors = []
                
                # Tür boş kontrolü
                if f_tur == "Seçiniz...":
                    errors.append("Tür seçimi zorunludur")
                
                # Kategori boş kontrolü
                if f_kat == "Seçiniz...":
                    errors.append("Kategori seçimi zorunludur")
                
                # Klinik Hastası için Hasta adı zorunlu
                if f_kat == "Klinik Hastası (Gelir)" and not f_hast.strip():
                    errors.append("Klinik Hastası için Hasta/Cari Adı zorunludur")
                
                # Tür-Kategori uyum kontrolü
                gelir_kategoriler = get_gelir_kategorileri()
                gider_kategoriler = get_gider_kategorileri()
                
                if f_tur == "Gelir" and f_kat in gider_kategoriler:
                    errors.append(f"'{f_kat}' bir Gider kategorisidir. Lütfen Gelir kategorisi seçin.")
                
                if f_tur == "Gider" and f_kat in gelir_kategoriler:
                    errors.append(f"'{f_kat}' bir Gelir kategorisidir. Lütfen Gider kategorisi seçin.")
                
                # Teknisyen Hastası kontrolü (prefix ile)
                if f_kat == "Teknisyen Hastası (Gelir)" and not f_tekn:
                    errors.append("Teknisyen Hastası için Teknisyen seçimi zorunludur")
                
                # Tutar kontrolü
                if f_tut <= 0:
                    errors.append("Tutar 0'dan büyük olmalıdır")
                
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    try:
                        now = datetime.now()
                        
                        # ID hesaplarken ACILIS satırlarını hariç tut
                        if len(df_raw) > 0:
                            normal_rows = df_raw[df_raw.get('Islem Turu', '') != 'ACILIS']
                            if len(normal_rows) > 0:
                                existing_ids = pd.to_numeric(normal_rows.iloc[:, 0], errors='coerce').dropna()
                                if len(existing_ids) > 0:
                                    next_id = int(existing_ids.max() + 1)
                                else:
                                    next_id = 1
                            else:
                                next_id = 1
                        else:
                            next_id = 1
                        
                        new_row = [
                            next_id, 
                            f_tar.strftime('%Y-%m-%d'),
                            f_tur, f_hast, clean_kategori(f_kat), f_para,  # Prefix temizlendi
                            int(f_tut), f_tekn, f_acik, "", 
                            now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
                        ]
                        
                        # Direkt yeni bağlantı aç
                        try:
                            creds = Credentials.from_service_account_info(
                                st.secrets["gcp_service_account"], 
                                scopes=["https://www.googleapis.com/auth/spreadsheets"]
                            )
                            client = gspread.authorize(creds)
                            sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
                            sheet.append_row(new_row)
                            
                            # Cache'i temizle ve sayfayı yenile
                            st.cache_data.clear()
                            st.session_state.form_key += 1  # Form key'ini artır - yeni form oluştur
                            st.success("✅ Kayıt eklendi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ekleme hatası detay: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Ekleme hatası: {str(e)}")
