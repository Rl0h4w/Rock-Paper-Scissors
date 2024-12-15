import asyncio
import websockets
import json

class RockPaperScissorsGame:
    """
    A class to manage the Rock-Paper-Scissors game between two players.

    Attributes:
        player1_ws (websockets.WebSocketServerProtocol): WebSocket for Player 1.
        player2_ws (websockets.WebSocketServerProtocol): WebSocket for Player 2.
        players (dict): A dictionary mapping WebSocket connections to their moves.
        game_over (bool): A flag indicating whether the game has ended.
    """

    def __init__(self, player1_ws, player2_ws):
        """
        Initializes the game with two player WebSocket connections.

        Args:
            player1_ws (websockets.WebSocketServerProtocol): WebSocket for Player 1.
            player2_ws (websockets.WebSocketServerProtocol): WebSocket for Player 2.
        """
        self.players = {player1_ws: None, player2_ws: None}
        self.player1_ws = player1_ws
        self.player2_ws = player2_ws
        self.game_over = False

    async def receive_move(self, websocket):
        """
        Receives and validates a move from a player.

        Args:
            websocket (websockets.WebSocketServerProtocol): The WebSocket connection of the player.

        Returns:
            bool: True if the move is valid, otherwise False.
        """
        try:
            data = await websocket.recv()
            message = json.loads(data)
            move = message.get("move")
            if move not in ["rock", "paper", "scissors"]:
                await websocket.send(json.dumps({"type": "error", "message": "Invalid move"}))
                return False
            self.players[websocket] = move
            return True
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            return False

    async def determine_winner(self):
        """
        Determines the winner based on the players' moves and broadcasts the result.
        """
        move1 = self.players[self.player1_ws]
        move2 = self.players[self.player2_ws]
        result = self.get_result(move1, move2)
        await self.broadcast({"type": "result", "move1": move1, "move2": move2, "result": result})
        self.game_over = True

    def get_result(self, move1, move2):
        """
        Determines the result of the game using traditional Rock-Paper-Scissors rules.

        Args:
            move1 (str): Move of Player 1.
            move2 (str): Move of Player 2.

        Returns:
            str: 'player1' if Player 1 wins, 'player2' if Player 2 wins, 'draw' if it's a tie.
        """
        if move1 == move2:
            return "draw"
        wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        return "player1" if wins[move1] == move2 else "player2"

    async def broadcast(self, message):
        """
        Sends a message to both players.

        Args:
            message (dict): The message to broadcast.
        """
        await self.player1_ws.send(json.dumps(message))
        await self.player2_ws.send(json.dumps(message))

    async def ask_for_rematch(self):
        """
        Prompts both players to decide if they want a rematch.

        If both players agree, the game state is reset and a new game begins.
        Otherwise, the game ends.
        """
        await self.broadcast({"type": "rematch"})
        responses = await asyncio.gather(
            self.receive_response(self.player1_ws),
            self.receive_response(self.player2_ws),
        )
        if all(responses):
            self.reset_game()
            await start_game(self)
        else:
            await self.broadcast({"type": "end", "message": "Game over."})

    async def receive_response(self, websocket):
        """
        Receives a response from a player about the rematch request.

        Args:
            websocket (websockets.WebSocketServerProtocol): The WebSocket connection of the player.

        Returns:
            bool: True if the player agrees to a rematch, otherwise False.
        """
        try:
            data = await websocket.recv()
            message = json.loads(data)
            return message.get("rematch") == "yes"
        except websockets.exceptions.ConnectionClosed:
            return False

    def reset_game(self):
        """
        Resets the game state for a new round.
        """
        self.players = {self.player1_ws: None, self.player2_ws: None}
        self.game_over = False

async def handler(websocket):
    """
    Handles incoming WebSocket connections and assigns players to games.

    Args:
        websocket (websockets.WebSocketServerProtocol): The incoming WebSocket connection.
    """
    print("New connection")
    try:
        if waiting_players:
            opponent_ws = waiting_players.pop(0)
            game = RockPaperScissorsGame(opponent_ws, websocket)
            await start_game(game)
        else:
            waiting_players.append(websocket)
            await websocket.send(json.dumps({"type": "waiting", "message": "Waiting for an opponent..."}))
            await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    finally:
        if websocket in waiting_players:
            waiting_players.remove(websocket)

async def start_game(game):
    """
    Sends game start messages to both players and begins the game loop.

    Args:
        game (RockPaperScissorsGame): The game instance.
    """
    await game.player1_ws.send(json.dumps({"type": "start", "player": "player1", "message": "Game started. You are Player 1"}))
    await game.player2_ws.send(json.dumps({"type": "start", "player": "player2", "message": "Game started. You are Player 2"}))
    await game_loop(game)

async def game_loop(game):
    """
    The main game loop for handling moves and determining the winner.

    Args:
        game (RockPaperScissorsGame): The game instance.
    """
    while not game.game_over:
        await game.player1_ws.send(json.dumps({"type": "your_move", "message": "Enter your move (rock, paper, or scissors):"}))
        await game.player2_ws.send(json.dumps({"type": "your_move", "message": "Enter your move (rock, paper, or scissors):"}))

        results = await asyncio.gather(
            game.receive_move(game.player1_ws),
            game.receive_move(game.player2_ws),
        )

        if not all(results):
            await game.broadcast({"type": "error", "message": "A player disconnected or made an invalid move."})
            break

        await game.determine_winner()
        break

    await game.ask_for_rematch()

waiting_players = []

async def main():
    """
    The main entry point for the WebSocket server.

    Listens for incoming connections and manages game sessions.
    """
    async with websockets.serve(handler, "localhost", 6789):
        print("Server started at ws://localhost:6789")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
