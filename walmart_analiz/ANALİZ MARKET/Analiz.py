"""
WALMART HAFTALIK SATIŞ ANALİZİ
================================
Kapsamlı keşifsel veri analizi, korelasyon analizi, hipotez testleri,
zaman serisi incelemesi ve çoklu doğrusal regresyon.

Girdi   : Walmart_Sales_clean.csv (önceden yüklenmiş / temizlenmiş veri)
Çıktılar: outputs/*.png  (grafikler)
          analysis_report.md (akademik özet rapor)

Not: Veri yükleme, sütun kontrolü ve temizleme adımları daha önce
WalmartBaşlangıç.py içinde yapıldığından burada tekrar edilmemiştir.

Kurulum (bir kez):
    pip install pandas numpy matplotlib seaborn scipy statsmodels
"""

import os
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# =========================================================
# 0) HAZIRLIK: klasör, stil, sabitler, rapor altyapısı
# =========================================================

os.makedirs("outputs", exist_ok=True)

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

RENK_MAVI = "#2a78d6"      # normal hafta / genel seri
RENK_TURUNCU = "#eb6834"   # tatil haftası
RENK_YESIL = "#0ca30c"     # en iyi performans / pozitif
RENK_KIRMIZI = "#d03b3b"   # en zayıf performans / negatif
RENK_MOR = "#7b4fa3"       # hareketli ortalama / regresyon vurgusu
RENK_GRI = "#8a8a86"       # yardımcı / referans çizgiler

ALPHA = 0.05  # tüm hipotez testlerinde kullanılan anlamlılık düzeyi

# ---- Rapor için yardımcı fonksiyonlar -------------------------------------
rapor = []  # analysis_report.md içeriğini biriktiren satır listesi


def baslik(metin, seviye=2):
    rapor.append(f"\n{'#' * seviye} {metin}\n")


def yaz(metin=""):
    rapor.append(metin)


def pfmt(p):
    """P-değerini akademik biçimde yazdırır."""
    return "< 0.001" if p < 0.001 else f"{p:.4f}"


def sayi(x, ondalik=2):
    return f"{x:,.{ondalik}f}"


def korelasyon_gucu(r):
    ar = abs(r)
    if ar < 0.10:
        return "ihmal edilebilir düzeyde"
    elif ar < 0.30:
        return "zayıf düzeyde"
    elif ar < 0.50:
        return "orta düzeyde"
    elif ar < 0.70:
        return "orta-güçlü düzeyde"
    elif ar < 0.90:
        return "güçlü düzeyde"
    return "çok güçlü düzeyde"


# =========================================================
# 1) VERİYİ OKU (temizlenmiş veri kullanılıyor, tekrar temizlik yapılmaz)
# =========================================================

df = pd.read_csv("Walmart_Sales_clean.csv")
df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month

AY_ADLARI = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
             "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

baslik("Walmart Haftalık Satış Analizi — Sonuç Raporu", seviye=1)
yaz(
    f"Veri seti **{df.shape[0]}** satır ve **{df.shape[1]}** sütundan oluşmaktadır. "
    f"Gözlemler **{df['Store'].nunique()}** farklı mağazaya ve "
    f"**{df['Date'].min().date()} – {df['Date'].max().date()}** tarih aralığına aittir. "
    f"Tüm testlerde anlamlılık düzeyi **alpha = {ALPHA}** olarak alınmıştır."
)

# =========================================================
# 2) KEŞİFSEL VERİ ANALİZİ (EDA)
# =========================================================
print("\n===== 1) KEŞİFSEL VERİ ANALİZİ =====")

ws = df["Weekly_Sales"]
ws_ozet = {
    "ortalama": ws.mean(),
    "medyan": ws.median(),
    "std": ws.std(),
    "min": ws.min(),
    "maks": ws.max(),
}
print("Weekly_Sales özet istatistikleri:")
for k, v in ws_ozet.items():
    print(f"  {k:8s}: {v:,.2f}")

# --- 2.1 Histogram + Boxplot (Weekly_Sales dağılımı) ------------------------
fig, (ax_hist, ax_box) = plt.subplots(
    2, 1, figsize=(9, 7), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
)
sns.histplot(ws, bins=40, color=RENK_MAVI, kde=True, ax=ax_hist)
ax_hist.axvline(ws.mean(), color=RENK_KIRMIZI, linestyle="--", linewidth=1.5, label=f"Ortalama = {ws.mean():,.0f}")
ax_hist.axvline(ws.median(), color=RENK_YESIL, linestyle="--", linewidth=1.5, label=f"Medyan = {ws.median():,.0f}")
ax_hist.set_title("Weekly_Sales Dağılımı — Histogram ve Boxplot")
ax_hist.set_ylabel("Frekans")
ax_hist.legend()

sns.boxplot(x=ws, color=RENK_MAVI, ax=ax_box, fliersize=3)
ax_box.set_xlabel("Haftalık Satış (Weekly_Sales)")

plt.tight_layout()
plt.savefig("outputs/eda_1_dagilim.png", dpi=150)
plt.close()

# --- 2.2 Zaman içinde satış değişimi (tüm mağazaların toplamı) --------------
haftalik_toplam = df.groupby("Date")["Weekly_Sales"].sum().sort_index()

plt.figure(figsize=(11, 5))
plt.plot(haftalik_toplam.index, haftalik_toplam.values, color=RENK_MAVI, linewidth=1.2)
plt.title("Zaman İçinde Toplam Haftalık Satış Değişimi (Tüm Mağazalar)")
plt.xlabel("Tarih")
plt.ylabel("Toplam Haftalık Satış")
plt.tight_layout()
plt.savefig("outputs/eda_2_zaman_serisi.png", dpi=150)
plt.close()

# --- 2.3 Mağaza bazında ortalama satış --------------------------------------
magaza_ortalama = df.groupby("Store")["Weekly_Sales"].mean().sort_values(ascending=False)

