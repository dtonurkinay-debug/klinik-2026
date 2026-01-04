import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale
import plotly.express as px
from functools import lru_cache

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

# --- 2. FONKSİYONLAR (İYİLEŞTİRİLMİŞ) ---

@st.cache_data(ttl=3600)
def get_exchange_rates():
    """Döviz kurlarını çeker - 1 saat cache"""
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

@st.cache_resource
def get_gspread_client():
    """GSpread client - Session boyunca cache"""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

@st.cache_data(ttl=300)  # 5 dakika cache
def load_data():
    """Verileri yükler ve ön-işlemeden geçirir"""
    client = get_gspread_client()
    sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
    data = sheet.get_all_values()
    
    # DataFrame oluşturma
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Veri tipleri optimizasyonu
    df['Tarih_DT'] = pd.to_datetime(df['Tarih'], errors='coerce')
    df['Tutar'] = pd.to_numeric(df['Tutar'], errors='coerce').fillna(0)
    
    # Sıralama
    sort_cols = ['Tarih_DT']
    if 'Yaratma Tarihi' in df.columns: 
        sort_cols.append('Yaratma Tarihi')
    if 'Yaratma Saati' in df.columns: 
        sort_cols.append('Yaratma Saati')
    
    df = df.sort_values(by=sort_cols, ascending=True)
    
    return df, sheet

@lru_cache(maxsize=128)
def calculate_upb(tutar: float, para_birimi: str, usd_rate: float, eur_rate: float) -> float:
    """UPB hesaplama - LRU cache ile optimize edilmiş"""
    rates = {'TRY': 1.0, 'USD': usd_rate, 'EUR': eur_rate}
    return tutar * rates.get(para_birimi, 1.0)

@st.cache_data
def prepare_dataframe_with_upb(df, kurlar):
    """DataFrame'e UPB sütunu ekler - Vektörel işlem"""
    df = df.copy()
    
    if "Silindi" not in df.columns: 
        df["Silindi"] = ""
    
    # Vektörel UPB hesaplama (çok daha hızlı)
    df['UPB_TRY'] = df['Tutar'].astype(float)
    df.loc[df['Para Birimi'] == 'USD', 'UPB_TRY'] *= kurlar['USD']
    df.loc[df['Para Birimi'] == 'EUR', 'UPB_TRY'] *= kurlar['EUR']
    
    return df

@st.cache_data
def get_monthly_data(df, ay_no):
    """Aylık verileri filtreler - Cache'li"""
    return df[df['Tarih_DT'].dt.month == ay_no].copy()

@st.cache_data
def get_cumulative_data(df, ay_no):
    """Kümülatif verileri filtreler - Cache'li"""
    return df[df['Tarih_DT'].dt.month <= ay_no].copy()

@st.cache_data
def calculate_metrics(df_kumulatif):
    """Metrikleri hesaplar - Cache'li"""
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
    return t_gelir, t_gider

@st.cache_data
def prepare_trend_data(df):
    """Trend verileri hazırlar - Cache'li"""
    df_trends = df.copy()
    df_trends['Ay_No'] = df_trends['Tarih_DT'].dt.month
    df_trends['Ay_Ad'] = df_trends['Tarih_DT'].dt.strftime('%B')
    
    trend_summary = df_trends.groupby(['Ay_No', 'Ay_Ad', 'Islem Turu'])['UPB_TRY'].sum().reset_index()
    trend_summary = trend_summary.sort_values('Ay_No')
    
    return trend_summary

def format_int(value):
    """Tam sayı formatı"""
    return f"{int(round(value)):,}".replace(",", ".")

def format_rate(value):
    """Kur formatı"""
    return f"{value:.2f}".replace(".", ",")

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Analitik", layout="wide")

