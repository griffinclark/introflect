from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class WHOOPRecoveryScore:
    user_calibrating: bool
    recovery_score: float  # Percentage (0-100)
    resting_heart_rate: float  # Beats per minute (bpm)
    hrv_rmssd_milli: float  # HRV in milliseconds
    spo2_percentage: float  # Blood oxygen saturation in percentage
    skin_temp_celsius: float  # Skin temperature in Celsius


@dataclass
class WHOOPRecovery:
    cycle_id: int
    sleep_id: int
    user_id: int
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    score_state: str
    score: WHOOPRecoveryScore


@dataclass
class WHOOPWorkoutScore:
    strain: float
    average_heart_rate: int  # bpm
    max_heart_rate: int  # bpm
    kilojoule: float  # Energy in kilojoules
    percent_recorded: float  # Percentage
    distance_meter: float  # Distance in meters
    altitude_gain_meter: float  # Altitude gain in meters
    altitude_change_meter: float  # Altitude change in meters
    zone_duration: Dict[str, int]  # Zone durations in milliseconds


@dataclass
class WHOOPWorkout:
    id: int
    user_id: int
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    start: str  # ISO 8601 datetime
    end: str  # ISO 8601 datetime
    timezone_offset: str  # e.g., "-08:00"
    sport_id: int
    score_state: str
    score: WHOOPWorkoutScore


@dataclass
class WHOOPSleepStageSummary:
    total_in_bed_time_milli: int
    total_awake_time_milli: int
    total_no_data_time_milli: int
    total_light_sleep_time_milli: int
    total_slow_wave_sleep_time_milli: int
    total_rem_sleep_time_milli: int
    sleep_cycle_count: int
    disturbance_count: int


@dataclass
class WHOOPSleepNeeded:
    baseline_milli: int
    need_from_sleep_debt_milli: int
    need_from_recent_strain_milli: int
    need_from_recent_nap_milli: int


@dataclass
class WHOOPSleepScore:
    stage_summary: WHOOPSleepStageSummary
    sleep_needed: WHOOPSleepNeeded
    respiratory_rate: float  # Breaths per minute
    sleep_performance_percentage: float
    sleep_consistency_percentage: float
    sleep_efficiency_percentage: float


@dataclass
class WHOOPSleep:
    id: int
    user_id: int
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    start: str  # ISO 8601 datetime
    end: str  # ISO 8601 datetime
    timezone_offset: str  # e.g., "-08:00"
    nap: bool
    score_state: str
    score: WHOOPSleepScore


@dataclass
class WHOOPCycleScore:
    strain: float
    kilojoule: float  # Energy in kilojoules
    average_heart_rate: int  # bpm
    max_heart_rate: int  # bpm


@dataclass
class WHOOPCycle:
    id: int
    user_id: int
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    start: str  # ISO 8601 datetime
    end: Optional[str]  # ISO 8601 datetime or None
    timezone_offset: str  # e.g., "-08:00"
    score_state: str
    score: WHOOPCycleScore

@dataclass
class PersonalityMetric:
    metric: str
    description: str
    score: int
    percentile: Optional[int]
    interpretation: str
    implications: Optional[List[str]] = field(default_factory=list)

@dataclass
class PersonalityProfile:
    metrics: List[PersonalityMetric]
    datetimeCreated: str = None
    for_user_UID: str = None
    source: str = None

@dataclass
class LLMTool:
    name: str  # Name of the tool
    description: str  # Description of what the tool does
    parameters: Dict[str, str]  # Parameters and their types
    use_cases: List[str]  # List of use cases
    limitations: List[str]  # List of limitations
    credibility_score: str  # Credibility score (HIGH, MEDIUM, LOW)


@dataclass
class ExpertLLM:
    template_name: str
    model: str
    temperature: float
    personality_prompt: str # who is this expert?
    speaking_instructions: str # how should they talk?
    tone: str # what tone should they use?
    default_length_preference: str # how long/short should their responses be? 
    preferred_vocabulary_complexity: str # should they speak simply or with detail? 
    default_response_format: str # should they be biased towards responding with quotes, poetry, bullet points, data, etc.?
    when_to_use: str # a description for our selector LLM to know when to use this expert