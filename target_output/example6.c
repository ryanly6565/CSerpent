#include <stdio.h>
#include <stdbool.h>

int func(int a, int b) {
    int _t1 = a + b;
    int c = _t1;
    for (int i = 0; i < 3; i = i + 1) {
        if (i == 1) {
            if (true) printf("True\n"); else printf("False\n");
        }
    }
    return c;
}

int main() {
    int _t2 = func(1, 2);
    printf("%d\n", _t2);
    return 0;
}
