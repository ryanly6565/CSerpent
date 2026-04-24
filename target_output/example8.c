#include <stdio.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdbool.h>

#include <string.h>
#include <stdlib.h>

typedef struct python_list_element_t {
	int type;
	void *value;
} python_list_element;

typedef struct python_list_t {
	int size;
	struct python_list_element_t *buffer;
    int refcount;
} python_list;

python_list * python_list_new() {
    python_list *lst = malloc(sizeof(python_list));
    
    lst->refcount = 1;
    lst->size = 0;
    lst->buffer = NULL;
    
    return lst;
}

int python_list_value_compare(python_list *lst1, python_list *lst2) {
    if (lst1->size != lst2->size) {
        return 0;
    }

    for (int i = 0; i < lst1->size; i++) {
        python_list_element e1 = lst1->buffer[i];
        python_list_element e2 = lst2->buffer[i];

        if (e1.type != e2.type) {
            return 0;
        }

        if (e1.type == 0) {  // int
            if ((int)(long)e1.value != (int)(long)e2.value) {
                return 0;
            }
        }
        else if (e1.type == 1) {  // bool
            if ((bool)(long)e1.value != (bool)(long)e2.value) {
                return 0;
            }
        }
        else if (e1.type == 2) {  // nested list
            python_list *sub1 = (python_list*)e1.value;
            python_list *sub2 = (python_list*)e2.value;

            if (!python_list_value_compare(sub1, sub2)) {
                return 0;
            }
        }
    }

    return 1;
}

char *python_list_to_string(python_list *lst) {
    int capacity = 1024;
    int length = 0;

    char *result = malloc(capacity);
    
    result[length++] = '[';
    result[length] = '\0';

    for (int i = 0; i < lst->size; i++) {
        python_list_element e = lst->buffer[i];
        char temp[256];

        if (e.type == 0) {  // int
            snprintf(temp, sizeof(temp), "%d", (int)(long)e.value);
        }
        else if (e.type == 1) {  // bool
            snprintf(temp, sizeof(temp), "%s", (bool)(long)e.value ? "True" : "False");
        }
        else if (e.type == 2) {  // nested list
            char *sub = python_list_to_string((python_list *)e.value);
            snprintf(temp, sizeof(temp), "%s", sub);
            free(sub);
        }

        int needed = strlen(temp) + 3;
        if (length + needed >= capacity) {
            capacity *= 2;
            result = realloc(result, capacity);
    
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
        result = realloc(result, capacity);
    
    }

    result[length++] = ']';
    result[length] = '\0';

    return result;
}

void python_list_retain(python_list *lst) {
    if (lst) lst->refcount++;
}

void python_list_release(python_list *lst) {
    if (!lst) return;

    lst->refcount--;

    if (lst->refcount == 0) {
        for (int i = 0; i < lst->size; i++) {
            python_list_element *e = &lst->buffer[i];

            if (e->type == 2) { // nested list
                python_list_release((python_list *)e->value);
            }
        }

        free(lst->buffer);
        free(lst);
    }
}

void python_list_append(python_list *python_lst, int type, void *value) {
	python_list_element *new_array = malloc(sizeof(python_list_element) * (python_lst->size + 1));
    
	memcpy(new_array, python_lst->buffer, sizeof(python_list_element) * python_lst->size);
	
	python_list_element new_elem; 
	new_elem.type = type;
	new_elem.value = value;

    if (type == 2) {
        python_list_retain((python_list *)value);
    }

	new_array[python_lst->size] = new_elem;

	// memory management
	free(python_lst->buffer);
	python_lst->buffer = new_array;	
	python_lst->size += 1;
}

void python_list_remove(python_list *python_lst, int type, void *value) {
        int found_index = -1;
        for (int i = 0; i < python_lst->size; i++) {
                python_list_element *curr_element = &python_lst->buffer[i];

				// in python, True == 1 and False == 0 are true, so remove will remove them, we emulate this behavior
				if (type + curr_element->type == 1) {
					if (type == 1) {
						if ((bool)(long)value && (int)(long)curr_element->value == 1) {
							found_index = i;
							break;
						}
						else if (((bool)(long)value == 0) && ((int)(long)curr_element->value == 0)) {
							found_index = i;
							break;
						}
					}
				}
                else if (type == 0 && curr_element->type == 0) {
                    if ((int)(long)curr_element->value == (int)(long)value) {
                        found_index = i;
                        break;
                    }
                }
                else if (type == 1 && curr_element->type == 1) {
                    if ((bool)(long)curr_element->value == (bool)(long)value) {
                        found_index = i;
                        break;
                    }
                }
				else {
                    if (curr_element->type == 2 && type == 2 &&
                        python_list_value_compare((python_list *)curr_element->value,
                                                (python_list *)value)) {
                        found_index = i;
                        break;
                    }
				}
        }

        if (found_index == -1) {
                exit(EXIT_FAILURE);
        }

        python_list_element *removed = &python_lst->buffer[found_index];
        if (removed->type == 2) {
            python_list_release((python_list *)removed->value);
        }

        python_list_element *new_array = (python_list_element*)malloc(sizeof(python_list_element) * (python_lst->size - 1));
        
        memcpy(new_array, python_lst->buffer, sizeof(python_list_element) * found_index);
        memcpy(new_array + found_index, (python_lst->buffer) + found_index + 1, sizeof(python_list_element) * (python_lst->size - found_index - 1));
        free(python_lst->buffer);
        python_lst->size--;
        python_lst->buffer = new_array;
}

// ownership belongs to the user of this function
python_list_element python_list_pop(python_list *python_lst, int index) {
        if (index >= python_lst->size) {
                exit(EXIT_FAILURE);
        }

	python_list_element element = python_lst->buffer[index];

        python_list_element *new_array = (python_list_element*)malloc(sizeof(python_list_element) * (python_lst->size - 1));
    
        memcpy(new_array, python_lst->buffer, sizeof(python_list_element) * index);
        memcpy(new_array + index, (python_lst->buffer) + index + 1, sizeof(python_list_element) * (python_lst->size - index - 1));
        free(python_lst->buffer);
        python_lst->size--;
        python_lst->buffer = new_array;

	return element;
}


int main() {
    python_list * _t1 = python_list_new();
    python_list * lst = _t1;
    python_list_retain(lst);
    for (int i = 0; i < 100000; i = i + 1) {
        python_list_append(lst, 0, (void*)(long) i);
    }
    python_list_release(lst);
    return 0;
}
