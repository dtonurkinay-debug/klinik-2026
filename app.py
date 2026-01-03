import streamlit as st

# --- 1. RESET & MODERN GİRİŞ TASARIMI ---
def check_password():
    if "password_correct" not in st.session_state:
        # Arka plan ve yazı tipleri için temel ayar
        st.markdown("""
            <style>
            .stApp { background-color: #F0F9FF; }
            /* Butonu ve kutuyu biraz daraltalım */
            div[data-testid="stVerticalBlock"] > div {
                width: 100% !important;
                max-width: 350px !important;
                margin: auto;
            }
            </style>
        """, unsafe_allow_html=True)

        # Sayfayı dikeyde ortalamak için boşluk bırakıyoruz
        st.write("##")
        st.write("##")
        st.write("##")

        # İçerik Alanı
        col1, col2, col3 = st.columns([1, 2, 1]) # Ortadaki sütun formu tutacak
        
        with col2:
            # Minimal Kart Görünümü (HTML)
            st.markdown("""
                <div style="background-color: white; padding: 30px; border-radius: 20px; 
                            box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center;">
                    <h1 style="font-size: 50px; margin: 0;">🏥</h1>
                    <h2 style="color: #1E3A8A; font-family: sans-serif; margin-bottom: 5px;">Klinik 2026</h2>
                    <p style="color: #64748B; font-size: 14px;">Lütfen şifrenizi giriniz</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("#") # Kart ile giriş kutusu arasında küçük boşluk

            # Giriş Elemanları (Streamlit yerel bileşenleri)
            pwd = st.text_input("Şifre", type="password", placeholder="Şifre...", label_visibility="collapsed")
            if st.button("Sisteme Giriş Yap", use_container_width=True):
                if pwd == "klinik2026":
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")
        
        return False
    return True

# --- 2. ANA PANEL BAŞLANGICI ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide", page_icon="🏥")

if check_password():
    # Giriş başarılıysa burası çalışacak
    st.markdown("<h1 style='color: #1E3A8A;'>🏢 Yönetim Paneli</h1>", unsafe_allow_html=True)
    st.write("Hoş geldiniz! Paneliniz hazır.")
    # Buraya v28'deki veri çekme ve tablo kodlarını ekleyebiliriz.
