/* LOGGING.hpp
 *   by Lut99
 *
 * Created:
 *   09 Aug 2023, 11:43:56
 * Last edited:
 *   09 Aug 2023, 13:45:06
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Defines a few macros to synchronize logging.
**/

#ifndef BSCRIPT_LOGGING_HPP
#define BSCRIPT_LOGGING_HPP

#include <chrono>
#include <ctime>
#include <iomanip>
#include <iostream>


/***** LIBRARY *****/
#define LOG_DEBUG(MESSAGE) \
    std::cout << "[D " << Now() << " BraneScript] " << MESSAGE << std::endl
#define LOG_INFO(MESSAGE) \
    std::cout << "[I " << Now() << " BraneScript] " << MESSAGE << std::endl
#define LOG_WARN(MESSAGE) \
    std::cout << "[W " << Now() << " BraneScript] " << MESSAGE << std::endl
#define LOG_ERROR(MESSAGE) \
    std::cout << "[E " << Now() << " BraneScript] " << MESSAGE << std::endl



/* Dummy struct to trigger our operator. */
struct Now {};
/* Defines the operator for streaming. */
std::ostream& operator<<(std::ostream& os, const Now& _now) {
    // Compute the current time string with everything except the milliseconds
    std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
    std::time_t current_time = std::chrono::system_clock::to_time_t(now);
    std::chrono::milliseconds now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch());
    struct tm current_local_time;
    localtime_r(&current_time, &current_local_time);
    char buffer[80];
    std::size_t char_count { std::strftime(buffer, 80, "%Y-%m-%d %H:%M:%S", &current_local_time) };
    if (char_count == 0) { throw std::runtime_error("Failed to format time"); }

    // Now write it + the milliseconds
    os << buffer << "." << std::setfill('0') << std::setw(3) << (now_ms.count() % 1000);

    // Done!
    return os;
}


#endif
