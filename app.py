import streamlit as st

# --- 1. STANDART MODERN GİRİŞ TASARIMI ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("""
            <style>
            /* Arka plan: Gözü yormayan açık gri/mavi */
            .stApp { background-color: #F8FAFC; }
            header {visibility: hidden;}
            
            /* Ana Kapsül: Standart 400px genişlik (UI Standardı) */
            .auth-container {
                max-width: 400px;
                margin: 80px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.05);
                border: 1px solid #EDF2F7;
                text-align: center;
            }
            
            /* Input ve Butonları kutuyla %100 eşitle */
            div[data-testid="stVerticalBlock"] > div {
                width: 100% !important;
            }
            
            .stTextInput input {
                border-radius: 10px !important;
                height: 45px !important;
            }
            
            .stButton button {
                width: 100% !important;
                border-radius: 10px !important;
                height: 48px !important;
                background-color: #2563EB !important;
                color: white !important;
                font-weight: 600 !important;
                border: none !important;
                margin-top: 10px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Görsel hiyerarşiyi tek bir div içinde topluyoruz
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Logo ve Metinler
        st.markdown("""
            <div style="margin-bottom: 30px;">
                <span style="font-size: 50px;">🏥</span>
                <h2 style="color: #1E3A8A; margin: 10px 0 5px 0; font-family: sans-serif;">Klinik 2026</h2>
                <p style="color: #64748B; font-size: 14px;">Lütfen erişim şifresini giriniz</p>
            </div>
        """, unsafe_allow_html=True)

        # Giriş Elemanları (Konteynır içinde)
        pwd = st.text_input("Şifre", type="password", placeholder="Şifre...", label_visibility="collapsed")
        if st.button("Sisteme Giriş Yap"):
            if pwd == "klinik2026":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Hatalı şifre!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# --- 2. ANA PANEL ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide", page_icon="🏥")

if check_password():
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; }
        header {visibility: visible;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #1E3A8A;'>🏢 Yönetim Paneli</h1>", unsafe_allow_html=True)
    st.info("Klinik finansal verileri başarıyla yüklendi.")
