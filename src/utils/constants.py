from dataclasses import dataclass, field
import datetime
from typing import Optional, List, Dict, Any


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
    version: int


@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    expert_used: Optional[str] = None  # Template name of the ExpertLLM
    expert_version: Optional[int] = None  # Version of the ExpertLLM
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

@dataclass
class ChatContext:
    user_id: str
    max_tokens: int  # Maximum tokens for sliding context
    context: List[ChatMessage] = field(default_factory=list)
    token_count: int = 0  # Current token count
    current_expert: Optional[ExpertLLM] = None  # Track the current expert

@dataclass
class Conversation:
    conversation_id: str
    user_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "expert_used": msg.expert_used,
                    "expert_version": msg.expert_version,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in self.messages
            ],
            "created_at": self.created_at.isoformat(),
        }

@dataclass
class User:
    uid: str  # Unique identifier for the user
    name: str  # Full name
    age: int  # Age stored as a number
    gender: str  # Gender of the user
    location: str  # User's location or description of where they live
    occupation: str  # User's current or past occupation
    favorite_books_and_movies: Dict[str, str]  # Map of titles to reasons why they are favorite
    pets: Dict[str, str]  # Map of pet names to descriptions
    languages_spoken: List[str]  # List of languages the user speaks
    cultural_religious_identity: str  # Cultural and religious identity description
    secrets: Dict[str, str] = field(default_factory=dict)  # Map of secrets like API keys, tokens, etc.
    social_graph_chimps: List[str] = field(default_factory=list)  # Array of chimp UIDs


    def __post_init__(self):
        # Validation to ensure types match expectations
        if not isinstance(self.favorite_books_and_movies, dict):
            raise TypeError("favorite_books_and_movies must be a dictionary of title: reason pairs.")
        if not isinstance(self.pets, dict):
            raise TypeError("pets must be a dictionary of pet names and descriptions.")
        if not isinstance(self.languages_spoken, list):
            raise TypeError("languages_spoken must be a list of strings.")
        if not isinstance(self.secrets, dict):
            raise TypeError("secrets must be a dictionary of key-value pairs.")

@dataclass
class Chimp:
    uid: str  # Unique identifier for the chimp
    name: str  # Full name of the chimp
    approx_age: int  
    how_we_met: str  # How the relationship started
    why_the_relationship_matters: str  # Importance of the relationship
    one_story: str  # A meaningful or memorable story about the chimp