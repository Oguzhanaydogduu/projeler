/* ============================================================================
   PROJE   : AdventureWorks — Satış, Müşteri ve Ürün Performansı Analizi
   AMAÇ    : Yönetime sunulacak bir "veri analisti" portföy çalışması.
             Şirketin (kurgusal bir bisiklet/ekipman üreticisi olan
             AdventureWorks Cycles) satış performansını, müşteri davranışını
             ve ürün karlılığını SQL ile analiz ediyoruz.

   VERİTABANI: Bu script AdventureWorks OLTP şemasını (AdventureWorks2019 /
   AdventureWorks2022 / AdventureWorks) hedefler — Sales, Production, Person
   şemalarındaki normal ilişkisel tabloları kullanır.
   NOT: Eğer kurulu olan "AdventureWorksDW" (Data Warehouse / yıldız şeması,
   FactInternetSales, DimProduct gibi tablolar) ise bu script DOĞRUDAN
   ÇALIŞMAZ — tablo adları tamamen farklıdır. Aşağıdaki USE satırını kendi
   veritabanı adınıza göre güncelleyin ve hangi sürümün kurulu olduğunu
   `SELECT name FROM sys.databases;` ile kontrol edin.

   KULLANILAN TEKNİKLER: JOIN (INNER/LEFT/SELF), alt sorgu (correlated /
   non-correlated), CTE (WITH), window fonksiyonları (ROW_NUMBER, RANK,
   LAG, SUM/AVG OVER), CASE WHEN, agregasyon.

   YAPI:
     BÖLÜM 0 — Ortam kontrolü
     BÖLÜM 1 — SATIŞ (Sales) analizi           [1.1 - 1.5]
     BÖLÜM 2 — MÜŞTERİ (Customer) analizi       [2.1 - 2.6]
     BÖLÜM 3 — ÜRÜN (Product) analizi           [3.1 - 3.6]
     BÖLÜM 4 — ÇAPRAZ ANALİZ (Satış+Müşteri+Ürün) [4.1 - 4.5]
   ============================================================================ */

USE AdventureWorks;  -- Kendi veritabanı adınıza göre değiştirin
GO


/* ============================================================================
   BÖLÜM 0 — ORTAM KONTROLÜ
   Sorguları çalıştırmadan önce doğru veritabanına bağlı olduğunuzu ve
   temel tabloların dolu olduğunu doğrulayın.
   ============================================================================ */

SELECT name FROM sys.databases ORDER BY name;

SELECT
    (SELECT COUNT(*) FROM Sales.SalesOrderHeader)   AS SiparisSayisi,
    (SELECT COUNT(*) FROM Sales.SalesOrderDetail)    AS SiparisSatiriSayisi,
    (SELECT COUNT(*) FROM Sales.Customer)            AS MusteriSayisi,
    (SELECT COUNT(*) FROM Production.Product)        AS UrunSayisi,
    (SELECT MIN(OrderDate) FROM Sales.SalesOrderHeader) AS IlkSiparisTarihi,
    (SELECT MAX(OrderDate) FROM Sales.SalesOrderHeader) AS SonSiparisTarihi;
GO



