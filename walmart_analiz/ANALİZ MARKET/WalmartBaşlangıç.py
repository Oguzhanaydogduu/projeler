import pandas as pd

df = pd.read_csv("Walmart_Sales.csv")

print("===== BOYUT (satır, sütun) =====")
print(df.shape)

print("\n===== SÜTUNLAR =====")
print(df.columns.tolist())

print("\n===== VERİ TİPLERİ =====")
print(df.dtypes)

print("\n===== İLK 5 SATIR =====")
print(df.head())

print("\n===== EKSİK (BOŞ) DEĞER SAYISI =====")
print(df.isnull().sum())

print("\n===== TEKRAR EDEN (DUPLICATE) SATIR SAYISI =====")
print(df.duplicated().sum())

print("\n===== BENZERSİZ DEĞER SAYISI (SÜTUN BAŞINA) =====")
print(df.nunique())

print("\n===== SAYISAL SÜTUNLAR İÇİN İSTATİSTİK =====")
print(df.describe())

# Date sütununu gerçek tarihe çevir (gg-aa-yyyy formatında)
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")

print("\n===== DATE ÇEVRİLDİKTEN SONRA VERİ TİPLERİ =====")
print(df.dtypes)

print("\n===== TARİH ARALIĞI =====")
print(df["Date"].min(), "-", df["Date"].max())

# Temizlenmiş veriyi kaydet
df.to_csv("Walmart_Sales_clean.csv", index=False)
print("\nTemizlenmiş veri 'Walmart_Sales_clean.csv' olarak kaydedildi.")
