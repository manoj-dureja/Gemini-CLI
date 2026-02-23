import random
from typing import List, Dict
import config
from models import Club, Player, Staff


class FinanceSystem:
    def process_match_revenue(self, home_team: Club, away_team: Club):
        base_demand = home_team.fanbase * 1000 * 0.5
        division_multiplier = 1.5 if "Division 1" in home_team.division else 1.0
        
        # Stadium level affects capacity utilization/appeal
        facility_appeal = 1.0 + (home_team.stadium_level * 0.1)
        
        attendance = int(min(home_team.stadium_capacity, base_demand * division_multiplier * facility_appeal))
        ticket_revenue = (attendance * config.TICKET_PRICE_BASE) / 1000

        home_team.cash += int(ticket_revenue)
        
        # Match Fees
        batters_home = len(home_team.squad)
        home_team.cash -= int(batters_home * config.MATCH_FEE)

        batters_away = len(away_team.squad)
        away_team.cash -= int(batters_away * config.MATCH_FEE)

    def pay_wages(self, club: Club):
        # Player Wages
        bill = sum(p.wage for p in club.squad)
        # Staff Wages
        staff_bill = sum(s.wage for s in club.staff)
        
        club.cash -= (bill + staff_bill)
        
        # Facility Maintenance
        maintenance = (club.stadium_level * 10) + (club.academy_level * 5) + (club.medical_level * 5)
        club.cash -= maintenance

    def award_prize_money(self, league):
        for div_name, clubs in league.divisions.items():
            standings = league.get_standings(div_name)
            prizes = config.PRIZE_MONEY.get(div_name, [0, 0, 0])
            for i, club in enumerate(standings):
                if i < len(prizes): club.cash += prizes[i]
                start_ott = config.OTT_REVENUE_BASE.get(div_name, 100)
                club.cash += start_ott


class TransferMarket:
    def generate_transfer_list(self, all_clubs: List[Club]) -> List[Player]:
        market = []
        for club in all_clubs:
            if len(club.squad) > 15:
                # Sell lower rated players
                sorted_squad = sorted(club.squad, key=lambda p: p.overall)
                # Sell bottom 3
                candidates = sorted_squad[:3]
                if candidates:
                    p = random.choice(candidates)
                    market.append(p)
        return market

    def evaluate_transfer(self, buyer: Club, player: Player, seller: Club) -> bool:
        if buyer == seller: return False
        cost = getattr(player, 'transfer_value', player.value * config.TRANSFER_MARKET_MARKUP)
        if buyer.cash < cost: return False

        current_best = buyer.get_best_xi()
        role_players = [p for p in current_best if p.role == player.role]
        if not role_players: return True

        avg_role_skill = sum(p.overall for p in role_players) / len(role_players)
        
        # Scouts check (if implemented, here we assume perfect info for AI)
        if player.overall > avg_role_skill + 5: return True
        return False

    def execute_transfer(self, buyer: Club, seller: Club, player: Player, price: int):
        if buyer.cash >= price:
            buyer.cash -= price
            seller.cash += price
            if player in seller.squad: seller.squad.remove(player)
            buyer.squad.append(player)
            player.contract_years = 2
            return True
        return False


class DevelopmentSystem:
    def run_youth_intake(self, club: Club):
        # Intake quality depends on Academy Level and Youth Rating
        # Academy Level (1-10) adds to the base skill
        
        num_youths = random.randint(2, 4) + (1 if club.academy_level > 5 else 0)
        
        for _ in range(num_youths):
            role_counts = {"Batsman": 0, "Pace Bowler": 0, "Spin Bowler": 0, "Allrounder": 0, "Wicketkeeper": 0}
            for p in club.squad: role_counts[p.role] = role_counts.get(p.role, 0) + 1
            needed_role = min(role_counts, key=role_counts.get)
            if random.random() < 0.3: needed_role = random.choice(list(role_counts.keys()))

            # Base skill improved by academy level
            base_skill = (club.youth_rating / 2) + 20 + (club.academy_level * 2)
            
            batting = int(base_skill + random.randint(-10, 10))
            bowling = int(base_skill + random.randint(-10, 10))
            fielding = int(base_skill + random.randint(-10, 10))

            if needed_role == "Batsman":
                batting += 20; bowling -= 15
            elif needed_role in ["Pace Bowler", "Spin Bowler"]:
                bowling += 20; batting -= 15
            elif needed_role == "Wicketkeeper":
                fielding += 15; batting += 10; bowling -= 15
            elif needed_role == "Allrounder":
                batting += 5; bowling += 5

            # Potential
            potential = base_skill + random.randint(10, 40) # Wider range

            p = Player(
                name=f"{random.choice(config.INDIAN_FIRST_NAMES)} {random.choice(config.INDIAN_LAST_NAMES)}",
                age=16, role=needed_role, batting=max(10, min(99, batting)),
                bowling=max(10, min(99, bowling)), fielding=max(10, min(99, fielding)),
                potential=min(100, int(potential)), wage=config.MIN_WAGE, contract_years=3,
                work_ethic=random.randint(5, 20) if random.random() < (club.youth_rating / 100.0) else random.randint(1, 15),
                injury_proneness=random.randint(1, 20)
            )
            p.update_start_skills()
            club.squad.append(p)

    def update_player_development(self, player: Player, club: Club):
        player.age += 1
        player.contract_years -= 1
        curve = config.AGING_CURVES.get(player.role, config.AGING_CURVES["Batsman"])
        
        # Determine coaching impact
        coaches = [s for s in club.staff if s.role == "Coach"]
        avg_coaching = sum(c.skill for c in coaches) / max(1, len(coaches)) if coaches else 20
        
        if player.age < curve["peak_start"]:
            growth_chance = (player.potential - player.overall) / 10.0
            growth_chance *= (avg_coaching / 100.0) * config.DEVELOPMENT_FACTOR
            growth_chance *= (player.work_ethic / 10.0)

            if random.random() < growth_chance:
                player.batting = min(player.potential, player.batting + random.randint(1, 3))
                player.bowling = min(player.potential, player.bowling + random.randint(1, 3))
                player.fitness = min(100, player.fitness + 2)

        elif player.age >= curve["decline"]:
            # Physios help reduce decline
            physios = [s for s in club.staff if s.role == "Physio"]
            avg_physio = sum(c.skill for c in physios) / max(1, len(physios)) if physios else 20
            
            decline_chance = (player.age - curve["decline"]) / 10.0
            decline_chance *= config.DECLINE_FACTOR * (1.0 - (avg_physio/200.0)) # Up to 50% reduction

            if random.random() < decline_chance:
                player.batting = max(10, player.batting - random.randint(1, 3))
                player.bowling = max(10, player.bowling - random.randint(1, 3))
                player.fitness = max(50, player.fitness - random.randint(1, 5))

    def process_biweekly_injuries(self, club: Club):
        physios = [s for s in club.staff if s.role == "Physio"]
        avg_physio = sum(c.skill for c in physios) / max(1, len(physios)) if physios else 20
        
        for p in club.squad:
            if p.is_injured:
                # Better physios reduce duration faster
                reduction = 1 + (1 if random.random() < (avg_physio/100.0) else 0)
                p.injury_duration -= reduction
                if p.injury_duration <= 0:
                    p.is_injured = False
                    p.fitness = 80
            else:
                p.fitness = min(100, p.fitness + 5 + int(avg_physio/20))
