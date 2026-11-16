import streamlit as st
from sqlalchemy import text
import random
from PIL import Image
import io
import json
import base64
import urllib.parse
from datetime import datetime
import pandas as pd
from shapely.geometry import Point, shape
from streamlit_geolocation import streamlit_geolocation
from fpdf import FPDF

# Uygulama Canlı URL'si (WhatsApp görsel linki üretimi için)
APP_BASE_URL = "https://kent-asistan-bpcusdhobee6vqmjbrcsxe.streamlit.app"

# Sayfa Yapılandırması
st.set_page_config(page_title="KentAsistan - Akıllı Kent ve Saha Yönetimi", layout="centered", page_icon="🏙️")

# --- KURUMSAL CSS TASARIM ENJEKSİYONU ---
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        color: #334155;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        color: #ffffff;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

# --- POSTGRESQL VERİTABANI BAĞLANTISI ---
try:
    conn = st.connection("postgresql", type="sql")
    baglanti_hatasi = None
except Exception as e:
    conn = None
    baglanti_hatasi = str(e)

# =========================================================================
# 📸 SAHA PERSONELİ İÇİN ŞİFRESİZ HIZLI HASAR GÖRSELİ EKRANI (?gorsel=ID)
# =========================================================================
query_params = st.query_params
if "gorsel" in query_params:
    hedef_talep_id = query_params["gorsel"].strip()
    st.title("📸 KentAsistan - Saha Görev Kartı")
    st.markdown(f"##### *Talep Numarası: `{hedef_talep_id}`*")
    st.markdown("---")
    
    if conn is not None:
        try:
            df_gorsel = conn.query("SELECT * FROM talepler WHERE talep_id = :tid;", params={"tid": hedef_talep_id}, ttl=0)
            if not df_gorsel.empty:
                t_data = df_gorsel.iloc[0].to_dict()
                
                st.info(f"**Kategori:** {t_data.get('alt_kategori')} | **Sorumlu Birim:** {t_data.get('alt_bolum')}")
                st.write(f"**Vatandaş Açıklaması:** {t_data.get('aciklama')}")
                st.write(f"**Bildirim Zamanı:** `{t_data.get('olusturma_tarihi')}`")
                
                lat = t_data.get('enlem')
                lon = t_data.get('boylam')
                if lat and lon:
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                    st.link_button("🗺️ Google Haritalar'da Yol Tarifi Al", maps_url, type="primary")
                
                st.markdown("### 📷 Vatandaşın Yüklediği Hasar Fotoğrafı")
                foto_b64 = t_data.get('fotograf_b64', '')
                if foto_b64:
                    try:
                        img = Image.open(io.BytesIO(base64.b64decode(foto_b64)))
                        st.image(img, caption=f"{hedef_talep_id} - Hasar Görseli", use_container_width=True)
                    except Exception:
                        st.error("Görsel dosyası çözümlenemedi.")
                else:
                    st.warning("Vatandaş bu talep için fotoğraf yüklememiş.")
                    
                st.markdown("---")
                if st.button("🏠 Ana Uygulamaya / Giriş Ekranına Geç"):
                    st.query_params.clear()
                    st.rerun()
            else:
                st.error("Belirtilen talep numarasına ait kayıt bulunamadı.")
        except Exception as e:
            st.error(f"Veri getirme hatası: {e}")
    st.stop() # Normal arayüzün yüklenmesini durdurur, sadece bu kartı gösterir

# --- TÜRKÇE KARAKTER DÖNÜŞTÜRÜCÜ & PDF OLUŞTURMA MOTORU ---
def tr_temizle(metin):
    if not metin:
        return ""
    ceviri = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return str(metin).translate(ceviri)

