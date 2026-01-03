# ... (Üst kısımdaki kütüphane ve fonksiyonlar v19 ile aynıdır) ...

            if btn_e.button("✏️", key=f"e_{row.iloc[0]}"):
                @st.dialog(f"Kayıt Düzenleme: {row.iloc[3]}")
                def edit_modal(r_data):
                    # Görsel bir ayırıcı ve bilgilendirme alanı ekleyerek odağı tarihten çekiyoruz
                    st.info(f"ID: {r_data.iloc[0]} numaralı kaydı güncelliyorsunuz.")
                    
                    # Düzenleme Alanları
                    n_hast = st.text_input("Hasta/Cari", value=r_data.iloc[3])
                    n_tar = st.date_input("İşlem Tarihi", value=pd.to_datetime(r_data.iloc[1]), format="DD.MM.YYYY")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        n_tur = st.selectbox("Tür", ["Gelir", "Gider"], index=0 if r_data.iloc[2]=="Gelir" else 1)
                        n_para = st.selectbox("Döviz", ["TRY", "USD", "EUR"], index=["TRY","USD","EUR"].index(r_data.iloc[5]))
                    with c2:
                        n_kat = st.selectbox("Kategori", ["İmplant", "Dolgu", "Maaş", "Kira", "Lab", "Diğer"])
                        n_tekn = st.selectbox("Teknisyen", ["YOK", "Ali", "Murat"])
                    
                    n_tut = st.number_input("Tutar", value=int(float(r_data.iloc[6])), step=1)
                    n_acik = st.text_area("Açıklama", value=r_data.iloc[8])
                    
                    st.write("---")
                    if st.button("Değişiklikleri Uygula", use_container_width=True):
                        if n_tut <= 0:
                            st.error("Hata: Tutar 0'dan büyük olmalıdır!")
                        else:
                            idx = df_raw[df_raw.iloc[:,0] == r_data.iloc[0]].index[0] + 2
                            new_row = [r_data.iloc[0], str(n_tar), n_tur, n_hast, n_kat, n_para, int(n_tut), n_tekn, n_acik, ""]
                            worksheet.update(f"A{idx}:J{idx}", [new_row])
                            st.success("Güncellendi!")
                            st.rerun()
                edit_modal(row)

# ... (Yeni kayıt formu ve geri kalan kısımlar korunmuştur) ...
