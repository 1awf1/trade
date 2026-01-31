# Çevre Değişkenleri Dokümantasyonu

Bu dokümanda Kripto Para Analiz Sistemi için kullanılan tüm çevre değişkenleri açıklanmaktadır.

## Genel Uygulama Ayarları

### APP_NAME
- **Açıklama**: Uygulamanın adı
- **Varsayılan**: `Kripto Para Analiz Sistemi`
- **Zorunlu**: Hayır
- **Örnek**: `APP_NAME=Kripto Para Analiz Sistemi`

### APP_VERSION
- **Açıklama**: Uygulamanın sürüm numarası
- **Varsayılan**: `1.0.0`
- **Zorunlu**: Hayır
- **Örnek**: `APP_VERSION=1.0.0`

### DEBUG
- **Açıklama**: Debug modunu aktif/pasif yapar
- **Varsayılan**: `True`
- **Zorunlu**: Hayır
- **Değerler**: `True`, `False`
- **Örnek**: `DEBUG=False`
- **Not**: Production ortamında mutlaka `False` olmalıdır

### ENVIRONMENT
- **Açıklama**: Çalışma ortamı
- **Varsayılan**: `development`
- **Zorunlu**: Hayır
- **Değerler**: `development`, `staging`, `production`
- **Örnek**: `ENVIRONMENT=production`

## Sunucu Yapılandırması

### HOST
- **Açıklama**: Uygulamanın dinleyeceği IP adresi
- **Varsayılan**: `0.0.0.0`
- **Zorunlu**: Hayır
- **Örnek**: `HOST=0.0.0.0`
- **Not**: `0.0.0.0` tüm network interface'lerden erişime izin verir

### PORT
- **Açıklama**: Uygulamanın dinleyeceği port numarası
- **Varsayılan**: `8000`
- **Zorunlu**: Hayır
- **Örnek**: `PORT=8000`

## Veritabanı Yapılandırması

### POSTGRES_HOST
- **Açıklama**: PostgreSQL sunucu adresi
- **Varsayılan**: `localhost`
- **Zorunlu**: Evet
- **Örnek**: `POSTGRES_HOST=postgres` (Docker) veya `POSTGRES_HOST=localhost` (yerel)

### POSTGRES_PORT
- **Açıklama**: PostgreSQL port numarası
- **Varsayılan**: `5432`
- **Zorunlu**: Hayır
- **Örnek**: `POSTGRES_PORT=5432`

### POSTGRES_DB
- **Açıklama**: Veritabanı adı
- **Varsayılan**: `crypto_analysis`
- **Zorunlu**: Evet
- **Örnek**: `POSTGRES_DB=crypto_analysis`

### POSTGRES_USER
- **Açıklama**: Veritabanı kullanıcı adı
- **Varsayılan**: `postgres`
- **Zorunlu**: Evet
- **Örnek**: `POSTGRES_USER=postgres`

### POSTGRES_PASSWORD
- **Açıklama**: Veritabanı şifresi
- **Varsayılan**: `postgres`
- **Zorunlu**: Evet
- **Örnek**: `POSTGRES_PASSWORD=güçlü_şifre_123`
- **Not**: Production ortamında güçlü bir şifre kullanın

### DATABASE_URL
- **Açıklama**: Tam veritabanı bağlantı URL'i
- **Varsayılan**: Otomatik oluşturulur
- **Zorunlu**: Hayır
- **Örnek**: `DATABASE_URL=postgresql://user:pass@host:5432/dbname`
- **Not**: Belirtilmezse diğer POSTGRES_* değişkenlerinden otomatik oluşturulur

## Redis Yapılandırması

### REDIS_HOST
- **Açıklama**: Redis sunucu adresi
- **Varsayılan**: `localhost`
- **Zorunlu**: Evet
- **Örnek**: `REDIS_HOST=redis` (Docker) veya `REDIS_HOST=localhost` (yerel)

