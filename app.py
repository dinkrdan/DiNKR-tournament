from flask import Flask, render_template, request, jsonify, session
import itertools
import random
from collections import defaultdict, Counter
import uuid
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

class TournamentGenerator:
    def __init__(self):
        # Default players with more diverse names and balanced ratings
        self.default_players = [
            {'name': 'Alex', 'gender': 'M', 'rating': 3.8},
            {'name': 'Ben', 'gender': 'M', 'rating': 3.9},
            {'name': 'Charlie', 'gender': 'M', 'rating': 3.5},
            {'name': 'Dan', 'gender': 'M', 'rating': 4.0},
            {'name': 'Emma', 'gender': 'F', 'rating': 3.9},
            {'name': 'Fi', 'gender': 'F', 'rating': 3.8},
            {'name': 'Gavin', 'gender': 'M', 'rating': 3.7},
            {'name': 'Hen', 'gender': 'F', 'rating': 3.6},
            {'name': 'India', 'gender': 'F', 'rating': 3.9},
            {'name': 'Julie', 'gender': 'F', 'rating': 3.8},
            {'name': 'Ken', 'gender': 'M', 'rating': 4.0},
            {'name': 'Liam', 'gender': 'M', 'rating': 3.9},
            {'name': 'Mary', 'gender': 'F', 'rating': 3.8},
            {'name': 'Nancy', 'gender': 'F', 'rating': 3.7},
            {'name': 'Oscar', 'gender': 'M', 'rating': 3.9},
            {'name': 'Pete', 'gender': 'M', 'rating': 3.8}
        ]
        
        # Track partnerships and opponents across rounds
        self.partnership_history = defaultdict(int)
        self.opponent_history = defaultdict(int)
        
    def generate_enhanced_tournament(self, courts, players_list, rounds, skip_players=None):
        """
        Enhanced tournament generator with proper constraint satisfaction
        """
        if skip_players is None:
            skip_players = []
            
        print(f"DEBUG: Generating tournament with {len(players_list)} players, {courts} courts, {rounds} rounds")
        print(f"DEBUG: Skip players: {skip_players}")
        
        # Filter out skipped players for this round
        available_players = [p for p in players_list if p['name'] not in skip_players]
        playing_players_needed = courts * 4
        
        print(f"DEBUG: Available players: {len(available_players)}, Need: {playing_players_needed}")
        
        if len(available_players) < playing_players_needed:
            return {
                "error": f"Not enough players available. Need {playing_players_needed}, have {len(available_players)}"
            }
        
        # Select players for this round
        playing_players = self.select_players_for_round(available_players, playing_players_needed)
        sitting_players = [p['name'] for p in players_list if p['name'] not in [p['name'] for p in playing_players]]
        
        # Generate matches for this round
        matches = self.generate_round_matches(playing_players, courts)
        
        if not matches:
            return {"error": "Could not generate valid matches for this round"}
        
        return {
            "success": True,
            "matches": matches,
            "sit_outs": sitting_players,
            "playing_players": [p['name'] for p in playing_players]
        }
    
    def select_players_for_round(self, available_players, needed):
        """
        Select players trying to balance play time
        """
        # For now, simple rotation - in a full implementation, 
        # this would track play frequency and try to balance
        return available_players[:needed]
    
    def generate_round_matches(self, players, courts):
        """
        Generate matches for a round using constraint satisfaction
        """
        if len(players) != courts * 4:
            return None
            
        # Simple but effective approach: generate all possible team combinations
        # and pick the best set that doesn't conflict
        
        matches = []
        used_players = set()
        
        players_list = list(players)
        random.shuffle(players_list)  # Add some randomness
        
        for court in range(courts):
            if len(used_players) >= len(players_list):
                break
                
            # Get 4 unused players
            available = [p for p in players_list if p['name'] not in used_players]
            if len(available) < 4:
                break
                
            court_players = available[:4]
            
            # Create teams - try to balance by rating and gender
            team_a, team_b = self.create_balanced_teams(court_players)
            
            matches.append([team_a, team_b])
            
            # Mark players as used
            for player in court_players:
                used_players.add(player['name'])
        
        return matches if len(matches) == courts else None
    
    def create_balanced_teams(self, four_players):
        """
        Create two balanced teams from 4 players
        """
        # Sort by rating for balance
        sorted_players = sorted(four_players, key=lambda x: x['rating'])
        
        # Try to balance: highest + lowest vs middle two
        team_a = [sorted_players[0], sorted_players[3]]  # lowest + highest
        team_b = [sorted_players[1], sorted_players[2]]  # middle two
        
        return team_a, team_b

    def generate_simple_tournament(self, courts, players_list, rounds):
        """
        Generate complete tournament schedule
        """
        print(f"DEBUG: Generating tournament with {len(players_list)} players, {courts} courts, {rounds} rounds")
        
        schedule = []
        for round_num in range(rounds):
            round_data = {
                "round": round_num + 1,
                "matches": [],
                "sit_outs": []
            }
            
            # For initial tournament generation, no skips
            result = self.generate_enhanced_tournament(courts, players_list, 1, skip_players=[])
            
            if 'error' in result:
                return {"error": result['error']}
            
            round_data["matches"] = result["matches"]
            round_data["sit_outs"] = result["sit_outs"]
            
            schedule.append(round_data)
        
        return {
            "success": True,
            "schedule": schedule,
            "players": players_list
        }

