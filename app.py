import streamlit as st
import random
from PIL import Image
import io
import json
from datetime import datetime
from shapely.geometry import Point, shape

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# Bellek Tabanlı Veri Deposu
if "talepler" not in st.session_state:
    st.session_state.talepler = [
        {
            "talep_id": "KENT-84920",
            "tc_kimlik_no": "11111111111",
            "ad_soyad": "Örnek Vatandaş",
            "telefon_no": "05321112233",
            "il": "Aydın",
            "ilce": "Yenipazar",
            "ana_kategori": "Su Altyapısı ile İlgili Talepler",
            "alt_kategori": "Su Borusu Patlağı",
            "alt_bolum": "Su ve Kanalizasyon Müdürlüğü",
            "gps_konum": "Otomatik GPS (Enlem: 37.8524, Boylam: 27.9312)",
            "olusturma_tarihi": "2026-11-01 08:30:00",
            "fotograf_adi": "Fotoğraf Yok",
            "fotograf_bytes": None,
            "aciklama": "Ana cadde üzerinde su patlağı var.",
            "sorumlu_kurum": "Su İdaresi",
            "durum": "Yeni (GPS Sınır İçi Doğrulandı)"
        }
    ]

if "personeller" not in st.session_state:
    st.session_state.personeller = [
        {"eposta_adresi": "fenisleri@belediye.bel.tr", "ad_soyad": "Ahmet Yılmaz", "unvan": "Fen İşleri Müdürü"},
        {"eposta_adresi": "suidaresi@belediye.bel.tr", "ad_soyad": "Canan Sucu", "unvan": "Su ve Kanalizasyon Amiri"},
        {"eposta_adresi": "parkbahce@belediye.bel.tr", "ad_soyad": "Mehmet Demir", "unvan": "Park ve Bahçeler Amiri"}
    ]

# Kategori ve Birim Matrisi
tum_veriler = [
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Borusu Patlağı", "sorumlu_kurum": "Su İdaresi", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Kesintisi", "sorumlu_kurum": "Su İdaresi", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Kanalizasyon Sızıntısı", "sorumlu_kurum": "Su İdaresi", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Yol ve Kaldırımlarla İlgili Talepler", "alt_kategori": "Yol Bozukluğu ile İlgili Talepler (Çukur vb.)", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Yol ve Kaldırımlarla İlgili Talepler", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Elektrik Altyapısı ile İlgili Talepler", "alt_kategori": "Elektrik Kaçağı ile İlgili Talepler", "sorumlu_kurum": "EDAŞ / Elektrik Şirketi", "alt_bolum": "Elektrik Dağıtım Birimi"},
    {"ana_kategori": "Doğalgaz Altyapısı ile İlgili Talepler", "alt_kategori": "Doğalgaz Kaçağı ile İlgili Talepler", "sorumlu_kurum": "Doğalgaz Dağıtım Şirketi", "alt_bolum": "Doğalgaz Acil Servis"},
    {"ana_kategori": "Çevre Kirliliği ile İlgili Talepler", "alt_kategori": "Hafriyat / Kaçak Atık Dökümü", "sorumlu_kurum": "Belediye", "alt_bolum": "Zabıta / Çevre Koruma"},
    {"ana_kategori": "Temizlik İşleri ile İlgili Talepler", "alt_kategori": "Çöp Konteyneri Kırık / Eksik", "sorumlu_kurum": "Belediye", "alt_bolum": "Temizlik İşleri Müdürlüğü"},
    {"ana_kategori": "Park ve Bahçeler ile İlgili Talepler", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Belediye", "alt_bolum": "Park ve Bahçeler Müdürlüğü"}
]

ana_kategoriler = sorted(list(set([item["ana_kategori"] for item in tum_veriler])))

