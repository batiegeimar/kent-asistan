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

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# --- GLOBAL OTURUM HAFIZASI ---
if "personel_giris" not in st.session_state:
    st.session_state["personel_giris"] = False
if "giris_yapan_personel" not in st.session_state:
    st.session_state["giris_yapan_personel"] = None

# SUPABASE BAĞLANTI BİLGİLERİ (Güvenli Secrets Entegrasyonu)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # Yerel testler için yedek (fallback) tanımlama
    SUPABASE_URL = "https://ziubmjjnvcxefodeyvxm.supabase.co/rest/v1/"
    SUPABASE_KEY = "sb_publishable_iFUTiJplbyvS-LC-SzwG4g_rgfMbGXi"

@st.cache_resource
def init_supabase():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client, None
    except Exception as e:
        return None, str(e)

supabase, baglanti_hatasi = init_supabase()

# Kurumlar Listesi
kurumlar_listesi = [
    {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Zabıta / Çevre Koruma"},
    {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Temizlik İşleri Müdürlüğü"},
    {"kurum_adi": "Yenipazar Belediyesi", "alt_bolum": "Park ve Bahçeler Müdürlüğü"},
    {"kurum_adi": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"kurum_adi": "Aydem Elektrik", "alt_bolum": "Elektrik Dağıtım Birimi"},
    {"kurum_adi": "Enerya Doğalgaz", "alt_bolum": "Doğalgaz Acil Servis"}
]

# Kategori ve Kurum Eşleştirme Matrisi
tum_veriler = [
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Borusu Patlağı", "sorumlu_kurum": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Su Altyapısı ile İlgili Talepler", "alt_kategori": "Su Kesintisi", "sorumlu_kurum": "Aydın Su ve Kanalizasyon İdaresi (ASKİ)", "alt_bolum": "Su ve Kanalizasyon Müdürlüğü"},
    {"ana_kategori": "Yol/Kaldırım Talepleri", "alt_kategori": "Yol Bozukluğu (Çukur vb.)", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Yol/Kaldırım Talepleri", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Fen İşleri Müdürlüğü"},
    {"ana_kategori": "Elektrik Altyapısı", "alt_kategori": "Elektrik Kaçağı / Aydınlatma", "sorumlu_kurum": "Aydem Elektrik", "alt_bolum": "Elektrik Dağıtım Birimi"},
    {"ana_kategori": "Doğalgaz Altyapısı", "alt_kategori": "Doğalgaz Kaçağı / Altyapı", "sorumlu_kurum": "Enerya Doğalgaz", "alt_bolum": "Doğalgaz Acil Servis"},
    {"ana_kategori": "Çevre Kirliliği", "alt_kategori": "Hafriyat / Kaçak Atık Dökümü", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Zabıta / Çevre Koruma"},
    {"ana_kategori": "Temizlik İşleri", "alt_kategori": "Çöp Konteyneri Kırık / Eksik", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Temizlik İşleri Müdürlüğü"},
    {"ana_kategori": "Park ve Bahçeler", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Yenipazar Belediyesi", "alt_bolum": "Park ve Bahçeler Müdürlüğü"}
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
    st.sidebar.error("🔴 Supabase Bağlantı Hatası!")

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
    telefon = st.text_input("Telefon Numarası (Örn: 0555...) *", key="vat_tel")
    
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
                    "telefon_no": telefon.strip(),
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
                    "saha_fotograf_adi": "Yüklenmedi",
                    "saha_fotograf_b64": "",
                    "olusturma_tarihi": simdiki_zaman,
                    "durum": "Yeni (GPS Sınır İçi Doğrulandı)",
                    "atanan_personel": "Atanmadı",
                    "yönetici_notu": "Henüz not eklenmedi"
                }
                
                if supabase is not None:
                    try:
                        supabase.table("talepler").insert(yeni_kayit_veri).execute()
                        st.success(f"Talebiniz başarıyla kaydedildi! Sorumlu Kurum: **{sorumlu_kurum}** | Takip Numaranız: **{talep_id}**")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Veritabanı kayıt hatası: {e}")
                else:
                    st.error("Supabase bağlantısı kurulamadı.")

with tab2:
    st.header("Kurum ve Personel Giriş Paneli")
    st.info("💡 **Giriş Bilgisi:** Supabase `personeller` tablosundaki kayıtlı telefon numaranız ve şifrenizle giriş yapabilirsiniz.")

    if not st.session_state["personel_giris"]:
        tel_giris = st.text_input("Telefon Numarası (Örn: 0555...)", key="personel_tel_input")
        sifre_giris = st.text_input("Şifre", type="password", key="personel_sifre_input")
        
        if st.button("Güvenli Giriş Yap", key="personel_giris_btn"):
            if tel_giris and sifre_giris:
                try:
                    clean_tel = tel_giris.strip().replace(" ", "")
                    res = supabase.table("personeller").select("*").eq("telefon_no", clean_tel).eq("sifre", sifre_giris).execute()
                    personeller_listesi = res.data
                    
                    if personeller_listesi and len(personeller_listesi) > 0:
                        eslesen_personel = personeller_listesi[0]
                        st.session_state["personel_giris"] = True
                        st.session_state["giris_yapan_personel"] = eslesen_personel
                        st.rerun()
                    else:
                        st.error("Hatalı telefon numarası veya şifre!")
                except Exception as e:
                    st.error(f"Giriş sorgulama hatası: {e}")
            else:
                st.warning("Lütfen telefon numaranızı ve şifrenizi giriniz.")

    # Oturum Açıldığında
    if st.session_state["personel_giris"]:
        personel = st.session_state["giris_yapan_personel"]
        st.success(f"Hoş geldiniz, {personel['ad_soyad']} ({personel['unvan']} - {personel['sorumlu_birim']})")
        
        if st.button("🚪 Çıkış Yap", key="cikis_yap_btn"):
            st.session_state["personel_giris"] = False
            st.session_state["giris_yapan_personel"] = None
            st.rerun()

        # 👑 TAMAMEN VERİTABANI ODAKLI SÜPER ADMIN KONTROLÜ
        # unvan alanı 'Süper_Admin' veya 'Süper Admin' olanlar doğrudan platform yöneticisidir.
        unvan_degeri = str(personel.get("unvan", "")).strip().lower()
        is_super_admin = unvan_degeri in ["süper_admin", "süper admin", "super_admin", "super admin"]

        # =========================================================================
        # 👑 1. SÜPER ADMIN PANELI (Yalnızca Kurum/Yönetici Atama ve Sistem Matrisi)
        # =========================================================================
        if is_super_admin:
            st.markdown("---")
            st.subheader("👑 Süper Admin - Platform Yönetim Paneli")
            st.info("Platform Sahibi olarak yalnızca paydaş kurumları, alt birimleri ve bu birimlerin kurum yöneticilerini (müdürlerini) veritabanı üzerinden yönetebilirsiniz.")
            
            admin_secim = st.radio(
                "Yönetim İşlemi Seçin:", 
                [
                    "📊 Sistem Kurum ve Yetkili Matrisi (Genel Liste)", 
                    "👥 Kurum Yöneticisi / Müdür Ekle"
                ], 
                key="admin_radio_secim"
            )
            
            if admin_secim == "📊 Sistem Kurum ve Yetkili Matrisi (Genel Liste)":
                st.markdown("#### 🌐 Supabase Kayıtlı Kurumlar, Birimler ve Yöneticiler")
                try:
                    p_res = supabase.table("personeller").select("*").execute()
                    tum_personeller = p_res.data
                    
                    for kurum in kurumlar_listesi:
                        kurum_adi = kurum["kurum_adi"]
                        birim_adi = kurum["alt_bolum"]
                        
                        ilgili_yetkililer = [p for p in tum_personeller if p.get("sorumlu_birim") == birim_adi]
                        
                        with st.expander(f"🏛️ {kurum_adi} ➔ {birim_adi}"):
                            if ilgili_yetkililer:
                                st.markdown("**Atanmış Kurum Yöneticileri:**")
                                for y in ilgili_yetkililer:
                                    st.write(f"- 👤 **{y['ad_soyad']}** | Tel: `{y.get('telefon_no')}` | Unvan: *{y['unvan']}*")
                            else:
                                st.warning("⚠️ Bu birime henüz kurum yöneticisi atanmamış.")
                except Exception as e:
                    st.error(f"Matris yüklenirken hata: {e}")

            elif admin_secim == "👥 Kurum Yöneticisi / Müdür Ekle":
                st.markdown("#### ➕ Supabase Veritabanına Kurum Yöneticisi Tanımla")
                p_ad = st.text_input("Yöneticinin Adı Soyadı", key="p_ad_input")
                p_tel = st.text_input("Telefon Numarası (Giriş için Örn: 0555...)", key="p_tel_input")
                p_sifre = st.text_input("Şifre", type="password", key="p_sifre_input")
                p_unvan = st.selectbox("Unvan", ["Kurum Yetkilisi", "Fen İşleri Müdürü", "Su ve Kanalizasyon Amiri", "Park ve Bahçeler Amiri", "Zabıta Amiri"], key="p_unvan_select")
                
                birim_secenekleri = [k["alt_bolum"] for k in kurumlar_listesi]
                p_birim = st.selectbox("Sorumlu Olduğu Kurum / Birim", birim_secenekleri, key="p_birim_select")
                
                if st.button("Supabase'e Kurum Yöneticisi Kaydet", key="yonetici_olustur_btn"):
                    if p_ad and p_tel and p_sifre:
                        try:
                            yeni_personel_veri = {
                                "ad_soyad": p_ad,
                                "telefon_no": p_tel.strip(),
                                "sifre": p_sifre,
                                "unvan": p_unvan,
                                "sorumlu_birim": p_birim
                            }
                            supabase.table("personeller").insert(yeni_personel_veri).execute()
                            st.success(f"✅ {p_ad} başarıyla kurum yöneticisi olarak eklendi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt eklenirken hata oluştu: {e}")
                    else:
                        st.error("Lütfen zorunlu alanları doldurun.")

        # =========================================================================
        # 🏛️ 2. KURUM YETKİLİSİ / MÜDÜR PANELI (Operasyon & Saha Personeli Yönetimi)
        # =========================================================================
        else:
            st.markdown("---")
            st.subheader(f"📋 {personel['sorumlu_birim']} - Kurum Operasyon Paneli")
            st.info("Kurum yöneticisi olarak biriminize gelen talepleri inceleyebilir, saha personellerinize yönlendirebilir ve süreçleri kapatabilirsiniz.")
            
            try:
                t_res = supabase.table("talepler").select("*").execute()
                sup_talepler = t_res.data
            except Exception as e:
                sup_talepler = []
                st.error(f"Talepler yüklenirken hata: {e}")

            # Sadece kendi birimine gelen talepleri filtrele
            gosterilecek_talepler = [t for t in sup_talepler if t.get('alt_bolum') == personel['sorumlu_birim']]
            
            if not gosterilecek_talepler:
                st.info("Biriminize ait aktif talep bulunmamaktadır.")
            
            for idx, talep in enumerate(gosterilecek_talepler):
                with st.expander(f"📌 {talep['talep_id']} - {talep['alt_kategori']} ({talep['durum']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Vatandaş:** {talep['ad_soyad']}")
                        st.markdown(f"**Telefon:** {talep['telefon_no']}")
                        st.markdown(f"**Sorumlu Kurum:** {talep.get('sorumlu_kurum', 'Belediye')}")
                        st.markdown(f"**Tarih:** {talep.get('olusturma_tarihi', 'Bilinmiyor')}")
                        st.markdown(f"**Konum:** {talep['gps_konum']}")
                        st.markdown(f"**Mevcut Durum:** {talep.get('durum', 'Yeni')}")
                        st.markdown(f"**Atanan Saha Personeli:** {talep.get('atanan_personel', 'Atanmadı')}")
                        st.markdown(f"**Açıklama:** {talep['aciklama']}")
                        st.markdown(f"**Yönetici Notu:** {talep.get('yönetici_notu', 'Yok')}")
                        
                        lat = talep.get('enlem')
                        lon = talep.get('boylam')
                        if lat and lon:
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                            st.markdown(f"🗺️ **[Google Haritalar'da Aç ve Rota Oluştur]({maps_url})**", unsafe_allow_html=True)
                        
                        if talep.get('atanan_personel') != "Atanmadı":
                            wa_mesaj = f"🔔 *Yeni Saha Görevi ({talep['talep_id']})*\n*Kategori:* {talep['alt_kategori']}\n*Açıklama:* {talep['aciklama']}\n*Konum:* https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                            encoded_msg = urllib.parse.quote(wa_mesaj)
                            wa_url = f"https://wa.me/?text={encoded_msg}"
                            st.markdown(f"💬 **[WhatsApp ile Saha Personeline Gönder]({wa_url})**", unsafe_allow_html=True)

                        if talep.get('durum') == "Çözüldü - Kapatıldı":
                            vatandas_tel = talep.get('telefon_no', '').strip()
                            vat_mesaj = f"Sayın {talep['ad_soyad']}, {talep['talep_id']} numaralı talebiniz kurumumuz tarafından başarıyla çözümlenmiştir. Sağlıklı günler dileriz."
                            encoded_vat_msg = urllib.parse.quote(vat_mesaj)
                            vat_wa_url = f"https://wa.me/{vatandas_tel}?text={encoded_vat_msg}"
                            st.markdown(f"✅ **[Vatandaşa WhatsApp ile Bilgi Ver]({vat_wa_url})**", unsafe_allow_html=True)

                    with col2:
                        st.markdown("📷 **Vatandaş Hasar Fotoğrafı:**")
                        foto_b64_data = talep.get('fotograf_b64', '')
                        if foto_b64_data:
                            try:
                                image_bytes = base64.b64decode(foto_b64_data)
                                image = Image.open(io.BytesIO(image_bytes))
                                st.image(image, caption="Vatandaş Görseli", use_container_width=True)
                            except Exception:
                                st.info("Görsel yüklenemedi.")
                        else:
                            st.info("Vatandaş fotoğraf yüklememiş.")

                        st.markdown("---")
                        st.markdown("🛠️ **Saha Çözüm / Bitiş Fotoğrafı:**")
                        saha_foto_b64 = talep.get('saha_fotograf_b64', '')
                        if saha_foto_b64:
                            try:
                                s_image_bytes = base64.b64decode(saha_foto_b64)
                                s_image = Image.open(io.BytesIO(s_image_bytes))
                                st.image(s_image, caption="Saha Çözüm Görseli", use_container_width=True)
                            except Exception:
                                st.info("Saha görseli çözülemedi.")
                        else:
                            st.info("Saha bitiş fotoğrafı henüz yüklenmedi.")
                    
                    st.markdown("---")
                    st.markdown("⚙️ **Operasyon Yönetimi ve Durum Güncelleme**")
                    
                    durumlar = ["Yeni (GPS Sınır İçi Doğrulandı)", "İnceleniyor", "Saha Ekibine Sevk Edildi", "Çözüldü - Kapatıldı"]
                    mevcut_durum = talep.get('durum', durumlar[0])
                    durum_index = durumlar.index(mevcut_durum) if mevcut_durum in durumlar else 0

                    try:
                        pers_res = supabase.table("personeller").select("ad_soyad").execute()
                        personeller = ["Atanmadı"] + [p["ad_soyad"] for p in pers_res.data]
                    except Exception:
                        personeller = ["Atanmadı"]

                    mevcut_personel = talep.get('atanan_personel', "Atanmadı")
                    personel_index = personeller.index(mevcut_personel) if mevcut_personel in personeller else 0

                    with st.form(key=f"form_{talep['talep_id']}_{idx}"):
                        yeni_durum = st.selectbox("Talep Durumunu Güncelle", durumlar, index=durum_index, key=f"durum_sel_{talep['talep_id']}_{idx}")
                        atanacak_kisi = st.selectbox("Saha Personeli Ata", personeller, index=personel_index, key=f"personel_sel_{talep['talep_id']}_{idx}")
                        yonetici_notu_input = st.text_area("Kurum Notu Ekle", value=talep.get('yönetici_notu', ''), key=f"not_input_{talep['talep_id']}_{idx}")
                        saha_fotograf_yukleme = st.file_uploader("Sahadan Çözüm Fotoğrafı Yükle", type=["jpg", "jpeg", "png"], key=f"saha_foto_up_{talep['talep_id']}_{idx}")
                        
                        kaydet_buton = st.form_submit_button(f"💾 Güncellemeyi Kaydet ({talep['talep_id']})")
                        
                        if kaydet_buton:
                            s_foto_adi = talep.get('saha_fotograf_adi', 'Yüklenmedi')
                            s_foto_b64 = talep.get('saha_fotograf_b64', '')

                            if saha_fotograf_yukleme is not None:
                                s_foto_adi = saha_fotograf_yukleme.name
                                s_bytes = saha_fotograf_yukleme.getvalue()
                                s_foto_b64 = base64.b64encode(s_bytes).decode("utf-8")

                            try:
                                guncelleme_verisi = {
                                    'durum': yeni_durum,
                                    'atanan_personel': atanacak_kisi,
                                    'yönetici_notu': yonetici_notu_input,
                                    'saha_fotograf_adi': s_foto_adi,
                                    'saha_fotograf_b64': s_foto_b64
                                }
                                supabase.table("talepler").update(guncelleme_verisi).eq("talep_id", talep["talep_id"]).execute()
                                st.success(f"✅ {talep['talep_id']} numaralı talep güncellendi!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Güncelleme hatası: {e}")
