from dataclasses import dataclass, field, asdict
import random
import uuid
from typing import List, Dict, Optional, Any
import config

@dataclass
class Staff:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unknown Staff"
    role: str = "Coach" # Coach, Scout, Physio
    skill: int = 50
    wage: int = 500

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Staff':
        return cls(**data)

@dataclass
class Player:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unknown"
    age: int = 20
    role: str = "Batsman"

    # Skills (0-100)
    batting: int = 50
    bowling: int = 50
    fielding: int = 50
    fitness: int = 100
    potential: int = 50

    # Mentals & Hidden (0-100 or 1-20)
    morale: int = 50
    leadership: int = 10
    work_ethic: int = 10
    injury_proneness: int = 10

    # Skill Growth Tracking (Set at start of season)
    start_batting: int = 50
    start_bowling: int = 50
    start_fielding: int = 50
    start_overall: int = 50

    # Contract
    wage: int = 20
    contract_years: int = 1

    # Stats / State (All-Time)
    matches_played: int = 0
    runs_scored: int = 0
    wickets_taken: int = 0

    # Stats / State (Seasonal)
    season_runs: int = 0
    season_wickets: int = 0
    last_season_runs: int = 0
    last_season_wickets: int = 0

    form: float = 50.0
    is_injured: bool = False
    injury_duration: int = 0

    @property
    def overall(self) -> int:
        if self.role == "Batsman":
            return int(self.batting * 0.8 + self.fielding * 0.2)
        elif self.role in ["Pace Bowler", "Spin Bowler"]:
            return int(self.bowling * 0.8 + self.fielding * 0.2)
        elif self.role == "Allrounder":
            return int(self.batting * 0.4 + self.bowling * 0.4 + self.fielding * 0.2)
        elif self.role == "Wicketkeeper":
            return int(self.batting * 0.6 + self.fielding * 0.4)
        return 50

    def update_start_skills(self):
        self.start_batting = self.batting
        self.start_bowling = self.bowling
        self.start_fielding = self.fielding
        self.start_overall = self.overall

    @property
    def value(self) -> int:
        base_val = (self.overall ** 2) / 10
        age_factor = 1.0
        if self.age < 24:
            age_factor = 1.3
        elif self.age > 32:
            age_factor = 0.6
        return int(base_val * age_factor * 10)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        return cls(**data)


@dataclass
class Tactics:
    batting_intent: float = 0.5
    bowling_intent: float = 0.5
    pace_spin_bias: float = 0.5
    risk_tolerance: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tactics':
        return cls(**data)


@dataclass
class Club:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Club FC"
    division: str = "Division 3"

    # History
    history_cash: List[int] = field(default_factory=list)
    history_rank: List[int] = field(default_factory=list)
    retired_players: List[Player] = field(default_factory=list)

    # Resources
    details: str = ""
    reputation: int = 50
    fanbase: int = 100
    cash: int = 1000
    cash_last_week: int = 1000
    cash_start_season: int = 1000
    wage_budget: int = 1000

    # Facilities & Staff
    stadium_capacity: int = 5000
    stadium_level: int = 1
    academy_level: int = 1
    medical_level: int = 1
    scouting_network: int = 0
    staff: List[Staff] = field(default_factory=list)
    
    # Legacy ratings
    coaching_rating: int = 50
    youth_rating: int = 50

    # Squad & Tactics
    squad: List[Player] = field(default_factory=list)
    tactics: Tactics = field(default_factory=Tactics)

    # Season Stats
    played: int = 0
    won: int = 0
    lost: int = 0
    tied: int = 0
    points: int = 0
    net_run_rate: float = 0.0
    runs_for: int = 0
    runs_against: int = 0
    form: List[str] = field(default_factory=list) # Last 5 results: ['W', 'L', 'T']

    def get_best_xi(self) -> List[Player]:
        available = [p for p in self.squad if not p.is_injured]
        available.sort(key=lambda p: p.overall, reverse=True)
        return available[:11]

    @property
    def wage_bill(self) -> int:
        return sum(p.wage for p in self.squad) + sum(s.wage for s in self.staff)

    @property
    def average_age(self) -> float:
        if not self.squad: return 0
        return sum(p.age for p in self.squad) / len(self.squad)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['squad'] = [p.to_dict() for p in self.squad]
        data['staff'] = [s.to_dict() for s in self.staff]
        data['tactics'] = self.tactics.to_dict()
        data['retired_players'] = [p.to_dict() for p in self.retired_players]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Club':
        squad_data = data.pop('squad', [])
        staff_data = data.pop('staff', [])
        tactics_data = data.pop('tactics', {})
        retired_data = data.pop('retired_players', [])
        
        club = cls(**data)
        club.squad = [Player.from_dict(p) for p in squad_data]
        club.staff = [Staff.from_dict(s) for s in staff_data]
        club.tactics = Tactics.from_dict(tactics_data)
        club.retired_players = [Player.from_dict(p) for p in retired_data]
        return club


