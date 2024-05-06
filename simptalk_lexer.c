#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

// Token types
typedef enum {
    TOKEN_EOF,
    TOKEN_NUMBER,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_MULTIPLY,
    TOKEN_DIVIDE,
    TOKEN_LPAREN,
    TOKEN_RPAREN
} TokenType;

// Token structure
typedef struct {
    TokenType type;
    int value;
} Token;

// Global variables
char *input;
Token current_token;
int current_position = 0;

// Function prototypes
void advance();
Token get_next_token();

// Lexer function
void lexer(char *text) {
    input = text;
    advance();
}

// Advance to the next character in the input
void advance() {
    current_position++;
}

// Get the next token from the input
Token get_next_token() {
    char current_char;

    // Skip whitespace
    while ((current_char = input[current_position]) != '\0' && isspace(current_char)) {
        advance();
    }

    if (current_char == '\0') {
        return (Token){TOKEN_EOF, 0};
    }

    // Parse numbers
    if (isdigit(current_char)) {
        int value = 0;
        while (isdigit(input[current_position])) {
            value = value * 10 + (input[current_position] - '0');
            advance();
        }
        return (Token){TOKEN_NUMBER, value};
    }

    // Parse operators and parentheses
    switch (current_char) {
        case '+': advance(); return (Token){TOKEN_PLUS, 0};
        case '-': advance(); return (Token){TOKEN_MINUS, 0};
        case '*': advance(); return (Token){TOKEN_MULTIPLY, 0};
        case '/': advance(); return (Token){TOKEN_DIVIDE, 0};
        case '(': advance(); return (Token){TOKEN_LPAREN, 0};
        case ')': advance(); return (Token){TOKEN_RPAREN, 0};
        default:
            printf("Invalid character: %c\n", current_char);
            exit(1);
    }
}

int main() {
    // Example input
    char *input = "3 + 4 * (2 - 1)";

    // Tokenize the input
    lexer(input);

    // Print tokens
    current_token = get_next_token();
    while (current_token.type != TOKEN_EOF) {
        switch (current_token.type) {
            case TOKEN_NUMBER: printf("Number(%d)\n", current_token.value); break;
            case TOKEN_PLUS: printf("Plus\n"); break;
            case TOKEN_MINUS: printf("Minus\n"); break;
            case TOKEN_MULTIPLY: printf("Multiply\n"); break;
            case TOKEN_DIVIDE: printf("Divide\n"); break;
            case TOKEN_LPAREN: printf("Left Parenthesis\n"); break;
            case TOKEN_RPAREN: printf("Right Parenthesis\n"); break;
        }
        current_token = get_next_token();
    }

    return 0;
}
/*This program is a simple lexer for a fictional programming language called Simptalk. The lexer reads an input string containing a basic arithmetic expression and tokenizes it into individual tokens. The tokens include numbers, arithmetic operators (+, -, *, /), and parentheses. The lexer skips whitespace characters and identifies invalid characters, such as letters or special characters not supported by the language.

The program demonstrates the basic principles of lexical analysis, which is the process of converting a sequence of characters into a sequence of tokens. Lexical analysis is an essential first step in the compilation process of a programming language.

To use the program, you can provide an arithmetic expression as input, such as "3 + 4 * (2 - 1)", and the lexer will tokenize it and print out the tokens, indicating the type of each token (e.g., Number, Plus, Minus, Multiply, Divide, Left Parenthesis, Right Parenthesis).*/





