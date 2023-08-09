/* CUSTOM INTERPRETER.cpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 17:39:03
 * Last edited:
 *   09 Aug 2023, 13:43:31
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Implements the custom interpreter for BraneScript.
 *   
 *   Based on: https://xeus.readthedocs.io/en/latest/kernel_implementation.html
**/

#include <string>
#include <unordered_map>
#include <iostream>
#include <xeus/xhelper.hpp>

#include "brane/brane_cli.h"
#include "logging.hpp"
#include "custom_interpreter.hpp"

using namespace std;
using namespace bscript;


/***** CONSTANTS *****/
/// The kernel version.
const static char* KERNEL_VERSION = "1.0.0";





/***** GLOBALS *****/
/* Whether we are in a usable state or not. */
bool errored = false;
/* The map of dynamically loaded compiler functions. */
Functions* brane_cli;





/***** HELPER CLASSES *****/
/* Collects everything we need to know per sesh. */
class Session {
public:
    /* The folder to download data to when it occurs. */
    string data_dir;

    /* The compiler with which we compile successive snippets. */
    Compiler* compiler;
    /* The VirtualMachine with which we execute successive snippets. */
    VirtualMachine* vm;

public:
    /* Constructor for the Session.
     * 
     * # Arguments
     * - `api_endpoint`: The Brane API endpoint to connect to.
     * - `drv_endpoint`: The Brane driver endpoint to connect to.
     * - `certs_dir`: Path to a folder with directories.
     * - `data_dir`: Path to a folder where we download datasets to, if any.
     * 
     * # Returns
     * A new Session object.
     */
    Session(const string& api_endpoint, const string& drv_endpoint, const string& certs_dir, const string& data_dir) :
        data_dir(data_dir)
    {
        // Load the package index for this sesh
        PackageIndex* pindex = nullptr;
        Error* err = brane_cli->pindex_new_remote(api_endpoint.c_str(), &pindex);
        if (err == nullptr) {
            brane_cli->error_print_err(err);
            brane_cli->error_free(err);
            throw string("Failed to get package index (see output above)");
        }

        // Load the data index for this sesh
        DataIndex* dindex = nullptr;
        err = brane_cli->dindex_new_remote(api_endpoint.c_str(), &dindex);
        if (err == nullptr) {
            brane_cli->error_print_err(err);
            brane_cli->error_free(err);
            brane_cli->pindex_free(pindex);
            throw string("Failed to get data index (see output above)");
        }

        // Load the compiler
        this->compiler = nullptr;
        err = brane_cli->compiler_new(pindex, dindex, &(this->compiler));
        if (err != nullptr) {
            brane_cli->error_print_err(err);
            brane_cli->error_free(err);
            brane_cli->dindex_free(dindex);
            brane_cli->pindex_free(pindex);
            throw string("Failed to create compiler (see output above)");
        }

        // Load the virtual machine representation
        this->vm = nullptr;
        err = brane_cli->vm_new(api_endpoint.c_str(), drv_endpoint.c_str(), certs_dir.c_str(), pindex, dindex, &(this->vm));
        if (err != nullptr) {
            brane_cli->error_print_err(err);
            brane_cli->error_free(err);
            brane_cli->compiler_free(this->compiler);
            brane_cli->dindex_free(dindex);
            brane_cli->pindex_free(pindex);
            throw string("Failed to create virtual machine (see output above)");
        }
    }

    /* Copy constructor for the Session, which is deleted. */
    Session(const Session& other) = delete;

    /* Move constructor for the Session.
     * 
     * # Arguments
     * - `other`: The other session to move.
     * 
     * # Returns
     * A new Session object.
     */
    Session(Session&& other) :
        data_dir(other.data_dir),

        compiler(other.compiler),
        vm(other.vm)
    {
        // Nullify fields that would other be invalidly deleted.
        other.compiler = nullptr;
        other.vm = nullptr;
    }

    /* Destructor for the Session. */
    ~Session() {
        // Free the internal VM, if any
        if (this->vm != nullptr) {
            brane_cli->vm_free(this->vm);
        }

        // Free the internal compiler, if any
        if (this->compiler != nullptr) {
            brane_cli->compiler_free(this->compiler);
        }
    }



    /* Copy assignment operator for the Session, which is deleted. */
    inline Session& operator=(const Session& other) = delete;

    /* Move assignment operator for the Session.
     * 
     * # Arguments
     * - `other`: The other Session to move.
     * 
     * # Returns
     * A reference to self for chaining.
     */
    inline Session& operator=(Session&& other) { if (this != &other) { swap(*this, other); } return *this; }

    /* Swap operator for the Session.
     * 
     * # Arguments
     * - `s1`: The one session to swap.
     * - `s2`: The other session to swap.
     */
    friend void swap(Session& s1, Session& s2);
};

/* Swap operator for the Session. */
void swap(Session& s1, Session& s2) {
    using std::swap;

    swap(s1.data_dir, s2.data_dir);

    swap(s1.compiler, s2.compiler);
    swap(s1.vm, s2.vm);
}





/***** MORE GLOBALS *****/
/* The global hashmap of sessions to running compilers. */
unordered_map<string, Session*> sessions;





/***** LIBRARY *****/
void custom_interpreter::configure_impl() {
    // Let's only log for now
    LOG_INFO("Initializing BraneScript kernel v" << KERNEL_VERSION << "...");

    // Try to read the location of libbrane
    const char* libbrane_path = std::getenv("LIBBRANE_PATH");
    if (libbrane_path == NULL) { cerr << "Environment variable 'LIBBRANE_PATH' not specified" << endl; exit(EXIT_FAILURE); }

    // Load the dynamic functions
    brane_cli = functions_load(libbrane_path);
    if (brane_cli == NULL) {
        // We cannot continue!
        cerr << "Failed to load '" << libbrane_path << "': " << dlerror() << endl;
        errored = true;
        return;
    }

    // Initialize the sessions map
    sessions = unordered_map<string, Session*>();

    // Done
    LOG_DEBUG("Initialization done.");
}

void custom_interpreter::shutdown_request_impl() {
    // Only do stuff if not errorred
    if (errored) { return; }
    LOG_INFO("Terminating BraneScript kernel...");

    // Clean the globals
    for (pair<string, Session*> p : sessions) {
        delete p.second;
    }
    sessions.clear();
    functions_unload(brane_cli);

    // Done
    LOG_DEBUG("Termination complete.");
}



nl::json custom_interpreter::execute_request_impl(int execution_counter, const std::string& code, bool silent, bool store_history, nl::json user_expressions, bool allow_stdin) {
    LOG_INFO("Handling execute request " << execution_counter);

    // Fetch the Rust code.
    /* TODO */

    // Just return some random stuff for now
    return xeus::create_error_reply("Hello_There", "123", {});
}

nl::json custom_interpreter::complete_request_impl(const std::string& code, int cursor_pos) {
    return xeus::create_complete_reply({}, 0, 0);
}

nl::json custom_interpreter::inspect_request_impl(const std::string& code, int cursor_pos, int detail_level) {
    return xeus::create_inspect_reply();
}

nl::json custom_interpreter::is_complete_request_impl(const std::string& code) {
    return xeus::create_is_complete_reply();
}

nl::json custom_interpreter::kernel_info_request_impl() {
    LOG_INFO("Handling kernel info request");
    return xeus::create_info_reply("", "bscript", brane_cli->version(), "BraneScript", "2.0.0", "application/brane-script", ".bs");
}
