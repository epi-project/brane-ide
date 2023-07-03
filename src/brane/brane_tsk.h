/* BRANE TSK.h
 *   by Lut99
 *
 * Created:
 *   14 Jun 2023, 11:49:07
 * Last edited:
 *   03 Jul 2023, 14:14:58
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Defines the headers of the `libbrane_tsk` library.
**/

#ifndef BRANE_TSK_H
#define BRANE_TSK_H

#include <stdlib.h>
#include <stdio.h>
#include <dlfcn.h>


/***** TYPES *****/
/* Defines the error type returned by the library.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _error Error;
/* Defines an alternative to the [`Error`]-type that can also encode source-related errors.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _source_error SourceError;

/* Defines a BraneScript AST, i.e., compiled source code.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _workflow Workflow;

/* Defines a BraneScript compiler.
 * 
 * Successive snippets can be compiled with the same compiler to retain state of what is already defined and what not.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _compiler Compiler;

// /* Defines a BRANE instance virtual machine.
//  * 
//  * This can run a compiled workflow on a running instance.
//  * 
//  * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
//  */
// typedef struct _virtual_machine VirtualMachine;



/* Defines a struct that can be used to conveniently initialize the function pointers in this library.
 */
struct _functions {
    /* The dlopen handle that we use to load stuff with. */
    void* handle;



    /***** LIBRARY FUNCTIONS *****/
    /* Returns the BRANE version for which this compiler is valid.
     * 
     * # Returns
     * String version that contains a major, minor and patch version separated by dots.
     */
    const char* (*version)();



    /***** ERROR *****/
    /* Destructor for the Error type.
     *
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     *
     * # Arguments
     * - `err`: The [`Error`] to deallocate.
     */
    void (*error_free)(Error* err);

    /* Prints the error message in this error to stderr.
     * 
     * # Arguments
     * - `err`: The [`Error`] to print.
     * 
     * # Panics
     * This function can panic if the given `err` is a NULL-pointer.
     */
    void (*error_print_err)(Error* err);



    /***** SOURCE ERROR *****/
    /* Destructor for the SourceError type.
     *
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     *
     * # Arguments
     * - `serr`: The [`SourceError`] to deallocate.
     */
    void (*serror_free)(SourceError* serr);

    /* Returns if a source warning has occurred.
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] struct to inspect.
     * 
     * # Returns
     * True if [`serr_print_swarns`] would print anything, or false otherwise.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    bool (*serror_has_swarns)(SourceError* serr);
    /* Returns if a source error has occurred.
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] struct to inspect.
     * 
     * # Returns
     * True if [`serr_print_serrs`] would print anything, or false otherwise.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    bool (*serror_has_serrs)(SourceError* serr);
    /* Returns if a program error has occurred.
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] struct to inspect.
     * 
     * # Returns
     * True if [`serr_print_err`] would print anything, or false otherwise.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    bool (*serror_has_err)(SourceError* serr);

    /* Prints the source warnings in this error to stderr.
     * 
     * Note that there may be zero or more warnings at once. To discover if there are any, check [`serror_has_swarns()`].
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] to print the source warnings of.
     * - `file`: Some string describing the source/filename of the source text.
     * - `source`: The physical source text, as parsed.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer, or if `file` or `source` do not point to valid UTF-8 strings.
     */
    void (*serror_print_swarns)(SourceError* serr, const char* file, const char* source);
    /* Prints the source errors in this error to stderr.
     * 
     * Note that there may be zero or more errors at once. To discover if there are any, check [`serror_has_serrs()`].
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] to print the source errors of.
     * - `file`: Some string describing the source/filename of the source text.
     * - `source`: The physical source text, as parsed.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer, or if `file` or `source` do not point to valid UTF-8 strings.
     */
    void (*serror_print_serrs)(SourceError* serr, const char* file, const char* source);
    /* Prints the error message in this error to stderr.
     * 
     * Note that there may be no error, but only source warnings- or errors. To discover if there is any, check [`serror_has_err()`].
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] to print the error of.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    void (*serror_print_err)(SourceError* serr);



    /***** WORKFLOW *****/
    /* Destructor for the Workflow.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `workflow`: The [`Workflow`] to free.
     */
    void (*workflow_free)(Workflow* workflow);

    /* Serializes the workflow by essentially disassembling it.
     * 
     * # Arguments
     * - `workflow`: The [`Workflow`] to disassemble.
     * - `assembly`: The serialized assembly of the same workflow, as a string. Don't forget to free it! Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * [`Null`] in all cases except when an error occurs. Then, an [`Error`]-struct is returned describing the error. Don't forget this has to be freed using [`error_free()`]!
     * 
     * # Panics
     * This function can panic if the given `workflow` is a NULL-pointer.
     */
    Error* (*workflow_disassemble)(Workflow* workflow, char** assembly);



