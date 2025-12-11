# 📘 F1 Telemetry Dashboard - Usage Guide

## 🚀 Getting Started (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `fastf1` - F1 data API  
- `streamlit` - Dashboard framework
- `plotly` - Interactive charts
- Plus data science libraries (pandas, numpy, scikit-learn)

### Step 2: Launch Dashboard
```bash
streamlit run app.py
```

Dashboard opens automatically at: `http://localhost:8501`

### Step 3: Load Your First Session

1. **In the sidebar**, select:
   - Year: `2024`
   - Race: `Bahrain`
   - Session: `R (Race)`

2. Click **"🔄 Load Session"**

3. Wait 5-10 seconds (first load downloads data)

4. ✅ You'll see "Session loaded!" when ready

## 📊 Dashboard Tour

### Tab 1: Overview
**What it shows**: Race summary and fastest laps

**How to use**:
- View event details
- See driver count and total laps
- Check top 10 fastest laps table

**Use case**: Quick race summary

---

### Tab 2: Tyre Degradation 🔧
**What it shows**: How tyres lose performance over a stint

**How to use**:
1. Select driver from dropdown (e.g., "VER" for Verstappen)
2. View degradation chart (bars show s/lap loss)
3. Read stint summary cards
4. Check detailed table at bottom

**Key Metrics**:
- **Degradation Rate**: e.g., 0.0450 s/lap
- **Total Degradation**: Total time lost over stint
- **Consistency**: Lower = more consistent

**Use case**: "Should we pit now or extend the stint?"

**Example**:
- Soft tyres: 0.08-0.12 s/lap → Pit after 10-15 laps
- Medium tyres: 0.04-0.07 s/lap → Can go 20-30 laps
- Hard tyres: 0.02-0.05 s/lap → 30-40+ laps

---

### Tab 3: Fuel-Corrected Pace ⛽
**What it shows**: True car pace without fuel weight effects

**How to use**:
1. Select Driver 1 (e.g., "VER")
2. Select Driver 2 (e.g., "HAM")
3. View corrected pace chart
4. Compare metrics below chart

**Key Metrics**:
- **Avg Corrected Pace**: True average pace
- **Best Lap**: Fastest corrected lap
- **Pace Delta**: Time difference between drivers
- **Faster Driver**: Who's genuinely quicker

**Use case**: "Is Driver A faster or just on fresher tyres?"

**Why it matters**:
- 110kg fuel at start = ~3.85s slower than empty
- Fuel burns ~1.6 kg/lap = ~0.056s improvement/lap
- Correction removes this effect to show true pace

---

### Tab 4: Stint Analysis 📈
**What it shows**: How well each stint was executed

**How to use**:
1. Select driver
2. View lap time chart (color-coded by compound)
3. See performance cards for each stint
4. Click "Recommendations" for AI insights

**Performance Scores** (0-100):
- **90+ = Excellent**: Perfect execution
- **75+ = Good**: Strong performance
- **60+ = Average**: Room for improvement
- **<60 = Poor**: Significant issues

**Scoring Breakdown**:
- Length (30%): Did we maximize stint?
- Consistency (40%): Were lap times stable?
- Degradation (30%): Was tyre wear managed?

**Use case**: "Why did we lose time in Stint 2?"

**Example Recommendations**:
- "Stint too short - consider extending next stint"
- "High degradation - consider earlier pit or tyre saving"
- "Excellent stint execution - maintain this performance"

---

### Tab 5: Telemetry Comparison 🎯
**What it shows**: Detailed speed/throttle/brake comparison

**How to use**:
1. Select two drivers
2. Choose "Use fastest laps" (or specify lap number)
3. Click "Compare Telemetry"
4. Analyze 3 charts: Speed, Throttle, Brake

**What to look for**:
- **Speed differences**: Where is one driver faster?
- **Throttle application**: Earlier/later/smoother?
- **Braking points**: Later braking = faster lap

**Use case**: "How is Driver A 0.3s faster in Sector 2?"

**Reading the charts**:
- Red line = Driver 1
- Blue line = Driver 2
- X-axis = Distance around track (meters)
- Overlapping = similar technique
- Gaps = performance difference

---

## 💡 Real-World Scenarios

### Scenario 1: Race Strategy Call
**Question**: "Should Verstappen pit now (Lap 15 on Softs) or extend?"

**Steps**:
1. Go to **Tyre Degradation** tab
2. Select "VER"
3. Check current stint degradation rate
4. Decision:
   - If deg > 0.10 s/lap → **Pit now**
   - If deg < 0.05 s/lap → **Stay out 5 more laps**
   - If between → **Monitor next 2 laps**

### Scenario 2: Driver Comparison
**Question**: "Hamilton looks faster, but is it just fresher tyres?"

**Steps**:
1. Go to **Fuel-Corrected Pace** tab
2. Select "HAM" vs "RUS"
3. Check corrected pace delta
4. Answer:
   - If delta > 0.2s → **Genuinely faster**
   - If delta < 0.1s → **Similar pace, tyres/fuel effect**

### Scenario 3: Post-Race Analysis
**Question**: "Why did we finish P5 instead of P3?"

