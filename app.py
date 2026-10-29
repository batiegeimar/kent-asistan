import streamlit as st
from supabase import create_client, Client

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim Sistemi", layout="centered")

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
    baglanti_hatasi = str(e)

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

# Bağlantı Kontrolü Uyarı Kutusu
if not baglanti_basarili:
    st.error(f"⚠️ Veritabanı bağlantı hatası oluştu! Lütfen Streamlit 'Secrets' ayarlarındaki URL ve KEY değerlerinizi kontrol edin.\n\nHata Detayı: {baglanti_hatasi}")
else:
    # Sekmeler (Vatandaş Formu ve Personel Paneli)
    tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

    with tab1:
        st.header("Yeni Talep Oluştur")
        
        try:
            # Kategorileri veritabanından çekme
            kategori_data = supabase.table("kategori_kurum_eslestirme").select("ana_kategori").execute()
            ana_kategoriler = list(set([item["ana_kategori"] for item in kategori_data.data]))
        except Exception as e:
            ana_kategoriler = []
            st.warning("Kategoriler yüklenirken veritabanına ulaşılamadı. Lütfen Supabase ayarlarınızı gözden geçirin.")

        with st.form("talep_formu"):
            tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)")
            ad_soyad = st.text_input("Ad Soyad *")
            telefon = st.text_input("Telefon Numarası *")
            
            secilen_ana_kategori = st.selectbox("Ana Kategori", options=ana_kategoriler if ana_kategoriler else ["Kategori Bulunamadı"])
            
            alt_kategoriler = []
            alt_kategori_data = None
            if ana_kategoriler:
                try:
                    alt_kategori_data = supabase.table("kategori_kurum_eslestirme").select("alt_kategori, sorumlu_kurum, alt_bolum").eq("ana_kategori", secilen_ana_kategori).execute()
                    alt_kategoriler = [item["alt_kategori"] for item in alt_kategori_data.data]
                except:
                    pass
            
            secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategoriler if alt_kategoriler else ["Alt Kategori Bulunamadı"])
            
            aciklama = st.text_area("Talep / Şikayet Açıklaması *")
            
            gonder_btn = st.form_submit_button("Talebi Gönder")
            
            if gonder_btn:
                if not ad_soyad or not telefon or not aciklama:
                    st.error("Lütfen zorunlu alanları (*) doldurunuz.")
                else:
                    eslesme = next((item for item in alt_kategori_data.data if item["alt_kategori"] == secilen_alt_kategori), None) if alt_kategori_data else None
                    sorumlu_kurum = eslesme["sorumlu_kurum"] if eslesme else "Belediye"
                    alt_bolum = eslesme["alt_bolum"] if eslesme else "Fen İşleri Müdürlüğü"
                    
                    import random
                    talep_id = f"KENT-{random.randint(10000, 99999)}"
                    
                    kayit = {
                        "talep_id": talep_id,
                        "tc_kimlik_no": tc_kimlik,
                        "ad_soyad": ad_soyad,
                        "telefon_no": telefon,
                        "ana_kategori": secilen_ana_kategori,
                        "alt_kategori": secilen_alt_kategori,
                        "alt_bolum": alt_bolum,
                        "aciklama": aciklama,
                        "sorumlu_kurum": sorumlu_kurum,
                        "durum": "Yeni"
                    }
                    
                    try:
                        response = supabase.table("talepler").insert(kayit).execute()
                        st.success(f"Talebiniz başarıyla alındı! Takip Numaranız: **{talep_id}**")
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
