#include <stdio.h>
#include <stdbool.h>

int func(int a, int b) {
    int _t1 = a + b;
    int c = _t1;
    return c;
}

int main() {
    int _t2 = func(1, 2);
    int d = _t2;
    printf("%d\n", d);
    int _t3 = func(1, 5);
    printf("%d\n", _t3);
    return 0;
}