**Steps**:
1. Go to **Stint Analysis** tab
2. Select your driver
3. Check performance scores
4. Compare with competitors (load their data too)
5. Identify:
   - Which stint had issues?
   - Was it strategy (wrong compound/timing)?
   - Was it execution (high degradation/inconsistency)?

### Scenario 4: Qualifying Comparison
**Question**: "Where am I losing time to pole position?"

**Steps**:
1. Load Qualifying session (not Race)
2. Go to **Telemetry Comparison** tab
3. Select yourself vs pole sitter
4. Use fastest laps
5. Analyze:
   - Speed traces: Where are you slower?
   - Throttle: Are you lifting where they're not?
   - Braking: Are they braking later?
6. Target improvements for next session

---

## 🔧 Tips & Tricks

### Tip 1: Data Loading
- **First load**: 5-10 seconds (downloads from FastF1)
- **Cached load**: <1 second (uses local cache)
- **Cache location**: `cache/` folder
- **Clear cache**: Delete `cache/` folder if issues

### Tip 2: Driver Abbreviations
- Use 3-letter codes: VER, HAM, LEC, NOR, etc.
- Full list appears in dropdowns
- Abbreviations are standard F1 codes

### Tip 3: Best Sessions for Each Analysis
- **Tyre Degradation**: Race (long stints)
- **Fuel Correction**: Race (fuel load matters)
- **Stint Analysis**: Race (multiple stints)
- **Telemetry**: Qualifying (clean laps)

### Tip 4: Handling Missing Data
- Not all laps have telemetry data
- Some drivers DNF (data ends early)
- Pit laps are automatically filtered
- Outliers (incidents) are removed

### Tip 5: Exporting Results
- Take screenshots of charts
- Copy data from tables
- Use browser dev tools to save charts
- Future: Export to PDF (coming soon)

---

## 🎯 Advanced Features

### Custom Fuel Effect
Edit `src/fuel_correction.py`:
```python
# Line 16
self.fuel_effect = 0.035  # Change to your value
```

### Custom Degradation Thresholds
Edit `src/tyre_degradation.py`:
```python
# Adjust cliff detection sensitivity
if last_gradient > avg_gradient * 2:  # Change multiplier
```

### Add More Circuits
All F1 circuits supported by FastF1:
- 2024: Full calendar
- 2023: Full calendar  
- 2022: Full calendar

---

## ❓ Troubleshooting

### Problem: "Session won't load"
**Causes**:
- Internet connection issue
- FastF1 servers slow
- Wrong race name

**Solutions**:
- Check internet
- Wait and retry
- Use correct race names (see dropdown)

### Problem: "No telemetry data"
**Causes**:
- Lap doesn't have telemetry
- Driver DNF'd
- Practice session (limited data)

**Solutions**:
- Try different lap
- Use "fastest lap" option
- Use race session instead

### Problem: "Degradation chart empty"
**Causes**:
- Driver did < 3 laps on a compound
- All laps were outliers (pit stops, incidents)

**Solutions**:
- Check driver completed race
- Try different driver
- Use race session (more laps)

### Problem: "Slow performance"
**Causes**:
- Large dataset
- Many drivers
- Telemetry data is heavy

**Solutions**:
- Close other tabs
- Clear cache: `rm -rf cache/`
- Restart Streamlit

---

## 📈 Understanding the Metrics

### Degradation Rate
- **What**: Lap time loss per lap (seconds/lap)
- **Good**: < 0.05 s/lap
- **Average**: 0.05-0.08 s/lap
- **Bad**: > 0.10 s/lap
- **Example**: 0.07 s/lap = 7 seconds lost over 10 laps

### Consistency
- **What**: Standard deviation of lap times
- **Good**: < 0.2s
- **Average**: 0.2-0.5s  
- **Bad**: > 0.5s
- **Example**: 0.3s = lap times vary by 0.3s on average

### Fuel Correction
- **Formula**: Corrected = Actual - (FuelLoad × 0.035)
- **Example**:
  - Lap 1: 88.5s with 110kg = 84.65s corrected
  - Lap 50: 87.0s with 30kg = 85.95s corrected
  - True pace degraded by 1.3s despite faster actual time

### Performance Score
- **Components**:
  - 30% Stint Length (did we max it?)
  - 40% Consistency (stable laps?)
  - 30% Degradation (tyre management?)
- **Example**:
  - Length: 20/25 expected = 80 pts
  - Consistency: 0.2s std = 80 pts
  - Degradation: 0.05 s/lap = 50 pts
  - **Total**: (80×0.3) + (80×0.4) + (50×0.3) = **79 pts = Good**

---

## 🎓 Learning Resources

### Understanding F1 Data
- [FastF1 Documentation](https://docs.fastf1.dev/)
- [F1 Technical Regulations](https://www.fia.com/regulation/category/110)

### Tyre Strategy
- Soft: High grip, low durability
- Medium: Balanced
- Hard: Low grip, high durability

### Fuel Strategy
- Start: ~110kg (max allowed)
- Consumption: ~1.6 kg/lap
- Effect: ~0.035s per kg

---

## 💬 Need Help?

1. **Check README.md** - Comprehensive guide
2. **Review this guide** - Step-by-step instructions
3. **FastF1 docs** - API reference
4. **GitHub Issues** - Report bugs

---

**Happy Analyzing!** 🏎️💨

*Built for race engineers who want data-driven decisions*

