import random
from typing import List, Tuple, Dict
import config
from models import Club, Player, MatchResult, Scorecard, PlayerMatchStats

class BallByBallSimulator:
    def simulate_innings(self, batting_team: Club, bowling_team: Club, target: int = None) -> Scorecard:
        card = Scorecard()
        # Initialize stats containers
        batting_stats_map = {} # player_id -> PlayerMatchStats
        bowling_stats_map = {} # player_id -> PlayerMatchStats

        batting_xi = batting_team.get_best_xi()
        bowling_xi = bowling_team.get_best_xi()
        
        # Select bowlers (top 5 for simplicity, or based on role)
        bowlers = [p for p in bowling_xi if p.role in ["Pace Bowler", "Spin Bowler", "Allrounder"]]
        if len(bowlers) < 5:
            bowlers.extend([p for p in bowling_xi if p not in bowlers][:5-len(bowlers)])
        random.shuffle(bowlers) # Randomize attack for now

        # Strikers
        striker_idx = 0
        non_striker_idx = 1
        next_batter_idx = 2
        
        striker = batting_xi[striker_idx]
        non_striker = batting_xi[non_striker_idx]

        # Init stats for openers
        for p in batting_xi:
            s = PlayerMatchStats(player_id=p.id, player_name=p.name, is_out=False)
            batting_stats_map[p.id] = s
            card.batting_stats.append(s)

        current_over = 0
        total_runs = 0
        wickets = 0
        
        # Main Loop: 20 Overs
        while current_over < 20 and wickets < 10:
            bowler = bowlers[current_over % len(bowlers)]
            if bowler.id not in bowling_stats_map:
                s = PlayerMatchStats(player_id=bowler.id, player_name=bowler.name, is_out=False)
                bowling_stats_map[bowler.id] = s
                card.bowling_stats.append(s)
            bowler_stats = bowling_stats_map[bowler.id]

            for ball in range(6):
                if wickets >= 10: break
                if target and total_runs > target: break

                outcome, runs, extra, is_wicket = self.simulate_ball(striker, bowler, batting_team.tactics, bowling_team.tactics)
                
                # Update Stats
                striker_stats = batting_stats_map[striker.id]
                
                if extra > 0:
                    card.extras += extra
                    total_runs += extra
                    bowler_stats.runs_conceded += extra
                    # Wides/No-balls don't count as ball faced usually, but for simplicity here we count legal balls in loop
                
                if not is_wicket:
                    striker_stats.runs += runs
                    striker_stats.balls += 1
                    if runs == 4: striker_stats.fours += 1
                    if runs == 6: striker_stats.sixes += 1
                    
                    striker.runs_scored += runs
                    striker.season_runs += runs
                    
                    total_runs += runs
                    bowler_stats.runs_conceded += runs
                    
                    # Rotate strike
                    if runs % 2 == 1:
                        striker, non_striker = non_striker, striker
                else:
                    striker_stats.balls += 1
                    striker_stats.is_out = True
                    wickets += 1
                    bowler_stats.wickets += 1
                    bowler.wickets_taken += 1
                    bowler.season_wickets += 1
                    
                    if next_batter_idx < 11:
                        striker = batting_xi[next_batter_idx]
                        next_batter_idx += 1
                    else:
                        striker = None # All out
                
            if target and total_runs > target: break
            
            # End of over rotation
            if striker and non_striker:
                striker, non_striker = non_striker, striker
            
            bowler_stats.overs += 1.0
            current_over += 1
            
        card.total_runs = total_runs
        card.wickets_lost = wickets
        card.overs_played = current_over + (0.0 if wickets==10 else 0.0) # Simplified
        
        return card

    def simulate_ball(self, batter: Player, bowler: Player, bat_tactics, bowl_tactics) -> Tuple[str, int, int, bool]:
        # Simple probability model
        # Skill difference
        skill_diff = batter.batting - bowler.bowling
        
        # Base probabilities (0, 1, 2, 3, 4, 6, W, Ex)
        # 0: 30%, 1: 30%, 2: 5%, 3: 1%, 4: 10%, 6: 5%, W: 5%, Ex: 4%
        
        # Adjust based on skill
        p_dot = 30 - skill_diff * 0.2
        p_single = 30 + skill_diff * 0.1
        p_boundary = 15 + skill_diff * 0.2 + (bat_tactics.batting_intent - 0.5) * 10
        p_wicket = 5 - skill_diff * 0.1 + (bowl_tactics.bowling_intent - 0.5) * 5
        
        # Normalize
        total = p_dot + p_single + p_boundary + p_wicket
        scale = 100.0 / total
        
        roll = random.uniform(0, 100)
        
        acc = 0
        if roll < (acc := acc + p_dot * scale): return ("0", 0, 0, False)
        if roll < (acc := acc + p_single * scale): return ("1", 1, 0, False)
        
        # Boundaries split
        p_four = p_boundary * 0.7
        p_six = p_boundary * 0.3
        
        if roll < (acc := acc + p_four * scale): return ("4", 4, 0, False)
        if roll < (acc := acc + p_six * scale): return ("6", 6, 0, False)
        
        if roll < (acc := acc + p_wicket * scale): return ("W", 0, 0, True)
        
        # Fallback to single
        return ("1", 1, 0, False)


class MatchSimulator:
    def __init__(self):
        self.engine = BallByBallSimulator()

    def simulate_match(self, home_team: Club, away_team: Club) -> MatchResult:
        for p in home_team.squad + away_team.squad:
            p.matches_played += 1
            
        # First Innings
        innings1 = self.engine.simulate_innings(home_team, away_team)
        
        # Second Innings
        innings2 = self.engine.simulate_innings(away_team, home_team, target=innings1.total_runs)
        
        winner = None
        details = ""
        if innings1.total_runs > innings2.total_runs:
            winner = home_team
            margin = innings1.total_runs - innings2.total_runs
            details = f"{home_team.name} won by {margin} runs"
        elif innings2.total_runs > innings1.total_runs:
            winner = away_team
            margin = 10 - innings2.wickets_lost
            details = f"{away_team.name} won by {margin} wickets"
        else:
            details = "Match Tied"

        return MatchResult(
            home_team=home_team,
            away_team=away_team,
            home_score=innings1.total_runs,
            away_score=innings2.total_runs,
            winner=winner,
            is_tie=(winner is None),
            details=details,
            home_innings=innings1,
            away_innings=innings2
        )

class SeasonScheduler:
    def generate_fixture_list(self, teams: List[Club]) -> List[List[Tuple[Club, Club]]]:
        teams_copy = list(teams)
        if len(teams_copy) % 2: teams_copy.append(None) 
        n = len(teams_copy)
        fixtures = []
        indices = list(range(n))
        
        for round_num in range(2): 
            for i in range(n - 1):
                round_matches = []
                for j in range(n // 2):
                    t1, t2 = indices[j], indices[n - 1 - j]
                    if teams_copy[t1] is not None and teams_copy[t2] is not None:
                        round_matches.append((teams_copy[t1], teams_copy[t2]) if round_num == 0 else (teams_copy[t2], teams_copy[t1]))
                fixtures.append(round_matches)
                indices.insert(1, indices.pop())
        return fixtures
