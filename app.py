import streamlit as st
from supabase import create_client, Client

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

# Supabase Bağlantısı
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    baglanti_basarili = True
except Exception as e:
    baglanti_basarili = False

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı, yol ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

# Sekmeler (Vatandaş Formu ve Personel Paneli)
tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    # Veritabanından kategorileri çekme denemesi
    ana_kategoriler = []
    alt_kategori_data = None
    
    try:
        kategori_data = supabase.table("kategori_kurum_eslestirme").select("ana_kategori, alt_kategori, sorumlu_kurum, alt_bolum").execute()
        if kategori_data.data:
            tum_veriler = kategori_data.data
            ana_kategoriler = list(set([item["ana_kategori"] for item in tum_veriler]))
    except Exception as e:
        tum_veriler = []

    # Eğer veritabanından çekilemezse sistem çökmesin diye yedek liste
    if not ana_kategoriler:
        tum_veriler = [
            {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Yol Bozukluğu / Çukur", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
            {"ana_kategori": "Yol ve Ulaşım", "alt_kategori": "Kaldırım ve Bordür Hasarı", "sorumlu_kurum": "Belediye", "alt_bolum": "Fen İşleri Müdürlüğü"},
            {"ana_kategori": "Park ve Yeşil Alan", "alt_kategori": "Park Aydınlatma Arızası", "sorumlu_kurum": "Belediye", "alt_bolum": "Park ve Bahçeler Müdürlüğü"},
            {"ana_kategori": "Çevre ve Temizlik", "alt_kategori": "Çöp Konteyneri Kırık", "sorumlu_kurum": "Belediye", "alt_bolum": "Temizlik İşleri Müdürlüğü"}
        ]
        ana_kategoriler = list(set([item["ana_kategori"] for item in tum_veriler]))

    with st.form("talep_formu"):
        tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)")
        ad_soyad = st.text_input("Ad Soyad *")
        telefon = st.text_input("Telefon Numarası *")
        
        secilen_ana_kategori = st.selectbox("Ana Kategori", options=sorted(ana_kategoriler))
        
        # Seçilen ana kategoriye ait alt kategorileri filtreleme
        filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
        alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
        
        secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategori_isimleri)
        
        # --- YENİ EKLENEN ALANLAR: Konum ve Fotoğraf ---
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
                
                import random
                talep_id = f"KENT-{random.randint(10000, 99999)}"
                
                # Fotoğraf adı simülasyonu (İleride Supabase Storage'a bağlanabilir)
                foto_adi = fotograf.name if fotograf else "Fotoğraf Yok"
                
                kayit = {
                    "talep_id": talep_id,
                    "tc_kimlik_no": tc_kimlik,
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
                
                try:
                    response = supabase.table("talepler").insert(kayit).execute()
                    st.success(f"Talebiniz başarıyla alındı! Takip Numaranız: **{talep_id}**")
                    st.balloons()
                except Exception as db_err:
                    st.error(f"Kayıt eklenirken bir hata oluştu: {db_err}")

with tab2:
    st.header("Belediye Personel Girişi")
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        try:
            personel_kontrol = supabase.table("kullanicilar_kurum").select("*").eq("eposta_adresi", eposta).execute()
            if personel_kontrol.data:
                st.success(f"Hoş geldiniz, {personel_kontrol.data[0]['ad_soyad']} ({personel_kontrol.data[0]['unvan']})")
                st.subheader("Gelen Talepler Listesi")
                talepler = supabase.table("talepler").select("*").execute()
                st.dataframe(talepler.data)
            else:
                st.error("Bu e-posta adresiyle kayıtlı yetkili personel bulunamadı!")
        except Exception as e:
            st.error(f"Personel sorgulanırken hata oluştu: {e}")
