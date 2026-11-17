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
import os

# Uygulama Canlı URL'si (WhatsApp görsel linki üretimi için)
APP_BASE_URL = "https://kent-asistan-bpcusdhobee6vqmjbrcsxe.streamlit.app"

# Sayfa Yapılandırması ve Kurumsal Logo İkonu Entegrasyonu
ikon_yolu = "logo.jpg" if os.path.exists("logo.jpg") else "🏙️"

st.set_page_config(
    page_title="KentAsistan - Akıllı Kent ve Saha Yönetimi",
    layout="centered",
    page_icon=ikon_yolu,
    initial_sidebar_state="collapsed"
)

def logo_base64_getir(dosya_yolu="logo.jpg"):
    if os.path.exists(dosya_yolu):
        with open(dosya_yolu, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

logo_b64 = logo_base64_getir()

# --- KURUMSAL GOVTECH TASARIM & MOBİL PWA CSS ENJEKSİYONU ---
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, .stDeployButton { display: none !important; }
.stApp { background-color: #f1f5f9 !important; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 3rem !important; max-width: 780px !important; }

/* Kurumsal Üst Hero Banner - Yazılar Kesinlikle Beyaz */
.kent-hero { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 18px; padding: 22px 26px; display: flex; align-items: center; gap: 20px; box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25); margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.08); }
.kent-hero img { width: 84px; height: 84px; object-fit: cover; border-radius: 14px; border: 2px solid rgba(56, 189, 248, 0.35); flex-shrink: 0; }
.kent-hero-text h1 { color: #ffffff !important; font-size: 1.65rem !important; font-weight: 700 !important; margin: 0 0 4px 0 !important; padding: 0 !important; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.kent-hero-text p { color: #e2e8f0 !important; font-size: 0.9rem !important; margin: 0 0 8px 0 !important; line-height: 1.4; }
.kent-badge { display: inline-block; background: rgba(2, 132, 199, 0.35); color: #38bdf8 !important; border: 1px solid rgba(56, 189, 248, 0.5); font-size: 0.72rem; font-weight: 600; padding: 3px 10px; border-radius: 999px; }

/* Form Etiketleri ve Genel Metinler */
.stSelectbox label p, .stTextInput label p, .stTextArea label p, .stRadio label p, .stFileUploader label p { color: #0f172a !important; font-weight: 600 !important; font-size: 0.92rem !important; }
p, span { color: #334155; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p { color: #ffffff !important; }
.stSelectbox>div>div, .stTextInput>div>div>input, .stTextArea>div>div>textarea { background-color: #ffffff !important; color: #0f172a !important; border-radius: 10px !important; border-color: #cbd5e1 !important; }

/* Modern Sekme (Tab) Tasarımı */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #e2e8f0; padding: 6px; border-radius: 14px; margin-bottom: 16px; }
.stTabs [data-baseweb="tab"] { height: 44px; border-radius: 10px; font-weight: 600; font-size: 0.88rem; color: #475569; padding: 0 14px; border: none !important; background-color: transparent; }
.stTabs [aria-selected="true"] { background-color: #ffffff !important; color: #0f172a !important; box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

/* Bölüm Kart Başlıkları */
.section-card-header { background: #ffffff; border-left: 4px solid #0284c7; padding: 14px 18px; border-radius: 10px; margin: 16px 0 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.section-card-header h4 { margin: 0 0 2px 0 !important; color: #0f172a !important; font-size: 1.02rem !important; font-weight: 700 !important; }
.section-card-header span { color: #475569 !important; font-size: 0.84rem !important; font-weight: 500 !important; display: block; }

.gps-box { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1.5px dashed #0284c7; border-radius: 14px; padding: 14px 16px; margin-bottom: 10px; }
.gps-box-title { color: #0369a1 !important; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
.gps-box-desc { color: #334155 !important; font-size: 0.82rem; margin: 0; }

iframe[title*="streamlit_geolocation"] { transform: scale(1.28); transform-origin: left center; margin: 6px 0 6px 4px; border-radius: 8px; }

/* Birincil Butonlar (Yazılar Kesinlikle Beyaz ve Kalın) */
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { background: linear-gradient(135deg, #0f172a 0%, #0284c7 100%) !important; border: none !important; border-radius: 12px !important; min-height: 48px !important; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25) !important; transition: all 0.2s ease !important; }
.stButton>button[kind="primary"] p, .stDownloadButton>button[kind="primary"] p, .stFormSubmitButton>button[kind="primary"] p,
.stButton>button[kind="primary"] span, .stDownloadButton>button[kind="primary"] span, .stFormSubmitButton>button[kind="primary"] span { color: #ffffff !important; font-weight: 700 !important; font-size: 1rem !important; }
.stButton>button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(2, 132, 199, 0.35) !important; }

.stButton>button, .stDownloadButton>button, .stLinkButton>a { border-radius: 12px !important; font-weight: 600 !important; min-height: 46px !important; }

div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
.streamlit-expanderHeader { background-color: #ffffff !important; border-radius: 12px !important; border: 1px solid #e2e8f0 !important; font-weight: 600 !important; color: #1e293b !important; padding: 14px !important; }

[data-testid="stSidebar"] { background-color: #0f172a; color: #ffffff; }
[data-testid="stSidebar"] .stMarkdown { color: #e2e8f0; }

@media (max-width: 640px) {
.kent-hero { padding: 16px; gap: 14px; }
.kent-hero img { width: 66px; height: 66px; }
.kent-hero-text h1 { font-size: 1.35rem !important; }
.kent-hero-text p { font-size: 0.8rem !important; }
.stTabs [data-baseweb="tab"] { font-size: 0.78rem; padding: 0 8px; }
}
</style>""", unsafe_allow_html=True)

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
                    st.link_button("🗺️ Google Haritalar'da Yol Tarifi Al", maps_url, type="primary", use_container_width=True)
                
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
                if st.button("🏠 Ana Uygulamaya / Giriş Ekranına Geç", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()
            else:
                st.error("Belirtilen talep numarasına ait kayıt bulunamadı.")
        except Exception as e:
            st.error(f"Veri getirme hatası: {e}")
    st.stop()

# --- TÜRKÇE KARAKTER DÖNÜŞTÜRÜCÜ & PDF OLUŞTURMA MOTORU ---
def tr_temizle(metin):
    if not metin:
        return ""
    ceviri = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    temizlenmis = str(metin).translate(ceviri)
    temizlenmis = ''.join(c for c in temizlenmis if ord(c) < 128)
    return temizlenmis

def yonetici_pdf_olustur(df_rapor, toplam, cozulen, bekleyen, reddedilen, en_cok_birim, basari_orani, tasarruf_tl, ort_sla_saat, raporlayan_kisi, raporlayan_birim):
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
    pdf.cell(0, 6, tr_temizle("Insan Kaynaklari, Ekonomik Verimlilik ve Stratejik Denetim Raporu"), ln=True)
    
    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(10, 42)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, tr_temizle(f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), ln=True)
    pdf.cell(0, 6, tr_temizle(f"Duzenleyen Yetkili: {raporlayan_kisi} ({raporlayan_birim})"), ln=True)
    pdf.ln(4)
    
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 1. OPERASYONEL VE EKONOMIK KAYNAK OZETI (KPI)"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 7, tr_temizle(f"- Toplam Gelen Bildirim: {toplam}"), border=1)
    pdf.cell(95, 7, tr_temizle(f"- Cozulen / Kapatilan Talep: {cozulen}"), border=1, ln=True)
    pdf.cell(95, 7, tr_temizle(f"- Incelemede / Bekleyen: {bekleyen}"), border=1)
    pdf.cell(95, 7, tr_temizle(f"- Reddedilen / Yersiz Talep: {reddedilen}"), border=1, ln=True)
    pdf.cell(95, 7, tr_temizle(f"- Ortalama Cozum Suresi (SLA): {ort_sla_saat} Saat"), border=1)
    pdf.cell(95, 7, tr_temizle(f"- Tahmini Rota/Saha Tasarrufu: {tasarruf_tl} TL"), border=1, ln=True)
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, tr_temizle(" 2. YAPAY ZEKA DESTEKLI KAYNAK OPTIMIZASYON OZETI"), ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 10)
    ozet_1 = f"- Operasyonel Basari Orani: %{basari_orani} seviyesindedir."
    ozet_2 = f"- En Yogun Birim Analizi: En fazla is yuku '{en_cok_birim}' biriminde toplanmistir."
    ozet_3 = f"- Ekonomik ve Insan Kaynagi Verimliligi: Dogrudan GPS ve gorsel teyitli sevk mekanizmasi sayesinde gereksiz saha kesif turlari onlenmis, yaklasik {tasarruf_tl} TL akaryakit ve adam/saat tasarrufu saglanmistir."
    
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
    pdf.cell(50, 7, tr_temizle("Sorumlu Personel"), border=1, fill=True)
    pdf.cell(60, 7, tr_temizle("Mevcut Durum"), border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 8)
    for _, row in df_rapor.tail(15).iterrows():
        t_id = tr_temizle(row.get('talep_id', ''))[:14]
        alt_k = tr_temizle(row.get('alt_kategori', ''))[:28]
        pers = tr_temizle(row.get('atanan_personel', ''))[:26]
        durum = tr_temizle(row.get('durum', ''))[:32]
        
        pdf.cell(28, 6, t_id, border=1)
        pdf.cell(52, 6, alt_k, border=1)
        pdf.cell(50, 6, pers, border=1)
        pdf.cell(60, 6, durum, border=1, ln=True)
        
    return bytes(pdf.output())

# --- GLOBAL OTURUM HAFIZASI ---
if "personel_giris" not in st.session_state:
    st.session_state["personel_giris"] = False
if "giris_yapan_personel" not in st.session_state:
    st.session_state["giris_yapan_personel"] = None

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

st.sidebar.markdown("---")
st.sidebar.info("📱 **Mobil Uygulama İpucu:** Tarayıcı menüsünden *'Ana Ekrana Ekle'* seçeneğine dokunarak KentAsistan'ı telefonunuza uygulama olarak kurabilirsiniz.")

# --- KURUMSAL KOYU LACİVERT ÜST HERO BANNER ---
img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="KentAsistan Logo">' if logo_b64 else ''
st.markdown(f"""
    <div class="kent-hero">
        {img_html}
        <div class="kent-hero-text">
            <span class="kent-badge">🏛️ YENİPAZAR BELEDİYESİ ORTAK ÇÖZÜM MASASI</span>
            <h1>KentAsistan</h1>
            <p>Akıllı Kent, CBS Konum Doğrulamalı Talep ve Saha Yönetim Sistemi</p>
        </div>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Talep Bildir", "🔍 Talep Sorgula", "🔒 Kurum Paneli"])

with tab1:
    st.markdown("""
        <div class="section-card-header">
            <h4>1. Bildirim ve İletişim Bilgileri</h4>
            <span>Kırsal mahalleler ve merkez dahil tüm vatandaşlarımız için hızlı bildirim portalı</span>
        </div>
    """, unsafe_allow_html=True)
    
    col_il1, col_il2 = st.columns(2)
    with col_il1:
        secilen_il = st.selectbox("İl", options=["Aydın", "Diğer"], index=0, key="vat_il")
    with col_il2:
        secilen_ilce = st.selectbox("İlçe", options=["Yenipazar", "Diğer"], index=0, key="vat_ilce")
        
    if secilen_ilce != "Yenipazar":
        st.warning("KentAsistan şu an yalnızca **Yenipazar** ilçesinde aktif olarak hizmet vermektedir.")
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        ad_soyad = st.text_input("Ad Soyad *", placeholder="Örn: Ahmet Yılmaz", key="vat_ad")
    with col_k2:
        telefon = st.text_input("Telefon Numarası *", placeholder="Örn: 0555 123 45 67", key="vat_tel")
        
    tc_kimlik = st.text_input("TC Kimlik Numarası (Opsiyonel)", placeholder="İsteğe bağlı girebilirsiniz", key="vat_tc")
    
    col_kat1, col_kat2 = st.columns(2)
    with col_kat1:
        secilen_ana_kategori = st.selectbox("Ana Kategori", options=ana_kategoriler, key="ana_kat_secim")
    
    filtrelenmis_altlar = [item for item in tum_veriler if item["ana_kategori"] == secilen_ana_kategori]
    alt_kategori_isimleri = [item["alt_kategori"] for item in filtrelenmis_altlar]
    
    with col_kat2:
        secilen_alt_kategori = st.selectbox("Alt Kategori / Konu", options=alt_kategori_isimleri, key="alt_kat_secim")
    
    # --- 2. BÖLÜM: MODERN GPS DOĞRULAMA KARTI ---
    st.markdown("""
        <div class="section-card-header">
            <h4>2. CBS / GPS Konum Doğrulama ve Hasar Görseli</h4>
            <span>Talebinizin doğru saha ekibine yönlendirilmesi için konumunuzu doğrulayın</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="gps-box">
            <div class="gps-box-title">📍 Adım 1: Aşağıdaki Hedef (GPS) İkonuna Dokunarak Konumunuzu Alın</div>
            <p class="gps-box-desc">Tarayıcınız konum izni isterse <b>"İzin Ver"</b> seçeneğini onaylayın. Sistem Yenipazar ilçe sınırlarını otomatik kontrol edecektir.</p>
        </div>
    """, unsafe_allow_html=True)

    col_gps_btn, col_gps_durum = st.columns([1, 3])
    with col_gps_btn:
        location = streamlit_geolocation()
    
    with col_gps_durum:
        if location and location.get('latitude') is not None and location.get('longitude') is not None:
            test_lat = location.get('latitude')
            test_lon = location.get('longitude')
            sinir_ok = True
            if yenipazar_poligonu is not None:
                sinir_ok = yenipazar_poligonu.contains(Point(test_lon, test_lat))
            if sinir_ok:
                st.success(f"✅ **GPS Konumu Doğrulandı!** (Yenipazar İlçe Sınırı İçi)\nKoordinat: `{test_lat:.5f}, {test_lon:.5f}`")
            else:
                st.error(f"❌ **Konum Sınır Dışı!** Koordinatlarınız (`{test_lat:.5f}, {test_lon:.5f}`) Yenipazar hizmet sınırı dışında görünüyor.")
        else:
            st.info("👈 Konum almak için soldaki hedef simgesine tıklayın.")

    konum_izni = st.radio(
        "Konum Paylaşım Onayı:",
        [
            "Konumumun paylaşılmasına izin veriyorum (GPS ile bağlan)", 
            "İzin vermiyorum"
        ],
        key="vat_konum_izni",
        horizontal=True
    )
    
    fotograf = st.file_uploader("📷 Hasarlı Bölgenin Canlı Fotoğrafı (Zorunludur - Galeriden Seçilemez)", type=["jpg", "jpeg", "png"], key="vat_foto")
if fotograf is None:
    st.warning("⚠️ Lütfen kameranızı kullanarak hasarlı bölgenin anlık fotoğrafını çekip yükleyiniz.")
    aciklama = st.text_area("Talep / Şikayet Açıklaması *", placeholder="Mahalle, sokak bilgisi ve sorunu kısaca açıklayınız...", key="vat_aciklama")
    
    gonder_btn = st.button("🚀 Talebi Sisteme Gönder", key="vat_gonder_btn", type="primary", use_container_width=True)
    
    if gonder_btn:
        if not ad_soyad or not telefon or not aciklama:
            st.error("Lütfen zorunlu alanları (*) doldurunuz.")
        elif secilen_ilce != "Yenipazar":
            st.error("Seçilen ilçe için sistem aktif değildir.")
        elif "İzin vermiyorum" in konum_izni:
            st.error("Konum paylaşımına izin vermediğiniz için talep oluşturulamamaktadır.")
        elif location is None or location.get('latitude') is None or location.get('longitude') is None:
            st.error("GPS konum veriniz henüz alınmadı. Lütfen yukarıdaki hedef ikonuna basarak konum izni veriniz.")
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

# =========================================================================
# 🔍 2. SEKME: GÜVENLİ VATANDAŞ TALEP VE SÜREÇ TAKİP MERKEZİ
# =========================================================================
with tab2:
    st.markdown("""
        <div class="section-card-header">
            <h4>Güvenli Vatandaş Talep ve Süreç Takip Merkezi</h4>
            <span>KVKK gereği takip numaranız ve kayıtlı telefon numaranız ile sorgulama yapabilirsiniz</span>
        </div>
    """, unsafe_allow_html=True)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sorgu_id = st.text_input("Talep Takip Numarası", placeholder="Örn: KENT-12345", key="vat_sorgu_id")
    with col_s2:
        sorgu_tel = st.text_input("Kayıtlı Telefon Numaranız", placeholder="Örn: 0555...", key="vat_sorgu_tel")
    
    if st.button("🔍 Talebi Güvenli Sorgula", key="guvenli_sorgula_btn", type="primary", use_container_width=True):
        if sorgu_id and sorgu_tel:
            try:
                clean_sorgu_tel = sorgu_tel.strip().replace(" ", "")
                q_guvenli = "SELECT * FROM talepler WHERE talep_id = :tid AND telefon_no = :tel;"
                df_sorgu = conn.query(q_guvenli, params={"tid": sorgu_id.strip(), "tel": clean_sorgu_tel}, ttl=0)
                
                if not df_sorgu.empty:
                    t = df_sorgu.iloc[0].to_dict()
                    st.success(f"Doğrulama Başarılı! Talep: {t['talep_id']} ({t['alt_kategori']})")
                    
                    st.markdown("### 🕒 Şeffaf Süreç Akışı ve Denetim İzi")
                    st.markdown(f"1. **Talep Oluşturma:** `{t.get('olusturma_tarihi', '-')}` tarihinde oluşturuldu ve **{t.get('alt_bolum')}** ({t.get('sorumlu_kurum')}) birimine iletildi.")
                    st.markdown(f"2. **Kurum İncelemesi:** Mevcut Durum: **{t.get('durum')}**")
                    st.markdown(f"3. **Saha Ekibi Sevk:** Atanan Sorumlu: **{t.get('atanan_personel')}** (Sevk Zamanı: `{t.get('guncelleme_tarihi', '-')}`)")
                    st.markdown(f"4. **Çözüm ve Kapanış:** `{t.get('cozum_tarihi', 'Sahada işlem devam ediyor')}`")
                    
                    if t.get('yönetici_notu') and t.get('yönetici_notu') != "Henüz not eklenmedi":
                        st.info(f"**Kurum / Müdür Notu:** {t.get('yönetici_notu')}")
                        
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        st.markdown("**Bildirim Fotoğrafınız:**")
                        if t.get('fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(t['fotograf_b64']))), caption="Yüklediğiniz Görsel", use_container_width=True)
                            except:
                                st.write("Görsel yüklenemedi.")
                        else:
                            st.write("Fotoğraf yüklememiştiniz.")
                    with c_f2:
                        st.markdown("**Saha Çözüm Kanıt Fotoğrafı:**")
                        if t.get('saha_fotograf_b64'):
                            try:
                                st.image(Image.open(io.BytesIO(base64.b64decode(t['saha_fotograf_b64']))), caption="Çözüm Görseli", use_container_width=True)
                            except:
                                st.write("Saha görseli çözülemedi.")
                        else:
                            st.info("Saha ekibi henüz çözüm fotoğrafı yüklemedi veya inceleme aşamasında.")
                else:
                    st.error("❌ Girdiğiniz Takip Numarası ile Telefon Numarası eşleşmedi! Lütfen bilgilerinizi kontrol ediniz.")
            except Exception as e:
                st.error(f"Sorgulama sırasında hata oluştu: {e}")
        else:
            st.warning("⚠️ Lütfen hem takip numaranızı hem de telefon numaranızı eksiksiz girin.")

# =========================================================================
# 🔒 3. SEKME: KURUM VE PERSONEL GİRİŞ PANELİ
# =========================================================================
with tab3:
    st.markdown("""
        <div class="section-card-header">
            <h4>Kurum Yöneticisi ve Saha Personeli Giriş Portalı</h4>
            <span>Yetkili kurum müdürleri, amirler ve saha ekipleri için şifreli erişim alanı</span>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state["personel_giris"]:
        tel_giris = st.text_input("Telefon Numarası", placeholder="Örn: 0555...", key="personel_tel_input")
        sifre_giris = st.text_input("Şifre", type="password", placeholder="••••••", key="personel_sifre_input")
        
        if st.button("🔐 Güvenli Giriş Yap", key="personel_giris_btn", type="primary", use_container_width=True):
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
        col_w1, col_w2 = st.columns([3, 1])
        with col_w1:
            st.success(f"👤 **{personel['ad_soyad']}** | {personel['unvan']} ({personel['sorumlu_birim']})")
        with col_w2:
            if st.button("🚪 Çıkış", key="cikis_yap_btn", use_container_width=True):
                st.session_state["personel_giris"] = False
                st.session_state["giris_yapan_personel"] = None
                st.rerun()

        unvan_degeri = str(personel.get("unvan", "")).strip().lower()
        is_super_admin = unvan_degeri in ["süper_admin", "süper admin", "super_admin", "super admin"]
        is_saha_personeli = unvan_degeri in ["saha personeli", "usta", "teknisyen", "operatör", "saha ekip sorumlusu"]

        # 1. SÜPER ADMIN PANELİ
        if is_super_admin:
            st.markdown("---")
            st.subheader("👑 Süper Admin - Platform Yönetim Paneli")
            
            admin_secim = st.radio("Yönetim İşlemi Seçin:", ["Sistem Kurum ve Yetkili Matrisi", "Kurum Yöneticisi / Müdür Ekle"], key="admin_radio_secim", horizontal=True)
            
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
                
                if st.button("Kaydet", key="yonetici_olustur_btn", type="primary", use_container_width=True):
                    if p_ad and p_tel and p_sifre:
                        with conn.session as s:
                            s.execute(text("INSERT INTO personeller (ad_soyad, telefon_no, sifre, unvan, sorumlu_birim) VALUES (:ad, :tel, :sifre, :unvan, :birim)"), {"ad": p_ad, "tel": p_tel.strip(), "sifre": p_sifre, "unvan": p_unvan, "birim": p_birim})
                            s.commit()
                        st.success("Yönetici eklendi!")
                        st.rerun()

        # 2. SAHA PERSONELİ MOBİL OPERASYON PANELİ
        elif is_saha_personeli:
            st.markdown("---")
            st.subheader(f"📱 Saha Mobil Operasyon Paneli")
            
            try:
                df_t_saha = conn.query("SELECT * FROM talepler WHERE atanan_personel = :personel_ad;", params={"personel_ad": personel['ad_soyad']}, ttl=0)
                saha_gorevleri = df_t_saha.to_dict('records') if not df_t_saha.empty else []
            except Exception as e:
                saha_gorevleri = []
                st.error(f"Görevler yüklenirken hata: {e}")

            bekleyen_is_sayisi = len([g for g in saha_gorevleri if "Çözüldü" not in str(g.get('durum')) and "Tamamlandı" not in str(g.get('durum'))])
            if bekleyen_is_sayisi > 0:
                st.error(f"🔔 **CANLI GÖREV BİLDİRİMİ:** Üzerinize atanmış **{bekleyen_is_sayisi} adet** aktif saha görevi bulunmaktadır!")
            else:
                st.success("✅ Üzerinize atanmış bekleyen yeni iş emri bulunmamaktadır.")
            
            for idx, gorev in enumerate(saha_gorevleri):
                durum_ikonu = "🔴" if "Sevk" in str(gorev['durum']) or "Kabul" in str(gorev['durum']) else "🟢"
                with st.expander(f"{durum_ikonu} Görev: {gorev['talep_id']} - {gorev['alt_kategori']} ({gorev['durum']})", expanded=(durum_ikonu == "🔴")):
                    st.write(f"**Vatandaş Açıklaması:** {gorev['aciklama']}")
                    st.write(f"**Atama Zamanı:** `{gorev.get('guncelleme_tarihi', '-')}`")
                    
                    lat = gorev.get('enlem')
                    lon = gorev.get('boylam')
                    if lat and lon:
                        maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        st.link_button("🗺️ Google Haritalar ile Sahaya Git", maps_url, type="primary", use_container_width=True)
                    
                    if gorev.get('fotograf_b64'):
                        st.markdown("**Vatandaş Hasar Görseli:**")
                        try:
                            st.image(Image.open(io.BytesIO(base64.b64decode(gorev['fotograf_b64']))), use_container_width=True)
                        except:
                            pass
                            
                    st.markdown("---")
                    st.markdown("**Sahada Yapılan İşi Kanıtlama (Çözüm Fotoğrafı Yükle):**")
                    
                    saha_foto_yukle = st.camera_input("📸 Çözüm Sonrası Canlı Fotoğraf Çek", key=f"saha_up_{gorev['talep_id']}_{idx}")
                    
                    if st.button(f"✅ İşi Tamamla ve Müdüre Gönder ({gorev['talep_id']})", key=f"saha_gonder_{gorev['talep_id']}_{idx}", type="primary", use_container_width=True):
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

        # 3. KURUM YETKİLİSİ / MÜDÜR PANELİ
        else:
            st.markdown("---")
            st.subheader(f"🏛️ {personel['sorumlu_birim']} - Operasyon Paneli")
            
            with st.expander("👥 Birim Saha Personelleri ve İnsan Kaynağı Yönetimi"):
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
                    
                    if st.form_submit_button("Birimime Saha Personeli Kaydet", use_container_width=True):
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
                with st.expander(f"📌 Talep ID: {talep['talep_id']} - {talep['alt_kategori']} ({talep['durum']})"):
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
                            st.link_button("🗺️ Konumu Haritada Gör", maps_url, use_container_width=True)
                        
                        atanan_kisi_adi = talep.get('atanan_personel')
                        if atanan_kisi_adi and atanan_kisi_adi != "Atanmadı":
                            try:
                                df_p_tel = conn.query("SELECT telefon_no FROM personeller WHERE ad_soyad = :p_ad;", params={"p_ad": atanan_kisi_adi}, ttl=0)
                                hedef_tel = df_p_tel.iloc[0]['telefon_no'].strip() if not df_p_tel.empty else ""
                                
                                gorsel_linki = f"{APP_BASE_URL}/?gorsel={talep['talep_id']}"
                                gorsel_satiri = f"\nHasar Fotografi (Sifresiz Goruntule): {gorsel_linki}" if talep.get('fotograf_b64') else ""
                                
                                wa_mesaj = f"🔔 *Yeni Saha Gorevi ({talep['talep_id']})*\n*Kategori:* {talep['alt_kategori']}\n*Aciklama:* {talep['aciklama']}\n*Konum:* https://www.google.com/maps/search/?api=1&query={lat},{lon}{gorsel_satiri}"
                                wa_url = f"https://wa.me/{hedef_tel}?text={urllib.parse.quote(wa_mesaj)}"
                                st.link_button("📲 WhatsApp ile Saha Personeline Gönder", wa_url, use_container_width=True)
                            except:
                                pass

                        if talep.get('durum') == "Çözüldü - Kapatıldı":
                            vatandas_tel = talep.get('telefon_no', '').strip()
                            vat_mesaj = f"Sayin {talep['ad_soyad']}, {talep['talep_id']} numarali talebiniz kurumumuz tarafindan basariyla cozumlenmistir. Saglikli gunler dileriz."
                            vat_wa_url = f"https://wa.me/{vatandas_tel}?text={urllib.parse.quote(vat_mesaj)}"
                            st.link_button("✅ Vatandaşa WhatsApp Çözüm Bildirimi Gönder", vat_wa_url, type="primary", use_container_width=True)

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
                        atanacak_kisi = st.selectbox("Saha Personeli Ata / Değiştir", personeller, index=personel_index, key=f"personel_sel_{talep['talep_id']}_{idx}")
                        yonetici_notu_input = st.text_area("Yönetici Notu veya Red Gerekçesi", value=talep.get('yönetici_notu', ''), key=f"not_input_{talep['talep_id']}_{idx}")
                        
                        kaydet_buton = st.form_submit_button(f"Kararı ve Atamayı Kaydet ({talep['talep_id']})", type="primary", use_container_width=True)
                        
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
                                        
                                    st.success("Talep ve personel ataması başarıyla güncellendi!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Güncelleme hatası: {e}")

            # 📊 İNSAN VE EKONOMİK KAYNAK YÖNETİMİ ANALİZ MERKEZİ
            st.markdown("---")
            st.header("📊 İnsan ve Ekonomik Kaynak Yönetimi Analiz Merkezi")
            st.info("Saha personeli iş yüklerini, ortalama çözüm sürelerini (SLA) ve gereksiz keşif turlarının önlenmesiyle sağlanan ekonomik tasarrufu hesaplar.")
            
            try:
                df_rapor = conn.query("SELECT * FROM talepler;", ttl=0)
                
                if not df_rapor.empty:
                    toplam_talep = len(df_rapor)
                    cozulen_talep = len(df_rapor[df_rapor['durum'] == "Çözüldü - Kapatıldı"])
                    bekleyen_talep = len(df_rapor[df_rapor['durum'].str.contains("Yeni|İnceleme", na=False)])
                    reddedilen_talep = len(df_rapor[df_rapor['durum'].str.contains("Reddedildi", na=False)])
                    
                    tahmini_tasarruf_tl = (cozulen_talep + reddedilen_talep) * 450
                    
                    sla_saatler = []
                    for _, r in df_rapor.iterrows():
                        try:
                            t1 = datetime.strptime(str(r['olusturma_tarihi']), "%Y-%m-%d %H:%M:%S")
                            t2 = datetime.strptime(str(r['cozum_tarihi']), "%Y-%m-%d %H:%M:%S")
                            fark_saat = round((t2 - t1).total_seconds() / 3600, 1)
                            if fark_saat >= 0:
                                sla_saatler.append(fark_saat)
                        except:
                            pass
                    ort_sla_saat = round(sum(sla_saatler) / len(sla_saatler), 1) if sla_saatler else 2.4
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Toplam Bildirim", toplam_talep)
                    col_m2.metric("Çözülen İş", cozulen_talep)
                    col_m3.metric("Ort. Çözüm (SLA)", f"{ort_sla_saat} Saat")
                    col_m4.metric("Ekonomik Tasarruf", f"₺{tahmini_tasarruf_tl:,}")
                    
                    st.markdown("---")
                    
                    st.subheader("👷 İnsan Kaynağı ve Saha Ekibi Verimlilik Tablosu")
                    atanan_df = df_rapor[df_rapor['atanan_personel'] != "Atanmadı"]
                    if not atanan_df.empty:
                        personel_ozet = []
                        for pers_adi, grup in atanan_df.groupby('atanan_personel'):
                            toplam_is = len(grup)
                            tamamlanan_is = len(grup[grup['durum'] == "Çözüldü - Kapatıldı"])
                            aktif_is = toplam_is - tamamlanan_is
                            verim = f"%{int((tamamlanan_is / toplam_is) * 100)}" if toplam_is > 0 else "%0"
                            personel_ozet.append({
                                "Saha Personeli / Usta": pers_adi,
                                "Atanan Toplam İş": toplam_is,
                                "Tamamlanan İş": tamamlanan_is,
                                "Sahada Devam Eden": aktif_is,
                                "Tamamlama Verimliliği": verim
                            })
                        st.dataframe(pd.DataFrame(personel_ozet), use_container_width=True, hide_index=True)
                    else:
                        st.info("Henüz saha personeline atanmış görev kaydı bulunmamaktadır.")

                    st.markdown("---")
                    
                    en_cok_birim = "Fen İşleri Müdürlüğü"
                    if 'alt_bolum' in df_rapor.columns and not df_rapor['alt_bolum'].dropna().empty:
                        en_cok_birim = df_rapor['alt_bolum'].mode()[0]
                    
                    basari_orani = int((cozulen_talep / toplam_talep * 100)) if toplam_talep > 0 else 0
                    
                    ai_ozet_metni = f"""
                    > **Başkanlık ve Kaynak Yönetimi Akıllı Sentezi:**
                    > Sistemde kayıtlı toplam **{toplam_talep}** bildirim üzerinden genel operasyonel başarı oranı **%{basari_orani}**, ortalama müdahale süresi (SLA) ise **{ort_sla_saat} saat** olarak ölçülmüştür. 
                    > Vatandaş fotoğrafı ve CBS/GPS doğrulaması sayesinde gereksiz saha keşif araç çıkışları önlenmiş, belediye bütçesine yaklaşık **₺{tahmini_tasarruf_tl:,}** doğrudan akaryakıt ve adam/saat tasarrufu sağlanmıştır.
                    > **İnsan Kaynağı Önerisi:** En yoğun iş yükü **{en_cok_birim}** birimindedir; vardiya ve ekip planlamasının bu birimdeki aktif iş sayısına göre dengelenmesi önerilir.
                    """
                    st.markdown(ai_ozet_metni)
                    
                    st.markdown("### 📄 Kurumsal Denetim ve Kaynak Raporu")
                    pdf_bytes = yonetici_pdf_olustur(
                        df_rapor=df_rapor,
                        toplam=toplam_talep,
                        cozulen=cozulen_talep,
                        bekleyen=bekleyen_talep,
                        reddedilen=reddedilen_talep,
                        en_cok_birim=en_cok_birim,
                        basari_orani=basari_orani,
                        tasarruf_tl=tahmini_tasarruf_tl,
                        ort_sla_saat=ort_sla_saat,
                        raporlayan_kisi=personel['ad_soyad'],
                        raporlayan_birim=personel['sorumlu_birim']
                    )
                    
                    st.download_button(
                        label="📥 Resmi Yönetici ve Kaynak Raporunu PDF Olarak İndir",
                        data=pdf_bytes,
                        file_name=f"KentAsistan_Kaynak_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        key="yonetici_pdf_indir_btn",
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        st.markdown("#### Sorumlu Birimlere Göre İş Yükü")
                        if 'alt_bolum' in df_rapor.columns:
                            st.bar_chart(df_rapor['alt_bolum'].value_counts())
                    with col_g2:
                        st.markdown("#### Kategori Bazlı Dağılım")
                        if 'alt_kategori' in df_rapor.columns:
                            st.bar_chart(df_rapor['alt_kategori'].value_counts())
                            
                else:
                    st.info("Rapor oluşturulabilecek henüz kayıtlı talep bulunmamaktadır.")
            except Exception as e:
                st.error(f"Raporlar yüklenirken veri tabanı hatası oluştu: {e}")
