import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from game import Choice, GameResult, determine_winner
import random

# Configure logging for easier debugging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "rock_paper_scissors_secret")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with Flask
db = SQLAlchemy(model_class=Base)

# Initialize the app with the SQLAlchemy extension
db.init_app(app)

# Import models after initializing app and db to avoid circular imports
with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    """Render the main landing page"""
    # Check if the player name is stored in the session
    player_name = session.get('player_name', None)
    return render_template('index.html', player_name=player_name)

@app.route('/register', methods=['POST'])
def register_player():
    """Register a player name"""
    player_name = request.form.get('player_name', '').strip()
    
    if not player_name:
        player_name = 'Anonymous'
    
    # Store the player name in the session
    session['player_name'] = player_name
    
    # Check if the player already exists in the database
    player = models.Player.query.filter_by(name=player_name).first()
    
    # If the player doesn't exist, create a new one
    if not player:
        new_player = models.Player()
        new_player.name = player_name
        db.session.add(new_player)
        db.session.commit()
        player = new_player
    
    # Store the player ID in the session
    session['player_id'] = player.id
    
    # Redirect back to the index page
    return redirect(url_for('index'))

@app.route('/game')
def game():
    """Render the game page"""
    # Reset the game state when starting a new game
    rounds = request.args.get('rounds', 3, type=int)
    
    session['rounds'] = rounds
    session['current_round'] = 1
    session['player_score'] = 0
    session['computer_score'] = 0
    session['game_history'] = []
    
    return render_template('game.html', rounds=rounds)

@app.route('/play', methods=['POST'])
def play():
    """Handle a player's move"""
    # Get player choice from form data
    player_choice_str = request.form.get('choice')
    
    try:
        # Convert string to Choice enum
        if player_choice_str is None:
            return jsonify({'error': "No choice provided. Choose rock, paper, or scissors."}), 400
        player_choice = Choice[player_choice_str.upper()]
        
        # Get computer choice
        computer_choice = random.choice(list(Choice))
        
        # Determine the winner
        result = determine_winner(player_choice, computer_choice)
        
        # Update scores
        if result == GameResult.WIN:
            session['player_score'] = session.get('player_score', 0) + 1
            result_text = "You win this round!"
        elif result == GameResult.LOSE:
            session['computer_score'] = session.get('computer_score', 0) + 1
            result_text = "Computer wins this round!"
        else:
            result_text = "It's a tie!"
            
        # Update current round
        current_round = session.get('current_round', 1)
        
        # Store round results in history
        round_result = {
            'round': current_round,
            'player_choice': player_choice.name,
            'computer_choice': computer_choice.name,
            'result': result.name,
            'result_text': result_text
        }
        
        # Add to history
        history = session.get('game_history', [])
        history.append(round_result)
        session['game_history'] = history
        
        # Increment the round
        session['current_round'] = current_round + 1
        
        # Check if the game is over
        total_rounds = session.get('rounds', 3)
        game_over = current_round >= total_rounds
        
        # Determine final game result if the game is over
        final_result = None
        if game_over:
            player_score = session.get('player_score', 0)
            computer_score = session.get('computer_score', 0)
            
            # Determine the game result
            if player_score > computer_score:
                final_result = "🎉 Congratulations! You won the game!"
                game_result = "WIN"
            elif player_score < computer_score:
                final_result = "😞 Computer won the game. Better luck next time!"
                game_result = "LOSE"
            else:
                final_result = "🤝 It's a draw!"
                game_result = "TIE"
            
            # Save the game result to the database if the player is registered
            player_id = session.get('player_id')
            if player_id:
                # Create a new game record
                game = models.Game()
                game.player_id = player_id
                game.rounds = total_rounds
                game.player_score = player_score
                game.computer_score = computer_score
                game.result = game_result
                
                db.session.add(game)
                db.session.flush()  # Get the game ID before committing
                
                # Save all rounds for this game
                for round_data in session.get('game_history', []):
                    game_round = models.GameRound()
                    game_round.game_id = game.id
                    game_round.round_number = round_data['round']
                    game_round.player_choice = round_data['player_choice']
                    game_round.computer_choice = round_data['computer_choice']
                    game_round.result = round_data['result']
                    
                    db.session.add(game_round)
                
                # Commit all changes to the database
                db.session.commit()
        
        # Return the results as JSON for AJAX handling
        return jsonify({
            'player_choice': player_choice.name,
            'computer_choice': computer_choice.name,
            'result': result.name,
            'result_text': result_text,
            'player_score': session.get('player_score', 0),
            'computer_score': session.get('computer_score', 0),
            'current_round': current_round,
            'total_rounds': total_rounds,
            'game_over': game_over,
            'final_result': final_result
        })
        
    except (KeyError, ValueError) as e:
        return jsonify({'error': f"Invalid choice: {player_choice_str}. Choose rock, paper, or scissors."}), 400

@app.route('/reset', methods=['POST'])
def reset_game():
    """Reset the game state for a new game"""
    rounds = request.form.get('rounds', 3, type=int)
    
    session['rounds'] = rounds
    session['current_round'] = 1
    session['player_score'] = 0
    session['computer_score'] = 0
    session['game_history'] = []
    
    return jsonify({'success': True, 'rounds': rounds})

@app.route('/stats')
def stats():
    """Display player statistics and game history"""
    player_id = session.get('player_id')
    
    if not player_id:
        # Redirect to the home page if no player is logged in
        return redirect(url_for('index'))
    
    # Get the player information
    player = models.Player.query.get(player_id)
    
    if not player:
        # Redirect to the home page if the player doesn't exist
        session.pop('player_id', None)
        session.pop('player_name', None)
        return redirect(url_for('index'))
    
    # Get the player's games, ordered by most recent first
    games = models.Game.query.filter_by(player_id=player_id).order_by(models.Game.created_at.desc()).all()
    
    # Calculate player statistics
    total_games = len(games)
    wins = sum(1 for game in games if game.result == 'WIN')
    losses = sum(1 for game in games if game.result == 'LOSE')
    ties = sum(1 for game in games if game.result == 'TIE')
    
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    
    # Prepare game history with rounds
    game_history = []
    for game in games[:10]:  # Limit to 10 most recent games
        # Get all rounds for this game
        rounds = models.GameRound.query.filter_by(game_id=game.id).order_by(models.GameRound.round_number).all()
        
        game_history.append({
            'id': game.id,
            'date': game.created_at,
            'rounds': game.rounds,
            'player_score': game.player_score,
            'computer_score': game.computer_score,
            'result': game.result,
            'round_data': rounds
        })
    
    return render_template('stats.html', 
                           player=player,
                           total_games=total_games,
                           wins=wins,
                           losses=losses,
                           ties=ties,
                           win_rate=win_rate,
                           game_history=game_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
