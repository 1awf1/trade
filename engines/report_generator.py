"""
Report Generator Engine
Generates HTML and PDF reports for analysis results.
Supports: AnalysisResult, BacktestResult, Portfolio reports
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from io import BytesIO
import base64

# HTML generation
from jinja2 import Template

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors

# WeasyPrint is optional (requires system libraries)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

from models.schemas import (
    AnalysisResult, BacktestResult, Portfolio, Signal, SignalType,
    IndicatorResults, OverallSentiment
)


class ReportGenerator:
    """
    Generates comprehensive reports for analysis results.
    Supports HTML and PDF formats with embedded charts.
    """
    
    def __init__(self):
        """Initialize report generator with templates."""
        self.html_template = self._create_html_template()
        self.backtest_html_template = self._create_backtest_html_template()
        self.portfolio_html_template = self._create_portfolio_html_template()
    
    # ========================================================================
    # HTML Report Generation
    # ========================================================================
    
    def generate_html_report(
        self,
        analysis: AnalysisResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate HTML report for analysis result.
        
        Args:
            analysis: Complete analysis result
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            HTML string
        """
        # Prepare data for template
        context = {
            'analysis': analysis,
            'coin': analysis.coin,
            'timeframe': analysis.timeframe,
            'timestamp': analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'signal': analysis.signal,
            'signal_color': self._get_signal_color(analysis.signal.signal_type),
            'success_probability': analysis.signal.success_probability,
            'technical': analysis.technical_results,
            'fundamental': analysis.fundamental_results,
            'explanation': analysis.explanation,
            'ai_report': analysis.ai_report,
            'price_at_analysis': analysis.price_at_analysis,
            'chart_images': chart_images or {},
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Render template
        template = Template(self.html_template)
        html = template.render(**context)
        
        return html
    
    def generate_backtest_html_report(
        self,
        backtest: BacktestResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate HTML report for backtest result.
        
        Args:
            backtest: Complete backtest result
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            HTML string
        """
        context = {
            'backtest': backtest,
            'coin': backtest.coin,
            'timeframe': backtest.timeframe,
            'start_date': backtest.period[0].strftime('%Y-%m-%d'),
            'end_date': backtest.period[1].strftime('%Y-%m-%d'),
            'metrics': backtest.metrics,
            'trades': backtest.trades,
            'parameters': backtest.parameters,
            'chart_images': chart_images or {},
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        template = Template(self.backtest_html_template)
        html = template.render(**context)
        
        return html
    
    def generate_portfolio_html_report(
        self,
        portfolio: Portfolio,
        chart_images: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate HTML report for portfolio.
        
        Args:
            portfolio: Portfolio data
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            HTML string
        """
        context = {
            'portfolio': portfolio,
            'holdings': portfolio.holdings,
            'total_value': portfolio.total_value,
            'total_invested': portfolio.total_invested,
            'total_profit_loss': portfolio.total_profit_loss,
            'total_profit_loss_percent': portfolio.total_profit_loss_percent,
            'chart_images': chart_images or {},
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        template = Template(self.portfolio_html_template)
        html = template.render(**context)
        
        return html
    
    # ========================================================================
    # PDF Report Generation (WeasyPrint)
    # ========================================================================
    
    def generate_pdf_report(
        self,
        analysis: AnalysisResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Generate PDF report for analysis result.
        Uses WeasyPrint if available, otherwise falls back to ReportLab.
        
        Args:
            analysis: Complete analysis result
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            PDF bytes
        """
        if WEASYPRINT_AVAILABLE:
            # Generate HTML first
            html_content = self.generate_html_report(analysis, chart_images)
            
            # Add PDF-specific CSS
            pdf_css = CSS(string=self._get_pdf_css())
            
            # Convert HTML to PDF
            pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[pdf_css])
            
            return pdf_bytes
        else:
            # Fallback to ReportLab
            return self._generate_pdf_with_reportlab(analysis, chart_images)
    
    def generate_backtest_pdf_report(
        self,
        backtest: BacktestResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Generate PDF report for backtest result.
        Uses WeasyPrint if available, otherwise falls back to ReportLab.
        
        Args:
            backtest: Complete backtest result
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            PDF bytes
        """
        if WEASYPRINT_AVAILABLE:
            html_content = self.generate_backtest_html_report(backtest, chart_images)
            pdf_css = CSS(string=self._get_pdf_css())
            pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[pdf_css])
            return pdf_bytes
        else:
            return self._generate_backtest_pdf_with_reportlab(backtest, chart_images)
    
    def generate_portfolio_pdf_report(
        self,
        portfolio: Portfolio,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Generate PDF report for portfolio.
        Uses WeasyPrint if available, otherwise falls back to ReportLab.
        
        Args:
            portfolio: Portfolio data
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            PDF bytes
        """
        if WEASYPRINT_AVAILABLE:
            html_content = self.generate_portfolio_html_report(portfolio, chart_images)
            pdf_css = CSS(string=self._get_pdf_css())
            pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[pdf_css])
            return pdf_bytes
        else:
            return self._generate_portfolio_pdf_with_reportlab(portfolio, chart_images)
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _get_signal_color(self, signal_type: SignalType) -> str:
        """Get color for signal type."""
        colors = {
            SignalType.STRONG_BUY: '#00C853',
            SignalType.BUY: '#4CAF50',
            SignalType.NEUTRAL: '#FFC107',
            SignalType.SELL: '#FF5722',
            SignalType.STRONG_SELL: '#D32F2F',
            SignalType.UNCERTAIN: '#9E9E9E'
        }
        return colors.get(signal_type, '#9E9E9E')
    
    def _get_pdf_css(self) -> str:
        """Get CSS for PDF generation."""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.4;
        }
        
        h1 {
            font-size: 18pt;
            color: #1976D2;
            margin-bottom: 10pt;
        }
        
        h2 {
            font-size: 14pt;
            color: #424242;
            margin-top: 15pt;
            margin-bottom: 8pt;
        }
        
        h3 {
            font-size: 12pt;
            color: #616161;
            margin-top: 10pt;
            margin-bottom: 6pt;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10pt 0;
        }
        
        th, td {
            border: 1px solid #E0E0E0;
            padding: 6pt;
            text-align: left;
        }
        
        th {
            background-color: #F5F5F5;
            font-weight: bold;
        }
        
        .page-break {
            page-break-after: always;
        }
        
        img {
            max-width: 100%;
            height: auto;
        }
        """
    
    # ========================================================================
    # HTML Templates
    # ========================================================================
    
    def _create_html_template(self) -> str:
        """Create HTML template for analysis report."""
        return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kripto Analiz Raporu - {{ coin }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
        }
        h2 {
            color: #424242;
            margin-top: 30px;
            border-bottom: 2px solid #E0E0E0;
            padding-bottom: 8px;
        }
        h3 {
            color: #616161;
            margin-top: 20px;
        }
        .header-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .info-item {
            padding: 10px;
        }
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }
        .info-value {
            font-size: 1.1em;
            margin-top: 5px;
        }
        .signal-box {
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            color: white;
            font-size: 1.3em;
            font-weight: bold;
        }
        .success-probability {
            font-size: 2em;
            margin: 10px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .indicator-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .indicator-card {
            padding: 15px;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            background-color: #fafafa;
        }
        .indicator-name {
            font-weight: bold;
            color: #1976D2;
            margin-bottom: 8px;
        }
        .indicator-value {
            font-size: 1.2em;
            margin: 5px 0;
        }
        .indicator-signal {
            color: #666;
            font-style: italic;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .ai-report {
            background-color: #E3F2FD;
            padding: 20px;
            border-left: 4px solid #1976D2;
            border-radius: 5px;
            margin: 20px 0;
            white-space: pre-wrap;
        }
        .explanation-section {
            margin: 15px 0;
        }
        .reason-list {
            list-style-type: none;
            padding-left: 0;
        }
        .reason-list li {
            padding: 8px;
            margin: 5px 0;
            background-color: #f9f9f9;
            border-left: 3px solid #1976D2;
            padding-left: 15px;
        }
        .risk-list li {
            border-left-color: #FF5722;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #E0E0E0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Kripto Para Analiz Raporu</h1>
        
        <div class="header-info">
            <div class="info-item">
                <div class="info-label">Coin</div>
                <div class="info-value">{{ coin }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Zaman Aralığı</div>
                <div class="info-value">{{ timeframe }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Analiz Tarihi</div>
                <div class="info-value">{{ timestamp }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Fiyat</div>
                <div class="info-value">${{ "%.2f"|format(price_at_analysis) }}</div>
            </div>
        </div>
        
        <div class="signal-box" style="background-color: {{ signal_color }};">
            <div>Sinyal: {{ signal.signal_type.value }}</div>
            <div class="success-probability">{{ "%.1f"|format(success_probability) }}%</div>
            <div style="font-size: 0.8em;">Başarı İhtimali</div>
        </div>
        
        {% if signal.stop_loss or signal.take_profit %}
        <div class="header-info">
            {% if signal.stop_loss %}
            <div class="info-item">
                <div class="info-label">Stop-Loss</div>
                <div class="info-value">${{ "%.2f"|format(signal.stop_loss) }}</div>
            </div>
            {% endif %}
            {% if signal.take_profit %}
            <div class="info-item">
                <div class="info-label">Take-Profit</div>
                <div class="info-value">${{ "%.2f"|format(signal.take_profit) }}</div>
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        <h2>Teknik Analiz Sonuçları</h2>
        
        <div class="indicator-grid">
            <div class="indicator-card">
                <div class="indicator-name">RSI</div>
                <div class="indicator-value">{{ "%.2f"|format(technical.rsi) }}</div>
                <div class="indicator-signal">{{ technical.rsi_signal }}</div>
                {% if technical.rsi_divergence %}
                <div style="color: #FF5722; margin-top: 5px;">Divergence: {{ technical.rsi_divergence }}</div>
                {% endif %}
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">MACD</div>
                <div class="indicator-value">{{ "%.4f"|format(technical.macd.macd) }}</div>
                <div class="indicator-signal">{{ technical.macd_signal }}</div>
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">EMA 50 / EMA 200</div>
                <div class="indicator-value">{{ "%.2f"|format(technical.ema_50) }} / {{ "%.2f"|format(technical.ema_200) }}</div>
                {% if technical.golden_death_cross %}
                <div style="color: #FF5722; margin-top: 5px;">{{ technical.golden_death_cross }}</div>
                {% endif %}
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">ATR</div>
                <div class="indicator-value">{{ "%.2f"|format(technical.atr.atr) }} ({{ "%.2f"|format(technical.atr.atr_percent) }}%)</div>
                <div class="indicator-signal">Volatilite</div>
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">VWAP</div>
                <div class="indicator-value">{{ "%.2f"|format(technical.vwap) }}</div>
                <div class="indicator-signal">{{ technical.vwap_signal }}</div>
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">OBV</div>
                <div class="indicator-value">{{ "%.0f"|format(technical.obv) }}</div>
                <div class="indicator-signal">{{ technical.obv_signal }}</div>
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">Confluence Score</div>
                <div class="indicator-value">{{ "%.2f"|format(technical.confluence_score) }}</div>
                <div class="indicator-signal">İndikatör Uyumu</div>
            </div>
            
            <div class="indicator-card">
                <div class="indicator-name">Trend Filtresi</div>
                <div class="indicator-value">{{ technical.ema_200_trend_filter }}</div>
                <div class="indicator-signal">EMA 200 Bazlı</div>
            </div>
        </div>
        
        <h3>Destek ve Direnç Seviyeleri</h3>
        <table>
            <tr>
                <th>Destek Seviyeleri</th>
                <th>Direnç Seviyeleri</th>
            </tr>
            <tr>
                <td>
                    {% for level in technical.support_levels %}
                    ${{ "%.2f"|format(level) }}{% if not loop.last %}, {% endif %}
                    {% endfor %}
                </td>
                <td>
                    {% for level in technical.resistance_levels %}
                    ${{ "%.2f"|format(level) }}{% if not loop.last %}, {% endif %}
                    {% endfor %}
                </td>
            </tr>
        </table>
        
        <h3>Fibonacci Retracement Seviyeleri</h3>
        <table>
            <tr>
                <th>Seviye</th>
                <th>Fiyat</th>
            </tr>
            <tr><td>0%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_0) }}</td></tr>
            <tr><td>23.6%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_236) }}</td></tr>
            <tr><td>38.2%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_382) }}</td></tr>
            <tr><td>50%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_500) }}</td></tr>
            <tr><td>61.8%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_618) }}</td></tr>
            <tr><td>100%</td><td>${{ "%.2f"|format(technical.fibonacci_levels.level_100) }}</td></tr>
        </table>
        
        {% if technical.patterns %}
        <h3>Tespit Edilen Formasyonlar</h3>
        <ul class="reason-list">
            {% for pattern in technical.patterns %}
            <li>
                <strong>{{ pattern.name }}</strong> (Güven: {{ "%.0f"|format(pattern.confidence * 100) }}%)
                <br>{{ pattern.description }}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        <h2>Temel Analiz Sonuçları</h2>
        
        <div class="header-info">
            <div class="info-item">
                <div class="info-label">Genel Duygu</div>
                <div class="info-value">{{ fundamental.classification.value }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Duygu Skoru</div>
                <div class="info-value">{{ "%.2f"|format(fundamental.overall_score) }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Trend</div>
                <div class="info-value">{{ fundamental.trend.value }}</div>
            </div>
        </div>
        
        <h3>Kaynak Bazlı Duygu Analizi</h3>
        <table>
            <tr>
                <th>Kaynak</th>
                <th>Duygu Skoru</th>
                <th>Güven</th>
                <th>Örnek Sayısı</th>
            </tr>
            {% for source in fundamental.sources %}
            <tr>
                <td>{{ source.source }}</td>
                <td>{{ "%.2f"|format(source.sentiment_score) }}</td>
                <td>{{ "%.0f"|format(source.confidence * 100) }}%</td>
                <td>{{ source.sample_size }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Sinyal Açıklaması</h2>
        
        <div class="explanation-section">
            <h3>Destekleyen İndikatörler</h3>
            <ul class="reason-list">
                {% for indicator in explanation.supporting_indicators %}
                <li>{{ indicator }}</li>
                {% endfor %}
            </ul>
        </div>
        
        {% if explanation.conflicting_indicators %}
        <div class="explanation-section">
            <h3>Çelişen İndikatörler</h3>
            <ul class="reason-list risk-list">
                {% for indicator in explanation.conflicting_indicators %}
                <li>{{ indicator }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <div class="explanation-section">
            <h3>Teknik Gerekçeler</h3>
            <ul class="reason-list">
                {% for reason in explanation.technical_reasons %}
                <li>{{ reason }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <div class="explanation-section">
            <h3>Temel Analiz Gerekçeleri</h3>
            <ul class="reason-list">
                {% for reason in explanation.fundamental_reasons %}
                <li>{{ reason }}</li>
                {% endfor %}
            </ul>
        </div>
        
        {% if explanation.risk_factors %}
        <div class="explanation-section">
            <h3>Risk Faktörleri</h3>
            <ul class="reason-list risk-list">
                {% for risk in explanation.risk_factors %}
                <li>{{ risk }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <h2>Yapay Zeka Yorumu</h2>
        <div class="ai-report">{{ ai_report }}</div>
        
        {% if chart_images %}
        <h2>Grafikler</h2>
        {% for chart_name, chart_data in chart_images.items() %}
        <div class="chart-container">
            <h3>{{ chart_name }}</h3>
            <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
        </div>
        {% endfor %}
        {% endif %}
        
        <div class="footer">
            <p>Bu rapor {{ generated_at }} tarihinde otomatik olarak oluşturulmuştur.</p>
            <p>Kripto Para Analiz Sistemi</p>
        </div>
    </div>
</body>
</html>
"""

    
    def _create_backtest_html_template(self) -> str:
        """Create HTML template for backtest report."""
        return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtesting Raporu - {{ coin }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
        }
        h2 {
            color: #424242;
            margin-top: 30px;
            border-bottom: 2px solid #E0E0E0;
            padding-bottom: 8px;
        }
        .header-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .info-item {
            padding: 10px;
        }
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }
        .info-value {
            font-size: 1.1em;
            margin-top: 5px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            padding: 20px;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            background-color: #fafafa;
            text-align: center;
        }
        .metric-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #1976D2;
        }
        .metric-value.positive {
            color: #4CAF50;
        }
        .metric-value.negative {
            color: #F44336;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #E0E0E0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Backtesting Raporu</h1>
        
        <div class="header-info">
            <div class="info-item">
                <div class="info-label">Coin</div>
                <div class="info-value">{{ coin }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Zaman Aralığı</div>
                <div class="info-value">{{ timeframe }}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Test Periyodu</div>
                <div class="info-value">{{ start_date }} - {{ end_date }}</div>
            </div>
        </div>
        
        <h2>Performans Metrikleri</h2>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Toplam İşlem</div>
                <div class="metric-value">{{ metrics.total_trades }}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Kazanan İşlem</div>
                <div class="metric-value positive">{{ metrics.winning_trades }}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Kaybeden İşlem</div>
                <div class="metric-value negative">{{ metrics.losing_trades }}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Başarı Oranı</div>
                <div class="metric-value">{{ "%.1f"|format(metrics.win_rate) }}%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Toplam Kar/Zarar</div>
                <div class="metric-value {% if metrics.total_profit_loss >= 0 %}positive{% else %}negative{% endif %}">
                    ${{ "%.2f"|format(metrics.total_profit_loss) }}
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Kar/Zarar %</div>
                <div class="metric-value {% if metrics.total_profit_loss_percent >= 0 %}positive{% else %}negative{% endif %}">
                    {{ "%.2f"|format(metrics.total_profit_loss_percent) }}%
                </div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Maksimum Düşüş</div>
                <div class="metric-value negative">{{ "%.2f"|format(metrics.max_drawdown_percent) }}%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Sharpe Ratio</div>
                <div class="metric-value">{{ "%.2f"|format(metrics.sharpe_ratio) }}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value">{{ "%.2f"|format(metrics.profit_factor) }}</div>
            </div>
        </div>
        
        <h2>Test Parametreleri</h2>
        <table>
            <tr>
                <th>Parametre</th>
                <th>Değer</th>
            </tr>
            <tr>
                <td>Kullanılan İndikatörler</td>
                <td>{{ parameters.indicators|join(', ') }}</td>
            </tr>
            <tr>
                <td>Temel Analiz Kullanımı</td>
                <td>{{ 'Evet' if parameters.use_fundamental else 'Hayır' }}</td>
            </tr>
            <tr>
                <td>Sinyal Eşiği</td>
                <td>{{ parameters.signal_threshold }}%</td>
            </tr>
        </table>
        
        {% if parameters.indicator_thresholds %}
        <h3>İndikatör Eşikleri</h3>
        <table>
            <tr>
                <th>İndikatör</th>
                <th>Eşik Değeri</th>
            </tr>
            {% for indicator, threshold in parameters.indicator_thresholds.items() %}
            <tr>
                <td>{{ indicator }}</td>
                <td>{{ threshold }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        
        <h2>İşlem Geçmişi</h2>
        <table>
            <tr>
                <th>Giriş Tarihi</th>
                <th>Giriş Fiyatı</th>
                <th>Çıkış Tarihi</th>
                <th>Çıkış Fiyatı</th>
                <th>Kar/Zarar</th>
                <th>Kar/Zarar %</th>
                <th>Sinyal</th>
            </tr>
            {% for trade in trades %}
            <tr>
                <td>{{ trade.entry_date.strftime('%Y-%m-%d %H:%M') }}</td>
                <td>${{ "%.2f"|format(trade.entry_price) }}</td>
                <td>{{ trade.exit_date.strftime('%Y-%m-%d %H:%M') }}</td>
                <td>${{ "%.2f"|format(trade.exit_price) }}</td>
                <td style="color: {% if trade.profit_loss >= 0 %}green{% else %}red{% endif %}">
                    ${{ "%.2f"|format(trade.profit_loss) }}
                </td>
                <td style="color: {% if trade.profit_loss_percent >= 0 %}green{% else %}red{% endif %}">
                    {{ "%.2f"|format(trade.profit_loss_percent) }}%
                </td>
                <td>{{ trade.signal_at_entry.signal_type.value }}</td>
            </tr>
            {% endfor %}
        </table>
        
        {% if chart_images %}
        <h2>Grafikler</h2>
        {% for chart_name, chart_data in chart_images.items() %}
        <div class="chart-container">
            <h3>{{ chart_name }}</h3>
            <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
        </div>
        {% endfor %}
        {% endif %}
        
        <div class="footer">
            <p>Bu rapor {{ generated_at }} tarihinde otomatik olarak oluşturulmuştur.</p>
            <p>Kripto Para Analiz Sistemi - Backtesting Modülü</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _create_portfolio_html_template(self) -> str:
        """Create HTML template for portfolio report."""
        return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portföy Raporu</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
        }
        h2 {
            color: #424242;
            margin-top: 30px;
            border-bottom: 2px solid #E0E0E0;
            padding-bottom: 8px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .summary-card {
            padding: 20px;
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            background-color: #fafafa;
            text-align: center;
        }
        .summary-label {
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .summary-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #1976D2;
        }
        .summary-value.positive {
            color: #4CAF50;
        }
        .summary-value.negative {
            color: #F44336;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #E0E0E0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Portföy Raporu</h1>
        
        <h2>Portföy Özeti</h2>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Toplam Değer</div>
                <div class="summary-value">${{ "%.2f"|format(total_value) }}</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Toplam Yatırım</div>
                <div class="summary-value">${{ "%.2f"|format(total_invested) }}</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Toplam Kar/Zarar</div>
                <div class="summary-value {% if total_profit_loss >= 0 %}positive{% else %}negative{% endif %}">
                    ${{ "%.2f"|format(total_profit_loss) }}
                </div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Kar/Zarar %</div>
                <div class="summary-value {% if total_profit_loss_percent >= 0 %}positive{% else %}negative{% endif %}">
                    {{ "%.2f"|format(total_profit_loss_percent) }}%
                </div>
            </div>
        </div>
        
        <h2>Holding Detayları</h2>
        <table>
            <tr>
                <th>Coin</th>
                <th>Miktar</th>
                <th>Alış Fiyatı</th>
                <th>Alış Tarihi</th>
                <th>Güncel Fiyat</th>
                <th>Güncel Değer</th>
                <th>Kar/Zarar</th>
                <th>Kar/Zarar %</th>
            </tr>
            {% for holding in holdings %}
            <tr>
                <td><strong>{{ holding.coin }}</strong></td>
                <td>{{ "%.8f"|format(holding.amount) }}</td>
                <td>${{ "%.2f"|format(holding.purchase_price) }}</td>
                <td>{{ holding.purchase_date.strftime('%Y-%m-%d') }}</td>
                <td>${{ "%.2f"|format(holding.current_price) }}</td>
                <td>${{ "%.2f"|format(holding.current_value) }}</td>
                <td style="color: {% if holding.profit_loss_amount >= 0 %}green{% else %}red{% endif %}">
                    ${{ "%.2f"|format(holding.profit_loss_amount) }}
                </td>
                <td style="color: {% if holding.profit_loss_percent >= 0 %}green{% else %}red{% endif %}">
                    {{ "%.2f"|format(holding.profit_loss_percent) }}%
                </td>
            </tr>
            {% endfor %}
        </table>
        
        {% if chart_images %}
        <h2>Performans Grafiği</h2>
        {% for chart_name, chart_data in chart_images.items() %}
        <div class="chart-container">
            <h3>{{ chart_name }}</h3>
            <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
        </div>
        {% endfor %}
        {% endif %}
        
        <div class="footer">
            <p>Bu rapor {{ generated_at }} tarihinde otomatik olarak oluşturulmuştur.</p>
            <p>Kripto Para Analiz Sistemi - Portföy Yönetimi</p>
        </div>
    </div>
</body>
</html>
"""

    
    # ========================================================================
    # ReportLab Fallback Methods
    # ========================================================================
    
    def _generate_pdf_with_reportlab(
        self,
        analysis: AnalysisResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Generate PDF using ReportLab (fallback when WeasyPrint unavailable).
        
        Args:
            analysis: Complete analysis result
            chart_images: Optional dict of chart names to base64 encoded images
        
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=20
        )
        story.append(Paragraph("Kripto Para Analiz Raporu", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Basic info table
        info_data = [
            ['Coin:', analysis.coin],
            ['Zaman Aralığı:', analysis.timeframe],
            ['Analiz Tarihi:', analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')],
            ['Fiyat:', f'${analysis.price_at_analysis:.2f}'],
            ['Sinyal:', analysis.signal.signal_type.value],
            ['Başarı İhtimali:', f'{analysis.signal.success_probability:.1f}%']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Technical Analysis section
        story.append(Paragraph("Teknik Analiz Sonuçları", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        tech_data = [
            ['İndikatör', 'Değer', 'Sinyal'],
            ['RSI', f'{analysis.technical_results.rsi:.2f}', analysis.technical_results.rsi_signal],
            ['MACD', f'{analysis.technical_results.macd.macd:.4f}', analysis.technical_results.macd_signal],
            ['EMA 50', f'{analysis.technical_results.ema_50:.2f}', ''],
            ['EMA 200', f'{analysis.technical_results.ema_200:.2f}', ''],
            ['ATR', f'{analysis.technical_results.atr.atr:.2f}', f'{analysis.technical_results.atr.atr_percent:.2f}%'],
            ['VWAP', f'{analysis.technical_results.vwap:.2f}', analysis.technical_results.vwap_signal],
            ['Confluence', f'{analysis.technical_results.confluence_score:.2f}', '']
        ]
        
        tech_table = Table(tech_data, colWidths=[2*inch, 2*inch, 2*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        story.append(tech_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Fundamental Analysis section
        story.append(Paragraph("Temel Analiz Sonuçları", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        fund_data = [
            ['Metrik', 'Değer'],
            ['Genel Duygu', analysis.fundamental_results.classification.value],
            ['Duygu Skoru', f'{analysis.fundamental_results.overall_score:.2f}'],
            ['Trend', analysis.fundamental_results.trend.value]
        ]
        
        fund_table = Table(fund_data, colWidths=[3*inch, 3*inch])
        fund_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(fund_table)
        story.append(Spacer(1, 0.3*inch))
        
        # AI Report
        story.append(Paragraph("Yapay Zeka Yorumu", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(analysis.ai_report, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _generate_backtest_pdf_with_reportlab(
        self,
        backtest: BacktestResult,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """Generate backtest PDF using ReportLab."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("Backtesting Raporu", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Basic info
        info_data = [
            ['Coin:', backtest.coin],
            ['Zaman Aralığı:', backtest.timeframe],
            ['Test Periyodu:', f"{backtest.period[0].strftime('%Y-%m-%d')} - {backtest.period[1].strftime('%Y-%m-%d')}"]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Metrics
        story.append(Paragraph("Performans Metrikleri", styles['Heading2']))
        metrics_data = [
            ['Metrik', 'Değer'],
            ['Toplam İşlem', str(backtest.metrics.total_trades)],
            ['Kazanan İşlem', str(backtest.metrics.winning_trades)],
            ['Kaybeden İşlem', str(backtest.metrics.losing_trades)],
            ['Başarı Oranı', f'{backtest.metrics.win_rate:.1f}%'],
            ['Toplam Kar/Zarar', f'${backtest.metrics.total_profit_loss:.2f}'],
            ['Kar/Zarar %', f'{backtest.metrics.total_profit_loss_percent:.2f}%']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _generate_portfolio_pdf_with_reportlab(
        self,
        portfolio: Portfolio,
        chart_images: Optional[Dict[str, str]] = None
    ) -> bytes:
        """Generate portfolio PDF using ReportLab."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("Portföy Raporu", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_data = [
            ['Toplam Değer:', f'${portfolio.total_value:.2f}'],
            ['Toplam Yatırım:', f'${portfolio.total_invested:.2f}'],
            ['Toplam Kar/Zarar:', f'${portfolio.total_profit_loss:.2f}'],
            ['Kar/Zarar %:', f'{portfolio.total_profit_loss_percent:.2f}%']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Holdings
        story.append(Paragraph("Holding Detayları", styles['Heading2']))
        holdings_data = [['Coin', 'Miktar', 'Alış Fiyatı', 'Güncel Fiyat', 'Kar/Zarar %']]
        
        for holding in portfolio.holdings:
            holdings_data.append([
                holding.coin,
                f'{holding.amount:.8f}',
                f'${holding.purchase_price:.2f}',
                f'${holding.current_price:.2f}',
                f'{holding.profit_loss_percent:.2f}%'
            ])
        
        holdings_table = Table(holdings_data)
        holdings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8)
        ]))
        story.append(holdings_table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
