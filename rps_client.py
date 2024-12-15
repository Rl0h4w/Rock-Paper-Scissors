import asyncio
import websockets
import json

def validate_move(move):
    """
    Validates if the provided move is one of the allowed moves in the game.

    Args:
        move (str): The player's move to validate.

    Returns:
        bool: True if the move is valid (rock, paper, or scissors), otherwise False.
    """
    valid_moves = ["rock", "paper", "scissors"]
    return move in valid_moves

async def play():
    """
    Connect to the server and play the game.

    Establishes a WebSocket connection with the server, handles game logic including
    sending moves, receiving results, and responding to rematch requests.
    """
    uri = "ws://localhost:6789"  # Server address
    async with websockets.connect(uri) as websocket:
        player = None  # Will hold 'player1' or 'player2'
        while True:
            try:
                data = await websocket.recv()  # Receive data from the server
                message = json.loads(data)  # Parse JSON message

                if message["type"] == "waiting":
                    print(message["message"])

                elif message["type"] == "start":
                    player = message["player"]
                    print(message["message"])

                elif message["type"] == "your_move":
                    print(message["message"])
                    move = ""
                    while not validate_move(move):
                        move = input("Enter your move (rock, paper, or scissors): ").strip().lower()
                        if not validate_move(move):
                            print("Invalid move. Please enter 'rock', 'paper', or 'scissors'.")
                    await websocket.send(json.dumps({"move": move}))

                elif message["type"] == "result":
                    move1 = message["move1"]
                    move2 = message["move2"]
                    result = message["result"]
                    print(f"Player 1 chose: {move1}")
                    print(f"Player 2 chose: {move2}")

                    if result == "draw":
                        print("Draw!")
                    elif (result == "player1" and player == "player1") or (
                        result == "player2" and player == "player2"
                    ):
                        print("You won!")
                    else:
                        print("You lost.")

                elif message["type"] == "rematch":
                    answer = ""
                    while answer not in ["yes", "no"]:
                        answer = input("Do you want to play again? (yes/no): ").strip().lower()
                        if answer not in ["yes", "no"]:
                            print("Invalid response. Please enter 'yes' or 'no'.")
                    await websocket.send(json.dumps({"rematch": answer}))

                elif message["type"] == "end":
                    print("Game over.")
                    break

                elif message["type"] == "error":
                    print("Error:", message["message"])
                    break

                else:
                    print("Unknown message:", message)

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

if __name__ == "__main__":
    asyncio.run(play())
