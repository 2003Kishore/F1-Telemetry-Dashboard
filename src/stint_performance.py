"""
Stint Performance Analyzer
Comprehensive analysis of stint strategies and performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StintMetrics:
    """Container for stint performance metrics"""
    stint_number: int
    compound: str
    start_lap: int
    end_lap: int
    stint_length: int
    avg_lap_time: float
    best_lap_time: float
    degradation_rate: float
    consistency: float
    fuel_corrected_pace: float
    tyre_age_start: int


class StintPerformanceAnalyzer:
    """Analyze stint performance and strategy effectiveness"""
    
    def __init__(self):
        """Initialize stint analyzer"""
        self.compound_characteristics = {
            'SOFT': {'grip': 1.0, 'durability': 0.6, 'warmup': 0.9},
            'MEDIUM': {'grip': 0.85, 'durability': 0.8, 'warmup': 0.7},
            'HARD': {'grip': 0.75, 'durability': 1.0, 'warmup': 0.5},
            'INTERMEDIATE': {'grip': 0.9, 'durability': 0.7, 'warmup': 0.8},
            'WET': {'grip': 0.95, 'durability': 0.9, 'warmup': 0.6}
        }
    
    def analyze_all_stints(self, laps: pd.DataFrame) -> List[StintMetrics]:
        """
        Analyze all stints in a race
        
        Args:
            laps: DataFrame with lap data
            
        Returns:
            List of StintMetrics objects
        """
        # Identify stints
        if 'StintNumber' not in laps.columns:
            laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()
        
        stints = []
        
        for stint_num in laps['StintNumber'].unique():
            stint_laps = laps[laps['StintNumber'] == stint_num].copy()
            
            if len(stint_laps) < 2:
                continue
            
            metrics = self._calculate_stint_metrics(stint_laps, stint_num)
            if metrics:
                stints.append(metrics)
        
        return stints
    
    def _calculate_stint_metrics(self, stint_laps: pd.DataFrame, 
                                stint_num: int) -> Optional[StintMetrics]:
        """Calculate metrics for a single stint"""
        # Convert lap times if needed
        if 'LapTimeSeconds' not in stint_laps.columns:
            if pd.api.types.is_timedelta64_dtype(stint_laps['LapTime']):
                stint_laps['LapTimeSeconds'] = stint_laps['LapTime'].dt.total_seconds()
            else:
                stint_laps['LapTimeSeconds'] = stint_laps['LapTime']
        
        # Remove outliers
        clean_laps = stint_laps[stint_laps['LapTimeSeconds'].notna()].copy()
        median = clean_laps['LapTimeSeconds'].median()
        clean_laps = clean_laps[clean_laps['LapTimeSeconds'] < median * 1.5]
        
        if len(clean_laps) < 2:
            return None
        
        # Calculate metrics
        compound = clean_laps['Compound'].iloc[0]
        start_lap = int(clean_laps['LapNumber'].iloc[0])
        end_lap = int(clean_laps['LapNumber'].iloc[-1])
        stint_length = len(clean_laps)
        
        avg_lap_time = clean_laps['LapTimeSeconds'].mean()
        best_lap_time = clean_laps['LapTimeSeconds'].min()
        consistency = clean_laps['LapTimeSeconds'].std()
        
        # Calculate degradation rate
        if len(clean_laps) >= 3:
            X = np.arange(len(clean_laps)).reshape(-1, 1)
            y = clean_laps['LapTimeSeconds'].values
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)
            degradation_rate = model.coef_[0]
        else:
            degradation_rate = 0.0
        
        # Fuel-corrected pace (simplified)
        fuel_corrected_pace = avg_lap_time - (stint_length * 1.6 * 0.035 / 2)  # Approximate
        
        # Tyre age at stint start
        tyre_age_start = int(stint_laps['TyreLife'].iloc[0]) if 'TyreLife' in stint_laps.columns else 0
        
        return StintMetrics(
            stint_number=stint_num,
            compound=compound,
            start_lap=start_lap,
            end_lap=end_lap,
            stint_length=stint_length,
            avg_lap_time=round(avg_lap_time, 3),
            best_lap_time=round(best_lap_time, 3),
            degradation_rate=round(degradation_rate, 4),
            consistency=round(consistency, 3),
            fuel_corrected_pace=round(fuel_corrected_pace, 3),
            tyre_age_start=tyre_age_start
        )
    
    def compare_stint_strategies(self, driver1_laps: pd.DataFrame,
                                driver2_laps: pd.DataFrame,
                                driver1_name: str,
                                driver2_name: str) -> Dict:
        """
        Compare stint strategies between two drivers
        
        Args:
            driver1_laps: Laps for driver 1
            driver2_laps: Laps for driver 2
            driver1_name: Name of driver 1
            driver2_name: Name of driver 2
            
        Returns:
            Dictionary with strategy comparison
        """
        d1_stints = self.analyze_all_stints(driver1_laps)
        d2_stints = self.analyze_all_stints(driver2_laps)
        
        comparison = {
            driver1_name: {
                'num_stints': len(d1_stints),
                'stints': [self._stint_to_dict(s) for s in d1_stints],
                'avg_stint_length': np.mean([s.stint_length for s in d1_stints]) if d1_stints else 0,
                'total_laps': sum([s.stint_length for s in d1_stints]) if d1_stints else 0
            },
            driver2_name: {
                'num_stints': len(d2_stints),
                'stints': [self._stint_to_dict(s) for s in d2_stints],
                'avg_stint_length': np.mean([s.stint_length for s in d2_stints]) if d2_stints else 0,
                'total_laps': sum([s.stint_length for s in d2_stints]) if d2_stints else 0
            }
        }
        
        # Strategy comparison
        d1_stops = len(d1_stints) - 1 if d1_stints else 0
        d2_stops = len(d2_stints) - 1 if d2_stints else 0
        
        comparison['strategy_analysis'] = {
            f'{driver1_name}_stops': d1_stops,
            f'{driver2_name}_stops': d2_stops,
            'strategy_difference': abs(d1_stops - d2_stops),
            'more_aggressive': driver1_name if d1_stops > d2_stops else driver2_name
        }
        
        return comparison
    
    def _stint_to_dict(self, stint: StintMetrics) -> Dict:
        """Convert StintMetrics to dictionary"""
        return {
            'stint_number': stint.stint_number,
            'compound': stint.compound,
            'laps': f"{stint.start_lap}-{stint.end_lap}",
            'length': stint.stint_length,
            'avg_time': stint.avg_lap_time,
            'best_time': stint.best_lap_time,
            'degradation': stint.degradation_rate,
            'consistency': stint.consistency
        }
    
    def evaluate_stint_performance(self, stint_metrics: StintMetrics) -> Dict:
        """
        Evaluate how well a stint was executed
        
        Args:
            stint_metrics: StintMetrics object
            
        Returns:
            Dictionary with performance evaluation
        """
        compound = stint_metrics.compound
        characteristics = self.compound_characteristics.get(compound, 
                                                           self.compound_characteristics['MEDIUM'])
        
        # Expected stint length based on compound
        expected_lengths = {
            'SOFT': 15,
            'MEDIUM': 25,
            'HARD': 35
        }
        expected_length = expected_lengths.get(compound, 20)
        
        # Performance scores (0-100)
        length_score = min(100, (stint_metrics.stint_length / expected_length) * 100)
        
        consistency_score = max(0, 100 - (stint_metrics.consistency * 100))
        
        # Degradation score (lower degradation = higher score)
        deg_threshold = 0.05  # 0.05s per lap is typical
        degradation_score = max(0, 100 - (abs(stint_metrics.degradation_rate) / deg_threshold) * 50)
        
        # Overall score
        overall_score = (length_score * 0.3 + consistency_score * 0.4 + 
                        degradation_score * 0.3)
        
        evaluation = {
            'overall_score': round(overall_score, 1),
            'length_score': round(length_score, 1),
            'consistency_score': round(consistency_score, 1),
            'degradation_score': round(degradation_score, 1),
            'rating': self._get_rating(overall_score),
            'recommendations': self._generate_recommendations(stint_metrics, overall_score)
        }
        
        return evaluation
    
    def _get_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Poor"
    
    def _generate_recommendations(self, stint: StintMetrics, 
                                 score: float) -> List[str]:
        """Generate recommendations based on stint performance"""
        recommendations = []
        
        # Check stint length
        if stint.stint_length < 10:
            recommendations.append("Stint too short - consider extending next stint")
        
        # Check consistency
        if stint.consistency > 0.5:
            recommendations.append("High lap time variation - focus on consistency")
        
        # Check degradation
        if stint.degradation_rate > 0.1:
            recommendations.append("High degradation - consider earlier pit stop or tyre saving")
        elif stint.degradation_rate < 0:
            recommendations.append("Improving pace through stint - good tyre management")
        
        # Overall performance
        if score > 85:
            recommendations.append("Excellent stint execution - maintain this performance")
        elif score < 50:
            recommendations.append("Review telemetry for areas of improvement")
        
        return recommendations if recommendations else ["Good stint performance"]
    
    def analyze_undercut_opportunity(self, leader_laps: pd.DataFrame,
                                    follower_laps: pd.DataFrame,
                                    current_lap: int) -> Dict:
        """
        Analyze if undercut strategy would be effective
        
        Args:
            leader_laps: Laps for leading driver
            follower_laps: Laps for following driver
            current_lap: Current lap number
            
        Returns:
            Dictionary with undercut analysis
        """
        # Get recent pace (last 3 laps)
        leader_recent = leader_laps[leader_laps['LapNumber'] >= current_lap - 3]
        follower_recent = follower_laps[follower_laps['LapNumber'] >= current_lap - 3]
        
        if len(leader_recent) == 0 or len(follower_recent) == 0:
            return {'undercut_viable': False, 'reason': 'Insufficient data'}
        
        # Convert lap times
        if 'LapTimeSeconds' not in leader_recent.columns:
            if pd.api.types.is_timedelta64_dtype(leader_recent['LapTime']):
                leader_recent = leader_recent.copy()
                leader_recent['LapTimeSeconds'] = leader_recent['LapTime'].dt.total_seconds()
                follower_recent = follower_recent.copy()
                follower_recent['LapTimeSeconds'] = follower_recent['LapTime'].dt.total_seconds()
        
        leader_pace = leader_recent['LapTimeSeconds'].mean()
        follower_pace = follower_recent['LapTimeSeconds'].mean()
        
        # Pit stop time (typical F1 pit stop)
        pit_time_loss = 22.0  # seconds
        
        # Estimated gain from new tyres (first lap)
        new_tyre_advantage = 1.5  # seconds
        
        # Check if undercut is viable
        pace_deficit = follower_pace - leader_pace
        undercut_gain = new_tyre_advantage - pit_time_loss / 2  # Simplified
        
        undercut_viable = undercut_gain > pace_deficit
        
        analysis = {
            'undercut_viable': undercut_viable,
            'leader_pace': round(leader_pace, 3),
            'follower_pace': round(follower_pace, 3),
            'pace_deficit': round(pace_deficit, 3),
            'estimated_undercut_gain': round(undercut_gain, 3),
            'recommendation': 'Pit now for undercut' if undercut_viable else 'Stay out'
        }
        
        return analysis


if __name__ == "__main__":
    print("Stint Performance Analyzer - Use with real F1 data")
    print("Provides comprehensive stint strategy analysis")