plt.figure(figsize=(12, 5))
sns.barplot(x=magaza_ortalama.index.astype(str), y=magaza_ortalama.values,
            color=RENK_MAVI, order=magaza_ortalama.index.astype(str))
plt.title("Mağaza Bazında Ortalama Haftalık Satış")
plt.xlabel("Mağaza No")
plt.ylabel("Ortalama Haftalık Satış")
plt.xticks(rotation=90, fontsize=7)
plt.tight_layout()
plt.savefig("outputs/eda_3_magaza_ortalama.png", dpi=150)
plt.close()

# --- 2.4 Tatil vs. normal hafta dağılım karşılaştırması ---------------------
df["Hafta_Tipi"] = df["Holiday_Flag"].map({0: "Normal Hafta", 1: "Tatil Haftası"})

fig, (ax_v, ax_b) = plt.subplots(1, 2, figsize=(11, 5))
sns.violinplot(data=df, x="Hafta_Tipi", y="Weekly_Sales",
               hue="Hafta_Tipi", palette=[RENK_MAVI, RENK_TURUNCU], legend=False, ax=ax_v)
ax_v.set_title("Dağılım (Violin Plot)")
ax_v.set_xlabel("")
ax_v.set_ylabel("Haftalık Satış")

sns.boxplot(data=df, x="Hafta_Tipi", y="Weekly_Sales",
            hue="Hafta_Tipi", palette=[RENK_MAVI, RENK_TURUNCU], legend=False, ax=ax_b)
ax_b.set_title("Dağılım (Boxplot)")
ax_b.set_xlabel("")
ax_b.set_ylabel("")

plt.suptitle("Tatil Haftası ve Normal Hafta — Satış Dağılımı Karşılaştırması")
plt.tight_layout()
plt.savefig("outputs/eda_4_tatil_karsilastirma.png", dpi=150)
plt.close()

baslik("1. Keşifsel Veri Analizi Bulguları")
yaz(
    f"Weekly_Sales değişkeninin ortalaması **{sayi(ws_ozet['ortalama'])}**, medyanı "
    f"**{sayi(ws_ozet['medyan'])}**, standart sapması **{sayi(ws_ozet['std'])}** olarak "
    f"hesaplanmıştır. Değerler **{sayi(ws_ozet['min'])}** ile **{sayi(ws_ozet['maks'])}** "
    f"arasında değişmektedir. Ortalamanın medyandan yüksek olması, dağılımın sağa çarpık "
    f"olduğuna ve yüksek satış rakamlarına sahip bir grup gözlemin (muhtemelen büyük "
    f"mağazalar veya yoğun tatil dönemleri) ortalamayı yukarı çektiğine işaret etmektedir. "
    f"Bu durum histogram ve boxplot grafiklerinde de gözlemlenmektedir "
    f"(`outputs/eda_1_dagilim.png`).\n\n"
    f"Zaman içindeki satış seyri (`outputs/eda_2_zaman_serisi.png`) belirgin, tekrarlayan "
    f"sıçramalar göstermekte; bu durum ileride Zaman Serisi bölümünde mevsimsellik ve tatil "
    f"etkisi başlıkları altında ayrıntılı incelenmektedir. Mağaza bazlı ortalama satış "
    f"grafiği (`outputs/eda_3_magaza_ortalama.png`) mağazalar arasında belirgin bir "
    f"performans farklılığı olduğunu; tatil/normal hafta karşılaştırması "
    f"(`outputs/eda_4_tatil_karsilastirma.png`) ise tatil haftalarında dağılımın sağa "
    f"kaydığını ön izlenim olarak ortaya koymaktadır (ayrıntılı test Bölüm 3'tedir)."
)

# =========================================================
# 3) KORELASYON ANALİZİ
# =========================================================
print("\n===== 2) KORELASYON ANALİZİ =====")

sayisal_degiskenler = ["Weekly_Sales", "Holiday_Flag", "Temperature", "Fuel_Price", "CPI", "Unemployment"]
korelasyon_matrisi = df[sayisal_degiskenler].corr(method="pearson")
print(korelasyon_matrisi.round(3))

plt.figure(figsize=(8, 6))
sns.heatmap(korelasyon_matrisi, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            vmin=-1, vmax=1, square=True, linewidths=0.5, linecolor="#fcfcfb")
plt.title("Sayısal Değişkenler Arası Pearson Korelasyon Matrisi (Heatmap)")
plt.tight_layout()
plt.savefig("outputs/korelasyon_heatmap.png", dpi=150)
plt.close()

# Weekly_Sales ile diğer değişkenler arasındaki korelasyon + p-değeri tablosu
hedef_degiskenler = ["Holiday_Flag", "Temperature", "Fuel_Price", "CPI", "Unemployment"]
korelasyon_sonuclari = []
for degisken in hedef_degiskenler:
    r, p = stats.pearsonr(df["Weekly_Sales"], df[degisken])
    korelasyon_sonuclari.append({"Değişken": degisken, "r": r, "p_value": p, "n": len(df)})

korelasyon_tablo = pd.DataFrame(korelasyon_sonuclari).sort_values("r", key=lambda s: s.abs(), ascending=False)
print("\nWeekly_Sales ile korelasyonlar (Pearson r, p-value):")
print(korelasyon_tablo.to_string(index=False))
korelasyon_tablo.to_csv("outputs/korelasyon_tablosu.csv", index=False)

baslik("2. Korelasyon Analizi Sonuçları")
yaz("Weekly_Sales ile incelenen değişkenler arasındaki Pearson korelasyon katsayıları:\n")
yaz("| Değişken | r | p-değeri | Yorum |")
yaz("|---|---|---|---|")
for _, row in korelasyon_tablo.iterrows():
    anlamli = "istatistiksel olarak anlamlı" if row["p_value"] < ALPHA else "istatistiksel olarak anlamlı değil"
    yaz(f"| {row['Değişken']} | {row['r']:.3f} | {pfmt(row['p_value'])} | "
        f"{korelasyon_gucu(row['r'])}, {'negatif' if row['r'] < 0 else 'pozitif'} yönlü, {anlamli} |")

