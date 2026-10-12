
# Walmart Haftalık Satış Analizi — Sonuç Raporu

Veri seti **6435** satır ve **10** sütundan oluşmaktadır. Gözlemler **45** farklı mağazaya ve **2010-02-05 – 2012-10-26** tarih aralığına aittir. Tüm testlerde anlamlılık düzeyi **alpha = 0.05** olarak alınmıştır.

## 1. Keşifsel Veri Analizi Bulguları

Weekly_Sales değişkeninin ortalaması **1,046,964.88**, medyanı **960,746.04**, standart sapması **564,366.62** olarak hesaplanmıştır. Değerler **209,986.25** ile **3,818,686.45** arasında değişmektedir. Ortalamanın medyandan yüksek olması, dağılımın sağa çarpık olduğuna ve yüksek satış rakamlarına sahip bir grup gözlemin (muhtemelen büyük mağazalar veya yoğun tatil dönemleri) ortalamayı yukarı çektiğine işaret etmektedir. Bu durum histogram ve boxplot grafiklerinde de gözlemlenmektedir (`outputs/eda_1_dagilim.png`).

Zaman içindeki satış seyri (`outputs/eda_2_zaman_serisi.png`) belirgin, tekrarlayan sıçramalar göstermekte; bu durum ileride Zaman Serisi bölümünde mevsimsellik ve tatil etkisi başlıkları altında ayrıntılı incelenmektedir. Mağaza bazlı ortalama satış grafiği (`outputs/eda_3_magaza_ortalama.png`) mağazalar arasında belirgin bir performans farklılığı olduğunu; tatil/normal hafta karşılaştırması (`outputs/eda_4_tatil_karsilastirma.png`) ise tatil haftalarında dağılımın sağa kaydığını ön izlenim olarak ortaya koymaktadır (ayrıntılı test Bölüm 3'tedir).

## 2. Korelasyon Analizi Sonuçları

Weekly_Sales ile incelenen değişkenler arasındaki Pearson korelasyon katsayıları:

| Değişken | r | p-değeri | Yorum |
|---|---|---|---|
| Unemployment | -0.106 | < 0.001 | zayıf düzeyde, negatif yönlü, istatistiksel olarak anlamlı |
| CPI | -0.073 | < 0.001 | ihmal edilebilir düzeyde, negatif yönlü, istatistiksel olarak anlamlı |
| Temperature | -0.064 | < 0.001 | ihmal edilebilir düzeyde, negatif yönlü, istatistiksel olarak anlamlı |
| Holiday_Flag | 0.037 | 0.0031 | ihmal edilebilir düzeyde, pozitif yönlü, istatistiksel olarak anlamlı |
| Fuel_Price | 0.009 | 0.4478 | ihmal edilebilir düzeyde, pozitif yönlü, istatistiksel olarak anlamlı değil |

İncelenen değişkenler arasında Weekly_Sales ile en güçlü ilişkiyi gösteren değişken **Unemployment** (r = -0.106, p < 0.001) olmuştur. Genel olarak Temperature, Fuel_Price, CPI ve Unemployment değişkenlerinin Weekly_Sales ile korelasyon katsayıları mutlak değer olarak düşük seviyededir; bu da haftalık satışların büyük ölçüde bu tekil ekonomik/çevresel faktörlerin doğrusal bir fonksiyonu olmadığını, satış düzeyinin esas olarak mağazaya özgü faktörlerden (ör. mağaza büyüklüğü, konum) etkilendiğini düşündürmektedir (bkz. Bölüm 4 ve Bölüm 6).

**Önemli not:** Burada hesaplanan korelasyon katsayıları değişkenler arasındaki doğrusal ilişkinin yönünü ve gücünü göstermektedir; **korelasyon nedensellik anlamına gelmez**. Örneğin CPI veya Unemployment ile Weekly_Sales arasında gözlenen ilişki, aradaki başka değişkenlerden (zaman, mağaza büyüklüğü, bölgesel farklılıklar vb.) kaynaklanıyor olabilir.

## 3. Tatil Etkisi Analizi Sonuçları

Normal haftaların ortalama satışı **1,041,256.38** (medyan 956,211.20, n = 5985), tatil haftalarının ortalama satışı ise **1,122,887.89** (medyan 1,018,538.04, n = 450) olarak hesaplanmıştır. Karşılaştırmalı dağılım grafiği için bkz. `outputs/eda_4_tatil_karsilastirma.png`.

**Varsayım kontrolleri:** D'Agostino-Pearson normallik testine göre normal hafta grubu p < 0.001, tatil haftası grubu p < 0.001 değerini almış; Levene testine göre varyans homojenliği p 0.0012 olarak bulunmuştur. En az bir grup normal dağılım varsayımını karşılamamaktadır. Bu nedenle karşılaştırma için **Mann-Whitney U Testi** kullanılmıştır.

Test istatistiği = 1431297.0000, p-değeri 0.0259. %95 güven düzeyinde (alpha = 0.05) H0 reddedilir; yani tatil haftaları ile normal haftaların ortalama satışları arasında istatistiksel olarak anlamlı bir fark bulunmaktadır. Ortalamalar karşılaştırıldığında tatil haftalarında satışların normal haftalara göre %7.84 daha yüksek olduğu görülmektedir.

## 4. Mağaza Bazlı Analiz Sonuçları

Mağaza bazında hesaplanan ortalama, toplam ve standart sapma değerleri `outputs/magaza_istatistikleri.csv` dosyasına kaydedilmiştir (görselleştirme: `outputs/store_1_siralama.png`). En yüksek ortalama satışa sahip mağaza **Mağaza 20** (ortalama 2,107,676.87), en düşük ortalama satışa sahip mağaza ise **Mağaza 33** (ortalama 259,861.69) olarak belirlenmiştir. Mağazalar arasındaki ortalama satış farkının büyüklüğü (8.1 kata varan oranlar), satış düzeyinin büyük ölçüde mağazaya özgü sabit etkilerden kaynaklandığını göstermektedir.

**Varsayım kontrolleri:** Mağaza başına uygulanan Shapiro-Wilk testlerine göre mağazaların %95.6 kadarında normal dağılım varsayımı reddedilmiştir; Levene testine göre mağazalar arası varyans homojenliği p < 0.001 olarak bulunmuştur. Bu nedenle karşılaştırma için **Kruskal-Wallis H Testi** kullanılmıştır.

Test istatistiği = 6144.3229, p-değeri < 0.001. %95 güven düzeyinde H0 reddedilir; yani mağazalar arasında ortalama haftalık satışlar açısından istatistiksel olarak anlamlı bir fark bulunmaktadır. Kruskal-Wallis testi anlamlı çıktığından, çoklu karşılaştırma hatasını kontrol etmek amacıyla mağaza çiftleri arasında **Bonferroni düzeltmeli ikili Mann-Whitney U testleri** uygulanmıştır (düzeltilmiş alpha = 5.05e-05). Toplam 990 ikili karşılaştırmadan **946** tanesi anlamlı bulunmuştur (ayrıntılar `outputs/posthoc_mannwhitney_magazalar.csv` dosyasındadır). 45 mağazanın ikili kombinasyon sayısının yüksekliği nedeniyle sonuçlar tablo/dosya halinde raporlanmış, tüm çiftler tek tek yorumlanmamıştır.

## 5. Zaman Serisi Analizi Sonuçları

Toplam haftalık satışın zaman içindeki seyri, 4 haftalık hareketli ortalama ve tatil haftalarının konumu `outputs/zamanserisi_1_trend_hareketli_ortalama.png` grafiğinde birlikte gösterilmiştir. Hareketli ortalama çizgisi, ham seride görülen haftalık dalgalanmayı yumuşatarak temeldeki trendi ortaya koymaktadır; grafikte tatil haftalarının (dikey çizgiler) sıklıkla yerel satış tepe noktalarıyla çakıştığı gözlenmektedir.

Takvim ayına göre hesaplanan ortalama satışlar (`outputs/zamanserisi_2_aylik_mevsimsellik.png`), yıldan bağımsız olarak belirgin bir mevsimsellik olduğunu göstermektedir. En yüksek ortalama satışın gözlendiği ay **Ara** ayıdır (ortalama 1,281,863.63); bu durum yılsonu/tatil dönemi alışverişleriyle tutarlıdır.

Tatil haftalarının zaman serisi üzerindeki etkisi doğrudan karşılaştırıldığında, tatil haftalarının ortalama satışı (1,122,887.89) normal haftaların ortalama satışından (1,041,256.38) yüksektir; bu gözlem Bölüm 3'te istatistiksel olarak da test edilmiştir.

## 6. Regresyon Analizi Sonuçları

Weekly_Sales'i açıklamak üzere iki model kurulmuştur: **Model 1**, yalnızca Holiday_Flag, Temperature, Fuel_Price, CPI ve Unemployment değişkenlerini içeren temel modeldir (R² = 0.0254, Düzeltilmiş R² = 0.0247). **Model 2**, aynı değişkenlere ek olarak Store değişkenini kategorik (dummy encoding, C(Store)) olarak içermektedir (R² = 0.9201, Düzeltilmiş R² = 0.9195). Store sabit etkilerinin eklenmesiyle açıklanan varyansta büyük bir artış gözlenmiş olması, mağazaya özgü sabit farklılıkların (büyüklük, konum, müşteri profili vb.) satışların en güçlü belirleyicisi olduğunu; ekonomik/çevresel değişkenlerin ise satış üzerinde göreli olarak sınırlı bir doğrusal etkiye sahip olduğunu göstermektedir. Bu nedenle yorumlar **Model 2 (Store sabit etkili)** temel alınarak yapılmıştır.

**Katsayılar ve anlamlılık (ana açıklayıcı değişkenler):**

| Değişken | Katsayı | p-değeri | Anlamlı mı? (α=0.05) |
|---|---|---|---|

| Holiday_Flag | 69239.2840 | < 0.001 | Evet |
| Temperature | -833.7115 | < 0.001 | Evet |
| Fuel_Price | -41354.1511 | < 0.001 | Evet |
| CPI | 2933.3510 | 0.0045 | Evet |
| Unemployment | -22467.0113 | < 0.001 | Evet |

%95 güven düzeyinde istatistiksel olarak anlamlı bulunan değişkenler: Holiday_Flag, Temperature, Fuel_Price, CPI, Unemployment. Anlamlı bulunmayan değişkenler: yoktur.

**Varsayım kontrolleri:**
- *Artıkların normalliği:* D'Agostino-Pearson testi p < 0.001; artıklar normal dağılımdan sapma göstermektedir (bkz. `outputs/regresyon_diagnostik.png` — Q-Q grafiği ve histogram).
- *Heteroskedastisite:* Breusch-Pagan testi LM p < 0.001; artıkların varyansı sabit görünmemektedir (heteroskedastisite mevcuttur).
- *Çoklu doğrusal bağlantı (VIF):* Holiday_Flag = 1.03, Temperature = 1.13, Fuel_Price = 1.08, CPI = 1.22, Unemployment = 1.15. Tüm VIF değerleri 5'in altında olup değişkenler arasında sorunlu bir çoklu doğrusal bağlantı gözlenmemiştir.

**Genel değerlendirme:** Model açıklanan varyans (Adjusted R² = 0.9195) açısından yüksek bir açıklama gücüne sahiptir. Ancak tespit edilen heteroskedastisite nedeniyle katsayıların standart hatalarının ve dolayısıyla p-değerlerinin temkinli yorumlanması gerekir; ileri analizlerde sağlam (robust/HC3) standart hatalar veya değişken dönüşümleri (ör. log(Weekly_Sales)) değerlendirilebilir.

## 7. Genel Sonuç ve Öneriler

Bu çalışmada Walmart'a ait haftalık satış verileri; keşifsel veri analizi, korelasyon analizi, tatil etkisi testi, mağaza bazlı karşılaştırma, zaman serisi incelemesi ve çoklu doğrusal regresyon yöntemleriyle incelenmiştir. Bulgular özetle şunu göstermektedir:

1. Haftalık satışların dağılımı sağa çarpıktır ve mağazadan mağazaya büyük farklılıklar göstermektedir (Bölüm 1, Bölüm 4).
2. Weekly_Sales ile Temperature, Fuel_Price, CPI ve Unemployment arasındaki doğrusal korelasyonlar genel olarak zayıf düzeydedir (Bölüm 2); bu ilişkiler nedensel olarak yorumlanmamalıdır.
3. Tatil haftaları ile normal haftalar arasındaki satış farkı istatistiksel olarak anlamlıdır (Mann-Whitney U Testi, p 0.0259) (Bölüm 3).
4. Mağazalar arasında ortalama satış açısından istatistiksel olarak anlamlı farklar bulunmaktadır (Kruskal-Wallis H Testi, p < 0.001) (Bölüm 4).
5. Zaman serisinde belirgin bir mevsimsel örüntü ve tatil dönemleriyle örtüşen satış artışları gözlenmektedir (Bölüm 5).
6. Çoklu doğrusal regresyon modelinde mağaza sabit etkileri eklendiğinde açıklanan varyans belirgin biçimde artmakta; bu da satış düzeyinin öncelikli belirleyicisinin mağazaya özgü yapısal faktörler olduğuna, ekonomik/çevresel değişkenlerin ise ikincil ve sınırlı bir rol oynadığına işaret etmektedir (Bölüm 6).

**Öneriler:** (a) Mağaza performansındaki farkların kaynağını daha iyi anlamak için mağaza büyüklüğü, bölge ve demografik veriler modele eklenebilir; (b) Weekly_Sales değişkeninin sağa çarpık dağılımı nedeniyle log dönüşümü ile regresyon tekrarlanabilir; (c) Tespit edilen heteroskedastisite göz önüne alınarak sağlam (robust) standart hatalar kullanılabilir; (d) Zaman serisindeki mevsimsel örüntüler dikkate alınarak ARIMA/SARIMA gibi zaman serisi modelleriyle ileriye dönük satış tahmini yapılabilir.

**Genel uyarı:** Bu raporda sunulan tüm ilişkiler gözlemsel veri üzerinden hesaplanmış korelasyon ve regresyon sonuçlarıdır; nedensellik iddiası taşımamaktadır.