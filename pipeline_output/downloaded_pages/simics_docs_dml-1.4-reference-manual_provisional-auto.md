[A Messages](messages.html) [C Managing deprecated language features](deprecations-auto.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [B Provisional language features](#provisional-language-features)
Sometimes, we may choose to extend the DML compiler with a feature before it is ready to be fully incorporated into the language. This can happen for different reasons, e.g. if the design is not fully evaluated or if the feature is backward incompatible. Currently, all provisional features are enabled on a per-file basis, by adding `provisional _feature_name_, _other_feature_name_;`just after the`dml 1.4;` statement.
Provisional features can come in two flavours:
  * _Stable_ provisional features have a proven design and are expected to remain pretty stable over time. Details in semantics may still change between versions, but if we decide to make a significant incompatible change to a supported provisional, then we will create a second version of the provisional, under a new name, and keep both versions in parallel for some time. It can make sense to use supported provisional features in production code.
  * _Unstable_ provisional features are expected to undergo significant incompatible changes over time, and are generally exposed to allow a dedicated team of modelers to evaluate an early design. It can be used to play around with, but should not be used in production code without first communicating with the DML team.


## [B.1 List of stable provisional features](#list-of-stable-provisional-features) 

[`explicit_param_decls`](#dt:explicit_param_decls)
    
This feature extends the DML syntax for parameter definitions to distinguish between an intent to declare a new parameter, and an intent to override an existing parameter (including when providing a definition for an abstract parameter). This distinction allows DML to capture misspelled parameter overrides as compile errors.
The following new forms are introduced to mark the intent of declaring a new parameter:
  * For typed parameters, `param NAME: TYPE = value;` is essentially a shorthand for
```
param NAME: TYPE;
param NAME = value;

```

and similarly, `param NAME: TYPE default value;` is essentially a shorthand for
```
param NAME: TYPE;
param NAME default value;

```

  * For untyped parameters, `param NAME := value;` is essentially a shorthand for
```
param NAME;
param NAME = value;

```

and similarly `param :default value;` is essentially a shorthand for
```
param NAME;
param NAME default value;

```



If one of these forms is used for overriding an existing parameter, then DMLC will signal an error, because the declaration was not intended as an override. DMLC will also signal an error if a plain `param NAME = value;` or `param NAME default value;` declaration appears that does not override a pre-existing parameter.
In some rare cases, you may need to declare a parameter without knowing if it's an override or a new parameter. In this case, one can accompany a `param NAME = value;` or `param NAME default value;` declaration with a `param NAME;` declaration in the same scope/rank. This marks that the parameter assignment may be either an override or a new parameter, and no error will be printed.
Enabling the `explicit_param_decls` feature in a file only affects the parameter definitions specified in that file. 

[`simics_util_vect`](#dt:simics_util_vect)
     This feature enables the `vect` type, based on the `VECT` macro from the Simics C API (`simics/util/vect.h`). This is a simple wrapping that behaves inconsistently in many ways, and we plan to eventually introduce a cleaner mechanism for vectors; the `simics_util_vect` is supported as an interim solution until we have that in place. The syntax is `BASETYPE vect`, e.g. `typedef int vect int_vect_t;` to define a type for vectors of the `int` type. Some caveats:
  * `vect` types typically need to be `typedef`:ed before they are used. This is because `int vect` is blindly expanded into `VECT(int)` in C, which in turn expands into a `struct` definition, meaning that saying `VECT(int)` twice yields two incompatible types. This means, for instance, that `typeof` in DML doesn't work properly for `vect` types unless `typedef`:ed
  * Importing `"internal.dml"` exposes various C macros from `vect.h` to DML: `VINIT`, `VELEMSIZE`, `VRESIZE`, `VRESIZE_FREE`, `VADD`, `VREMOVE`, `VDELETE_ORDER`, `VINSERT`, `VSETLAST`, `VLEN`, `VVEC`, `VGROW`, `VSHRINK`, `VFREE`, `VTRUNCATE`, `VCLEAR`, and `VCOPY`.
  * DML natively supports indexing syntax, which is translated to `VGET` (or `VSET` for assignment). For instance: ```
typedef int vect int_vect_t;
method first_element(int_vect_t v) -> (int) {
  assert VLEN(v) > 0;
  return v[0];
}

```


Enabling the `simics_util_vect` feature in a file only affects the `vect` declarations in that file.
When the `simics_util_vect` feature is disabled, usage of `vect` is an error unless the [`experimental_vect` compatibility feature](deprecations-auto.html#experimental_vect) is enabled.
[A Messages](messages.html) [C Managing deprecated language features](deprecations-auto.html)
