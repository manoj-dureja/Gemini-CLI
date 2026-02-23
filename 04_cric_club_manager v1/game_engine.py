 import random
import datetime
import json
import os
from typing import List, Dict, Optional
import config
from models import Club, Player, League, MatchResult, StandingRecord, Staff
from match_engine import MatchSimulator, SeasonScheduler
from systems import FinanceSystem, TransferMarket, DevelopmentSystem


class GameEngine:
    def __init__(self):
        self.league = League()
        self.start_year = datetime.datetime.now().year
        self.current_year = self.start_year
        self.season_number = 1
        self.current_week = 1

        self.match_simulator = MatchSimulator()
        self.scheduler = SeasonScheduler()
        self.finance_system = FinanceSystem()
        self.transfer_market = TransferMarket()
        self.development_system = DevelopmentSystem()

        self.fixtures: Dict[str, List[List[tuple]]] = {}
        self.results: List[MatchResult] = []
        self.managed_club: Optional[Club] = None

    def initialize_game(self):
        for div in config.DIVISIONS:
            team_names = config.TEAM_NAMES.get(div, [])
            for i in range(config.TEAMS_PER_DIVISION):
                name = team_names[i] if i < len(team_names) else f"{div} Team {i + 1}"
                club = self._create_random_club(name, div)
                self.league.add_club(club)
        self.schedule_fixtures()

    def _create_random_club(self, name: str, division: str) -> Club:
        club = Club(name=name, division=division)
        mean_cash = config.STARTING_CASH_MEAN.get(division, 1000)
        club.cash = int(random.gauss(mean_cash, mean_cash * 0.2))
        club.cash_start_season = club.cash
        club.cash_last_week = club.cash

        mean_attr = config.ATTR_MEAN.get(division, 50)
        
        # Create Squad
        roles = ["Batsman"] * 6 + ["Pace Bowler"] * 4 + ["Spin Bowler"] * 3 + ["Allrounder"] * 3 + ["Wicketkeeper"] * 2
        for role in roles:
            club.squad.append(self._create_random_player(mean_attr, role))

        # Create Staff
        for role, mult in [("Coach", 5), ("Physio", 4), ("Scout", 3)]:
            s_name = f"{random.choice(config.INDIAN_FIRST_NAMES)} {random.choice(config.INDIAN_LAST_NAMES)}"
            club.staff.append(Staff(name=s_name, role=role, skill=int(mean_attr), wage=int(mean_attr * mult)))

        # Setup Facilities
        club.stadium_level = 1 if "Division 3" in division else (2 if "Division 2" in division else 3)
        club.academy_level = club.stadium_level
        club.medical_level = club.stadium_level
        club.stadium_capacity = 2000 * club.stadium_level

        club.wage_budget = int(club.wage_bill * 1.2)
        club.reputation = int(mean_attr)
        return club

    def _create_random_player(self, mean_attr: int, role: str = None) -> Player:
        if not role: role = random.choice(["Batsman", "Pace Bowler", "Spin Bowler", "Allrounder", "Wicketkeeper"])
        age = random.randint(config.AGE_MIN, config.AGE_MAX)
        batting = int(random.gauss(mean_attr, config.ATTR_STD))
        bowling = int(random.gauss(mean_attr, config.ATTR_STD))
        fielding = int(random.gauss(mean_attr, config.ATTR_STD))

        if role == "Batsman":
            batting += 20; bowling -= 15
        elif role in ["Pace Bowler", "Spin Bowler"]:
            bowling += 20; batting -= 15
        elif role == "Wicketkeeper":
            fielding += 15; batting += 10; bowling -= 15
        elif role == "Allrounder":
            batting += 5; bowling += 5

        p = Player(
            name=f"{random.choice(config.INDIAN_FIRST_NAMES)} {random.choice(config.INDIAN_LAST_NAMES)}",
            age=age, role=role, batting=max(10, min(99, batting)), bowling=max(10, min(99, bowling)),
            fielding=max(10, min(99, fielding)), potential=min(100, max(batting, bowling) + random.randint(0, 20)),
            wage=max(config.MIN_WAGE, int(mean_attr * 0.5)), contract_years=random.randint(1, 3)
        )
        p.update_start_skills()
        return p

    def schedule_fixtures(self):
        for div in config.DIVISIONS:
            self.fixtures[div] = self.scheduler.generate_fixture_list(self.league.divisions[div])

    def advance_week(self) -> List[MatchResult]:
        week_results = []
        if self.current_week > len(self.fixtures[config.DIVISIONS[0]]): return []

        for div in config.DIVISIONS:
            for club in self.league.divisions[div]:
                club.cash_last_week = club.cash

        round_idx = self.current_week - 1

        for div in config.DIVISIONS:
            if round_idx < len(self.fixtures[div]):
                for home, away in self.fixtures[div][round_idx]:
                    result = self.match_simulator.simulate_match(home, away)
                    self._process_match_result(result, div)
                    week_results.append(result)
                    self.results.append(result) # SAVE FOR GUI
                    self.finance_system.process_match_revenue(home, away)
                    
                    # Injuries
                    for club in [home, away]:
                        if not club.squad: continue
                        victim = random.choice(club.squad)
                        if random.random() < 0.02 * (victim.injury_proneness / 10.0):
                            victim.is_injured = True
                            dur_mult = 1.5 if victim.role == "Pace Bowler" else 1.0
                            victim.injury_duration = int(random.randint(1, 4) * dur_mult)
                            
                    # Injuries healing
                    for club in [home, away]:
                        self.development_system.process_biweekly_injuries(club)

        self.current_week += 1
        if self.current_week > 0:
            for div in config.DIVISIONS:
                standings = self.league.get_standings(div)
                for rank, club in enumerate(standings):
                    club.history_cash.append(club.cash)
                    club.history_rank.append(rank + 1)
        return week_results

    def _process_match_result(self, result: MatchResult, division: str):
        home = result.home_team
        away = result.away_team

        # UPDATE LEAGUE STATS (Single place for mutation)
        home.played += 1
        away.played += 1
        home.runs_for += result.home_score
        home.runs_against += result.away_score
        away.runs_for += result.away_score
        away.runs_against += result.home_score

        if result.winner == home:
            home.won += 1; home.points += config.POINTS_WIN; away.lost += 1
            home.form.append("W"); away.form.append("L")
        elif result.winner == away:
            away.won += 1; away.points += config.POINTS_WIN; home.lost += 1
            home.form.append("L"); away.form.append("W")
        else:
            home.tied += 1; away.tied += 1
            home.points += config.POINTS_TIE; away.points += config.POINTS_TIE
            home.form.append("T"); away.form.append("T")

        # Keep last 5
        home.form = home.form[-5:]
        away.form = away.form[-5:]

        # NRR (Correctly calculated as average run difference per game)
        home.net_run_rate = (home.runs_for - home.runs_against) / max(1, home.played)
        away.net_run_rate = (away.runs_for - away.runs_against) / max(1, away.played)

        # Update Records
        for score, team in [(result.home_score, home), (result.away_score, away)]:
            if score > self.league.records.highest_team_score_runs:
                self.league.records.highest_team_score_runs = score
                self.league.records.highest_team_score_details = f"{score} - {team.name} (Season {self.season_number})"

        for innings in [result.home_innings, result.away_innings]:
            if innings:
                for b_stat in innings.batting_stats:
                    if b_stat.runs > self.league.records.highest_player_score_runs:
                        self.league.records.highest_player_score_runs = b_stat.runs
                        # FIX: Use player_name, not player.name
                        self.league.records.highest_player_score_details = f"{b_stat.runs} by {b_stat.player_name} (Season {self.season_number})"
                for b_stat in innings.bowling_stats:
                    w, r = b_stat.wickets, b_stat.runs_conceded
                    if w > self.league.records.best_bowling_wickets or (
                            w == self.league.records.best_bowling_wickets and r < self.league.records.best_bowling_runs):
                        self.league.records.best_bowling_wickets = w
                        self.league.records.best_bowling_runs = r
                        # FIX: Use player_name
                        self.league.records.best_bowling_details = f"{w}/{r} by {b_stat.player_name} (Season {self.season_number})"

    def end_season(self):
        print(f"\n--- END OF SEASON {self.season_number} ({self.current_year}) ---")

        # 1. Archive Standings
        self.league.history[self.season_number] = {}
        for div in config.DIVISIONS:
            standings = self.league.get_standings(div)
            self.league.history[self.season_number][div] = [
                StandingRecord(i + 1, c.name, c.played, c.won, c.lost, c.tied, c.points, c.net_run_rate) for i, c in
                enumerate(standings)
            ]

        self._process_league_changes()

        # 2. End of Season Finances & Growth
        for div in config.DIVISIONS:
            for club in self.league.divisions[div]:
                self.finance_system.pay_wages(club)
                
                # Reset Stats
                for p in club.squad:
                    # Records check
                    if p.season_runs > self.league.records.most_runs_season_runs:
                        self.league.records.most_runs_season_runs = p.season_runs
                        self.league.records.most_runs_season_details = f"{p.season_runs} by {p.name} ({club.name}, S{self.season_number})"
                    if p.season_wickets > self.league.records.most_wickets_season_wickets:
                        self.league.records.most_wickets_season_wickets = p.season_wickets
                        self.league.records.most_wickets_season_details = f"{p.season_wickets} by {p.name} ({club.name}, S{self.season_number})"

                    p.last_season_runs = p.season_runs
                    p.last_season_wickets = p.season_wickets
                    p.season_runs = 0
                    p.season_wickets = 0

                    self.development_system.update_player_development(p, club) # Pass club for staff access
                    p.update_start_skills()

                retiring = [p for p in club.squad if p.age > config.RETIREMENT_MEAN + random.randint(-2, 2)]
                club.retired_players.extend(retiring)
                club.squad = [p for p in club.squad if p not in retiring]

                self.development_system.run_youth_intake(club)

        self._run_transfer_window()

        self.current_year += 1
        self.season_number += 1
        self.current_week = 1

        for div in config.DIVISIONS:
            for club in self.league.divisions[div]:
                club.cash_start_season = club.cash
                club.cash_last_week = club.cash

        self._reset_stats()
        self.schedule_fixtures()

    def _process_league_changes(self):
        d1 = self.league.get_standings("Division 1")
        d2 = self.league.get_standings("Division 2")
        d3 = self.league.get_standings("Division 3")

        self.finance_system.award_prize_money(self.league)

        promoted_to_d1 = d2[:2]; relegated_to_d2 = d1[-2:]
        promoted_to_d2 = d3[:2]; relegated_to_d3 = d2[-2:]

        for c in promoted_to_d1: c.division = "Division 1"; self.league.divisions["Division 2"].remove(c); self.league.divisions["Division 1"].append(c)
        for c in relegated_to_d2: c.division = "Division 2"; self.league.divisions["Division 1"].remove(c); self.league.divisions["Division 2"].append(c)
        for c in promoted_to_d2: c.division = "Division 2"; self.league.divisions["Division 3"].remove(c); self.league.divisions["Division 2"].append(c)
        for c in relegated_to_d3: c.division = "Division 3"; self.league.divisions["Division 2"].remove(c); self.league.divisions["Division 3"].append(c)

    def _run_transfer_window(self):
        all_clubs = []
        for d in self.league.divisions.values(): all_clubs.extend(d)
        market = self.transfer_market.generate_transfer_list(all_clubs)
        for buyer in all_clubs:
            if buyer.cash < 500: continue
            for player in market:
                seller = self._find_club(player, all_clubs)
                if seller and self.transfer_market.evaluate_transfer(buyer, player, seller):
                    price = int(player.value * config.TRANSFER_MARKET_MARKUP)
                    self.transfer_market.execute_transfer(buyer, seller, player, price)

    def _find_club(self, player: Player, all_clubs: List[Club]) -> Optional[Club]:
        for c in all_clubs:
            if player in c.squad: return c
        return None

    def _reset_stats(self):
        for div in self.league.divisions.values():
            for club in div:
                club.played = club.won = club.lost = club.tied = club.points = 0
                club.net_run_rate = 0.0
                club.runs_for = club.runs_against = 0
                club.form = []
                
    def save_game(self, filename="savegame.json"):
        data = {
            "current_year": self.current_year,
            "season_number": self.season_number,
            "current_week": self.current_week,
            "league": self.league.to_dict(),
            "managed_club_id": self.managed_club.id if self.managed_club else None
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Game saved to {filename}")

    def load_game(self, filename="savegame.json"):
        if not os.path.exists(filename):
            print("Save file not found.")
            return False
            
        with open(filename, 'r') as f:
            data = json.load(f)
            
        self.current_year = data["current_year"]
        self.season_number = data["season_number"]
        self.current_week = data["current_week"]
        self.league = League.from_dict(data["league"])
        
        # Restore managed club reference
        managed_id = data.get("managed_club_id")
        if managed_id:
            for div in self.league.divisions.values():
                for club in div:
                    if club.id == managed_id:
                        self.managed_club = club
                        break
        
        # Regenerate fixtures for the season (since we don't save them)
        self.schedule_fixtures()
        print(f"Game loaded from {filename}")
        return True