en_guclu = korelasyon_tablo.iloc[0]
yaz(
    f"\nİncelenen değişkenler arasında Weekly_Sales ile en güçlü ilişkiyi gösteren değişken "
    f"**{en_guclu['Değişken']}** (r = {en_guclu['r']:.3f}, p {pfmt(en_guclu['p_value'])}) olmuştur. "
    f"Genel olarak Temperature, Fuel_Price, CPI ve Unemployment değişkenlerinin Weekly_Sales ile "
    f"korelasyon katsayıları mutlak değer olarak düşük seviyededir; bu da haftalık satışların "
    f"büyük ölçüde bu tekil ekonomik/çevresel faktörlerin doğrusal bir fonksiyonu olmadığını, "
    f"satış düzeyinin esas olarak mağazaya özgü faktörlerden (ör. mağaza büyüklüğü, konum) "
    f"etkilendiğini düşündürmektedir (bkz. Bölüm 4 ve Bölüm 6).\n\n"
    f"**Önemli not:** Burada hesaplanan korelasyon katsayıları değişkenler arasındaki doğrusal "
    f"ilişkinin yönünü ve gücünü göstermektedir; **korelasyon nedensellik anlamına gelmez**. "
    f"Örneğin CPI veya Unemployment ile Weekly_Sales arasında gözlenen ilişki, aradaki başka "
    f"değişkenlerden (zaman, mağaza büyüklüğü, bölgesel farklılıklar vb.) kaynaklanıyor olabilir."
)

# =========================================================
# 4) TATİL ETKİSİ ANALİZİ
# =========================================================
print("\n===== 3) TATİL ETKİSİ ANALİZİ =====")
print("H0: Tatil haftaları ile normal haftaların ortalama satışları arasında anlamlı fark yoktur.")
print("H1: Tatil haftaları ile normal haftaların ortalama satışları arasında anlamlı fark vardır.")

grup_normal = df.loc[df["Holiday_Flag"] == 0, "Weekly_Sales"]
grup_tatil = df.loc[df["Holiday_Flag"] == 1, "Weekly_Sales"]

tatil_ozet = pd.DataFrame({
    "Normal Hafta": [grup_normal.mean(), grup_normal.median(), grup_normal.std(), len(grup_normal)],
    "Tatil Haftası": [grup_tatil.mean(), grup_tatil.median(), grup_tatil.std(), len(grup_tatil)],
}, index=["Ortalama", "Medyan", "Std. Sapma", "n"])
print(tatil_ozet.round(2))

# Varsayım kontrolleri
# Not: n > 5000 olduğunda Shapiro-Wilk testi güvenilirliğini yitirdiğinden
# (statsmodels/scipy belge önerisi) normallik için D'Agostino-Pearson (normaltest) kullanılmıştır.
_, p_norm_normal = stats.normaltest(grup_normal)
_, p_norm_tatil = stats.normaltest(grup_tatil)
_, p_levene_tatil = stats.levene(grup_normal, grup_tatil)

normal_dagilim_var = (p_norm_normal > ALPHA) and (p_norm_tatil > ALPHA)
varyans_homojen = p_levene_tatil > ALPHA

print(f"\nNormallik testi (D'Agostino-Pearson) — Normal hafta p = {p_norm_normal:.4g}, "
      f"Tatil haftası p = {p_norm_tatil:.4g}")
print(f"Varyans homojenliği (Levene) p = {p_levene_tatil:.4g}")

if normal_dagilim_var and varyans_homojen:
    test_adi = "Bağımsız Örneklem t-Testi (eşit varyans varsayımı ile)"
    t_ist, p_deger = stats.ttest_ind(grup_tatil, grup_normal, equal_var=True)
elif normal_dagilim_var and not varyans_homojen:
    test_adi = "Bağımsız Örneklem t-Testi (Welch düzeltmesi, eşit olmayan varyans)"
    t_ist, p_deger = stats.ttest_ind(grup_tatil, grup_normal, equal_var=False)
else:
    test_adi = "Mann-Whitney U Testi"
    t_ist, p_deger = stats.mannwhitneyu(grup_tatil, grup_normal, alternative="two-sided")

print(f"\nUygulanan test: {test_adi}")
print(f"Test istatistiği = {t_ist:.4f}, p-value = {p_deger:.4g}")

anlamli_fark = p_deger < ALPHA
karar = "H0 reddedilir" if anlamli_fark else "H0 reddedilemez"
print(f"Karar (%95 güven düzeyi): {karar}")

