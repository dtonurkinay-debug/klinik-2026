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
        .stApp { background: linear-gradient(to bottom, #FFFFFF 0%, #F5F7FA 100%); }
        .login-container { max-width: 420px; margin: 100px auto; padding: 50px; background: white; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.08); border: 1px solid var(--border); text-align: center; }
        .login-title { font-size: 36px; font-weight: bold; color: var(--primary); margin-bottom: 8px; }
        .login-subtitle { color: var(--text-light); margin-bottom: 30px; font-size: 15px; }
        [data-testid="metric-container"] { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid var(--border); transition: all 0.3s ease; }
        [data-testid="metric-container"]:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
        [data-testid="stMetricLabel"] { color: var(--text-light) !important; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
        [data-testid="stMetricValue"] { color: var(--primary) !important; font-size: 28px; font-weight: 700; }
        h1 { color: var(--primary) !important; font-weight: 800; margin-bottom: 30px; }
        h2, h3 { color: var(--primary) !important; font-weight: 700; }
        [data-baseweb="select"] { border-radius: 10px; border: 1px solid var(--border) !important; box-shadow: 0 2px 4px rgba(0,0,0,0.04); }
        input:not([role="combobox"]), textarea { border-radius: 8px !important; border: 1.5px solid var(--border) !important; padding: 12px !important; transition: all 0.3s ease; background: white !important; }
        input:not([role="combobox"]):focus, textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.08) !important; }
        .stButton button { border-radius: 8px; font-weight: 600; padding: 10px 20px; border: none; transition: all 0.3s ease; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
        .stButton button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .stButton button[kind="primary"] { background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); color: white; }
        .stButton button[type="submit"] { background: linear-gradient(135deg, #27AE60 0%, #229954 100%); color: white; width: 100%; }
        button[key*="e_"] { background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%) !important; color: white !important; padding: 6px 14px !important; font-size: 14px !important; border-radius: 6px !important; }
        button[key*="d_"] { background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%) !important; color: white !important; padding: 6px 14px !important; font-size: 14px !important; border-radius: 6px !important; }
        [data-testid="stExpander"] { background: white; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 10px; }
        [data-testid="stMarkdownContainer"] strong { color: var(--primary); background: #F8F9FA; padding: 10px 0px 10px 12px; border-radius: 8px; display: inline-block; width: 100%; text-align: left; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid var(--border); margin: 0; }
        [data-testid="column"] > div { padding: 8px 0px 8px 2mm; text-align: left; }
        hr { border: none; height: 1px; background: var(--border); margin: 20px 0; }
        [data-testid="stForm"] { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid var(--border); }
        .element-container:has([data-testid="stForm"]) { background: white; padding: 20px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .stAlert { border-radius: 10px; border: 1px solid var(--border); box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
        .gelir-badge { background: linear-gradient(135deg, #27AE60 0%, #229954 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 12px; display: inline-block; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 6px rgba(39, 174, 96, 0.3); }
        .gider-badge { background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 12px; display: inline-block; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 2px 6px rgba(231, 76, 60, 0.3); }
        .element-container:hover { background: #F8F9FA; border-radius: 8px; transition: all 0.2s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .stApp > div { animation: fadeIn 0.4s ease-out; }
    </style>
    """, unsafe_allow_html=True)

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
        load_custom_css()
        st.markdown('<div class="login-container"><div class="login-title">🦷 Klinik 2026</div><div class="login-subtitle">Diş Kliniği Yönetim Sistemi</div></div>', unsafe_allow_html=True)
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
            if code in ['USD', 'EUR', 'GBP']:
                buying_text = currency.find('ForexBuying').text
                if buying_text:
                    rates[code] = float(buying_text)
        return rates
    except Exception:
        return {'TRY': 1.0, 'USD': 30.00, 'EUR': 33.00, 'GBP': 36.00}

def get_gspread_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

def get_fresh_worksheet():
    try:
        client = get_gspread_client()
        return client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
    except:
        return None

@st.cache_data(ttl=60)
def load_data():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
        data = sheet.get_all_values()
        if len(data) < 2: return pd.DataFrame(), sheet
        df = pd.DataFrame(data[1:], columns=data[0])
        df['Tarih_DT'] = pd.to_datetime(df['Tarih'], format='%Y-%m-%d', errors='coerce')
        df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
        return df, sheet
    except Exception as e:
        st.error(f"❌ Veri yükleme hatası: {str(e)}")
        st.stop()

def format_int(value):
    try: return f"{int(round(float(value))):,}".replace(",", ".")
    except: return "0"

def format_rate(value):
    try: return f"{float(value):.2f}".replace(".", ",")
    except: return "0,00"

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Analitik", layout="wide", page_icon="🦷")

if check_password():
    load_custom_css()
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""

    # YARDIMCI HESAPLAMA FONKSİYONU
    def safe_upb_calc(row):
        try:
            return float(row['Tutar']) * kurlar.get(row['Para Birimi'], 1.0)
        except: return 0.0

    # UPB Hesaplama ve Ana DF Ayrıştırma
    df_raw['UPB_TRY'] = df_raw.apply(safe_upb_calc, axis=1)
    df_acilis = df_raw[(df_raw["Islem Turu"] == "ACILIS") & (df_raw["Silindi"] != "X")].copy()
    df = df_raw[(df_raw["Islem Turu"] != "ACILIS") & (df_raw["Silindi"] != "X")].copy()
    
    # Başlangıç Bakiyesi Tanımı
    acilis_bakiye = df_acilis['UPB_TRY'].sum()

    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    # Aylık Bakiye Hesaplama
    if secilen_ay_no == 1:
        acilis_bakiye_ay = acilis_bakiye
        acilis_detay = {p: df_acilis[df_acilis['Para Birimi'] == p]['Tutar'].sum() for p in ['TRY', 'USD', 'EUR', 'GBP']}
    else:
        df_onceki = df[df['Tarih_DT'].dt.month < secilen_ay_no]
        acilis_bakiye_ay = acilis_bakiye + df_onceki[df_onceki["Islem Turu"] == "Gelir"]['UPB_TRY'].sum() - df_onceki[df_onceki["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
        acilis_detay = {}
        for p in ['TRY', 'USD', 'EUR', 'GBP']:
            baslangic = df_acilis[df_acilis['Para Birimi'] == p]['Tutar'].sum()
            gelir = df_onceki[(df_onceki['Para Birimi'] == p) & (df_onceki['Islem Turu'] == "Gelir")]['Tutar'].sum()
            gider = df_onceki[(df_onceki['Para Birimi'] == p) & (df_onceki['Islem Turu'] == "Gider")]['Tutar'].sum()
            acilis_detay[p] = baslangic + gelir - gider

    df_secilen_ay = df[df['Tarih_DT'].dt.month == secilen_ay_no].copy()
    t_gelir = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
    net_kasa = acilis_bakiye_ay + t_gelir - t_gider

    # Metrikler
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("💼 Açılış Bakiyesi", f"{format_int(acilis_bakiye_ay)} ₺")
        with st.expander("Detaylar"):
            for p, sim in zip(['TRY', 'USD', 'EUR', 'GBP'], ['₺', '$', '€', '£']):
                st.write(f"{p}: {format_int(acilis_detay.get(p, 0))} {sim}")
    
    with m2:
        st.metric(f"💰 Gelir ({secilen_ay_adi})", f"{format_int(t_gelir)} ₺")
    with m3:
        st.metric(f"💸 Gider ({secilen_ay_adi})", f"{format_int(t_gider)} ₺")
    with m4:
        st.metric("💵 Net Kasa", f"{format_int(net_kasa)} ₺")
    with m5:
        st.metric("💱 Döviz Kurları", "TCMB")
        with st.expander("Detaylar"):
            st.write(f"USD: {format_rate(kurlar.get('USD'))} ₺")
            st.write(f"EUR: {format_rate(kurlar.get('EUR'))} ₺")
            st.write(f"GBP: {format_rate(kurlar.get('GBP'))} ₺")

    st.title("🦷 Klinik 2026 Yönetim Paneli")

    # Grafik Analiz
    with st.expander("📊 Grafiksel Analizler", expanded=False):
        df_trends = df.copy()
        df_trends['Ay_Ad'] = df_trends['Tarih_DT'].dt.strftime('%B')
        trend_summary = df_trends.groupby([df_trends['Tarih_DT'].dt.month, 'Ay_Ad', 'Islem Turu'])['UPB_TRY'].sum().reset_index()
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(px.line(trend_summary, x='Ay_Ad', y='UPB_TRY', color='Islem Turu', title="Aylık Trend"), use_container_width=True)
        with g2:
            st.plotly_chart(px.pie(df_secilen_ay[df_secilen_ay["Islem Turu"] == "Gelir"], values='UPB_TRY', names='Kategori', title="Gelir Dağılımı"), use_container_width=True)

    st.divider()
    col_main, col_side = st.columns([4.5, 1])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Hareketleri")
        search_term = st.text_input("🔍 Hızlı Arama:", placeholder="Hasta adı, kategori...")
        df_display = df_secilen_ay.copy()
        if search_term:
            df_display = df_display[df_display.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
        for col, h in zip(c, ["ID", "Tarih", "Tür", "Hasta Adı", "Kat.", "Döv", "Tutar", "UPB", "Tekn.", "Açıklama", "İşlem"]):
            col.markdown(f"**{h}**")
        st.write("---")

        def show_edit_modal(row_data):
            @st.dialog(f"✏️ Düzenle: {row_data.get('Hasta Adi')}")
            def edit_modal():
                n_hast = st.text_input("Hasta/Cari Adı", value=str(row_data.get('Hasta Adi')))
                n_tar = st.date_input("İşlem Tarihi", value=pd.to_datetime(row_data['Tarih']).date())
                n_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], index=0 if row_data['Islem Turu']=="Gelir" else 1)
                n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR", "GBP"], index=["TRY","USD","EUR","GBP"].index(row_data['Para Birimi']))
                n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
                n_tut = st.number_input("Tutar", value=int(row_data['Tutar']), step=1)
                n_acik = st.text_area("Açıklama", value=str(row_data.get('Aciklama')))
                if st.button("💾 Güncelle", use_container_width=True):
                    try:
                        idx = df_raw[df_raw.iloc[:,0] == row_data.iloc[0]].index[0] + 2
                        fresh_sheet = get_fresh_worksheet()
                        fresh_sheet.update(f"A{idx}:I{idx}", [[row_data.iloc[0], n_tar.strftime('%Y-%m-%d'), n_tur, n_hast, n_kat, n_para, int(n_tut), "YOK", n_acik]])
                        st.cache_data.clear()
                        st.success("✅ Güncellendi!"); st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")
            edit_modal()

        def show_delete_modal(row_data):
            @st.dialog("⚠️ Silme Onayı")
            def delete_modal():
                if st.button("🗑️ Evet, Sil", use_container_width=True, type="primary"):
                    try:
                        idx = df_raw[df_raw.iloc[:,0] == row_data.iloc[0]].index[0] + 2
                        fresh_sheet = get_fresh_worksheet()
                        fresh_sheet.update_cell(idx, 10, "X")
                        st.cache_data.clear()
                        st.success("✅ Silindi!"); st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")
            delete_modal()

        for _, row in df_display.iterrows():
            badge = "gelir-badge" if row['Islem Turu'] == "Gelir" else "gider-badge"
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
            r[0].write(row.iloc[0]); r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y'))
            r[2].markdown(f"<span class='{badge}'>{row['Islem Turu']}</span>", unsafe_allow_html=True)
            r[3].write(row['Hasta Adi']); r[4].write(row['Kategori']); r[5].write(row['Para Birimi'])
            r[6].write(format_int(row['Tutar'])); r[7].write(format_int(row['UPB_TRY']))
            r[8].write(row['Teknisyen']); r[9].write(row['Aciklama'])
            btn_e, btn_d = r[10].columns(2)
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"): show_edit_modal(row)
            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"): show_delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("yeni_kayit", clear_on_submit=True):
            f_tar = st.date_input("📅 Tarih", date.today())
            f_tur = st.selectbox("📊 Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("👤 Hasta/Cari")
            f_kat = st.selectbox("📁 Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("💱 Para Birimi", ["TRY", "USD", "EUR", "GBP"])
            f_tut = st.number_input("💰 Tutar", min_value=0, step=1)
            f_acik = st.text_input("📝 Açıklama")
            if st.form_submit_button("✅ Ekle", use_container_width=True):
                if f_tut > 0:
                    try:
                        next_id = int(pd.to_numeric(df_raw.iloc[:,0], errors='coerce').max() + 1) if len(df_raw) > 0 else 1
                        new_row = [next_id, f_tar.strftime('%Y-%m-%d'), f_tur, f_hast, f_kat, f_para, int(f_tut), "YOK", f_acik, "", datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S")]
                        worksheet.append_row(new_row)
                        st.cache_data.clear(); st.success("✅ Kayıt eklendi!"); st.rerun()
                    except Exception as e: st.error(f"Hata: {e}")
