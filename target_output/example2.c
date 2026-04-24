#include <stdio.h>
#include <stdbool.h>

int main() {
    int age = 18;
    int change = 0;
    bool _t1 = age >= 18;
    bool _t2 = age < 35;
    if (_t1 && _t2) {
        change = 1;
        printf("%d\n", 1);
        if (1) {
            change = 2;
            printf("%d\n", 2);
        }
    } else {
        if (age < 2) {
            change = 3;
            printf("%d\n", 3);
        } else {
            if (age < 5) {
                change = 5;
                printf("%d\n", 5);
            } else {
                change = 1000;
                printf("%d\n", 1000);
            }
        }
    }
    return 0;
}
