/* MAIN.cpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 16:07:51
 * Last edited:
 *   10 Jul 2023, 09:56:42
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Entrypoint for the custom Jupyter kernel for BraneScript.
 *   
 *   Based on: https://xeus.readthedocs.io/en/latest/kernel_implementation.html
**/

#include <iostream>
#include "brane/brane_cli.h"

using namespace std;


/***** ENTRYPOINT *****/
int main(int argc, char* argv[]) {
    // REad the input
    if (argc < 4) { cerr << "Usage: " << argv[0] << " <LIBBRANE_TSK_SO_PATH> <BRANE_API_ADDRESS> <BRANE_DRV_ADDRESS>"; return 1; }
    const char* so_path     = argv[1];
    const char* api_address = argv[2];
    const char* drv_address = argv[3];

    // Define a piece of BraneScript source code to test
    const char* source = "println(\"Hello, world!\");";
    
    // Load the functions in the .so file
    Functions* functions = functions_load(so_path);
    if (functions == nullptr) { return 1; }

    // Load the indices
    PackageIndex* pindex;
    Error* err = functions->pindex_new_remote(api_address, &pindex);
    if (err != nullptr) {
        functions->error_print_err(err);
        functions->error_free(err);
        return 1;
    }
    DataIndex* dindex;
    err = functions->dindex_new_remote(api_address, &dindex);
    if (err != nullptr) {
        functions->pindex_free(pindex);
        functions->error_print_err(err);
        functions->error_free(err);
        return 1;
    }

    // Create the compiler
    Compiler* compiler;
    err = functions->compiler_new(pindex, dindex, &compiler);
    if (err != nullptr) {
        functions->dindex_free(dindex);
        functions->pindex_free(pindex);
        functions->error_print_err(err);
        functions->error_free(err);
        return 1;
    }

    // Create the virtual machine
    VirtualMachine* vm;
    err = functions->vm_new(drv_address, pindex, dindex, &vm);
    if (err != nullptr) {
        functions->compiler_free(compiler);
        functions->dindex_free(dindex);
        functions->pindex_free(pindex);
        functions->error_print_err(err);
        functions->error_free(err);
        return 1;
    }
    // Free the indices since their counted pointer is taken by the compiler and VM
    functions->dindex_free(dindex);
    functions->pindex_free(pindex);

    // Attempt to compile with it
    Workflow* workflow;
    SourceError* serr = functions->compiler_compile(compiler, "<buildin>", source, &workflow);
    functions->serror_print_swarns(serr);
    functions->serror_print_serrs(serr);
    functions->serror_print_err(serr);
    bool should_exit = functions->serror_has_serrs(serr) || functions->serror_has_err(serr);
    functions->serror_free(serr);
    if (should_exit) {
        cout << "k bye" << endl;
        functions->vm_free(vm);
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
        functions->vm_free(vm);
        functions->compiler_free(compiler);
        functions_unload(functions);
        return 1;
    }
    cout << disas << endl;

    // Run the workflow on the VM
    FullValue* result;
    err = functions->vm_run(vm, workflow, &result);
    if (err != nullptr) {
        functions->error_print_err(err);
        functions->error_free(err);
        functions->workflow_free(workflow);
        functions->vm_free(vm);
        functions->compiler_free(compiler);
        functions_unload(functions);
        return 1;
    }

    // Free everything up and we're done
    functions->fvalue_free(result);
    free(disas);
    functions->workflow_free(workflow);
    functions->vm_free(vm);
    functions->compiler_free(compiler);
    functions_unload(functions);
}
