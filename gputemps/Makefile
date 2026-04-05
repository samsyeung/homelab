CC      = gcc
CFLAGS  = -O3
LDFLAGS = -lnvidia-ml -lpci
TARGET  = gputemps

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) $< -o $@ $(LDFLAGS)

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: install clean
