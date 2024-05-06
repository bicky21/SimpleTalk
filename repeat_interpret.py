def interpret_program(program):
    # Split the program into lines
    lines = program.split('\n')
    repeat_stack = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
        # Split the line into tokens
        tokens = line.split()
        if tokens[0] == "repeat":
            if len(tokens) == 3 and tokens[2] == "times":
                # Push the repeat count to the stack
                repeat_stack.append((int(tokens[1]), i))  # Store the start index of the repeat block
            else:
                print("Error: Invalid repeat syntax.")
        elif tokens[0] == "end" and tokens[1] == "repeat":
            # Pop the repeat count and start index from the stack
            count, start_index = repeat_stack.pop()
            # Repeat the block of code count-1 times
            block = "\n".join(lines[start_index+1:i])
            for _ in range(count-1):
                interpret_program(block)
        elif tokens[0] == "say":
            if len(tokens) >= 2:
                message = " ".join(tokens[1:])
                if message.startswith('"') and message.endswith('"'):
                    print(message[1:-1])
                else:
                    print("Error: Invalid message format.")
            else:
                print("Error: Missing message.")
        i += 1

def main():
    # Read the program file
    with open('repeat.simp', 'r') as file:
        program = file.read()
    # Interpret the program
    interpret_program(program)

if __name__ == "__main__":
    main()
