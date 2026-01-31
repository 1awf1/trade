# Kripto Para Analiz Sistemi

Kripto para birimlerini analiz etmek için kapsamlı bir web platformu. Teknik analiz, temel analiz, yapay zeka destekli yorumlama, portföy izleme, alarm sistemi ve backtesting özellikleri sunar.

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Gereksinimler](#gereksinimler)
- [Kurulum](#kurulum)
  - [Docker ile Kurulum (Önerilen)](#docker-ile-kurulum-önerilen)
  - [Manuel Kurulum](#manuel-kurulum)
- [Yapılandırma](#yapılandırma)
- [Kullanım](#kullanım)
- [Proje Yapısı](#proje-yapısı)
- [Geliştirme](#geliştirme)
- [API Dokümantasyonu](#api-dokümantasyonu)
- [Sorun Giderme](#sorun-giderme)
- [Katkıda Bulunma](#katkıda-bulunma)

## ✨ Özellikler

- 🔍 **Teknik Analiz**: 
  - RSI, MACD, Bollinger Bands, Stochastic Oscillator
  - ATR, VWAP, OBV, Fibonacci Retracement
  - Golden Cross / Death Cross tespiti
  - RSI Divergence analizi
  - EMA 200 Trend Filtresi
  - Dinamik Stop-Loss ve Take-Profit hesaplama

- 📊 **Temel Analiz**: 
  - Sosyal medya duygu analizi (Twitter, Reddit)
  - Haber duygu analizi
  - Google Trends entegrasyonu

- 🤖 **AI Yorumlama**: 
  - GPT-4 destekli Türkçe analiz raporları
  - Teknik terim açıklamaları
  - Kullanıcı dostu yorumlar

- 💼 **Portföy Yönetimi**: 
  - Gerçek zamanlı performans takibi
  - Kar/zarar hesaplama
  - İşlem geçmişi

- 🔔 **Alarm Sistemi**: 
  - Fiyat bazlı alarmlar
  - Sinyal bazlı alarmlar
  - Başarı ihtimali bazlı alarmlar
  - E-posta bildirimleri

- 📈 **Backtesting**: 
  - Geçmiş veriler üzerinde strateji testi
  - Detaylı performans metrikleri
  - Strateji karşılaştırma

- 🌐 **Web Arayüzü**: 
  - Responsive ve kullanıcı dostu
  - Gerçek zamanlı grafikler
  - Mobil uyumlu

## 🛠 Teknoloji Yığını

**Backend:**
- Python 3.10+
- FastAPI (Web framework)
- Pandas, NumPy (Veri işleme)
- TA-Lib (Teknik analiz)
- Transformers/OpenAI (AI yorumlama)
- Celery (Asenkron görevler)
- PostgreSQL (Veritabanı)
- Redis (Önbellek ve kuyruk)

**Frontend:**
- React.js / Vue.js
- TradingView Lightweight Charts
- Tailwind CSS

**Deployment:**
- Docker & Docker Compose
- Nginx (Reverse proxy)

## 📦 Gereksinimler

### Minimum Gereksinimler

- **Python**: 3.10 veya üzeri
- **Docker**: 20.10+ (önerilen kurulum için)
- **Docker Compose**: 2.0+ (önerilen kurulum için)
- **PostgreSQL**: 15+ (manuel kurulum için)
- **Redis**: 7+ (manuel kurulum için)
- **RAM**: En az 4GB (8GB önerilir)
- **Disk**: En az 10GB boş alan

### Sistem Bağımlılıkları

- **TA-Lib**: Teknik analiz kütüphanesi (sistem seviyesinde kurulum gerekir)
- **GCC/G++**: C/C++ derleyici (TA-Lib için)
- **PostgreSQL development headers**: libpq-dev (Ubuntu/Debian) veya postgresql-devel (CentOS/RHEL)

## 🚀 Kurulum

### Docker ile Kurulum (Önerilen)

Docker kullanarak kurulum en kolay ve hızlı yöntemdir. Tüm bağımlılıklar otomatik olarak yüklenir.

#### 1. Repoyu Klonlayın

```bash
git clone https://github.com/your-username/crypto-analysis-system.git
cd crypto-analysis-system
```

#### 2. Çevre Değişkenlerini Yapılandırın

```bash
# .env.example dosyasını kopyalayın
cp .env.example .env

# .env dosyasını düzenleyin
nano .env  # veya tercih ettiğiniz editör
```

**Önemli:** En azından şu değişkenleri yapılandırın:
- `SECRET_KEY`: Güçlü bir rastgele anahtar
- `POSTGRES_PASSWORD`: Güvenli bir veritabanı şifresi
- `OPENAI_API_KEY`: OpenAI API anahtarınız (AI yorumlama için)
- `BINANCE_API_KEY` ve `BINANCE_API_SECRET`: Binance API anahtarlarınız

Detaylı çevre değişkeni dokümantasyonu için [ENV_VARIABLES.md](ENV_VARIABLES.md) dosyasına bakın.

#### 3. Docker Container'ları Başlatın

```bash
# Production ortamı için
docker-compose up -d

# Veya development ortamı için (hot-reload ile)
docker-compose -f docker-compose.dev.yml up -d
```

#### 4. Logları Kontrol Edin

```bash
docker-compose logs -f
```

#### 5. Uygulamaya Erişin

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

### Manuel Kurulum

Manuel kurulum daha fazla kontrol sağlar ancak daha karmaşıktır.

#### 1. Repoyu Klonlayın

```bash
git clone https://github.com/your-username/crypto-analysis-system.git
cd crypto-analysis-system
```

#### 2. Python Sanal Ortamı Oluşturun

```bash
python3 -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 3. TA-Lib'i Yükleyin

**macOS:**
```bash
brew install ta-lib
```

**Ubuntu/Debian:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
```

**Windows:**
- [TA-Lib Windows binary](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) indirin
- Wheel dosyasını yükleyin: `pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑win_amd64.whl`

#### 4. Python Bağımlılıklarını Yükleyin

```bash
pip install -r requirements.txt
```

#### 5. PostgreSQL ve Redis'i Kurun ve Başlatın

**PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql
brew services start postgresql

# Veritabanı oluşturun
sudo -u postgres createdb crypto_analysis
```

**Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

#### 6. Çevre Değişkenlerini Yapılandırın

```bash
cp .env.example .env
nano .env  # Düzenleyin
```

#### 7. Veritabanı Migrasyonlarını Çalıştırın

```bash
python migrate.py
```

#### 8. Uygulamayı Başlatın

```bash
# Başlangıç kontrollerini çalıştır
python startup.py

# API sunucusunu başlat
uvicorn api.main:app --reload

# Ayrı terminallerde Celery worker ve beat başlatın
celery -A utils.celery_app worker --loglevel=info
celery -A utils.celery_app beat --loglevel=info
```

## ⚙️ Yapılandırma

Tüm yapılandırma `.env` dosyası üzerinden yapılır. Detaylı açıklamalar için [ENV_VARIABLES.md](ENV_VARIABLES.md) dosyasına bakın.

### Temel Yapılandırma

```bash
# Uygulama
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=çok_güçlü_rastgele_anahtar

# Veritabanı
POSTGRES_HOST=postgres  # Docker için, localhost yerel için
POSTGRES_PASSWORD=güvenli_şifre

# Redis
REDIS_HOST=redis  # Docker için, localhost yerel için

# API Anahtarları (zorunlu)
OPENAI_API_KEY=sk-...
BINANCE_API_KEY=...
BINANCE_API_SECRET=...

# E-posta (alarm bildirimleri için)
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### API Anahtarları Nasıl Alınır?

1. **OpenAI API Key**: https://platform.openai.com/api-keys
2. **Binance API Key**: https://www.binance.com/en/my/settings/api-management
3. **CoinGecko API Key**: https://www.coingecko.com/en/api/pricing
4. **Twitter API**: https://developer.twitter.com/en/portal/dashboard
5. **Reddit API**: https://www.reddit.com/prefs/apps

## 📖 Kullanım

### Makefile Komutları

Proje, yaygın işlemler için Makefile komutları içerir:

```bash
# Yardım
make help

# Bağımlılıkları yükle
make install

# Başlangıç kontrollerini çalıştır
make startup

# Veritabanı migrasyonları
make migrate

# Testleri çalıştır
make test
make test-cov      # Coverage ile
make test-pbt      # Sadece property-based testler

# Development sunucusu
make dev

# Docker işlemleri
make docker-build
make docker-up
make docker-up-dev
make docker-down
make logs

# Celery
make celery-worker
make celery-beat

# Temizlik
make clean
```

### API Kullanımı

API dokümantasyonuna erişmek için uygulamayı başlatın ve tarayıcınızda şu adresleri ziyaret edin:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Örnek API İstekleri

```bash
# Analiz başlat
curl -X POST "http://localhost:8000/api/analysis/start" \
  -H "Content-Type: application/json" \
  -d '{
    "coin": "BTC",
    "timeframe": "1h"
  }'

# Portföy görüntüle
curl -X GET "http://localhost:8000/api/portfolio" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Alarm oluştur
curl -X POST "http://localhost:8000/api/alarms" \
  -H "Content-Type: application/json" \
  -d '{
    "coin": "ETH",
    "type": "price",
    "condition": "above",
    "threshold": 3000
  }'
```

## 📁 Proje Yapısı

```
crypto-analysis-system/
├── api/                      # API Gateway ve endpoint'ler
│   ├── __init__.py
│   ├── main.py              # FastAPI uygulaması
│   └── routes/              # API route'ları
│       ├── analysis.py
│       ├── portfolio.py
│       └── alarms.py
├── engines/                 # Analiz motorları
│   ├── technical_analysis.py
│   ├── fundamental_analysis.py
│   ├── signal_generator.py
│   ├── ai_interpreter.py
│   ├── portfolio_manager.py
│   ├── alarm_system.py
│   ├── backtesting.py
│   └── data_collector.py
├── models/                  # Veri modelleri
│   ├── database.py         # SQLAlchemy modelleri
│   └── schemas.py          # Pydantic şemaları
├── tests/                   # Test dosyaları
│   ├── test_technical_analysis.py
│   ├── test_signal_generator.py
│   └── ...
├── utils/                   # Yardımcı fonksiyonlar
│   ├── config.py           # Yapılandırma yönetimi
│   ├── logger.py           # Loglama
│   ├── cache.py            # Redis önbellek
│   ├── dependencies.py     # Bağımlılık kontrolü
│   ├── celery_app.py       # Celery yapılandırması
│   └── security.py         # Güvenlik fonksiyonları
├── frontend/                # Frontend uygulaması
│   ├── src/
│   ├── package.json
│   └── ...
├── .env.example            # Örnek çevre değişkenleri
├── .gitignore
├── docker-compose.yml      # Production Docker Compose
├── docker-compose.dev.yml  # Development Docker Compose
├── Dockerfile              # Backend Dockerfile
├── Dockerfile.frontend     # Frontend Dockerfile
├── nginx.conf              # Nginx yapılandırması
├── init.sql                # Veritabanı başlangıç scripti
├── migrate.py              # Veritabanı migration scripti
├── startup.py              # Uygulama başlangıç scripti
├── requirements.txt        # Python bağımlılıkları
├── Makefile                # Makefile komutları
├── README.md               # Bu dosya
└── ENV_VARIABLES.md        # Çevre değişkenleri dokümantasyonu
```

## 🔧 Geliştirme

### Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest

# Verbose mod ile
pytest -v

# Coverage raporu ile
pytest --cov=. --cov-report=html

# Sadece property-based testler
pytest tests/ -k "property"

# Belirli bir test dosyası
pytest tests/test_technical_analysis.py
```

### Kod Kalitesi

```bash
# Linting
make lint

# Code formatting
make format

# Bağımlılık kontrolü
make check-deps
```

### Development Ortamı

Development ortamında hot-reload aktiftir:

```bash
# Docker ile
make docker-up-dev

# Manuel
make dev
```

## 📚 API Dokümantasyonu

Uygulama çalışırken otomatik API dokümantasyonuna erişebilirsiniz:

- **Swagger UI**: http://localhost:8000/docs
  - İnteraktif API dokümantasyonu
  - API endpoint'lerini test edebilirsiniz

- **ReDoc**: http://localhost:8000/redoc
  - Daha okunabilir dokümantasyon formatı

### Ana Endpoint'ler

- `POST /api/analysis/start` - Yeni analiz başlat
- `GET /api/analysis/{id}` - Analiz sonucu getir
- `GET /api/portfolio` - Portföy görüntüle
- `POST /api/portfolio/add` - Portföye coin ekle
- `POST /api/alarms` - Alarm oluştur
- `POST /api/backtest/start` - Backtesting başlat

## 🐛 Sorun Giderme

### Veritabanı Bağlantı Hatası

**Hata**: `could not connect to server: Connection refused`

**Çözüm**:
```bash
# PostgreSQL'in çalıştığını kontrol edin
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Docker kullanıyorsanız
docker-compose ps
docker-compose logs postgres
```

### Redis Bağlantı Hatası

**Hata**: `Error connecting to Redis`

**Çözüm**:
```bash
# Redis'in çalıştığını kontrol edin
sudo systemctl status redis  # Linux
brew services list  # macOS

# Docker kullanıyorsanız
docker-compose logs redis
```

### TA-Lib Import Hatası

**Hata**: `ImportError: No module named 'talib'`

**Çözüm**:
```bash
# TA-Lib sistem kütüphanesini yükleyin (yukarıdaki kurulum adımlarına bakın)
# Sonra Python paketini yükleyin
pip install TA-Lib
```

### API Anahtarı Hataları

**Hata**: `401 Unauthorized` veya `Invalid API key`

**Çözüm**:
- `.env` dosyasında API anahtarlarının doğru girildiğinden emin olun
- API anahtarlarının aktif ve geçerli olduğunu kontrol edin
- Rate limit aşımı olup olmadığını kontrol edin

### Docker Build Hatası

**Hata**: `ERROR [internal] load metadata for docker.io/library/python:3.11-slim`

**Çözüm**:
```bash
# Docker daemon'ın çalıştığından emin olun
sudo systemctl start docker  # Linux

# Docker cache'i temizleyin
docker system prune -a

# Tekrar build edin
docker-compose build --no-cache
```

### Port Zaten Kullanımda

**Hata**: `Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use`

**Çözüm**:
```bash
# Portu kullanan process'i bulun
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Process'i durdurun veya .env dosyasında farklı bir port kullanın
PORT=8001
```

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Katkıda bulunmak için:

1. Repo'yu fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

### Katkı Kuralları

- Kod değişikliklerinde testler ekleyin
- Tüm testlerin geçtiğinden emin olun
- Kod formatını koruyun (black, flake8)
- Commit mesajlarını açıklayıcı yazın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 📞 Destek

Sorularınız veya sorunlarınız için:

- GitHub Issues: [Issues sayfası](https://github.com/your-username/crypto-analysis-system/issues)
- Email: support@cryptoanalysis.com
- Documentation: [Wiki](https://github.com/your-username/crypto-analysis-system/wiki)

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynak projeleri kullanmaktadır:

- [FastAPI](https://fastapi.tiangolo.com/)
- [TA-Lib](https://ta-lib.org/)
- [Pandas](https://pandas.pydata.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)
- [Celery](https://docs.celeryproject.org/)

---

**Not**: Bu proje eğitim ve araştırma amaçlıdır. Finansal tavsiye değildir. Yatırım kararlarınızı kendi araştırmanıza dayanarak verin.
