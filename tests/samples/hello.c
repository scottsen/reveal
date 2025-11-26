#include <stdio.h>
#include <stdlib.h>

// Simple hello world in C
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <name>\n", argv[0]);
        return 1;
    }

    printf("Hello, %s!\n", argv[1]);
    return 0;
}

void greet(const char *name) {
    printf("Greetings, %s!\n", name);
}
