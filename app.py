import streamlit as st
import random
from PIL import Image
import io
import json
from datetime import datetime
from shapely.geometry import Point, shape
from supabase import create_client, Client

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# Supabase Bağlantı Kurulumu
@st.cache_resource
def init_supabase():
    try:
        # Önce st.secrets üzerinden okumayı dene
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception:
        # Eğer secrets paneli okunamazsa doğrudan kod içindeki projenin bilgileriyle bağlan
        url = "https://ziubmjjnvcxfedeyvxm.supabase.co"
        key = "sb_publishable_iFUTiJpbyvS-LC-SzwG4g_rgfMBGXi"
    
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase Bağlantı Hatası Detayı: {e}")
        return None

supabase = init_supabase()

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

if supabase is not None:
    st.sidebar.success("🟢 Supabase: Bulut Veritabanı Aktif")
else:
    st.sidebar.warning("🟡 Supabase: Bağlantı Bilgileri Bekleniyor")

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
        
        fotograf = st.file_uploader("Hasarlı Bölgeye Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"])
        aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...")
        
        gonder_btn = st.form_submit_button("Talebi Gönder")
        
        if gonder_btn:
            if not ad_soyad or not telefon or not aciklama:
                st.error("Lütfen zorunlu alanları (*) doldurunuz.")
            elif secilen_ilce != "Yenipazar":
                st.error("❌ **Hata:** Seçilen ilçe için sistem aktif değildir.")
            elif "İzin vermiyorum" in konum_izni:
                st.error("❌ **Hata:** Konum paylaşımına izin vermediğiniz için talep oluşturulamamaktadır. Altyapı bildirimleri için GPS konumu zorunludur.")
            else:
                boylam, enlem = 27.9312, 37.8524 # Canlıda HTML5 Geolocation API ile alınacak koordinat
                
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
                    
                    foto_adi = "Fotoğraf Yok"
                    if fotograf is not None:
                        foto_adi = fotograf.name
                    
                    yeni_kayit_veri = {
                        "talep_id": talep_id,
                        "tc_kimlik_no": tc_kimlik if tc_kimlik else "Belirtilmemiş",
                        "ad_soyad": ad_soyad,
                        "telefon_no": telefon,
                        "il": secilen_il,
                        "ilce": secilen_ilce,
                        "ana_kategori": secilen_ana_kategori,
                        "alt_kategori": secilen_alt_kategori,
                        "alt_bolum": alt_bolum,
                        "sorumlu_kurum": sorumlu_kurum,
                        "gps_konum": f"Otomatik GPS (Enlem: {enlem}, Boylam: {boylam})",
                        "aciklama": aciklama,
                        "fotograf_adi": foto_adi,
                        "durum": "Yeni (GPS Sınır İçi Doğrulandı)"
                    }
                    
                    # Supabase veritabanına kayıt ekleme
                    if supabase is not None:
                        try:
                            supabase.table("talepler").insert(yeni_kayit_veri).execute()
                            st.success(f"Talebiniz Supabase veritabanına başarıyla kaydedildi! Takip Numaranız: **{talep_id}**")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Veritabanı kayıt hatası: {e}")
                    else:
                        st.error("Supabase bağlantısı kurulamadı!")

with tab2:
    st.header("Belediye Personel / Müdür Girişi")
    st.info("💡 Test için oluşturduğumuz e-postayı yazabilirsiniz (Örn: `fenisleri@belediye.bel.tr` / Şifre: `12345`)")
    
    eposta_giris = st.text_input("Personel E-Posta Adresi")
    sifre_giris = st.text_input("Şifre", type="password")
    
    if st.button("Güvenli Giriş Yap"):
        if supabase is not None and eposta_giris:
            # Supabase personeller tablosundan yetki kontrolü
            response = supabase.table("personeller").select("*").eq("eposta_adresi", eposta_giris.strip().lower()).eq("sifre", sifre_giris).execute()
            personel_listesi = response.data
            
            if personel_listesi:
                personel = personel_listesi[0]
                st.success(f"Hoş geldiniz, {personel['ad_soyad']} ({personel['unvan']} - {personel['sorumlu_birim']})")
                
                st.subheader(f"📋 {personel['sorumlu_birim']} - Gelen Talepler (Supabase Canlı Veri)")
                
                # Sadece ilgili birimin taleplerini çekelim (RBAC - Rol Tabanlı Filtreleme)
                talep_response = supabase.table("talepler").select("*").eq("alt_bolum", personel['sorumlu_birim']).order("olusturma_tarihi", desc=True).execute()
                birim_talepleri = talep_response.data
                
                if birim_talepleri:
                    for talep in birim_talepleri:
                        with st.expander(f"📌 {talep['talep_id']} - {talep['alt_kategori']} ({talep['durum']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Vatandaş:** {talep['ad_soyad']}")
                                st.markdown(f"**Telefon:** {talep['telefon_no']}")
                                st.markdown(f"**Oluşturulma Tarihi:** {talep['olusturma_tarihi']}")
                                st.markdown(f"**Konum:** {talep['gps_konum']}")
                            with col2:
                                st.markdown(f"**Açıklama:** {talep['aciklama']}")
                else:
                    st.info("Biriminize ait henüz gelen aktif talep bulunmamaktadır.")
            else:
                st.error("Hatalı e-posta adresi veya şifre!")
        else:
            st.warning("Lütfen e-posta adresinizi giriniz ve Supabase bağlantısını kontrol ediniz.")
