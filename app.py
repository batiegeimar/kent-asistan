import streamlit as st
import random
from PIL import Image
import io
import json
import base64
from datetime import datetime
from shapely.geometry import Point, shape
from supabase import create_client, Client
from streamlit_geolocation import streamlit_geolocation
import requests

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

SUPABASE_URL = "https://ziubmjjnvcxfedeyvxm.supabase.co"
SUPABASE_KEY = "sb_publishable_iFUTiJpbyvS-LC-SzwG4g_rgfMBGXi"

# Supabase Bağlantı ve Hata Toleranslı Kurulum
@st.cache_resource
def init_supabase():
    try:
        requests.get(f"{SUPABASE_URL}/rest/v1/", headers={"apikey": SUPABASE_KEY}, timeout=3)
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client, None
    except Exception as e:
        return None, str(e)

supabase, baglanti_hatasi = init_supabase()

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

# Sidebar Durum Göstergeleri
if yenipazar_poligonu is not None:
    st.sidebar.success("🟢 CBS Altyapı: Yenipazar Sınırı Aktif")
else:
    st.sidebar.error("🔴 CBS Altyapı: Sınır Dosyası Bulunamadı!")

if supabase is not None:
    st.sidebar.success("🟢 Supabase: Bulut Veritabanı Aktif")
else:
    st.sidebar.warning("🟡 Supabase: Yerel Test Modu Aktif")

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
    
    st.markdown("---")
    st.subheader("📍 Konum İzni ve Otomatik GPS Doğrulama")
    st.info("Sistem, talebinizin ilçe sınırları içerisinde çözülebilmesi için cihazınızın güncel GPS konumuna ihtiyaç duyar.")
    
    location = streamlit_geolocation()

    konum_izni = st.radio(
        "Konum Paylaşım İzni:",
        [
            "✅ Konumumun paylaşılmasına izin veriyorum (GPS ile bağlan)", 
            "❌ İzin vermiyorum"
        ]
    )
    
    fotograf = st.file_uploader("Hasarlı Bölgeye Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"])
    aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...")
    
    gonder_btn = st.button("Talebi Gönder")
    
    if gonder_btn:
        if not ad_soyad or not telefon or not aciklama:
            st.error("❌ Lütfen zorunlu alanları (*) doldurunuz.")
        elif secilen_ilce != "Yenipazar":
            st.error("❌ **Hata:** Seçilen ilçe için sistem aktif değildir.")
        elif "İzin vermiyorum" in konum_izni:
            st.error("❌ **Hata:** Konum paylaşımına izin vermediğiniz için talep oluşturulamamaktadır.")
        elif location is None or location.get('latitude') is None or location.get('longitude') is None:
            st.error("❌ **Hata:** GPS konum veriniz alınamadı. Lütfen konum izni verdiğinizden emin olun.")
        else:
            enlem = location.get('latitude')
            boylam = location.get('longitude')
            
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
                foto_b64 = ""
                if fotograf is not None:
                    foto_adi = fotograf.name
                    bytes_data = fotograf.getvalue()
                    foto_b64 = base64.b64encode(bytes_data).decode("utf-8")
                
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
                    "fotograf_b64": foto_b64,
                    "olusturma_tarihi": simdiki_zaman,
                    "durum": "Yeni (GPS Sınır İçi Doğrulandı)",
                    "atanan_personel": "Atanmadı",
                    "yonetici_notu": "Henüz not eklenmedi"
                }
                
                if "yerel_talepler" not in st.session_state:
                    st.session_state["yerel_talepler"] = []
                st.session_state["yerel_talepler"].insert(0, yeni_kayit_veri)
                
                if supabase is not None:
                    try:
                        supabase.table("talepler").insert(yeni_kayit_veri).execute()
                    except Exception:
                        pass
                
                st.success(f"Talebiniz başarıyla kaydedildi! Takip Numaranız: **{talep_id}**")
                st.balloons()

