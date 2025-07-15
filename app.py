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
            {'name': 'Pete', 'gender': 'M', 'rating': 3.8},
            {'name': 'Quinn', 'gender': 'F', 'rating': 3.6},
            {'name': 'Rob', 'gender': 'M', 'rating': 3.7},
            {'name': 'Sarah', 'gender': 'F', 'rating': 4.1},
            {'name': 'Tom', 'gender': 'M', 'rating': 3.8},
            {'name': 'Uma', 'gender': 'F', 'rating': 3.9},
            {'name': 'Victor', 'gender': 'M', 'rating': 3.7},
            {'name': 'Wendy', 'gender': 'F', 'rating': 3.8},
            {'name': 'Xavier', 'gender': 'M', 'rating': 3.6}
        ]
        
        # Track partnerships across rounds to prevent duplicates
        self.partnership_history = defaultdict(int)
        
    def get_partnership_key(self, player1, player2):
        """Create a consistent key for a partnership regardless of order"""
        names = sorted([player1['name'], player2['name']])
        return f"{names[0]}|{names[1]}"
    
    def have_partnered_before(self, player1, player2):
        """Check if two players have been partners before"""
        key = self.get_partnership_key(player1, player2)
        return self.partnership_history[key] > 0
    
    def record_partnership(self, player1, player2):
        """Record that two players have been partners"""
        key = self.get_partnership_key(player1, player2)
        self.partnership_history[key] += 1
    
    def validate_player_switch(self, current_matches, player_to_replace, replacement_player):
        """
        Validate if a player switch would create duplicate partnerships
        Returns: (is_valid, message)
        """
        # Find which match and position the player_to_replace is in
        for match_idx, match in enumerate(current_matches):
            team_a, team_b = match
            
            # Check team A
            for pos, player in enumerate(team_a):
                if player['name'] == player_to_replace:
                    # Check if replacement would create duplicate partnership
                    partner = team_a[1 - pos]  # Get the other player in team A
                    if self.have_partnered_before(replacement_player, partner):
                        return False, f"{replacement_player['name']} has already partnered with {partner['name']}"
                    return True, "Valid switch"
            
            # Check team B
            for pos, player in enumerate(team_b):
                if player['name'] == player_to_replace:
                    # Check if replacement would create duplicate partnership
                    partner = team_b[1 - pos]  # Get the other player in team B
                    if self.have_partnered_before(replacement_player, partner):
                        return False, f"{replacement_player['name']} has already partnered with {partner['name']}"
                    return True, "Valid switch"
        
        return False, "Player not found in current matches"

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
        
        # Record partnerships for future constraint checking
        for match in matches:
            team_a, team_b = match
            self.record_partnership(team_a[0], team_a[1])
            self.record_partnership(team_b[0], team_b[1])
        
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
        
        # Initialize partnership history
        self.partnership_history = defaultdict(int)
        
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
            # No restriction on number of players now
            if total_players <= len(tournament_gen.default_players):
                players = random.sample(tournament_gen.default_players, total_players)
            else:
                # If they want more players than we have defaults, cycle through them
                players = []
                default_cycle = itertools.cycle(tournament_gen.default_players)
                for i in range(total_players):
                    player = next(default_cycle).copy()
                    if i >= len(tournament_gen.default_players):
                        player['name'] = f"{player['name']}{i // len(tournament_gen.default_players) + 1}"
                    players.append(player)
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

