# hardcoded chunk, fuzzy comparison, no API keys
import sys

while True:

    try:
        print(":> ", end="", flush=True)
        user_input = input()

        if not user_input.strip():
            continue

        if user_input == "!reveal":
            # answer directly
            print("placeholder - direct answer")
        elif user_input.startswith("!"):
            #unknown command, warn
            print("placeholder - warn not a command!")
        else:
            # teacher mode
            # Step 1: Ask the question (you already have it in user_input)
            # Step 2: Retrieve chunks (placeholder for now)
            # Step 3: Prompt user to explain
            explanation = input("Explain this in your own words: ")
            # Step 4: Generate critique (placeholder)
            print("placeholder - critique")

    except KeyboardInterrupt:
        print("\n> exiting..", flush=True)
        sys.exit(0)
