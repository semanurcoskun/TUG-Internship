import requests

def test_7timer_seeing(lat: float, lon: float):
    # 7Timer Astro API Endpoint'i
    url = "http://www.7timer.info/bin/api.pl"
    
    # Parametreler (astro ürünü özellikle astronomik verileri içerir)
    params = {
        "lon": lon,
        "lat": lat,
        "product": "astro",
        "output": "json"
    }
    
    print(f"{lat}, {lon} koordinatları için 7Timer! API'sine bağlanılıyor...\n")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print("--- SEEING TAHMİN SONUÇLARI ---")
        print("Skorlama: 1 (Mükemmel < 0.5\") - 8 (Çok Kötü > 3\")")
        print("-" * 35)
        
        # 'dataseries' listesi gelecekteki 3'er saatlik tahminleri tutar
        # İlk 8 veri noktasını (önümüzdeki 24 saati) ekrana basalım
        for item in data.get("dataseries", [])[:24]:
            timepoint = item["timepoint"]
            seeing = item["seeing"]
            
            # Daha şık bir çıktı için if-else ile durum tespiti
            durum = "Mükemmel" if seeing <= 2 else "İdare Eder" if seeing <= 5 else "Kötü"
            
            print(f"Şu andan +{timepoint:02d} saat sonra -> İndeks: {seeing}/8 ({durum})")
            
    except requests.exceptions.RequestException as e:
        print(f"API'ye ulaşılamadı. Hata: {e}")

if __name__ == "__main__":
    # TUG Koordinatları (Enlem: 36.824, Boylam: 30.335) ile testi başlatıyoruz
    test_7timer_seeing(36.824, 30.335)