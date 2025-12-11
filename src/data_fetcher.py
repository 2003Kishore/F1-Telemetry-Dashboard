"""
F1 Data Fetcher using FastF1 API
Fetches telemetry, lap times, and session data
"""

import fastf1
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Enable FastF1 cache
fastf1.Cache.enable_cache('cache')


class F1DataFetcher:
    """Fetch F1 telemetry and session data using FastF1 API"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize data fetcher
        
        Args:
            cache_dir: Directory for caching downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
    def get_session(self, year: int, race: str, session_type: str = 'R'):
        """
        Load an F1 session
        
        Args:
            year: Year (e.g., 2024)
            race: Race name or round number (e.g., 'Monaco', 'Bahrain', 1, 2)
            session_type: 'FP1', 'FP2', 'FP3', 'Q', 'S' (Sprint), 'R' (Race)
            
        Returns:
            FastF1 Session object
        """
        print(f"Loading {year} {race} {session_type}...")
        session = fastf1.get_session(year, race, session_type)
        session.load()
        print(f"Session loaded: {session.event['EventName']} - {session.name}")
        return session
    
    def get_driver_laps(self, session, driver: str) -> pd.DataFrame:
        """
        Get all laps for a specific driver
        
        Args:
            session: FastF1 Session object
            driver: Driver abbreviation (e.g., 'VER', 'HAM', 'LEC')
            
        Returns:
            DataFrame with lap data
        """
        laps = session.laps.pick_driver(driver)
        return laps
    
    def get_telemetry(self, lap) -> pd.DataFrame:
        """
        Get telemetry data for a specific lap
        
        Args:
            lap: FastF1 Lap object
            
        Returns:
            DataFrame with telemetry (Speed, Throttle, Brake, RPM, Gear, DRS)
        """
        telemetry = lap.get_telemetry()
        return telemetry
    
    def get_stint_data(self, session, driver: str) -> pd.DataFrame:
        """
        Get stint information for a driver
        
        Args:
            session: FastF1 Session object
            driver: Driver abbreviation
            
        Returns:
            DataFrame with stint data including tyre compound and age
        """
        laps = self.get_driver_laps(session, driver)
        
        # Add stint number
        laps['StintNumber'] = (laps['Compound'] != laps['Compound'].shift()).cumsum()
        
        # Calculate tyre age
        laps['TyreAge'] = laps.groupby('StintNumber').cumcount() + 1
        
        return laps
    
    def get_all_drivers_fastest_laps(self, session) -> pd.DataFrame:
        """
        Get fastest lap for each driver
        
        Args:
            session: FastF1 Session object
            
        Returns:
            DataFrame with fastest lap per driver
        """
        fastest_laps = []
        
        for driver in session.drivers:
            try:
                driver_laps = session.laps.pick_driver(driver)
                if len(driver_laps) > 0:
                    fastest = driver_laps.pick_fastest()
                    if fastest is not None:
                        fastest_laps.append({
                            'Driver': driver,
                            'Team': fastest['Team'],
                            'LapTime': fastest['LapTime'].total_seconds() if pd.notna(fastest['LapTime']) else None,
                            'LapNumber': fastest['LapNumber'],
                            'Compound': fastest['Compound'],
                            'TyreLife': fastest['TyreLife'],
                            'Sector1Time': fastest['Sector1Time'].total_seconds() if pd.notna(fastest['Sector1Time']) else None,
                            'Sector2Time': fastest['Sector2Time'].total_seconds() if pd.notna(fastest['Sector2Time']) else None,
                            'Sector3Time': fastest['Sector3Time'].total_seconds() if pd.notna(fastest['Sector3Time']) else None,
                        })
            except Exception as e:
                print(f"Error getting fastest lap for {driver}: {e}")
                continue
        
        return pd.DataFrame(fastest_laps)
    
    def get_lap_comparison(self, session, driver1: str, driver2: str, 
                          lap_number: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Compare telemetry between two drivers
        
        Args:
            session: FastF1 Session object
            driver1: First driver abbreviation
            driver2: Second driver abbreviation
            lap_number: Specific lap number (if None, uses fastest laps)
            
        Returns:
            Tuple of (driver1_telemetry, driver2_telemetry)
        """
        if lap_number:
            lap1 = session.laps.pick_driver(driver1).pick_lap(lap_number)
            lap2 = session.laps.pick_driver(driver2).pick_lap(lap_number)
        else:
            lap1 = session.laps.pick_driver(driver1).pick_fastest()
            lap2 = session.laps.pick_driver(driver2).pick_fastest()
        
        tel1 = self.get_telemetry(lap1)
        tel2 = self.get_telemetry(lap2)
        
        return tel1, tel2
    
    def export_race_data(self, year: int, race: str, 
                        drivers: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Export comprehensive race data for analysis
        
        Args:
            year: Year
            race: Race name/number
            drivers: List of driver abbreviations (if None, exports all)
            
        Returns:
            Dictionary with 'laps', 'weather', and 'results' DataFrames
        """
        session = self.get_session(year, race, 'R')
        
        data = {
            'laps': session.laps,
            'weather': session.weather_data,
            'results': session.results
        }
        
        if drivers:
            data['laps'] = data['laps'][data['laps']['Driver'].isin(drivers)]
        
        return data
    
    def save_session_data(self, session, output_dir: str = "data"):
        """
        Save session data to CSV files
        
        Args:
            session: FastF1 Session object
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        event_name = session.event['EventName'].replace(' ', '_')
        session_name = session.name.replace(' ', '_')
        
        # Save laps
        laps_file = output_path / f"{event_name}_{session_name}_laps.csv"
        session.laps.to_csv(laps_file, index=False)
        print(f"Saved laps to: {laps_file}")
        
        # Save results
        results_file = output_path / f"{event_name}_{session_name}_results.csv"
        session.results.to_csv(results_file, index=False)
        print(f"Saved results to: {results_file}")
        
        # Save weather
        weather_file = output_path / f"{event_name}_{session_name}_weather.csv"
        session.weather_data.to_csv(weather_file, index=False)
        print(f"Saved weather to: {weather_file}")


if __name__ == "__main__":
    # Example usage
    fetcher = F1DataFetcher()
    
    # Load 2024 Bahrain GP Race
    session = fetcher.get_session(2024, 'Bahrain', 'R')
    
    # Get Verstappen's laps
    ver_laps = fetcher.get_driver_laps(session, 'VER')
    print(f"\nVerstappen laps: {len(ver_laps)}")
    print(ver_laps[['LapNumber', 'LapTime', 'Compound', 'TyreLife']].head(10))
    
    # Get fastest laps
    fastest = fetcher.get_all_drivers_fastest_laps(session)
    print(f"\nFastest laps:")
    print(fastest.sort_values('LapTime').head(10))
    
    # Save data
    fetcher.save_session_data(session)

