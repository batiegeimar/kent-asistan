import streamlit as st
import random

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# Bellek Tabanlı Veri Deposu (Veritabanı bağlantısı olmasa bile sistemin anlık çalışmasını sağlar)
if "talepler" not in st.session_state:
    st.session_state.talepler = [
        {
            "talep_id": "KENT-84920",
            "tc_kimlik_no": "11111111111",
            "ad_soyad": "Örnek Vatandaş",
            "telefon_no": "05321112233",
            "ana_kategori": "Yol ve Ulaşım",
            "alt_kategori": "Yol Bozukluğu / Çukur",
            "alt_bolum": "Fen İşleri Müdürlüğü",
            "gps_konum": "Cumhuriyet Mah. Atatürk Cad. No:5",
            "fotograf_url": "yol_ornegi.jpg",
            "aciklama": "Ana cadde üzerinde derin çukur oluşmuş durumda.",
            "sorumlu_kurum": "Belediye",
            "durum": "Yeni"
        }
    ]

if "personeller" not in st.session_state:
    st.session_state.personeller = [
        {"eposta_adresi": "fenisleri@belediye.bel.tr", "ad_soyad": "Ahmet Yılmaz", "unvan": "Fen İşleri Müdürü"},
        {"eposta_adresi": "parkbahce@belediye.bel.tr", "ad_soyad": "Mehmet Demir", "unvan": "Park ve Bahçeler Amiri"}
    ]

# Statik Kategori Listesi (Hızlı ve Hatasız Çalışma İçin)
tum_veriler = [
    {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Yol Bozukluğu / Çukur", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Park ve Yeşil Alan", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Belediye", "alt_bolum": "Park ve Bahçeler Müdürlüğü"},
    {"ana_kategori": "Çevre ve Temizlik", "alt_kategori": "Çöp Konteyneri Kırık", "sorumlu_kurum": "Belediye", "alt_bolum": "Temizlik İşleri Müdürlüğü"}
]
ana_kategoriler = list(set([item["ana_kategori"] for item in tum_veriler]))

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı, yol ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

# Sekmeler
tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    with st.form("talep_formu"):
        tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)")
        ad_soyad = st.text_input("Ad Soyad *")
        telefon = st.text_input("Telefon Numarası *")
        
        secilen_ana_kategori = st.selectbox("Ana Kategori", options=sorted(ana_kategoriler))
        
        filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
        alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
        
        secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategori_isimleri)
        
        konum_tarif = st.text_input("Konum / Mahalle, Sokak veya Adres Tarifi *", placeholder="Örn: Cumhuriyet Mah. Atatürk Cad. No:12 önü")
        fotograf = st.file_uploader("Hasarlı Bölgeye Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"])
        aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...")
        
        gonder_btn = st.form_submit_button("Talebi Gönder")
        
        if gonder_btn:
            if not ad_soyad or not telefon or not aciklama or not konum_tarif:
                st.error("Lütfen zorunlu alanları (*) doldurunuz.")
            else:
                eslesme = next((item for item in filtrelenmis_altlar if item["alt_kategori"] == secilen_alt_kategori), None)
                sorumlu_kurum = eslesme["sorumlu_kurum"] if eslesme else "Belediye"
                alt_bolum = eslesme["alt_bolum"] if eslesme else "Fen İşleri Müdürlüğü"
                
                talep_id = f"KENT-{random.randint(10000, 99999)}"
                foto_adi = fotograf.name if fotograf else "Fotoğraf Yok"
                
                yeni_kayit = {
                    "talep_id": talep_id,
                    "tc_kimlik_no": tc_kimlik if tc_kimlik else "Belirtilmemiş",
                    "ad_soyad": ad_soyad,
                    "telefon_no": telefon,
                    "ana_kategori": secilen_ana_kategori,
                    "alt_kategori": secilen_alt_kategori,
                    "alt_bolum": alt_bolum,
                    "gps_konum": konum_tarif,
                    "fotograf_url": foto_adi,
                    "aciklama": aciklama,
                    "sorumlu_kurum": sorumlu_kurum,
                    "durum": "Yeni"
                }
                
                # Belleğe (Session State) kaydet
                st.session_state.talepler.insert(0, yeni_kayit)
                
                st.success(f"Talebiniz başarıyla alındı! İlgili birime iletildi. Takip Numaranız: **{talep_id}**")
                st.balloons()

with tab2:
    st.header("Belediye Personel Girişi")
    st.info("💡 Test için şu kayıtlı e-postalardan birini yazabilirsiniz: `fenisleri@belediye.bel.tr` veya `parkbahce@belediye.bel.tr`")
    
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        bulunan_personel = next((p for p in st.session_state.personeller if p["eposta_adresi"].lower() == eposta.strip().lower()), None)
        
        if bulunan_personel or "@belediye.bel.tr" in eposta:
            unvan = bulunan_personel["unvan"] if bulunan_personel else "Belediye Yetkilisi"
            ad = bulunan_personel["ad_soyad"] if bulunan_personel else eposta.split("@")[0]
            
            st.success(f"Hoş geldiniz, {ad} ({unvan})")
            st.subheader("📋 Belediyeye Gelen Vatandaş Talepleri")
            
            # Tüm talepleri tablo halinde göster
            import pandas as pd
            df = pd.DataFrame(st.session_state.talepler)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Bu e-posta adresiyle kayıtlı yetkili personel bulunamadı!")
