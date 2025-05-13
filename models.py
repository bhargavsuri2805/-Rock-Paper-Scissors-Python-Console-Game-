from datetime import datetime
# Import db directly to avoid circular imports
from app import db


class Player(db.Model):
    """Player model to store information about players"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, default='Anonymous')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    games = db.relationship('Game', backref='player', lazy='dynamic')

    def __repr__(self):
        return f'<Player {self.name}>'


class Game(db.Model):
    """Game model to store completed games"""
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    rounds = db.Column(db.Integer, nullable=False)
    player_score = db.Column(db.Integer, nullable=False)
    computer_score = db.Column(db.Integer, nullable=False)
    result = db.Column(db.String(16), nullable=False)  # 'WIN', 'LOSE', 'TIE'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rounds_data = db.relationship('GameRound', backref='game', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Game {self.id} - Player: {self.player_id}, Result: {self.result}>'


class GameRound(db.Model):
    """Model to store individual rounds of a game"""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    player_choice = db.Column(db.String(16), nullable=False)  # 'ROCK', 'PAPER', 'SCISSORS'
    computer_choice = db.Column(db.String(16), nullable=False)  # 'ROCK', 'PAPER', 'SCISSORS'
    result = db.Column(db.String(16), nullable=False)  # 'WIN', 'LOSE', 'TIE'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GameRound {self.id} - Game: {self.game_id}, Round: {self.round_number}>'
