import random

choices = ["rock", "paper", "scissors"]

print("=== Welcome to Rock, Paper, Scissors Game ===\n")
print("-- Game Rules --")
print("1. This is a Best of 3 game (exactly 3 rounds).")
print("2. Whoever wins 2 rounds wins the match.")
print("3. If no one wins 2 rounds after 3 rounds, the match is a draw.")
print("4. Rock beats Scissors")
print("5. Scissors beats Paper")
print("6. Paper beats Rock")
print("7. Same choice results in a draw.\n")

while True:
    user_score = 0
    computer_score = 0
    round_number = 1

    # Exactly 3 rounds
    while round_number <= 3:
        print(f"\n--- Round {round_number} ---")

        user_choice = input("Enter your choice (Rock, Paper, Scissors): ").strip().lower()
        if user_choice not in choices:
            print("Invalid choice! Please enter Rock, Paper, or Scissors.")
            continue

        computer_choice = random.choice(choices)

        # Decide round result
        if user_choice == computer_choice:
            result = "It's a Draw!"
        elif (user_choice == "rock" and computer_choice == "scissors") or \
             (user_choice == "paper" and computer_choice == "rock") or \
             (user_choice == "scissors" and computer_choice == "paper"):
            result = "You Win this round!"
            user_score += 1
        else:
            result = "Computer Wins this round!"
            computer_score += 1

        # Display round result
        print("\n--- Round Result ---")
        print(f"Your choice: {user_choice.capitalize()}")
        print(f"Computer's choice: {computer_choice.capitalize()}")
        print(f"Result: {result}")
        print(f"Score → You: {user_score} | Computer: {computer_score}")

        round_number += 1

    # Final match result after 3 rounds
    print("\n=== Match Result ===")
    if user_score == 2:
        print("Congratulations! You won the match!")
    elif computer_score == 2:
        print("Computer won the match. Better luck next time!")
    else:
        print("The match is a draw!")

    # Play again
    play = input("\nDo you want to play another match? (Yes/No): ").strip().lower()
    if play != "yes":
        print("\nThank you for playing! Goodbye!")
        break