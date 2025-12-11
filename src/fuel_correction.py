"""
Fuel-Corrected Pace Analysis
Adjusts lap times for fuel load to compare true car pace
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from sklearn.linear_model import LinearRegression


class FuelCorrectedPaceAnalyzer:
    """Analyze and correct lap times for fuel load effects"""
    
    def __init__(self, fuel_effect: float = 0.035):
        """
        Initialize fuel correction analyzer
        
        Args:
            fuel_effect: Time penalty per kg of fuel (default 0.035s/kg for F1)
        """
        self.fuel_effect = fuel_effect  # seconds per kg
        self.kg_per_lap = 1.6  # Approximate fuel consumption per lap in F1
        
    def calculate_fuel_corrected_pace(self, laps: pd.DataFrame,
                                     race_laps: int = 57) -> pd.DataFrame:
        """
        Calculate fuel-corrected lap times
        
        Args:
            laps: DataFrame with lap data
            race_laps: Total race distance in laps
            
        Returns:
            DataFrame with fuel-corrected times
        """
        laps = laps.copy()
        
        # Convert LapTime to seconds if needed
        if 'LapTimeSeconds' not in laps.columns:
            if pd.api.types.is_timedelta64_dtype(laps['LapTime']):
                laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
            else:
                laps['LapTimeSeconds'] = laps['LapTime']
        
        # Calculate fuel load at each lap
        laps['LapsRemaining'] = race_laps - laps['LapNumber']
        laps['EstimatedFuelLoad'] = laps['LapsRemaining'] * self.kg_per_lap
        
        # Calculate fuel correction
        laps['FuelCorrection'] = laps['EstimatedFuelLoad'] * self.fuel_effect
        
        # Corrected lap time (what the lap time would be with empty tank)
        laps['CorrectedLapTime'] = laps['LapTimeSeconds'] - laps['FuelCorrection']
        
        # Calculate pace delta from personal best corrected time
        if len(laps) > 0:
            personal_best = laps['CorrectedLapTime'].min()
            laps['DeltaToBest'] = laps['CorrectedLapTime'] - personal_best
        
        return laps
    
    def compare_race_pace(self, laps_driver1: pd.DataFrame,
                         laps_driver2: pd.DataFrame,
                         driver1_name: str, driver2_name: str,
                         race_laps: int = 57) -> Dict:
        """
        Compare fuel-corrected race pace between two drivers
        
        Args:
            laps_driver1: Laps for driver 1
            laps_driver2: Laps for driver 2
            driver1_name: Name of driver 1
            driver2_name: Name of driver 2
            race_laps: Total race laps
            
        Returns:
            Dictionary with pace comparison
        """
        # Get corrected times
        d1_corrected = self.calculate_fuel_corrected_pace(laps_driver1, race_laps)
        d2_corrected = self.calculate_fuel_corrected_pace(laps_driver2, race_laps)
        
        # Clean data (remove outliers)
        d1_clean = self._remove_outliers(d1_corrected)
        d2_clean = self._remove_outliers(d2_corrected)
        
        # Calculate average corrected pace
        d1_avg_pace = d1_clean['CorrectedLapTime'].mean()
        d2_avg_pace = d2_clean['CorrectedLapTime'].mean()
        
        pace_delta = d1_avg_pace - d2_avg_pace
        
        comparison = {
            driver1_name: {
                'avg_corrected_pace': round(d1_avg_pace, 3),
                'best_corrected_lap': round(d1_clean['CorrectedLapTime'].min(), 3),
                'consistency_std': round(d1_clean['CorrectedLapTime'].std(), 3),
                'laps_analyzed': len(d1_clean)
            },
            driver2_name: {
                'avg_corrected_pace': round(d2_avg_pace, 3),
                'best_corrected_lap': round(d2_clean['CorrectedLapTime'].min(), 3),
                'consistency_std': round(d2_clean['CorrectedLapTime'].std(), 3),
                'laps_analyzed': len(d2_clean)
            },
            'comparison': {
                'pace_delta_seconds': round(pace_delta, 3),
                'faster_driver': driver1_name if pace_delta < 0 else driver2_name,
                'pace_advantage_pct': round(abs(pace_delta / d2_avg_pace) * 100, 2)
            }
        }
        
        return comparison
    
    def _remove_outliers(self, laps: pd.DataFrame) -> pd.DataFrame:
        """Remove outlier laps for pace analysis"""
        laps = laps[laps['CorrectedLapTime'].notna()].copy()
        
        if len(laps) == 0:
            return laps
        
        # Remove laps more than 1.5x median (pit stops, incidents)
        median_time = laps['CorrectedLapTime'].median()
        laps = laps[laps['CorrectedLapTime'] < median_time * 1.5]
        
        # Remove first lap (often slower)
        laps = laps[laps['LapNumber'] > 1]
        
        return laps
    
    def analyze_stint_pace(self, laps: pd.DataFrame, 
                          race_laps: int = 57) -> pd.DataFrame:
        """
        Analyze fuel-corrected pace per stint
        
        Args:
            laps: DataFrame with lap data
            race_laps: Total race laps
            
        Returns:
            DataFrame with stint pace analysis
        """
        laps = self.calculate_fuel_corrected_pace(laps, race_laps)
        
        # Identify stints
        if 'StintNumber' not in laps.columns:
            laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()
        
        # Analyze each stint
        stint_analysis = []
        
        for stint_num in laps['StintNumber'].unique():
            stint_laps = laps[laps['StintNumber'] == stint_num].copy()
            stint_clean = self._remove_outliers(stint_laps)
            
            if len(stint_clean) < 2:
                continue
            
            analysis = {
                'StintNumber': stint_num,
                'Compound': stint_laps['Compound'].iloc[0],
                'StintLength': len(stint_laps),
                'AvgCorrectedPace': stint_clean['CorrectedLapTime'].mean(),
                'BestCorrectedLap': stint_clean['CorrectedLapTime'].min(),
                'Consistency': stint_clean['CorrectedLapTime'].std(),
                'AvgFuelLoad': stint_clean['EstimatedFuelLoad'].mean()
            }
            
            stint_analysis.append(analysis)
        
        return pd.DataFrame(stint_analysis)
    
    def calculate_true_pace_advantage(self, qual_time: float, 
                                     race_pace: float,
                                     fuel_load: float = 110) -> Dict:
        """
        Calculate true pace advantage accounting for fuel
        
        Args:
            qual_time: Qualifying lap time (low fuel)
            race_pace: Average race lap time (high fuel)
            fuel_load: Starting fuel load in kg
            
        Returns:
            Dictionary with pace analysis
        """
        # Expected time loss from fuel
        expected_fuel_penalty = fuel_load * self.fuel_effect
        
        # Fuel-corrected race pace
        corrected_race_pace = race_pace - expected_fuel_penalty
        
        # True pace degradation (not fuel-related)
        true_pace_loss = corrected_race_pace - qual_time
        
        return {
            'qualifying_time': qual_time,
            'race_pace': race_pace,
            'fuel_effect': expected_fuel_penalty,
            'corrected_race_pace': corrected_race_pace,
            'true_pace_loss': true_pace_loss,
            'true_pace_loss_pct': (true_pace_loss / qual_time) * 100
        }
    
    def estimate_optimal_fuel_strategy(self, laps: pd.DataFrame,
                                      race_distance: int = 57) -> Dict:
        """
        Estimate optimal fuel strategy based on pace data
        
        Args:
            laps: Historical lap data
            race_distance: Race distance in laps
            
        Returns:
            Dictionary with fuel strategy recommendations
        """
        corrected = self.calculate_fuel_corrected_pace(laps, race_distance)
        clean = self._remove_outliers(corrected)
        
        if len(clean) == 0:
            return {}
        
        # Calculate pace consistency
        consistency = clean['CorrectedLapTime'].std()
        
        # Estimate fuel saving potential
        best_pace = clean['CorrectedLapTime'].min()
        avg_pace = clean['CorrectedLapTime'].mean()
        pace_margin = avg_pace - best_pace
        
        # Fuel that could be saved by managing pace
        potential_fuel_saving = pace_margin / self.fuel_effect
        
        strategy = {
            'best_corrected_pace': round(best_pace, 3),
            'avg_corrected_pace': round(avg_pace, 3),
            'pace_margin': round(pace_margin, 3),
            'consistency': round(consistency, 3),
            'potential_fuel_saving_kg': round(potential_fuel_saving, 1),
            'recommendation': 'Push' if consistency < 0.2 else 'Fuel Save' if pace_margin > 0.5 else 'Maintain'
        }
        
        return strategy


if __name__ == "__main__":
    print("Fuel-Corrected Pace Analyzer - Use with real F1 data")
    print("Accounts for ~0.035s/kg fuel effect")