baslik("3. Tatil Etkisi Analizi Sonuçları")
yaz(
    f"Normal haftaların ortalama satışı **{sayi(grup_normal.mean())}** (medyan {sayi(grup_normal.median())}, "
    f"n = {len(grup_normal)}), tatil haftalarının ortalama satışı ise **{sayi(grup_tatil.mean())}** "
    f"(medyan {sayi(grup_tatil.median())}, n = {len(grup_tatil)}) olarak hesaplanmıştır. "
    f"Karşılaştırmalı dağılım grafiği için bkz. `outputs/eda_4_tatil_karsilastirma.png`.\n\n"
    f"**Varsayım kontrolleri:** D'Agostino-Pearson normallik testine göre normal hafta grubu "
    f"p {pfmt(p_norm_normal)}, tatil haftası grubu p {pfmt(p_norm_tatil)} değerini almış; "
    f"Levene testine göre varyans homojenliği p {pfmt(p_levene_tatil)} olarak bulunmuştur. "
    f"{'Her iki grup da normal dağılıma uygundur.' if normal_dagilim_var else 'En az bir grup normal dağılım varsayımını karşılamamaktadır.'} "
    f"Bu nedenle karşılaştırma için **{test_adi}** kullanılmıştır.\n\n"
    f"Test istatistiği = {t_ist:.4f}, p-değeri {pfmt(p_deger)}. %95 güven düzeyinde "
    f"(alpha = {ALPHA}) {karar}; yani tatil haftaları ile normal haftaların ortalama satışları "
    f"arasında istatistiksel olarak {'anlamlı bir fark bulunmaktadır' if anlamli_fark else 'anlamlı bir fark bulunmamaktadır'}. "
    + (
        f"Ortalamalar karşılaştırıldığında tatil haftalarında satışların normal haftalara göre "
        f"%{((grup_tatil.mean() - grup_normal.mean()) / grup_normal.mean() * 100):.2f} "
        f"{'daha yüksek' if grup_tatil.mean() > grup_normal.mean() else 'daha düşük'} olduğu görülmektedir."
        if anlamli_fark else
        "Örneklem farkı gözlense de bu fark istatistiksel olarak şansa bağlı değişkenlikten ayırt edilememektedir."
    )
)

# =========================================================
# 5) MAĞAZA BAZLI ANALİZ
# =========================================================
print("\n===== 4) MAĞAZA BAZLI ANALİZ =====")
print("H0: Tüm mağazaların ortalama haftalık satışları eşittir.")
print("H1: En az bir mağazanın ortalama haftalık satışı diğerlerinden farklıdır.")

magaza_istatistik = df.groupby("Store")["Weekly_Sales"].agg(
    Ortalama="mean", Toplam="sum", Std_Sapma="std"
).sort_values("Ortalama", ascending=False)

en_iyi_magaza = magaza_istatistik.index[0]
en_dusuk_magaza = magaza_istatistik.index[-1]
print(magaza_istatistik.round(2).head())
print("...")
print(f"En yüksek ortalama satış: Mağaza {en_iyi_magaza} ({sayi(magaza_istatistik.iloc[0]['Ortalama'])})")
print(f"En düşük ortalama satış : Mağaza {en_dusuk_magaza} ({sayi(magaza_istatistik.iloc[-1]['Ortalama'])})")

magaza_istatistik.to_csv("outputs/magaza_istatistikleri.csv")

# Sıralı bar grafiği (en iyi ve en düşük mağazalar vurgulanmış)
renkler = [RENK_YESIL if s == en_iyi_magaza else (RENK_KIRMIZI if s == en_dusuk_magaza else RENK_MAVI)
           for s in magaza_istatistik.index]

plt.figure(figsize=(12, 5))
sns.barplot(x=magaza_istatistik.index.astype(str), y=magaza_istatistik["Ortalama"],
            hue=magaza_istatistik.index.astype(str), palette=renkler, legend=False,
            order=magaza_istatistik.index.astype(str))
plt.title("Mağazalara Göre Ortalama Haftalık Satış (Sıralı)")
plt.xlabel("Mağaza No")
plt.ylabel("Ortalama Haftalık Satış")
plt.xticks(rotation=90, fontsize=7)
plt.tight_layout()
plt.savefig("outputs/store_1_siralama.png", dpi=150)
plt.close()

# --- Varsayım kontrolleri: normallik (mağaza başına) ve varyans homojenliği ---
magaza_gruplari = [g["Weekly_Sales"].values for _, g in df.groupby("Store")]

shapiro_p_degerleri = [stats.shapiro(g)[1] for g in magaza_gruplari]
oran_normal_olmayan = np.mean(np.array(shapiro_p_degerleri) < ALPHA)

_, p_levene_magaza = stats.levene(*magaza_gruplari)

print(f"\nShapiro-Wilk (mağaza başına) — normal dağılımı reddeden mağaza oranı: "
      f"%{oran_normal_olmayan * 100:.1f}")
print(f"Levene testi (mağazalar arası varyans homojenliği) p = {p_levene_magaza:.4g}")

anova_varsayimlari_uygun = (oran_normal_olmayan < 0.20) and (p_levene_magaza > ALPHA)

if anova_varsayimlari_uygun:
    magaza_test_adi = "One-Way ANOVA"
    f_ist, p_magaza = stats.f_oneway(*magaza_gruplari)
    print(f"\nUygulanan test: {magaza_test_adi}")
    print(f"F istatistiği = {f_ist:.4f}, p-value = {p_magaza:.4g}")
else:
    magaza_test_adi = "Kruskal-Wallis H Testi"
    f_ist, p_magaza = stats.kruskal(*magaza_gruplari)
    print(f"\nUygulanan test: {magaza_test_adi}")
    print(f"H istatistiği = {f_ist:.4f}, p-value = {p_magaza:.4g}")

magaza_farki_anlamli = p_magaza < ALPHA
magaza_karar = "H0 reddedilir" if magaza_farki_anlamli else "H0 reddedilemez"
print(f"Karar (%95 güven düzeyi): {magaza_karar}")

