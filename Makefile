CC = gcc
CFLAGS = -Wall -Wno-unused-variable -Wno-unused-but-set-variable -Wextra -std=c11

SRC_DIR = target_output
SRCS = $(wildcard $(SRC_DIR)/*.c)
BINS = $(SRCS:.c=)

all: $(BINS)

$(SRC_DIR)/%: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(BINS)
