/* CUSTOM INTERPRETER.hpp
 *   by Lut99
 *
 * Created:
 *   13 Jun 2023, 16:09:11
 * Last edited:
 *   13 Jun 2023, 16:10:31
 * Auto updated?
 *   Yes
 *
 * Description:
 *   Header file for the custom interpreter implementation for BraneScript.
**/

#ifndef CUSTOM_INTERPRETER_HPP
#define CUSTOM_INTERPRETER_HPP

#include "xeus/xinterpreter.hpp"
#include "nlohmann/json.hpp"

using xeus::xinterpreter;
namespace nl = nlohmann;

namespace bscript {
    class custom_interpreter: public xinterpreter {
        
    };
}

#endif