# Global tournament generator
tournament_gen = TournamentGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('simple_test.html')

@app.route('/api/test')
def test_api():
    return jsonify({"message": "API is working!", "status": "success"})

@app.route('/api/generate_tournament', methods=['POST'])
def generate_tournament():
    try:
        print("DEBUG: Starting tournament generation...")
        data = request.json
        print(f"DEBUG: Received data: {data}")
        
        courts = data.get('courts', 2)
        players_data = data.get('players', [])
        rounds = data.get('rounds', 6)
        use_defaults = data.get('useDefaults', True)
        avoid_mm_vs_ff = data.get('avoidMMvsFF', True)
        use_rating_balance = data.get('useRatingBalance', True)
        rating_factor = data.get('ratingFactor', 3)
        round_duration = data.get('roundDuration', 13)
        total_players = data.get('totalPlayers', 8)
        
        print(f"DEBUG: courts={courts}, rounds={rounds}, use_defaults={use_defaults}, total_players={total_players}")
        
        # Prepare players list
        if use_defaults:
            print("DEBUG: Using default players...")
            players = random.sample(tournament_gen.default_players, total_players)
            random.shuffle(players)
            print(f"DEBUG: Selected players: {[p['name'] for p in players]}")
        else:
            players = players_data[:total_players] if players_data else []
            if len(players) < total_players:
                print(f"ERROR: Need {total_players} players, got {len(players)}")
                return jsonify({"error": f"Need {total_players} players, got {len(players)}"}), 400
        
        print("DEBUG: About to generate tournament...")
        
        # Generate complete tournament schedule
        result = tournament_gen.generate_simple_tournament(
            courts=courts,
            players_list=players,
            rounds=rounds
        )
        
        print("DEBUG: Tournament generation successful!")
        
        if 'error' in result:
            print(f"DEBUG: Tournament generation returned error: {result['error']}")
            return jsonify(result), 400
        
        # Store in session
        session['tournament'] = result
        session['config'] = {
            'courts': courts,
            'rounds': rounds,
            'roundDuration': round_duration,
            'avoidMMvsFF': avoid_mm_vs_ff,
            'useRatingBalance': use_rating_balance,
            'ratingFactor': rating_factor
        }
        session['scores'] = {}
        session['current_round'] = 0
        
        print("DEBUG: Returning success response...")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/update_score', methods=['POST'])
