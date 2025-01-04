# WHOOP Data Context for LLM

This data represents structured metrics collected from WHOOP, a wearable health and fitness tracker. Each data type corresponds to a specific aspect of a user's activity, recovery, or sleep performance.

## Data Types

### 1. **Recovery (`WHOOPRecovery`)**

- Represents the user's daily recovery score, which measures readiness for strain (percentage: 0-100).
- Includes metrics such as:
  - **Resting Heart Rate (bpm)**: Beats per minute.
  - **HRV (ms)**: Heart rate variability in milliseconds.
  - **Blood Oxygen Saturation (%)**: SPO2 levels.
  - **Skin Temperature (°C)**: Recorded during recovery.
- Linked to a specific sleep event and activity cycle.

### 2. **Workout (`WHOOPWorkout`)**

- Captures data on physical activity sessions, including:
  - **Strain**: The effort exerted during the workout.
  - **Heart Rate Metrics**: Average and maximum heart rate (bpm).
  - **Energy Expenditure**: Measured in kilojoules.
  - **Duration in Heart Rate Zones**: Time spent in different intensity zones (milliseconds).
  - **Distance and Altitude**: If applicable.
- Includes session metadata such as start/end times and activity type.

### 3. **Sleep (`WHOOPSleep`)**

- Tracks sleep performance and efficiency, including:
  - **Sleep Stage Summary**: Time spent in light, deep, and REM sleep stages.
  - **Respiratory Rate**: Breaths per minute.
  - **Sleep Efficiency (%)**: Percentage of time spent asleep while in bed.
  - **Sleep Disturbances**: Count of interruptions during the sleep cycle.
- Provides detailed data on sleep needs and cycles.

### 4. **Cycle (`WHOOPCycle`)**

- Represents periods of activity and rest throughout the day.
- Metrics include:
  - **Strain**: Effort across the cycle.
  - **Energy Expenditure (kJ)**.
  - **Heart Rate Metrics**: Average and maximum heart rates.
  - **Cycle Start/End Times**: ISO 8601 formatted timestamps.

---

## How to Work with the Data

1. **Structured Data**:

   - Each data point is represented as a Python `dataclass` with nested fields for clear organization.
   - Attributes are strongly typed for easier integration and manipulation.

2. **Usage**:

   - Use recovery scores to analyze daily readiness for physical strain.
   - Combine workout strain and recovery data to evaluate user performance trends.
   - Leverage sleep efficiency and respiratory rates to assess sleep quality.
   - Analyze cycles to identify patterns in daily activity and recovery.

3. **Integration**:
   - Fields are designed for straightforward parsing and processing, making it easy to build insights or feed the data into models.

This context ensures the WHOOP data is ready for logical interpretation and actionable insights.
