#include <stdio.h>
#include <stdbool.h>

int main() {
    int integer_var = 9;
    bool boolean_var = true;
    int _t1 = -10;
    int unary_op_var = _t1;
    int _t2 = -10;
    int _t3 = _t2 + 3;
    int binary_op_var = _t3;
    int _t4 = integer_var * 19;
    int complex_op_var = _t4;
    bool _t5 = true && false;
    bool _t6 = _t5 || false;
    bool bool2 = _t6;
    printf("%d\n", integer_var);
    if (boolean_var) printf("True\n"); else printf("False\n");
    printf("%d\n", unary_op_var);
    printf("%d\n", binary_op_var);
    printf("%d\n", complex_op_var);
    if (bool2) printf("True\n"); else printf("False\n");
    return 0;
}
