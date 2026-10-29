import streamlit as st
from supabase import create_client, Client

# Sayfa Yapılandırması (Düzeltildi)
st.set_page_config(page_title="KentAsistan - Vatandaş Bildirim Sistemi", layout="centered")

# Supabase Bağlantısı (Streamlit Secrets üzerinden güvenli bağlantı)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.title("🏙️ KentAsistan - Vatandaş Bildirim ve Çözüm Portalı")
st.write("Belediyemiz sınırları içerisindeki altyapı ve çevre taleplerinizi buradan kolayca iletebilirsiniz.")

# Sekmeler (Vatandaş Formu ve Personel Paneli)
tab1, tab2 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔒 Personel / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    
    with st.form("talep_formu"):
        tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)")
        ad_soyad = st.text_input("Ad Soyad *")
        telefon = st.text_input("Telefon Numarası *")
        
        # Kategorileri veritabanından çekme
        kategori_data = supabase.table("kategori_kurum_eslestirme").select("ana_kategori").execute()
        ana_kategoriler = list(set([item["ana_kategori"] for item in kategori_data.data]))
        
        secilen_ana_kategori = st.selectbox("Ana Kategori", options=ana_kategoriler)
        
        # Seçilen ana kategoriye ait alt kategorileri çekme
        alt_kategori_data = supabase.table("kategori_kurum_eslestirme").select("alt_kategori, sorumlu_kurum, alt_bolum").eq("ana_kategori", secilen_ana_kategori).execute()
        alt_kategoriler = [item["alt_kategori"] for item in alt_kategori_data.data]
        
        secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategoriler)
        
        aciklama = st.text_area("Talep / Şikayet Açıklaması *")
        
        gonder_btn = st.form_submit_button("Talebi Gönder")
        
        if gonder_btn:
            if not ad_soyad or not telefon or not aciklama:
                st.error("Lütfen zorunlu alanları (*) doldurunuz.")
            else:
                # İlgili kurum ve alt bölümü eşleşme tablosundan bulma
                eslesme = next((item for item in alt_kategori_data.data if item["alt_kategori"] == secilen_alt_kategori), None)
                sorumlu_kurum = eslesme["sorumlu_kurum"] if eslesme else "Belediye"
                alt_bolum = eslesme["alt_bolum"] if eslesme else "Fen İşleri Müdürlüğü"
                
                import random
                talep_id = f"KENT-{random.randint(10000, 99999)}"
                
                # Veriyi PostgreSQL (Supabase) talepler tablosuna kaydetme
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
                
                response = supabase.table("talepler").insert(kayit).execute()
                st.success(f"Talebiniz başarıyla alındı! Takip Numaranız: **{talep_id}**")

with tab2:
    st.header("Belediye Personel Girişi")
    eposta = st.text_input("Personel E-Posta Adresi")
    
    if st.button("Giriş Yap"):
        personel_kontrol = supabase.table("kullanicilar_kurum").select("*").eq("eposta_adresi", eposta).execute()
        if personel_kontrol.data:
            st.success(f"Hoş geldiniz, {personel_kontrol.data[0]['ad_soyad']} ({personel_kontrol.data[0]['unvan']})")
            st.subheader("Gelen Talepler Listesi")
            talepler = supabase.table("talepler").select("*").execute()
            st.dataframe(talepler.data)
        else:
            st.error("Bu e-posta adresiyle kayıtlı yetkili personel bulunamadı!")