# --- Post-hoc analiz (sadece ana test anlamlıysa) ---------------------------
posthoc_ozet = ""
if magaza_farki_anlamli:
    magazalar = sorted(df["Store"].unique())
    ikili_kombinasyonlar = list(combinations(magazalar, 2))
    bonferroni_alpha = ALPHA / len(ikili_kombinasyonlar)

    if magaza_test_adi == "One-Way ANOVA":
        tukey_sonuc = pairwise_tukeyhsd(endog=df["Weekly_Sales"], groups=df["Store"], alpha=ALPHA)
        tukey_df = pd.DataFrame(data=tukey_sonuc._results_table.data[1:],
                                 columns=tukey_sonuc._results_table.data[0])
        tukey_df.to_csv("outputs/posthoc_tukey_magazalar.csv", index=False)
        n_anlamli = int(tukey_df["reject"].sum())
        posthoc_ozet = (
            f"Post-hoc analiz olarak **Tukey HSD** testi uygulanmıştır. {len(ikili_kombinasyonlar)} "
            f"ikili karşılaştırmadan **{n_anlamli}** tanesi %95 güven düzeyinde anlamlı bulunmuştur "
            f"(ayrıntılar `outputs/posthoc_tukey_magazalar.csv` dosyasındadır)."
        )
    else:
        sonuclar = []
        for s1, s2 in ikili_kombinasyonlar:
            g1 = df.loc[df["Store"] == s1, "Weekly_Sales"]
            g2 = df.loc[df["Store"] == s2, "Weekly_Sales"]
            u_ist, p_ikili = stats.mannwhitneyu(g1, g2, alternative="two-sided")
            sonuclar.append({"Magaza_1": s1, "Magaza_2": s2, "U": u_ist, "p_value": p_ikili,
                              "anlamli_bonferroni": p_ikili < bonferroni_alpha})
        posthoc_df = pd.DataFrame(sonuclar)
        posthoc_df.to_csv("outputs/posthoc_mannwhitney_magazalar.csv", index=False)
        n_anlamli = int(posthoc_df["anlamli_bonferroni"].sum())
        posthoc_ozet = (
            f"Kruskal-Wallis testi anlamlı çıktığından, çoklu karşılaştırma hatasını kontrol etmek "
            f"amacıyla mağaza çiftleri arasında **Bonferroni düzeltmeli ikili Mann-Whitney U testleri** "
            f"uygulanmıştır (düzeltilmiş alpha = {bonferroni_alpha:.2e}). Toplam "
            f"{len(ikili_kombinasyonlar)} ikili karşılaştırmadan **{n_anlamli}** tanesi anlamlı "
            f"bulunmuştur (ayrıntılar `outputs/posthoc_mannwhitney_magazalar.csv` dosyasındadır). "
            f"45 mağazanın ikili kombinasyon sayısının yüksekliği nedeniyle sonuçlar tablo/dosya "
            f"halinde raporlanmış, tüm çiftler tek tek yorumlanmamıştır."
        )
else:
    posthoc_ozet = "Ana test anlamlı çıkmadığından post-hoc karşılaştırma yapılmamıştır."

baslik("4. Mağaza Bazlı Analiz Sonuçları")
yaz(
    f"Mağaza bazında hesaplanan ortalama, toplam ve standart sapma değerleri "
    f"`outputs/magaza_istatistikleri.csv` dosyasına kaydedilmiştir "
    f"(görselleştirme: `outputs/store_1_siralama.png`). En yüksek ortalama satışa sahip mağaza "
    f"**Mağaza {en_iyi_magaza}** (ortalama {sayi(magaza_istatistik.iloc[0]['Ortalama'])}), en düşük "
    f"ortalama satışa sahip mağaza ise **Mağaza {en_dusuk_magaza}** "
    f"(ortalama {sayi(magaza_istatistik.iloc[-1]['Ortalama'])}) olarak belirlenmiştir. Mağazalar "
    f"arasındaki ortalama satış farkının büyüklüğü ({sayi(magaza_istatistik.iloc[0]['Ortalama'] / magaza_istatistik.iloc[-1]['Ortalama'], 1)} "
    f"kata varan oranlar), satış düzeyinin büyük ölçüde mağazaya özgü sabit etkilerden "
    f"kaynaklandığını göstermektedir.\n\n"
    f"**Varsayım kontrolleri:** Mağaza başına uygulanan Shapiro-Wilk testlerine göre mağazaların "
    f"%{oran_normal_olmayan * 100:.1f} kadarında normal dağılım varsayımı reddedilmiştir; Levene "
    f"testine göre mağazalar arası varyans homojenliği p {pfmt(p_levene_magaza)} olarak bulunmuştur. "
    f"Bu nedenle karşılaştırma için **{magaza_test_adi}** kullanılmıştır.\n\n"
    f"Test istatistiği = {f_ist:.4f}, p-değeri {pfmt(p_magaza)}. %95 güven düzeyinde "
    f"{magaza_karar}; yani mağazalar arasında ortalama haftalık satışlar açısından istatistiksel "
    f"olarak {'anlamlı bir fark bulunmaktadır' if magaza_farki_anlamli else 'anlamlı bir fark bulunmamaktadır'}. "
    f"{posthoc_ozet}"
)

# =========================================================
# 6) ZAMAN SERİSİ VE TREND ANALİZİ
# =========================================================
print("\n===== 5) ZAMAN SERİSİ VE TREND ANALİZİ =====")

# 6.1 Genel trend + 4 haftalık hareketli ortalama + tatil haftaları işaretlenmiş
haftalik_toplam = df.groupby("Date")["Weekly_Sales"].sum().sort_index()
hareketli_ortalama = haftalik_toplam.rolling(window=4, center=True).mean()
tatil_tarihleri = sorted(df.loc[df["Holiday_Flag"] == 1, "Date"].unique())

plt.figure(figsize=(12, 5.5))
plt.plot(haftalik_toplam.index, haftalik_toplam.values, color=RENK_MAVI, linewidth=1,
         alpha=0.6, label="Haftalık Toplam Satış")
plt.plot(hareketli_ortalama.index, hareketli_ortalama.values, color=RENK_MOR, linewidth=2.2,
         label="4 Haftalık Hareketli Ortalama")
for i, tarih in enumerate(tatil_tarihleri):
    plt.axvline(tarih, color=RENK_TURUNCU, linestyle=":", linewidth=1,
                label="Tatil Haftası" if i == 0 else None)
plt.title("Zaman İçinde Toplam Satış Trendi, Hareketli Ortalama ve Tatil Haftaları")
plt.xlabel("Tarih")
plt.ylabel("Toplam Haftalık Satış")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/zamanserisi_1_trend_hareketli_ortalama.png", dpi=150)
plt.close()

