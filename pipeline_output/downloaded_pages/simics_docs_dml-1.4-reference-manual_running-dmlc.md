[1 Introduction](introduction.html) [3 Device Modeling Language, version 1.4](language.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [2 The DML compiler](#the-dml-compiler)
A DML source file can be compiled into a runnable device model using the DML compiler, `dmlc`. The main output of the compiler is a C file, that can be compiled into a Simics module.
The DML compiler and its libraries are available as part of the _Simics Base_ package.
## [2.1 Building dmlc](#building-dmlc)
The `dmlc` compiler can be build locally. This requires an installation of the Simics 6 base package.
In order to build the compiler, checkout [the DML repository ](https://github.com/intel/device-modeling-language) into the into the `modules/dmlc` subdirectory of your Simics project. The compiler can be built using the `make dmlc` command. The build result ends up in `_host_/bin/dml`(where _`host`_is`linux64` or `win64`), and consists of three parts:
  * `_host_/bin/dml/python`contains the Python module that implements the compiler
  * `_host_/bin/dml/1.4`contains the standard libraries required to compile a device
  * `_host_/bin/dml/api`contains`.dml` files that expose the Simics API


In order to use a locally built version of `dmlc` to compile your devices, you can add the following line to your `config-user.mk` file:
```
DMLC_DIR = $(SIMICS_PROJECT)/$(HOST_TYPE)/bin

```

## [2.2 Running dmlc](#running-dmlc)
The syntax for running `dmlc` from the command line is:
```
dmlc [_options_] _input_ [_output-base_]

```

where _input_ should be the name of a DML source file. If _output-base_ is provided, it will be used to name the created files. The name of a DML source file should normally have the suffix "`.dml`". The _input_ file must contain a [`device` declaration](language.html#device-declaration).
The main output of `dmlc` is a C file named `_<output-base>_.c`, which that can be compiled and linked into a Simics module using the`gcc` compiler. The compiler also produces some other helper files with `.h` and `.c` suffix, which the main output file includes.
## [2.3 Command Line Options](#command-line-options)
The following are the available command line options to `dmlc`: 

[ -h, --help ](#dt:h-help)
    
Print usage help. 

[ -I _path_ ](#dt:i-path)
    
Add _path_ to the search path for imported modules. 

[ -D _name_ =_definition_ ](#dt:d-name-definition)
    
Define a compile-time parameter. The definition must be a literal expression, and can be a quoted string, a boolean, an integer, or a floating point constant. The parameter will appear in the top-level scope. 

[ --dep ](#dt:dep)
    
Output makefile rules describing dependencies. 

[ -T ](#dt:t)
    
Show tags on warning messages. The tags can be used with the `--nowarn` and `--warn` options. 

[ -g ](#dt:g)
    
Generate artifacts that allow for easier source-level debugging. This generates a DML debug file leveraged by debug-simics, and causes generated C code to follow the DML code more closely. 

[ --coverity ](#dt:coverity)
    
Adds Synopsys® Coverity® analysis annotations to suppress common false positives in generated C code created from DML 1.4 device models. It also allows for false positives to be suppressed manually through the use of the [`COVERITY` pragma](language.html#coverity-pragma)
Analysis annotation generation impacts the generation of line directives in a way that may cause debugging or coverage tools besides Coverity to display unexpected behavior. Because of this, it's recommended that `--coverity` is only used when needed. 

[ --warn=_tag_ ](#dt:warn-tag)
    
Enable selected warnings. The tags can be found using the `-T` option. 

[ --nowarn=_tag_ ](#dt:nowarn-tag)
    
Suppress selected warnings. The tags can be found using the `-T` option. 

[ --werror ](#dt:werror)
    
Turn all warnings into errors. 

[ --strict ](#dt:strict)
    
Report errors for some constructs that will be forbidden in future versions of the DML language 

[ --noline ](#dt:noline)
    
Suppress line directives for the C preprocessor so that the C code can be debugged. 

[ --info ](#dt:info)
    
Enable the output of an XML file describing register layout. 

[ --version ](#dt:version)
    
Print version information. 

[ --simics-api=_version_ ](#dt:simics-api-version)
    
Use Simics API version _version_. 

[ --max-errors=_N_ ](#dt:max-errors-n)
    
Limit the number of error messages to _N_.
[1 Introduction](introduction.html) [3 Device Modeling Language, version 1.4](language.html)
