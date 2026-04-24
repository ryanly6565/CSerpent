#include <stdio.h>
#include <stdbool.h>

int main() {
    int x = 5;
    for (int i = 1; i < x; i = i + 5) {
        printf("%d\n", i);
    }
    for (int i = 0; i < 5; i = i + 1) {
        printf("%d\n", i);
    }
    for (int i = 0; i < 10; i = i + 1) {
        printf("%d\n", i);
    }
    for (int i = 0; i < 10; i = i + 2) {
        printf("%d\n", i);
    }
    return 0;
}