    /***** COMPILER *****/
    /* Constructor for the Compiler.
     * 
     * # Arguments
     * - `endpoint`: The endpoint (as an address) to read the package & data index from. This is the address of a `brane-api` instance.
     * - `compiler`: Will point to the newly created [`Compiler`] when done. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * [`Null`] in all cases except when an error occurs. Then, an [`Error`]-struct is returned describing the error. Don't forget this has to be freed using [`error_free()`]!
     * 
     * # Panics
     * This function can panic if the given `endpoint` does not point to a valid UTF-8 string.
     */
    Error* (*compiler_new)(const char* endpoint, Compiler** compiler);
    /* Destructor for the Compiler.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `compiler`: The [`Compiler`] to free.
     */
    void (*compiler_free)(Compiler* compiler);
    
    /* Compiles the given BraneScript snippet to the BRANE Workflow Representation.
     * 
     * Note that this function changes the `compiler`'s state.
     * 
     * # Arguments
     * - `compiler`: The [`Compiler`] to compile with. Essentially this determines which previous compile state to use.
     * - `raw`: The raw BraneScript snippet to parse.
     * - `workflow`: Will point to the compiled AST. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * A [`SourceError`]-struct describing the error, if any, and source warnings/errors. Don't forget this has to be freed using [`serror_free()`]!
     * 
     * # Panics
     * This function can panic if the given `compiler` points to NULL, or `endpoint` does not point to a valid UTF-8 string.
     */
    SourceError* (*compiler_compile)(Compiler* compiler, const char* raw, Workflow** workflow);



    // /***** VIRTUAL MACHINE *****/
    // /* Constructor for the VirtualMachine.
    //  * 
    //  * # Arguments
    //  * - `api_endpoint`: The BRANE API endpoint to connect to for package information.
    //  * - `drv_endpoint`: The BRANE driver endpoint to connect to to execute stuff.
    //  * - `virtual_machine`: Will point to the newly created [`VirtualMachine`] when done. Will be [`NULL`] if there is an error (see below).
    //  * 
    //  * # Returns
    //  * An [`Error`]-struct that may or may not contain any generated errors.
    //  */
};
typedef struct _functions Functions;





/***** FUNCTIONS *****/
/* Loads the [`Functions`]-struct dynamically from the given .so file.
 * 
 * # Arguments
 * - `path`: The path to the .so file to load.
 * 
 * # Returns
 * The [`Functions`]-struct with everything loaded, including the dlopen handle - unless an error occurred. Then `NULL` is returned.
 */
Functions* functions_load(const char* path) {
    // Allocate the struct
    Functions* functions = (Functions*) malloc(sizeof(Functions));

    // Attempt to load the dlopen handle
    functions->handle = dlopen(path, RTLD_LAZY);
    if (functions->handle == NULL) { fprintf(stderr, "Failed to load dynamic library '%s'", path); return NULL; }

    // Load the error symbols
    functions->error_free = (void (*)(Error*)) dlsym(functions->handle, "error_free");
    functions->error_print_err = (void (*)(Error*)) dlsym(functions->handle, "error_print_err");

    // Load the source error symbols
    functions->serror_free = (void (*)(SourceError*)) dlsym(functions->handle, "serror_free");
    functions->serror_has_swarns = (bool (*)(SourceError*)) dlsym(functions->handle, "serror_has_warns");
    functions->serror_has_serrs = (bool (*)(SourceError*)) dlsym(functions->handle, "serror_has_serrs");
    functions->serror_has_err = (bool (*)(SourceError*)) dlsym(functions->handle, "serror_has_err");
    functions->serror_print_swarns = (void (*)(SourceError*, const char*, const char*)) dlsym(functions->handle, "serror_print_swarns");
    functions->serror_print_serrs = (void (*)(SourceError*, const char*, const char*)) dlsym(functions->handle, "serror_print_serrs");
    functions->serror_print_err = (void (*)(SourceError*)) dlsym(functions->handle, "serror_print_err");

    // Load the workflow symbols
    functions->workflow_free = (void (*)(Workflow*)) dlsym(functions->handle, "workflow_free");
    functions->workflow_disassemble = (Error* (*)(Workflow*, char**)) dlsym(functions->handle, "workflow_disassemble");

    // Load the compiler symbols
    functions->compiler_new = (Error* (*)(const char*, Compiler**)) dlsym(functions->handle, "compiler_new");
    functions->compiler_free = (void (*)(Compiler*)) dlsym(functions->handle, "compiler_free");
    functions->compiler_compile = (SourceError* (*)(Compiler*, const char*, Workflow**)) dlsym(functions->handle, "compiler_compile");

    // Done
    return functions;
}
/* Destroys the [`Functions`]-struct, unloading all the symbols within.
 * 
 * # Arguments
 * - `functions`: The [`Functions`]-struct to free.
 */
void functions_unload(Functions* functions) {
    // Close the handle, then free
    dlclose(functions->handle);
    free(functions);
}

#endif
