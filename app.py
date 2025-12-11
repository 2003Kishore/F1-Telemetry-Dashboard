"""
F1 Telemetry Analysis Dashboard
Interactive dashboard for race engineers
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
sys.path.append('src')

from data_fetcher import F1DataFetcher
from tyre_degradation import TyreDegradationAnalyzer
from fuel_correction import FuelCorrectedPaceAnalyzer
from stint_performance import StintPerformanceAnalyzer

# Page configuration
st.set_page_config(
    page_title="F1 Telemetry Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force English language
import os
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #E10600;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #15151E;
        font-weight: 600;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #E10600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_data' not in st.session_state:
    st.session_state.session_data = None
if 'selected_drivers' not in st.session_state:
    st.session_state.selected_drivers = []


@st.cache_data
def load_session_data(year, race, session_type):
    """Load F1 session data with caching"""
    fetcher = F1DataFetcher()
    session = fetcher.get_session(year, race, session_type)
    return session


def plot_lap_times(laps, driver_name):
    """Plot lap times over race distance"""
    # Convert lap times
    if pd.api.types.is_timedelta64_dtype(laps['LapTime']):
        laps = laps.copy()
        laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    else:
        laps = laps.copy()
        laps['LapTimeSeconds'] = laps['LapTime']
    
    # Remove outliers
    median = laps['LapTimeSeconds'].median()
    clean_laps = laps[laps['LapTimeSeconds'] < median * 1.5]
    
    fig = go.Figure()
    
    # Color by compound
    compounds = clean_laps['Compound'].unique()
    colors = {'SOFT': '#FF0000', 'MEDIUM': '#FFD700', 'HARD': '#FFFFFF', 
              'INTERMEDIATE': '#00FF00', 'WET': '#0000FF'}
    
    for compound in compounds:
        compound_laps = clean_laps[clean_laps['Compound'] == compound]
        fig.add_trace(go.Scatter(
            x=compound_laps['LapNumber'],
            y=compound_laps['LapTimeSeconds'],
            mode='lines+markers',
            name=compound,
            marker=dict(color=colors.get(compound, '#808080'), size=6),
            line=dict(color=colors.get(compound, '#808080'), width=2)
        ))
    
    fig.update_layout(
        title=f"Lap Times - {driver_name}",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        height=400,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig


def plot_tyre_degradation(stint_metrics):
    """Plot tyre degradation analysis"""
    if len(stint_metrics) == 0:
        return None
    
    fig = go.Figure()
    
    for _, row in stint_metrics.iterrows():
        stint_num = row['StintNumber']
        compound = row['Compound']
        fig.add_trace(go.Bar(
            name=f"Stint {stint_num} ({compound})",
            x=['Degradation Rate'],
            y=[row['DegradationRate']],
            text=[f"{row['DegradationRate']:.3f} s/lap"],
            textposition='auto'
        ))
    
    fig.update_layout(
        title="Tyre Degradation by Stint",
        yaxis_title="Degradation Rate (s/lap)",
        height=400,
        template='plotly_white'
    )
    
    return fig


def plot_fuel_corrected_pace(laps_dict):
    """Plot fuel-corrected pace comparison"""
    analyzer = FuelCorrectedPaceAnalyzer()
    
    fig = go.Figure()
    
    for driver_name, laps in laps_dict.items():
        corrected = analyzer.calculate_fuel_corrected_pace(laps)
        clean = corrected[corrected['CorrectedLapTime'].notna()]
        median = clean['CorrectedLapTime'].median()
        clean = clean[clean['CorrectedLapTime'] < median * 1.5]
        
        fig.add_trace(go.Scatter(
            x=clean['LapNumber'],
            y=clean['CorrectedLapTime'],
            mode='lines',
            name=driver_name,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="Fuel-Corrected Pace Comparison",
        xaxis_title="Lap Number",
        yaxis_title="Corrected Lap Time (seconds)",
        height=400,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig


def plot_telemetry_comparison(tel1, tel2, driver1, driver2):
    """Plot telemetry comparison between two drivers"""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Speed', 'Throttle', 'Brake'),
        shared_xaxes=True,
        vertical_spacing=0.08
    )
    
    # Speed
    fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], 
                             name=f"{driver1} Speed", line=dict(color='red')),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], 
                             name=f"{driver2} Speed", line=dict(color='blue')),
                  row=1, col=1)
    
    # Throttle
    fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Throttle'], 
                             name=f"{driver1} Throttle", line=dict(color='red'), 
                             showlegend=False),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Throttle'], 
                             name=f"{driver2} Throttle", line=dict(color='blue'), 
                             showlegend=False),
                  row=2, col=1)
    
    # Brake
    fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Brake'], 
                             name=f"{driver1} Brake", line=dict(color='red'), 
                             showlegend=False),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Brake'], 
                             name=f"{driver2} Brake", line=dict(color='blue'), 
                             showlegend=False),
                  row=3, col=1)
    
    fig.update_xaxes(title_text="Distance (m)", row=3, col=1)
    fig.update_yaxes(title_text="km/h", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_yaxes(title_text="%", row=3, col=1)
    
    fig.update_layout(height=800, template='plotly_white')
    
    return fig


# Main App
def main():
    st.markdown('<h1 class="main-header">🏎️ F1 Telemetry Analysis Dashboard</h1>', 
                unsafe_allow_html=True)
    st.markdown("### Real-time performance analysis for race engineers")
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.formula1.com/etc/designs/fom-website/images/f1_logo.svg", 
                 width=200)
        st.markdown("## ⚙️ Session Selection")
        
        year = st.selectbox("Year", [2024, 2023, 2022], index=0)
        race = st.selectbox("Race", [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
            "Miami", "Monaco", "Canada", "Spain", "Austria",
            "Great Britain", "Hungary", "Belgium", "Netherlands",
            "Italy", "Singapore", "United States", "Mexico",
            "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ])
        session_type = st.selectbox("Session", ["R (Race)", "Q (Qualifying)", 
                                                "FP1", "FP2", "FP3"], index=0)
        
        session_code = session_type.split()[0]
        
        if st.button(" Load Session", type="primary"):
            with st.spinner("Loading session data..."):
                try:
                    session = load_session_data(year, race, session_code)
                    st.session_state.session_data = session
                    st.success(" Session loaded!")
                except Exception as e:
                    st.error(f"Error loading session: {str(e)}")
    
    # Main content
    if st.session_state.session_data is None:
        st.info(" Select a session from the sidebar to begin analysis")
        
        # Show features
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🔧 Features")
            st.markdown("""
            - **Tyre Degradation Analysis**
            - **Fuel-Corrected Pace**
            - **Stint Performance**
            - **Telemetry Comparison**
            """)
        with col2:
            st.markdown("### 📊 Visualizations")
            st.markdown("""
            - **Lap Time Charts**
            - **Degradation Plots**
            - **Pace Comparison**
            - **Interactive Telemetry**
            """)
        with col3:
            st.markdown("### 💡 Insights")
            st.markdown("""
            - **Strategy Recommendations**
            - **Performance Ratings**
            - **Driver Comparisons**
            - **Real-time Metrics**
            """)
        
        return
    
    session = st.session_state.session_data
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "🔧 Tyre Degradation", "⛽ Fuel-Corrected Pace", 
        "📈 Stint Analysis", "🎯 Telemetry Comparison"
    ])
    
    # Get available drivers
    drivers = sorted(session.drivers)
    
    with tab1:
        st.markdown('<div class="sub-header">Race Overview</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Event", session.event['EventName'])
        with col2:
            st.metric("Session", session.name)
        with col3:
            st.metric("Drivers", len(drivers))
        with col4:
            st.metric("Total Laps", len(session.laps))
        
        st.markdown("---")
        
        # Fastest laps
        st.markdown("### ⚡ Fastest Laps")
        fetcher = F1DataFetcher()
        fastest_laps = fetcher.get_all_drivers_fastest_laps(session)
        
        if not fastest_laps.empty:
            fastest_laps_sorted = fastest_laps.sort_values('LapTime').head(10)
            st.dataframe(fastest_laps_sorted, use_container_width=True, height=400)
    
    with tab2:
        st.markdown('<div class="sub-header">Tyre Degradation Analysis</div>', unsafe_allow_html=True)
        
        driver_deg = st.selectbox("Select Driver for Degradation Analysis", drivers, key='deg_driver')
        
        if driver_deg:
            fetcher = F1DataFetcher()
            driver_laps = fetcher.get_stint_data(session, driver_deg)
            
            analyzer = TyreDegradationAnalyzer()
            stint_metrics = analyzer.calculate_degradation(driver_laps)
            
            if not stint_metrics.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Degradation plot
                    fig = plot_tyre_degradation(stint_metrics)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### 📋 Stint Summary")
                    for _, row in stint_metrics.iterrows():
                        st.markdown(f"""
                        **Stint {int(row['StintNumber'])} ({row['Compound']})**
                        - Length: {int(row['StintLength'])} laps
                        - Avg Time: {row['AvgLapTime']:.3f}s
                        - Degradation: {row['DegradationRate']:.4f} s/lap
                        - Consistency: {row['Consistency']:.3f}s
                        ---
                        """)
                
                # Detailed table
                st.markdown("### 📊 Detailed Stint Data")
                st.dataframe(stint_metrics, use_container_width=True)
            else:
                st.warning("No stint data available for this driver")
    
    with tab3:
        st.markdown('<div class="sub-header">Fuel-Corrected Pace Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            driver1_fuel = st.selectbox("Driver 1", drivers, key='fuel_driver1')
        with col2:
            driver2_fuel = st.selectbox("Driver 2", drivers, index=min(1, len(drivers)-1), key='fuel_driver2')
        
        if driver1_fuel and driver2_fuel:
            fetcher = F1DataFetcher()
            d1_laps = fetcher.get_driver_laps(session, driver1_fuel)
            d2_laps = fetcher.get_driver_laps(session, driver2_fuel)
            
            # Plot comparison
            fig = plot_fuel_corrected_pace({driver1_fuel: d1_laps, driver2_fuel: d2_laps})
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparison metrics
            analyzer = FuelCorrectedPaceAnalyzer()
            comparison = analyzer.compare_race_pace(d1_laps, d2_laps, driver1_fuel, driver2_fuel)
            
            st.markdown("### 📊 Pace Comparison")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"#### {driver1_fuel}")
                st.metric("Avg Corrected Pace", 
                         f"{comparison[driver1_fuel]['avg_corrected_pace']:.3f}s")
                st.metric("Best Lap", 
                         f"{comparison[driver1_fuel]['best_corrected_lap']:.3f}s")
                st.metric("Consistency", 
                         f"{comparison[driver1_fuel]['consistency_std']:.3f}s")
            
            with col2:
                st.markdown(f"#### {driver2_fuel}")
                st.metric("Avg Corrected Pace", 
                         f"{comparison[driver2_fuel]['avg_corrected_pace']:.3f}s")
                st.metric("Best Lap", 
                         f"{comparison[driver2_fuel]['best_corrected_lap']:.3f}s")
                st.metric("Consistency", 
                         f"{comparison[driver2_fuel]['consistency_std']:.3f}s")
            
            with col3:
                st.markdown("#### 🏆 Comparison")
                st.metric("Pace Delta", 
                         f"{comparison['comparison']['pace_delta_seconds']:.3f}s")
                st.metric("Faster Driver", 
                         comparison['comparison']['faster_driver'])
                st.metric("Advantage", 
                         f"{comparison['comparison']['pace_advantage_pct']:.2f}%")
    
    with tab4:
        st.markdown('<div class="sub-header">Stint Performance Analysis</div>', unsafe_allow_html=True)
        
        driver_stint = st.selectbox("Select Driver", drivers, key='stint_driver')
        
        if driver_stint:
            fetcher = F1DataFetcher()
            driver_laps = fetcher.get_stint_data(session, driver_stint)
            
            stint_analyzer = StintPerformanceAnalyzer()
            stints = stint_analyzer.analyze_all_stints(driver_laps)
            
            if stints:
                # Lap times plot
                fig = plot_lap_times(driver_laps, driver_stint)
                st.plotly_chart(fig, use_container_width=True)
                
                # Stint performance cards
                st.markdown("### 📊 Stint Performance Ratings")
                cols = st.columns(len(stints))
                
                for i, stint in enumerate(stints):
                    eval = stint_analyzer.evaluate_stint_performance(stint)
                    
                    with cols[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                        <h4>Stint {stint.stint_number} ({stint.compound})</h4>
                        <p><strong>Score:</strong> {eval['overall_score']:.1f}/100</p>
                        <p><strong>Rating:</strong> {eval['rating']}</p>
                        <p><strong>Length:</strong> {stint.stint_length} laps</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("Recommendations"):
                            for rec in eval['recommendations']:
                                st.write(f"• {rec}")
            else:
                st.warning("No stint data available")
    
    with tab5:
        st.markdown('<div class="sub-header">Telemetry Comparison</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            driver1_tel = st.selectbox("Driver 1", drivers, key='tel_driver1')
        with col2:
            driver2_tel = st.selectbox("Driver 2", drivers, index=min(1, len(drivers)-1), key='tel_driver2')
        
        use_fastest = st.checkbox("Use fastest laps", value=True)
        
        if not use_fastest:
            lap_number = st.number_input("Lap Number", min_value=1, value=1)
        else:
            lap_number = None
        
        if st.button("Compare Telemetry", type="primary"):
            with st.spinner("Loading telemetry data..."):
                try:
                    fetcher = F1DataFetcher()
                    tel1, tel2 = fetcher.get_lap_comparison(session, driver1_tel, driver2_tel, lap_number)
                    
                    fig = plot_telemetry_comparison(tel1, tel2, driver1_tel, driver2_tel)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Lap time comparison
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        lap1 = session.laps.pick_driver(driver1_tel).pick_fastest() if use_fastest else \
                               session.laps.pick_driver(driver1_tel).pick_lap(lap_number)
                        st.metric(f"{driver1_tel} Lap Time", 
                                 f"{lap1['LapTime'].total_seconds():.3f}s" if pd.notna(lap1['LapTime']) else "N/A")
                    with col2:
                        lap2 = session.laps.pick_driver(driver2_tel).pick_fastest() if use_fastest else \
                               session.laps.pick_driver(driver2_tel).pick_lap(lap_number)
                        st.metric(f"{driver2_tel} Lap Time", 
                                 f"{lap2['LapTime'].total_seconds():.3f}s" if pd.notna(lap2['LapTime']) else "N/A")
                    with col3:
                        if pd.notna(lap1['LapTime']) and pd.notna(lap2['LapTime']):
                            delta = lap1['LapTime'].total_seconds() - lap2['LapTime'].total_seconds()
                            st.metric("Delta", f"{delta:.3f}s")
                
                except Exception as e:
                    st.error(f"Error loading telemetry: {str(e)}")


if __name__ == "__main__":
    main()