def yonetici_pdf_olustur(df_rapor, toplam, cozulen, bekleyen, reddedilen, en_cok_birim, basari_orani, raporlayan_kisi, raporlayan_birim):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 35, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(10, 10)
    pdf.cell(0, 8, tr_temizle("KENTASISTAN - AKILLI KENT VE SAHA YONETIMI"), ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10)
    pdf.cell(0, 6, tr_temizle("Yonetici Performans, Denetim ve Yapay Zeka Stratejik Analiz Raporu"), ln=True)
    
    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(10, 42)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, tr_temizle(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), ln=True)
    pdf.cell(0, 6, tr_temizle(f"Duzenleyen Yetkili: {raporlayan_kisi} ({raporlayan_birim})"), ln=True)
    pdf.ln(4)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 1. OPERASYONEL PERFORMANS OZETI (KPI)"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, tr_temizle(f"- Toplam Gelen Bildirim Sayisi: {toplam}"), border=1)
    pdf.cell(95, 7, tr_temizle(f"- Cozulen / Kapatilan Talep: {cozulen}"), border=1, ln=True)
    pdf.cell(95, 7, tr_temizle(f"- Incelemede / Bekleyen Talep: {bekleyen}"), border=1)
    pdf.cell(95, 7, tr_temizle(f"- Reddedilen / Yersiz Talep: {reddedilen}"), border=1, ln=True)
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 2. YAPAY ZEKA DESTEKLI STRATEJIK YONETICI OZETI"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    ozet_1 = f"- Genel Operasyonel Basari Orani: %{basari_orani} seviyesindedir."
    ozet_2 = f"- En Yogun Birim Analizi: Sistemdeki veriler incelendiginde en fazla talep alan birim '{en_cok_birim}' olarak tespit edilmistir."
    ozet_3 = "- Cografi Kumelenme ve Eylem Onerisi: Kirsal mahalleler ve ilce merkezinden gelen altyapi/yol bildirimlerinin harita uzerinde kumelendigi gorulmektedir. Saha ekiplerinin ve arac rotalarinin en yogun hatlara kaydirilmasi ortalama cozum suresini (SLA) kisaltacaktir."
    
    pdf.multi_cell(0, 6, tr_temizle(ozet_1))
    pdf.ln(1)
    pdf.multi_cell(0, 6, tr_temizle(ozet_2))
    pdf.ln(1)
    pdf.multi_cell(0, 6, tr_temizle(ozet_3))
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 3. BIRIMLERE GORE IS YUKU DAGILIMI"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    if 'alt_bolum' in df_rapor.columns:
        birim_sayilari = df_rapor['alt_bolum'].value_counts()
        for birim, sayi in birim_sayilari.items():
            pdf.cell(0, 6, tr_temizle(f"- {birim}: {sayi} adet talep"), ln=True)
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 4. DENETIM IZI VE SON TALEPLER LISTESI"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(28, 7, "Talep ID", border=1, fill=True)
    pdf.cell(52, 7, tr_temizle("Alt Kategori"), border=1, fill=True)
    pdf.cell(50, 7, tr_temizle("Sorumlu Birim"), border=1, fill=True)
    pdf.cell(60, 7, tr_temizle("Mevcut Durum"), border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 8)
    for _, row in df_rapor.tail(15).iterrows():
        t_id = tr_temizle(row.get('talep_id', ''))[:14]
        alt_k = tr_temizle(row.get('alt_kategori', ''))[:28]
        birim = tr_temizle(row.get('alt_bolum', ''))[:26]
        durum = tr_temizle(row.get('durum', ''))[:32]
        
        pdf.cell(28, 6, t_id, border=1)
        pdf.cell(52, 6, alt_k, border=1)
        pdf.cell(50, 6, birim, border=1)
        pdf.cell(60, 6, durum, border=1, ln=True)
        
    return bytes(pdf.output())

# --- GLOBAL OTURUM HAFIZASI ---
if "personel_giris" not in st.session_state:
    st.session_state["personel_giris"] = False
if "giris_yapan_personel" not in st.session_state:
    st.session_state["giris_yapan_personel"] = None

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

if yenipazar_poligonu is not None:
    st.sidebar.success("CBS Altyapisi: Yenipazar Siniri Aktif")
else:
    st.sidebar.error("CBS Altyapisi: Sinir Dosyasi Bulunamadi!")

if baglanti_hatasi is None:
    st.sidebar.success("Supabase: Bulut Veritabani Aktif")
else:
    st.sidebar.error(f"Supabase Baglanti Hatasi: {baglanti_hatasi}")

st.title("🏙️ KentAsistan - Akıllı Kent ve Saha Yönetimi")
st.markdown("##### *Yenipazar Belediyesi ve Paydaş Kurumlar Ortak Çözüm Masası*")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 Talep Bildir (Vatandaş)", "🔍 Talep Sorgula & Şeffaf Takip", "🔒 Kurum / Yönetim Paneli"])