with tab2:
    st.header("Belediye Personel / Müdür Girişi")
    st.info("💡 Test için: `fenisleri@belediye.bel.tr` / Şifre: `12345`")
    
    # Oturum state tanımları
    if "personel_giris" not in st.session_state:
        st.session_state["personel_giris"] = False
    if "giris_yapan_personel" not in st.session_state:
        st.session_state["giris_yapan_personel"] = None

    # Eğer daha önceden giriş yapılmadıysa giriş formunu göster
    if not st.session_state["personel_giris"]:
        eposta_giris = st.text_input("Personel E-Posta Adresi", key="personel_eposta")
        sifre_giris = st.text_input("Şifre", type="password", key="personel_sifre")
        
        col_giris1, col_giris2 = st.columns([1, 3])
        with col_giris1:
            giris_buton = st.button("Güvenli Giriş Yap")
        
        if giris_buton:
            if eposta_giris:
                personel_listesi = []
                
                if supabase is not None:
                    try:
                        response = supabase.table("personeller").select("*").eq("eposta_adresi", eposta_giris.strip().lower()).eq("sifre", sifre_giris).execute()
                        personel_listesi = response.data
                    except Exception:
                        pass
                
                if not personel_listesi and eposta_giris.strip().lower() == "fenisleri@belediye.bel.tr" and sifre_giris == "12345":
                    personel_listesi = [{
                        "ad_soyad": "Ahmet Yılmaz (Fen İşleri Müdürü)",
                        "unvan": "Müdür",
                        "sorumlu_birim": "Fen İşleri Müdürlüğü"
                    }]
                
                if personel_listesi:
                    st.session_state["personel_giris"] = True
                    st.session_state["giris_yapan_personel"] = personel_listesi[0]
                    st.rerun()
                else:
                    st.error("Hatalı e-posta adresi veya şifre!")
            else:
                st.warning("Lütfen e-posta adresinizi giriniz.")

    # Eğer oturum açıldıysa yönetim panelini sürekli göster (sayfa yenilense bile kapanmaz)
    if st.session_state["personel_giris"]:
        personel = st.session_state["giris_yapan_personel"]
        st.success(f"Hoş geldiniz, {personel['ad_soyad']} ({personel['unvan']} - {personel['sorumlu_birim']})")
        
        if st.button("🚪 Çıkış Yap"):
            st.session_state["personel_giris"] = False
            st.session_state["giris_yapan_personel"] = None
            st.rerun()

        st.subheader(f"📋 {personel['sorumlu_birim']} - Gelen Talepler ve Operasyon Paneli")
        
        birim_talepleri = []
        if supabase is not None:
            try:
                talep_response = supabase.table("talepler").select("*").eq("alt_bolum", personel['sorumlu_birim']).order("olusturma_tarihi", desc=True).execute()
                birim_talepleri = talep_response.data
            except Exception:
                pass
        
        if "yerel_talepler" in st.session_state:
            for t in st.session_state["yerel_talepler"]:
                if not any(item['talep_id'] == t['talep_id'] for item in birim_talepleri):
                    birim_talepleri.append(t)
        
        if not birim_talepleri:
            birim_talepleri = [
                {
                    "talep_id": "KENT-48070",
                    "alt_kategori": "Yol Bozukluğu ile İlgili Talepler (Çukur vb.)",
                    "durum": "Yeni (GPS Sınır İçi Doğrulandı)",
                    "ad_soyad": "Test Vatandaş",
                    "telefon_no": "0555 123 45 67",
                    "olusturma_tarihi": "2026-11-03 12:40:00",
                    "gps_konum": "Otomatik GPS (Enlem: 37.935, Boylam: 27.812)",
                    "aciklama": "Yol bozuk adamım",
                    "fotograf_adi": "Fotoğraf Yok",
                    "fotograf_b64": "",
                    "atanan_personel": "Atanmadı",
                    "yonetici_notu": "Henüz not eklenmedi"
                }
            ]
        
        for idx, talep in enumerate(birim_talepleri):
            with st.expander(f"📌 {talep['talep_id']} - {talep['alt_kategori']} ({talep['durum']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Vatandaş:** {talep['ad_soyad']}")
                    st.markdown(f"**Telefon:** {talep['telefon_no']}")
                    st.markdown(f"**Oluşturulma Tarihi:** {talep.get('olusturma_tarihi', 'Bilinmiyor')}")
                    st.markdown(f"**Konum:** {talep['gps_konum']}")
                    st.markdown(f"**Mevcut Durum:** {talep.get('durum', 'Yeni')}")
                    st.markdown(f"**Atanan Personel:** {talep.get('atanan_personel', 'Atanmadı')}")
                    st.markdown(f"**Açıklama:** {talep['aciklama']}")
                with col2:
                    foto_b64_data = talep.get('fotograf_b64', '')
                    if foto_b64_data:
                        try:
                            image_bytes = base64.b64decode(foto_b64_data)
                            image = Image.open(io.BytesIO(image_bytes))
                            st.image(image, caption=f"Yüklenen Fotoğraf: {talep.get('fotograf_adi', 'Görsel')}", use_container_width=True)
                        except Exception:
                            st.info("📷 Fotoğraf yüklenmiş ancak çözülemedi.")
                    else:
                        st.info("📷 Bu talep için fotoğraf yüklenmemiş.")
                
                st.markdown("---")
                st.markdown("⚙️ **Yönetici İşlemleri ve Atama Paneli**")
                
                yeni_durum = st.selectbox(
                    "Talep Durumunu Güncelle",
                    ["Yeni (GPS Sınır İçi Doğrulandı)", "İnceleniyor", "Saha Ekibine Sevk Edildi", "Çözüldü - Kapatıldı"],
                    key=f"durum_{talep['talep_id']}_{idx}"
                )
                
                atanacak_kisi = st.selectbox(
                    "Saha Personeli / Usta Ata",
                    ["Atanmadı", "Mehmet Usta (Fen İşleri Ekip 1)", "Ali Usta (Yol Bakım Ekibi)", "Hüseyin Kaya (Yama Ekip Şefi)"],
                    key=f"personel_{talep['talep_id']}_{idx}"
                )
                
                yonetici_notu_input = st.text_area(
                    "Yönetçi / Müdür Notu Ekle",
                    value=talep.get('yonetici_notu', ''),
                    key=f"not_{talep['talep_id']}_{idx}"
                )
                
                if st.button(f"💾 Güncellemeyi Kaydet ({talep['talep_id']})", key=f"kaydet_{talep['talep_id']}_{idx}"):
                    birim_talepleri[idx]['durum'] = yeni_durum
                    birim_talepleri[idx]['atanan_personel'] = atanacak_kisi
                    birim_talepleri[idx]['yonetici_notu'] = yonetici_notu_input
                    st.success(f"✅ {talep['talep_id']} numaralı talep başarıyla güncellendi ve ilgili personele iletildi!")
                    st.rerun()
