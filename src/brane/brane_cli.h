/* BRANE CLI.h
 *   by Lut99
 *
 * Created:
 *   14 Jun 2023, 11:49:07
 * Last edited:
 *   17 Aug 2023, 10:00:10
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Defines the headers of the `libbrane_cli` library.
**/

#ifndef BRANE_CLI_H
#define BRANE_CLI_H

#include <stdlib.h>
#include <stdio.h>
#include <dlfcn.h>


/***** MACROS *****/
/* Defines a shortcut for loading a symbol from a handle with `dlsym()`. */
#define LOAD_SYMBOL(TARGET, PROTOTYPE) \
    (state->TARGET) = (PROTOTYPE) dlsym(state->handle, (#TARGET)); \
    if ((state->TARGET) == NULL) { fprintf(stderr, "Failed to load symbol '%s': %s\n", (#TARGET), dlerror()); return NULL; }





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

/* Defines an index of available packages.
 * 
 * In reality, this actually wraps an `Arc<PackageIndex>`, meaning that you can safely deallocate this reference once given to a compiler- or VM-constructor without worrying about segfaults.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _package_index PackageIndex;
/* Defines an index of available datasets.
 * 
 * In reality, this actually wraps an `Arc<DataIndex>`, meaning that you can safely deallocate this reference once given to a compiler- or VM-constructor without worrying about segfaults.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _data_index DataIndex;

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

/* Defines a BRANE return value of a workflow.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _full_value FullValue;
/* Defines a BRANE instance virtual machine.
 * 
 * This can run a compiled workflow on a running instance.
 * 
 * WARNING: Do not access any internals yourself, since there are no guarantees on the internal layout of this struct.
 */
typedef struct _virtual_machine VirtualMachine;



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

    /* Forces the serialization functions to either use colour or not.
     * 
     * If you don't call this function, then it depends on whether the backend [`console`] library thinks if the stdout/stderr support ANSI colours.
     * 
     * # Arguments
     * - `force`: If true, then ANSI characters will be forced to be printed. Otherwise, if false, they will be forced to _not_ be printed.
     */
    void (*set_force_colour)(bool force);



    /***** ERROR *****/
    /* Destructor for the Error type.
     *
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     *
     * # Arguments
     * - `err`: The [`Error`] to deallocate.
     */
    void (*error_free)(Error* err);

    /* Serializes the error message in this error to the given buffer.
     * 
     * # Arguments
     * - `err`: the [`Error`] to serialize the error of.
     * - `buffer`: The buffer to serialize to. Will be freshly allocated using `malloc` for the correct size; can be freed using `free()`.
     * 
     * # Panics
     * This function can panic if the given `err` or `buffer` are NULL-pointers.
     */
    void (*error_serialize_err)(Error* err, char** buffer);

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

    /* Serializes the source warnings in this error to the given buffer.
     * 
     * Note that there may be zero or more warnings at once. To discover if there are any, check [`serror_has_swarns()`].
     * 
     * # Arguments
     * - `serr`: the [`SourceError`] to serialize the source warnings of.
     * - `buffer`: The buffer to serialize to. Will be freshly allocated using `malloc` for the correct size; can be freed using `free()`.
     * 
     * # Panics
     * This function can panic if the given `serr` or `buffer` are NULL-pointers.
     */
    void (*serror_serialize_swarns)(SourceError* serr, char** buffer);
    /* Serializes the source errors in this error to the given buffer.
     * 
     * Note that there may be zero or more errors at once. To discover if there are any, check [`serror_has_serrs()`].
     * 
     * # Arguments
     * - `serr`: the [`SourceError`] to serialize the source errors of.
     * - `buffer`: The buffer to serialize to. Will be freshly allocated using `malloc` for the correct size; can be freed using `free()`.
     * 
     * # Panics
     * This function can panic if the given `serr` or `buffer` are NULL-pointers.
     */
    void (*serror_serialize_serrs)(SourceError* serr, char** buffer);
    /* Serializes the error message in this error to the given buffer.
     * 
     * Note that there may be no error, but only source warnings- or errors. To discover if there is any, check [`serror_has_err()`].
     * 
     * # Arguments
     * - `serr`: the [`SourceError`] to serialize the error of.
     * - `buffer`: The buffer to serialize to. Will be freshly allocated using `malloc` for the correct size; can be freed using `free()`.
     * 
     * # Panics
     * This function can panic if the given `serr` or `buffer` are NULL-pointers.
     */
    void (*serror_serialize_err)(SourceError* serr, char** buffer);

    /* Prints the source warnings in this error to stderr.
     * 
     * Note that there may be zero or more warnings at once. To discover if there are any, check [`serror_has_swarns()`].
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] to print the source warnings of.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    void (*serror_print_swarns)(SourceError* serr);
    /* Prints the source errors in this error to stderr.
     * 
     * Note that there may be zero or more errors at once. To discover if there are any, check [`serror_has_serrs()`].
     * 
     * # Arguments
     * - `serr`: The [`SourceError`] to print the source errors of.
     * 
     * # Panics
     * This function can panic if the given `serr` is a NULL-pointer.
     */
    void (*serror_print_serrs)(SourceError* serr);
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



    /***** PACKAGE INDEX *****/
    /* Constructs a new [`PackageIndex`] that lists the available packages in a remote instance.
     * 
     * # Arguments
     * - `endpoint`: The remote API-endpoint to read the packages from. The path (`/graphql`) will be deduced and needn't be given, just the host and port.
     * - `pindex`: Will point to the newly created [`PackageIndex`] when done. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * [`Null`] in all cases except when an error occurs. Then, an [`Error`]-struct is returned describing the error. Don't forget this has to be freed using [`error_free()`]!
     * 
     * # Panics
     * This function can panic if the given `endpoint` does not point to a valud UTF-8 string.
     */
    Error* (*pindex_new_remote)(const char* endpoint, PackageIndex** pindex);

    /* Destructor for the PackageIndex.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `pindex`: The [`PackageIndex`] to free.
     */
    void (*pindex_free)(PackageIndex* pindex);



    /***** DATA INDEX *****/
    /* Constructs a new [`DataIndex`] that lists the available datasets in a remote instance.
     * 
     * # Arguments
     * - `endpoint`: The remote API-endpoint to read the datasets from. The path (`/data/info`) will be deduced and needn't be given, just the host and port.
     * - `dindex`: Will point to the newly created [`DataIndex`] when done. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * [`Null`] in all cases except when an error occurs. Then, an [`Error`]-struct is returned describing the error. Don't forget this has to be freed using [`error_free()`]!
     * 
     * # Panics
     * This function can panic if the given `endpoint` does not point to a valud UTF-8 string.
     */
    Error* (*dindex_new_remote)(const char* endpoint, DataIndex** dindex);

    /* Destructor for the DataIndex.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `dindex`: The [`DataIndex`] to free.
     */
    void (*dindex_free)(DataIndex* dindex);



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
     * - `pindex`: The [`PackageIndex`] to resolve package references in the snippets with.
     * - `dindex`: The [`DataIndex`] to resolve dataset references in the snippets with.
     * - `compiler`: Will point to the newly created [`Compiler`] when done. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * [`Null`] in all cases except when an error occurs. Then, an [`Error`]-struct is returned describing the error. Don't forget this has to be freed using [`error_free()`]!
     * 
     * # Panics
     * This function can panic if the given `pindex` or `dindex` points to NULL.
     */
    Error* (*compiler_new)(PackageIndex* pindex, DataIndex* dindex, Compiler** compiler);
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
     * - `what`: Some string describing what we are compiling (e.g., a file, `<intern>`, a cell, etc.)
     * - `raw`: The raw BraneScript snippet to parse.
     * - `workflow`: Will point to the compiled AST. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * A [`SourceError`]-struct describing the error, if any, and source warnings/errors.
     * 
     * ## SAFETY
     * Be aware that the returned [`SourceError`] refers the the given `compiler` and `what`. Freeing any of those two and then using the [`SourceError`] _will_ lead to undefined behaviour.
     * 
     * You _must_ free this [`SourceError`] using [`serror_free()`], since its allocated using Rust internals and cannot be deallocated directly using `malloc`. Note, however, that it's safe to call [`serror_free()`] _after_ freeing `compiler` or `what` (but that's the only function).
     * 
     * # Panics
     * This function can panic if the given `compiler` points to NULL, or `what`/`raw` does not point to a valid UTF-8 string.
     */
    SourceError* (*compiler_compile)(Compiler* compiler, const char* what, const char* raw, Workflow** workflow);



    /***** FULL VALUE *****/
    /* Destructor for the FullValue.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `fvalue`: The [`FullValue`] to free.
     */
    void (*fvalue_free)(FullValue* fvalue);

    /* Checks if this [`FullValue`] needs processing.
     * 
     * For now, this only occurs when it is a [`FullValue::Data`] (download it) or [`FullValue::IntermediateResult`] (throw a warning).
     * 
     * # Arguments
     * - `fvalue`: The [`FullValue`] to analyse.
     * 
     * # Returns
     * True if `vm_process()` should be called on this value or false otherwise.
     * 
     * # Panics
     * This function can panic if `fvalue` pointed to [`NULL`].
     */
    bool (*fvalue_needs_processing)(FullValue* fvalue);

    /* Serializes a FullValue to show as result of the workflow.
     * 
     * # Arguments
     * - `fvalue`: the [`FullValue`] to serialize.
     * - `data_dir`: The data directory to which we downloaded the `fvalue`, if we did so.
     * - `result`: The buffer to serialize to. Will be freshly allocated using `malloc` for the correct size; can be freed using `free()`.
     * 
     * # Panics
     * This function can panic if the given `fvalue` is a NULL-pointer or if `data_dir` did not point to a valid UTF-8 string.
     */
    void (*fvalue_serialize)(FullValue* fvalue, const char* data_dir, char** result);



    /***** VIRTUAL MACHINE *****/
    /* Constructor for the VirtualMachine.
     * 
     * # Arguments
     * - `api_endpoint`: The Brane API endpoint to connect to to download available registries and all that.
     * - `drv_endpoint`: The BRANE driver endpoint to connect to to execute stuff.
     * - `certs_dir`: The directory where certificates for downloading datasets are stored.
     * - `pindex`: The [`PackageIndex`] to resolve package references in the snippets with.
     * - `dindex`: The [`DataIndex`] to resolve dataset references in the snippets with.
     * - `virtual_machine`: Will point to the newly created [`VirtualMachine`] when done. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * An [`Error`]-struct that contains the error occurred, or [`NULL`] otherwise.
     * 
     * # Panics
     * This function can panic if the given `pindex` or `dindex` are NULL, or if the given `api_endpoint`, `drv_endpoint` or `certs_dir` do not point to a valid UTF-8 string.
     */
    Error* (*vm_new)(const char* api_endpoint, const char* drv_endpoint, const char* certs_dir, PackageIndex* pindex, DataIndex* dindex, VirtualMachine** vm);
    /* Destructor for the VirtualMachine.
     * 
     * SAFETY: You _must_ call this destructor yourself whenever you are done with the struct to cleanup any code. _Don't_ use any C-library free!
     * 
     * # Arguments
     * - `vm`: The [`VirtualMachine`] to free.
     */
    void (*vm_free)(VirtualMachine* vm);

    /* Runs the given code snippet on the backend instance.
     * 
     * # Arguments
     * - `vm`: The [`VirtualMachine`] that we execute with. This determines which backend to use.
     * - `workflow`: The compiled workflow to execute.
     * - `prints`: A newly allocated string which represents any stdout- or stderr prints done during workflow execution. Will be [`NULL`] if there is an error (see below).
     * - `result`: A [`FullValue`] which represents the return value of the workflow. Will be [`NULL`] if there is an error (see below).
     * 
     * # Returns
     * An [`Error`]-struct that contains the error occurred, or [`NULL`] otherwise.
     * 
     * # Panics
     * This function may panic if the input `vm` or `workflow` pointed to a NULL-pointer.
     */
    Error* (*vm_run)(VirtualMachine* vm, Workflow* workflow, char** prints, FullValue** result);
    /* Processes the result referred to by the [`FullValue`].
     * 
     * Processing currently consists of:
     * - Downloading the dataset if it's a [`FullValue::Data`]
     * - Throwing a warning if it's a [`FullValue::IntermediateResult`]
     * - Doing nothing otherwise
     * 
     * # Arguments
     * - `vm`: The [`VirtualMachine`] that we download with. This determines which backend to use.
     * - `result`: The [`FullValue`] which we will attempt to download if needed.
     * - `data_dir`: The directory to download the result to. This should be the generic data directory, as a new directory for this dataset will be created within.
     * 
     * # Returns
     * An [`Error`]-struct that contains the error occurred, or [`NULL`] otherwise.
     * 
     * # Panics
     * This function may panic if the input `vm` or `result` pointed to a NULL-pointer, or if `data_dir` did not point to a valid UTF-8 string.
     */
    Error* (*vm_process)(VirtualMachine* vm, FullValue* result, const char* data_dir);
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
    Functions* state = (Functions*) malloc(sizeof(Functions));

    // Attempt to load the dlopen handle
    state->handle = dlopen(path, RTLD_LAZY);
    if (state->handle == NULL) { fprintf(stderr, "Failed to load dynamic library '%s': %s\n", path, dlerror()); return NULL; }

    // Load the separate-function symbols
    LOAD_SYMBOL(version, const char* (*)());
    LOAD_SYMBOL(set_force_colour, void (*)(bool));

    // Load the error symbols
    LOAD_SYMBOL(error_free, void (*)(Error*));
    LOAD_SYMBOL(error_serialize_err, void (*)(Error*, char**));
    LOAD_SYMBOL(error_print_err, void (*)(Error*));

    // Load the source error symbols
    LOAD_SYMBOL(serror_free, void (*)(SourceError*));
    LOAD_SYMBOL(serror_has_swarns, bool (*)(SourceError*));
    LOAD_SYMBOL(serror_has_serrs, bool (*)(SourceError*));
    LOAD_SYMBOL(serror_has_err, bool (*)(SourceError*));
    LOAD_SYMBOL(serror_serialize_swarns, void (*)(SourceError*, char**));
    LOAD_SYMBOL(serror_serialize_serrs, void (*)(SourceError*, char**));
    LOAD_SYMBOL(serror_serialize_err, void (*)(SourceError*, char**));
    LOAD_SYMBOL(serror_print_swarns, void (*)(SourceError*));
    LOAD_SYMBOL(serror_print_serrs, void (*)(SourceError*));
    LOAD_SYMBOL(serror_print_err, void (*)(SourceError*));

    // Load the index symbols
    LOAD_SYMBOL(pindex_new_remote, Error* (*)(const char*, PackageIndex**));
    LOAD_SYMBOL(pindex_free, void (*)(PackageIndex*));
    LOAD_SYMBOL(dindex_new_remote, Error* (*)(const char*, DataIndex**));
    LOAD_SYMBOL(dindex_free, void (*)(DataIndex*));

    // Load the workflow symbols
    LOAD_SYMBOL(workflow_free, void (*)(Workflow*));
    LOAD_SYMBOL(workflow_disassemble, Error* (*)(Workflow*, char**));

    // Load the compiler symbols
    LOAD_SYMBOL(compiler_new, Error* (*)(PackageIndex*, DataIndex*, Compiler**));
    LOAD_SYMBOL(compiler_free, void (*)(Compiler*));
    LOAD_SYMBOL(compiler_compile, SourceError* (*)(Compiler*, const char*, const char*, Workflow**));

    // Load the FullValue symbols
    LOAD_SYMBOL(fvalue_free, void (*)(FullValue*));
    LOAD_SYMBOL(fvalue_needs_processing, bool (*)(FullValue*));
    LOAD_SYMBOL(fvalue_serialize, void (*)(FullValue*, const char*, char**));

    // Load the VM symbols
    LOAD_SYMBOL(vm_new, Error* (*)(const char*, const char*, const char*, PackageIndex*, DataIndex*, VirtualMachine**));
    LOAD_SYMBOL(vm_free, void (*)(VirtualMachine*));
    LOAD_SYMBOL(vm_run, Error* (*)(VirtualMachine*, Workflow*, char**, FullValue**));
    LOAD_SYMBOL(vm_process, Error* (*)(VirtualMachine*, FullValue*, const char*));

    // Done
    return state;
}
/* Destroys the [`Functions`]-struct, unloading all the symbols within.
 * 
 * # Arguments
 * - `state`: The [`Functions`]-struct to free.
 */
void functions_unload(Functions* state) {
    // Close the handle, then free
    dlclose(state->handle);
    free(state);
}

#endif
