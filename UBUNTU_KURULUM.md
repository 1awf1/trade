# Ubuntu 24.04 Sunucu Kurulum Rehberi

Bu rehber, Kripto Para Analiz Sistemi'ni Ubuntu 24.04 sunucusuna kurmanız için adım adım talimatlar içerir.

## 📋 Gereksinimler

- Ubuntu 24.04 LTS sunucu
- Root veya sudo yetkisi
- En az 4GB RAM (8GB önerilir)
- En az 20GB disk alanı
- İnternet bağlantısı

## 🚀 Hızlı Kurulum (Docker ile - Önerilen)

### 1. Sunucuya Bağlanın

```bash
ssh kullanici@sunucu-ip-adresi
```

### 2. Sistemi Güncelleyin

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Docker ve Docker Compose Kurun

```bash
# Docker kurulum scripti
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker'ı sudo olmadan kullanabilmek için
sudo usermod -aG docker $USER

# Docker Compose kurun
sudo apt install docker-compose-plugin -y

# Yeni grup ayarlarını aktif edin
newgrp docker

# Docker'ın çalıştığını kontrol edin
docker --version
docker compose version
```

### 4. Projeyi Klonlayın

```bash
# Ana dizine gidin
cd ~

# Projeyi klonlayın (GitHub'dan)
git clone https://github.com/kullanici-adi/crypto-analysis-system.git
cd crypto-analysis-system

# VEYA dosyaları manuel olarak yükleyin (SCP ile)
# Yerel bilgisayarınızdan:
# scp -r /yerel/proje/yolu kullanici@sunucu-ip:~/crypto-analysis-system
```

### 5. Çevre Değişkenlerini Yapılandırın

```bash
# .env dosyasını oluşturun
cp .env.example .env

# .env dosyasını düzenleyin
nano .env
```

**Önemli: Aşağıdaki değişkenleri mutlaka değiştirin:**

```bash
# Güvenlik
SECRET_KEY=çok_güçlü_rastgele_bir_anahtar_buraya_32_karakter_minimum
DEBUG=False
ENVIRONMENT=production

# Veritabanı
POSTGRES_PASSWORD=güvenli_veritabanı_şifresi_buraya

# API Anahtarları (zorunlu)
GEMINI_API_KEY=your-gemini-api-key-here
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-api-secret

# E-posta (alarm bildirimleri için)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Opsiyonel API anahtarları
COINGECKO_API_KEY=
TWITTER_BEARER_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
```

**Güçlü SECRET_KEY oluşturmak için:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Docker Container'ları Başlatın

```bash
# Production modunda başlatın
docker compose up -d

# Logları takip edin
docker compose logs -f
```

### 7. Kurulumu Doğrulayın

```bash
# Container'ların çalıştığını kontrol edin
docker compose ps

# API'nin çalıştığını test edin
curl http://localhost:8000/health

# Veya tarayıcıdan:
# http://sunucu-ip-adresi:8000/docs
```

### 8. Firewall Ayarları (Opsiyonel ama Önerilen)

```bash
# UFW firewall'u aktif edin
sudo ufw enable

# SSH portunu açın (bağlantınız kopmasın!)
sudo ufw allow 22/tcp

# HTTP ve HTTPS portlarını açın
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# API portu (geçici, production'da nginx arkasında olmalı)
sudo ufw allow 8000/tcp

# Frontend portu
sudo ufw allow 3000/tcp

# Firewall durumunu kontrol edin
sudo ufw status
```

## 🔧 Manuel Kurulum (Docker Olmadan)

### 1. Python 3.11 Kurun

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 2. Sistem Bağımlılıklarını Kurun

```bash
sudo apt install -y \
    build-essential \
    gcc \
    g++ \
    make \
    wget \
    curl \
    git \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    redis-server
```

### 3. TA-Lib Kurun

```bash
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
cd ~
```

### 4. PostgreSQL Yapılandırın

