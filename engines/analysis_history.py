"""
Analysis History Manager
Manages saving, retrieving, comparing, and tracking accuracy of analyses.
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.database import Analysis
from models.schemas import (
    AnalysisResult, AnalysisSummary, ComparisonReport, AccuracyStats,
    SignalType
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalysisHistoryManager:
    """Manages analysis history operations."""
    
    def __init__(self, user_id: str, db_session_factory=None):
        """
        Initialize Analysis History Manager.
        
        Args:
            user_id: User ID for filtering analyses
            db_session_factory: Optional database session factory for testing
        """
        self.user_id = user_id
        if db_session_factory is None:
            from utils.database import get_db
            self.db_session_factory = get_db
        else:
            self.db_session_factory = db_session_factory
    
    def save_analysis(self, analysis: AnalysisResult) -> str:
        """
        Save analysis result to database.
        
        Args:
            analysis: Complete analysis result
            
        Returns:
            analysis_id: ID of saved analysis
            
        Validates: Requirement 16.1
        """
        try:
            with self.db_session_factory() as db:
                # Convert Pydantic models to dict with JSON-serializable values
                technical_data = analysis.technical_results.model_dump(mode='json')
                fundamental_data = analysis.fundamental_results.model_dump(mode='json')
                signal_data = analysis.signal.model_dump(mode='json')
                
                # Create database record
                db_analysis = Analysis(
                    id=analysis.id,
                    user_id=self.user_id,
                    coin=analysis.coin,
                    timeframe=analysis.timeframe,
                    timestamp=analysis.timestamp,
                    technical_data=technical_data,
                    fundamental_data=fundamental_data,
                    signal=signal_data,
                    ai_report=analysis.ai_report,
                    price_at_analysis=float(analysis.price_at_analysis),
                    price_after_period=float(analysis.price_after_period) if analysis.price_after_period else None,
                    actual_outcome=analysis.actual_outcome
                )
                
                db.add(db_analysis)
                db.commit()
                
                logger.info(f"Analysis saved: {analysis.id} for {analysis.coin}")
                return analysis.id
                
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            raise
    
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        Retrieve a specific analysis by ID.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            AnalysisResult or None if not found
        """
        try:
            with self.db_session_factory() as db:
                db_analysis = db.query(Analysis).filter(
                    Analysis.id == analysis_id,
                    Analysis.user_id == self.user_id
                ).first()
                
                if not db_analysis:
                    logger.warning(f"Analysis not found: {analysis_id}")
                    return None
                
                # Convert database record to AnalysisResult
                return self._db_to_analysis_result(db_analysis)
                
        except Exception as e:
            logger.error(f"Error retrieving analysis: {str(e)}")
            raise
    
    def list_analyses(
        self,
        coin: Optional[str] = None,
        limit: int = 100
    ) -> List[AnalysisSummary]:
        """
        List analyses with optional filtering.
        
        Args:
            coin: Optional coin filter
            limit: Maximum number of results (default 100)
            
        Returns:
            List of analysis summaries sorted by timestamp (newest first)
            
        Validates: Requirement 16.2
        """
        try:
            with self.db_session_factory() as db:
                query = db.query(Analysis).filter(
                    Analysis.user_id == self.user_id
                )
                
                # Apply coin filter if provided
                if coin:
                    query = query.filter(Analysis.coin == coin.upper())
                
                # Order by timestamp descending (newest first)
                query = query.order_by(desc(Analysis.timestamp))
                
                # Apply limit
                query = query.limit(limit)
                
                # Execute query
                analyses = query.all()
                
                # Convert to summaries
                summaries = []
                for db_analysis in analyses:
                    signal_data = db_analysis.signal
                    summaries.append(AnalysisSummary(
                        id=db_analysis.id,
                        coin=db_analysis.coin,
                        timeframe=db_analysis.timeframe,
                        timestamp=db_analysis.timestamp,
                        signal_type=SignalType(signal_data['signal_type']),
                        success_probability=signal_data['success_probability'],
                        price_at_analysis=float(db_analysis.price_at_analysis)
                    ))
                
                logger.info(f"Listed {len(summaries)} analyses for user {self.user_id}")
                return summaries
                
        except Exception as e:
            logger.error(f"Error listing analyses: {str(e)}")
            raise
    
    def _db_to_analysis_result(self, db_analysis: Analysis) -> AnalysisResult:
        """
        Convert database Analysis to AnalysisResult.
        
        Args:
            db_analysis: Database analysis record
            
        Returns:
            AnalysisResult
        """
        from models.schemas import (
            IndicatorResults, OverallSentiment, Signal, SignalExplanation
        )
        
        return AnalysisResult(
            id=db_analysis.id,
            coin=db_analysis.coin,
            timeframe=db_analysis.timeframe,
            timestamp=db_analysis.timestamp,
            technical_results=IndicatorResults(**db_analysis.technical_data),
            fundamental_results=OverallSentiment(**db_analysis.fundamental_data),
            signal=Signal(**db_analysis.signal),
            explanation=SignalExplanation(**{
                'signal': Signal(**db_analysis.signal),
                'technical_reasons': [],
                'fundamental_reasons': [],
                'supporting_indicators': [],
                'conflicting_indicators': [],
                'risk_factors': []
            }),
            ai_report=db_analysis.ai_report or "",
            actual_outcome=db_analysis.actual_outcome,
            price_at_analysis=float(db_analysis.price_at_analysis),
            price_after_period=float(db_analysis.price_after_period) if db_analysis.price_after_period else None
        )

    def compare_analyses(self, analysis_ids: List[str]) -> ComparisonReport:
        """
        Compare multiple analyses.
        
        Args:
            analysis_ids: List of analysis IDs to compare
            
        Returns:
            ComparisonReport with detailed comparison
            
        Validates: Requirements 16.3, 16.4
        """
        try:
            if len(analysis_ids) < 2:
                raise ValueError("At least 2 analyses required for comparison")
            
            # Retrieve all analyses
            analyses = []
            for analysis_id in analysis_ids:
                analysis = self.get_analysis(analysis_id)
                if not analysis:
                    raise ValueError(f"Analysis not found: {analysis_id}")
                analyses.append(analysis)
            
            # Calculate changes
            success_probability_changes = [
                a.signal.success_probability for a in analyses
            ]
            
            signal_changes = [
                a.signal.signal_type.value for a in analyses
            ]
            
            # Calculate indicator differences
            indicator_differences = {}
            
            # RSI changes
            indicator_differences['rsi'] = [
                a.technical_results.rsi for a in analyses
            ]
            
            # MACD changes
            indicator_differences['macd_histogram'] = [
                a.technical_results.macd.histogram for a in analyses
            ]
            
            # Bollinger Bands bandwidth changes
            indicator_differences['bollinger_bandwidth'] = [
                a.technical_results.bollinger.bandwidth for a in analyses
            ]
            
            # Confluence score changes
            indicator_differences['confluence_score'] = [
                a.technical_results.confluence_score for a in analyses
            ]
            
            # ATR changes
            indicator_differences['atr'] = [
                a.technical_results.atr.atr for a in analyses
            ]
            
            # Sentiment changes
            sentiment_changes = [
                a.fundamental_results.overall_score for a in analyses
            ]
            
            logger.info(f"Compared {len(analyses)} analyses")
            
            return ComparisonReport(
                analyses=analyses,
                success_probability_changes=success_probability_changes,
                signal_changes=signal_changes,
                indicator_differences=indicator_differences,
                sentiment_changes=sentiment_changes
            )
            
        except Exception as e:
            logger.error(f"Error comparing analyses: {str(e)}")
            raise
    
    def update_accuracy(
        self,
        analysis_id: str,
        actual_outcome: str
    ) -> None:
        """
        Update analysis with actual outcome.
        
        Args:
            analysis_id: Analysis ID
            actual_outcome: "correct" or "incorrect"
            
        Validates: Requirement 16.5
        """
        try:
            if actual_outcome not in ["correct", "incorrect"]:
                raise ValueError("actual_outcome must be 'correct' or 'incorrect'")
            
            with self.db_session_factory() as db:
                db_analysis = db.query(Analysis).filter(
                    Analysis.id == analysis_id,
                    Analysis.user_id == self.user_id
                ).first()
                
                if not db_analysis:
                    raise ValueError(f"Analysis not found: {analysis_id}")
                
                db_analysis.actual_outcome = actual_outcome
                db.commit()
                
                logger.info(f"Updated accuracy for analysis {analysis_id}: {actual_outcome}")
                
        except Exception as e:
            logger.error(f"Error updating accuracy: {str(e)}")
            raise
    
    def get_user_accuracy_stats(self) -> AccuracyStats:
        """
        Calculate user's overall prediction accuracy.
        
        Returns:
            AccuracyStats with detailed accuracy metrics
            
        Validates: Requirement 16.6
        """
        try:
            with self.db_session_factory() as db:
                # Get all analyses with outcomes
                analyses = db.query(Analysis).filter(
                    Analysis.user_id == self.user_id,
                    Analysis.actual_outcome.isnot(None)
                ).all()
                
                total_predictions = len(analyses)
                correct_predictions = sum(
                    1 for a in analyses if a.actual_outcome == "correct"
                )
                incorrect_predictions = sum(
                    1 for a in analyses if a.actual_outcome == "incorrect"
                )
                
                accuracy_rate = (
                    (correct_predictions / total_predictions * 100)
                    if total_predictions > 0 else 0.0
                )
                
                # Calculate accuracy by signal type
                by_signal_type = {}
                for analysis in analyses:
                    signal_type = analysis.signal['signal_type']
                    if signal_type not in by_signal_type:
                        by_signal_type[signal_type] = {
                            'total': 0,
                            'correct': 0,
                            'incorrect': 0
                        }
                    
                    by_signal_type[signal_type]['total'] += 1
                    if analysis.actual_outcome == "correct":
                        by_signal_type[signal_type]['correct'] += 1
                    else:
                        by_signal_type[signal_type]['incorrect'] += 1
                
                logger.info(f"Calculated accuracy stats for user {self.user_id}")
                
                return AccuracyStats(
                    total_predictions=total_predictions,
                    correct_predictions=correct_predictions,
                    incorrect_predictions=incorrect_predictions,
                    accuracy_rate=accuracy_rate,
                    by_signal_type=by_signal_type
                )
                
        except Exception as e:
            logger.error(f"Error calculating accuracy stats: {str(e)}")
            raise