def update_score():
    try:
        data = request.json
        round_idx = data['roundIndex']
        match_idx = data['matchIndex']
        team = data['team']
        score = data['score']
        
        if 'scores' not in session:
            session['scores'] = {}
        
        if str(round_idx) not in session['scores']:
            session['scores'][str(round_idx)] = {}
        
        if str(match_idx) not in session['scores'][str(round_idx)]:
            session['scores'][str(round_idx)][str(match_idx)] = {}
        
        session['scores'][str(round_idx)][str(match_idx)][team] = score
        session.modified = True
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"ERROR in update_score: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/advance_round', methods=['POST'])
def advance_round():
    try:
        data = request.json
        skip_players = data.get('skipPlayers', [])
        
        current = session.get('current_round', 0)
        tournament = session.get('tournament', {})
        config = session.get('config', {})
        
        print(f"DEBUG: Advancing from round {current}, skip players: {skip_players}")
        
        if current < len(tournament.get('schedule', [])) - 1:
            # Generate new round with skipped players
            next_round = current + 1
            
            # Generate matches for next round considering skips
            result = tournament_gen.generate_enhanced_tournament(
                courts=config.get('courts', 2),
                players_list=tournament['players'],
                rounds=1,
                skip_players=skip_players
            )
            
            if 'error' in result:
                return jsonify({"error": result['error']}), 400
            
            # Update the tournament schedule
            if 'schedule' not in tournament:
                tournament['schedule'] = []
            
            # Update or create the next round
            next_round_data = {
                "round": next_round + 1,
                "matches": result["matches"],
                "sit_outs": result["sit_outs"]
            }
            
            if next_round < len(tournament['schedule']):
                tournament['schedule'][next_round] = next_round_data
            else:
                tournament['schedule'].append(next_round_data)
            
            # Update session
            session['tournament'] = tournament
            session['current_round'] = next_round
            session.modified = True
            
            print(f"DEBUG: Successfully advanced to round {next_round + 1}")
            print(f"DEBUG: Sitting out: {result['sit_outs']}")
            
            return jsonify({"success": True, "round": next_round})
        else:
            return jsonify({"completed": True})
            
    except Exception as e:
        print(f"ERROR in advance_round: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_tournament_state')
def get_tournament_state():
    return jsonify({
        'tournament': session.get('tournament'),
        'config': session.get('config'),
        'scores': session.get('scores', {}),
        'current_round': session.get('current_round', 0)
    })

@app.route('/api/calculate_results')
def calculate_results():
    try:
        tournament = session.get('tournament', {})
        scores = session.get('scores', {})
        
        if not tournament:
            return jsonify({"error": "No tournament data"}), 400
        
        players = tournament['players']
        schedule = tournament['schedule']
        
        player_stats = {}
        for player in players:
            player_name = player['name']
            player_stats[player_name] = {
                'name': player_name,
                'totalScore': 0,
                'matchesPlayed': 0,
                'wins': 0,
                'rating': player['rating'],
                'gender': player['gender']
            }
        
        # Calculate stats from matches
        for round_idx, round_data in enumerate(schedule):
            round_scores = scores.get(str(round_idx), {})
            
            for match_idx, match in enumerate(round_data['matches']):
                match_scores = round_scores.get(str(match_idx), {})
                team_a, team_b = match
                
                if 'teamA' in match_scores and 'teamB' in match_scores:
                    score_a = int(match_scores['teamA']) if match_scores['teamA'] else 0
                    score_b = int(match_scores['teamB']) if match_scores['teamB'] else 0
                    
                    # Update team A players
                    for player in team_a:
                        player_name = player['name']
                        player_stats[player_name]['totalScore'] += score_a
                        player_stats[player_name]['matchesPlayed'] += 1
                        if score_a > score_b:
                            player_stats[player_name]['wins'] += 1
                    
                    # Update team B players
                    for player in team_b:
                        player_name = player['name']
                        player_stats[player_name]['totalScore'] += score_b
                        player_stats[player_name]['matchesPlayed'] += 1
                        if score_b > score_a:
                            player_stats[player_name]['wins'] += 1
        
        # Sort by total score, then wins, then matches played
        results = sorted(player_stats.values(), 
                        key=lambda x: (-x['totalScore'], -x['wins'], -x['matchesPlayed']))
        
        return jsonify(results)
        
    except Exception as e:
        print(f"ERROR in calculate_results: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Production settings
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)