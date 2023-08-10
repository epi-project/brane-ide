/* TEST KERNEL.cpp
 *   by Lut99
 *
 * Created:
 *   10 Aug 2023, 13:07:51
 * Last edited:
 *   10 Aug 2023, 13:30:56
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Entrypoint that can test some of the functions more standalone.
**/

#include <iostream>

#include "custom_interpreter.hpp"

using namespace std;


/***** ENTRYPOINT *****/
int main() {
    // Run the execute request with fake data
    bscript::custom_interpreter interpreter;

    // Start it
    interpreter.configure_impl();

    // Run a fake snippet
    nl::json res = interpreter.execute_request_impl(0, "test", false, true, {}, false);
    cout << res << endl;

    // Done
    interpreter.shutdown_request_impl();

    // Jepjepjep
    return 0;
}
