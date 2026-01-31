# Katkıda Bulunma Rehberi

Kripto Para Analiz Sistemi'ne katkıda bulunmak istediğiniz için teşekkür ederiz! Bu dokümanda katkıda bulunma sürecini ve kurallarını bulabilirsiniz.

## İçindekiler

- [Davranış Kuralları](#davranış-kuralları)
- [Nasıl Katkıda Bulunabilirim?](#nasıl-katkıda-bulunabilirim)
- [Geliştirme Ortamı Kurulumu](#geliştirme-ortamı-kurulumu)
- [Kod Standartları](#kod-standartları)
- [Test Yazma](#test-yazma)
- [Pull Request Süreci](#pull-request-süreci)
- [Issue Raporlama](#issue-raporlama)

## Davranış Kuralları

Bu projede herkes için saygılı ve kapsayıcı bir ortam sağlamayı taahhüt ediyoruz. Lütfen:

- Saygılı ve yapıcı olun
- Farklı bakış açılarına açık olun
- Eleştirileri yapıcı bir şekilde kabul edin
- Topluluk için en iyisine odaklanın

## Nasıl Katkıda Bulunabilirim?

### Bug Raporlama

Bug bulduysanız:

1. Önce [Issues](https://github.com/your-username/crypto-analysis-system/issues) sayfasında benzer bir issue olup olmadığını kontrol edin
2. Yoksa yeni bir issue açın ve şunları ekleyin:
   - Açıklayıcı bir başlık
   - Hatayı yeniden oluşturma adımları
   - Beklenen davranış
   - Gerçekleşen davranış
   - Sistem bilgileri (OS, Python versiyonu, vb.)
   - Hata mesajları ve loglar

### Özellik Önerme

Yeni bir özellik önermek için:

1. [Issues](https://github.com/your-username/crypto-analysis-system/issues) sayfasında benzer bir öneri olup olmadığını kontrol edin
2. Yeni bir issue açın ve şunları açıklayın:
   - Özelliğin amacı
   - Kullanım senaryoları
   - Olası implementasyon yaklaşımı
   - Alternatifler

### Kod Katkısı

Kod katkısında bulunmak için:

1. Repo'yu fork edin
2. Feature branch oluşturun
3. Değişikliklerinizi yapın
4. Testler ekleyin
5. Pull request açın

## Geliştirme Ortamı Kurulumu

### 1. Repo'yu Fork ve Clone Edin

```bash
# Fork edin (GitHub web arayüzünden)
# Clone edin
git clone https://github.com/YOUR-USERNAME/crypto-analysis-system.git
cd crypto-analysis-system

# Upstream remote ekleyin
git remote add upstream https://github.com/original-username/crypto-analysis-system.git
```

### 2. Development Ortamını Kurun

```bash
# Python sanal ortamı oluşturun
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Development bağımlılıklarını yükleyin
pip install pytest pytest-cov black flake8 mypy
```

### 3. Docker ile Development

```bash
# Development ortamını başlatın
docker-compose -f docker-compose.dev.yml up -d

# Logları takip edin
docker-compose logs -f
```

### 4. Pre-commit Hooks (Opsiyonel)

```bash
pip install pre-commit
pre-commit install
```

## Kod Standartları

### Python Kod Stili

- **PEP 8** standartlarına uyun
- **Black** ile kod formatlama (line length: 120)
- **Flake8** ile linting
- **Type hints** kullanın (Python 3.10+)

```bash
# Kod formatlama
black . --line-length=120

# Linting
flake8 . --max-line-length=127

# Type checking
mypy .
```

### Docstring Formatı

Google style docstrings kullanın:

```python
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of price values
        period: RSI period (default: 14)
    
    Returns:
        RSI value between 0 and 100
    
    Raises:
        ValueError: If prices list is empty or period is invalid
    
    Example:
        >>> prices = [100, 102, 101, 103, 105]
        >>> rsi = calculate_rsi(prices)
        >>> print(f"RSI: {rsi:.2f}")
    """
    pass
```

### Commit Mesajları

Açıklayıcı commit mesajları yazın:

```
feat: Add RSI divergence detection
fix: Fix database connection timeout
docs: Update installation instructions
test: Add property tests for signal generator
refactor: Simplify technical analysis engine
```

Prefix'ler:
- `feat`: Yeni özellik
- `fix`: Bug düzeltme
- `docs`: Dokümantasyon
- `test`: Test ekleme/düzeltme
- `refactor`: Kod refactoring
- `style`: Kod formatı
- `perf`: Performans iyileştirme
- `chore`: Bakım işleri

## Test Yazma

### Test Türleri

1. **Unit Tests**: Spesifik fonksiyonları test eder
2. **Property-Based Tests**: Evrensel özellikleri test eder (Hypothesis)
3. **Integration Tests**: Bileşenler arası etkileşimi test eder

### Test Yazma Kuralları

```python
import pytest
from hypothesis import given, strategies as st

# Unit test örneği
def test_calculate_rsi_basic():
    """Test RSI calculation with known values."""
    prices = [44, 44.34, 44.09, 43.61, 44.33]
    rsi = calculate_rsi(prices, period=14)
    assert 0 <= rsi <= 100

# Property-based test örneği
@given(st.lists(st.floats(min_value=1, max_value=1000), min_size=20))
def test_rsi_range_property(prices):
    """Property: RSI should always be between 0 and 100."""
    rsi = calculate_rsi(prices)
    assert 0 <= rsi <= 100
```

### Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest

# Verbose mod
pytest -v

# Coverage ile
pytest --cov=. --cov-report=html

# Sadece property-based testler
pytest -k "property"

# Belirli bir dosya
pytest tests/test_technical_analysis.py
```

### Test Coverage

- Yeni kod için en az %80 coverage hedefleyin
- Critical path'ler için %100 coverage
- Property-based testler ekleyin

## Pull Request Süreci

### 1. Branch Oluşturun

```bash
# Upstream'den güncellemeleri çekin
git fetch upstream
git checkout main
git merge upstream/main

# Feature branch oluşturun
git checkout -b feature/amazing-feature
```

### 2. Değişikliklerinizi Yapın

```bash
# Kod yazın
# Testler ekleyin
# Dokümantasyon güncelleyin

# Değişiklikleri commit edin
git add .
git commit -m "feat: Add amazing feature"
```

### 3. Testleri Çalıştırın

```bash
# Tüm testlerin geçtiğinden emin olun
pytest

# Kod formatını kontrol edin
black . --check
flake8 .
```

### 4. Push ve PR Açın

```bash
# Branch'i push edin
git push origin feature/amazing-feature

# GitHub'da Pull Request açın
```

### PR Checklist

Pull request açmadan önce kontrol edin:

- [ ] Tüm testler geçiyor
- [ ] Yeni testler eklendi
- [ ] Dokümantasyon güncellendi
- [ ] Kod formatı uygun (black, flake8)
- [ ] Commit mesajları açıklayıcı
- [ ] CHANGELOG.md güncellendi (major değişiklikler için)
- [ ] Breaking changes dokümante edildi

### PR Açıklaması

PR açıklamanızda şunları ekleyin:

```markdown
## Değişiklik Özeti
Kısa açıklama

## Değişiklik Türü
- [ ] Bug fix
- [ ] Yeni özellik
- [ ] Breaking change
- [ ] Dokümantasyon

## Test Edildi mi?
- [ ] Evet
- [ ] Hayır

## Checklist
- [ ] Testler eklendi
- [ ] Dokümantasyon güncellendi
- [ ] Kod formatı uygun
```

## Issue Raporlama

### Bug Report Template

```markdown
**Bug Açıklaması**
Açık ve kısa bug açıklaması.

**Yeniden Oluşturma Adımları**
1. '...' sayfasına git
2. '....' butonuna tıkla
3. Aşağı kaydır
4. Hatayı gör

**Beklenen Davranış**
Ne olmasını bekliyordunuz?

**Gerçekleşen Davranış**
Ne oldu?

**Ekran Görüntüleri**
Varsa ekran görüntüleri ekleyin.

**Sistem Bilgileri**
- OS: [örn. Ubuntu 22.04]
- Python: [örn. 3.11]
- Docker: [örn. 20.10.21]

**Ek Bilgiler**
Diğer bilgiler.
```

### Feature Request Template

```markdown
**Özellik İsteği**
Özelliğin açık ve kısa açıklaması.

**Problem**
Hangi problemi çözüyor? [örn. Her zaman ... yapmak zorundayım]

**Önerilen Çözüm**
Nasıl çözülmesini istersiniz?

**Alternatifler**
Düşündüğünüz alternatif çözümler.

**Ek Bilgiler**
Diğer bilgiler, mockup'lar, vb.
```

## Kod Review Süreci

Pull request'iniz açıldıktan sonra:

1. Otomatik testler çalışır (CI/CD)
2. Maintainer'lar kodu review eder
3. Gerekirse değişiklik talep edilir
4. Onaylandıktan sonra merge edilir

### Review Kriterleri

- Kod kalitesi ve okunabilirlik
- Test coverage
- Dokümantasyon
- Performans etkileri
- Güvenlik etkileri
- Breaking changes

## Sorularınız mı Var?

- GitHub Discussions kullanın
- Issue açın
- Email: dev@cryptoanalysis.com

## Teşekkürler!

Katkılarınız için teşekkür ederiz! 🎉
