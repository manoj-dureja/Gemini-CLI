import os
import time
import config
from game_engine import GameEngine
from models import Club

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50 + "\n")

class GameCLI:
    def __init__(self):
        self.game = GameEngine()
        self.running = True

    def start(self):
        print_header("CRICKET CLUB MANAGER v1")
        print("1. New Game")
        print("2. Load Game")
        choice = input("\nSelect Option: ")
        
        if choice == "2":
            filename = input("Enter save filename (default: savegame.json): ")
            if not filename: filename = "savegame.json"
            
            if self.game.load_game(filename):
                print("Game Loaded Successfully!")
                self.main_loop()
            else:
                input("Press Enter to try again...")
                self.start()
        else:
            print("Initializing game world...")
            self.game.initialize_game()
            self.select_club()
            self.main_loop()

    def select_club(self):
        print("\nSelect a Division to manage in:")
        for db in config.DIVISIONS:
            print(f"- {db}")
        
        print("\nAvailable Clubs in Division 3:")
        div3 = self.game.league.divisions["Division 3"]
        for i, club in enumerate(div3):
            ov = int(club.get_best_xi()[0].overall) if club.get_best_xi() else 0
            print(f"{i+1}. {club.name} (Best Player: {ov})")
            
        choice = input("\nEnter club number (1-10): ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(div3):
                self.game.managed_club = div3[idx]
                print(f"You are now managing {self.game.managed_club.name}!")
            else:
                print("Invalid selection. Defaulting to first club.")
                self.game.managed_club = div3[0]
        except ValueError:
            print("Invalid input. Defaulting to first club.")
            self.game.managed_club = div3[0]

    def main_loop(self):
        self.running = True
        while self.running:
            # clear_screen()
            self.print_dashboard()
            
            print("\nOPTIONS:")
            print("1. Advance Week (Play Matches)")
            print("2. Advance Season (Fast Sim)")
            print("3. View Squad")
            print("4. View League Table")
            print("5. View Finances")
            print("6. View Staff")
            print("8. Save Game")
            print("9. Quit")
            
            choice = input("\nSelect Action: ")
            
            if choice == "1":
                self.run_week()
            elif choice == "2":
                self.run_season()
            elif choice == "3":
                self.view_squad()
            elif choice == "4":
                self.view_table()
            elif choice == "5":
                self.view_finances()
            elif choice == "6":
                self.view_staff()
            elif choice == "8":
                filename = input("Enter filename (default: savegame.json): ")
                if not filename: filename = "savegame.json"
                self.game.save_game(filename)
                input("Game Saved. Press Enter.")
            elif choice == "9":
                self.running = False
                print("Thanks for playing!")
            else:
                input("Invalid option. Press Enter.")

    def print_dashboard(self):
        club = self.game.managed_club
        if not club: return
        print_header(f"{club.name} | {club.division} | Season {self.game.season_number}")
        print(f"Week: {self.game.current_week} / {len(self.game.fixtures.get(club.division, []))}")
        print(f"Cash: ${club.cash}K | Wage Bill: ${club.wage_bill}K")
        print(f"Record: P{club.played} W{club.won} L{club.lost} | Pts: {club.points}")

    def run_week(self):
        print("\nSimulating matches...")
        results = self.game.advance_week()
        
        my_match = None
        for r in results:
            if r.home_team == self.game.managed_club or r.away_team == self.game.managed_club:
                my_match = r
                break
        
        if my_match:
            print(f"\nMatch Result: {my_match.details}")
            print(f"{my_match.home_team.name}: {my_match.home_score}/{my_match.home_innings.wickets_lost if my_match.home_innings else '?'}")
            print(f"{my_match.away_team.name}: {my_match.away_score}/{my_match.away_innings.wickets_lost if my_match.away_innings else '?'}")
            
            # Show top performers
            if my_match.home_innings:
                top_bat = max(my_match.home_innings.batting_stats, key=lambda x: x.runs, default=None)
                if top_bat: print(f"Home Top Scorer: {top_bat.player_name} ({top_bat.runs})")
            if my_match.away_innings:
                top_bat = max(my_match.away_innings.batting_stats, key=lambda x: x.runs, default=None)
                if top_bat: print(f"Away Top Scorer: {top_bat.player_name} ({top_bat.runs})")
                
        else:
            if not results:
                # End of season check or just empty week?
                if self.game.current_week > len(self.game.fixtures[config.DIVISIONS[0]]):
                   print("Season Finished! Processing End of Season...")
                   self.game.end_season()
                else:
                   print("No match scheduled.")
            else:
                print("No match for your team this week (Bye or completed).")
        
        input("\nPress Enter to continue...")

    def run_season(self):
        print("Simulating remaining season...")
        max_weeks = len(self.game.fixtures.get(config.DIVISIONS[0], []))
        while self.game.current_week <= max_weeks:
            self.game.advance_week()
            if self.game.current_week % 2 == 0: print(".", end="", flush=True)
        
        # End season
        self.game.end_season()
        input("\nSeason Complete. Press Enter.")

    def view_squad(self):
        print_header("SQUAD LIST")
        print(f"{'Name':<20} {'Role':<12} {'Age':<4} {'Bat':<4} {'Bwl':<4} {'Fit':<4} {'Wage':<5}")
        print("-" * 60)
        for p in self.game.managed_club.squad:
            print(f"{p.name:<20} {p.role:<12} {p.age:<4} {p.batting:<4} {p.bowling:<4} {p.fitness:<4} ${p.wage}K")
        input("\nPress Enter...")

    def view_staff(self):
        print_header("STAFF LIST")
        print(f"{'Name':<20} {'Role':<12} {'Skill':<5} {'Wage':<5}")
        print("-" * 60)
        for s in self.game.managed_club.staff:
            print(f"{s.name:<20} {s.role:<12} {s.skill:<5} ${s.wage}K")
        print("-" * 60)
        c = self.game.managed_club
        print(f"Facilities: Stadium L{c.stadium_level} | Academy L{c.academy_level} | Medical L{c.medical_level}")
        input("\nPress Enter...")

    def view_table(self):
        print_header(f"{self.game.managed_club.division} Standings")
        table = self.game.league.get_standings(self.game.managed_club.division)
        print(f"{'Pos':<4} {'Team':<20} {'P':<3} {'W':<3} {'L':<3} {'Pts':<4} {'NRR':<6}")
        print("-" * 60)
        for i, club in enumerate(table):
            marker = "*" if club == self.game.managed_club else " "
            print(f"{i+1:<4} {marker}{club.name:<19} {club.played:<3} {club.won:<3} {club.lost:<3} {club.points:<4} {club.net_run_rate:.2f}")
        input("\nPress Enter...")

    def view_finances(self):
        c = self.game.managed_club
        print_header("FINANCES")
        print(f"Cash Balance: ${c.cash}K")
        print(f"Wage Budget: ${c.wage_budget}K")
        print(f"Player Wages: ${sum(p.wage for p in c.squad)}K")
        print(f"Staff Wages: ${sum(s.wage for s in c.staff)}K")
        print(f"Stadium Cap: {c.stadium_capacity}")
        input("\nPress Enter...")

if __name__ == "__main__":
    app = GameCLI()
    app.start()
