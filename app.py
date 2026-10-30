import streamlit as st
import random
from PIL import Image
import io

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# Bellek Tabanlı Veri Deposu (Fotoğraf verisini de tutacak şekilde güncellendi)
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
            "fotograf_adi": "Fotoğraf Yok",
            "fotograf_bytes": None,
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

tum_veriler = [
    {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Yol Bozukluğu / Çukur", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Park ve Yeşil Alan", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Belediye", "alt_bolum": "Park ve Bahçeler Müdürlüğü"},
    {"ana_kategori": "Çevre ve Temizlik", "alt_kategori": "Çöp Konteyneri Kırık", "sorumlu_kurum": "Belediye", "alt_bolum": "Temizlik İşleri Müdürlüğü"}
]
ana_kategoriler = list(set([item["ana_kategori"] for item in tum_veriler]))

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı, yol ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

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
                
                # Fotoğraf verisini byte olarak yakalayalım
                foto_bytes = None
                foto_adi = "Fotoğraf Yok"
                if fotograf is not None:
                    foto_bytes = fotograf.getvalue()
                    foto_adi = fotograf.name
                
                yeni_kayit = {
                    "talep_id": talep_id,
                    "tc_kimlik_no": tc_kimlik if tc_kimlik else "Belirtilmemiş",
                    "ad_soyad": ad_soyad,
                    "telefon_no": telefon,
                    "ana_kategori": secilen_ana_kategori,
                    "alt_kategori": secilen_alt_kategori,
                    "alt_bolum": alt_bolum,
                    "gps_konum": konum_tarif,
                    "fotograf_adi": foto_adi,
                    "fotograf_bytes": foto_bytes,
                    "aciklama": aciklama,
                    "sorumlu_kurum": sorumlu_kurum,
                    "durum": "Yeni"
                }
                
                st.session_state.talepler.insert(0, yeni_kayit)
                st.success(f"Talebiniz başarıyla alındı! İlgili birime iletildi. Takip Numaranız: **{talep_id}**")
                st.balloons()

with tab2:
    st.header("Belediye Personel Girişi")
    st.info("💡 Test için şu e-postayı yazabilirsiniz: `fenisleri@belediye.bel.tr`")
    
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        bulunan_personel = next((p for p in st.session_state.personeller if p["eposta_adresi"].lower() == eposta.strip().lower()), None)
        
        if bulunan_personel or "@belediye.bel.tr" in eposta:
            unvan = bulunan_personel["unvan"] if bulunan_personel else "Belediye Yetkilisi"
            ad = bulunan_personel["ad_soyad"] if bulunan_personel else eposta.split("@")[0]
            
            st.success(f"Hoş geldiniz, {ad} ({unvan})")
            st.subheader("📋 Gelen Talepler ve Detay İnceleme")
            
            # Her bir talebi detaylı kartlar halinde gösterelim ki fotoğraf net açılsın
            for talep in st.session_state.talepler:
                with st.expander(f"📌 {talep['talep_id']} - {talep['ana_kategori']} / {talep['alt_kategori']} ({talep['durum']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(**"Vatandaş:"** f" {talep['ad_soyad']}")
                        st.write(**"Telefon:"** f" {talep['telefon_no']}")
                        st.write(**"Konum:"** f" {talep['gps_konum']}")
                        st.write(**"Birim:"** f" {talep['alt_bolum']}")
                    with col2:
                        st.write(**"Açıklama:"** f" {talep['aciklama']}")
                    
                    # Eğer fotoğraf yüklendiyse doğrudan ekranda göster
                    if talep["fotograf_bytes"] is not None:
                        st.markdown("---")
                        st.write("📷 **Yüklenen Hasar Fotoğrafı:**")
                        image = Image.open(io.BytesIO(talep["fotograf_bytes"]))
                        st.image(image, caption=talep["fotograf_adi"], use_column_width=True)
                    else:
                        st.info("Bu talep için fotoğraf yüklenmemiş.")
        else:
            st.error("Bu e-posta adresiyle kayıtlı yetkili personel bulunamadı!")