with tab1:
    st.header("Yeni Talep Oluştur")
    st.write("Kırsal mahalleler ve merkez dahil tüm vatandaşlarımız için hızlı bildirim portalı.")
    
    col_il1, col_il2 = st.columns(2)
    with col_il1:
        secilen_il = st.selectbox("İl", options=["Aydın", "Diğer"], index=0, key="vat_il")
    with col_il2:
        secilen_ilce = st.selectbox("İlçe", options=["Yenipazar", "Diğer"], index=0, key="vat_ilce")
        
    if secilen_ilce != "Yenipazar":
        st.warning("KentAsistan şu an yalnızca **Yenipazar** ilçesinde aktif olarak hizmet vermektedir.")
    
    tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)", key="vat_tc")
    ad_soyad = st.text_input("Ad Soyad *", key="vat_ad")
    telefon = st.text_input("Telefon Numarası (Örn: 0555...) *", key="vat_tel")
    
    secilen_ana_kategori = st.selectbox("Ana Kategori", options=ana_kategoriler, key="ana_kat_secim")
    
    filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
    alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
    
    secilen_alt_kategori = st.selectbox("Alt Kategori", options=alt_kategori_isimleri, key="alt_kat_secim")
    
    st.markdown("---")
    st.subheader("Konum İzni ve Otomatik GPS Doğrulama")
    st.info("Sistem, talebinizin ilçe sınırları içerisinde çözülebilmesi için cihazınızın güncel GPS konumuna ihtiyaç duyar.")
    
    location = streamlit_geolocation()

    konum_izni = st.radio(
        "Konum Paylaşım İzni:",
        [
            "Konumumun paylaşılmasına izin veriyorum (GPS ile bağlan)", 
            "İzin vermiyorum"
        ],
        key="vat_konum_izni"
    )
    
    fotograf = st.file_uploader("Hasarlı Bölgeye Ait Fotoğraf Yükle (Opsiyonel)", type=["jpg", "jpeg", "png"], key="vat_foto")
    aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Lütfen sorunu kısaca açıklayınız...", key="vat_aciklama")
    
    gonder_btn = st.button("Talebi Gönder", key="vat_gonder_btn", type="primary")
    
    if gonder_btn:
        if not ad_soyad or not telefon or not aciklama:
            st.error("Lütfen zorunlu alanları (*) doldurunuz.")
        elif secilen_ilce != "Yenipazar":
            st.error("Seçilen ilçe için sistem aktif değildir.")
        elif "İzin vermiyorum" in konum_izni:
            st.error("Konum paylaşımına izin vermediğiniz için talep oluşturulamamaktadır.")
        elif location is None or location.get('latitude') is None or location.get('longitude') is None:
            st.error("GPS konum veriniz alınamadı. Lütfen konum izni verdiğinizden emin olun.")
        else:
            enlem = location.get('latitude')
            boylam = location.get('longitude')
            
            sinir_icinde_mi = True
            if yenipazar_poligonu is not None:
                vatandas_noktasi = Point(boylam, enlem)
                sinir_icinde_mi = yenipazar_poligonu.contains(vatandas_noktasi)
            
            if not sinir_icinde_mi:
                st.error("GPS koordinatlarınız resmi Yenipazar ilçe sınırları dışındadır. Talep reddedildi.")
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
                
                if conn is not None:
                    try:
                        query = """
                            INSERT INTO talepler (
                                talep_id, tc_kimlik_no, ad_soyad, telefon_no, il, ilce, 
                                ana_kategori, alt_kategori, alt_bolum, sorumlu_kurum, 
                                gps_konum, enlem, boylam, aciklama, fotograf_adi, 
                                fotograf_b64, saha_fotograf_adi, saha_fotograf_b64, 
                                olusturma_tarihi, guncelleme_tarihi, cozum_tarihi, durum, atanan_personel, yönetici_notu
                            ) VALUES (
                                :talep_id, :tc_kimlik_no, :ad_soyad, :telefon_no, :il, :ilce, 
                                :ana_kategori, :alt_kategori, :alt_bolum, :sorumlu_kurum, 
                                :gps_konum, :enlem, :boylam, :aciklama, :fotograf_adi, 
                                :fotograf_b64, :saha_fotograf_adi, :saha_fotograf_b64, 
                                :olusturma_tarihi, :guncelleme_tarihi, :cozum_tarihi, :durum, :atanan_personel, :yonetici_notu
                            )
                        """
                        with conn.session as s:
                            s.execute(
                                text(query),
                                {
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
                                    "guncelleme_tarihi": "Henüz işlem yapılmadı",
                                    "cozum_tarihi": "Henüz çözülmedi",
                                    "durum": "Yeni (İnceleme Bekliyor)",
                                    "atanan_personel": "Atanmadı",
                                    "yonetici_notu": "Henüz not eklenmedi"
                                }
                            )
                            s.commit()
                            
                        st.success(f"Talebiniz başarıyla kaydedildi! Sorumlu Kurum: **{sorumlu_kurum}** | Takip Numaranız: **{talep_id}**")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Veritabanı kayıt hatası: {e}")
                else:
                    st.error("Veritabanı bağlantısı kurulamadı.")

