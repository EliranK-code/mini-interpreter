from parser import run


def main():
    env = {}
    while True:
        try:
            line = input(">>> ")
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if line.strip() == "":
            continue
        
        if line.strip() == "exit":
            break
        try:
            result = run(line, env)
            print(result)
        except (SyntaxError, NameError, ZeroDivisionError) as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()