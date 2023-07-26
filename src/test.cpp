/* TEST.cpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 16:07:51
 * Last edited:
 *   26 Jul 2023, 12:43:13
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Test file for developing the libbrane_cli.so library.
**/

#include <iostream>
#include "brane/brane_cli.h"

using namespace std;


/***** ENTRYPOINT *****/
int main(int argc, char* argv[]) {
    // REad the input
    if (argc < 5) { cerr << "Usage: " << argv[0] << " <LIBBRANE_TSK_SO_PATH> <BRANE_API_ADDRESS> <BRANE_DRV_ADDRESS> <CERTS_DIR> <DATA_DIR>\n"; return 1; }
    const char* so_path     = argv[1];
    const char* api_address = argv[2];
    const char* drv_address = argv[3];
    const char* certs_dir   = argv[4];
    const char* data_dir    = argv[5];

    // Define a piece of BraneScript source code to test
    // const char* source = "println(\"Hello, world!\");";
    const char* source = "import data_init; on \"test\" { let res := zeroes(16, \"vector\"); return commit_result(\"test_result\", res); }";
    
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
    err = functions->vm_new(api_address, drv_address, certs_dir, pindex, dindex, &vm);
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
    err = functions->workflow_disassemble(workflow, &disas);
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
    free(disas);

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

    // Process the result if necessary
    if (functions->fvalue_needs_processing(result)) {
        // Call the process function
        err = functions->vm_process(vm, result, data_dir);
        if (err != nullptr) {
            functions->error_print_err(err);
            functions->error_free(err);
            functions->fvalue_free(result);
            functions->workflow_free(workflow);
            functions->vm_free(vm);
            functions->compiler_free(compiler);
            functions_unload(functions);
            return 1;
        }
    }

    // Free everything up and we're done
    functions->fvalue_free(result);
    functions->workflow_free(workflow);
    functions->vm_free(vm);
    functions->compiler_free(compiler);
    functions_unload(functions);
}