# 6.2 Aylık (takvim ayı) mevsimsellik — yıllardan bağımsız ortalama
aylik_mevsimsellik = df.groupby("Month")["Weekly_Sales"].mean()

plt.figure(figsize=(9, 5))
eksen = sns.barplot(x=[AY_ADLARI[m - 1] for m in aylik_mevsimsellik.index],
                     y=aylik_mevsimsellik.values, color=RENK_MAVI)
en_yogun_ay_no = aylik_mevsimsellik.idxmax()
eksen.patches[list(aylik_mevsimsellik.index).index(en_yogun_ay_no)].set_facecolor(RENK_TURUNCU)
plt.title("Takvim Ayına Göre Ortalama Haftalık Satış (Mevsimsellik)")
plt.xlabel("Ay")
plt.ylabel("Ortalama Haftalık Satış")
plt.tight_layout()
plt.savefig("outputs/zamanserisi_2_aylik_mevsimsellik.png", dpi=150)
plt.close()

tatil_haftalarinda_ortalama = df.loc[df["Holiday_Flag"] == 1, "Weekly_Sales"].mean()
normal_haftalarda_ortalama = df.loc[df["Holiday_Flag"] == 0, "Weekly_Sales"].mean()

baslik("5. Zaman Serisi Analizi Sonuçları")
yaz(
    f"Toplam haftalık satışın zaman içindeki seyri, 4 haftalık hareketli ortalama ve tatil "
    f"haftalarının konumu `outputs/zamanserisi_1_trend_hareketli_ortalama.png` grafiğinde "
    f"birlikte gösterilmiştir. Hareketli ortalama çizgisi, ham seride görülen haftalık "
    f"dalgalanmayı yumuşatarak temeldeki trendi ortaya koymaktadır; grafikte tatil haftalarının "
    f"(dikey çizgiler) sıklıkla yerel satış tepe noktalarıyla çakıştığı gözlenmektedir.\n\n"
    f"Takvim ayına göre hesaplanan ortalama satışlar (`outputs/zamanserisi_2_aylik_mevsimsellik.png`), "
    f"yıldan bağımsız olarak belirgin bir mevsimsellik olduğunu göstermektedir. En yüksek ortalama "
    f"satışın gözlendiği ay **{AY_ADLARI[en_yogun_ay_no - 1]}** ayıdır (ortalama "
    f"{sayi(aylik_mevsimsellik.max())}); bu durum yılsonu/tatil dönemi alışverişleriyle tutarlıdır.\n\n"
    f"Tatil haftalarının zaman serisi üzerindeki etkisi doğrudan karşılaştırıldığında, tatil "
    f"haftalarının ortalama satışı ({sayi(tatil_haftalarinda_ortalama)}) normal haftaların "
    f"ortalama satışından ({sayi(normal_haftalarda_ortalama)}) yüksektir; bu gözlem Bölüm 3'te "
    f"istatistiksel olarak da test edilmiştir."
)

# =========================================================
# 7) ÇOKLU DOĞRUSAL REGRESYON
# =========================================================
print("\n===== 6) ÇOKLU DOĞRUSAL REGRESYON =====")

# --- Model 1: Temel model (ekonomik/çevresel değişkenler, mağaza etkisi yok) ---
formula_model1 = "Weekly_Sales ~ Holiday_Flag + Temperature + Fuel_Price + CPI + Unemployment"
model1 = smf.ols(formula_model1, data=df).fit()
print("\n--- MODEL 1: Temel model (Store hariç) ---")
print(model1.summary())

# --- Model 2: Mağaza sabit etkileri dahil (Store kategorik / dummy encoding) ---
# Not: Store, mağazaya özgü sabit farklılıkları (büyüklük, konum vb.) yakalamak için
# C(Store) ile kategorik değişken (dummy encoding) olarak modele dahil edilmiştir.
formula_model2 = "Weekly_Sales ~ Holiday_Flag + Temperature + Fuel_Price + CPI + Unemployment + C(Store)"
model2 = smf.ols(formula_model2, data=df).fit()
print("\n--- MODEL 2: Store sabit etkili model ---")
print(model2.summary())

print(f"\nModel 1 -> R2 = {model1.rsquared:.4f}, Adj. R2 = {model1.rsquared_adj:.4f}")
print(f"Model 2 -> R2 = {model2.rsquared:.4f}, Adj. R2 = {model2.rsquared_adj:.4f}")

# Nihai model olarak Adjusted R2 değeri belirgin biçimde daha yüksek olan Model 2 seçilmiştir.
nihai_model = model2 if model2.rsquared_adj > model1.rsquared_adj else model1
nihai_model_adi = "Model 2 (Store sabit etkili)" if nihai_model is model2 else "Model 1 (Temel model)"

# --- Ana açıklayıcı değişkenlerin anlamlılığı (nihai modelden) ---
ana_degiskenler = ["Holiday_Flag", "Temperature", "Fuel_Price", "CPI", "Unemployment"]
katsayi_tablo = pd.DataFrame({
    "Değişken": ana_degiskenler,
    "Katsayı": [nihai_model.params[d] for d in ana_degiskenler],
    "p_value": [nihai_model.pvalues[d] for d in ana_degiskenler],
})
katsayi_tablo["Anlamli_mi"] = katsayi_tablo["p_value"] < ALPHA
print("\nAna değişkenlerin katsayıları (nihai model):")
print(katsayi_tablo.to_string(index=False))
katsayi_tablo.to_csv("outputs/regresyon_katsayilar.csv", index=False)

