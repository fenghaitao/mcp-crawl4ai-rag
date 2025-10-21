[5 Standard Templates](utility.html) [B Provisional language features](provisional-auto.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [A Messages](#messages)
The following sections list the warnings and error messages from `dmlc`, with some clarifications.
## [A.1 Warning Messages](#warning-messages)
The messages are listed in alphabetical order; the corresponding tags are shown within brackets, e.g., `[WNDOC]`. 

[******... [WSYSTEMC]**](#dt:wsystemc)
    
SystemC specific warnings 

[******... [WWRNSTMT]**](#dt:wwrnstmt)
    
The source code contained a statement "`warning;`", which causes a warning to be printed. 

[******'X then Y' log level has no effect when the levels are the same [WREDUNDANTLEVEL]**](#dt:x-then-y-log-level-has-no-effect-when-the-levels-are-the-same-wredundantlevel)
    
`X then Y` log level syntax has no effect when the first and subsequent levels are the same. 

[******_**INCREDIBLY UNSAFE**_ use of immediate 'after' statement: the callback argument '...' is a pointer to stack-allocated data! [WIMMAFTER]**](#dt:incredibly-unsafe-use-of-immediate-after-statement-the-callback-argument-is-a-pointer-to-stack-allocated-data-wimmafter)
    
An immediate `after` statement was specified where some argument to the callback is a pointer to some stack-allocated data — i.e. a pointer to data stored within a local variable. That data is guaranteed to be invalid by the point the callback is called, which presents an enormous security risk! 

[******_**INCREDIBLY UNSAFE**_ use of the 'send' operation of a hook: the message component '...' is a pointer to stack-allocated data! [WHOOKSEND]**](#dt:incredibly-unsafe-use-of-the-send-operation-of-a-hook-the-message-component-is-a-pointer-to-stack-allocated-data-whooksend)
    
The `send` operation of a hook was called, and some provided message component is a pointer to some stack-allocated data — i.e. a pointer to data stored within a local variable. That data is guaranteed to be invalid by the point the message is sent, which presents an enormous security risk!
If you must use pointers to stack-allocated data, then `send_now` should be used instead of `send`. If you want the message to be delayed to avoid ordering bugs, create a method which wraps the `send_now` call together with the declarations of the local variable(s) which you need pointers to, and then use immediate after (`after: m(...)`) to delay the call to that method. 

[******Comparing negative constant to unsigned integer has a constant result [WNEGCONSTCOMP]**](#dt:comparing-negative-constant-to-unsigned-integer-has-a-constant-result-wnegconstcomp)
    
DML uses a special method when comparing an unsigned and signed integer, meaning that comparing a negative constant to an unsigned integer always has the same result, which is usually not the intended behaviour. 

[******Outdated AST file: ... [WOLDAST]**](#dt:outdated-ast-file-woldast)
    
A precompiled DML file has an old time-stamp. This may happen if a user accidentally edits a DML file from the standard library. A safe way to suppress the warning is to remove the outdated `.dmlast` file. 

[******The assignment source is a constant value which does not fit the assign target of type '...', and will thus be truncated [WASTRUNC]**](#dt:the-assignment-source-is-a-constant-value-which-does-not-fit-the-assign-target-of-type-and-will-thus-be-truncated-wastrunc)
    
The source of an assignment is a constant value that can't fit in the type of the target, and is thus truncated. This warning can be silenced by explicitly casting the expression to the target type. 

[******Use of unsupported feature: ... [WEXPERIMENTAL]**](#dt:use-of-unsupported-feature-wexperimental)
    
This part of the language is experimental, and not yet officially supported. Code relying on the feature may break without notice in future releases. 

[******Use of unsupported feature: ... [WEXPERIMENTAL_UNMAPPED]**](#dt:use-of-unsupported-feature-wexperimental_unmapped)
    
This part of the language is experimental, and not yet officially supported. Code relying on the feature may break without notice in future releases. 

[******deprecation: ... [WDEPRECATED]**](#dt:deprecation-wdeprecated)
    
This part of the language is deprecated, usually because the underlying support in Simics is deprecated. 

[******duplicate event checkpoint names: ... [WDUPEVENT]**](#dt:duplicate-event-checkpoint-names-wdupevent)
    
Two or more events will be checkpointed using the same name, which means that the checkpoint cannot be safely read back. 

[******file has no version tag, assuming version 1.2 [WNOVER]**](#dt:file-has-no-version-tag-assuming-version-1-2-wnover)
    
A DML file must start with a version statement, such as `dml 1.4;` 

[******implementation of ...() without 'is ...' is ignored by the standard library [WNOIS]**](#dt:implementation-of-without-is-is-ignored-by-the-standard-library-wnois)
    
Many standard method overrides will only be recognized if a template named like the method is also instantiated. For instance, the method `set` in a field has no effect unless the `set` template is instantiated. 

[******log statement with likely misspecified log level(s) and log groups: ... [WLOGMIXUP]**](#dt:log-statement-with-likely-misspecified-log-level-s-and-log-groups-wlogmixup)
    
A specified log level of a `log` looks as though you meant to specify the log groups instead, and/or vice versa. For example:
```
// Log group used as log level, when the intention is instead to
// specify log groups and implicitly use log level 1
log spec_viol, some_log_group: ...;
// Log groups and log level mistakenly specified in reverse order
log info, (some_log_group | another_log_group), 2: ...;
// Log level used as log groups, when the intention is instead to
// specify the subsequent log level
log info, 2, 3: ...;

```

If you want to specify log groups, make sure to (explicitly) specify the log level beforehand. If you want to specify the subsequent log level, use `then` syntax.
```
log spec_viol, 1, some_log_group: ...;
log info, 2, (some_log_group | another_log_group): ...;
log info, 2 then 3: ...;

```

This warning is only enabled by default with Simics API version 7 or above (due to the compatibility feature `suppress_WLOGMIXUP`.) 

[******negative register offset:_N_ [WNEGOFFS]**](#dt:negative-register-offset-n-wnegoffs)
    
A negative integer expression is given as a register offset. Register offsets are unsigned 64-bit numbers, which means that a negative offset expression translates to a very large offset. 

[******no 'desc' parameter specified for device [WNSHORTDESC]**](#dt:no-desc-parameter-specified-for-device-wnshortdesc)
    
No short description string was specified using the 'desc' parameter. (This warning is disabled by default.) 

[******no documentation for '...' [WNDOC]**](#dt:no-documentation-for-wndoc)
    
No documentation string was specified for the attribute. (This warning is disabled by default.) 

[******no documentation for required attribute '...' [WNDOCRA]**](#dt:no-documentation-for-required-attribute-wndocra)
    
No documentation string was specified for a _required_ attribute. 

[******overriding non-throwing DML 1.4 method with throwing DML 1.2 method [WTHROWS_DML12]**](#dt:overriding-non-throwing-dml-1-4-method-with-throwing-dml-1-2-method-wthrows_dml12)
    
In DML 1.2, a method is by default permitted to throw an exception, while in DML 1.4, an annotation `throws` is required for that. So, if a method without annotations is ported to DML 1.4, it will no longer permit exceptions. If such method is overridden by a DML 1.2 file, then a non-throwing method is overridden by a potentially throwing method, which is normally a type error. However, this particular case is reduced to this warning. If an exception is uncaught in the override, then this will automatically be caught in runtime and an error message will be printed. 

[******potential leak of confidential information [WCONFIDENTIAL]**](#dt:potential-leak-of-confidential-information-wconfidential)
    
The object's name/qname is used as part of an expression in a context other than the log statement, which could potentially lead to the leak of confidential information. 

[******prefer 'is' statement outside template braces, 'template ... is (x, y) {' [WTEMPLATEIS]**](#dt:prefer-is-statement-outside-template-braces-template-is-x-y-wtemplateis)
    
In a template with methods marked `shared`, it is recommended that other templates are instantiated on the same line 

[******shifting away all data [WSHALL]**](#dt:shifting-away-all-data-wshall)
    
The result of the shift operation will always be zero. (This warning is disabled by default.) 

[******sizeof on a type is not legal, use sizeoftype instead [WSIZEOFTYPE]**](#dt:sizeof-on-a-type-is-not-legal-use-sizeoftype-instead-wsizeoftype)
    
The 'sizeof' operator is used on a type name, but expects an expression. Use the 'sizeoftype' operator for types. 

[******the time value of type '...' is implicitly converted to the type '...' expected by the specified time unit '...'. [WTTYPEC]**](#dt:the-time-value-of-type-is-implicitly-converted-to-the-type-expected-by-the-specified-time-unit-wttypec)
    
The delay value provided to an `after` call is subject to implicit type conversion which may be unexpected for certain types. To silence this warning, explicitly cast the delay value to the expected type. 

[******unused implementation of DML 1.2 method ...; enclose in #if (dml_1_2) ? [WUNUSED_DML12]**](#dt:unused-implementation-of-dml-1-2-method-enclose-in-if-dml_1_2-wunused_dml12)
    
A DML 1.4 file contains a method implementation that would override a library method in DML 1.2, but which is not part of the DML 1.4 library, because some methods have been renamed. For instance, implementing `read_access` in a register makes no sense in DML 1.4, because the method has been renamed to `read_register`.
If a DML 1.4 file contains common code that also is imported from DML 1.2 devices, then it may need to implement methods like `read_access` to get the right callbacks when compiled for DML 1.2. Such implementations can be placed inside `#if (dml_1_2) { }` blocks to avoid this warning. 

[******unused parameter ... contains ... [WREF]**](#dt:unused-parameter-contains-wref)
    
An unused parameter refers to an object that has not been declared.
This warning message will be replaced with a hard error in future major versions of Simics. 

[******unused: ... [WUNUSED]**](#dt:unused-wunused)
    
The object is not referenced anywhere. (This warning is disabled by default.; it typically causes many false warnings.) 

[******unused: ... methods are not called automatically for ... objects in ... [WUNUSEDDEFAULT]**](#dt:unused-methods-are-not-called-automatically-for-objects-in-wunuseddefault)
    
The object is not referenced anywhere but it matches a name of an object automatically referenced in another scope. This is the same as WUNUSED but only for known common errors and it will never be emitted if WUNUSED is enabled. 

[******very suspect pointer-to-pointer cast: the new base type has incompatible representation. This could lead to your code getting mangled by the C compiler, with unpredictable results. [WPCAST]**](#dt:very-suspect-pointer-to-pointer-cast-the-new-base-type-has-incompatible-representation-this-could-lead-to-your-code-getting-mangled-by-the-c-compiler-with-unpredictable-results-wpcast)
    
A pointer is cast to a base type which has incompatible representation compared to the original. Accessing the pointed-to object via the new pointer type will almost certainly constitute undefined behavior.
This warning is extremely limited in scope: don't rely on it to catch every bad pointer cast.
To silence this warning, first cast the pointer to `void *`, then cast it to the desired type.
## [A.2 Error Messages](#error-messages)
The messages are listed in alphabetical order; the corresponding tags are shown within brackets, e.g., `[ENBOOL]`. 

[******... [EERRSTMT]**](#dt:eerrstmt)
    
The source code contained a statement "`error;`", which forces a compilation error with the given message, or the standard message "forced compilation error in source code". 

[******... in template ... does not belong to the template type [ENSHARED]**](#dt:in-template-does-not-belong-to-the-template-type-enshared)
    
If a template provides an object that is not accessible from shared methods, such as an untyped parameter or a non-shared method, then that object's name is reserved within the scope of the shared method. I.e., if a shared method tries to access a symbol that isn't accessible, then ENSHARED is reported, even before looking for the symbol in the global scope. Section [3.7.2](language.html#shared-methods) describes which template symbols are accessible from a shared method. 

[******'...' has no member named '...' [EMEMBER]**](#dt:has-no-member-named-emember)
    
Attempt to access a nonexisting member of a compound data structure. 

[******'...' is a message component parameter, and can only be used as a direct argument to the callback method of the after statement [EAFTERMSGCOMPPARAM]**](#dt:is-a-message-component-parameter-and-can-only-be-used-as-a-direct-argument-to-the-callback-method-of-the-after-statement-eaftermsgcompparam)
    
Message component parameters bound by a hook-bound after statement can only be used as direct arguments to the specified callback method, and cannot be used in arbitrary expressions. 

[******'...' is a not a valid message component type for a hook, as it is or contains some ... [EHOOKTYPE]**](#dt:is-a-not-a-valid-message-component-type-for-a-hook-as-it-is-or-contains-some-ehooktype)
    
There are some minor restrictions to a hook's message component types. Anonymous structs and arrays of variable/unknown size are not supported. 

[******'.len' cannot be used with variable-length arrays [EVLALEN]**](#dt:len-cannot-be-used-with-variable-length-arrays-evlalen)
    
`.len` cannot be used with variable-length arrays 

[******Ambiguous invocation of default implementation [EAMBDEFAULT]**](#dt:ambiguous-invocation-of-default-implementation-eambdefault)
    
A method may not invoke its default implementation if multiple methods are overridden, and the template inheritance graph is insufficient to infer that one default implementation overrides the others. See section [3.10.3](language.html#calling-methods) for details. 

[******Ambiguous invocation of template-qualified method implementation call. '...' does not provide an implementation of '...', and inherits multiple unrelated implementations from its ancestor templates.... [EAMBTQMIC]**](#dt:ambiguous-invocation-of-template-qualified-method-implementation-call-does-not-provide-an-implementation-of-and-inherits-multiple-unrelated-implementations-from-its-ancestor-templates-eambtqmic)
    
A template-qualified method implementation call was made, when the template inheritance graph for specified template is insufficient to infer that one implementation overrides the others. To resolve this, the template-qualified method implementation call should instead be qualified with the specific ancestor template that has the desired implementation. 

[******Cannot declare '...' variable in an inline method [ESTOREDINLINE]**](#dt:cannot-declare-variable-in-an-inline-method-estoredinline)
    
You cannot declare session or saved variables in methods marked with 'inline' 

[******DML version ... does not support API version ... [ESIMAPI]**](#dt:dml-version-does-not-support-api-version-esimapi)
    
The DML file is written in a too old version of DML. Use the `--simics-api` option to use a sufficiently old Simics API. 

[******Declaration would result in conflicting attribute name [EATTRCOLL]**](#dt:declaration-would-result-in-conflicting-attribute-name-eattrcoll)
    
This error is signalled if two DML declarations would result in two Simics attributes being registered with the same name.
This most commonly happens when an attribute name is a result of the object hierarchy, and there is another object named similarly. For example, if a bank contains one register named `g_r` and a group `g` containing a register named `r`. 

[******Instantiating template ... requires abstract ... ... to be implemented [EABSTEMPLATE]**](#dt:instantiating-template-requires-abstract-to-be-implemented-eabstemplate)
    
If a template has any abstract methods or parameters, they must all be implemented when instantiating the template. 

[******No such provisional feature .... Valid values are: ... [ENOPROV]**](#dt:no-such-provisional-feature-valid-values-are-enoprov)
    
An invalid identifier was passed in the `provisional` statement. 

[******The interface struct member ... is not a function pointer [EIMPLMEMBER]**](#dt:the-interface-struct-member-is-not-a-function-pointer-eimplmember)
    
A method in an `implement` object corresponds to a struct member that isn't a function pointer 

[******Too many loggroup declarations. A maximum of 63 log groups (61 excluding builtins) may be declared per device. [ELOGGROUPS]**](#dt:too-many-loggroup-declarations-a-maximum-of-63-log-groups-61-excluding-builtins-may-be-declared-per-device-eloggroups)
    
Too many log groups were declared. A device may have a maximum of 63 `loggroup` declarations (61 excluding the built-in `Register_Read` and `Register_Write` loggroups). 

[******Unknown pragma: ... [EPRAGMA]**](#dt:unknown-pragma-epragma)
    
An unknown pragma was specified 

[******abstract method ... overrides existing method [EAMETH]**](#dt:abstract-method-overrides-existing-method-eameth)
    
An abstract method cannot override another method. 

[******an anonymous ... cannot implement interfaces [EANONPORT]**](#dt:an-anonymous-cannot-implement-interfaces-eanonport)
    
An `implement` definition can only exist in a port or bank that has a name. 

[******array has too many elements (_N_ >= 2147483648) [EASZLARGE]**](#dt:array-has-too-many-elements-n-2147483648-easzlarge)
    
Object arrays with huge dimensions are not allowed; the product of dimension sizes must be smaller than 231. 

[******array index out of bounds [EOOB]**](#dt:array-index-out-of-bounds-eoob)
    
The used index is outside the defined range. 

[******array range must start at 0 [EZRANGE]**](#dt:array-range-must-start-at-0-ezrange)
    
An array index range must start at zero. 

[******array size is less than 1 [EASZR]**](#dt:array-size-is-less-than-1-easzr)
    
An array must have at least one element. 

[******array upper bound is not a constant integer: ... [EASZVAR]**](#dt:array-upper-bound-is-not-a-constant-integer-easzvar)
    
The size of an array must be a constant integer. 

[******assignment to constant [ECONST]**](#dt:assignment-to-constant-econst)
    
The lvalue that is assigned to is declared as a `const` and thus can't be assigned to. 

[******attempt to override non-default method '...' [EDMETH]**](#dt:attempt-to-override-non-default-method-edmeth)
    
A method can only be overridden if it is declared as `default` 

[******attempt to override non-shared method ... with shared method [ETMETH]**](#dt:attempt-to-override-non-shared-method-with-shared-method-etmeth)
    
A shared method cannot override a non-shared method 

[******attribute has no get or set method [EANULL]**](#dt:attribute-has-no-get-or-set-method-eanull)
    
An attribute must have a set or a get method to be useful. 

[******attribute type undefined: ... [EATYPE]**](#dt:attribute-type-undefined-eatype)
    
Either the `attr_type` or the `type` parameter of the attribute must be specified. 

[******bad declaration of automatic parameter '...' [EAUTOPARAM]**](#dt:bad-declaration-of-automatic-parameter-eautoparam)
    
Some parameters are predefined by DML, using the `auto` keyword. Such parameters may only be declared by the standard library, and they may not be overridden. 

[******bit range of field '...' outside register boundaries [EBITRR]**](#dt:bit-range-of-field-outside-register-boundaries-ebitrr)
    
The bit range of a field can only use bits present in the register. 

[******bit range of field '...' overlaps with field '...' [EBITRO]**](#dt:bit-range-of-field-overlaps-with-field-ebitro)
    
The fields of a register must not overlap. 

[******bitslice size of ... bits is not between 1 and 64 [EBSSIZE]**](#dt:bitslice-size-of-bits-is-not-between-1-and-64-ebssize)
    
Bit slices cannot be larger than 64 bits. 

[******bitslice with big-endian bit order and uncertain bit width [EBSBE]**](#dt:bitslice-with-big-endian-bit-order-and-uncertain-bit-width-ebsbe)
    
A big-endian bit slice can only be done on an expression whose type is explicitly defined, such as a local variable or a register field. 

[******call to method '...' in unsupported context [EAPPLYMETH]**](#dt:call-to-method-in-unsupported-context-eapplymeth)
    
Calls to inline methods, methods that may throw, or methods that have multiple output parameters cannot be used as arbitrary expressions. In DML 1.2, any such method must be called via the `call` or `inline` statements, and in DML 1.4 any such method must be called either as a standalone statement, or as an initializer (e.g., RHS of an assignment or argument of a `return` statement). 

[******cannot access device instance in device independent context [EINDEPENDENTVIOL]**](#dt:cannot-access-device-instance-in-device-independent-context-eindependentviol)
    
Expressions that depend on values stored in a device instance cannot be evaluated in contexts where the device instance is not available. This is within static contexts — for example when initializing typed template parameters — or within independent methods. 

[******cannot assign to inlined parameter: '...' [EASSINL]**](#dt:cannot-assign-to-inlined-parameter-eassinl)
    
The target of the assignment is a method parameter that has been given a constant or undefined value when inlining the method. 

[******cannot assign to this expression: '...' [EASSIGN]**](#dt:cannot-assign-to-this-expression-eassign)
    
The target of the assignment is not an l-value, and thus cannot be assigned to. 

[******cannot convert this method reference to a function pointer [ESTATICEXPORT]**](#dt:cannot-convert-this-method-reference-to-a-function-pointer-estaticexport)
    
A method reference can only be converted to a function pointer if the method is non-inline, non-shared, non-throwing, and declared outside an object array. 

[******cannot define both 'allocate_type' parameter and local data objects [EATTRDATA]**](#dt:cannot-define-both-allocate_type-parameter-and-local-data-objects-eattrdata)
    
Specifying `allocate_type` and using 'data' declarations in the same attribute object is not allowed. 

[******cannot export this method [EEXPORT]**](#dt:cannot-export-this-method-eexport)
    
Can only export non-inline, non-shared, non-throwing methods declared outside object arrays. 

[******cannot find file to import: ... [EIMPORT]**](#dt:cannot-find-file-to-import-eimport)
    
The file to imported could not be found. Use the `-I` option to specify additional directories to search for imported files. 

[******cannot import file containing device declaration [EDEVIMP]**](#dt:cannot-import-file-containing-device-declaration-edevimp)
    
Source files that are used with `import` directives may not contain `device` declarations. 

[******cannot use a register with fields as a value: ... [EREGVAL]**](#dt:cannot-use-a-register-with-fields-as-a-value-eregval)
    
When a register has been specified with explicit fields, you have to use the `get` and `set` methods to access the register as a single value. 

[******cannot use an array as a value: '...' [EARRAY]**](#dt:cannot-use-an-array-as-a-value-earray)
    
A whole array cannot be used as a single value. 

[******cannot use endian integer as argument type in declaration [EEARG]**](#dt:cannot-use-endian-integer-as-argument-type-in-declaration-eearg)
    
Function and method arguments in declarations cannot be of endian integer type. 

[******cannot use variable index in a constant list [EAVAR]**](#dt:cannot-use-variable-index-in-a-constant-list-eavar)
    
Indexing into constant lists can only be done with constant indexes. 

[******checkpointable attribute missing set or get method [EACHK]**](#dt:checkpointable-attribute-missing-set-or-get-method-eachk)
    
An attribute must have set and get methods to be checkpointable. This attribute has neither, and the 'configuration' parameter is either "required" or "optional". 

[******circular dependency in parameter value [ERECPARAM]**](#dt:circular-dependency-in-parameter-value-erecparam)
    
The value of a parameter may not reference the parameter itself, neither directly nor indirectly. 

[******conditional 'in each' is not allowed [ECONDINEACH]**](#dt:conditional-in-each-is-not-allowed-econdineach)
    
It is not permitted to have an `in each` statement directly inside an `if` conditional. 

[******conditional parameters are not allowed [ECONDP]**](#dt:conditional-parameters-are-not-allowed-econdp)
    
It is not permitted to declare a parameter directly inside an `if` conditional. 

[******conditional templates are not allowed [ECONDT]**](#dt:conditional-templates-are-not-allowed-econdt)
    
It is not permitted to use a template directly inside an `if` conditional. 

[******conflicting default definitions for method '...' [EDDEFMETH]**](#dt:conflicting-default-definitions-for-method-eddefmeth)
    
If a method has two default implementations, then at least one of them must be defined in a template. 

[******conflicting definitions of ... when instantiating ... and ... [EAMBINH]**](#dt:conflicting-definitions-of-when-instantiating-and-eambinh)
    
If a method or parameter has multiple definitions, then there must be a unique definition that overrides all other definitions. 

[******const qualified function type [ECONSTFUN]**](#dt:const-qualified-function-type-econstfun)
    
A function type cannot be `const` qualified; 

[******const qualifier discarded [EDISCONST]**](#dt:const-qualifier-discarded-edisconst)
    
A pointer to a constant value has been assigned to a pointer to a non-constant. 

[******continue is not possible here [ECONTU]**](#dt:continue-is-not-possible-here-econtu)
    
A `continue` statement cannot be used in a `#foreach` or `#select` statement. 

[******cyclic import [ECYCLICIMP]**](#dt:cyclic-import-ecyclicimp)
    
A DML file imports itself, either directly or indirectly. 

[******cyclic template inheritance [ECYCLICTEMPLATE]**](#dt:cyclic-template-inheritance-ecyclictemplate)
    
A template inherits from itself, either directly or indirectly. 

[******declaration of vect type without simics_util_vect provisional [EOLDVECT]**](#dt:declaration-of-vect-type-without-simics_util_vect-provisional-eoldvect)
    
`vect` types are only permitted if the [`simics_util_vect` provisional feature](provisional-auto.html#simics_util_vect) is enabled. 

[******duplicate bank function number:_N_ [EDBFUNC]**](#dt:duplicate-bank-function-number-n-edbfunc)
    
The device contains two differently-named banks that use the same function number. 

[******duplicate definition of variable '...' [EDVAR]**](#dt:duplicate-definition-of-variable-edvar)
    
A local variable has more than one definition in the same code block. 

[******duplicate method parameter name '...' [EARGD]**](#dt:duplicate-method-parameter-name-eargd)
    
All parameter names of a method must be distinct. 

[******expression may not depend on the index variable ... [EIDXVAR]**](#dt:expression-may-not-depend-on-the-index-variable-eidxvar)
    
Expressions that are evaluated statically to constants cannot have different values for different elements in a register array. This includes, for instance, the `allocate` parameter in registers and fields, and object-level `if` statements. 

[******file not found [ENOFILE]**](#dt:file-not-found-enofile)
    
The main input file could not be found. 

[******heterogeneous bitsize in field array [EFARRSZ]**](#dt:heterogeneous-bitsize-in-field-array-efarrsz)
    
The bit width must be identical across the elements of a field array. 

[******illegal 'after' statement bound to hook '...': hook has _N_ message components, but _N_ message component parameters are given [EAFTERHOOK]**](#dt:illegal-after-statement-bound-to-hook-hook-has-n-message-components-but-n-message-component-parameters-are-given-eafterhook)
    
An illegal hook-bound `after` statement was specified. The number of message component parameters must be equal to the number of message components of the hook. 

[******illegal 'after' statement... with callback '....send_now': every message component of '...' ...must be of serializable type... [EAFTERSENDNOW]**](#dt:illegal-after-statement-with-callback-send_now-every-message-component-of-must-be-of-serializable-type-eaftersendnow)
    
An illegal `after` statement was specified where the callback is `send_now` of a hook. Every message component type of the hook must be serializable (unless that component is provided through a message component parameter of the `after` statement, if the `after` statement is attaching the callback to another hook.) 

[******illegal 'after' statement... with callback method '...': ... [EAFTER]**](#dt:illegal-after-statement-with-callback-method-eafter)
    
An illegal `after` statement was specified. The method callback specified may not have any output parameters/return values. If the after is with a time delay or bound to a hook, every input parameter must be of serializable type (unless that input parameter receives a message component of a hook). 

[******illegal attribute name: ... [EANAME]**](#dt:illegal-attribute-name-eaname)
    
This name is not available as the name of an attribute, since it is used for an automatically added attribute. 

[******illegal bitfields definition: ... [EBFLD]**](#dt:illegal-bitfields-definition-ebfld)
    
A `bitfield` declaration must have an integer type that matches the width of the field. 

[******illegal bitorder: '...' [EBITO]**](#dt:illegal-bitorder-ebito)
    
The specified bit-order is not allowed. 

[******illegal bitslice operation [EBSLICE]**](#dt:illegal-bitslice-operation-ebslice)
    
A bitslice operation was attempted on an expression that is not an integer. 

[******illegal cast to '...' [ECAST]**](#dt:illegal-cast-to-ecast)
    
The cast operation was not allowed. It is illegal to cast to void. 

[******illegal comparison; mismatching types [EILLCOMP]**](#dt:illegal-comparison-mismatching-types-eillcomp)
    
The values being compared do not have matching types. 

[******illegal function application of '...' [EAPPLY]**](#dt:illegal-function-application-of-eapply)
    
The applied value is not a function. 

[******illegal increment/decrement operation [EINC]**](#dt:illegal-increment-decrement-operation-einc)
    
An increment or decrement operation can only be performed on simple lvalues such as variables. 

[******illegal interface method reference: ... [EIFREF]**](#dt:illegal-interface-method-reference-eifref)
    
Interface function calls must be simple references to the method. 

[******illegal layout definition: ... [ELAYOUT]**](#dt:illegal-layout-definition-elayout)
    
The type of a member of a `layout` declaration must be an integer or bitfield with a bit width that is a multiple of 8, or another layout. 

[******illegal operands to binary '...' [EBINOP]**](#dt:illegal-operands-to-binary-ebinop)
    
One or both of the operands have the wrong type for the given binary operator. 

[******illegal pointer type: ... [EINTPTRTYPE]**](#dt:illegal-pointer-type-eintptrtype)
    
Pointer types that point to integers with a bit width that is not a power of two are not allowed. 

[******illegal register size for '...' [EREGISZ]**](#dt:illegal-register-size-for-eregisz)
    
The specified register size is not allowed. Possible values are 1-8. 

[******illegal type: array of functions [EFUNARRAY]**](#dt:illegal-type-array-of-functions-efunarray)
    
It is illegal to express an array type where the base type is a function type. 

[******illegal use of void type [EVOID]**](#dt:illegal-use-of-void-type-evoid)
    
The type `void` is not a value, and thus cannot be used as the type of e.g. a variable or struct member 

[******illegal value for parameter '...' [EPARAM]**](#dt:illegal-value-for-parameter-eparam)
    
The parameter is not bound to a legal value. 

[******incompatible array declarations: ... [EAINCOMP]**](#dt:incompatible-array-declarations-eaincomp)
    
The array has been declared more than once, in an incompatible way. 

[******incompatible extern declarations for '...': type mismatch [EEXTERNINCOMP]**](#dt:incompatible-extern-declarations-for-type-mismatch-eexternincomp)
    
Multiple `extern` declarations with mismatching types are given for the same identifier. 

[******incompatible method definitions: ... [EMETH]**](#dt:incompatible-method-definitions-emeth)
    
The default implementation is overridden by an implementation with different input/output parameters. 

[******incompatible version (...) while compiling a ... device [EVERS]**](#dt:incompatible-version-while-compiling-a-device-evers)
    
A device declared to be written in one DML language version tried to import a file written in an incompatible language version. 

[******invalid data initializer: ... [EDATAINIT]**](#dt:invalid-data-initializer-edatainit)
    
An invalid initializer was detected. The error message provides the detailed information. 

[******invalid expression: '...' [EINVALID]**](#dt:invalid-expression-einvalid)
    
The expression does not produce a proper value. 

[******invalid log type: '...' [ELTYPE]**](#dt:invalid-log-type-eltype)
    
Log-statement type must be one of `info`, `warning`, `error`, `spec_viol`, and `unimpl`. 

[******invalid name parameter value: '...' [ENAMEID]**](#dt:invalid-name-parameter-value-enameid)
    
The name parameter does not follow identifier syntax. 

[******invalid override of non-default declaration ... [EINVOVER]**](#dt:invalid-override-of-non-default-declaration-einvover)
    
Only default declarations of parameters can be overridden. 

[******invalid template-qualified method implementation call made via a value of template type: '...' does not provide nor inherit a shared implementation of '...' [ENSHAREDTQMIC]**](#dt:invalid-template-qualified-method-implementation-call-made-via-a-value-of-template-type-does-not-provide-nor-inherit-a-shared-implementation-of-ensharedtqmic)
     A template-qualified method implementation call via a value of template type, including when `this.templates` is used within the body of a `shared` method, can only be done if the specified template provides or inherits a `shared` implementation of the specified method. If an implementation is never provided or inherited by the template, or the template provides or inherits a non-`shared` implementation, then the call can't be made. For example, the following is permitted: ```
template t {
  shared method m();
}
template u is t {
  shared method m() default {
    log info: "implementation from 'u'";
  }
}
template v is t {
  shared method m() default {
    log info: "implementation from 'v'";
  }
}
template uv is (u, v) {
  shared method m() {
    // 'this' is a value of the template type 'uv'
    this.templates.u.m();
    // Equivalent to 'this.templates.v.m()'
    templates.v.m();
  }
}

```
But the following is not: ```
template t {
  shared method m();
}
template u is t {
  shared method m() default {
    log info: "implementation from 'u'";
  }
}
template v is t {
  method m() default {
    log info: "implementation from 'v'";
  }
}
template uv is (u, v) {
  // Indirection as a shared implementation is not allowed to override a
  // non-shared implementation, but even if it were...
  method m() {
    m_impl();
  }
  shared method m_impl() {
    this.templates.u.m();
    // This is rejected because the implementation of 'm' provided by
    // 'v' is not shared.
    this.templates.v.m();
  }
}

```
As a result, resolving a conflict between a non-`shared` method implementation and a `shared` method implementation can typically only be done by having most parts of the overriding implementation be non-`shared`: ```
template uv is (u, v) {
  method m() {
    // OK; 'this' is a compile-time reference to the object
    // instantiating the template rather than a value of template type.
    this.templates.u.m();
    this.templates.v.m();
  }
}

```
Alternatively, a new `shared` method with non-`shared` implementation can be declared to allow access to the specific non-`shared` implementation needed (at the cost of increasing the memory overhead needed for the template type): ```
template uv is (u, v) {
  method m() {
    m_impl();
  }
  shared method m_impl_by_v();
  method m_impl_by_v() {
    this.templates.v.m();
  }
  shared method m_impl() {
    this.templates.u.m();
    // OK
    m_impl_by_v();
  }
}

```


[******invalid template-qualified method implementation call, '...' does not instantiate '...' [ETQMIC]**](#dt:invalid-template-qualified-method-implementation-call-does-not-instantiate-etqmic)
     A template-qualified method implementation call can only be done if the specified template is actually instantiated by the object. 

[******invalid template-qualified method implementation call, '...' does not provide nor inherit an implementation of a method '...'... [EMEMBERTQMIC]**](#dt:invalid-template-qualified-method-implementation-call-does-not-provide-nor-inherit-an-implementation-of-a-method-emembertqmic)
     A template-qualified method implementation call can only be done if the specified template actually does provide or inherit an implementation of the named method for the object instantiating the template. That the template provides or inherits an abstract declaration of the method is not sufficient. Apart from more mundane causes (e.g. misspellings), this error could happen if all implementations that the specified template may provide/inherit end up not being provided to the object instantiating the template, due to every implementation being eliminated by an `#if` statement. 

[******invalid template-qualified method implementation call, '...' not a subtemplate of '...' [ETTQMIC]**](#dt:invalid-template-qualified-method-implementation-call-not-a-subtemplate-of-ettqmic)
     A template-qualified method implementation call via a value of template type, including when `this.templates` is used within the body of a `shared` method, can only be done if the specified template is an ancestor template of the template type, the `object` template type, or the template type itself. 

[******invalid upcast, ... not a subtemplate of ... [ETEMPLATEUPCAST]**](#dt:invalid-upcast-not-a-subtemplate-of-etemplateupcast)
     When casting to a template type, the source expression must be either an object implementing the template, or an expression whose type is a subtemplate of the target type. 

[******log level must be ... [ELLEV]**](#dt:log-level-must-be-ellev)
     The log level given in a log statement must be an integer between 1 and 4, or 1 and 5 for a subsequent log level (`then ...`), unless the log kind is one of "warning", "error", or "critical", in which case it must be 1 (or 5 for subsequent log level). 

[******malformed format string: unknown format at position _N_ [EFORMAT]**](#dt:malformed-format-string-unknown-format-at-position-n-eformat)
     The log-statement format string is malformed. 

[******malformed switch statement: ... [ESWITCH]**](#dt:malformed-switch-statement-eswitch)
     A switch statement must start with a `case` label, and there may be at most one `default` label which must appear after all `case` labels 

[******method return type declarations may not be named: ... [ERETARGNAME]**](#dt:method-return-type-declarations-may-not-be-named-eretargname)
     In DML 1.4, the output arguments of a method are anonymous 

[******missing device declaration [EDEVICE]**](#dt:missing-device-declaration-edevice)
     The main source file given to the DML compiler must contain a `device` declaration. 

[******missing return statement in method with output argument [ENORET]**](#dt:missing-return-statement-in-method-with-output-argument-enoret)
     If a method has output arguments, then control flow may not reach the end of the method. Either an explicit value must be returned in a return statement, or the execution must be aborted by an exception or assertion failure. Note that DMLC's control flow analysis is rather rudimentary, and can issue this error on code that provably will return. In this case, the error message can be silenced by adding `assert false;` to the end of the method body. 

[******more than one output parameter not allowed in interface methods [EIMPRET]**](#dt:more-than-one-output-parameter-not-allowed-in-interface-methods-eimpret)
     Methods within an `interface` declaration may have only have zero or one output parameter. 

[******name collision on '...' [ENAMECOLL]**](#dt:name-collision-on-enamecoll)
     The name is already in use in the same scope. 

[******negative size (_N_ < _N_) of bit range for '...' [EBITRN]**](#dt:negative-size-n-n-of-bit-range-for-ebitrn)
     The size of the bit range must be positive. Note that the [msb:lsb] syntax requires that the most significant bit (msb) is written to the left of the colon, regardless of the actual bit numbering used. 

[******no assignment to parameter '...' [ENPARAM]**](#dt:no-assignment-to-parameter-enparam)
     The parameter has been declared, but is not assigned a value or a default value. 

[******no default implementation [ENDEFAULT]**](#dt:no-default-implementation-endefault)
     The default implementation of a method was invoked, but there was no default implementation. 

[******no return type [ERETTYPE]**](#dt:no-return-type-erettype)
     The type of the return value (if any) must be specified for methods that implement interfaces. 

[******no type for ... parameter '...' [ENARGT]**](#dt:no-type-for-parameter-enargt)
     Methods that are called must have data type declarations for all their parameters. (Methods that are only inlined do not need this.) 

[******non-boolean condition: '...' of type '...' [ENBOOL]**](#dt:non-boolean-condition-of-type-enbool)
     Conditions must be properly boolean expressions; e.g., "`if (i == 0)`" is allowed, but "`if (i)`" is not, if `i` is an integer. 

[******non-constant expression: ... [ENCONST]**](#dt:non-constant-expression-enconst)
     A constant expression was expected. 

[******non-constant parameter, or circular parameter dependencies: '...' [EVARPARAM]**](#dt:non-constant-parameter-or-circular-parameter-dependencies-evarparam)
     The value assigned to the parameter is not a well-defined constant. 

[******non-constant strings cannot be concatenated using '+' [ECSADD]**](#dt:non-constant-strings-cannot-be-concatenated-using-ecsadd)
     Non-constant strings cannot be concatenated using `+`. 

[******not a list: ... [ENLST]**](#dt:not-a-list-enlst)
     A list was expected. 

[******not a method: '...' [ENMETH]**](#dt:not-a-method-enmeth)
     A method name was expected. This might be caused by using `call` or `inline` on something that counts as a C function rather than a method. 

[******not a pointer: ... (...) [ENOPTR]**](#dt:not-a-pointer-enoptr)
     A pointer value was expected. 

[******not a value: ... [ENVAL]**](#dt:not-a-value-enval)
     Only some objects can be used as values directly. An attribute can only be accessed directly as a value if it has been declared using the `allocate_type` parameter. 

[******nothing to break from [EBREAK]**](#dt:nothing-to-break-from-ebreak)
     A `break` statement can only be used inside a loop or switch construct. 

[******nothing to continue [ECONT]**](#dt:nothing-to-continue-econt)
     A `continue` statement can only be used inside a loop construct. 

[******object expected: ... [ENOBJ]**](#dt:object-expected-enobj)
     A reference to an object was expected. 

[******object is not allocated at run-time: ... [ENALLOC]**](#dt:object-is-not-allocated-at-run-time-enalloc)
     An object which is not allocated at run-time cannot be referenced as a run-time value. 

[******operand of '...' is not an lvalue [ERVAL]**](#dt:operand-of-is-not-an-lvalue-erval)
     The operand of `sizeof`, `typeof` and `&` must be a lvalue. 

[******overlapping registers: '...' and '...' [EREGOL]**](#dt:overlapping-registers-and-eregol)
     The registers are mapped to overlapping address ranges. 

[******parameter '...' not declared previously. To declare and define a new parameter, use the ':...' syntax. [ENOVERRIDE]**](#dt:parameter-not-declared-previously-to-declare-and-define-a-new-parameter-use-the-syntax-enoverride)
     When the `explict_param_decls` provisional feature is enabled, parameter definitions written using `=` and `default` are only accepted if the parameter has already been declared. To declare and define a new parameter not already declared, use the `:=` or `:default` syntax. 

[******passing const reference for nonconst parameter ... in ... [ECONSTP]**](#dt:passing-const-reference-for-nonconst-parameter-in-econstp)
     C function called with a pointer to a constant value for a parameter declared without const in the prototype. 

[******recursive inline of ... [ERECUR]**](#dt:recursive-inline-of-erecur)
     Methods may not be inlined recursively. 

[******recursive type definition of ... [ETREC]**](#dt:recursive-type-definition-of-etrec)
     The definition of a structure type can not have itself as direct or indirect member. 

[******reference to unknown object '...' [EREF]**](#dt:reference-to-unknown-object-eref)
     The referenced object has not been declared. 

[******right-hand side operand of '...' is zero [EDIVZ]**](#dt:right-hand-side-operand-of-is-zero-edivz)
     The right-hand side of the given / or % operator is always zero. 

[******saved variable declared with (partially) const-qualified type ... [ESAVEDCONST]**](#dt:saved-variable-declared-with-partially-const-qualified-type-esavedconst)
     Declaring a saved variable with a type that is (partially) const-qualified is not allowed, as they can be modified due to checkpoint restoration. 

[******shift with negative shift count: '... [ESHNEG]**](#dt:shift-with-negative-shift-count-eshneg)
     The right-hand side operand to a shift operator must not be negative. 

[******struct declaration not allowed in a ... [EANONSTRUCT]**](#dt:struct-declaration-not-allowed-in-a-eanonstruct)
     Declarations of new structs are not permitted in certain contexts, such as method arguments, `new` expressions, `sizeoftype` expressions and `cast` expressions. 

[******struct member is a function [EFUNSTRUCT]**](#dt:struct-member-is-a-function-efunstruct)
     A member of a struct cannot have a function type. 

[******struct or layout with no fields [EEMPTYSTRUCT]**](#dt:struct-or-layout-with-no-fields-eemptystruct)
     A struct or layout type must have at least one field. This restriction does not apply to structs declared in a `extern typedef`. 

[******syntax error...... [ESYNTAX]**](#dt:syntax-error-esyntax)
     The code is malformed. 

[******the parameter '...' has already been declared (':...' syntax may not be used for parameter overrides) [EOVERRIDE]**](#dt:the-parameter-has-already-been-declared-syntax-may-not-be-used-for-parameter-overrides-eoverride)
     When the `explict_param_decls` provisional feature is enabled, any parameter declared via `:=` or `:default` may not already have been declared. This means `:=` or `:default` syntax can't be used to override existing parameter declarations (not even those lacking a definition of the parameter.) 

[******the size of dimension _N_ (with index variable '...') is never defined [EAUNKDIMSIZE]**](#dt:the-size-of-dimension-n-with-index-variable-is-never-defined-eaunkdimsize)
     The size of an array dimension of an object array must be defined at least once across all declarations of that object array. 

[******this object is not allowed here [ENALLOW]**](#dt:this-object-is-not-allowed-here-enallow)
     Many object types have limitations on the contexts in which they may appear. 

[******trying to get a member of a non-struct: '...' of type '...' [ENOSTRUCT]**](#dt:trying-to-get-a-member-of-a-non-struct-of-type-enostruct)
     The left-hand side operand of the `.` operator is not of struct type. 

[******trying to index something that isn't an array: '...' [ENARRAY]**](#dt:trying-to-index-something-that-isn-t-an-array-enarray)
     Indexing can only be applied to arrays, integers (bit-slicing), and lists. 

[******typed parameter definitions may not contain independent methods calls [ETYPEDPARAMVIOL]**](#dt:typed-parameter-definitions-may-not-contain-independent-methods-calls-etypedparamviol)
     Independent method calls are not allowed within the definitions of typed parameters. 

[******uncaught exception [EBADFAIL]**](#dt:uncaught-exception-ebadfail)
     An exception is thrown in a context where it will not be caught. 

[******uncaught exception in call to DML 1.2 method '...' [EBADFAIL_dml12]**](#dt:uncaught-exception-in-call-to-dml-1-2-method-ebadfail_dml12)
     If a DML 1.2 method lacks a `nothrow` annotation, and a non-throwing DML 1.4 method calls it, then DMLC will analyze whether the method call can actually cause an exception. If it can, this error is reported; if not, the call is permitted. For this error, a 1.2 method counts as throwing if it throws an exception, or calls a `throws` marked 1.4 method, or (recursively) if it invokes a method that counts as throwing. A call or throw statement inside a `try` block does not cause the method to count as throwing. The methods `attribute.set`, `bank.read_access` and `bank.write_access` count as throwing even if they don't throw. This error is normally reported while porting common DML 1.2 code to DML 1.4: most 1.2 methods are not meant to throw exceptions, and when converted to DML 1.4 this becomes a strict requirement unless the method is annotated with the `throws` keyword. The remedy for this error message is normally to insert a `try` block around some call along the throwing call chain, with a `catch` block that handles the exception gracefully. The `try` block should usually be as close as possible to the `throw` in the call chain. 

[******undefined register size for '...' [EREGNSZ]**](#dt:undefined-register-size-for-eregnsz)
     All registers must have a specified constant size. 

[******undefined value: '...' [EUNDEF]**](#dt:undefined-value-eundef)
     Caused by an attempt to generate code for an expression that contains the `undefined` value. 

[******unknown identifier: '...' [EIDENT]**](#dt:unknown-identifier-eident)
     The identifier has not been declared anywhere. 

[******unknown interface type: ... [EIFTYPE]**](#dt:unknown-interface-type-eiftype)
     The interface datatype is unknown. 

[******unknown template: '...' [ENTMPL]**](#dt:unknown-template-entmpl)
     The template has not been defined. 

[******unknown type of expression [ENTYPE]**](#dt:unknown-type-of-expression-entype)
     This expression has an unknown type. 

[******unknown type: '...' [ETYPE]**](#dt:unknown-type-etype)
     The data type is not defined in the DML code. 

[******unknown value identifier in the operand of 'sizeof': '...' [EIDENTSIZEOF]**](#dt:unknown-value-identifier-in-the-operand-of-sizeof-eidentsizeof)
     A variant of the EIDENT message exclusive to usages of `sizeof`: it is emitted when the operand of `sizeof` makes use of an identifier which is not present in value scope, but _is_ present in type scope. This likely means `sizeof` was used when `sizeoftype` was intended. 

[******unserializable type: ... [ESERIALIZE]**](#dt:unserializable-type-eserialize)
     Some complex types, in particular most pointer types, cannot be automatically checkpointed by DML, and are therefore disallowed in contexts such as `saved` declarations. 

[******value of parameter ... is not yet initialized [EUNINITIALIZED]**](#dt:value-of-parameter-is-not-yet-initialized-euninitialized)
     Some parameters that are automatically supplied by DML cannot be accessed in early stages of compilation, such as in object-level if statements. 

[******variable length array declared with (partially) const-qualified type [EVLACONST]**](#dt:variable-length-array-declared-with-partially-const-qualified-type-evlaconst)
     Variable length arrays may not be declared const-qualified or with a base type that is (partially) const-qualified. 

[******variable or field declared ... [EVARTYPE]**](#dt:variable-or-field-declared-evartype)
     A variable has been declared with a given type but the type is not acceptable. 

[******wrong number of ... arguments [EARG]**](#dt:wrong-number-of-arguments-earg)
     The number of input/output arguments given in the call differs from the method definition. 

[******wrong number of arguments for format string [EFMTARGN]**](#dt:wrong-number-of-arguments-for-format-string-efmtargn)
     The log-statement has too few or too many arguments for the given format string. 

[******wrong number of return value recipients: Expected _N_ , got _N_ [ERETLVALS]**](#dt:wrong-number-of-return-value-recipients-expected-n-got-n-eretlvals)
     The number of return value recipients differs from the number of values the called method returns. 

[******wrong number of return values: Expected _N_ , got _N_ [ERETARGS]**](#dt:wrong-number-of-return-values-expected-n-got-n-eretargs)
     The number of return values in a return statement must match the number of outputs in the method. 

[******wrong type [EBTYPE]**](#dt:wrong-type-ebtype)
     An expression had the wrong type. 

[******wrong type for '...' operator [EINCTYPE]**](#dt:wrong-type-for-operator-einctype)
     The prefix and postfix increment/decrement operators can only be used on integer and pointer expressions. 

[******wrong type for argument _N_ of format string ('...') [EFMTARGT]**](#dt:wrong-type-for-argument-n-of-format-string-efmtargt)
     Argument type mismatch in a log-statement format string. 

[******wrong type for initializer [EASTYPE]**](#dt:wrong-type-for-initializer-eastype)
     The target of an initializer is incompatible with the type of the initializer. 

[******wrong type for parameter ... in ... call [EPTYPE]**](#dt:wrong-type-for-parameter-in-call-eptype)
     The data type of the argument value given for the mentioned method or function parameter differs from the function prototype. 

[******wrong type in ... parameter '...' when ... '...' [EARGT]**](#dt:wrong-type-in-parameter-when-eargt)
     The data type of the argument value given for the mentioned method parameter differs from the method definition.
[5 Standard Templates](utility.html) [B Provisional language features](provisional-auto.html)