```bash
# PostgreSQL'i başlatın
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Veritabanı oluşturun
sudo -u postgres psql -c "CREATE DATABASE crypto_analysis;"
sudo -u postgres psql -c "CREATE USER crypto_user WITH PASSWORD 'güvenli_şifre';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE crypto_analysis TO crypto_user;"
```

### 5. Redis Yapılandırın

```bash
# Redis'i başlatın
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Redis'in çalıştığını kontrol edin
redis-cli ping
# Yanıt: PONG
```

### 6. Projeyi Kurun

```bash
# Proje dizinine gidin
cd ~/crypto-analysis-system

# Python sanal ortamı oluşturun
python3.11 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Çevre Değişkenlerini Yapılandırın

```bash
cp .env.example .env
nano .env

# Manuel kurulum için özel ayarlar:
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

### 8. Veritabanı Migrasyonlarını Çalıştırın

```bash
python migrate.py
```

### 9. Uygulamayı Başlatın

```bash
# Başlangıç kontrollerini çalıştır
python startup.py

# API sunucusunu başlat (arka planda)
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# Celery worker başlat (arka planda)
nohup celery -A utils.celery_app worker --loglevel=info > logs/celery_worker.log 2>&1 &

# Celery beat başlat (arka planda)
nohup celery -A utils.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
```

### 10. Systemd Servisleri Oluşturun (Önerilen)

API servisi için:

```bash
sudo nano /etc/systemd/system/crypto-api.service
```

İçeriği:
```ini
[Unit]
Description=Crypto Analysis API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=kullanici-adi
WorkingDirectory=/home/kullanici-adi/crypto-analysis-system
Environment="PATH=/home/kullanici-adi/crypto-analysis-system/venv/bin"
ExecStart=/home/kullanici-adi/crypto-analysis-system/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Celery worker servisi:

```bash
sudo nano /etc/systemd/system/crypto-celery-worker.service
```

İçeriği:
```ini
[Unit]
Description=Crypto Analysis Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=kullanici-adi
WorkingDirectory=/home/kullanici-adi/crypto-analysis-system
Environment="PATH=/home/kullanici-adi/crypto-analysis-system/venv/bin"
ExecStart=/home/kullanici-adi/crypto-analysis-system/venv/bin/celery -A utils.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Celery beat servisi:

```bash
sudo nano /etc/systemd/system/crypto-celery-beat.service
```

İçeriği:
```ini
[Unit]
Description=Crypto Analysis Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=kullanici-adi
WorkingDirectory=/home/kullanici-adi/crypto-analysis-system
Environment="PATH=/home/kullanici-adi/crypto-analysis-system/venv/bin"
ExecStart=/home/kullanici-adi/crypto-analysis-system/venv/bin/celery -A utils.celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Servisleri aktif edin:

```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-api crypto-celery-worker crypto-celery-beat
sudo systemctl start crypto-api crypto-celery-worker crypto-celery-beat

