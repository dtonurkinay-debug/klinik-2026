import streamlit as st

# --- 1. YATAY & MODERN GİRİŞ TASARIMI ---
def check_password():
    if "password_correct" not in st.session_state:
        # Sayfayı yatayda genişleten ve estetik katan CSS
        st.markdown("""
            <style>
            .stApp { background-color: #F0F7FF; }
            header {visibility: hidden;}
            
            /* Yatay Kart Tasarımı */
            .login-horizontal-card {
                background: white;
                padding: 40px;
                border-radius: 24px;
                box-shadow: 0 12px 40px rgba(0,0,0,0.06);
                max-width: 500px; /* Kartı yatayda genişlettik */
                margin: auto;
                text-align: center;
                border: 1px solid #E2E8F0;
            }
            
            /* Giriş Alanlarını Genişlet */
            .stTextInput, .stButton button {
                width: 100% !important;
                border-radius: 12px !important;
            }
            
            .stButton button {
                background-color: #2563EB !important;
                color: white !important;
                font-weight: 600 !important;
                padding: 10px !important;
                margin-top: 10px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Sayfayı dikeyde ortala
        st.write("##")
        st.write("##")

        col1, col2, col3 = st.columns([0.5, 1, 0.5])
        
        with col2:
            # Tüm içeriği tek bir beyaz kutuda birleştiriyoruz
            st.markdown("""
                <div class="login-horizontal-card">
                    <div style="font-size: 50px; margin-bottom: 10px;">🏥</div>
                    <h2 style="color: #1E3A8A; font-family: sans-serif; margin-bottom: 0px;">Klinik 2026</h2>
                    <p style="color: #64748B; font-size: 15px; margin-bottom: 30px;">Yönetim Paneline Giriş Yapın</p>
            """, unsafe_allow_html=True)
            
            # Form bileşenleri kartın içinde kalacak şekilde yerleşiyor
            pwd = st.text_input("Şifre", type="password", placeholder="Erişim şifresini yazın...", label_visibility="collapsed")
            if st.button("Sisteme Giriş Yap"):
                if pwd == "klinik2026":
                    st.session_state.password_correct = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre, lütfen kontrol edin.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        return False
    return True

# --- 2. ANA PANEL ---
st.set_page_config(page_title="Klinik 2026 Pro", layout="wide", page_icon="🏥")

if check_password():
    # Başarılı girişte görünecek olan ana panel CSS'i
    st.markdown("""
        <style>
        .stApp { background-color: #F8FAFC; }
        header {visibility: visible;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #1E3A8A;'>🏢 Yönetim Paneli</h1>", unsafe_allow_html=True)
    st.success("Giriş başarılı. Verileriniz yükleniyor...")
    # Buradan sonra v28'deki tablo ve grafik kodlarını ekleyebilirsiniz.