if check_password():
    # Veri yükleme (cache'li)
    with st.spinner("📊 Veriler yükleniyor..."):
        df_raw, worksheet = load_data()
        kurlar = get_exchange_rates()
    
    # DataFrame hazırlama (cache'li)
    df = prepare_dataframe_with_upb(df_raw, kurlar)
    df = df[df["Silindi"] != "X"].copy()

    st.title("📊 Klinik 2026 Yönetim Paneli")
    
    # Ay seçimi
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    # Kümülatif hesaplamalar (cache'li)
    df_kumulatif = get_cumulative_data(df, secilen_ay_no)
    t_gelir, t_gider = calculate_metrics(df_kumulatif)

    # Metrikler
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"Gelir (Oca-{secilen_ay_adi[:3]})", f"{format_int(t_gelir)} ₺")
    m2.metric(f"Gider (Oca-{secilen_ay_adi[:3]})", f"{format_int(t_gider)} ₺")
    m3.metric("Net Kasa", f"{format_int(t_gelir - t_gider)} ₺")
    m4.metric("USD Kuru", f"{format_rate(kurlar['USD'])} ₺")
    m5.metric("EUR Kuru", f"{format_rate(kurlar['EUR'])} ₺")

    # --- ANALİZ PANELİ ---
    with st.expander("📊 Grafiksel Analizleri Göster/Gizle", expanded=False):
        trend_summary = prepare_trend_data(df)

        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.line(trend_summary, x='Ay_Ad', y='UPB_TRY', color='Islem Turu', 
                          title="Aylık Gelir/Gider Trendi", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = px.pie(df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"], 
                         values='UPB_TRY', names='Kategori', 
                         title="Gelir Dağılımı (Kümülatif)", hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        g3, g4 = st.columns(2)
        with g3:
            df_kasa = trend_summary.pivot(index='Ay_Ad', columns='Islem Turu', values='UPB_TRY').fillna(0)
            if 'Gelir' in df_kasa and 'Gider' in df_kasa:
                df_kasa['Net'] = df_kasa['Gelir'] - df_kasa['Gider']
                df_kasa['Kumulatif'] = df_kasa['Net'].cumsum()
                fig3 = px.area(df_kasa.reset_index(), x='Ay_Ad', y='Kumulatif', 
                              title="Kasa Büyüme Trendi")
                st.plotly_chart(fig3, use_container_width=True)
        with g4:
            fig4 = px.pie(df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"], 
                         values='UPB_TRY', names='Kategori', 
                         title="Gider Dağılımı (Kümülatif)", hole=0.4)
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    col_main, col_side = st.columns([4.5, 1])

    with col_main:
        st.subheader(f"📑 {secilen_ay_adi} Ayı Hareketleri")
        
        # Aylık veri (cache'li)
        df_display = get_monthly_data(df, secilen_ay_no)
        
        # Arama
        search_term = st.text_input("🔍 Hızlı Arama:", "")
        if search_term:
            mask = df_display.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            df_display = df_display[mask]

        # Tablo başlıkları
        c = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
        heads = ["ID", "Tarih", "Tür", "Hasta Adi", "Kat.", "Döv", "Tutar", "UPB", "Tekn.", "Açıklama", "İşlem"]
        for col, h in zip(c, heads): 
            col.markdown(f"**{h}**")
        st.write("---")

        # Satırları göster
        for _, row in df_display.iterrows():
            color = "#2e7d32" if row['Islem Turu'] == "Gelir" else "#c62828"
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
            
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")
            r[2].markdown(f"<span style='color:{color}; font-weight:bold;'>{row.iloc[2]}</span>", 
                         unsafe_allow_html=True)
            r[3].write(row.iloc[3])
            r[4].write(row.iloc[4])
            r[5].write(row.iloc[5])
            r[6].write(format_int(float(row.iloc[6])))
            r[7].write(format_int(row['UPB_TRY']))
            r[8].write(row.iloc[7])
            r[9].write(row.iloc[8])
            
            btn_e, btn_d = r[10].columns(2)
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Düzenle: {row.iloc[3]}")
                def edit_modal(r_data):
                    n_hast = st.text_input("Hasta/Cari Adı", value=r_data.iloc[3])
                    n_tar = st.date_input("İşlem Tarihi", value=pd.to_datetime(r_data.iloc[1]))
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        n_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], 
                                           index=0 if r_data.iloc[2]=="Gelir" else 1)
                        n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"], 
                                            index=["TRY","USD","EUR"].index(r_data.iloc[5]))
                    with c_m2:
                        n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
                        n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
                    n_tut = st.number_input("Tutar", value=int(float(r_data.iloc[6])), step=1)
                    n_acik = st.text_area("Açıklama", value=r_data.iloc[8])
                    if st.button("Güncelle"):
                        if n_tut <= 0: 
                            st.error("Lütfen geçerli bir tutar girin!")
                        else:
                            idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                            worksheet.update(f"A{idx}:J{idx}", 
                                          [[r_data.iloc[0], str(n_tar), n_tur, n_hast, 
                                            n_kat, n_para, int(n_tut), n_tekn, n_acik, ""]])
                            st.cache_data.clear()  # Cache temizle
                            st.rerun()
                edit_modal(row)

            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                @st.dialog("⚠️ Kayıt Silme Onayı")
                def delete_modal(r_data):
                    st.error(f"SİLİNECEK: {r_data.iloc[0]} | {r_data.iloc[3]} | {r_data.iloc[6]} {r_data.iloc[5]}")
                    if st.button("Evet, Sil", use_container_width=True, type="primary"):
                        idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 10, "X")
                        st.cache_data.clear()  # Cache temizle
                        st.rerun()
                delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("form_v22_final", clear_on_submit=True):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("Hasta/Cari")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0, step=1)
            f_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
            f_acik = st.text_input("Açıklama")
            
            submitted = st.form_submit_button("Ekle", use_container_width=True)
            if submitted:
                if f_tut <= 0:
                    st.warning("⚠️ Tutar 0'dan büyük olmalıdır!")
                else:
                    now = datetime.now()
                    try: 
                        next_id = int(pd.to_numeric(df_raw.iloc[:, 0]).max() + 1)
                    except: 
                        next_id = 1
                    
                    worksheet.append_row([
                        next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, 
                        int(f_tut), f_tekn, f_acik, "", 
                        now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
                    ])
                    st.cache_data.clear()  # Cache temizle
                    st.rerun()