# --- VIF (çoklu doğrusal bağlantı) — sadece sürekli/ana açıklayıcı değişkenler üzerinden ---
# Not: Store, 45 seviyeli bir kategorik değişken olduğundan dummy'leri VIF matrisine dahil
# etmek yorumlanabilirliği düşürür; VIF bu nedenle temel açıklayıcı değişkenler üzerinden
# hesaplanmıştır (yaygın uygulama).
X_vif = sm.add_constant(df[ana_degiskenler])
vif_tablo = pd.DataFrame({
    "Değişken": X_vif.columns,
    "VIF": [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])],
})
vif_tablo = vif_tablo[vif_tablo["Değişken"] != "const"].reset_index(drop=True)
print("\nVIF (Varyans Şişirme Faktörü) tablosu:")
print(vif_tablo.to_string(index=False))
vif_tablo.to_csv("outputs/regresyon_vif.csv", index=False)

coklu_baglanti_var = (vif_tablo["VIF"] > 5).any()

# --- Artık (residual) diyagnostikleri (nihai modelden) ---
artiklar = nihai_model.resid
tahminler = nihai_model.fittedvalues

fig, eksenler = plt.subplots(2, 2, figsize=(11, 9))

# Residual vs Fitted
eksenler[0, 0].scatter(tahminler, artiklar, s=8, alpha=0.4, color=RENK_MAVI)
eksenler[0, 0].axhline(0, color=RENK_KIRMIZI, linestyle="--", linewidth=1)
eksenler[0, 0].set_title("Artıklar vs. Tahmin Değerleri")
eksenler[0, 0].set_xlabel("Tahmin Edilen Weekly_Sales")
eksenler[0, 0].set_ylabel("Artık (Residual)")

# QQ Plot
sm.qqplot(artiklar, line="45", fit=True, ax=eksenler[0, 1], markerfacecolor=RENK_MAVI,
          markeredgecolor=RENK_MAVI, alpha=0.4, markersize=4)
eksenler[0, 1].set_title("Artıkların Normal Q-Q Grafiği")

# Histogram
sns.histplot(artiklar, bins=40, kde=True, color=RENK_MAVI, ax=eksenler[1, 0])
eksenler[1, 0].set_title("Artıkların Dağılımı (Histogram)")
eksenler[1, 0].set_xlabel("Artık (Residual)")

# Scale-Location (heteroskedastisite görünümü)
eksenler[1, 1].scatter(tahminler, np.sqrt(np.abs(artiklar)), s=8, alpha=0.4, color=RENK_MOR)
eksenler[1, 1].set_title("Scale-Location (Heteroskedastisite Kontrolü)")
eksenler[1, 1].set_xlabel("Tahmin Edilen Weekly_Sales")
eksenler[1, 1].set_ylabel("sqrt(|Artık|)")

plt.suptitle(f"Regresyon Varsayım Diyagnostikleri — {nihai_model_adi}")
plt.tight_layout()
plt.savefig("outputs/regresyon_diagnostik.png", dpi=150)
plt.close()

# Artıkların normalliği (n > 5000 -> D'Agostino-Pearson)
_, p_artik_normal = stats.normaltest(artiklar)

# Heteroskedastisite: Breusch-Pagan testi
bp_stat, bp_pvalue, _, _ = het_breuschpagan(artiklar, nihai_model.model.exog)
heteroskedastisite_var = bp_pvalue < ALPHA

print(f"\nArtıkların normalliği (D'Agostino-Pearson) p = {p_artik_normal:.4g}")
print(f"Breusch-Pagan heteroskedastisite testi: LM p = {bp_pvalue:.4g}")

baslik("6. Regresyon Analizi Sonuçları")
yaz(
    f"Weekly_Sales'i açıklamak üzere iki model kurulmuştur: **Model 1**, yalnızca Holiday_Flag, "
    f"Temperature, Fuel_Price, CPI ve Unemployment değişkenlerini içeren temel modeldir "
    f"(R² = {model1.rsquared:.4f}, Düzeltilmiş R² = {model1.rsquared_adj:.4f}). **Model 2**, "
    f"aynı değişkenlere ek olarak Store değişkenini kategorik (dummy encoding, C(Store)) olarak "
    f"içermektedir (R² = {model2.rsquared:.4f}, Düzeltilmiş R² = {model2.rsquared_adj:.4f}). "
    f"Store sabit etkilerinin eklenmesiyle açıklanan varyansta büyük bir artış gözlenmiş olması, "
    f"mağazaya özgü sabit farklılıkların (büyüklük, konum, müşteri profili vb.) satışların en "
    f"güçlü belirleyicisi olduğunu; ekonomik/çevresel değişkenlerin ise satış üzerinde göreli "
    f"olarak sınırlı bir doğrusal etkiye sahip olduğunu göstermektedir. Bu nedenle yorumlar "
    f"**{nihai_model_adi}** temel alınarak yapılmıştır.\n\n"
    f"**Katsayılar ve anlamlılık (ana açıklayıcı değişkenler):**\n\n"
    f"| Değişken | Katsayı | p-değeri | Anlamlı mı? (α={ALPHA}) |\n|---|---|---|---|\n"
)
for _, row in katsayi_tablo.iterrows():
    yaz(f"| {row['Değişken']} | {row['Katsayı']:.4f} | {pfmt(row['p_value'])} | "
        f"{'Evet' if row['Anlamli_mi'] else 'Hayır'} |")

