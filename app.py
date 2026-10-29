import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim ve Çözüm Portalı", layout="centered")

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı, yol ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

# Bağlantı ve Debug Testi
baglanti_basarili = False
supabase = None

try:
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    
    # Ekranda ne okuduğunu görelim (Güvenlik için key'i gizliyoruz)
    st.success(f"✅ Okunan Supabase URL: `{url}`")
    
    supabase = create_client(url, key)
    baglanti_basarili = True
except Exception as e:
    st.error(f"⚠️ Secrets / Bağlantı Hatası: {e}")

# Sekmeler
tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    ana_kategoriler = []
    tum_veriler = []
    
    if baglanti_basarili and supabase:
        try:
            kategori_data = supabase.table("kategori_kurum_eslestirme").select("ana_kategori, alt_kategori, sorumlu_kurum, alt_bolum").execute()
            if kategori_data.data:
                tum_veriler = kategori_data.data
                ana_kategoriler = list(set([item["ana_kategori"] for item in tum_veriler]))
        except Exception as db_err:
            st.warning(f"Kategoriler tablodan çekilemedi: {db_err}")

    # Yedek Liste (Bağlantı kurulana kadar formun çalışmasını sağlar)
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
        
        filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
        alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
        
        secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategori_isimleri if alt_kategori_isimleri else ["Alt Kategori Bulunamadı"])
        
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
                
                if baglanti_basarili and supabase:
                    try:
                        response = supabase.table("talepler").insert(kayit).execute()
                        st.success(f"Talebiniz başarıyla alındı! Takip Numaranız: **{talep_id}**")
                        st.balloons()
                    except Exception as db_err:
                        st.error(f"Kayıt eklenirken veritabanı hatası oluştu: {db_err}")
                else:
                    st.error("Veritabanı bağlantısı kurulamadığı için kayıt yapılamadı. Lütfen üstteki Secrets ayarlarını kontrol edin.")

with tab2:
    st.header("Belediye Personel Girişi")
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        if baglanti_basarili and supabase:
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
        else:
            st.error("Veritabanı bağlantısı yok.")
