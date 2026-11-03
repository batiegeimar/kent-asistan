import streamlit as st
import random
from PIL import Image
import io
import json
import base64
import urllib.parse
from datetime import datetime
from shapely.geometry import Point, shape
from supabase import create_client, Client
from streamlit_geolocation import streamlit_geolocation
import requests

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# --- GLOBAL OTURUM HAFIZASI ---
if "personel_giris" not in st.session_state:
    st.session_state["personel_giris"] = False
if "giris_yapan_personel" not in st.session_state:
    st.session_state["giris_yapan_personel"] = None

# Kurumlar Listesi
if "kurumlar" not in st.session_state:
    st.session_state["kurumlar"] = [
        {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
        {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Zabıta / Çevre Koruma"},
        {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Temizlik İşleri Müdürlüğü"},
        {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Park ve Bahçeler Müdürlüğü"},
        {"kurum_adi": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
        {"kurum_adi": "Aydem Elektrik", "alt_bolum": "Elektrik Dağıtım Birimi"},
        {"kurum_adi": "Enerya Doğalgaz", "alt_bolum": "Doğalgaz Acil Servis"}
    ]

# Personel / Kurum Yöneticileri Listesi (Telefon Numarası Tabanlı)
if "personeller" not in st.session_state:
    st.session_state["personeller"] = [
        {"ad_soyad": "Sistem Süper Admin", "telefon_no": "05550000000", "sifre": "admin123", "unvan": "Süper Admin", "sorumlu_birim": "Tüm Sistem"},
        {"ad_soyad": "Ahmet Yılmaz", "telefon_no": "05551111111", "sifre": "12345", "unvan": "Müdür", "sorumlu_birim": "Fen İşleri Müdürlüğü"},
        {"ad_soyad": "Mehmet Su", "telefon_no": "05552222222", "sifre": "12345", "unvan": "Kurum Yetkilisi", "sorumlu_birim": "Su ve Kanalizasyon Müdürlüğü"},
        {"ad_soyad": "Can Elektrikçi", "telefon_no": "05553333333", "sifre": "12345", "unvan": "Kurum Yetkilisi", "sorumlu_birim": "Elektrik Dağıtım Birimi"},
        {"ad_soyad": "Gazci Celal", "telefon_no": "05554444444", "sifre": "12345", "unvan": "Kurum Yetkilisi", "sorumlu_birim": "Doğalgaz Acil Servis"}
    ]

if "yerel_talepler" not in st.session_state:
    st.session_state["yerel_talepler"] = [
        {
            "talep_id": "KENT-48070",
            "alt_kategori": "Yol Bozukluğu ile İlgili Talepler (Çukur vb.)",
            "durum": "Yeni (GPS Sınır İçi Doğrulandı)",
            "ad_soyad": "Test Vatandaş",
            "telefon_no": "0555 123 45 67",
            "olusturma_tarihi": "2026-11-03 12:40:00",
            "gps_konum": "Otomatik GPS (Enlem: 37.935, Boylam: 27.812)",
            "enlem": 37.935,
            "boylam": 27.812,
            "aciklama": "Yol bozuk acil bakım gerekiyor.",
            "fotograf_adi": "Fotoğraf Yok",
            "fotograf_b64": "",
            "atanan_personel": "Ahmet Yılmaz",
            "yönetici_notu": "Fen işleri ekibi yönlendirildi."
        }
    ]

SUPABASE_URL = "https://ziubmjjnvcxfedeyvxm.supabase.co"
SUPABASE_KEY = "sb_publishable_iFUTiJpbyvS-LC-SzwG4g_rgfMBGXi"

@st.cache_resource
def init_supabase():
    try:
        requests.get(f"{SUPABASE_URL}/rest/v1/", headers={"apikey": SUPABASE_KEY}, timeout=3)
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client, None
    except Exception as e:
        return None, str(e)

supabase, baglanti_hatasi = init_supabase()

# Kategori ve Kurum Eşleştirme Matrisi
tum_veriler = [
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Borusu Patlağı", "sorumlu_kurum": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Kesintisi", "sorumlu_kurum": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Yol ve Kaldırımlarla İlgili Talepler", "alt_kategori": "Yol Bozukluğu ile İlgili Talepler (Çukur vb.)", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Yol ve Kaldırımlarla İlgili Talepler", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Elektrik Altyapısı ile İlgili Talepler", "alt_kategori": "Elektrik Kaçağı / Aydınlatma", "sorumlu_kurum": "Aydem Elektrik", "alt_bolum": "Elektrik Dağıtım Birimi"},
    {"ana_kategori": "Doğalgaz Altyapısı ile İlgili Talepler", "alt_kategori": "Doğalgaz Kaçağı / Altyapı", "sorumlu_kurum": "Enerya Doğalgaz", "alt_bolum": "Doğalgaz Acil Servis"},
    {"ana_kategori": "Çevre Kirliliği ile İlgili Talepler", "alt_kategori": "Hafriyat / Kaçak Atık Dökümü", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Zabıta / Çevre Koruma"},
    {"ana_kategori": "Temizlik İşleri ile İlgili Talepler", "alt_kategori": "Çöp Konteyneri Kırık / Eksik", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Temizlik İşleri Müdürlüğü"},
    {"ana_kategori": "Park ve Bahçeler ile İlgili Talepler", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Park ve Bahçeler Müdürlüğü"}
]

ana_kategoriler = sorted(list(set([item["ana_kategori"] for item in tum_veriler])))

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
st.write("Yenipazar Belediyesi ve Paydaş Kurumlar Ortak Çözüm Masası")

tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Kurum / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    col_il1, col_il2 = st.columns(2)
    with col_il1:
        secilen_il = st.selectbox("İl", options=["Aydın", "Diğer"], index=0, key="vat_il")
    with col_il2:
        secilen_ilce = st.selectbox("İlçe", options=["Yenipazar", "Diğer"], index=0, key="vat_ilce")
        
    if secilen_ilce != "Yenipazar":
        st.warning("⚠️ KentAsistan şu an yalnızca **Yenipazar** ilçesinde aktif olarak hizmet vermektedir.")
    
    tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)", key="vat_tc")
    ad_soyad = st.text_input("Ad Soyad *", key="vat_ad")
    telefon = st.text_input("Telefon Numarası *", key="vat_tel")
    
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
        ],
        key="vat_konum_izni"
    )
    
    fotograf = st.file_uploader("Hasarlı Bölgeye Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"], key="vat_foto")
    aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...", key="vat_aciklama")
    
    gonder_btn = st.button("Talebi Gönder", key="vat_gonder_btn")
    
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
                sorumlu_kurum = eslesme["sorumlu_kurum"] if eslesme else "Yenipazar Belediyesi"
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
                    "enlem": enlem,
                    "boylam": boylam,
                    "aciklama": aciklama,
                    "fotograf_adi": foto_adi,
                    "fotograf_b64": foto_b64,
                    "olusturma_tarihi": simdiki_zaman,
                    "durum": "Yeni (GPS Sınır İçi Doğrulandı)",
                    "atanan_personel": "Atanmadı",
                    "yönetici_notu": "Henüz not eklenmedi"
                }
                
                st.session_state["yerel_talepler"].insert(0, yeni_kayit_veri)
                st.success(f"Talebiniz başarıyla kaydedildi! Sorumlu Kurum: **{sorumlu_kurum}** | Takip Numaranız: **{talep_id}**")
                st.balloons()

with tab2:
    st.header("Kurum ve Personel Giriş Paneli")
    st.info("💡 **Test Hesapları (Telefon Numarası ile):**\n- Süper Admin: `05550000000` / Şifre: `admin123`\n- Fen İşleri: `05551111111` / Şifre: `12345`\n- ASKİ (Su): `05552222222` / Şifre: `12345`\n- Aydem (Elektrik): `05553333333` / Şifre: `12345`\n- Enerya (Doğalgaz): `05554444444` / Şifre: `12345`")

    if not st.session_state["personel_giris"]:
        tel_giris = st.text_input("Telefon Numarası (Örn: 0555...)", key="personel_tel_input")
        sifre_giris = st.text_input("Şifre", type="password", key="personel_sifre_input")
        
        if st.button("Güvenli Giriş Yap", key="personel_giris_btn"):
            if tel_giris:
                eslesen_personel = None
                clean_tel = tel_giris.strip().replace(" ", "")
                for p in st.session_state["personeller"]:
                    if p["telefon_no"].replace(" ", "") == clean_tel and p["sifre"] == sifre_giris:
                        eslesen_personel = p
                        break
                
                if eslesen_personel:
                    st.session_state["personel_giris"] = True
                    st.session_state["giris_yapan_personel"] = eslesen_personel
                    st.rerun()
                else:
                    st.error("Hatalı telefon numarası veya şifre!")
            else:
                st.warning("Lütfen telefon numaranızı giriniz.")

    # Oturum Açıldığında
    if st.session_state["personel_giris"]:
        personel = st.session_state["giris_yapan_personel"]
        st.success(f"Hoş geldiniz, {personel['ad_soyad']} ({personel['unvan']} - {personel['sorumlu_birim']})")
        
        if st.button("🚪 Çıkış Yap", key="cikis_yap_btn"):
            st.session_state["personel_giris"] = False
            st.session_state["giris_yapan_personel"] = None
            st.rerun()

        # --- SÜPER ADMIN ÖZEL YÖNETİM ALANI ---
        if personel["unvan"] == "Süper Admin":
            st.markdown("---")
            st.subheader("👑 Süper Admin / Sistem Yönetim Paneli")
            
            admin_secim = st.radio("Yönetim İşlemi Seçin:", ["Kurum / Birim Listesi ve Ekle", "Kurum Yöneticisi / Personel Ekle"])
            
            if admin_secim == "Kurum / Birim Listesi ve Ekle":
                st.markdown("#### 🏢 Mevcut Kurum ve Altyapı Birimleri")
                for k in st.session_state["kurumlar"]:
                    st.write(f"- **{k['kurum_adi']}** / {k['alt_bolum']}")
                
                st.markdown("#### ➕ Yeni Kurum / Birim Tanımla")
                yeni_kurum_adi = st.text_input("Kurum Adı (Örn: Enerya Doğalgaz)")
                yeni_birim_adi = st.text_input("Alt Birim / Müdürlük Adı (Örn: Doğalgaz Acil Servis)")
                if st.button("Kurumu Sisteme Ekle"):
                    if yeni_kurum_adi and yeni_birim_adi:
                        st.session_state["kurumlar"].append({"kurum_adi": yeni_kurum_adi, "alt_bolum": yeni_birim_adi})
                        st.success(f"✅ {yeni_kurum_adi} - {yeni_birim_adi} başarıyla sisteme eklendi!")
                        st.rerun()
                    else:
                        st.error("Lütfen tüm alanları doldurun.")
            
            elif admin_secim == "Kurum Yöneticisi / Personel Ekle":
                st.markdown("#### 👥 Kayıtlı Kurum Yöneticileri")
                for pers in st.session_state["personeller"]:
                    st.write(f"- **{pers['ad_soyad']}** ({pers['telefon_no']}) ➔ {pers['sorumlu_birim']} [{pers['unvan']}]")
                
                st.markdown("#### ➕ Yeni Kurum Yöneticisi / Personel Tanımla")
                p_ad = st.text_input("Ad Soyad")
                p_tel = st.text_input("Telefon Numarası (Giriş