### REDIS_PORT
- **Açıklama**: Redis port numarası
- **Varsayılan**: `6379`
- **Zorunlu**: Hayır
- **Örnek**: `REDIS_PORT=6379`

### REDIS_DB
- **Açıklama**: Redis veritabanı numarası
- **Varsayılan**: `0`
- **Zorunlu**: Hayır
- **Örnek**: `REDIS_DB=0`

### REDIS_PASSWORD
- **Açıklama**: Redis şifresi (varsa)
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `REDIS_PASSWORD=redis_şifresi`

### REDIS_URL
- **Açıklama**: Tam Redis bağlantı URL'i
- **Varsayılan**: Otomatik oluşturulur
- **Zorunlu**: Hayır
- **Örnek**: `REDIS_URL=redis://localhost:6379/0`

## Celery Yapılandırması

### CELERY_BROKER_URL
- **Açıklama**: Celery broker URL'i
- **Varsayılan**: REDIS_URL ile aynı
- **Zorunlu**: Hayır
- **Örnek**: `CELERY_BROKER_URL=redis://localhost:6379/0`

### CELERY_RESULT_BACKEND
- **Açıklama**: Celery sonuç backend URL'i
- **Varsayılan**: REDIS_URL ile aynı
- **Zorunlu**: Hayır
- **Örnek**: `CELERY_RESULT_BACKEND=redis://localhost:6379/0`

## Güvenlik Ayarları

### SECRET_KEY
- **Açıklama**: JWT token şifreleme için gizli anahtar
- **Varsayılan**: `your-secret-key-here-change-in-production`
- **Zorunlu**: Evet
- **Örnek**: `SECRET_KEY=çok_güçlü_ve_rastgele_bir_anahtar_12345`
- **Not**: Production'da mutlaka değiştirin! En az 32 karakter, rastgele olmalı

### ALGORITHM
- **Açıklama**: JWT token şifreleme algoritması
- **Varsayılan**: `HS256`
- **Zorunlu**: Hayır
- **Örnek**: `ALGORITHM=HS256`

### ACCESS_TOKEN_EXPIRE_MINUTES
- **Açıklama**: Access token geçerlilik süresi (dakika)
- **Varsayılan**: `30`
- **Zorunlu**: Hayır
- **Örnek**: `ACCESS_TOKEN_EXPIRE_MINUTES=30`

## Dış Servis API Anahtarları

### BINANCE_API_KEY
- **Açıklama**: Binance API anahtarı
- **Varsayılan**: Boş
- **Zorunlu**: Evet (fiyat verileri için)
- **Örnek**: `BINANCE_API_KEY=your_binance_api_key`
- **Nasıl Alınır**: https://www.binance.com/en/my/settings/api-management

### BINANCE_API_SECRET
- **Açıklama**: Binance API secret
- **Varsayılan**: Boş
- **Zorunlu**: Evet (fiyat verileri için)
- **Örnek**: `BINANCE_API_SECRET=your_binance_api_secret`

### COINGECKO_API_KEY
- **Açıklama**: CoinGecko API anahtarı
- **Varsayılan**: Boş
- **Zorunlu**: Hayır (alternatif veri kaynağı)
- **Örnek**: `COINGECKO_API_KEY=your_coingecko_api_key`
- **Nasıl Alınır**: https://www.coingecko.com/en/api/pricing

## Sosyal Medya API Anahtarları

### TWITTER_API_KEY
- **Açıklama**: Twitter API anahtarı
- **Varsayılan**: Boş
- **Zorunlu**: Hayır (temel analiz için)
- **Örnek**: `TWITTER_API_KEY=your_twitter_api_key`
- **Nasıl Alınır**: https://developer.twitter.com/en/portal/dashboard

### TWITTER_API_SECRET
- **Açıklama**: Twitter API secret
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `TWITTER_API_SECRET=your_twitter_api_secret`

