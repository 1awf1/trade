# Kripto Para Analiz Sistemi - Frontend

Modern, responsive React uygulaması. Tailwind CSS ile stillendirilmiş, mobil uyumlu tasarım.

## Özellikler

- ✅ Responsive tasarım (mobil, tablet, desktop)
- ✅ Dark mode desteği
- ✅ Modern UI bileşenleri
- ✅ TradingView Lightweight Charts entegrasyonu
- ✅ Recharts ile performans grafikleri
- ✅ React Router ile sayfa yönlendirme
- ✅ Zustand ile state yönetimi
- ✅ Axios ile API iletişimi

## Kurulum

```bash
cd frontend
npm install
```

## Geliştirme

```bash
npm run dev
```

Uygulama http://localhost:3000 adresinde çalışacaktır.

## Build

```bash
npm run build
```

Build dosyaları `dist/` klasöründe oluşturulur.

## Responsive Breakpoints

Tailwind CSS breakpoints kullanılmaktadır:

- `sm`: 640px (mobil landscape)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)

## Sayfalar

1. **Ana Sayfa** (`/`) - Coin seçimi ve analiz başlatma
2. **Analiz Sonuçları** (`/analysis/:id`) - Detaylı analiz görüntüleme
3. **Portföy** (`/portfolio`) - Portföy yönetimi ve performans takibi
4. **Alarmlar** (`/alarms`) - Alarm oluşturma ve yönetimi
5. **Backtesting** (`/backtesting`) - Strateji testi
6. **Geçmiş** (`/history`) - Analiz geçmişi ve karşılaştırma

## Responsive Tasarım Özellikleri

### Mobil (< 768px)
- Tek sütunlu layout
- Hamburger menü (gelecekte eklenebilir)
- Touch-friendly butonlar
- Optimize edilmiş tablo görünümü

### Tablet (768px - 1024px)
- İki sütunlu grid layout
- Yan yana kartlar
- Optimize edilmiş navigasyon

### Desktop (> 1024px)
- Çoklu sütun layout
- Geniş tablolar
- Detaylı görünümler

## Tailwind CSS Kullanımı

Özel utility class'lar:

```css
.btn-primary - Birincil buton stili
.btn-secondary - İkincil buton stili
.card - Kart container
.input - Form input stili
```

## API Entegrasyonu

Backend API'ye proxy üzerinden bağlanır:

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

## State Yönetimi

Zustand kullanılarak minimal ve performanslı state yönetimi:

```javascript
const useStore = create((set) => ({
  currentAnalysis: null,
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  // ...
}))
```

## Performans Optimizasyonu

- Lazy loading (gelecekte eklenebilir)
- Code splitting
- Optimized images
- Minimal bundle size
