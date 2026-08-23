# projeler
### 📂 Projeler ve Yetkinlikler

* **1. Perakende Satış Analitiği & İstatistiksel Modelleme (`ANALİZ MARKET/`):**
Veri: 45 mağazaya ait 6.435 satırlık haftalık satış verisi.
Python / EDA: Pandas, Matplotlib, Seaborn, SciPy ve Statsmodels ile keşifsel veri analizi, çoklu regresyon, VIF analizi, hareketli ortalamalar ve hipotez testleri.
Raporlama: Bulguların dokümante edildiği detaylı analiz raporu (analysis_report.md).

* **2. Power BI Dashboard & DAX Modelleme (`walmart.pbix`):**
Veri Kaynağı: Walmart haftalık satış verisi (6.435 satır, 45 mağaza, 2010-2012)
Power BI: Power Query ile veri temizleme (yerel/ondalık ayracı hatasının kök nedenini bulup düzeltme, tarih tipleme), hesaplanan sütunlar (Year, Month, Quarter, Holiday Category), DAX ölçüleri (CALCULATE, DIVIDE, SWITCH; DATEADD'in tarih-tipi kısıtı nedeniyle çalışmadığı bir durumda MAX() tabanlı özel bir zaman karşılaştırma mantığıyla Sales Growth % ölçüsü), 3 sayfalık interaktif dashboard (KPI kartları, zaman trendi, Top/Bottom 10 mağaza karşılaştırması, tatil vs normal dönem satış karşılaştırması, slicer'lar)
Odak: Mağaza performans karşılaştırması ve tatil döneminin satışa etkisinin analizi

* **3. AdventureWorks Kurumsal Satış & Müşteri Analizi (`SQLQuery_advventureworks.sql`):**
Veritabanı: Microsoft AdventureWorks 
T-SQL: Çoklu Tablo Birleştirmeleri (JOIN), Ortak Tablo İfadeleri (CTE), Pencere Fonksiyonları (DENSE_RANK, ROW_NUMBER, SUM() OVER) ve raporlama için VIEW yapıları
Odak: Müşteri segmentasyonu, ürün kârlılığı ve bölgesel satış kırılımları
