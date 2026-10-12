"""
Kurulum (terminalde bir kez çalıştır):
    pip install pandas matplotlib seaborn
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================================================
# 0) HAZIRLIK: Klasör ve stil ayarları
# =========================================================

# Grafiklerin kaydedileceği klasörü oluştur (varsa dokunma)
os.makedirs("outputs", exist_ok=True)

# Sade, okunabilir bir görsel stil
sns.set_style("whitegrid")
plt.rcParams["figure.facecolor"] = "#fcfcfb"
plt.rcParams["axes.facecolor"] = "#fcfcfb"
plt.rcParams["axes.edgecolor"] = "#c3c2b7"
plt.rcParams["grid.color"] = "#e1e0d9"
plt.rcParams["text.color"] = "#0b0b0b"
plt.rcParams["axes.labelcolor"] = "#0b0b0b"
plt.rcParams["xtick.color"] = "#52514e"
plt.rcParams["ytick.color"] = "#52514e"
plt.rcParams["font.family"] = "sans-serif"

# Renk paleti (kategorik anlam taşıyan sabit renkler)
RENK_MAVI = "#2a78d6"     # normal hafta
RENK_TURUNCU = "#eb6834"  # tatil haftası
RENK_YESIL = "#0ca30c"    # en iyi performans
RENK_KIRMIZI = "#d03b3b"  # en zayıf performans

# =========================================================
# 1) VERİYİ OKU VE HAZIRLA
# =========================================================

df = pd.read_csv("Walmart_Sales.csv")

# Date sütununu gerçek tarihe çevir (kaynak formatı: gün-ay-yıl)
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")

# Ay bilgisini ayrı bir sütun olarak çıkar (mevsimsellik analizi için)
df["Month"] = df["Date"].dt.month

print("Veri seti boyutu:", df.shape)
print(df.head())

# =========================================================
# 2) VAKA 1: TATİL DÖNEMİ CİRO ETKİSİ
# =========================================================

# Tatil haftası (1) ve normal hafta (0) için ortalama haftalık satış
tatil_ortalama = df.groupby("Holiday_Flag")["Weekly_Sales"].mean()

satis_normal = tatil_ortalama.loc[0]
satis_tatil = tatil_ortalama.loc[1]
yuzde_fark = (satis_tatil - satis_normal) / satis_normal * 100

print("\n===== VAKA 1: Tatil Dönemi Ciro Etkisi =====")
print(f"Normal hafta ortalama satış : {satis_normal:,.2f}")
print(f"Tatil haftası ortalama satış: {satis_tatil:,.2f}")
print(f"Yüzde fark                  : %{yuzde_fark:.2f}")

# Barplot: Normal vs Tatil haftası ortalama satış
plt.figure(figsize=(6, 5))
kategoriler = ["Normal Hafta", "Tatil Haftası"]
eksen = sns.barplot(
    x=kategoriler,
    y=[satis_normal, satis_tatil],
    hue=kategoriler,
    palette=[RENK_MAVI, RENK_TURUNCU],
    legend=False,
)

# Bar üzerine değer etiketi ekle (okunabilirlik için)
for cubuk in eksen.patches:
    yukseklik = cubuk.get_height()
    eksen.text(
        cubuk.get_x() + cubuk.get_width() / 2,
        yukseklik,
        f"{yukseklik:,.0f}",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#0b0b0b",
    )

plt.title("Tatil Haftası ve Normal Hafta Ortalama Satış Karşılaştırması")
plt.ylabel("Ortalama Haftalık Satış")
plt.xlabel("")
plt.tight_layout()
plt.savefig("outputs/1_tatil_etkisi.png", dpi=150)
plt.show()

# =========================================================
# 3) VAKA 2: EN İYİ VE EN ZAYIF 5 MAĞAZA
# =========================================================

# Mağaza bazında toplam ciro
magaza_toplam = df.groupby("Store")["Weekly_Sales"].sum().sort_values(ascending=False)

en_iyi_5 = magaza_toplam.head(5)
en_zayif_5 = magaza_toplam.tail(5).sort_values(ascending=True)

print("\n===== VAKA 2: En İyi 5 Mağaza (Toplam Ciro) =====")
print(en_iyi_5)
print("\n===== VAKA 2: En Zayıf 5 Mağaza (Toplam Ciro) =====")
print(en_zayif_5)

# İki grubu tek grafikte, alt alta (subplot) gösteren yatay barplot
# ÖNEMLİ: sharex=True ile iki grafiği aynı x-eksen ölçeğine sabitliyoruz.
# Aksi halde her subplot kendi veri aralığına göre otomatik ölçeklenir ve
# çubuklar görsel olarak birbirine yakın uzunlukta görünüp gerçek farkı
# (en iyi mağaza en zayıftan ~8 kat fazla) gizler.
fig, (ust, alt) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

sns.barplot(
    x=en_iyi_5.values,
    y=en_iyi_5.index.astype(str),
    orient="h",
    color=RENK_YESIL,
    ax=ust,
)
ust.set_title("En Yüksek Ciroya Sahip İlk 5 Mağaza")
ust.set_xlabel("")
ust.set_ylabel("Mağaza No")

sns.barplot(
    x=en_zayif_5.values,
    y=en_zayif_5.index.astype(str),
    orient="h",
    color=RENK_KIRMIZI,
    ax=alt,
)
alt.set_title("En Düşük Ciroya Sahip Son 5 Mağaza")
alt.set_xlabel("Toplam Satış")
alt.set_ylabel("Mağaza No")

# Her çubuğun ucuna gerçek değeri yaz (ortak eksende küçük çubuklar
# görsel olarak sıkışık kalabileceği için sayısal okunabilirlik şart)
for eksen in (ust, alt):
    for cubuk in eksen.patches:
        genislik = cubuk.get_width()
        eksen.text(
            genislik,
            cubuk.get_y() + cubuk.get_height() / 2,
            f" {genislik:,.0f}",
            ha="left",
            va="center",
            fontsize=9,
            color="#0b0b0b",
        )

plt.tight_layout()
plt.savefig("outputs/2_magaza_performansi.png", dpi=150)
plt.show()

# =========================================================
# 4) VAKA 3: AYLIK SATIŞ TRENDİ (MEVSİMSELLİK)
# =========================================================

aylik_ortalama = df.groupby("Month")["Weekly_Sales"].mean()

print("\n===== VAKA 3: Aylık Ortalama Haftalık Satış =====")
print(aylik_ortalama)

en_yogun_ay = aylik_ortalama.idxmax()
print(f"\nEn yoğun ay: {en_yogun_ay} (Ortalama satış: {aylik_ortalama.max():,.2f})")

plt.figure(figsize=(9, 5))
eksen = sns.lineplot(
    x=aylik_ortalama.index,
    y=aylik_ortalama.values,
    marker="o",
    color=RENK_MAVI,
    linewidth=2,
)

# Her noktanın üzerine milyon (M) kısaltmalı değer etiketi ekle
for ay, deger in aylik_ortalama.items():
    eksen.text(
        ay,
        deger,
        f"{deger / 1_000_000:,.2f}M",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#0b0b0b",
    )

plt.title("Aylara Göre Ortalama Haftalık Satış Trendi")
plt.xlabel("Ay")
plt.ylabel("Ortalama Haftalık Satış")
plt.xticks(range(1, 13))
plt.tight_layout()
plt.savefig("outputs/3_aylik_trend.png", dpi=150)
plt.show()

print("\nTüm grafikler 'outputs/' klasörüne kaydedildi.")