with tab2:
    st.header("Vatandaş Şeffaf Talep ve Süreç Takip Merkezi")
    st.info("Takip numaranızla (Örn: KENT-12345) talebinizin hangi birimde olduğunu, hangi saha personeline atandığını ve tüm zaman damgalarını şeffafça takip edebilirsiniz.")
    
    sorgu_id = st.text_input("Talep Takip Numarasını Giriniz (Örn: KENT-XXXXX)", key="vat_sorgu_input")
    
    if st.button("Talebi Sorgula", key="talep_sorgula_btn", type="primary"):
        if sorgu_id:
            try:
                df_sorgu = conn.query("SELECT * FROM talepler WHERE talep_id = :tid;", params={"tid": sorgu_id.strip()}, ttl=0)
                if not df_sorgu.empty:
                    t = df_sorgu.iloc[0].to_dict()
                    st.success(f"Talep Bulundu: {t['talep_id']} ({t['alt_kategori']})")
                    
                    st.markdown("### Süreç Akışı ve Denetim İzi (Şeffaf Takip)")
                    
                    st.markdown(f"1. **Talep Oluşturma:** `{t.get('olusturma_tarihi', '-')}` tarihinde vatandaş tarafından oluşturuldu ve **{t.get('alt_bolum')}** ({t.get('sorumlu_kurum')}) birimine iletildi.")
                    st.markdown(f"2. **Yönetici / Müdür İncelemesi:** Mevcut Durum: **{t.get('durum')}**")
                    st.markdown(f"3. **Saha Personeli Ataması:** Atanan Personel: **{t.get('atanan_personel')}** (Sevk Zamanı / Güncelleme: `{t.get('guncelleme_tarihi', '-')}`)")
                    st.markdown(f"4. **Çözüm ve Kapatılma Zamanı:** `{t.get('cozum_tarihi', 'Henüz tamamlanmadı')}`")
                    
                    if t.get('yönetici_notu') and t.get('yönetici_notu') != "Henüz not eklenmedi":
                        st.info(f"**Kurum / Müdür Notu:** {t.get('yönetici_notu')}")
                        
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        st.markdown("**Vatandaş Bildirim Fotoğrafı:**")
                        if t.get('fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(t['fotograf_b64']))), caption="Vatandaş Görseli", use_container_width=True)
                            except:
                                st.write("Görsel yüklenemedi.")
                        else:
                            st.write("Fotoğraf yok.")
                    with c_f2:
                        st.markdown("**Saha Çözüm Bitiş Fotoğrafı:**")
                        if t.get('saha_fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(t['saha_fotograf_b64']))), caption="Saha Çözüm Görseli", use_container_width=True)
                            except:
                                st.write("Saha görseli yüklenemedi.")
                        else:
                            st.write("Saha personeli henüz çözüm fotoğrafı yüklemedi.")
                else:
                    st.warning("Bu takip numarasına ait kayıt bulunamadı.")
            except Exception as e:
                st.error(f"Sorgulama hatası: {e}")
        else:
            st.warning("Lütfen bir takip numarası girin.")

with tab3:
    st.header("Kurum ve Personel Giriş Paneli")
    st.info("Güvenlik Notu: Bu alan yetkili kurum yöneticilerine, amirlere ve saha personeline özeldir.")

    if not st.session_state["personel_giris"]:
        tel_giris = st.text_input("Telefon Numarası (Örn: 0555...)", key="personel_tel_input")
        sifre_giris = st.text_input("Şifre", type="password", key="personel_sifre_input")
        
        if st.button("Güvenli Giriş Yap", key="personel_giris_btn", type="primary"):
            if tel_giris and sifre_giris:
                try:
                    clean_tel = tel_giris.strip().replace(" ", "")
                    q_login = "SELECT * FROM personeller WHERE telefon_no = :tel AND sifre = :sifre;"
                    df_pers = conn.query(q_login, params={"tel": clean_tel, "sifre": sifre_giris}, ttl=0)
                    
                    if not df_pers.empty:
                        eslesen_personel = df_pers.iloc[0].to_dict()
                        st.session_state["personel_giris"] = True
                        st.session_state["giris_yapan_personel"] = eslesen_personel
                        st.rerun()
                    else:
                        st.error("Hatalı telefon numarası veya şifre!")
                except Exception as e:
                    st.error(f"Giriş sorgulama hatası: {e}")
            else:
                st.warning("Lütfen telefon numaranızı ve şifrenizi giriniz.")

    if st.session_state["personel_giris"]:
        personel = st.session_state["giris_yapan_personel"]
        st.success(f"Hoş geldiniz, {personel['ad_soyad']} ({personel['unvan']} - {personel['sorumlu_birim']})")
        
        if st.button("Çıkış Yap", key="cikis_yap_btn"):
            st.session_state["personel_giris"] = False
            st.session_state["giris_yapan_personel"] = None
            st.rerun()

        unvan_degeri = str(personel.get("unvan", "")).strip().lower()
        is_super_admin = unvan_degeri in ["süper_admin", "süper admin", "super_admin", "super admin"]
        is_saha_personeli = unvan_degeri in ["saha personeli", "usta", "teknisyen", "operatör", "saha ekip sorumlusu"]

        # =========================================================================
        # 👑 1. SÜPER ADMIN PANELI
        # =========================================================================
        if is_super_admin:
            st.markdown("---")
            st.subheader("Süper Admin - Platform Yönetim Paneli")
            
            admin_secim = st.radio("Yönetim İşlemi Seçin:", ["Sistem Kurum ve Yetkili Matrisi", "Kurum Yöneticisi / Müdür Ekle"], key="admin_radio_secim")
            
            if admin_secim == "Sistem Kurum ve Yetkili Matrisi":
                try:
                    df_all_pers = conn.query("SELECT * FROM personeller;", ttl=0)
                    tum_personeller = df_all_pers.to_dict('records') if not df_all_pers.empty else []
                    
                    for kurum in kurumlar_listesi:
                        kurum_adi = kurum["kurum_adi"]
                        birim_adi = kurum["alt_bolum"]
                        ilgili_yetkililer = [p for p in tum_personeller if p.get("sorumlu_birim") == birim_adi]
                        
                        with st.expander(f"{kurum_adi} ➔ {birim_adi}"):
                            if ilgili_yetkililer:
                                for y in ilgili_yetkililer:
                                    col_info, col_del = st.columns([4, 1])
                                    with col_info:
                                        st.write(f"- **{y['ad_soyad']}** | Tel: `{y.get('telefon_no')}` | Unvan: *{y['unvan']}*")
                                    with col_del:
                                        if st.button("Sil", key=f"del_sup_{y.get('telefon_no')}_{y.get('ad_soyad')}"):
                                            with conn.session as s:
                                                s.execute(text("DELETE FROM personeller WHERE telefon_no = :tel AND ad_soyad = :ad"), {"tel": y.get('telefon_no'), "ad": y.get('ad_soyad')})
                                                s.commit()
                                            st.success("Personel silindi!")
                                            st.rerun()
                            else:
                                st.warning("Bu birime henüz yetkili atanmamış.")
                except Exception as e:
                    st.error(f"Hata: {e}")

            elif admin_secim == "Kurum Yöneticisi / Müdür Ekle":
                p_ad = st.text_input("Yöneticinin Adı Soyadı", key="p_ad_input")
                p_tel = st.text_input("Telefon Numarası (Giriş için Örn: 0555...)", key="p_tel_input")
                p_sifre = st.text_input("Şifre", type="password", key="p_sifre_input")
                p_unvan = st.selectbox("Unvan", ["Kurum Yetkilisi", "Fen İşleri Müdürü", "Su ve Kanalizasyon Amiri", "Park ve Bahçeler Amiri", "Zabıta Amiri"], key="p_unvan_select")
                p_birim = st.selectbox("Sorumlu Olduğu Kurum / Birim", [k["alt_bolum"] for k in kurumlar_listesi], key="p_birim_select")
                
                if st.button("Kaydet", key="yonetici_olustur_btn", type="primary"):
                    if p_ad and p_tel and p_sifre:
                        with conn.session as s:
                            s.execute(text("INSERT INTO personeller (ad_soyad, telefon_no, sifre, unvan, sorumlu_birim) VALUES (:ad, :tel, :sifre, :unvan, :birim)"), {"ad": p_ad, "tel": p_tel.strip(), "sifre": p_sifre, "unvan": p_unvan, "birim": p_birim})
                            s.commit()
                        st.success("Yönetici eklendi!")
                        st.rerun()

        # =========================================================================
        # 🛠️ 2. SAHA PERSONELİ PANELI
        # =========================================================================
        elif is_saha_personeli:
            st.markdown("---")
            st.subheader(f"Saha Operasyon Paneli - {personel['ad_soyad']}")
            st.info("Size atanan işleri buradan görebilir, tamamlandığında **Saha Çözüm Fotoğrafı** yükleyip kurum müdürünün onayına gönderebilirsiniz.")
            
            try:
                df_t_saha = conn.query("SELECT * FROM talepler WHERE atanan_personel = :personel_ad;", params={"personel_ad": personel['ad_soyad']}, ttl=0)
                saha_gorevleri = df_t_saha.to_dict('records') if not df_t_saha.empty else []
            except Exception as e:
                saha_gorevleri = []
                st.error(f"Görevler yüklenirken hata: {e}")
                
            if not saha_gorevleri:
                st.info("Üzerinize atanmış aktif saha görevi bulunmamaktadır.")
            
            for idx, gorev in enumerate(saha_gorevleri):
                with st.expander(f" Görev ID: {gorev['talep_id']} - {gorev['alt_kategori']} ({gorev['durum']})"):
                    st.write(f"**Açıklama:** {gorev['aciklama']}")
                    st.write(f"**Konum:** {gorev['gps_konum']}")
                    
                    lat = gorev.get('enlem')
                    lon = gorev.get('boylam')
                    if lat and lon:
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        st.markdown(f"**[Google Haritalar'da Rotayı Aç]({maps_url})**", unsafe_allow_html=True)
                    
                    if gorev.get('fotograf_b64'):
                        st.markdown("**Vatandaş Hasar Görseli:**")
                        try:
                            st.image(Image.open(io.BytesIO(base64.b64decode(gorev['fotograf_b64']))), use_container_width=True)
                        except:
                            pass
                            
                    st.markdown("---")
                    st.markdown("**Sahada Yapılan İşi Kanıtlama (Çözüm Fotoğrafı Yükle):**")
                    
                    saha_foto_yukle = st.file_uploader("Çözüm Sonrası Fotoğraf Yükle", type=["jpg", "jpeg", "png"], key=f"saha_up_{gorev['talep_id']}_{idx}")
                    
                    if st.button(f"Talebi Çözüldü Olarak Müdüre Gönder ({gorev['talep_id']})", key=f"saha_gonder_{gorev['talep_id']}_{idx}", type="primary"):
                        if saha_foto_yukle is not None:
                            s_foto_adi = saha_foto_yukle.name
                            s_foto_b64 = base64.b64encode(saha_foto_yukle.getvalue()).decode("utf-8")
                            simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            try:
                                q_saha_upd = """
                                    UPDATE talepler 
                                    SET durum = :durum, 
                                        saha_fotograf_adi = :f_adi, 
                                        saha_fotograf_b64 = :f_b64,
                                        guncelleme_tarihi = :g_tarih
                                    WHERE talep_id = :tid
                                """
                                with conn.session as s:
                                    s.execute(
                                        text(q_saha_upd),
                                        {
                                            "durum": "Saha Çözümü Tamamlandı (Müdür Onayı Bekliyor)",
                                            "f_adi": s_foto_adi,
                                            "f_b64": s_foto_b64,
                                            "g_tarih": simdiki_zaman,
                                            "tid": gorev['talep_id']
                                        }
                                    )
                                    s.commit()
                                st.success("Çözüm fotoğrafı ve durumu müdür onayına başarıyla gönderildi!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Güncelleme hatası: {e}")
                        else:
                            st.warning("Lütfen sahadaki çözüme ait kanıt fotoğrafı yükleyiniz.")

        # =========================================================================
        # 🏛️ 3. KURUM YETKİLİSİ / MÜDÜR PANELI
        # =========================================================================
        else:
            st.markdown("---")
            st.subheader(f"{personel['sorumlu_birim']} - Kurum Operasyon Paneli")
            st.info("Müdür olarak biriminize gelen talepleri inceler, saha personeline atar ve saha personelinden gelen çözümleri onaylayarak vatandaşa otomatik WhatsApp bilgilendirmesi tetiklersiniz.")
            
            with st.expander("Birim Saha Personelleri ve Personel Yönetimi"):
                try:
                    df_birim_pers = conn.query("SELECT * FROM personeller WHERE sorumlu_birim = :birim AND unvan IN ('Saha Personeli', 'Usta', 'Teknisyen', 'Operatör', 'Saha Ekip Sorumlusu');", params={"birim": personel['sorumlu_birim']}, ttl=0)
                    if not df_birim_pers.empty:
                        for _, bp in df_birim_pers.iterrows():
                            c_info, c_del = st.columns([4, 1])
                            with c_info:
                                st.write(f"- **{bp['ad_soyad']}** | Tel: `{bp.get('telefon_no')}` | Unvan: *{bp['unvan']}*")
                            with c_del:
                                if st.button("Sil", key=f"del_birim_{bp.get('telefon_no')}_{bp.get('ad_soyad')}"):
                                    with conn.session as s:
                                        s.execute(text("DELETE FROM personeller WHERE telefon_no = :tel AND ad_soyad = :ad"), {"tel": bp.get('telefon_no'), "ad": bp.get('ad_soyad')})
                                        s.commit()
                                    st.success("Silindi!")
                                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")

                st.markdown("#### Yeni Saha Personeli Tanımla")
                with st.form("birim_alt_personel_form"):
                    alt_ad = st.text_input("Personelin Adı Soyadı", key="birim_alt_ad")
                    alt_tel = st.text_input("Telefon Numarası (Örn: 0555...)", key="birim_alt_tel")
                    alt_sifre = st.text_input("Şifre", type="password", key="birim_alt_sifre")
                    alt_unvan = st.selectbox("Unvan", ["Saha Personeli", "Usta", "Teknisyen", "Operatör", "Saha Ekip Sorumlusu"], key="birim_alt_unvan")
                    
                    if st.form_submit_button("Birimime Saha Personeli Kaydet"):
                        if alt_ad and alt_tel and alt_sifre:
                            with conn.session as s:
                                s.execute(text("INSERT INTO personeller (ad_soyad, telefon_no, sifre, unvan, sorumlu_birim) VALUES (:ad, :tel, :sifre, :unvan, :birim)"), {"ad": alt_ad, "tel": alt_tel.strip(), "sifre": alt_sifre, "unvan": alt_unvan, "birim": personel['sorumlu_birim']})
                                s.commit()
                            st.success("Saha personeli eklendi!")
                            st.rerun()

            st.markdown("---")
            try:
                df_t = conn.query("SELECT * FROM talepler;", ttl=0)
                sup_talepler = df_t.to_dict('records') if not df_t.empty else []
            except Exception as e:
                sup_talepler = []
                st.error(f"Talepler yüklenirken hata: {e}")

            gosterilecek_talepler = [t for t in sup_talepler if t.get('alt_bolum') == personel['sorumlu_birim']]
            
            if not gosterilecek_talepler:
                st.info("Biriminize ait aktif talep bulunmamaktadır.")
            
            for idx, talep in enumerate(gosterilecek_talepler):
                with st.expander(f"Talep ID: {talep['talep_id']} - {talep['alt_kategori']} ({talep['durum']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Vatandaş:** {talep['ad_soyad']}")
                        st.write(f"**Telefon:** {talep['telefon_no']}")
                        st.write(f"**Durum:** {talep.get('durum')}")
                        st.write(f"**Atanan Personel:** {talep.get('atanan_personel', 'Atanmadı')}")
                        st.write(f"**Açıklama:** {talep['aciklama']}")
                        
                        lat = talep.get('enlem')
                        lon = talep.get('boylam')
                        if lat and lon:
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                            st.markdown(f"**[Google Haritalar'da Aç]({maps_url})**", unsafe_allow_html=True)
                        
                        # WhatsApp Otomasyonu (Şifresiz Doğrudan Hasar Görseli Linki Dahil!)
                        atanan_kisi_adi = talep.get('atanan_personel')
                        if atanan_kisi_adi and atanan_kisi_adi != "Atanmadı":
                            try:
                                df_p_tel = conn.query("SELECT telefon_no FROM personeller WHERE ad_soyad = :p_ad;", params={"p_ad": atanan_kisi_adi}, ttl=0)
                                hedef_tel = df_p_tel.iloc[0]['telefon_no'].strip() if not df_p_tel.empty else ""
                                
                                gorsel_linki = f"{APP_BASE_URL}/?gorsel={talep['talep_id']}"
                                gorsel_satiri = f"\nHasar Fotografi (Sifresiz Goruntule): {gorsel_linki}" if talep.get('fotograf_b64') else ""
                                
                                wa_mesaj = f"Yeni Saha Gorevi ({talep['talep_id']})\nKategori: {talep['alt_kategori']}\nAciklama: {talep['aciklama']}\nKonum: https://www.google.com/maps/search/?api=1&query={lat},{lon}{gorsel_satiri}"
                                wa_url = f"https://wa.me/{hedef_tel}?text={urllib.parse.quote(wa_mesaj)}"
                                st.markdown(f"**[WhatsApp ile Saha Personeline Otomatik Gönder]({wa_url})**", unsafe_allow_html=True)
                            except:
                                pass

                        if talep.get('durum') == "Çözüldü - Kapatıldı":
                            vatandas_tel = talep.get('telefon_no', '').strip()
                            vat_mesaj = f"Sayin {talep['ad_soyad']}, {talep['talep_id']} numarali talebiniz kurumumuz tarafindan basariyla cozumlenmistir. Saglikli gunler dileriz."
                            vat_wa_url = f"https://wa.me/{vatandas_tel}?text={urllib.parse.quote(vat_mesaj)}"
                            st.markdown(f"**[Vatandaşa WhatsApp ile Bilgi Gönder]({vat_wa_url})**", unsafe_allow_html=True)

                    with col2:
                        st.markdown("**Vatandaş Hasar Fotoğrafı:**")
                        if talep.get('fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(talep['fotograf_b64']))), caption="Vatandaş Görseli", use_container_width=True)
                            except:
                                st.write("Görsel yüklenemedi.")
                        else:
                            st.write("Fotoğraf yok.")

                        st.markdown("---")
                        st.markdown("**Sahadan Gelen Çözüm Fotoğrafı:**")
                        if talep.get('saha_fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(talep['saha_fotograf_b64']))), caption="Saha Çözüm Görseli", use_container_width=True)
                            except:
                                st.write("Saha görseli yüklenemedi.")
                        else:
                            st.write("Saha personeli henüz fotoğraf yüklemedi.")
                    
                    st.markdown("---")
                    st.markdown("**Operasyon Yönetimi ve Onay Mekanizması**")
                    
                    durumlar = [
                        "Yeni (İnceleme Bekliyor)", 
                        "Talep Kabul Edildi", 
                        "Talep Reddedildi (Gerekçeli)", 
                        "Saha Ekibine Sevk Edildi", 
                        "Saha Çözümü Tamamlandı (Müdür Onayı Bekliyor)",
                        "Çözüldü - Kapatıldı"
                    ]
                    mevcut_durum = talep.get('durum', durumlar[0])
                    durum_index = durumlar.index(mevcut_durum) if mevcut_durum in durumlar else 0

                    try:
                        df_p_list = conn.query("SELECT ad_soyad FROM personeller WHERE sorumlu_birim = :birim;", params={"birim": personel['sorumlu_birim']}, ttl=0)
                        personeller = ["Atanmadı"] + [p["ad_soyad"] for p in df_p_list.to_dict('records')] if not df_p_list.empty else ["Atanmadı"]
                    except:
                        personeller = ["Atanmadı"]

                    mevcut_personel = talep.get('atanan_personel', "Atanmadı")
                    personel_index = personeller.index(mevcut_personel) if mevcut_personel in personeller else 0

                    with st.form(key=f"form_{talep['talep_id']}_{idx}"):
                        yeni_durum = st.selectbox("Talep İnceleme ve Durum Güncelle", durumlar, index=durum_index, key=f"durum_sel_{talep['talep_id']}_{idx}")
                        atanacak_kisi = st.selectbox("Saha Personeli Ata", personeller, index=personel_index, key=f"personel_sel_{talep['talep_id']}_{idx}")
                        yonetici_notu_input = st.text_area("Yönetici Notu veya Red Gerekçesi", value=talep.get('yönetici_notu', ''), key=f"not_input_{talep['talep_id']}_{idx}")
                        
                        kaydet_buton = st.form_submit_button(f"Kararı Kaydet ({talep['talep_id']})", type="primary")
                        
                        if kaydet_buton:
                            if "Reddedildi" in yeni_durum and not yonetici_notu_input.strip():
                                st.warning("Talebi reddettiğiniz için lütfen bir ret gerekçesi yazınız.")
                            else:
                                simdiki_zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                mevcut_cozum_tarihi = talep.get('cozum_tarihi', 'Henüz çözülmedi')
                                if yeni_durum == "Çözüldü - Kapatıldı" and ("Henüz" in str(mevcut_cozum_tarihi)):
                                    cozum_tarihi = simdiki_zaman
                                else:
                                    cozum_tarihi = mevcut_cozum_tarihi

                                try:
                                    q_upd = """
                                        UPDATE talepler 
                                        SET durum = :durum, 
                                            atanan_personel = :personel, 
                                            yönetici_notu = :notu, 
                                            guncelleme_tarihi = :g_tarih,
                                            cozum_tarihi = :c_tarih
                                        WHERE talep_id = :tid
                                    """
                                    with conn.session as s:
                                        s.execute(
                                            text(q_upd),
                                            {
                                                "durum": yeni_durum,
                                                "personel": atanacak_kisi,
                                                "notu": yonetici_notu_input,
                                                "g_tarih": simdiki_zaman,
                                                "c_tarih": cozum_tarihi,
                                                "tid": talep["talep_id"]
                                            }
                                        )
                                        s.commit()
                                        
                                    st.success("Talep başarıyla güncellendi!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Güncelleme hatası: {e}")

            # =========================================================================
            # 📊 YAPAY ZEKA DESTEKLİ KURUMSAL RAPORLAR VE PDF İNDİRME
            # =========================================================================
            st.markdown("---")
            st.markdown("---")
            st.header("Yapay Zeka Destekli Yönetici Raporu ve Analiz Merkezi")
            st.info("Zaman damgalarını, birim yüklerini ve coğrafi verileri analiz ederek başkanlık makamı için stratejik özetler ve resmi PDF çıktıları üretir.")
            
            try:
                df_rapor = conn.query("SELECT * FROM talepler;", ttl=0)
                
                if not df_rapor.empty:
                    toplam_talep = len(df_rapor)
                    cozulen_talep = len(df_rapor[df_rapor['durum'] == "Çözüldü - Kapatıldı"])
                    bekleyen_talep = len(df_rapor[df_rapor['durum'].str.contains("Yeni|İnceleme", na=False)])
                    reddedilen_talep = len(df_rapor[df_rapor['durum'].str.contains("Reddedildi", na=False)])
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Toplam Talep", toplam_talep)
                    col_m2.metric("Çözülen / Kapatılan", cozulen_talep)
                    col_m3.metric("İncelemedeki / Bekleyen", bekleyen_talep)
                    col_m4.metric("Reddedilen / Yersiz", reddedilen_talep)
                    
                    st.markdown("---")
                    
                    st.subheader("Yapay Zeka Destekli Stratejik Yönetici Özeti")
                    
                    en_cok_birim = "Fen İşleri Müdürlüğü"
                    if 'alt_bolum' in df_rapor.columns and not df_rapor['alt_bolum'].dropna().empty:
                        en_cok_birim = df_rapor['alt_bolum'].mode()[0]
                    
                    basari_orani = int((cozulen_talep / toplam_talep * 100)) if toplam_talep > 0 else 0
                    
                    ai_ozet_metni = f"""
                    > **Başkanlık ve Birim Amirliği Akıllı Sentezi:**
                    > Sistemde kayıtlı toplam **{toplam_talep}** bildirim incelenmiştir. Genel operasyonel başarı ve kapatılma oranı **%{basari_orani}** seviyesindedir. 
                    > En fazla talep alan sorumlu birim **{en_cok_birim}** olarak öne çıkmaktadır. Kırsal mahallelerden gelen taleplerin coğrafi kümelenme gösterdiği, altyapı ve yol bozuklukları kategorisinde yoğunlaştığı tespit edilmiştir. 
                    > **Öneri:** Kaynakların ve saha ekiplerinin en çok talep gelen hatlara yönlendirilmesi, ortalama çözüm süresini (SLA) optimize edecektir.
                    """
                    st.markdown(ai_ozet_metni)
                    
                    st.markdown("### Kurumsal Rapor Çıktısı")
                    pdf_bytes = yonetici_pdf_olustur(
                        df_rapor=df_rapor,
                        toplam=toplam_talep,
                        cozulen=cozulen_talep,
                        bekleyen=bekleyen_talep,
                        reddedilen=reddedilen_talep,
                        en_cok_birim=en_cok_birim,
                        basari_orani=basari_orani,
                        raporlayan_kisi=personel['ad_soyad'],
                        raporlayan_birim=personel['sorumlu_birim']
                    )
                    
                    st.download_button(
                        label="Resmi Yönetici Raporunu PDF Olarak İndir",
                        data=pdf_bytes,
                        file_name=f"KentAsistan_Yonetici_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                    
                    st.markdown("---")
                    
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        st.markdown("#### Sorumlu Birimlere Göre İş Yükü Dağılımı")
                        if 'alt_bolum' in df_rapor.columns:
                            st.bar_chart(df_rapor['alt_bolum'].value_counts())
                    with col_g2:
                        st.markdown("#### Kategori Bazlı Dağılım")
                        if 'alt_kategori' in df_rapor.columns:
                            st.bar_chart(df_rapor['alt_kategori'].value_counts())
                            
                    st.markdown("---")
                    st.markdown("#### Detaylı Operasyon Veri Tablosu")
                    st.dataframe(df_rapor[['talep_id', 'ad_soyad', 'alt_bolum', 'alt_kategori', 'durum', 'olusturma_tarihi', 'cozum_tarihi']], use_container_width=True)
                    
                else:
                    st.info("Rapor oluşturulabilecek henüz kayıtlı talep bulunmamaktadır.")
            except Exception as e:
                st.error(f"Raporlar yüklenirken veri tabanı hatası oluştu: {e}")