@app.route('/api/validate_player_switch', methods=['POST'])
def validate_player_switch():
    try:
        data = request.json
        tournament = session.get('tournament', {})
        current_round = session.get('current_round', 0)
        
        player_to_replace = data.get('playerToReplace')
        replacement_player_name = data.get('replacementPlayer')
        
        # Find the replacement player object
        replacement_player = None
        for player in tournament['players']:
            if player['name'] == replacement_player_name:
                replacement_player = player
                break
        
        if not replacement_player:
            return jsonify({"valid": False, "message": "Replacement player not found"})
        
        # Get current matches
        current_matches = tournament['schedule'][current_round]['matches']
        
        # Validate the switch
        is_valid, message = tournament_gen.validate_player_switch(
            current_matches, player_to_replace, replacement_player
        )
        
        return jsonify({"valid": is_valid, "message": message})
        
    except Exception as e:
        print(f"ERROR in validate_player_switch: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/apply_player_switches', methods=['POST'])
def apply_player_switches():
    try:
        data = request.json
        switches = data.get('switches', [])
        round_index = data.get('roundIndex', session.get('current_round', 0))
        
        tournament = session.get('tournament', {})
        
        if not tournament or 'schedule' not in tournament:
            return jsonify({"error": "No tournament data found"}), 400
        
        if round_index >= len(tournament['schedule']):
            return jsonify({"error": "Invalid round index"}), 400
        
        # Apply all switches to the specified round
        current_matches = tournament['schedule'][round_index]['matches']
        
        # Create a mapping of player names to player objects for quick lookup
        player_map = {}
        for player in tournament['players']:
            # Handle both name formats
            if 'name' in player and player['name']:
                player_map[player['name']] = player
            elif 'firstName' in player:
                full_name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                if full_name:
                    player_map[full_name] = player
                    player_map[player['firstName']] = player  # Also map by first name only
        
        print(f"DEBUG: Available players in map: {list(player_map.keys())}")
        print(f"DEBUG: Applying {len(switches)} switches: {switches}")
        
        # Apply each switch
        switches_applied = 0
        for switch in switches:
            old_player_name = switch['oldPlayer']
            new_player_name = switch['newPlayer']
            
            print(f"DEBUG: Switching {old_player_name} -> {new_player_name}")
            
            if new_player_name not in player_map:
                print(f"ERROR: New player '{new_player_name}' not found in player map")
                print(f"Available players: {list(player_map.keys())}")
                continue
                
            new_player = player_map[new_player_name]
            
            # Find and replace the player in matches
            switch_applied = False
            for match_idx, match in enumerate(current_matches):
                team_a, team_b = match
                
                # Check team A
                for i, player in enumerate(team_a):
                    player_name = player.get('name') or f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                    if player_name == old_player_name:
                        team_a[i] = new_player
                        switch_applied = True
                        switches_applied += 1
                        print(f"DEBUG: Replaced {old_player_name} with {new_player_name} in Team A of match {match_idx}")
                        break
                
                if switch_applied:
                    break
                
                # Check team B
                for i, player in enumerate(team_b):
                    player_name = player.get('name') or f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                    if player_name == old_player_name:
                        team_b[i] = new_player
                        switch_applied = True
                        switches_applied += 1
                        print(f"DEBUG: Replaced {old_player_name} with {new_player_name} in Team B of match {match_idx}")
                        break
                
                if switch_applied:
                    break
            
            if not switch_applied:
                print(f"WARNING: Could not find player {old_player_name} to replace")
        
        if switches_applied == 0:
            return jsonify({"error": "No switches were applied. Check player names match exactly."}), 400
        
        # Update sit-outs based on new assignments
        all_playing = set()
        for match in current_matches:
            team_a, team_b = match
            for player in team_a + team_b:
                player_name = player.get('name') or f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
                all_playing.add(player_name)
        
        all_players = set()
        for player in tournament['players']:
            player_name = player.get('name') or f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
            all_players.add(player_name)
        
        sitting_out = list(all_players - all_playing)
        tournament['schedule'][round_index]['sit_outs'] = sitting_out
        
        print(f"DEBUG: Updated sit-outs: {sitting_out}")
        
        # Update session
        session['tournament'] = tournament
        session.modified = True
        
        print(f"DEBUG: Successfully applied {switches_applied} out of {len(switches)} switches")
        return jsonify({"success": True, "applied_switches": switches_applied, "total_switches": len(switches)})
        
    except Exception as e:
        print(f"ERROR in apply_player_switches: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to apply switches: {str(e)}"}), 500

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
        player_switches = data.get('playerSwitches', [])
        
        current = session.get('current_round', 0)
        tournament = session.get('tournament', {})
        config = session.get('config', {})
        
        print(f"DEBUG: Advancing from round {current}, skip players: {skip_players}, switches: {player_switches}")
        
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
            
            # Apply any manual player switches for the next round
            if player_switches:
                # Apply switches to the newly generated round
                current_matches = tournament['schedule'][next_round]['matches']
                player_map = {p['name']: p for p in tournament['players']}
                
                for switch in player_switches:
                    old_player_name = switch['oldPlayer']
                    new_player_name = switch['newPlayer']
                    
                    if new_player_name not in player_map:
                        continue
                        
                    new_player = player_map[new_player_name]
                    
                    # Find and replace the player in matches
                    for match in current_matches:
                        team_a, team_b = match
                        
                        # Check team A
                        for i, player in enumerate(team_a):
                            if player['name'] == old_player_name:
                                team_a[i] = new_player
                                break
                        
                        # Check team B
                        for i, player in enumerate(team_b):
                            if player['name'] == old_player_name:
                                team_b[i] = new_player
                                break
            
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
