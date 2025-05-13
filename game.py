from enum import Enum, auto

class Choice(Enum):
    """Enum representing Rock, Paper, Scissors choices"""
    ROCK = auto()
    PAPER = auto()
    SCISSORS = auto()
    
    def __str__(self):
        """Return a capitalized string representation of the choice"""
        return self.name.capitalize()

class GameResult(Enum):
    """Enum representing possible game outcomes"""
    WIN = auto()
    LOSE = auto()
    TIE = auto()

def determine_winner(player_choice, computer_choice):
    """
    Determine the winner of a rock-paper-scissors round
    
    Args:
        player_choice (Choice): The player's choice
        computer_choice (Choice): The computer's choice
        
    Returns:
        GameResult: The result of the game (WIN, LOSE, or TIE)
    """
    if player_choice == computer_choice:
        return GameResult.TIE
    elif (
        (player_choice == Choice.ROCK and computer_choice == Choice.SCISSORS) or
        (player_choice == Choice.PAPER and computer_choice == Choice.ROCK) or
        (player_choice == Choice.SCISSORS and computer_choice == Choice.PAPER)
    ):
        return GameResult.WIN
    else:
        return GameResult.LOSE
