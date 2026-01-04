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
        
        /* Metrik Kartları - Beyaz Kartlar */
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
        
        /* Başlıklar */
        h1 {
            color: var(--primary) !important;
            font-weight: 800;
            margin-bottom: 30px;
        }
        
        h2, h3 {
            color: var(--primary) !important;
            font-weight: 700;
        }
        
        /* Selectbox */
        [data-baseweb="select"] {
            border-radius: 10px;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        
        /* Input Alanları - Selectbox hariç */
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
            padding: 8px 0px 8px 0px;
            text-align: left;
        }
        
        /* Divider */
        hr {
            border: none;
            height: 1px;
            background: var(--border);
            margin: 20px 0;
        }
        
        /* Form Container */
        [data-testid="stForm"] {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid var(--border);
        }
        
        /* Yan Panel (Yeni Kayıt) */
        .element-container:has([data-testid="stForm"]) {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
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
            padding: 8px 0;
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
except Exception as e:
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR')
    except Exception as e2:
        st.warning(f"⚠️ Türkçe locale yüklenemedi. Varsayılan kullanılıyor.")

# --- 2. GÜVENLİK ---
PASSWORD = "klinik2026"

def check_password():
    if "password_correct" not in st.session_state:
        load_custom_css()  # CSS yükle
        
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🦷 Klinik 2026</div>
            <div class="login-subtitle">Diş Kliniği Yönetim Sistemi</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Login formu
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
            if code in ['USD', 'EUR']:
                buying_text = currency.find('ForexBuying').text
                if buying_text:
                    rates[code] = float(buying_text)
        return rates
    except Exception as e:
        st.warning(f"⚠️ Döviz kurları yüklenemedi, varsayılan değerler kullanılıyor")
        return {'TRY': 1.0, 'USD': 30.00, 'EUR': 33.00}

def get_gspread_client():
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Google Sheets bağlantısı başarısız: {str(e)}")
        st.stop()

def load_data():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key("1TypLnTiG3M62ea2u2f6oxqHjR9CqfUJsiVrJb5i3-SM").sheet1
        data = sheet.get_all_values()
        
        if len(data) < 2:
            st.warning("⚠️ Tabloda veri bulunamadı.")
            return pd.DataFrame(), sheet
        
        df = pd.DataFrame(data[1:], columns=data[0])
        df['Tarih_DT'] = pd.to_datetime(df['Tarih'], errors='coerce')
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

# --- ANA PROGRAM ---
st.set_page_config(page_title="Klinik 2026 Analitik", layout="wide", page_icon="🦷")

if check_password():
    load_custom_css()  # CSS yükle
    
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()
    
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

    st.title("🦷 Klinik 2026 Yönetim Paneli")
    
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    secilen_ay_adi = st.selectbox("📅 İzlenecek Ayı Seçin:", aylar, index=datetime.now().month - 1)
    secilen_ay_no = aylar.index(secilen_ay_adi) + 1

    df_kumulatif = df[df['Tarih_DT'].dt.month <= secilen_ay_no].copy()
    t_gelir = df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"]['UPB_TRY'].sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"💰 Gelir (Oca-{secilen_ay_adi[:3]})", f"{format_int(t_gelir)} ₺")
    m2.metric(f"💸 Gider (Oca-{secilen_ay_adi[:3]})", f"{format_int(t_gider)} ₺")
    m3.metric("💵 Net Kasa", f"{format_int(t_gelir - t_gider)} ₺")
    m4.metric("💲 USD Kuru", f"{format_rate(kurlar['USD'])} ₺")
    m5.metric("💶 EUR Kuru", f"{format_rate(kurlar['EUR'])} ₺")

    # --- ANALİZ PANELİ ---
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
            fig2 = px.pie(df_kumulatif[df_kumulatif["Islem Turu"] == "Gelir"], 
                         values='UPB_TRY', names='Kategori', 
                         title="Gelir Dağılımı (Kümülatif)", hole=0.4)
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
            fig4 = px.pie(df_kumulatif[df_kumulatif["Islem Turu"] == "Gider"], 
                         values='UPB_TRY', names='Kategori', 
                         title="Gider Dağılımı (Kümülatif)", hole=0.4)
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
                    n_tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"], 
                                       index=0 if row_data.get('Islem Turu')=="Gelir" else 1)
                    curr_para = row_data.get('Para Birimi', 'TRY')
                    para_idx = ["TRY","USD","EUR"].index(curr_para) if curr_para in ["TRY","USD","EUR"] else 0
                    n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"], index=para_idx)
                with c_m2:
                    n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
                    n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
                
                try:
                    default_tutar = int(float(row_data.get('Tutar', 0)))
                except:
                    default_tutar = 0
                n_tut = st.number_input("Tutar", value=default_tutar, step=1)
                n_acik = st.text_area("Açıklama", value=str(row_data.get('Aciklama', '')))
                
                if st.button("💾 Güncelle", use_container_width=True):
                    if n_tut <= 0: 
                        st.error("Lütfen geçerli bir tutar girin!")
                    else:
                        try:
                            row_id = row_data.get('ID', '')
                            matching_rows = df_raw[df_raw.iloc[:,0] == row_id]
                            if len(matching_rows) > 0:
                                idx = matching_rows.index[0] + 2
                                worksheet.update(f"A{idx}:J{idx}", 
                                              [[row_id, str(n_tar), n_tur, n_hast, 
                                                n_kat, n_para, int(n_tut), n_tekn, n_acik, ""]])
                                st.success("✅ Güncelleme başarılı!")
                                st.rerun()
                            else:
                                st.error("❌ Kayıt bulunamadı!")
                        except Exception as e:
                            st.error(f"❌ Güncelleme hatası: {str(e)}")
            edit_modal()

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
                            worksheet.update_cell(idx, 10, "X")
                            st.success("✅ Silme başarılı!")
                            st.rerun()
                        else:
                            st.error("❌ Kayıt bulunamadı!")
                    except Exception as e:
                        st.error(f"❌ Silme hatası: {str(e)}")
            delete_modal()

        # Satırları göster
        for _, row in df_display.iterrows():
            is_gelir = row.get('Islem Turu') == "Gelir"
            badge_class = "gelir-badge" if is_gelir else "gider-badge"
            r = st.columns([0.4, 0.9, 0.7, 1.2, 0.8, 0.5, 0.8, 0.8, 0.7, 1.0, 0.8])
            
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih_DT'].strftime('%d.%m.%Y') if pd.notnull(row['Tarih_DT']) else "")
            r[2].markdown(f"<span class='{badge_class}'>{row.get('Islem Turu', '')}</span>", unsafe_allow_html=True)
            r[3].write(row.get('Hasta Adi', ''))
            r[4].write(row.get('Kategori', ''))
            r[5].write(row.get('Para Birimi', ''))
            r[6].write(format_int(row.get('Tutar', 0)))
            r[7].write(format_int(row.get('UPB_TRY', 0)))
            r[8].write(row.get('Teknisyen', ''))
            r[9].write(row.get('Aciklama', ''))
            
            btn_e, btn_d = r[10].columns(2)
            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                show_edit_modal(row)
            if btn_d.button("🗑️", key=f"d_{row.iloc[0]}"):
                show_delete_modal(row)

    with col_side:
        st.subheader("➕ Yeni Kayıt")
        with st.form("form_v22_final", clear_on_submit=True):
            f_tar = st.date_input("📅 Tarih", date.today())
            f_tur = st.selectbox("📊 Tür", ["Gelir", "Gider"])
            f_hast = st.text_input("👤 Hasta/Cari", placeholder="Ad Soyad...")
            f_kat = st.selectbox("📁 Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_para = st.selectbox("💱 Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("💰 Tutar", min_value=0, step=1)
            f_tekn = st.selectbox("👨‍⚕️ Teknisyen", ["YOK", "Ali", "Murat"])
            f_acik = st.text_input("📝 Açıklama", placeholder="Not ekle...")
            
            submitted = st.form_submit_button("✅ Ekle", use_container_width=True)
            if submitted:
                if f_tut <= 0:
                    st.warning("⚠️ Tutar 0'dan büyük olmalıdır!")
                else:
                    try:
                        now = datetime.now()
                        
                        if len(df_raw) > 0:
                            existing_ids = pd.to_numeric(df_raw.iloc[:, 0], errors='coerce').dropna()
                            if len(existing_ids) > 0:
                                next_id = int(existing_ids.max() + 1)
                            else:
                                next_id = 1
                        else:
                            next_id = 1
                        
                        worksheet.append_row([
                            next_id, str(f_tar), f_tur, f_hast, f_kat, f_para, 
                            int(f_tut), f_tekn, f_acik, "", 
                            now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
                        ])
                        st.success("✅ Kayıt eklendi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ekleme hatası: {str(e)}")
