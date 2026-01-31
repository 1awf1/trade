"""
AI Interpreter Engine for generating natural language explanations of analysis results.
Implements Google Gemini API integration with Turkish language support and technical term explanations.
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
try:
    import google.generativeai as genai
except ImportError:
    import google.genai as genai
from utils.logger import logger
from models.schemas import (
    IndicatorResults, OverallSentiment, Signal, SignalExplanation,
    SignalType, SentimentClassification, TrendDirection
)


class AIInterpreter:
    """
    AI Interpreter for cryptocurrency analysis results.
    Generates natural language explanations in Turkish with technical term definitions.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_local_llm: bool = False):
        """
        Initialize AI Interpreter.
        
        Args:
            api_key: Google Gemini API key (if None, reads from environment)
            use_local_llm: If True, use local LLM instead of Gemini (not implemented yet)
        """
        self.use_local_llm = use_local_llm
        self.model = None
        self.model_name = "gemini-2.5-flash"  # Using stable Gemini 2.5 Flash model
        
        # Technical terms dictionary (Turkish)
        self.technical_terms = self._initialize_technical_terms()
        
        if not use_local_llm:
            # Initialize Gemini client
            api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("Gemini API key not provided. AI interpretation will be limited.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(self.model_name)
                    logger.info(f"AI Interpreter initialized with Google Gemini model: {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    self.model = None
        else:
            logger.info("AI Interpreter initialized with local LLM (not yet implemented)")
    
    def _initialize_technical_terms(self) -> Dict[str, str]:
        """
        Initialize technical terms dictionary with Turkish explanations.
        
        Returns:
            Dictionary mapping technical terms to their explanations
        
        Validates: Gereksinim 9.5 - Teknik terim açıklaması
        """
        return {
            # Technical Indicators
            "RSI": "RSI (Relative Strength Index - Göreceli Güç Endeksi): Fiyat hareketlerinin hızını ve değişimini ölçen momentum göstergesi. 0-100 arası değer alır. 30'un altı aşırı satım (oversold), 70'in üstü aşırı alım (overbought) bölgesi olarak kabul edilir.",
            
            "MACD": "MACD (Moving Average Convergence Divergence - Hareketli Ortalama Yakınsama Uzaklaşma): İki hareketli ortalama arasındaki ilişkiyi gösteren trend takip göstergesi. MACD çizgisi sinyal çizgisini yukarı keserse yükseliş, aşağı keserse düşüş sinyali verir.",
            
            "Bollinger Bands": "Bollinger Bantları: Fiyatın volatilitesini gösteren üç çizgiden oluşan gösterge. Orta bant hareketli ortalama, üst ve alt bantlar ise standart sapma ile hesaplanır. Fiyat bantların dışına çıktığında aşırı alım/satım durumu oluşabilir.",
            
            "Moving Average": "Hareketli Ortalama (MA): Belirli bir dönemdeki fiyatların ortalamasını alarak trend yönünü gösteren gösterge. SMA (Basit Hareketli Ortalama) ve EMA (Üstel Hareketli Ortalama) en yaygın türleridir.",
            
            "EMA": "EMA (Exponential Moving Average - Üstel Hareketli Ortalama): Son fiyatlara daha fazla ağırlık veren hareketli ortalama türü. Fiyat değişimlerine SMA'dan daha hızlı tepki verir.",
            
            "Stochastic": "Stochastic Osilatör: Fiyatın belirli bir dönemdeki en yüksek ve en düşük değerleri arasındaki konumunu gösteren momentum göstergesi. 0-100 arası değer alır. 20'nin altı aşırı satım, 80'in üstü aşırı alım bölgesidir.",
            
            "ATR": "ATR (Average True Range - Ortalama Gerçek Aralık): Piyasanın volatilitesini (oynaklığını) ölçen gösterge. Yüksek ATR değeri yüksek volatilite, düşük ATR değeri düşük volatilite anlamına gelir. Stop-loss ve take-profit seviyelerini belirlemede kullanılır.",
            
            "VWAP": "VWAP (Volume Weighted Average Price - Hacim Ağırlıklı Ortalama Fiyat): Gün içi işlemlerde hacim ve fiyatı birleştirerek hesaplanan ortalama. Fiyat VWAP'ın üzerindeyse alıcılar, altındaysa satıcılar baskındır.",
            
            "OBV": "OBV (On-Balance Volume - Birikimli Hacim): Fiyat hareketlerinin hacim ile desteklenip desteklenmediğini gösteren gösterge. Fiyat yükselirken OBV de yükseliyorsa hareket sağlıklıdır.",
            
            "Fibonacci": "Fibonacci Düzeltme Seviyeleri: Fiyatın geri çekilme (retracement) seviyelerini belirlemek için kullanılan matematiksel oran dizisi. %23.6, %38.2, %50, %61.8 gibi seviyeler destek ve direnç noktaları olarak kullanılır.",
            
            # Chart Patterns
            "Golden Cross": "Golden Cross (Altın Haç): EMA 50'nin EMA 200'ü yukarı kesmesi durumu. Güçlü yükseliş (bullish) sinyali olarak kabul edilir ve uzun vadeli trend değişimini gösterebilir.",
            
            "Death Cross": "Death Cross (Ölüm Haçı): EMA 50'nin EMA 200'ü aşağı kesmesi durumu. Güçlü düşüş (bearish) sinyali olarak kabul edilir ve uzun vadeli trend değişimini gösterebilir.",
            
            "Divergence": "Divergence (Uyuşmazlık): Fiyat hareketi ile gösterge hareketi arasındaki uyumsuzluk. Pozitif divergence (fiyat düşerken gösterge yükselir) yükseliş, negatif divergence (fiyat yükselirken gösterge düşer) düşüş sinyali verebilir.",
            
            "Support": "Destek Seviyesi: Fiyatın düşüş trendinde durma ve yükselişe geçme eğilimi gösterdiği fiyat seviyesi. Alıcıların baskın olduğu bölgedir.",
            
            "Resistance": "Direnç Seviyesi: Fiyatın yükseliş trendinde durma ve düşüşe geçme eğilimi gösterdiği fiyat seviyesi. Satıcıların baskın olduğu bölgedir.",
            
            "Confluence": "Confluence (Uyum): Birden fazla teknik göstergenin aynı yönde sinyal vermesi durumu. Yüksek confluence, sinyalin güvenilirliğini artırır.",
            
            # Trading Terms
            "Stop-Loss": "Stop-Loss (Zarar Durdur): Kayıpları sınırlamak için belirlenen otomatik satış emri seviyesi. Fiyat bu seviyeye ulaştığında pozisyon otomatik olarak kapatılır.",
            
            "Take-Profit": "Take-Profit (Kar Al): Karı realize etmek için belirlenen otomatik satış emri seviyesi. Fiyat bu seviyeye ulaştığında pozisyon otomatik olarak kapatılır ve kar elde edilir.",
            
            "Volatility": "Volatilite (Oynaklık): Fiyatın ne kadar hızlı ve büyük oranda değiştiğini gösteren ölçü. Yüksek volatilite hem fırsat hem de risk anlamına gelir.",
            
            "Bullish": "Bullish (Yükseliş Yönlü): Fiyatın yükseleceği beklentisi veya yükseliş trendi. Boğa piyasası (bull market) terimi buradan gelir.",
            
            "Bearish": "Bearish (Düşüş Yönlü): Fiyatın düşeceği beklentisi veya düşüş trendi. Ayı piyasası (bear market) terimi buradan gelir.",
            
            "Oversold": "Oversold (Aşırı Satım): Fiyatın çok hızlı düştüğü ve geri dönüş (yükseliş) olasılığının arttığı durum. RSI < 30 veya Stochastic < 20 gibi göstergelerle tespit edilir.",
            
            "Overbought": "Overbought (Aşırı Alım): Fiyatın çok hızlı yükseldiği ve geri çekilme (düşüş) olasılığının arttığı durum. RSI > 70 veya Stochastic > 80 gibi göstergelerle tespit edilir.",
            
            # Sentiment Terms
            "Sentiment": "Piyasa Duygusu (Market Sentiment): Yatırımcıların ve piyasa katılımcılarının genel ruh hali ve beklentileri. Pozitif duygu yükseliş, negatif duygu düşüş beklentisi anlamına gelir.",
            
            "FUD": "FUD (Fear, Uncertainty, Doubt - Korku, Belirsizlik, Şüphe): Piyasada panik yaratmak için yayılan olumsuz haberler veya söylentiler.",
            
            "FOMO": "FOMO (Fear Of Missing Out - Kaçırma Korkusu): Yatırımcıların fırsatı kaçırma korkusuyla acelece alım yapması durumu. Genellikle fiyat zirvelerinde görülür."
        }
    
    def _detect_technical_terms(self, text: str) -> List[str]:
        """
        Detect technical terms used in the text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of detected technical terms
        """
        detected_terms = []
        text_upper = text.upper()
        
        for term in self.technical_terms.keys():
            # Check if term appears in text (case-insensitive)
            if term.upper() in text_upper:
                detected_terms.append(term)
        
        return detected_terms
    
    def _add_term_explanations(self, text: str, detected_terms: List[str]) -> str:
        """
        Add explanations for detected technical terms to the text.
        
        Args:
            text: Original text
            detected_terms: List of detected technical terms
        
        Returns:
            Text with term explanations appended
        
        Validates: Gereksinim 9.5 - Teknik terim açıklaması
        """
        if not detected_terms:
            return text
        
        # Add explanations section
        explanations = "\n\n📚 **Teknik Terimler Sözlüğü:**\n\n"
        
        for term in detected_terms:
            if term in self.technical_terms:
                explanations += f"• **{term}**: {self.technical_terms[term]}\n\n"
        
        return text + explanations

    def _create_technical_analysis_prompt(self, indicators: IndicatorResults) -> str:
        """
        Create prompt for technical analysis interpretation.
        
        Args:
            indicators: Technical indicator results
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Sen bir kripto para teknik analiz uzmanısın. Aşağıdaki teknik analiz sonuçlarını Türkçe olarak açıkla.

**Teknik Göstergeler:**

RSI: {indicators.rsi:.2f} ({indicators.rsi_signal})
{f"RSI Divergence: {indicators.rsi_divergence}" if indicators.rsi_divergence else ""}

MACD: 
- MACD Line: {indicators.macd.macd:.4f}
- Signal Line: {indicators.macd.signal:.4f}
- Histogram: {indicators.macd.histogram:.4f}
- Sinyal: {indicators.macd_signal}

Bollinger Bands:
- Üst Bant: {indicators.bollinger.upper:.2f}
- Orta Bant: {indicators.bollinger.middle:.2f}
- Alt Bant: {indicators.bollinger.lower:.2f}
- Sinyal: {indicators.bollinger_signal}

Hareketli Ortalamalar:
- SMA 50: {indicators.moving_averages.sma_50:.2f}
- SMA 200: {indicators.moving_averages.sma_200:.2f}
- EMA 50: {indicators.ema_50:.2f}
- EMA 200: {indicators.ema_200:.2f}
- Sinyal: {indicators.ma_signal}
{f"- {indicators.golden_death_cross.replace('_', ' ').title()} tespit edildi!" if indicators.golden_death_cross else ""}

Stochastic Oscillator:
- K: {indicators.stochastic.k:.2f}
- D: {indicators.stochastic.d:.2f}
- Sinyal: {indicators.stochastic_signal}

ATR (Volatilite):
- ATR: {indicators.atr.atr:.2f} ({indicators.atr.atr_percent:.2f}% of price)
- Volatilite Seviyesi: {"Yüksek" if indicators.atr.percentile > 0.7 else "Normal" if indicators.atr.percentile > 0.3 else "Düşük"}
- Stop-Loss Önerisi: {indicators.atr_stop_loss:.2f}
- Take-Profit Önerisi: {indicators.atr_take_profit:.2f}

VWAP: {indicators.vwap:.2f} (Fiyat VWAP'ın {indicators.vwap_signal})

OBV: {indicators.obv:.0f} ({indicators.obv_signal})

Fibonacci Seviyeleri:
- 0% (Swing High): {indicators.fibonacci_levels.level_0:.2f}
- 23.6%: {indicators.fibonacci_levels.level_236:.2f}
- 38.2%: {indicators.fibonacci_levels.level_382:.2f}
- 50%: {indicators.fibonacci_levels.level_500:.2f}
- 61.8%: {indicators.fibonacci_levels.level_618:.2f}
- 100% (Swing Low): {indicators.fibonacci_levels.level_100:.2f}

Confluence Score: {indicators.confluence_score:.2f} (İndikatör uyumu)
EMA 200 Trend Filtresi: {indicators.ema_200_trend_filter}

Destek Seviyeleri: {', '.join([f'{level:.2f}' for level in indicators.support_levels[:3]])}
Direnç Seviyeleri: {', '.join([f'{level:.2f}' for level in indicators.resistance_levels[:3]])}

Lütfen bu teknik göstergeleri yorumla ve şunları içeren bir analiz yaz:
1. Mevcut teknik durum özeti (2-3 cümle)
2. Öne çıkan göstergeler ve anlamları
3. Potansiyel fiyat hareketleri
4. Dikkat edilmesi gereken seviyeler

Açıklaman net, anlaşılır ve Türkçe olsun. Teknik terimleri kullan ama karmaşık jargondan kaçın."""

        return prompt
    
    def _create_fundamental_analysis_prompt(self, sentiment: OverallSentiment) -> str:
        """
        Create prompt for fundamental analysis interpretation.
        
        Args:
            sentiment: Overall sentiment results
        
        Returns:
            Formatted prompt string
        """
        # Format source details
        source_details = []
        for source in sentiment.sources:
            source_details.append(
                f"- {source.source.title()}: Skor {source.sentiment_score:.2f}, "
                f"Güven {source.confidence:.2f}, Örneklem {source.sample_size}"
            )
        
        sources_text = "\n".join(source_details)
        
        prompt = f"""Sen bir kripto para piyasa analisti ve duygu analizi uzmanısın. Aşağıdaki temel analiz sonuçlarını Türkçe olarak açıkla.

**Piyasa Duygusu Analizi:**

Genel Duygu Skoru: {sentiment.overall_score:.2f} (Aralık: -1 ile +1 arası)
Sınıflandırma: {sentiment.classification.value.upper()}
Trend: {sentiment.trend.value.upper()}

**Kaynak Bazlı Detaylar:**
{sources_text}

Lütfen bu duygu analizi sonuçlarını yorumla ve şunları içeren bir özet yaz:
1. Genel piyasa duygusunun değerlendirmesi
2. Farklı kaynakların (sosyal medya, haber) uyumu veya çelişkisi
3. Duygu trendinin anlamı (yükseliş/düşüş/sabit)
4. Yatırımcı psikolojisi hakkında çıkarımlar

Açıklaman net, anlaşılır ve Türkçe olsun."""

        return prompt
    
    def _create_comprehensive_report_prompt(
        self,
        signal: Signal,
        explanation: SignalExplanation,
        indicators: IndicatorResults,
        sentiment: OverallSentiment
    ) -> str:
        """
        Create prompt for comprehensive analysis report.
        
        Args:
            signal: Generated trading signal
            explanation: Signal explanation
            indicators: Technical indicator results
            sentiment: Overall sentiment results
        
        Returns:
            Formatted prompt string
        """
        # Format supporting and conflicting indicators
        supporting = ", ".join(explanation.supporting_indicators) if explanation.supporting_indicators else "Yok"
        conflicting = ", ".join(explanation.conflicting_indicators) if explanation.conflicting_indicators else "Yok"
        
        # Format risk factors
        risks = "\n".join([f"- {risk}" for risk in explanation.risk_factors]) if explanation.risk_factors else "- Önemli risk faktörü tespit edilmedi"
        
        prompt = f"""Sen bir profesyonel kripto para analisti ve yatırım danışmanısın. Aşağıdaki kapsamlı analiz sonuçlarına dayanarak Türkçe bir rapor hazırla.

**ANALİZ ÖZETİ:**
Coin: {signal.coin}
Zaman Dilimi: {signal.timeframe}
Tarih: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**SİNYAL:**
Sinyal Türü: {signal.signal_type.value}
Başarı İhtimali: %{signal.success_probability:.1f}
Stop-Loss: {signal.stop_loss:.2f} USD
Take-Profit: {signal.take_profit:.2f} USD

**TEKNİK ANALİZ:**
Destekleyen Göstergeler: {supporting}
Çelişen Göstergeler: {conflicting}
Confluence Score: {indicators.confluence_score:.2f}
EMA 200 Filtresi: {signal.ema_200_filter_applied}
{f"Golden/Death Cross: {signal.golden_death_cross_detected}" if signal.golden_death_cross_detected else ""}
{f"RSI Divergence: {signal.rsi_divergence_detected}" if signal.rsi_divergence_detected else ""}

**TEMEL ANALİZ:**
Piyasa Duygusu: {sentiment.classification.value.upper()} (Skor: {sentiment.overall_score:.2f})
Duygu Trendi: {sentiment.trend.value.upper()}

**RİSK FAKTÖRLERİ:**
{risks}

**GÖREV:**
Yukarıdaki bilgilere dayanarak, yatırımcılar için kapsamlı bir analiz raporu hazırla. Rapor şunları içermeli:

1. **Yönetici Özeti** (2-3 cümle): Mevcut durumun ve sinyalin kısa özeti

2. **Teknik Analiz Değerlendirmesi** (1 paragraf):
   - Öne çıkan teknik göstergeler
   - Destek ve direnç seviyeleri
   - Trend analizi

3. **Piyasa Duygusu Değerlendirmesi** (1 paragraf):
   - Sosyal medya ve haber analizi
   - Yatırımcı psikolojisi
   - Duygu trendinin etkisi

4. **Sinyal Gerekçesi** (1 paragraf):
   - Neden bu sinyal üretildi?
   - Hangi faktörler en önemli?
   - Başarı ihtimalinin temeli nedir?

5. **Risk Yönetimi Önerileri** (madde işaretli liste):
   - Stop-loss ve take-profit kullanımı
   - Pozisyon büyüklüğü önerileri
   - Dikkat edilmesi gereken riskler

6. **Sonuç ve Öneriler** (2-3 cümle):
   - Genel değerlendirme
   - Yatırımcılar için net öneri

**ÖNEMLİ:**
- Rapor profesyonel ama anlaşılır olmalı
- Teknik terimleri kullan ama açıkla
- Net ve kesin ifadeler kullan
- Türkçe dilbilgisi kurallarına uy
- Yatırım tavsiyesi değil, analiz raporu olduğunu belirt
- Emoji kullanma, profesyonel bir ton kullan"""

        return prompt
    
    def interpret_technical(self, indicators: IndicatorResults) -> str:
        """
        Interpret technical analysis results in natural language.
        
        Args:
            indicators: Technical indicator results
        
        Returns:
            Turkish language interpretation of technical analysis
        
        Validates: Gereksinim 9.1 - Teknik analiz doğal dilde açıklama
        """
        if self.model is None:
            logger.warning("Gemini model not initialized, using fallback interpretation")
            return self._fallback_technical_interpretation(indicators)
        
        try:
            logger.info("Generating technical analysis interpretation with AI")
            
            # Create prompt
            prompt = self._create_technical_analysis_prompt(indicators)
            
            # Configure safety settings to be more permissive for financial analysis
            safety_settings = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=800,
                ),
                safety_settings=safety_settings
            )
            
            # Check if response has text
            if not response.text:
                logger.warning("Gemini returned empty response, using fallback")
                return self._fallback_technical_interpretation(indicators)
            
            # Extract response
            interpretation = response.text.strip()
            
            logger.info("Technical analysis interpretation generated successfully")
            return interpretation
            
        except Exception as e:
            logger.error(f"Error generating technical interpretation: {e}")
            return self._fallback_technical_interpretation(indicators)
    
    def interpret_fundamental(self, sentiment: OverallSentiment) -> str:
        """
        Interpret fundamental analysis results in natural language.
        
        Args:
            sentiment: Overall sentiment results
        
        Returns:
            Turkish language interpretation of fundamental analysis
        
        Validates: Gereksinim 9.2 - Temel analiz özeti
        """
        if self.model is None:
            logger.warning("Gemini model not initialized, using fallback interpretation")
            return self._fallback_fundamental_interpretation(sentiment)
        
        try:
            logger.info("Generating fundamental analysis interpretation with AI")
            
            # Create prompt
            prompt = self._create_fundamental_analysis_prompt(sentiment)
            
            # Configure safety settings
            safety_settings = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
            
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=600,
                ),
                safety_settings=safety_settings
            )
            
            # Check if response has text
            if not response.text:
                logger.warning("Gemini returned empty response, using fallback")
                return self._fallback_fundamental_interpretation(sentiment)
            
            # Extract response
            interpretation = response.text.strip()
            
            logger.info("Fundamental analysis interpretation generated successfully")
            return interpretation
            
        except Exception as e:
            logger.error(f"Error generating fundamental interpretation: {e}")
            return self._fallback_fundamental_interpretation(sentiment)
    
    def generate_report(
        self,
        signal: Signal,
        explanation: SignalExplanation,
        indicators: IndicatorResults,
        sentiment: OverallSentiment
    ) -> str:
        """
        Generate comprehensive analysis report in Turkish.
        
        Args:
            signal: Generated trading signal
            explanation: Signal explanation
            indicators: Technical indicator results
            sentiment: Overall sentiment results
        
        Returns:
            Comprehensive Turkish language report
        
        Validates: Gereksinim 9.3 - Kapsamlı rapor üretimi
        Validates: Gereksinim 9.4 - Türkçe çıktı
        """
        if self.model is None:
            logger.warning("Gemini model not initialized, using fallback report generation")
            return self._fallback_report_generation(signal, explanation, indicators, sentiment)
        
        try:
            logger.info("Generating comprehensive analysis report with AI")
            
            # Create prompt
            prompt = self._create_comprehensive_report_prompt(signal, explanation, indicators, sentiment)
            
            # Configure safety settings to be more permissive for financial analysis
            safety_settings = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
            
            # Call Gemini API with higher token limit for comprehensive report
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1500,
                ),
                safety_settings=safety_settings
            )
            
            # Check if response has text
            if not response.text:
                logger.warning("Gemini returned empty response, using fallback")
                return self._fallback_report_generation(signal, explanation, indicators, sentiment)
            
            # Extract response
            report = response.text.strip()
            
            # Detect technical terms in the report
            detected_terms = self._detect_technical_terms(report)
            
            # Add term explanations
            report_with_explanations = self._add_term_explanations(report, detected_terms)
            
            logger.info(f"Comprehensive report generated successfully ({len(detected_terms)} technical terms explained)")
            return report_with_explanations
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return self._fallback_report_generation(signal, explanation, indicators, sentiment)

    def _fallback_technical_interpretation(self, indicators: IndicatorResults) -> str:
        """
        Fallback method for technical interpretation when AI is unavailable.
        Uses template-based generation.
        
        Args:
            indicators: Technical indicator results
        
        Returns:
            Template-based Turkish interpretation
        """
        logger.info("Using fallback template for technical interpretation")
        
        # Determine overall trend
        bullish_count = 0
        bearish_count = 0
        
        if indicators.rsi_signal == "oversold":
            bullish_count += 1
        elif indicators.rsi_signal == "overbought":
            bearish_count += 1
        
        if indicators.macd_signal == "bullish":
            bullish_count += 1
        elif indicators.macd_signal == "bearish":
            bearish_count += 1
        
        if indicators.ma_signal == "bullish":
            bullish_count += 1
        elif indicators.ma_signal == "bearish":
            bearish_count += 1
        
        if bullish_count > bearish_count:
            trend = "yükseliş"
            trend_desc = "Teknik göstergeler genel olarak yükseliş yönünde sinyal veriyor."
        elif bearish_count > bullish_count:
            trend = "düşüş"
            trend_desc = "Teknik göstergeler genel olarak düşüş yönünde sinyal veriyor."
        else:
            trend = "kararsız"
            trend_desc = "Teknik göstergeler karışık sinyaller veriyor ve net bir yön göstermiyor."
        
        interpretation = f"""**Teknik Analiz Özeti:**

{trend_desc}

**Öne Çıkan Göstergeler:**

• RSI ({indicators.rsi:.1f}): {
    "Aşırı satım bölgesinde, potansiyel yükseliş fırsatı" if indicators.rsi < 30
    else "Aşırı alım bölgesinde, potansiyel düşüş riski" if indicators.rsi > 70
    else "Normal seviyede"
}

• MACD: {
    "Yükseliş sinyali veriyor (histogram pozitif)" if indicators.macd.histogram > 0
    else "Düşüş sinyali veriyor (histogram negatif)"
}

• Hareketli Ortalamalar: {
    "Fiyat önemli MA seviyelerinin üzerinde, yükseliş trendi" if indicators.ma_signal == "bullish"
    else "Fiyat önemli MA seviyelerinin altında, düşüş trendi" if indicators.ma_signal == "bearish"
    else "Fiyat MA seviyeleri arasında, kararsız"
}

{f"• {indicators.golden_death_cross.replace('_', ' ').title()} tespit edildi - Güçlü trend değişim sinyali!" if indicators.golden_death_cross else ""}

{f"• RSI {indicators.rsi_divergence} divergence tespit edildi - Potansiyel trend dönüşü sinyali!" if indicators.rsi_divergence else ""}

**Volatilite ve Risk:**

ATR bazlı volatilite: {
    "Yüksek (dikkatli olunmalı)" if indicators.atr.percentile > 0.7
    else "Normal seviyede" if indicators.atr.percentile > 0.3
    else "Düşük (sakin piyasa)"
}

Önerilen Stop-Loss: {indicators.atr_stop_loss:.2f} USD
Önerilen Take-Profit: {indicators.atr_take_profit:.2f} USD

**Önemli Seviyeler:**

Destek: {', '.join([f'{level:.2f}' for level in indicators.support_levels[:3]])} USD
Direnç: {', '.join([f'{level:.2f}' for level in indicators.resistance_levels[:3]])} USD

İndikatör Uyumu (Confluence): {indicators.confluence_score:.0%} - {
    "Yüksek uyum, güvenilir sinyal" if indicators.confluence_score > 0.7
    else "Orta seviye uyum" if indicators.confluence_score > 0.4
    else "Düşük uyum, dikkatli olunmalı"
}"""
        
        return interpretation
    
    def _fallback_fundamental_interpretation(self, sentiment: OverallSentiment) -> str:
        """
        Fallback method for fundamental interpretation when AI is unavailable.
        Uses template-based generation.
        
        Args:
            sentiment: Overall sentiment results
        
        Returns:
            Template-based Turkish interpretation
        """
        logger.info("Using fallback template for fundamental interpretation")
        
        # Determine sentiment strength
        if abs(sentiment.overall_score) > 0.6:
            strength = "güçlü"
        elif abs(sentiment.overall_score) > 0.3:
            strength = "orta"
        else:
            strength = "zayıf"
        
        # Sentiment description
        if sentiment.classification == SentimentClassification.POSITIVE:
            sentiment_desc = f"Piyasa duygusu {strength} şekilde POZİTİF. Yatırımcılar genel olarak iyimser ve alım yönünde."
        elif sentiment.classification == SentimentClassification.NEGATIVE:
            sentiment_desc = f"Piyasa duygusu {strength} şekilde NEGATİF. Yatırımcılar genel olarak karamsar ve satış yönünde."
        else:
            sentiment_desc = "Piyasa duygusu NÖTR. Yatırımcılar kararsız ve bekleme modunda."
        
        # Trend description
        if sentiment.trend == TrendDirection.RISING:
            trend_desc = "Duygu trendi YÜKSELİŞTE. Pozitif haberler ve sosyal medya aktivitesi artıyor."
        elif sentiment.trend == TrendDirection.FALLING:
            trend_desc = "Duygu trendi DÜŞÜŞTE. Negatif haberler ve FUD (korku, belirsizlik, şüphe) artıyor."
        else:
            trend_desc = "Duygu trendi SABİT. Piyasa dengeli ve büyük değişim yok."
        
        # Source analysis
        source_analysis = []
        for source in sentiment.sources:
            source_name = source.source.title()
            if source.sentiment_score > 0.2:
                source_sentiment = "pozitif"
            elif source.sentiment_score < -0.2:
                source_sentiment = "negatif"
            else:
                source_sentiment = "nötr"
            
            source_analysis.append(
                f"• {source_name}: {source_sentiment} (skor: {source.sentiment_score:.2f}, "
                f"{source.sample_size} örnek)"
            )
        
        interpretation = f"""**Temel Analiz Özeti:**

{sentiment_desc}

{trend_desc}

**Kaynak Bazlı Analiz:**

{chr(10).join(source_analysis)}

**Genel Değerlendirme:**

Duygu skoru {sentiment.overall_score:.2f} seviyesinde (aralık: -1 ile +1 arası). {
    "Bu, piyasada güçlü bir yükseliş beklentisi olduğunu gösteriyor." if sentiment.overall_score > 0.5
    else "Bu, piyasada güçlü bir düşüş beklentisi olduğunu gösteriyor." if sentiment.overall_score < -0.5
    else "Bu, piyasanın kararsız olduğunu ve net bir yön olmadığını gösteriyor."
}

{
    "Sosyal medya ve haber kaynakları uyumlu sinyaller veriyor, bu da duygunun güvenilirliğini artırıyor."
    if len(sentiment.sources) > 1 and all(
        (s.sentiment_score > 0) == (sentiment.overall_score > 0) for s in sentiment.sources
    )
    else "Farklı kaynaklar çelişkili sinyaller veriyor, bu nedenle dikkatli olunmalı."
    if len(sentiment.sources) > 1
    else "Tek kaynak kullanıldı, daha fazla veri ile doğrulama önerilir."
}"""
        
        return interpretation
    
    def _fallback_report_generation(
        self,
        signal: Signal,
        explanation: SignalExplanation,
        indicators: IndicatorResults,
        sentiment: OverallSentiment
    ) -> str:
        """
        Fallback method for report generation when AI is unavailable.
        Uses template-based generation.
        
        Args:
            signal: Generated trading signal
            explanation: Signal explanation
            indicators: Technical indicator results
            sentiment: Overall sentiment results
        
        Returns:
            Template-based comprehensive Turkish report
        """
        logger.info("Using fallback template for comprehensive report")
        
        # Get individual interpretations
        technical_interp = self._fallback_technical_interpretation(indicators)
        fundamental_interp = self._fallback_fundamental_interpretation(sentiment)
        
        # Signal description
        signal_desc = {
            SignalType.STRONG_BUY: "GÜÇLÜ AL - Yüksek güvenilirlikli yükseliş sinyali",
            SignalType.BUY: "AL - Orta güvenilirlikli yükseliş sinyali",
            SignalType.NEUTRAL: "NÖTR - Bekleme önerilir",
            SignalType.SELL: "SAT - Orta güvenilirlikli düşüş sinyali",
            SignalType.STRONG_SELL: "GÜÇLÜ SAT - Yüksek güvenilirlikli düşüş sinyali",
            SignalType.UNCERTAIN: "BELİRSİZ - Net sinyal yok, işlem önerilmez"
        }.get(signal.signal_type, "BİLİNMEYEN")
        
        report = f"""
═══════════════════════════════════════════════════════════════
KRİPTO PARA ANALİZ RAPORU
═══════════════════════════════════════════════════════════════

**Coin:** {signal.coin}
**Zaman Dilimi:** {signal.timeframe}
**Analiz Tarihi:** {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

───────────────────────────────────────────────────────────────
1. YÖNETİCİ ÖZETİ
───────────────────────────────────────────────────────────────

**Sinyal:** {signal_desc}
**Başarı İhtimali:** %{signal.success_probability:.1f}

{
    f"Analiz sonuçları {signal.coin} için {signal.signal_type.value} sinyali üretmiştir. "
    f"Teknik göstergeler ve piyasa duygusu birlikte değerlendirildiğinde, "
    f"bu sinyalin başarı ihtimali %{signal.success_probability:.1f} olarak hesaplanmıştır."
}

───────────────────────────────────────────────────────────────
2. TEKNİK ANALİZ DEĞERLENDİRMESİ
───────────────────────────────────────────────────────────────

{technical_interp}

**Destekleyen Göstergeler:** {', '.join(explanation.supporting_indicators) if explanation.supporting_indicators else 'Yok'}
**Çelişen Göstergeler:** {', '.join(explanation.conflicting_indicators) if explanation.conflicting_indicators else 'Yok'}

───────────────────────────────────────────────────────────────
3. PİYASA DUYGUSU DEĞERLENDİRMESİ
───────────────────────────────────────────────────────────────

{fundamental_interp}

───────────────────────────────────────────────────────────────
4. SİNYAL GEREKÇESİ
───────────────────────────────────────────────────────────────

Bu sinyal aşağıdaki faktörlere dayanarak üretilmiştir:

**Teknik Faktörler:**
{chr(10).join([f'• {reason}' for reason in explanation.technical_reasons]) if explanation.technical_reasons else '• Teknik faktör bulunamadı'}

**Temel Faktörler:**
{chr(10).join([f'• {reason}' for reason in explanation.fundamental_reasons]) if explanation.fundamental_reasons else '• Temel faktör bulunamadı'}

Başarı ihtimali, teknik analiz (%60 ağırlık), temel analiz (%30 ağırlık) ve 
indikatör uyumu (%10 ağırlık) birleştirilerek hesaplanmıştır.

───────────────────────────────────────────────────────────────
5. RİSK YÖNETİMİ ÖNERİLERİ
───────────────────────────────────────────────────────────────

**Stop-Loss ve Take-Profit:**
• Önerilen Stop-Loss: {signal.stop_loss:.2f} USD (ATR bazlı dinamik seviye)
• Önerilen Take-Profit: {signal.take_profit:.2f} USD (ATR bazlı dinamik seviye)

**Pozisyon Büyüklüğü:**
• Başarı ihtimali %{signal.success_probability:.0f} olduğundan, {
    'agresif pozisyon alınabilir (portföyün %5-10\'u)' if signal.success_probability >= 80
    else 'orta seviye pozisyon önerilir (portföyün %3-5\'i)' if signal.success_probability >= 60
    else 'küçük pozisyon veya bekleme önerilir (portföyün %1-2\'si)' if signal.success_probability >= 40
    else 'işlem önerilmez, bekleme modunda kalın'
}

**Dikkat Edilmesi Gereken Riskler:**
{chr(10).join([f'• {risk}' for risk in explanation.risk_factors]) if explanation.risk_factors else '• Önemli risk faktörü tespit edilmedi'}

───────────────────────────────────────────────────────────────
6. SONUÇ VE ÖNERİLER
───────────────────────────────────────────────────────────────

{
    f"{signal.coin} için yapılan kapsamlı analiz sonucunda {signal.signal_type.value} sinyali üretilmiştir. "
    f"Teknik göstergeler ve piyasa duygusu birlikte değerlendirildiğinde, "
    f"{'bu fırsat değerlendirilebilir ancak risk yönetimi kurallarına mutlaka uyulmalıdır.' if signal.success_probability >= 60 else 'dikkatli olunması ve daha net sinyaller beklenmesi önerilir.'}"
}

**UYARI:** Bu rapor yatırım tavsiyesi değil, analiz raporudur. 
Yatırım kararlarınızı verirken kendi araştırmanızı yapın ve 
risk toleransınızı göz önünde bulundurun.

═══════════════════════════════════════════════════════════════
"""
        
        # Detect technical terms and add explanations
        detected_terms = self._detect_technical_terms(report)
        report_with_explanations = self._add_term_explanations(report, detected_terms)
        
        return report_with_explanations

