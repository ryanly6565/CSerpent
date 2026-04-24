#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

typedef struct python_list_element_t {
    int type;   // 0 = int, 1 = bool, 2 = list
    void *value;
} python_list_element;

typedef struct python_list_t {
    int size;
    int capacity;
    python_list_element *buffer;
    int refcount;
} python_list;

python_list * python_list_new() {
    python_list *lst = malloc(sizeof(python_list));
    if (!lst) exit(EXIT_FAILURE);

    lst->size = 0;
    lst->capacity = 8;
    lst->buffer = malloc(sizeof(python_list_element) * lst->capacity);
    if (!lst->buffer) exit(EXIT_FAILURE);

    lst->refcount = 1;
    return lst;
}

void python_list_retain(python_list *lst) {
    if (lst) lst->refcount++;
}

void python_list_release(python_list *lst) {
    if (!lst) return;

    lst->refcount--;

    if (lst->refcount == 0) {
        for (int i = 0; i < lst->size; i++) {
            if (lst->buffer[i].type == 2) {
                python_list_release((python_list *)lst->buffer[i].value);
            }
        }
        free(lst->buffer);
        free(lst);
    }
}

int python_list_value_compare(python_list *lst1, python_list *lst2) {
    if (lst1->size != lst2->size) return 0;

    for (int i = 0; i < lst1->size; i++) {
        python_list_element e1 = lst1->buffer[i];
        python_list_element e2 = lst2->buffer[i];

        if (e1.type != e2.type) return 0;

        if (e1.type == 0) {
            if ((int)(long)e1.value != (int)(long)e2.value) return 0;
        }
        else if (e1.type == 1) {
            if ((bool)(long)e1.value != (bool)(long)e2.value) return 0;
        }
        else if (e1.type == 2) {
            if (!python_list_value_compare(
                    (python_list *)e1.value,
                    (python_list *)e2.value)) return 0;
        }
    }
    return 1;
}

void python_list_append(python_list *lst, int type, void *value) {
    if (lst->size >= lst->capacity) {
        int new_capacity = lst->capacity * 2;
        python_list_element *tmp =
            realloc(lst->buffer, sizeof(python_list_element) * new_capacity);
        if (!tmp) exit(EXIT_FAILURE);

        lst->buffer = tmp;
        lst->capacity = new_capacity;
    }

    if (type == 2) {
        python_list_retain((python_list *)value);
    }

    lst->buffer[lst->size++] = (python_list_element){type, value};
}

void python_list_remove(python_list *lst, int type, void *value) {
    int found = -1;

    for (int i = 0; i < lst->size; i++) {
        python_list_element *e = &lst->buffer[i];

        // bool/int equivalence
        if ((type == 0 && e->type == 1) || (type == 1 && e->type == 0)) {
            if ((int)(long)value == (int)(long)e->value) {
                found = i;
                break;
            }
        }
        else if (type == 0 && e->type == 0) {
            if ((int)(long)e->value == (int)(long)value) {
                found = i;
                break;
            }
        }
        else if (type == 1 && e->type == 1) {
            if ((bool)(long)e->value == (bool)(long)value) {
                found = i;
                break;
            }
        }
        else if (type == 2 && e->type == 2) {
            if (python_list_value_compare(
                    (python_list *)e->value,
                    (python_list *)value)) {
                found = i;
                break;
            }
        }
    }

    if (found == -1) exit(EXIT_FAILURE);

    if (lst->buffer[found].type == 2) {
        python_list_release((python_list *)lst->buffer[found].value);
    }

    for (int i = found; i < lst->size - 1; i++) {
        lst->buffer[i] = lst->buffer[i + 1];
    }

    lst->size--;

    if (lst->capacity > 8 && lst->size <= lst->capacity / 4) {
        int new_capacity = lst->capacity / 2;
        python_list_element *tmp =
            realloc(lst->buffer, sizeof(python_list_element) * new_capacity);
        if (tmp) {
            lst->buffer = tmp;
            lst->capacity = new_capacity;
        }
    }
}

python_list_element python_list_pop(python_list *lst, int index) {
    if (index < 0 || index >= lst->size) exit(EXIT_FAILURE);

    python_list_element elem = lst->buffer[index];

    for (int i = index; i < lst->size - 1; i++) {
        lst->buffer[i] = lst->buffer[i + 1];
    }

    lst->size--;

    if (lst->capacity > 8 && lst->size <= lst->capacity / 4) {
        int new_capacity = lst->capacity / 2;
        python_list_element *tmp =
            realloc(lst->buffer, sizeof(python_list_element) * new_capacity);
        if (tmp) {
            lst->buffer = tmp;
            lst->capacity = new_capacity;
        }
    }

    return elem; // caller owns if type == 2
}

char *python_list_to_string(python_list *lst) {
    int capacity = 1024;
    int length = 0;

    char *result = malloc(capacity);
    if (!result) exit(EXIT_FAILURE);

    result[length++] = '[';
    result[length] = '\0';

    for (int i = 0; i < lst->size; i++) {
        python_list_element e = lst->buffer[i];
        char temp[256];

        if (e.type == 0) {
            snprintf(temp, sizeof(temp), "%d", (int)(long)e.value);
        }
        else if (e.type == 1) {
            snprintf(temp, sizeof(temp), "%s",
                     (bool)(long)e.value ? "True" : "False");
        }
        else {
            char *sub = python_list_to_string((python_list *)e.value);
            snprintf(temp, sizeof(temp), "%s", sub);
            free(sub);
        }

        int needed = strlen(temp) + 3;
        if (length + needed >= capacity) {
            capacity *= 2;
            char *tmp = realloc(result, capacity);
            if (!tmp) {
                free(result);
                exit(EXIT_FAILURE);
            }
            result = tmp;
        }

        strcpy(result + length, temp);
        length += strlen(temp);

        if (i < lst->size - 1) {
            result[length++] = ',';
            result[length++] = ' ';
            result[length] = '\0';
        }
    }

    if (length + 2 >= capacity) {
        capacity += 2;
        char *tmp = realloc(result, capacity);
        if (!tmp) {
            free(result);
            exit(EXIT_FAILURE);
        }
        result = tmp;
    }

    result[length++] = ']';
    result[length] = '\0';

    return result;
}