# Durumu kontrol edin
sudo systemctl status crypto-api
sudo systemctl status crypto-celery-worker
sudo systemctl status crypto-celery-beat
```

## 🌐 Nginx ile Reverse Proxy (Production için Önerilen)

### 1. Nginx Kurun

```bash
sudo apt install -y nginx
```

### 2. Nginx Yapılandırması

```bash
sudo nano /etc/nginx/sites-available/crypto-analysis
```

İçeriği:
```nginx
server {
    listen 80;
    server_name sunucu-ip-veya-domain.com;

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (eğer varsa)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3. Nginx'i Aktif Edin

```bash
# Yapılandırmayı aktif edin
sudo ln -s /etc/nginx/sites-available/crypto-analysis /etc/nginx/sites-enabled/

# Varsayılan siteyi devre dışı bırakın
sudo rm /etc/nginx/sites-enabled/default

# Yapılandırmayı test edin
sudo nginx -t

# Nginx'i yeniden başlatın
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 4. SSL Sertifikası (Let's Encrypt - Ücretsiz)

```bash
# Certbot kurun
sudo apt install -y certbot python3-certbot-nginx

# SSL sertifikası alın
sudo certbot --nginx -d sunucu-domain.com

# Otomatik yenileme test edin
sudo certbot renew --dry-run
```

## 📊 İzleme ve Bakım

### Logları Görüntüleme

**Docker ile:**
```bash
# Tüm loglar
docker compose logs -f

# Sadece API logları
docker compose logs -f api

# Son 100 satır
docker compose logs --tail=100 api
```

**Manuel kurulum:**
```bash
# API logları
tail -f logs/api.log

# Celery logları
tail -f logs/celery_worker.log

# Systemd servisleri
sudo journalctl -u crypto-api -f
sudo journalctl -u crypto-celery-worker -f
```

### Container'ları Yeniden Başlatma

```bash
# Tüm servisleri yeniden başlat
docker compose restart

# Sadece API'yi yeniden başlat
docker compose restart api

# Servisleri durdur
docker compose down

# Servisleri başlat
docker compose up -d
```

### Güncelleme

```bash
# Kodu güncelleyin
git pull origin main

# Docker ile
docker compose down
docker compose build --no-cache
docker compose up -d

# Manuel kurulum
source venv/bin/activate
pip install -r requirements.txt
python migrate.py
sudo systemctl restart crypto-api crypto-celery-worker crypto-celery-beat
```

### Yedekleme

```bash
# Veritabanı yedeği
docker compose exec postgres pg_dump -U postgres crypto_analysis > backup_$(date +%Y%m%d).sql

# Manuel kurulum
sudo -u postgres pg_dump crypto_analysis > backup_$(date +%Y%m%d).sql

# .env dosyası yedeği
cp .env .env.backup
```

## 🔍 Sorun Giderme

### Container Başlamıyor

```bash
# Logları kontrol edin
docker compose logs

# Container durumunu kontrol edin
docker compose ps

# Container'ı yeniden oluşturun
docker compose down
docker compose up -d --force-recreate
```

### Veritabanı Bağlantı Hatası

```bash
# PostgreSQL'in çalıştığını kontrol edin
docker compose exec postgres pg_isready

# Manuel kurulum
sudo systemctl status postgresql
```

### Redis Bağlantı Hatası

```bash
# Redis'in çalıştığını kontrol edin
docker compose exec redis redis-cli ping

# Manuel kurulum
redis-cli ping
```

### Port Zaten Kullanımda

```bash
# Portu kullanan process'i bulun
sudo lsof -i :8000

# Process'i durdurun
sudo kill -9 <PID>
```

### Disk Alanı Doldu

```bash
# Docker temizliği
docker system prune -a

# Log dosyalarını temizle
sudo find /var/log -type f -name "*.log" -mtime +30 -delete
```

## 🔒 Güvenlik Önerileri

1. **Firewall kullanın** - Sadece gerekli portları açın
2. **SSH anahtarı kullanın** - Şifre ile giriş yerine
3. **Fail2ban kurun** - Brute force saldırılarına karşı
4. **Düzenli güncellemeler** - Sistem ve paketleri güncel tutun
5. **Güçlü şifreler** - Tüm servisler için
6. **SSL kullanın** - HTTPS ile şifreli bağlantı
7. **Logları izleyin** - Anormal aktiviteleri takip edin
8. **Yedekleme** - Düzenli veritabanı yedekleri

## 📞 Yardım

Sorun yaşarsanız:

1. Logları kontrol edin
2. GitHub Issues'da arayın
3. Yeni issue açın
4. Dokümantasyonu okuyun: README.md, ENV_VARIABLES.md

## 🎉 Başarılı Kurulum!

Kurulum tamamlandıktan sonra:

- **API**: http://sunucu-ip:8000
- **API Docs**: http://sunucu-ip:8000/docs
- **Frontend**: http://sunucu-ip:3000

İlk analizinizi yapmak için API dokümantasyonunu kullanabilirsiniz!
