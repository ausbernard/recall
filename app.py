# Only if you need change the CLI (add a flag, change prompt style)

from session import Session
from config import load_config

def main():
    config = load_config()
    session = Session(config)

    while True:
        try:
            print(":> ", end="", flush=True)
            user_input = input()
            output = session.handle(user_input)
            print(output)
        except KeyboardInterrupt:
            print("\n> Bye.")
            break

if __name__ == "__main__":
    main()