# Akıllı GeoJSON Sınır Dosyası Yükleme
@st.cache_resource
def ilce_sinirini_yukle():
    olasi_yollar = [
        "CBS_ALTYAPISI/YenipazarSinir.geojson",
        "cbs_altyapisi/YenipazarSinir.geojson",
        "CBS_Altyapisi/Yenipazarsinir.geojson",
        "YenipazarSinir.geojson",
        "yenipazarsinir.geojson"
    ]
    for yol in olasi_yollar:
        try:
            with open(yol, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
            if geojson_data.get("type") == "FeatureCollection":
                poligon = shape(geojson_data["features"][0]["geometry"])
            elif geojson_data.get("type") == "Feature":
                poligon = shape(geojson_data["geometry"])
            else:
                poligon = shape(geojson_data)
            return poligon
        except Exception:
            continue
    return None

yenipazar_poligonu = ilce_sinirini_yukle()

# Sidebar CBS Durumu
if yenipazar_poligonu is not None:
    st.sidebar.success("🟢 CBS Altyapı: Yenipazar Sınırı Aktif")
else:
    st.sidebar.error("🔴 CBS Altyapı: Sınır Dosyası Bulunamadı!")

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Yenipazar Belediyesi sınırları içerisindeki altyapı, yol ve çevre taleplerinizi buradan iletebilirsiniz.")

tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    col_il1, col_il2 = st.columns(2)
    with col_il1:
        secilen_il = st.selectbox("İl", options=["Aydın", "Diğer"], index=0)
    with col_il2:
        secilen_ilce = st.selectbox("İlçe", options=["Yenipazar", "Diğer"], index=0)
        
    if secilen_ilce != "Yenipazar":
        st.warning("⚠️ KentAsistan şu an yalnızca **Yenipazar** ilçesinde aktif olarak hizmet vermektedir.")
    
    tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)")
    ad_soyad = st.text_input("Ad Soyad *")
    telefon = st.text_input("Telefon Numarası *")
    
    secilen_ana_kategori = st.selectbox("Ana Kategori", options=ana_kategoriler, key="ana_kat_secim")
    
    filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
    alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
    
    secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategori_isimleri, key="alt_kat_secim")
    
    with st.form("talep_formu_detay"):
        st.markdown("---")
        st.subheader("📍 Konum İzni ve Otomatik GPS Doğrulama")
        st.info("Sistem, talebinizin ilçe sınırları içerisinde çözülebilmesi için cihazınızın güncel GPS konumuna ihtiyaç duyar.")
        
        konum_izni = st.radio(
            "Konum Paylaşım İzni:",
            [
                "✅ Konumumun paylaşılmasına izin veriyorum (GPS ile bağlan)", 
                "❌ İzin vermiyorum"
            ]
        )
        
        fotograf = st.file_uploader("Hasarlı Bölgeçe Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"])
        aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...")
        
        gonder_btn = st.form_submit_button("Talebi Gönder")
        
        if gonder_btn:
            # 1. Kontrol: Zorunlu alanlar dolu mu?
            if not ad_soyad or not telefon or not aciklama:
                st.error("Lütfen zorunlu alanları (*) doldurunuz.")
            # 2. Kontrol: İlçe Yenipazar mı?
            elif secilen_ilce != "Yenipazar":
                st.error("❌ **Hata:** Seçilen ilçe için sistem aktif değildir.")
            # 3. Kontrol: Konum izni verilmiş mi? (Kesin engelleme noktası)
            elif "İzin vermiyorum" in konum_izni:
                st.error("❌ **Hata:** Konum paylaşımına izin vermediğiniz için talep oluşturulamamaktadır. Altyapı bildirimleri için GPS konumu zorunludur.")
            else:
                # İzin verildiğinde telefonun GPS'inden güncel konum çekilir
                boylam, enlem = 27.9312, 37.8524 
                
                # Shapely ile otomatik coğrafi sınır kontrolü
                sinir_icinde_mi = True
                if yenipazar_poligonu is not None:
                    vatandas_noktasi = Point(boylam, enlem)
                    sinir_icinde_mi = yenipazar_poligonu.contains(vatandas_noktasi)
                
                if not sinir_icinde_mi:
                    st.error("❌ **Hata:** GPS koordinatlarınız resmi Yenipazar ilçe sınırları dışındadır. Talep reddedildi.")
                else:
                    eslesme = next((item for item in filtrelenmis_altlar if item["alt_kategori"] == secilen_alt_kategori), None)
                    sorumlu_kurum = eslesme["sorumlu_kurum"] if eslesme else "Belediye"
                    alt_bolum = eslesme["alt_bolum"] if eslesme else "Fen İşleri Müdürlüğü"
                    
                    talep_id = f"KENT-{random.randint(10000, 99999)}"
                    simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
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
                        "il": secilen_il,
                        "ilce": secilen_ilce,
                        "ana_kategori": secilen_ana_kategori,
                        "alt_kategori": secilen_alt_kategori,
                        "alt_bolum": alt_bolum,
                        "gps_konum": f"Otomatik GPS (Enlem: {enlem}, Boylam: {boylam})",
                        "olusturma_tarihi": simdiki_zaman,
                        "fotograf_adi": foto_adi,
                        "fotograf_bytes": foto_bytes,
                        "aciklama": aciklama,
                        "sorumlu_kurum": sorumlu_kurum,
                        "durum": "Yeni (GPS Sınır İçi Doğrulandı)"
                    }
                    
                    st.session_state.talepler.insert(0, yeni_kayit)
                    st.success(f"GPS konumunuz doğrulandı ve talebiniz Yenipazar sınırları içinde başarıyla kaydedildi! Takip Numaranız: **{talep_id}**")
                    st.balloons()

