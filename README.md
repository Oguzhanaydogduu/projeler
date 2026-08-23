# projeler
### 📂 Projeler ve Yetkinlikler

#### 1. Perakende Satış Analitiği & İstatistiksel Modelleme (`ANALİZ MARKET/`)
* **Veri Kaynağı:** 45 mağazaya ait 6.435 satırlık haftalık satış verisi (`Walmart_Sales.csv`).
* **Python / EDA:** `Pandas`, `Matplotlib`, `Seaborn`, `SciPy` ve `Statsmodels` ile keşifsel veri analizi, çoklu regresyon, VIF analizi, hareketli ortalamalar ve hipotez testleri.
* **Raporlama:** Bulguların ve çıkarımların dokümante edildiği detaylı akademik özet rapor (`analysis_report.md`).

#### 2. Power BI Dashboard & DAX Modelleme (`walmart.pbix`)
* **Veri Kaynağı:** 45 mağazaya ait 6.435 satırlık haftalık satış verisi (`Walmart_Sales.csv`).
* **Power Query & ETL:** Veri temizleme adımları (yerel/ondalık ayracı hatasının kök neden tespiti ve düzeltilmesi, tarih tipleme), hesaplanan sütunlar (`Year`, `Month`, `Quarter`, `Holiday Category`).
* **DAX Ölçüleri:** `CALCULATE`, `DIVIDE`, `SWITCH` fonksiyonları; `DATEADD` kısıtına alternatif olarak `MAX()` tabanlı özel zaman karşılaştırma mantığıyla geliştirilen dinamik `Sales Growth %` ölçüsü.
* **Dashboard Tasarımı:** 3 sayfalık interaktif yönetici paneli (KPI kartları, zaman serisi trendi, Top/Bottom 10 mağaza karşılaştırması, tatil vs. normal dönem satış kırılımları, dinamik filtreleme/slicer yapıları).
* **Odak:** Mağaza performans karşılaştırması ve tatil dönemlerinin satış hacmine etkisinin analizi.

#### 3. AdventureWorks Kurumsal Satış & Müşteri Analizi (`SQLQuery_advventureworks.sql`)
* **Veritabanı:** Microsoft AdventureWorks.
* **T-SQL:** Çoklu Tablo Birleştirmeleri (`JOIN`), Ortak Tablo İfadeleri (`CTE`), Pencere Fonksiyonları (`DENSE_RANK`, `ROW_NUMBER`, `SUM() OVER`) ve raporlama süreçleri için optimize edilmiş `VIEW` yapıları.
* **Odak:** Müşteri segmentasyonu, ürün kârlılık analizi ve bölgesel satış performans kırılımları.
