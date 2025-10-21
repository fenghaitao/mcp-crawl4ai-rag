[B Provisional language features](provisional-auto.html) [D Changes from DML 1.2 to DML 1.4](changes.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [C Managing deprecated language features](#managing-deprecated-language-features)
As the DML language evolves, we sometimes need to change the language in incompatible ways, which requires DML users to migrate their code. This appendix describes the mechanisms we provide to make this migration process smooth for users with large DML code bases.
In DML, deprecations can come in many forms. Deprecations in the form of removed or renamed symbols in libraries are rather easy to manage, since they give clear compile errors that often are straightforward to fix. A slightly harder type of deprecation is when some language construct or API function adjusts its semantics; this can make the model behave differently without signalling error messages. A third kind of deprecation is when DML changes how compiled models appear in Simics, typically to adjust changes in the Simics API. Such changes add another dimension because they typically affect the end-users of the DML models, rather than the authors of the models. Thus, as an author of a model you may need to synchronize your migration of such features with your end-users, to ease their transition to a new major version.
## [C.1 Deprecation mechanisms](#deprecation-mechanisms)
The simplest deprecation mechanism is Simics API versions: Each deprecated DML feature is associated with a Simics API version, and each Simics version supports a number of such API versions. Features reach end-of-life when moving to a new Simics major version, the features belonging to a previous Simics API version are dropped. Since Simics is currently the primary distribution channel for DML, this deprecation scheme is used for DML features as well.
This scheme allows users with a large code base to smoothly migrate from one Simics major version, N, to the next, N+1:
  * First, while still using version N, make sure all Simics modules are updated to use API version N. Modules can be migrated one by one.
  * Second, update the Simics version to N+1. This should normally have no effect on DML, but may come with other challenges.
  * Third, update modules to API N+1, one by one. Simics version N+1 will always offers full support for API N, so there is no rush to update, but changing the API version early makes sure deprecated features are not introduced in new code.


In addition to the API version, DML offers some compiler flags for selectively disabling deprecated features that are normally part of the used API. This has some uses, in particular:
  * During migration to a new API version, disabling one deprecated feature at a time can allow a smoother, more gradual, migration.
  * If a legacy feature is still fully supported in the latest API version, then it cannot be disabled by selecting an API version, so selectively disabling it is the only way to turn it off. There are reasons to do this, e.g.: 
    * Disabling a feature before it is deprecated guarantees that it is not relied upon in new code, which eases later migration.
    * Avoiding a feature that has a newer replacement makes the code base cleaner and more consistent.
    * Some legacy features can also bloat models, by exposing features in a redundant manner. This can also have a negative impact on performance.


## [C.2 Controlling deprecation on the DML command-line](#controlling-deprecation-on-the-dml-command-line)
DMLC provides a command-line flag `--api-version` to specify the API version to be used for a model. When building with the standard Simics build system, this is controlled by the `SIMICS_API_VERSION` variable in `make`, or the `SIMICS_API`/`MODULE_SIMICS_API` variable in `CMake`.
DMLC also provides the `--no-compat=_tag_`flag, which disables the feature represented by _`tag`_. The available tags are listed in the next section. The tag also controls the name of a global boolean parameter that the DML program may use to check whether the feature is available. The parameter's name is the tag name preceded by`_compat_`.
## [C.3 List of deprecated features](#list-of-deprecated-features)
### [C.3.1 Features available up to and including --simics-api=6](#features-available-up-to-and-including-simics-api-6)
These features correspond to functionality removed when compiling using Simics API 7 or newer. With older Simics API versions, these features can be disabled individually by passing `--no-compat=_TAG_` to the `dmlc` compiler. 

[dml12_goto](#dt:dml12_goto)
    
The `goto` statement is deprecated; this compatibility feature preserves it. Most `goto` based control structures can be reworked by changing the `goto` into a `throw`, and its label into a `catch` block; since this is sometimes nontrivial, it can be useful to disable the `goto` statement separately. 

[dml12_inline](#dt:dml12_inline)
    
When using `inline` to inline a method in a DML 1.2 device, constant arguments passed in typed parameters are inlined as constants when this feature is enabled. This can improve compilation time in some cases, but has some unintuitive semantic implications. 

[dml12_int](#dt:dml12_int)
    
This compatibility feature affects many semantic details of integer arithmetic. When this feature is enabled, DMLC translates most integer operations directly into C, without compensating for DML-specifics, like the support for odd-sized `uint _NN_` types; this can sometimes have unexpected consequences. The most immediate effect of disabling this feature is that DMLC will report errors on statements like `assert 0;` and `while (1) { ... }`, which need to change into `assert false;` and `while (true) { ... }`, respectively. Other effects include:
  * Integers of non-standard sizes are represented as a native C type, e.g. `uint5` is represented as `uint8`, allowing it to store numbers too large to fit in 5 bits. With modern DML semantics, arithmetic is done on 64-bit integers and bits are truncated if casting or storing in a smaller type.
Old code sometimes relies on this feature by comparing variables of type `int1` to the value `1`. In DML 1.4, the only values of type `int1` are `0` and `-1`, so such code should be rewritten to use the `uint1` type. It can be a good idea to grep for `[^a-z_]int1[^0-9]` and review if `uint1` is a better choice.
  * Some operations have undefined behaviour in C, which is inherited by traditional DML 1.2. In modern DML this is well-defined, e.g., an unconditional critical error on negative shift or division by zero, and truncation on too large shift operands or signed shift overflow.
  * Comparison operators `<`, `<=`, `==`, `>=`, `>` inherit C semantics in traditional DML, whereas in modern DML they are compared as integers. This sometimes makes a difference when comparing signed and unsigned numbers; in particular, `-1 != 0xffffffffffffffff` consistently in modern DML, whereas with compatibility semantics, they are consiered different only if both are constant.


The `dml12_int` feature only applies to DML 1.2 files; if a DML 1.4 file is imported from a DML 1.2 file, then modern DML semantics is still used for operations in that file. 

[dml12_misc](#dt:dml12_misc)
    
This compatibility feature preserves a number of minor language quirks that were originally in DML 1.2, but were cleaned up in DML 1.4. When this feature is enabled, DML 1.2 will permit the following:
  * `sizeof(typename)` (see `WSIZEOFTYPE`)
  * the `typeof` operator on an expression that isn't an lvalue
  * `select` statements over `vect` types
  * Passing a string literal in a (non-`const`) `char *` method argument
  * Using the character `-` in the `c_name` parameter of `interface` objects
  * Using the `c_name` parameter to override interface type in `implement` objects
  * `loggroup` identifiers are accessible under the same name in generated C code
  * Applying the `&` operator on something that isn't an lvalue (typically gives broken C code)
  * `extern` statements that do not specify a type (`extern foo;`)
  * Anonymous banks (`bank { ... }`)
  * Unused templates may instantiate non-existing templates
  * The same symbol may be used both for a top-level object (`$` scope) and a top-level symbol (non-`$` scope, e.g. `extern`, `constant` or `loggroup`)



[io_memory](#dt:io_memory)
    
The `transaction` interface was introduced in 6, and will eventually replace the `io_memory` interface. When this feature is enabled, the top-level parameter `use_io_memory` defaults to `true`, causing `bank` objects to implement `io_memory` instead of `transaction` by default. 

[shared_logs_on_device](#dt:shared_logs_on_device)
    
This compatibility feature changes the semantics of log statements inside shared methods so that they always log on the device object, instead of the nearest enclosing configuration object like with non-shared methods. This behaviour was a bug present since the very introduction of shared methods, which has lead to plenty of script code having become reliant on it, especially in regards to how banks log. This feature preserves the bugged behaviour. 

[suppress_WLOGMIXUP](#dt:suppress_wlogmixup)
    
This compatibility feature makes it so the warning `WLOGMIXUP` is suppressed by default. `WLOGMIXUP` warns about usages of a common faulty pattern which results in broken log statements — for more information, see the documentation of `WLOGMIXUP` in the [Messages](messages.html) section.
`WLOGMIXUP` is suppressed by default below Simics API version 7 in order to avoid overwhelming users with warnings, as the faulty pattern that `WLOGMIXUP` reports is very prevalent within existing code. Addressing applications of the faulty pattern should be done before or as part of migration to Simics API version 7.
Passing `--no-compat=suppress_WLOGMIXUP` to DMLC has almost the same effect as passing `--warn=WLOGMIXUP`; either will cause DMLC to report the warning even when the Simics API version in use is below 7. The only difference between these two options is that if `--no-compat=suppress_WLOGMIXUP` is used (and `--warn=WLOGMIXUP` is not), then `WLOGMIXUP` may still be explicitly suppressed via `--no-warn=WLOGMIXUP`. In contrast, `--warn=WLOGMIXUP` doesn't allow for `WLOGMIXUP` to be suppressed at all.
### [C.3.2 Features available up to and including --simics-api=7](#features-available-up-to-and-including-simics-api-7)
These features correspond to functionality removed when compiling using Simics API 8 or newer. With older Simics API versions, these features can be disabled individually by passing `--no-compat=_TAG_` to the `dmlc` compiler. 

[broken_conditional_is](#dt:broken_conditional_is)
    
This compatibility feature prevents DML from reporting errors when instantiating a template within an `#if` block:
```
#if (true) {
  group g {
    // should be an error, but silently ignored when this
    // feature is enabled
    is nonexisting_template;
  }
}

```

Up to Simics 7, a bug prevented DMLC from reporting an error; this feature exists to preserve that behaviour. 

[broken_unused_types](#dt:broken_unused_types)
    
This compatibility feature prevents DML from reporting errors on unused `extern`-declared types:
```
extern typedef struct {
  undefined_type_t member;
} never_used_t;

```

Up to Simics 7, a bug prevented DMLC from reporting an error; this feature exists to preserve that behaviour. 

[experimental_vect](#dt:experimental_vect)
    
This compat feature controls how DMLC reacts to uses of the `vect` syntax in files where the [`simics_util_vect` provisional feature](provisional-auto.html#simics_util_vect) is not enabled.
When the `experimental_vect` compatibility feature is enabled, such uses are permitted, and give a `WEXPERIMENTAL` warning in DML 1.4 (but no warning in DML 1.2). When `experimental_vect` is disabled, DMLC forbids the `vect` syntax. 

[function_in_extern_struct](#dt:function_in_extern_struct)
    
This compatibility feature enables a traditionally allowed syntax for function pointer members of `extern typedef struct` declarations, where the `*` is omitted in the pointer type. When disabling this feature, any declarations on this form:
```
extern typedef struct {
  void m(conf_object_t *);
} my_interface_t;

```

need to be changed to the standard C form:
```
extern typedef struct {
  void (*m)(conf_object_t *);
} my_interface_t;

```


[legacy_attributes](#dt:legacy_attributes)
    
This compatibility feature makes DMLC register all attributes using the legacy `SIM_register_typed_attribute` API function instead of the modern `SIM_register_attribute` family of API functions.
Disabling this feature will make the dictionary attribute type ("D" in type strings) to become unsupported, and any usage of it rejected by Simics. Thus, when migrating away from this feature, any attribute of the model that leverages dictionary values should be changed to leverage a different representation. In general, any dictionary can instead be represented by a list of two-element lists, e.g. `[[_X_,_Y_]*]`, where _X_ describes the type of keys, and _Y_ describes the type of values. 

[lenient_typechecking](#dt:lenient_typechecking)
    
This compatibility feature makes DMLC's type checking very inexact and lenient in multiple respects when compared to GCC's type checking of the generated C. This discrepency mostly affects method overrides or uses of `extern`:d C macros, because in those scenarios DMLC can become wholly responsible for proper type checking.
While migrating away from this feature, the most common type errors that its disablement introduces are due to discrepencies between pointer types. In particular, implicitly discarding `const`-qualification of a pointer's base type will never be tolerated, and `void` pointers are only considered equivalent with any other pointer type in the same contexts as C.
Novel type errors from uses of `extern`:d macros can often be resolved by changing the signature of the `extern` declaration to more accurately reflect the macro's effective type. 

[meaningless_log_levels](#dt:meaningless_log_levels)
    
The log level that may be specified for logs of kind "warning", "error" or "critical" typically must be 1, and any subsequent log level must typically be 5. This compatibility feature makes it so either log level may be any integer between 1 and 4 for these log kinds. The primary log level is always treated as 1, and any other value than 1 for the subsequent log level will be treated as 5 (that is, the log will only happen once) 

[no_method_index_asserts](#dt:no_method_index_asserts)
    
This compatibility feature makes it so that methods defined under object arrays don't implicitly assert that the indices used to reference the object array when calling the method are in bounds.
Migrating away from this compatibility feature should be a priority. If its disablement makes the simulation crash due to an assertion failing, then that **definitely signifies a bug in your model; a bug that would very likely result in memory corruption if the assertion were not to be made.** 

[optional_version_statement](#dt:optional_version_statement)
    
When this compatibility feature is enabled, the version specification statement (`dml 1.4;`) statement at the start of each file is optional (but the compiler warns if it is omitted). Also, `dml 1.3;` is permitted as a deprecated alias for `dml 1.4;`, with a warning. 

[port_proxy_attrs](#dt:port_proxy_attrs)
    
In Simics 5, configuration attributes for `connect`, `attribute` and `register` objects inside banks and ports were registered on the device object, named like `_bankname___attrname_`. Such proxy attributes are only created When this feature is enabled. Proxy attributes are not created for all banks and ports, in the same manner as documented in the`port_proxy_ifaces` feature. 

[port_proxy_ifaces](#dt:port_proxy_ifaces)
    
Version 5 and earlier of Simics relied on interface ports (as registered by the `SIM_register_port_interface` API function) for exposing the interfaces of ports and banks. In newer versions of Simics, interfaces are instead exposed on separate configuration objects. When this feature is enabled, old-style interface ports are created as proxies to the interfaces on the respective port objects. Such proxies are not created for all banks and ports; e.g., banks inside groups were not allowed in Simics 5, so such banks do not need proxies for backward compatibility. 

[warning_statement](#dt:warning_statement)
    
This compatibility feature enables the `_warning` statement. This turned out to not be very useful, so in Simics API 8 and newer the feature is no longer allowed.
[B Provisional language features](provisional-auto.html) [D Changes from DML 1.2 to DML 1.4](changes.html)