/* ============================================================================
   BÖLÜM 1 — SATIŞ (SALES) ANALİZİ
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- 1.1  Yıllık ve çeyreklik satış trendi
-- İş sorusu : Gelir zaman içinde nasıl değişiyor? Hangi çeyrekler güçlü/zayıf?
-- Teknik    : GROUP BY + agregasyon (SUM, COUNT, AVG)
-- ----------------------------------------------------------------------------
SELECT
    YEAR(soh.OrderDate)                         AS Yil,
    DATEPART(QUARTER, soh.OrderDate)             AS Ceyrek,
    COUNT(DISTINCT soh.SalesOrderID)             AS SiparisSayisi,
    SUM(soh.TotalDue)                            AS ToplamGelir,
    AVG(soh.TotalDue)                            AS OrtalamaSiparisDegeri
FROM Sales.SalesOrderHeader AS soh
GROUP BY YEAR(soh.OrderDate), DATEPART(QUARTER, soh.OrderDate)
ORDER BY Yil, Ceyrek;
GO


-- ----------------------------------------------------------------------------
-- 1.2  Bölge (Territory) bazlı satış performansı
-- İş sorusu : Hangi satış bölgesi en çok geliri üretiyor?
-- Teknik    : INNER JOIN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT
    st.Name                                      AS Bolge,
    st.[Group]                                   AS BolgeGrubu,
    COUNT(DISTINCT soh.SalesOrderID)             AS SiparisSayisi,
    SUM(soh.TotalDue)                            AS ToplamGelir,
    CAST(SUM(soh.TotalDue) * 100.0 /
         SUM(SUM(soh.TotalDue)) OVER ()  AS DECIMAL(5,2))  AS GelirPayi_Yuzde
FROM Sales.SalesOrderHeader AS soh
INNER JOIN Sales.SalesTerritory AS st
    ON soh.TerritoryID = st.TerritoryID
GROUP BY st.Name, st.[Group]
ORDER BY ToplamGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 1.3  Online vs Mağaza (satış kanalı) karşılaştırması
-- İş sorusu : Online kanal mı yoksa satış temsilcisi üzerinden yapılan
--             satışlar mı daha değerli / daha sık?
-- Teknik    : CASE WHEN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN soh.OnlineOrderFlag = 1 THEN 'Online' ELSE 'Satış Temsilcisi (Offline)' END AS SatisKanali,
    COUNT(DISTINCT soh.SalesOrderID)             AS SiparisSayisi,
    SUM(soh.TotalDue)                            AS ToplamGelir,
    AVG(soh.TotalDue)                            AS OrtalamaSiparisDegeri
FROM Sales.SalesOrderHeader AS soh
GROUP BY CASE WHEN soh.OnlineOrderFlag = 1 THEN 'Online' ELSE 'Satış Temsilcisi (Offline)' END;
GO


-- ----------------------------------------------------------------------------
-- 1.4  Aylık gelir + 3 aylık hareketli ortalama
-- İş sorusu : Kısa vadeli dalgalanmaların altındaki asıl trend nedir?
-- Teknik    : Window fonksiyonu — AVG() OVER (... ROWS BETWEEN ...)
-- ----------------------------------------------------------------------------
WITH AylikGelir AS (
    SELECT
        DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1) AS Ay,
        SUM(TotalDue) AS AylikToplam
    FROM Sales.SalesOrderHeader
    GROUP BY DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1)
)
SELECT
    Ay,
    AylikToplam,
    AVG(AylikToplam) OVER (
        ORDER BY Ay
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    )                                             AS HareketliOrtalama_3Ay
FROM AylikGelir
ORDER BY Ay;
GO


-- ----------------------------------------------------------------------------
-- 1.5  Yıldan yıla (YoY) büyüme oranı
-- İş sorusu : Şirket her yıl bir öncekine göre ne kadar büyüdü/küçüldü?
-- Teknik    : Window fonksiyonu — LAG()
-- ----------------------------------------------------------------------------
WITH YillikGelir AS (
    SELECT YEAR(OrderDate) AS Yil, SUM(TotalDue) AS ToplamGelir
    FROM Sales.SalesOrderHeader
    GROUP BY YEAR(OrderDate)
)
SELECT
    Yil,
    ToplamGelir,
    LAG(ToplamGelir) OVER (ORDER BY Yil)           AS OncekiYilGeliri,
    CAST(
        (ToplamGelir - LAG(ToplamGelir) OVER (ORDER BY Yil)) * 100.0
        / NULLIF(LAG(ToplamGelir) OVER (ORDER BY Yil), 0)
    AS DECIMAL(6,2))                               AS YoY_Buyume_Yuzde
FROM YillikGelir
ORDER BY Yil;
GO



/* ============================================================================
   BÖLÜM 2 — MÜŞTERİ (CUSTOMER) ANALİZİ
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- 2.1  En yüksek harcama yapan Top 20 müşteri
-- İş sorusu : En değerli müşterilerimiz kim? (VIP / büyük hesap listesi)
-- Teknik    : JOIN + TOP + ORDER BY
-- ----------------------------------------------------------------------------
SELECT TOP 20
    c.CustomerID,
    COALESCE(p.FirstName + ' ' + p.LastName, s.Name, 'Bilinmiyor') AS MusteriAdi,
    COUNT(DISTINCT soh.SalesOrderID)             AS SiparisSayisi,
    SUM(soh.TotalDue)                            AS ToplamHarcama
FROM Sales.Customer AS c
INNER JOIN Sales.SalesOrderHeader AS soh
    ON c.CustomerID = soh.CustomerID
LEFT JOIN Person.Person AS p
    ON c.PersonID = p.BusinessEntityID
LEFT JOIN Sales.Store AS s
    ON c.StoreID = s.BusinessEntityID
GROUP BY c.CustomerID, p.FirstName, p.LastName, s.Name
ORDER BY ToplamHarcama DESC;
GO


-- ----------------------------------------------------------------------------
-- 2.2  Müşteri segmentasyonu: Bireysel vs Mağaza/Bayi
-- İş sorusu : Gelirimizin ne kadarı bireysel müşterilerden, ne kadarı
--             mağaza/bayi (B2B) müşterilerinden geliyor?
-- Teknik    : CASE WHEN + JOIN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN c.StoreID IS NOT NULL THEN 'Mağaza / Bayi (B2B)' ELSE 'Bireysel Müşteri' END AS MusteriSegmenti,
    COUNT(DISTINCT c.CustomerID)                 AS MusteriSayisi,
    COUNT(DISTINCT soh.SalesOrderID)             AS SiparisSayisi,
    SUM(soh.TotalDue)                            AS ToplamGelir,
    AVG(soh.TotalDue)                            AS OrtalamaSiparisDegeri
FROM Sales.Customer AS c
INNER JOIN Sales.SalesOrderHeader AS soh
    ON c.CustomerID = soh.CustomerID
GROUP BY CASE WHEN c.StoreID IS NOT NULL THEN 'Mağaza / Bayi (B2B)' ELSE 'Bireysel Müşteri' END;
GO


-- ----------------------------------------------------------------------------
-- 2.3  Tekrar eden vs tek seferlik müşteriler
-- İş sorusu : Müşteri sadakati nasıl? Kaç müşteri sadece 1 kez sipariş verdi?
-- Teknik    : HAVING ile alt küme + CASE WHEN
-- ----------------------------------------------------------------------------
WITH MusteriSiparisSayisi AS (
    SELECT CustomerID, COUNT(DISTINCT SalesOrderID) AS SiparisSayisi
    FROM Sales.SalesOrderHeader
    GROUP BY CustomerID
)
SELECT
    CASE WHEN SiparisSayisi = 1 THEN 'Tek Seferlik Müşteri' ELSE 'Tekrar Eden Müşteri' END AS MusteriTipi,
    COUNT(*)                                     AS MusteriSayisi,
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () AS DECIMAL(5,2)) AS Yuzde
FROM MusteriSiparisSayisi
GROUP BY CASE WHEN SiparisSayisi = 1 THEN 'Tek Seferlik Müşteri' ELSE 'Tekrar Eden Müşteri' END;
GO


-- ----------------------------------------------------------------------------
-- 2.4  RFM benzeri analiz (Recency, Frequency, Monetary)
-- İş sorusu : Müşterileri "ne kadar yakın zamanda, ne sıklıkla, ne kadar
--             harcayarak" alışveriş yaptıklarına göre puanlayalım.
-- Teknik    : CTE + correlated alt sorgu + NTILE() window fonksiyonu
-- ----------------------------------------------------------------------------
WITH RFM_Ham AS (
    SELECT
        c.CustomerID,
        DATEDIFF(DAY, MAX(soh.OrderDate), (SELECT MAX(OrderDate) FROM Sales.SalesOrderHeader)) AS Recency_Gun,
        COUNT(DISTINCT soh.SalesOrderID)             AS Frequency,
        SUM(soh.TotalDue)                            AS Monetary
    FROM Sales.Customer AS c
    INNER JOIN Sales.SalesOrderHeader AS soh
        ON c.CustomerID = soh.CustomerID
    GROUP BY c.CustomerID
)
SELECT
    CustomerID,
    Recency_Gun, Frequency, Monetary,
    NTILE(5) OVER (ORDER BY Recency_Gun ASC)         AS R_Skoru,   -- 5 = en yakın zamanda alışveriş
    NTILE(5) OVER (ORDER BY Frequency DESC)          AS F_Skoru,   -- 5 = en sık alışveriş
    NTILE(5) OVER (ORDER BY Monetary DESC)           AS M_Skoru    -- 5 = en yüksek harcama
FROM RFM_Ham
ORDER BY Monetary DESC;
GO


-- ----------------------------------------------------------------------------
-- 2.5  Bölgeye göre müşteri dağılımı ve bölge başına ortalama müşteri değeri
-- İş sorusu : Hangi bölgede kaç müşteri var, ortalama müşteri değeri nasıl
--             farklılaşıyor?
-- Teknik    : JOIN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT
    st.Name                                      AS Bolge,
    COUNT(DISTINCT c.CustomerID)                 AS MusteriSayisi,
    SUM(soh.TotalDue)                            AS ToplamGelir,
    SUM(soh.TotalDue) / COUNT(DISTINCT c.CustomerID) AS MusteriBasinaOrtalamaGelir
FROM Sales.Customer AS c
INNER JOIN Sales.SalesOrderHeader AS soh
    ON c.CustomerID = soh.CustomerID
INNER JOIN Sales.SalesTerritory AS st
    ON c.TerritoryID = st.TerritoryID
GROUP BY st.Name
ORDER BY MusteriBasinaOrtalamaGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 2.6  Bölge içinde müşteri sıralaması
-- İş sorusu : Her bölgenin kendi içindeki en değerli 3 müşterisi kim?
-- Teknik    : Window fonksiyonu — RANK() OVER (PARTITION BY ...)
-- ----------------------------------------------------------------------------
WITH MusteriBolgeGelir AS (
    SELECT
        st.Name                                  AS Bolge,
        c.CustomerID,
        SUM(soh.TotalDue)                        AS ToplamHarcama,
        RANK() OVER (PARTITION BY st.Name ORDER BY SUM(soh.TotalDue) DESC) AS BolgeIciSira
    FROM Sales.Customer AS c
    INNER JOIN Sales.SalesOrderHeader AS soh
        ON c.CustomerID = soh.CustomerID
    INNER JOIN Sales.SalesTerritory AS st
        ON c.TerritoryID = st.TerritoryID
    GROUP BY st.Name, c.CustomerID
)
SELECT * FROM MusteriBolgeGelir
WHERE BolgeIciSira <= 3
ORDER BY Bolge, BolgeIciSira;
GO



/* ============================================================================
   BÖLÜM 3 — ÜRÜN (PRODUCT) ANALİZİ
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- 3.1  En çok satan Top 15 ürün (miktar ve gelir bazlı)
-- İş sorusu : Hangi ürünler hem hacim hem gelir açısından en güçlüsü?
-- Teknik    : JOIN + GROUP BY + TOP
-- ----------------------------------------------------------------------------
SELECT TOP 15
    p.ProductID,
    p.Name                                       AS UrunAdi,
    SUM(sod.OrderQty)                            AS SatilanAdet,
    SUM(sod.LineTotal)                           AS ToplamGelir
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Production.Product AS p
    ON sod.ProductID = p.ProductID
GROUP BY p.ProductID, p.Name
ORDER BY ToplamGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 3.2  Kategori bazlı satış ve kar marjı analizi
-- İş sorusu : Hangi ürün kategorisi hem en çok satıyor hem de en karlı?
-- Teknik    : Çoklu JOIN (Product -> Subcategory -> Category) + agregasyon
-- ----------------------------------------------------------------------------
SELECT
    pc.Name                                      AS Kategori,
    SUM(sod.OrderQty)                            AS SatilanAdet,
    SUM(sod.LineTotal)                           AS ToplamGelir,
    SUM(sod.OrderQty * p.StandardCost)           AS ToplamMaliyet,
    SUM(sod.LineTotal) - SUM(sod.OrderQty * p.StandardCost) AS TahminiKarMarji,
    CAST(
        (SUM(sod.LineTotal) - SUM(sod.OrderQty * p.StandardCost)) * 100.0
        / NULLIF(SUM(sod.LineTotal), 0)
    AS DECIMAL(5,2))                             AS KarMarjiYuzde
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Production.Product AS p
    ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc
    ON p.ProductSubcategoryID = psc.ProductSubcategoryID
INNER JOIN Production.ProductCategory AS pc
    ON psc.ProductCategoryID = pc.ProductCategoryID
GROUP BY pc.Name
ORDER BY TahminiKarMarji DESC;
GO


-- ----------------------------------------------------------------------------
-- 3.3  En karlı ürünler vs en çok satan ürünler — fark var mı?
-- İş sorusu : "Çok satan" ile "çok kazandıran" her zaman aynı ürün mü?
-- Teknik    : CTE + iki ayrı sıralama (ROW_NUMBER) kıyaslaması
-- ----------------------------------------------------------------------------
WITH UrunOzet AS (
    SELECT
        p.ProductID,
        p.Name AS UrunAdi,
        SUM(sod.OrderQty) AS SatilanAdet,
        SUM(sod.LineTotal) - SUM(sod.OrderQty * p.StandardCost) AS TahminiKar
    FROM Sales.SalesOrderDetail AS sod
    INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
    GROUP BY p.ProductID, p.Name
),
Siralamalar AS (
    SELECT *,
        ROW_NUMBER() OVER (ORDER BY SatilanAdet DESC) AS AdetSirasi,
        ROW_NUMBER() OVER (ORDER BY TahminiKar DESC)  AS KarSirasi
    FROM UrunOzet
)
SELECT TOP 10 UrunAdi, SatilanAdet, AdetSirasi, TahminiKar, KarSirasi
FROM Siralamalar
ORDER BY KarSirasi;
GO


-- ----------------------------------------------------------------------------
-- 3.4  Alt kategori (Subcategory) performans sıralaması
-- İş sorusu : 37 alt kategori arasında en güçlü/zayıf 5'er tanesi hangisi?
-- Teknik    : JOIN + GROUP BY + TOP (iki ayrı sorgu: en iyi / en kötü)
-- ----------------------------------------------------------------------------
SELECT TOP 5
    psc.Name AS AltKategori, SUM(sod.LineTotal) AS ToplamGelir
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc ON p.ProductSubcategoryID = psc.ProductSubcategoryID
GROUP BY psc.Name
ORDER BY ToplamGelir DESC;   -- En iyi 5

SELECT TOP 5
    psc.Name AS AltKategori, SUM(sod.LineTotal) AS ToplamGelir
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc ON p.ProductSubcategoryID = psc.ProductSubcategoryID
GROUP BY psc.Name
ORDER BY ToplamGelir ASC;    -- En zayıf 5
GO


-- ----------------------------------------------------------------------------
-- 3.5  Hiç satılmamış ürünler
-- İş sorusu : Kataloğumuzda olup hiç satılmayan / stokta atıl kalan ürün var mı?
-- Teknik    : LEFT JOIN + IS NULL  (aynı işi NOT EXISTS ile de gösteriyoruz)
-- ----------------------------------------------------------------------------
SELECT p.ProductID, p.Name AS UrunAdi, p.ListPrice
FROM Production.Product AS p
LEFT JOIN Sales.SalesOrderDetail AS sod
    ON p.ProductID = sod.ProductID
WHERE sod.SalesOrderDetailID IS NULL
ORDER BY p.ListPrice DESC;

-- Aynı sonuç, NOT EXISTS (correlated alt sorgu) ile:
SELECT p.ProductID, p.Name AS UrunAdi, p.ListPrice
FROM Production.Product AS p
WHERE NOT EXISTS (
    SELECT 1 FROM Sales.SalesOrderDetail AS sod
    WHERE sod.ProductID = p.ProductID
)
ORDER BY p.ListPrice DESC;
GO


-- ----------------------------------------------------------------------------
-- 3.6  Birlikte sıkça satılan ürün çiftleri (basit sepet analizi)
-- İş sorusu : Hangi ürünler aynı siparişte birlikte satın alınıyor?
--             (çapraz satış / paketleme fırsatları için)
-- Teknik    : SELF JOIN (aynı SalesOrderID üzerinden) + GROUP BY
-- ----------------------------------------------------------------------------
SELECT TOP 20
    p1.Name AS Urun1,
    p2.Name AS Urun2,
    COUNT(*) AS BirlikteSatinAlmaSayisi
FROM Sales.SalesOrderDetail AS sod1
INNER JOIN Sales.SalesOrderDetail AS sod2
    ON sod1.SalesOrderID = sod2.SalesOrderID
    AND sod1.ProductID < sod2.ProductID     -- aynı çifti iki kez saymamak için
INNER JOIN Production.Product AS p1 ON sod1.ProductID = p1.ProductID
INNER JOIN Production.Product AS p2 ON sod2.ProductID = p2.ProductID
GROUP BY p1.Name, p2.Name
ORDER BY BirlikteSatinAlmaSayisi DESC;
GO



/* ============================================================================
   BÖLÜM 4 — ÇAPRAZ ANALİZ (SATIŞ + MÜŞTERİ + ÜRÜN BİRLİKTE)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- 4.1  Bölge x Kategori satış matrisi
-- İş sorusu : Her bölge hangi ürün kategorisine yatkın? (bölgesel ürün
--             stratejisi / stok dağıtımı için)
-- Teknik    : Çoklu JOIN + GROUP BY (iki boyutlu kırılım)
-- ----------------------------------------------------------------------------
SELECT
    st.Name                                      AS Bolge,
    pc.Name                                      AS Kategori,
    SUM(sod.LineTotal)                           AS ToplamGelir
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Sales.SalesOrderHeader AS soh ON sod.SalesOrderID = soh.SalesOrderID
INNER JOIN Sales.SalesTerritory AS st ON soh.TerritoryID = st.TerritoryID
INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc ON p.ProductSubcategoryID = psc.ProductSubcategoryID
INNER JOIN Production.ProductCategory AS pc ON psc.ProductCategoryID = pc.ProductCategoryID
GROUP BY st.Name, pc.Name
ORDER BY Bolge, ToplamGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 4.2  Müşteri segmentine göre en çok tercih edilen kategori
-- İş sorusu : Bireysel müşteriler mi, bayiler mi hangi kategoriyi daha çok
--             tercih ediyor? Pazarlama segmentasyonu için önemli.
-- Teknik    : CASE WHEN + çoklu JOIN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT
    CASE WHEN c.StoreID IS NOT NULL THEN 'Mağaza / Bayi (B2B)' ELSE 'Bireysel Müşteri' END AS MusteriSegmenti,
    pc.Name                                      AS Kategori,
    SUM(sod.LineTotal)                           AS ToplamGelir
FROM Sales.SalesOrderDetail AS sod
INNER JOIN Sales.SalesOrderHeader AS soh ON sod.SalesOrderID = soh.SalesOrderID
INNER JOIN Sales.Customer AS c ON soh.CustomerID = c.CustomerID
INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc ON p.ProductSubcategoryID = psc.ProductSubcategoryID
INNER JOIN Production.ProductCategory AS pc ON psc.ProductCategoryID = pc.ProductCategoryID
GROUP BY CASE WHEN c.StoreID IS NOT NULL THEN 'Mağaza / Bayi (B2B)' ELSE 'Bireysel Müşteri' END, pc.Name
ORDER BY MusteriSegmenti, ToplamGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 4.3  Tarihe göre kümülatif (running total) gelir
-- İş sorusu : Yıl içinde hedefe doğru birikimli ilerleme nasıl görünüyor?
-- Teknik    : Window fonksiyonu — SUM() OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)
-- ----------------------------------------------------------------------------
WITH AylikGelir AS (
    SELECT
        DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1) AS Ay,
        SUM(TotalDue) AS AylikToplam
    FROM Sales.SalesOrderHeader
    GROUP BY DATEFROMPARTS(YEAR(OrderDate), MONTH(OrderDate), 1)
)
SELECT
    Ay,
    AylikToplam,
    SUM(AylikToplam) OVER (ORDER BY Ay ROWS UNBOUNDED PRECEDING) AS KumulatifGelir
FROM AylikGelir
ORDER BY Ay;
GO


-- ----------------------------------------------------------------------------
-- 4.4  En değerli 20 müşterinin en çok satın aldığı kategoriler
-- İş sorusu : VIP müşterilerimiz asıl olarak neye para harcıyor? Onlara özel
--             kampanya tasarlarken hangi kategoriye odaklanmalıyız?
-- Teknik    : CTE (Top20 müşteri alt kümesi) + JOIN + GROUP BY
-- ----------------------------------------------------------------------------
WITH Top20Musteri AS (
    SELECT TOP 20 c.CustomerID
    FROM Sales.Customer AS c
    INNER JOIN Sales.SalesOrderHeader AS soh ON c.CustomerID = soh.CustomerID
    GROUP BY c.CustomerID
    ORDER BY SUM(soh.TotalDue) DESC
)
SELECT
    pc.Name                                      AS Kategori,
    SUM(sod.LineTotal)                           AS ToplamGelir,
    COUNT(DISTINCT soh.CustomerID)               AS VipMusteriSayisi
FROM Top20Musteri AS t
INNER JOIN Sales.SalesOrderHeader AS soh ON t.CustomerID = soh.CustomerID
INNER JOIN Sales.SalesOrderDetail AS sod ON soh.SalesOrderID = sod.SalesOrderID
INNER JOIN Production.Product AS p ON sod.ProductID = p.ProductID
INNER JOIN Production.ProductSubcategory AS psc ON p.ProductSubcategoryID = psc.ProductSubcategoryID
INNER JOIN Production.ProductCategory AS pc ON psc.ProductCategoryID = pc.ProductCategoryID
GROUP BY pc.Name
ORDER BY ToplamGelir DESC;
GO


-- ----------------------------------------------------------------------------
-- 4.5  Satış temsilcisi performansı — bölge bazında sıralama
-- İş sorusu : Her bölgede en yüksek performanslı satış temsilcisi kim?
--             (Not: yalnızca offline/temsilci üzerinden yapılan siparişleri
--             kapsar; online siparişlerde SalesPersonID boştur.)
-- Teknik    : JOIN + window fonksiyonu (RANK) + PARTITION BY
-- ----------------------------------------------------------------------------
WITH TemsilciGelir AS (
    SELECT
        st.Name                                  AS Bolge,
        sp.BusinessEntityID                      AS TemsilciID,
        per.FirstName + ' ' + per.LastName        AS TemsilciAdi,
        SUM(soh.TotalDue)                        AS ToplamGelir,
        RANK() OVER (PARTITION BY st.Name ORDER BY SUM(soh.TotalDue) DESC) AS BolgeIciSira
    FROM Sales.SalesOrderHeader AS soh
    INNER JOIN Sales.SalesPerson AS sp ON soh.SalesPersonID = sp.BusinessEntityID
    INNER JOIN Person.Person AS per ON sp.BusinessEntityID = per.BusinessEntityID
    INNER JOIN Sales.SalesTerritory AS st ON soh.TerritoryID = st.TerritoryID
    WHERE soh.SalesPersonID IS NOT NULL
    GROUP BY st.Name, sp.BusinessEntityID, per.FirstName, per.LastName
)
SELECT * FROM TemsilciGelir
WHERE BolgeIciSira = 1
ORDER BY ToplamGelir DESC;
GO