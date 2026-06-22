#include <iostream>
#include <fstream>
#include <filesystem>
#include <thread>
#include <chrono>
#include <string>
#include <vector>
#include <algorithm>
#include <zmq.hpp>

namespace fs = std::filesystem;

const std::string INPUT_DIR = "../data_input";

// Simple utility to clean and tokenize text to lowercase
void clean_and_process_text(std::string& raw_text) {
    // 1. Convert to lowercase
    auto convert_to_lowercase = [](unsigned char c) { return std::tolower(c); };
    std::transform(raw_text.begin(), raw_text.end(), raw_text.begin(), convert_to_lowercase);
    
    // 2. Strip basic punctuation (Simulating high-speed parsing)
    auto is_punct = [](unsigned char c) { return std::ispunct(c); };
    raw_text.erase(
        std::remove_if(raw_text.begin(), raw_text.end(), is_punct),
        raw_text.end());
}

void parse_json_headline(const fs::path& file_path, zmq::socket_t& publisher) {
    std::ifstream file(file_path);
    if (!file.is_open()) return;

    std::string line;
    std::string headline = "";

    // A lightweight, raw-string parser to extract the "headline" without heavy external library overhead
    while (std::getline(file, line)) {
        size_t pos = line.find("\"headline\":");
        if (pos != std::string::npos) {
            // Extract text between quotes after "headline":
            size_t start_quote = line.find("\"", pos + 11);
            size_t end_quote = line.find("\"", start_quote + 1);
            if (start_quote != std::string::npos && end_quote != std::string::npos) {
                headline = line.substr(start_quote + 1, end_quote - start_quote - 1);
            }
        }
    }
    file.close();

    if (!headline.empty()) {
        std::cout << "[C++ Core] Ingested raw file: " << file_path.filename() << "\n";
        clean_and_process_text(headline);
        std::cout << "[C++ Core] Cleaned Payload: \"" << headline << "\"\n\n";

        // Publish the cleaned headline to ZeroMQ
        zmq::message_t message(headline.size());
        memcpy(message.data(), headline.data(), headline.size());
        publisher.send(message, zmq::send_flags::none);
    }
}

zmq::socket_t initialize_zero_mq(zmq::context_t& context) {
    zmq::socket_t publisher_socket(context, zmq::socket_type::pub);
    publisher_socket.bind("tcp://*:5555"); // Listen on port 5555
    return publisher_socket;
}

int main() {
    std::cout << "=== VeloRAG C++ Core Engine Active ===" << std::endl;
    // Ensure directory exists
    if (!fs::exists(INPUT_DIR)) {
        std::cerr << "Error: Input directory does not exist: " << INPUT_DIR << std::endl;
        return 1;
    }

    std::cout << "Monitoring directory: " << INPUT_DIR << std::endl;

    // Initialize ZeroMQ context and publisher socket
    zmq::context_t context(1);
    zmq::socket_t publisher = initialize_zero_mq(context);
    std::cout << "ZeroMQ Publisher bound to tcp://*:5555" << std::endl;

    try {
        while (true) {
            // Scan directory for files
            for (const auto& entry : fs::directory_iterator(INPUT_DIR)) {
                // Ignore temporary hidden writing files from Python script
                if (entry.is_regular_file() && entry.path().extension() == ".json" && 
                    entry.path().filename().string().find(".tmp_") != 0) {
                    
                    parse_json_headline(entry.path(), publisher);
                    
                    // Instantly clean up the disk boundary to maintain high throughput
                    fs::remove(entry.path());
                }
            }
            // Sleep briefly to prevent pinning a full CPU core to 100% during execution loops
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    } catch (const std::exception& e) {
        std::cerr << "Engine Exception encountered: " << e.what() << std::endl;
    }

    return 0;
}