@dataclass
class PlayerMatchStats:
    player_id: str
    player_name: str
    runs: int = 0
    balls: int = 0
    fours: int = 0
    sixes: int = 0
    is_out: bool = True
    wickets: int = 0
    overs: float = 0.0
    runs_conceded: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerMatchStats':
        return cls(**data)


@dataclass
class Scorecard:
    batting_stats: List[PlayerMatchStats] = field(default_factory=list)
    bowling_stats: List[PlayerMatchStats] = field(default_factory=list)
    total_runs: int = 0
    wickets_lost: int = 0
    overs_played: float = 20.0
    extras: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'batting_stats': [s.to_dict() for s in self.batting_stats],
            'bowling_stats': [s.to_dict() for s in self.bowling_stats],
            'total_runs': self.total_runs,
            'wickets_lost': self.wickets_lost,
            'overs_played': self.overs_played,
            'extras': self.extras
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scorecard':
        card = cls(
            total_runs=data.get('total_runs', 0),
            wickets_lost=data.get('wickets_lost', 0),
            overs_played=data.get('overs_played', 0.0),
            extras=data.get('extras', 0)
        )
        card.batting_stats = [PlayerMatchStats.from_dict(s) for s in data.get('batting_stats', [])]
        card.bowling_stats = [PlayerMatchStats.from_dict(s) for s in data.get('bowling_stats', [])]
        return card


@dataclass
class MatchResult:
    home_team: Club
    away_team: Club
    home_score: int
    away_score: int
    winner: Optional[Club]
    is_tie: bool = False
    details: str = ""
    home_innings: Optional[Scorecard] = None
    away_innings: Optional[Scorecard] = None
    
    def to_dict(self) -> Dict[str, Any]:
        # Minimal serialization for history
        return {
            'home_team_id': self.home_team.id,
            'home_team_name': self.home_team.name,
            'away_team_id': self.away_team.id,
            'away_team_name': self.away_team.name,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'winner_id': self.winner.id if self.winner else None,
            'is_tie': self.is_tie,
            'details': self.details,
            'home_innings': self.home_innings.to_dict() if self.home_innings else None,
            'away_innings': self.away_innings.to_dict() if self.away_innings else None
        }

    # No from_dict: we don't reconstruct full match objects from history usually, 
    # or we handle it manually if we do.


@dataclass
class StandingRecord:
    pos: int
    team_name: str
    played: int
    won: int
    lost: int
    tied: int
    points: int
    nrr: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandingRecord':
        return cls(**data)


@dataclass
class LeagueRecords:
    highest_team_score_runs: int = 0
    highest_team_score_details: str = "None"
    highest_player_score_runs: int = 0
    highest_player_score_details: str = "None"
    best_bowling_wickets: int = 0
    best_bowling_runs: int = 999
    best_bowling_details: str = "None"
    most_runs_season_runs: int = 0
    most_runs_season_details: str = "None"
    most_wickets_season_wickets: int = 0
    most_wickets_season_details: str = "None"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeagueRecords':
        return cls(**data)


class League:
    def __init__(self):
        self.divisions: Dict[str, List[Club]] = {d: [] for d in config.DIVISIONS}
        self.history: Dict[int, Dict[str, List[StandingRecord]]] = {}
        self.records = LeagueRecords()

    def add_club(self, club: Club):
        if club.division in self.divisions:
            self.divisions[club.division].append(club)

    def get_standings(self, division: str) -> List[Club]:
        return sorted(
            self.divisions[division],
            key=lambda c: (c.points, c.won, c.net_run_rate),
            reverse=True
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'divisions': {d: [c.to_dict() for c in clubs] for d, clubs in self.divisions.items()},
            'history': {str(y): {d: [r.to_dict() for r in recs] for d, recs in div_recs.items()} for y, div_recs in self.history.items()},
            'records': self.records.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'League':
        league = cls()
        
        # Load Divisions
        div_data = data.get('divisions', {})
        for d, clubs_data in div_data.items():
            league.divisions[d] = [Club.from_dict(c) for c in clubs_data]
            
        # Load History
        hist_data = data.get('history', {})
        for y, div_recs in hist_data.items():
            league.history[int(y)] = {d: [StandingRecord.from_dict(r) for r in recs] for d, recs in div_recs.items()}
            
        # Load Records
        if 'records' in data:
            league.records = LeagueRecords.from_dict(data['records'])
            
        return league