anlamli_degiskenler = katsayi_tablo.loc[katsayi_tablo["Anlamli_mi"], "Değişken"].tolist()
anlamsiz_degiskenler = katsayi_tablo.loc[~katsayi_tablo["Anlamli_mi"], "Değişken"].tolist()
yaz(
    f"\n%95 güven düzeyinde istatistiksel olarak anlamlı bulunan değişkenler: "
    f"{', '.join(anlamli_degiskenler) if anlamli_degiskenler else 'yoktur'}. "
    f"Anlamlı bulunmayan değişkenler: {', '.join(anlamsiz_degiskenler) if anlamsiz_degiskenler else 'yoktur'}.\n\n"
    f"**Varsayım kontrolleri:**\n"
    f"- *Artıkların normalliği:* D'Agostino-Pearson testi p {pfmt(p_artik_normal)}; "
    f"{'normallik varsayımı karşılanmaktadır' if p_artik_normal > ALPHA else 'artıklar normal dağılımdan sapma göstermektedir'} "
    f"(bkz. `outputs/regresyon_diagnostik.png` — Q-Q grafiği ve histogram).\n"
    f"- *Heteroskedastisite:* Breusch-Pagan testi LM p {pfmt(bp_pvalue)}; "
    f"{'artıkların varyansı sabit görünmemektedir (heteroskedastisite mevcuttur)' if heteroskedastisite_var else 'sabit varyans (homoskedastisite) varsayımı reddedilememiştir'}.\n"
    f"- *Çoklu doğrusal bağlantı (VIF):* " +
    ", ".join(f"{r['Değişken']} = {r['VIF']:.2f}" for _, r in vif_tablo.iterrows()) + ". " +
    ("VIF değerlerinden en az biri 5'in üzerinde olduğundan değişkenler arasında dikkate değer "
     "çoklu doğrusal bağlantı riski bulunmaktadır." if coklu_baglanti_var else
     "Tüm VIF değerleri 5'in altında olup değişkenler arasında sorunlu bir çoklu doğrusal "
     "bağlantı gözlenmemiştir.") +
    "\n\n"
    f"**Genel değerlendirme:** Model açıklanan varyans (Adjusted R² = {nihai_model.rsquared_adj:.4f}) "
    f"açısından " +
    ("yüksek bir açıklama gücüne sahiptir" if nihai_model.rsquared_adj > 0.7 else
     "orta düzeyde bir açıklama gücüne sahiptir" if nihai_model.rsquared_adj > 0.3 else
     "sınırlı bir açıklama gücüne sahiptir") +
    ". " +
    ("Ancak tespit edilen heteroskedastisite nedeniyle katsayıların standart hatalarının ve "
     "dolayısıyla p-değerlerinin temkinli yorumlanması gerekir; ileri analizlerde sağlam "
     "(robust/HC3) standart hatalar veya değişken dönüşümleri (ör. log(Weekly_Sales)) "
     "değerlendirilebilir." if heteroskedastisite_var else
     "Varsayım kontrollerinde ciddi bir ihlal gözlenmemiştir.")
)

# =========================================================
# 8) SONUÇ RAPORU — analysis_report.md dosyasına yaz
# =========================================================
baslik("7. Genel Sonuç ve Öneriler")
yaz(
    "Bu çalışmada Walmart'a ait haftalık satış verileri; keşifsel veri analizi, korelasyon "
    "analizi, tatil etkisi testi, mağaza bazlı karşılaştırma, zaman serisi incelemesi ve çoklu "
    "doğrusal regresyon yöntemleriyle incelenmiştir. Bulgular özetle şunu göstermektedir:\n\n"
    f"1. Haftalık satışların dağılımı sağa çarpıktır ve mağazadan mağazaya büyük farklılıklar "
    f"göstermektedir (Bölüm 1, Bölüm 4).\n"
    f"2. Weekly_Sales ile Temperature, Fuel_Price, CPI ve Unemployment arasındaki doğrusal "
    f"korelasyonlar genel olarak zayıf düzeydedir (Bölüm 2); bu ilişkiler nedensel olarak "
    f"yorumlanmamalıdır.\n"
    f"3. Tatil haftaları ile normal haftalar arasındaki satış farkı istatistiksel olarak "
    f"{'anlamlıdır' if anlamli_fark else 'anlamlı bulunmamıştır'} ({test_adi}, p {pfmt(p_deger)}) (Bölüm 3).\n"
    f"4. Mağazalar arasında ortalama satış açısından istatistiksel olarak "
    f"{'anlamlı farklar bulunmaktadır' if magaza_farki_anlamli else 'anlamlı fark bulunmamaktadır'} "
    f"({magaza_test_adi}, p {pfmt(p_magaza)}) (Bölüm 4).\n"
    f"5. Zaman serisinde belirgin bir mevsimsel örüntü ve tatil dönemleriyle örtüşen satış "
    f"artışları gözlenmektedir (Bölüm 5).\n"
    f"6. Çoklu doğrusal regresyon modelinde mağaza sabit etkileri eklendiğinde açıklanan varyans "
    f"belirgin biçimde artmakta; bu da satış düzeyinin öncelikli belirleyicisinin mağazaya özgü "
    f"yapısal faktörler olduğuna, ekonomik/çevresel değişkenlerin ise ikincil ve sınırlı bir rol "
    f"oynadığına işaret etmektedir (Bölüm 6).\n\n"
    "**Öneriler:** (a) Mağaza performansındaki farkların kaynağını daha iyi anlamak için mağaza "
    "büyüklüğü, bölge ve demografik veriler modele eklenebilir; (b) Weekly_Sales değişkeninin "
    "sağa çarpık dağılımı nedeniyle log dönüşümü ile regresyon tekrarlanabilir; (c) Tespit edilen "
    "heteroskedastisite göz önüne alınarak sağlam (robust) standart hatalar kullanılabilir; "
    "(d) Zaman serisindeki mevsimsel örüntüler dikkate alınarak ARIMA/SARIMA gibi zaman serisi "
    "modelleriyle ileriye dönük satış tahmini yapılabilir.\n\n"
    "**Genel uyarı:** Bu raporda sunulan tüm ilişkiler gözlemsel veri üzerinden hesaplanmış "
    "korelasyon ve regresyon sonuçlarıdır; nedensellik iddiası taşımamaktadır."
)

with open("analysis_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(rapor))

print("\n\nTüm analizler tamamlandı.")
print("Grafikler 'outputs/' klasörüne, tablolar CSV olarak 'outputs/' klasörüne kaydedildi.")
print("Kapsamlı sonuç raporu 'analysis_report.md' olarak oluşturuldu.")
