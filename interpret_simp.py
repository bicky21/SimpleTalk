def interpret_program(program):
    # Split the program into lines
    lines = program.split('\n')
    for line in lines:
        # Split the line into tokens
        tokens = line.split()
        # Check if the program starts with "say "
        if tokens[0] == "say":
            if len(tokens) >= 2:
                # Check if the message is enclosed in double quotes
                message = tokens[1]
                if message.startswith('"') and message.endswith('"'):
                    # Print the message without the double quotes
                    print(message[1:-1])
                else:
                    print("Error: Invalid message format.")
            else:
                print("Error: Missing message.")
        else:
            print("Error: Invalid program syntax.")

def main():
    # Read the program file
    with open('hello.simp', 'r') as file:
        program = file.read()
    # Interpret the program
    interpret_program(program)

if __name__ == "__main__":
    main()
