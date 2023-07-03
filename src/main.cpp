/* MAIN.cpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 16:07:51
 * Last edited:
 *   03 Jul 2023, 14:10:03
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
    // REad the input
    if (argc < 3) { cerr << "Usage: " << argv[0] << " <LIBBRANE_TSK_SO_PATH> <BRANE_API_ADDRESS>"; return 1; }
    const char* so_path     = argv[1];
    const char* api_address = argv[2];

    // Define a piece of BraneScript source code to test
    const char* source = "println(\"Hello, world!\");";
    
    // Load the functions in the .so file
    Functions* functions = functions_load(so_path);
    if (functions == nullptr) { return 1; }

    // Create the compiler
    Compiler* compiler;
    Error* err = functions->compiler_new(api_address, &compiler);
    if (err != nullptr) {
        functions->error_print_err(err);
        functions->error_free(err);
        return 1;
    }

    // Attempt to compile with it
    Workflow* workflow;
    SourceError* serr = functions->compiler_compile(compiler, source, &workflow);
    functions->serror_print_swarns(serr, "<hardcoded>", source);
    functions->serror_print_serrs(serr, "<hardcoded>", source);
    functions->serror_print_err(serr);
    bool should_exit = functions->serror_has_serrs(serr) || functions->serror_has_err(serr);
    functions->serror_free(serr);
    if (should_exit) {
        cout << "k bye" << endl;
        functions->compiler_free(compiler);
        functions_unload(functions);
        return 1;
    }

    // Print the disassembled version of the workflow
    char* disas;
    cout << "A" << endl;
    err = functions->workflow_disassemble(workflow, &disas);
    cout << "B" << endl;
    if (err != nullptr) {
        functions->error_print_err(err);
        functions->error_free(err);
        functions->workflow_free(workflow);
        functions->compiler_free(compiler);
        functions_unload(functions);
        return 1;
    }
    cout << disas << endl;

    // Free everything up and we're done
    free(disas);
    functions->workflow_free(workflow);
    functions->compiler_free(compiler);
    functions_unload(functions);
}