### TWITTER_ACCESS_TOKEN
- **Açıklama**: Twitter access token
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `TWITTER_ACCESS_TOKEN=your_twitter_access_token`

### TWITTER_ACCESS_SECRET
- **Açıklama**: Twitter access secret
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `TWITTER_ACCESS_SECRET=your_twitter_access_secret`

### TWITTER_BEARER_TOKEN
- **Açıklama**: Twitter bearer token
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `TWITTER_BEARER_TOKEN=your_twitter_bearer_token`

### REDDIT_CLIENT_ID
- **Açıklama**: Reddit client ID
- **Varsayılan**: Boş
- **Zorunlu**: Hayır (temel analiz için)
- **Örnek**: `REDDIT_CLIENT_ID=your_reddit_client_id`
- **Nasıl Alınır**: https://www.reddit.com/prefs/apps

### REDDIT_CLIENT_SECRET
- **Açıklama**: Reddit client secret
- **Varsayılan**: Boş
- **Zorunlu**: Hayır
- **Örnek**: `REDDIT_CLIENT_SECRET=your_reddit_client_secret`

### REDDIT_USER_AGENT
- **Açıklama**: Reddit user agent
- **Varsayılan**: `CryptoAnalysisBot/1.0`
- **Zorunlu**: Hayır
- **Örnek**: `REDDIT_USER_AGENT=CryptoAnalysisBot/1.0`

## Yapay Zeka Yapılandırması

### GEMINI_API_KEY
- **Açıklama**: Google Gemini API anahtarı
- **Varsayılan**: Boş
- **Zorunlu**: Evet (AI yorumlama için)
- **Örnek**: `GEMINI_API_KEY=AIzaSy...`
- **Nasıl Alınır**: https://makersuite.google.com/app/apikey

