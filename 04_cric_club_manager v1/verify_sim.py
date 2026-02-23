
import config
from game_engine import GameEngine
import random

def run_verification():
    print("Initializing Verification Simulation...")
    game = GameEngine()
    game.initialize_game()
    
    # Pick a random club to track
    tracked_club = game.league.divisions["Division 3"][0]
    print(f"Tracking Club: {tracked_club.name} (Starts in {tracked_club.division})")
    
    for season in range(3):
        print(f"\n--- SIMULATING SEASON {season + 1} ---")
        
        # Simulate all matches
        while game.current_week <= config.MATCHES_PER_SEASON:
            game.advance_week()
            if game.current_week % 5 == 0:
                print(f"Week {game.current_week} complete...")
        
        # Print Tables (Before reset)
        print("\nEnd of Season Tables:")
        for div in config.DIVISIONS:
            print(f"\n{div}")
            table = game.league.get_standings(div)
            for i, c in enumerate(table):
                print(f"{i+1}. {c.name} | Pts: {c.points} | W: {c.won} | L: {c.lost} | NRR: {c.net_run_rate:.2f}")

        # End season
        game.end_season()
    
    print("\n--- VERIFICATION COMPLETE ---")
    print(f"Tracked Club Final Status:")
    print(f"Name: {tracked_club.name}")
    print(f"Division: {tracked_club.division}")
    print(f"Cash: ${tracked_club.cash}K")
    print(f"Squad Size: {len(tracked_club.squad)}")

if __name__ == "__main__":
    # Seed for reproducibility
    random.seed(42)
    run_verification()
