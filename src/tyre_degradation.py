"""
Tyre Degradation Analysis Module
Detects tyre deg patterns and predicts performance drop-off
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression, RANSACRegressor
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')


class TyreDegradationAnalyzer:
    """Analyze tyre degradation from lap time data"""
    
    def __init__(self):
        """Initialize degradation analyzer"""
        self.models = {}
        
    def calculate_degradation(self, laps: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate tyre degradation metrics per stint
        
        Args:
            laps: DataFrame with lap data including TyreAge, LapTime, Compound
            
        Returns:
            DataFrame with degradation metrics per stint
        """
        # Ensure we have required columns
        required_cols = ['LapTime', 'Compound', 'TyreLife']
        if not all(col in laps.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        
        # Convert LapTime to seconds if it's timedelta
        if pd.api.types.is_timedelta64_dtype(laps['LapTime']):
            laps = laps.copy()
            laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
        else:
            laps = laps.copy()
            laps['LapTimeSeconds'] = laps['LapTime']
        
        # Remove outliers (pit laps, slow laps, etc.)
        laps = self._remove_outliers(laps)
        
        # Identify stints
        if 'StintNumber' not in laps.columns:
            laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()
        
        # Calculate degradation per stint
        stint_metrics = []
        
        for stint_num in laps['StintNumber'].unique():
            stint_laps = laps[laps['StintNumber'] == stint_num].copy()
            
            if len(stint_laps) < 3:  # Need minimum laps for meaningful analysis
                continue
            
            metrics = self._analyze_stint(stint_laps, stint_num)
            stint_metrics.append(metrics)
        
        return pd.DataFrame(stint_metrics)
    
    def _remove_outliers(self, laps: pd.DataFrame) -> pd.DataFrame:
        """Remove outlier laps (pits, incidents, etc.)"""
        # Remove NaN lap times
        laps = laps[laps['LapTimeSeconds'].notna()].copy()
        
        if len(laps) == 0:
            return laps
        
        # Remove laps > 1.5x median (likely pit laps or incidents)
        median_time = laps['LapTimeSeconds'].median()
        laps = laps[laps['LapTimeSeconds'] < median_time * 1.5]
        
        # Remove first lap (often slower due to traffic)
        laps = laps[laps['LapNumber'] > 1]
        
        return laps
    
    def _analyze_stint(self, stint_laps: pd.DataFrame, stint_num: int) -> Dict:
        """
        Analyze degradation for a single stint
        
        Args:
            stint_laps: Laps in this stint
            stint_num: Stint number
            
        Returns:
            Dictionary with stint degradation metrics
        """
        # Basic info
        compound = stint_laps['Compound'].iloc[0]
        stint_length = len(stint_laps)
        
        # Calculate tyre age if not present
        if 'TyreAge' not in stint_laps.columns:
            stint_laps['TyreAge'] = range(1, len(stint_laps) + 1)
        
        X = stint_laps['TyreAge'].values.reshape(-1, 1)
        y = stint_laps['LapTimeSeconds'].values
        
        # Linear degradation (seconds per lap)
        try:
            model = RANSACRegressor(random_state=42)  # Robust to outliers
            model.fit(X, y)
            deg_rate = model.estimator_.coef_[0]  # seconds per lap
        except:
            deg_rate = 0.0
        
        # Calculate statistics
        first_lap_time = y[0]
        last_lap_time = y[-1]
        avg_lap_time = y.mean()
        std_lap_time = y.std()
        
        # Total degradation over stint
        total_deg = last_lap_time - first_lap_time
        
        # Consistency metric (lower is better)
        consistency = std_lap_time
        
        # Predict lap time at various tyre ages
        predicted_at_lap_10 = first_lap_time + (deg_rate * 10)
        predicted_at_lap_20 = first_lap_time + (deg_rate * 20)
        
        return {
            'StintNumber': stint_num,
            'Compound': compound,
            'StintLength': stint_length,
            'DegradationRate': deg_rate,  # seconds/lap
            'DegradationPct': (deg_rate / first_lap_time) * 100,  # percentage per lap
            'TotalDegradation': total_deg,
            'FirstLapTime': first_lap_time,
            'LastLapTime': last_lap_time,
            'AvgLapTime': avg_lap_time,
            'Consistency': consistency,
            'PredictedLap10': predicted_at_lap_10,
            'PredictedLap20': predicted_at_lap_20
        }
    
    def compare_tyre_compounds(self, laps: pd.DataFrame) -> pd.DataFrame:
        """
        Compare degradation across different tyre compounds
        
        Args:
            laps: DataFrame with lap data
            
        Returns:
            DataFrame comparing compounds
        """
        stint_data = self.calculate_degradation(laps)
        
        if len(stint_data) == 0:
            return pd.DataFrame()
        
        compound_comparison = stint_data.groupby('Compound').agg({
            'DegradationRate': 'mean',
            'DegradationPct': 'mean',
            'AvgLapTime': 'mean',
            'Consistency': 'mean',
            'StintLength': 'mean'
        }).round(3)
        
        return compound_comparison
    
    def predict_optimal_stint_length(self, laps: pd.DataFrame, 
                                     target_laptime: float,
                                     compound: str) -> int:
        """
        Predict optimal stint length before lap times exceed target
        
        Args:
            laps: DataFrame with lap data
            target_laptime: Target lap time threshold
            compound: Tyre compound to analyze
            
        Returns:
            Optimal stint length in laps
        """
        compound_laps = laps[laps['Compound'] == compound]
        
        if len(compound_laps) == 0:
            return 0
        
        stint_data = self.calculate_degradation(compound_laps)
        
        if len(stint_data) == 0:
            return 0
        
        avg_deg_rate = stint_data['DegradationRate'].mean()
        avg_first_lap = stint_data['FirstLapTime'].mean()
        
        # Calculate laps until target time is exceeded
        if avg_deg_rate <= 0:
            return 999  # No degradation detected
        
        laps_until_target = (target_laptime - avg_first_lap) / avg_deg_rate
        
        return max(1, int(laps_until_target))
    
    def detect_cliff(self, laps: pd.DataFrame) -> Optional[int]:
        """
        Detect performance "cliff" - sudden degradation increase
        
        Args:
            laps: DataFrame with stint laps
            
        Returns:
            Lap number where cliff occurs, or None
        """
        if len(laps) < 5:
            return None
        
        laps = self._remove_outliers(laps)
        
        if len(laps) < 5:
            return None
        
        lap_times = laps['LapTimeSeconds'].values
        
        # Calculate rolling gradient
        window = 3
        gradients = []
        
        for i in range(len(lap_times) - window):
            slope = (lap_times[i + window] - lap_times[i]) / window
            gradients.append(slope)
        
        # Detect if gradient suddenly increases (cliff)
        if len(gradients) < 3:
            return None
        
        avg_gradient = np.mean(gradients[:-1])
        last_gradient = gradients[-1]
        
        # Cliff detected if last gradient is 2x average
        if last_gradient > avg_gradient * 2 and last_gradient > 0.1:
            cliff_lap = laps.iloc[len(laps) - window]['LapNumber']
            return int(cliff_lap)
        
        return None
    
    def generate_degradation_report(self, laps: pd.DataFrame, 
                                   driver: str) -> Dict:
        """
        Generate comprehensive degradation report
        
        Args:
            laps: DataFrame with lap data
            driver: Driver name
            
        Returns:
            Dictionary with complete degradation analysis
        """
        stint_metrics = self.calculate_degradation(laps)
        compound_comparison = self.compare_tyre_compounds(laps)
        
        report = {
            'driver': driver,
            'total_laps': len(laps),
            'stints': len(stint_metrics),
            'stint_details': stint_metrics.to_dict('records'),
            'compound_comparison': compound_comparison.to_dict() if not compound_comparison.empty else {},
            'average_degradation': stint_metrics['DegradationRate'].mean() if len(stint_metrics) > 0 else 0,
            'most_consistent_stint': stint_metrics.loc[stint_metrics['Consistency'].idxmin()].to_dict() if len(stint_metrics) > 0 else {}
        }
        
        return report


if __name__ == "__main__":
    print("Tyre Degradation Analyzer - Use with real F1 data")
    print("Example usage in main dashboard application")

