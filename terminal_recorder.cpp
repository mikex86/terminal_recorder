#include <iostream>
#include <unistd.h>
#include <pty.h>
#include <termios.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <poll.h>
#include <fstream>
#include <chrono>
#include <sys/ioctl.h>
#include <cstring>

// Data type constants
const uint8_t DATA_TYPE_SIZE_CHANGE = 0;
const uint8_t DATA_TYPE_STDIN = 1;
const uint8_t DATA_TYPE_STDOUT = 2;

struct terminal_size_t {
    uint16_t rows;
    uint16_t cols;
};

void write_to_log(std::ofstream &log_file, uint8_t data_type, const char *buf, ssize_t len) {
    auto now = std::chrono::steady_clock::now().time_since_epoch();
    auto time_ms = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();

    log_file.write(reinterpret_cast<const char *>(&data_type), sizeof(data_type));
    log_file.write(reinterpret_cast<const char *>(&time_ms), sizeof(time_ms));
    log_file.write(reinterpret_cast<const char *>(&len), sizeof(len));
    log_file.write(buf, len);
    log_file.flush();
}

bool is_terminal_size_equal(const terminal_size_t &a, const terminal_size_t &b) {
    return a.rows == b.rows && a.cols == b.cols;
}

void check_and_log_terminal_size(int master_fd, std::ofstream &log_file, terminal_size_t &prev_terminal_size) {
    struct winsize ws{};
    ioctl(master_fd, TIOCGWINSZ, &ws);

    terminal_size_t current_terminal_size = {static_cast<uint16_t>(ws.ws_row), static_cast<uint16_t>(ws.ws_col)};
    if (!is_terminal_size_equal(current_terminal_size, prev_terminal_size)) {
        prev_terminal_size = current_terminal_size;
        write_to_log(log_file, DATA_TYPE_SIZE_CHANGE, reinterpret_cast<const char *>(&current_terminal_size),
                     sizeof(current_terminal_size));
    }
}

int main(int argc, char **argv) {
    int master_fd;
    std::ofstream log_file("terminal_log.bin", std::ios::binary);

    // Get the terminal size of the parent process
    struct winsize parent_ws{};
    ioctl(STDIN_FILENO, TIOCGWINSZ, &parent_ws);

    pid_t pid = forkpty(&master_fd, nullptr, nullptr, nullptr);
    if (pid == -1) {
        perror("forkpty");
        return 1;
    }

    if (pid == 0) { // Child process
        // Set the terminal size of the child process
        ioctl(STDIN_FILENO, TIOCSWINSZ, &parent_ws);

        execv("/bin/bash", argv);
        perror("execv");
        return 1;
    }
    // Parent process

    // Set the terminal to raw mode
    struct termios orig_term_settings{}, raw_term_settings{};
    tcgetattr(STDIN_FILENO, &orig_term_settings);
    raw_term_settings = orig_term_settings;
    tcgetattr(STDIN_FILENO, &orig_term_settings);
raw_term_settings = orig_term_settings; 
raw_term_settings.c_lflag &= ~(ECHO | ICANON | IEXTEN | ISIG);
raw_term_settings.c_iflag &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON);
raw_term_settings.c_cflag &= ~(CSIZE | PARENB);
raw_term_settings.c_cflag |= CS8;
raw_term_settings.c_oflag &= ~(OPOST);
raw_term_settings.c_cc[VMIN] = 1;  
raw_term_settings.c_cc[VTIME] = 0;
tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw_term_settings);
    tcsetattr(STDIN_FILENO, TCSANOW, &raw_term_settings);

    // Use poll to multiplex input and output between user and shell
    struct pollfd fds[2];
    fds[0].fd = STDIN_FILENO;
    fds[0].events = POLLIN;
    fds[1].fd = master_fd;
    fds[1].events = POLLIN;

    terminal_size_t prev_terminal_size = {0, 0};

    while (true) {
        int ret = poll(fds, 2, -1);
        if (ret == -1) {
            perror("poll");
            break;
        }

        int status;
        pid_t result = waitpid(pid, &status, WNOHANG);
        if (result == pid) {
            break;
        } else if (result != 0) {
            // Error occurred
            perror("waitpid failed");
            break;
        }

        check_and_log_terminal_size(master_fd, log_file, prev_terminal_size);

        if (fds[0].revents & POLLIN) {
            char buf[4096];
            ssize_t len = read(STDIN_FILENO, buf, sizeof(buf));
            if (len <= 0) break;
            write(master_fd, buf, len);
            write_to_log(log_file, DATA_TYPE_STDIN, buf, len);
        }

        if (fds[1].revents & POLLIN) {
            char buf[4096];
            ssize_t len = read(master_fd, buf, sizeof(buf));
            if (len <= 0) break;
            write(STDOUT_FILENO, buf, len);
            write_to_log(log_file, DATA_TYPE_STDOUT, buf, len);
        }
    }

    // Restore the terminal settings
    tcsetattr(STDIN_FILENO, TCSANOW, &orig_term_settings);

    // Close the master fd and wait for the child process
    close(master_fd);
    waitpid(pid, nullptr, 0);

    return 0;
}
