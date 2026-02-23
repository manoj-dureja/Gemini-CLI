# Cricket Club Manager v1 - Configuration

# --- LEAGUE STRUCTURE ---
DIVISIONS = ["Division 1", "Division 2", "Division 3"]
TEAMS_PER_DIVISION = 10
MATCHES_PER_SEASON = 18  # Double round robin
PROMOTION_ZONES = 2
RELEGATION_ZONES = 2
POINTS_WIN = 2
POINTS_TIE = 1
POINTS_LOSS = 0

# --- TEAM NAMES (Indian Cities by Tier) ---
TEAM_NAMES = {
    "Division 1": [
        "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore", 
        "Kolkata Knight Riders", "Delhi Capitals", "Sunrisers Hyderabad", 
        "Rajasthan Royals", "Punjab Kings", "Lucknow Super Giants", "Gujarat Titans"
    ],
    "Division 2": [
        "Pune Warriors", "Kochi Tuskers", "Deccan Chargers", "Ahmedabad Rockets",
        "Indore Holkars", "Nagpur Oranges", "Jaipur Pinks", "Surat Diamonds",
        "Visakhapatnam Steel", "Kanpur Leather"
    ],
    "Division 3": [
        "Bhopal Lakers", "Patna Pilots", "Ranchi Rhinos", "Guwahati Gaurs",
        "Bhubaneswar Bulls", "Raipur Rangers", "Dehradun Doons", "Goa Gaurdians",
        "Trivandrum Titans", "Chandigarh Champs"
    ]
}

# --- ECONOMY (in $K) ---
STARTING_CASH_MEAN = {
    "Division 1": 5000,
    "Division 2": 2000,
    "Division 3": 500
}
WAGE_BUDGET_RATIO = 0.6  # Target wage bill as % of revenue
MIN_WAGE = 10  # Minimum wage per season in $K
MATCH_FEE = 0.5 # Pay per match played

PRIZE_MONEY = {
    "Division 1": [2000, 1000, 500], # Top 3
    "Division 2": [800, 400, 200],
    "Division 3": [300, 150, 75]
}

OTT_REVENUE_BASE = {
    "Division 1": 1500,
    "Division 2": 500,
    "Division 3": 100
}

TICKET_PRICE_BASE = 20 # Avg ticket price

# --- STADIUM & FACILITIES ---
STADIUM_CAPACITY_BASE = {
    "Division 1": 25000,
    "Division 2": 10000,
    "Division 3": 4000
}
EXPANSION_COST_PER_SEAT = 0.5 # $K per seat
MAINTENANCE_PER_SEAT = 0.01 # $K per seat per year
FACILITY_UPKEEP_EXPONENT = 1.5   # Punishes hoarding 100-rated facilities
FACILITY_UPKEEP_MULTIPLIER = 0.2 # Multiplier for the exponential cost

# --- PLAYER GENERATION ---
ATTR_MEAN = {
    "Division 1": 75,
    "Division 2": 60,
    "Division 3": 45
}
ATTR_STD = 10
AGE_MIN = 18
AGE_MAX = 35
SQUAD_SIZE = 18

# --- MATCH ENGINE ---
# Base T20 score parameters (approximate)
BASE_RUNS_MU = 160
BASE_RUNS_SIGMA = 25
MIN_SCORE = 60
MAX_SCORE = 260

# Strength Impact
BATTING_WEIGHT = 0.6
BOWLING_WEIGHT = 0.4
HOME_ADVANTAGE = 10 # Runs added to mu

# --- DEVELOPMENT & AGING CURVES ---
# Format: {Role: (Peak Start, Peak End, Decline Start)}
AGING_CURVES = {
    "Pace Bowler": {"peak_start": 24, "peak_end": 28, "decline": 31},
    "Batsman": {"peak_start": 27, "peak_end": 32, "decline": 34},
    "Spin Bowler": {"peak_start": 29, "peak_end": 34, "decline": 36},
    "Allrounder": {"peak_start": 26, "peak_end": 30, "decline": 32},
    "Wicketkeeper": {"peak_start": 26, "peak_end": 31, "decline": 33},
}
RETIREMENT_MEAN = 36
DEVELOPMENT_FACTOR = 2.0 # Multiplier for growth
DECLINE_FACTOR = 3.0 # Multiplier for aging decline

# --- TRANSFERS ---
TRANSFER_MARKET_MARKUP = 1.2 # AI buying markup
TRANSFER_WINDOW_WEEKS = 4


# --- INDIAN NAMES ---
INDIAN_FIRST_NAMES = [
    "Aarav", "Vihaan", "Vivaan", "Ananya", "Diya", "Advik", "Kabir", "Rohan", "Aryan", "Ishaan",
    "Arjun", "Reyansh", "Mohammed", "Sai", "Ayaan", "Krishna", "Dhruv", "Ishita", "Anvi", "Aditi",
    "Rahul", "Amit", "Suresh", "Ramesh", "Vijay", "Sanjay", "Manoj", "Rajesh", "Sunil", "Anil",
    "Priya", "Neha", "Sneha", "Anjali", "Pooja", "Riya", "Shreya", "Tanvi", "Kavya", "Meera",
    "Virat", "Rohit", "MS", "Hardik", "Ravindra", "Jasprit", "Shikhar", "Rishabh", "Shreyas", "KL",
    "Sachin", "Sourav", "Virender", "Yuvraj", "Zaheer", "Harbhajan", "Gautam", "VVS", "Anil", "Rahul"
]

INDIAN_LAST_NAMES = [
    "Patel", "Sharma", "Singh", "Kumar", "Gupta", "Shah", "Jain", "Mehta", "Mishra", "Yadav",
    "Das", "Reddy", "Nair", "Iyer", "Rao", "Gowda", "Pillai", "Menon", "Chopra", "Malhotra",
    "Kohli", "Dhoni", "Sharma", "Jadeja", "Bumrah", "Dhawan", "Pant", "Iyer", "Rahul", "Pandya",
    "Tendulkar", "Ganguly", "Sehwag", "Singh", "Khan", "Gambhir", "Laxman", "Kumble", "Dravid",
    "Agarwal", "Verma", "Joshi", "Kulkarni", "Deshmukh", "Patil", "Pawar", "Chavan", "Bhat", "Acharya"
]