/* MAIN.cpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 16:07:51
 * Last edited:
 *   29 Jun 2023, 11:51:04
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Entrypoint for the custom Jupyter kernel for BraneScript.
 *   
 *   Based on: https://xeus.readthedocs.io/en/latest/kernel_implementation.html
**/

#include <iostream>
#include "brane/brane_tsk.h"

using namespace std;


/***** ENTRYPOINT *****/
int main(int argc, char* argv[]) {
    // Define a piece of BraneScript source code to test
    const char* source = "println(\"Hello, world!\");";
    
    // Load the functions in the .so file
    const char* so_path = "/libbrane_tsk.so";
    Functions* functions = functions_load(so_path);
    if (functions == nullptr) { return 1; }

    // Create the compiler
    Compiler* compiler;
    Error* error = functions->compiler_new("http://145.109.125.145:50051", &compiler);
    if (error != nullptr) {
        functions->error_print_msg(error);
        functions->error_free(error);
        return 1;
    }

    // Attempt to compile with it
    char* json;
    error = functions->compiler_compile(compiler, source, &json);
    if (error != nullptr) {
        Error* err = functions->error_print_warns(error, "<hardcoded>", source);
        if (err != nullptr) { functions->error_print_msg(err); return 1; }
        functions->error_print_errs(error, "<hardcoded>", source);
        functions->error_print_msg(error);
        bool should_exit = functions->error_msg_occurred(error) || functions->error_err_occurred(error);
        functions->error_free(error);
        if (should_exit) { return 1; }
    }

    // Print the JSON
    cout << json << endl;

    // Free everything up and we're done
    free(json);
    functions->compiler_free(compiler);
    functions_unload(functions);
}
