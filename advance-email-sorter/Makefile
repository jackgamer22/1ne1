CC = gcc
CFLAGS = -Wall -Wextra -pthread
TARGET = email_sorter

all: $(TARGET)

$(TARGET): main.c
	$(CC) $(CFLAGS) -o $(TARGET) main.c

clean:
	rm -f $(TARGET)
