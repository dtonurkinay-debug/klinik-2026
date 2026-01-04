import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
import requests
import xml.etree.ElementTree as ET
import locale
from google.oauth2.service_account import Credentials
import gspread

# --- 1. AYARLAR VE GÜVENLİK ---
PASSWORD = "klinik2026"

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>
            .stApp { background: #F1F5F9; }
            .login-box {
                background: white; padding: 40px; border-radius: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center;
                max-width: 350px; margin: auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.write("##")
        _, col_mid, _ = st.columns([1, 1, 1])
        with col_mid:
            st.markdown("<div class='login-box'><h1>🏥</h1><h3>Klinik 2026</h3></div>", unsafe_allow_html=True)
            pwd = st.text_input("Şifre", type="password", label_visibility="collapsed")
            if st.button("Giriş", use_container_width=True):
                if pwd == PASSWORD:
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("Hatalı!")
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
    return df, sheet

def format_int(value):
    return f"{int(round(value)):,}".replace(",", ".")

# --- 3. ANA PANEL ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide", page_icon="🏥")

if check_password():
    df_raw, worksheet = load_data()
    kurlar = get_exchange_rates()
    
    if "Silindi" not in df_raw.columns: df_raw["Silindi"] = ""
    df = df_raw[df_raw["Silindi"] != "X"].copy()
    df['UPB_TRY'] = df.apply(lambda r: float(r['Tutar']) * kurlar.get(r['Para Birimi'], 1.0), axis=1)

    st.title("🏢 Klinik Yönetim Paneli")
    
    # Metrikler
    m = st.columns(5)
    t_gelir = df[df["Islem Turu"] == "Gelir"]['UPB_TRY'].sum()
    t_gider = df[df["Islem Turu"] == "Gider"]['UPB_TRY'].sum()
    m[0].metric("Toplam Gelir", f"{format_int(t_gelir)} ₺")
    m[1].metric("Toplam Gider", f"{format_int(t_gider)} ₺")
    m[2].metric("Kasa", f"{format_int(t_gelir-t_gider)} ₺")
    m[3].metric("USD", f"{kurlar['USD']} ₺")
    m[4].metric("EUR", f"{kurlar['EUR']} ₺")

    st.divider()

    col_tab, col_form = st.columns([4, 1.2])

    with col_tab:
        st.subheader("İşlem Hareketleri")
        # Manuel Tablo Tasarımı (Düzenle ve Sil butonları ile)
        c = st.columns([0.5, 1, 0.8, 1.5, 1, 0.6, 1, 1, 1])
        heads = ["ID", "Tarih", "Tür", "Cari", "Kat.", "Döv", "Tutar", "UPB", "İşlem"]
        for col, h in zip(c, heads): col.markdown(f"**{h}**")
        
        for _, row in df.tail(15).iterrows(): # Son 15 kaydı gösterir
            r = st.columns([0.5, 1, 0.8, 1.5, 1, 0.6, 1, 1, 1])
            r[0].write(row.iloc[0])
            r[1].write(row['Tarih'])
            r[2].write(row.iloc[2])
            r[3].write(row.iloc[3]); r[4].write(row.iloc[4]); r[5].write(row.iloc[5])
            r[6].write(format_int(float(row.iloc[6])))
            r[7].write(format_int(row['UPB_TRY']))
            
            # BUTONLAR (Düzenle & Sil)
            btn_edit, btn_del = r[8].columns(2)
            
            # 1. DÜZENLE MODAL (Tüm alanlar dolu gelir)
            if btn_edit.button("✏️", key=f"ed_{row.iloc[0]}"):
                @st.dialog(f"Kayıt Düzenle (ID: {row.iloc[0]})")
                def edit_row(data):
                    e_hast = st.text_input("Hasta/Cari", value=data.iloc[3])
                    e_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"], index=["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"].index(data.iloc[4]) if data.iloc[4] in ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"] else 0)
                    e_tut = st.number_input("Tutar", value=int(float(data.iloc[6])))
                    e_pb = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"], index=["TRY", "USD", "EUR"].index(data.iloc[5]))
                    if st.button("Değişiklikleri Kaydet"):
                        idx = df_raw[df_raw.iloc[:,0] == data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 4, e_hast)
                        worksheet.update_cell(idx, 5, e_kat)
                        worksheet.update_cell(idx, 6, e_pb)
                        worksheet.update_cell(idx, 7, int(e_tut))
                        st.success("Güncellendi!")
                        st.rerun()
                edit_row(row)

            # 2. SİL POP-UP (Dinamik Mesajlı)
            if btn_del.button("🗑️", key=f"del_{row.iloc[0]}"):
                @st.dialog("Kaydı Silmek İstediğinize Emin Misiniz?")
                def delete_dialog(data):
                    st.warning(f"SİLİNECEK KAYIT DETAYI:\n\n**ID:** {data.iloc[0]}\n\n**Tür:** {data.iloc[2]}\n\n**Cari:** {data.iloc[3]}\n\n**Tutar:** {data.iloc[6]} {data.iloc[5]}")
                    st.write("Bu işlem geri alınamaz.")
                    if st.button("EVET, SİL", use_container_width=True, type="primary"):
                        idx = df_raw[df_raw.iloc[:,0] == data.iloc[0]].index[0] + 2
                        worksheet.update_cell(idx, 10, "X")
                        st.rerun()
                delete_dialog(row)

    with col_form:
        st.subheader("Yeni Kayıt")
        with st.form("yeni_v24_1"):
            f_tar = st.date_input("Tarih", date.today())
            f_tur = st.selectbox("Tür", ["Gelir", "Gider"])
            f_cari = st.text_input("Cari Adı")
            f_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
            f_pb = st.selectbox("Para Birimi", ["TRY", "USD", "EUR"])
            f_tut = st.number_input("Tutar", min_value=0)
            if st.form_submit_button("Kaydet", use_container_width=True):
                worksheet.append_row([int(pd.to_numeric(df_raw.iloc[:,0]).max()+1), str(f_tar), f_tur, f_cari, f_kat, f_pb, f_tut, "", "", "", datetime.now().strftime("%Y-%m-%d")])
                st.rerun()