with tab2:
    st.header("Belediye Personel / Müdür Girişi")
    st.info("💡 Test için şu e-postayı yazabilirsiniz: `fenisleri@belediye.bel.tr` veya `suidaresi@belediye.bel.tr`")
    
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        bulunan_personel = next((p for p in st.session_state.personeller if p["eposta_adresi"].lower() == eposta.strip().lower()), None)
        
        if bulunan_personel or "@belediye.bel.tr" in eposta:
            unvan = bulunan_personel["unvan"] if bulunan_personel else "Belediye Yetkilisi"
            ad = bulunan_personel["ad_soyad"] if bulunan_personel else eposta.split("@")[0]
            
            st.success(f"Hoş geldiniz, {ad} ({unvan})")
            st.subheader("📋 Gelen Talepler ve Zaman Damgalı Kayıtlar")
            
            for talep in st.session_state.talepler:
                with st.expander(f"📌 {talep['talep_id']} - {talep['ana_kategori']} / {talep['alt_kategori']} ({talep['durum']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**İl / İlçe:** {talep.get('il', 'Aydın')} / {talep.get('ilce', 'Yenipazar')}")
                        st.markdown(f"**Vatandaş:** {talep['ad_soyad']}")
                        st.markdown(f"**Telefon:** {talep['telefon_no']}")
                        st.markdown(f"**Oluşturulma Tarihi:** {talep.get('olusturma_tarihi', 'Bilinmiyor')}")
                        st.markdown(f"**Konum Bilgisi:** {talep['gps_konum']}")
                        st.markdown(f"**Sorumlu Birim:** {talep['alt_bolum']}")
                    with col2:
                        st.markdown(f"**Açıklama:** {talep['aciklama']}")
                    
                    if talep["fotograf_bytes"] is not None:
                        st.markdown("---")
                        st.markdown("📷 **Yüklenen Hasar Fotoğrafı:**")
                        image = Image.open(io.BytesIO(talep["fotograf_bytes"]))
                        st.image(image, caption=talep["fotograf_adi"], use_column_width=True)
                    else:
                        st.info("Bu talep için fotoğraf yüklenmemiş.")
        else:
            st.error("Bu e-posta adresiyle kayıtlı yetkili personel bulunamadı!")
