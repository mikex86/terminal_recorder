CXX = g++
CXXFLAGS = -L/usr/local/lib -lutil
TARGET = terminal_recorder

# Build rules
all: $(TARGET)

$(TARGET): terminal_recorder.o
	$(CXX) -o $(TARGET) terminal_recorder.o $(CXXFLAGS)

terminal_recorder.o: terminal_recorder.cpp
	$(CXX) -c terminal_recorder.cpp

# Clean rule
clean:
	rm -f *.o $(TARGET)