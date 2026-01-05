import pandas as pd
import requests
from xml.etree import ElementTree as ET
from datetime import datetime

def get_tcmb_rates():
    """TCMB'den USD, EUR ve GBP kurlarını çeker."""
    try:
        response = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml")
        root = ET.fromstring(response.content)
        rates = {}
        # USD, EUR ve yeni eklenen GBP için döngü
        for currency in ['USD', 'EUR', 'GBP']:
            curr_data = root.find(f".//Currency[@CurrencyCode='{currency}']/BanknoteSelling")
            if curr_data is not None:
                rates[currency] = float(curr_data.text)
        return rates
    except Exception as e:
        print(f"Kur çekme hatası: {e}")
        return {'USD': 0.0, 'EUR': 0.0, 'GBP': 0.0}

def standardize_and_process(file_path):
    # 1. Kurları Al
    rates = get_tcmb_rates()
    
    # Excel dosyasındaki tüm sayfaları oku
    excel_file = pd.ExcelFile(file_path)
    all_sheets = excel_file.sheet_names
    processed_sheets = {}
    
    previous_closing_balance = None

    for i, sheet_name in enumerate(all_sheets):
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # --- DEĞİŞİKLİK 1: ISO TARİH FORMATI (YYYY-MM-DD) ---
        if 'Tarih' in df.columns:
            df['Tarih'] = pd.to_datetime(df['Tarih']).dt.strftime('%Y-%m-%d')

        # --- DEĞİŞİKLİK 2: GBP HESAPLAMA MANTIĞI ---
        # Eğer 'Para Birimi' sütununda GBP seçilirse, Tutar'ı GBP kuru ile çarp
        if 'Para Birimi' in df.columns and 'Tutar' in df.columns:
            # USD ve EUR için yaptığımızın aynısını GBP için uyguluyoruz
            mask_gbp = df['Para Birimi'] == 'GBP'
            df.loc[mask_gbp, 'TL_Karsiligi'] = df.loc[mask_gbp, 'Tutar'] * rates['GBP']

        # --- DEĞİŞİKLİK 3: AÇILIŞ BAKİYESİ VE DEVİR MANTIĞI ---
        # Eğer ilk sayfa değilse, önceki ayın kapanışını bu ayın açılışı yap
        if i > 0 and previous_closing_balance is not None:
            # "Önceki Aydan Devir" satırını bul ve güncelle
            # Not: Sizin excel yapınızda 'Tanım' sütununda bu ifadeyi arıyoruz
            df.loc[df['Tanım'] == 'Önceki Aydan Devir', 'Tutar'] = previous_closing_balance

        # Cari ayın bakiyesini hesapla (Gelir - Gider + Açılış)
        # (Bu kısım mevcut hesaplama mantığınızla uyumlu olmalı)
        current_month_income = df[df['Gelir/Gider'] == 'Gelir']['Tutar'].sum()
        current_month_expense = df[df['Gelir/Gider'] == 'Gider']['Tutar'].sum()
        opening_bal = df.loc[df['Tanım'] == 'Önceki Aydan Devir', 'Tutar'].sum()
        
        # Kapanış bakiyesini bir sonraki ay için sakla
        previous_closing_balance = (opening_bal + current_month_income) - current_month_expense
        
        processed_sheets[sheet_name] = df

    # --- EXCEL ÇIKTISI VE HEADER DÜZENLEME ---
    with pd.ExcelWriter("Guncel_Takip_Tablosu.xlsx", engine='xlsxwriter') as writer:
        for sheet_name, df in processed_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5) # Header için yer bırak
            
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Header'a Kur Bilgilerini Yazma (USD ve EUR yanına GBP)
            header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D7E4BC'})
            worksheet.write('A1', f"USD Kuru: {rates['USD']}", header_format)
            worksheet.write('B1', f"EUR Kuru: {rates['EUR']}", header_format)
            worksheet.write('C1', f"GBP Kuru: {rates['GBP']}", header_format) # GBP Eklendi
            
            # "Para Birimi" Sütunu İçin Data Validation (GBP Eklendi)
            # Sütunun 'F' olduğunu varsayarsak (kendi sütun harfinize göre güncelleyebilirsiniz)
            worksheet.data_validation('F6:F500', {
                'validate': 'list',
                'source': ['TRY', 'USD', 'EUR', 'GBP'],
            })

    print("İşlem tamamlandı: Tarihler ISO yapıldı, GBP eklendi ve bakiyeler devredildi.")

# Çalıştır
# standardize_and_process("mevcut_dosyaniz.xlsx")