### AI_MODEL
- **Açıklama**: Kullanılacak AI modeli
- **Varsayılan**: `gemini-2.5-flash`
- **Zorunlu**: Hayır
- **Değerler**: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-flash-latest`, `gemini-pro-latest`
- **Örnek**: `AI_MODEL=gemini-2.5-flash`
- **Not**: `gemini-2.5-flash` hızlı ve ekonomik, `gemini-2.5-pro` daha gelişmiş analiz için önerilir

### AI_TEMPERATURE
- **Açıklama**: AI yanıt çeşitliliği (0-2 arası)
- **Varsayılan**: `0.7`
- **Zorunlu**: Hayır
- **Örnek**: `AI_TEMPERATURE=0.7`
- **Not**: Düşük değer daha tutarlı, yüksek değer daha yaratıcı yanıtlar

### AI_MAX_TOKENS
- **Açıklama**: Maksimum token sayısı
- **Varsayılan**: `1000`
- **Zorunlu**: Hayır
- **Örnek**: `AI_MAX_TOKENS=1000`

## E-posta Yapılandırması

### SMTP_HOST
- **Açıklama**: SMTP sunucu adresi
- **Varsayılan**: `smtp.gmail.com`
- **Zorunlu**: Evet (alarm bildirimleri için)
- **Örnek**: `SMTP_HOST=smtp.gmail.com`

### SMTP_PORT
- **Açıklama**: SMTP port numarası
- **Varsayılan**: `587`
- **Zorunlu**: Hayır
- **Örnek**: `SMTP_PORT=587`

### SMTP_USER
- **Açıklama**: SMTP kullanıcı adı (e-posta)
- **Varsayılan**: Boş
- **Zorunlu**: Evet (alarm bildirimleri için)
- **Örnek**: `SMTP_USER=your_email@gmail.com`

### SMTP_PASSWORD
- **Açıklama**: SMTP şifresi veya app password
- **Varsayılan**: Boş
- **Zorunlu**: Evet (alarm bildirimleri için)
- **Örnek**: `SMTP_PASSWORD=your_app_password`
- **Not**: Gmail için "App Password" kullanın

### EMAIL_FROM
- **Açıklama**: Gönderen e-posta adresi
- **Varsayılan**: `noreply@cryptoanalysis.com`
- **Zorunlu**: Hayır
- **Örnek**: `EMAIL_FROM=noreply@cryptoanalysis.com`

## Önbellek Ayarları

### CACHE_TTL_PRICE
- **Açıklama**: Fiyat verisi önbellek süresi (saniye)
- **Varsayılan**: `60`
- **Zorunlu**: Hayır
- **Örnek**: `CACHE_TTL_PRICE=60`

### CACHE_TTL_OHLCV
- **Açıklama**: OHLCV verisi önbellek süresi (saniye)
- **Varsayılan**: `300`
- **Zorunlu**: Hayır
- **Örnek**: `CACHE_TTL_OHLCV=300`

### CACHE_TTL_SOCIAL
- **Açıklama**: Sosyal medya verisi önbellek süresi (saniye)
- **Varsayılan**: `3600`
- **Zorunlu**: Hayır
- **Örnek**: `CACHE_TTL_SOCIAL=3600`

### CACHE_TTL_NEWS
- **Açıklama**: Haber verisi önbellek süresi (saniye)
- **Varsayılan**: `3600`
- **Zorunlu**: Hayır
- **Örnek**: `CACHE_TTL_NEWS=3600`

### CACHE_TTL_ANALYSIS
- **Açıklama**: Analiz sonucu önbellek süresi (saniye)
- **Varsayılan**: `600`
- **Zorunlu**: Hayır
- **Örnek**: `CACHE_TTL_ANALYSIS=600`

## Performans Ayarları

### MAX_CONCURRENT_ANALYSES
- **Açıklama**: Eşzamanlı maksimum analiz sayısı
- **Varsayılan**: `10`
- **Zorunlu**: Hayır
- **Örnek**: `MAX_CONCURRENT_ANALYSES=10`

### ANALYSIS_TIMEOUT_SECONDS
- **Açıklama**: Analiz timeout süresi (saniye)
- **Varsayılan**: `30`
- **Zorunlu**: Hayır
- **Örnek**: `ANALYSIS_TIMEOUT_SECONDS=30`

## Örnek Yapılandırma Senaryoları

### Development (Geliştirme)
```bash
DEBUG=True
ENVIRONMENT=development
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

### Production (Üretim)
```bash
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=çok_güçlü_rastgele_anahtar
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=güçlü_veritabanı_şifresi
REDIS_HOST=redis
```

### Docker Compose
```bash
POSTGRES_HOST=postgres
REDIS_HOST=redis
# Diğer ayarlar .env dosyasında
```

## Güvenlik Önerileri

1. **SECRET_KEY**: Production'da mutlaka değiştirin ve güçlü bir anahtar kullanın
2. **POSTGRES_PASSWORD**: Varsayılan şifreyi değiştirin
3. **API Anahtarları**: Asla git'e commit etmeyin, .env dosyasını .gitignore'a ekleyin
4. **DEBUG**: Production'da mutlaka False olmalı
5. **SMTP_PASSWORD**: Gmail için "App Password" kullanın, normal şifre kullanmayın

## Sorun Giderme

### Veritabanı bağlantı hatası
- POSTGRES_HOST değerini kontrol edin (Docker: `postgres`, Yerel: `localhost`)
- POSTGRES_PASSWORD'ün doğru olduğundan emin olun
- PostgreSQL servisinin çalıştığını kontrol edin

### Redis bağlantı hatası
- REDIS_HOST değerini kontrol edin (Docker: `redis`, Yerel: `localhost`)
- Redis servisinin çalıştığını kontrol edin

### API anahtarı hataları
- API anahtarlarının doğru girildiğinden emin olun
- API anahtarlarının aktif ve geçerli olduğunu kontrol edin
- Rate limit aşımı olup olmadığını kontrol edin
