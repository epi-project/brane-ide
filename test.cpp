#include <iostream>
#include <memory>
#include <string>

#include "json.hpp"

using namespace std;
namespace nl = nlohmann;


int main() {
    char* buf = new char[13];
    strncpy(buf, "Hello there!\0", 13);
    std::string test(buf);
    nl::json test2;
    test2["test"] = test;
    delete[] buf;
    cout << test2["test"] << endl;
}
