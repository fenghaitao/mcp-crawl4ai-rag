[3 Device Modeling Language, version 1.4](language.html) [5 Standard Templates](utility.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [4 Libraries and Built-ins](#libraries-and-built-ins)
Most standard functionality in Device Modeling Language (DML) is implemented in templates. Built-in templates can be categorized as follows:
  * Each object type has a corresponding template which is instantiated for all objects of that type. For instance, the template `register` is automatically instantiated in all registers. All such templates inherit the `object` template, and define the `objtype` parameter to the name of the object type, e.g. `"register"` for registers.
  * Some templates primarily provide a standard implementation of some behaviour. For instance, the `uint64_attr` template can be applied on `attribute` objects to make it a simple integer attribute.
  * Some templates primarily specify a programming interface, typically by providing an abstract or overrideable method or parameter. Such templates are often named like the provided member. For instance, objects that implement the `init` template provide the abstract method `init`. Interface templates have a number of uses:
    * In some cases, an interface template extends an existing template, altering its default behaviour to make sure its interface method is called. Often, this means that when you provide an implementation of an interface method, you _must_ instantiate the corresponding template; otherwise, the method will not be called. For instance, if you implement the `write` method in a register, it is not called by default upon a write access; however, if you instantiate the `write` template in the register, then the register's behaviour is altered to call the `write` method. Thus, in order to provide custom side-effects on a write, you must write something like:
```
register r @ 0 is write { method write(uint64 value) { default();
log info: "wrote r"; } }

```

    * When writing a method or parameter override _inside a template_ , you must explicitly instantiate the template you are overriding in order to specify that your declaration takes precedence over the default implementation. If your template is intended for a specific object type, then it is sufficient to override that template, but it is often better to override a more specific template if possible. For instance, the `init_val` parameter belongs to the `init_val` template, which is inherited by all registers. So a template that overrides this parameter may be implemented as follows:
```
template init_to_ten is register {
  param init_val = 10;
}

```

However, it is even better to only inherit the `init_val` template:
```
template init_to_ten is init_val {
  param init_val = 10;
}

```

The latter improves efficiency and permits `init_to_ten` to also be used on fields.
    * Similarly, if you write a template that needs to _access_ some member of the object, then it must inherit a template that provides that member. For instance:
```
template log_on_change is (write, get, name) {
  method write(uint64 value) {
    if (this.get() != value) {
      log info: "%s changed!", this.name;
    }
    default();
  }
}

```

Again, it would also work to inherit `register` instead of `get` and `name`, but at the cost of reduced flexibility and efficiency.


## [4.1 Universal templates](#universal-templates)
The following templates are applicable to all object kinds:
### [4.1.1 name](#name)
Provides a string parameter `name`, containing the name of the object, as exposed to the end-user. This parameter is typically used in log messages and names of configuration attributes. The name can be overridden in order to hide confidential information from the end-user.
### [4.1.2 desc](#desc)
Provides a string parameter `desc`, with a short description in plain text. By convention, this should preferably be a few descriptive words, but may also be a long name. The description can appear during simulation, when inspecting the device, and also serves as a docstring that enriches the DML source code. The parameter's default value is `undefined`. The `desc` parameter has a short-hand syntax described in section [Object Declarations](language.html#object-declarations).
Also provides a string parameter `shown_desc`, which is the string actually exposed to the end-user during simulation. This parameter defaults to `desc`, and can be overridden in order to hide confidential information from the end-user.
See also [template `documentation`](#documentation).
### [4.1.3 shown_desc](#shown_desc)
A subtemplate of [`desc`](#desc) that makes the `shown_desc` parameter a typed parameter. This is inherited by objects that need to access `shown_desc` from the context of a shared method.
### [4.1.4 documentation](#documentation)
Provides a string parameter `documentation`, with a longer description. The documentation may appear when extracting documentation from the device.
If you have the _Documentation and Packaging_ package and intend to generate Simics reference documentation for the device then the `documentation` string must follow the Simics documentation XML format, otherwise you will get a syntax error during the documentation build. See the _Writing Documentation_ application note.
Also provides a string parameter `shown_documentation`, defaulting to `documentation`. This parameter is similar to `shown_desc` in the [desc](#desc) template, and is mainly a convenient way to suppress documentation.
### [4.1.5 limitations](#limitations)
Provides a string parameter `limitations`, describing limitations in the implementation of this object. The documentation may appear when extracting documentation from the device.
If you have the _Documentation and Packaging_ package and intend to generate Simics reference documentation for the device then the `limitations` string must follow the Simics documentation XML format, otherwise you will get a syntax error during the documentation build. See the _Writing Documentation_ application note.
Also provides a string parameter `shown_limitations`, defaulting to `limitations`. This parameter is similar to `shown_desc`, and is mainly a convenient way to suppress documentation.
### [4.1.6 init](#init)
Provides an abstract method `init`, which is called when the device is created, _before_ any attributes have been initialized. Typically used to initialize a default value, or to set up data structures.
The method `init` is automatically called on all objects that implement the `init` template. The order in which `init` of objects are called is not defined, except that `init` of a particular object is guaranteed to be called before `init` of any of its parent objects. In particular, `init` of the device object will be called only after all other implementations of `init`.
### [4.1.7 post_init](#post_init)
Provides an abstract method `post_init`, which is called when the device is created, _after_ any attributes have been initialized. Typically used to establish connections to other devices, or to set up data structures that depend on configured attribute values.
The method `post_init` is automatically called on all objects that implement the `post_init` template.
### [4.1.8 destroy](#destroy)
Provides an abstract method `destroy`, which is called when the device is being deleted. This provides a means to clean up resources associated with the device instance that are not managed by DMLC (and `destroy` should not be used for any other purpose). This typically amounts to invoking [`delete`](language.html#delete-statements) on any device state that has been dynamically allocated using [`new`](language.html#new-expressions).
The method `destroy` is automatically called on all objects that implement the `destroy` template. The order in which `destroy` of objects are called is not defined, except that `destroy` of a particular object is guaranteed to be called before `destroy` of any of its parent objects. In particular, `destroy` of the device object will be called only after all other implementations of `destroy`.
Usage notes:
  * While the device is being deleted, it is not allowed to communicate with any other Simics object (whether that is by accessing `connect`ed devices or by leveraging the Simics API.) This includes even the device's own clock; don't attempt to post or cancel time/cycle-based events in `destroy()` (including posting events using `after` with a time/cycle delay). The cancellation of such events is handled automatically, before the `destroy()` calls are invoked. The use of `.cancel_after()` inside `destroy()` is tolerated (even if almost always redundant.)
  * Exiting Simics, even gracefully, will not perform device deletion and cause `destroy()` to be called on its own. Simics instead simply relies on all resources being released by virtue of the process terminating. This means that side-effects within `destroy()` such as logging will not be visible upon program exit unless deletion is explicitly performed beforehand — hence why `destroy` should _only_ be used to ensure resources get cleaned up.


**Note:** the `destroy` template can't be instantiated for `event` objects. This is because `event` objects, through the `custom_time_event` or `custom_cycle_event` template, may already require defining a method named `destroy` whose purpose is different from the one required by the `destroy` template. To work around this limitation, you may declare a `group` within the `event` object that instantiates the `destroy` template instead.
### [4.1.9 object](#object)
Base template, implemented by all objects. Inherits the templates [`name`](#name), [`desc`](#desc), [`documentation`](#documentation) and [`limitations`](#limitations). Provides the following additional parameters, which cannot be overridden:
  * `this` (reference): Always refers to the current object, i.e., the nearest enclosing object definition.
  * `objtype`: string constant describing the object type, e.g. `"register"`
  * `parent` (reference or `undefined`): Always refers to the parent (containing) object. Has the value `undefined` in the `device` object.
  * qname: The fully qualified name, including indices, such as `some_bank.r0`. Constructed from the `name` parameter. In the device object, this is equal to the `name` parameter.
  * dev: The top-level `device` object
  * templates: see [Template-Qualified Method Implementation Calls](language.html#template-qualified-method-implementation-calls).
  * indices: List of local indices for this object. For a non-array object, this is the empty list. In a register array of size N, it is a list with one element, a non-negative integer smaller than N. The parameter is _not_ cumulative across the object hierarchy, so for a single field inside a register array, the value is the empty list.
  * Each array has an _individual index parameter_ , to make it possible to refer to both inner and outer indexes when arrays are nested (cf. the `indices` parameter, above). The parameter name is specified in the array declaration; for instance, the declaration `register regs[i < 4][j < 11];` defines two index parameters, `i` and `j`. In this case, the `indices` parameter is `[i, j]`.


The `object` template provides the non-overridable method `cancel_after()`, which cancels all pending events posted using `after` which are associated with the object (any events associated with subobjects are unaffected).
There are no other methods common for all objects, but the methods `init`, `post_init`, and `destroy` are automatically called on all objects that implement the [`init`](#init), [`post_init`](#post_init), and [`destroy`](#destroy) template, respectively.
## [4.2 Device objects](#device-objects)
The top-level scope of a DML file defines the _device object_ , defined by the template `device`. This template inherits the [`init`](#init), [`post_init`](#post_init), and [`destroy`](#destroy) templates.
The `device` template contains the following methods:
  * `init()`: Called when the device object is loaded, but before its configuration-object attributes have been initialized.
  * `post_init()`: Called when the device object is loaded, _after_ its configuration-object attributes have been initialized.
  * `destroy()`: Called when the device object is being deleted.


The `device` template contains the following parameters:
  * `classname` _[string]_ : The name of the Simics configuration object class defined by the device model. Defaults to the name of the device object.
  * `register_size` _[integer | undefined]_ : The default size (width) in bytes used for `register` objects; inherited by `bank` objects. The default value is `undefined`.
  * `byte_order` _[string]_ : The default byte order used when accessing registers wider than a single byte; inherited by `bank` objects. Allowed values are `"little-endian"` and `"big-endian"`. The default value is `"little-endian"`.
  * `be_bitorder` _[bool]_ : The default value of the `be_bitorder` in banks. The default value is `true` if the DML file containing the `device` statement declares `bitorder be;`, and `false` otherwise.
  * `use_io_memory` _[bool]_ : The default value of the `use_io_memory` parameter in banks. The current default value is `true`, but in future Simics versions it will be `false`.
  * `obj` *[conf_object_t _]_ : A pointer to the `conf_object_t` C struct that Simics associates with this device instance
  * `simics_api_version` _[string]_ : The Simics API version used when building this device, as specified by the `--simics-api` command-line argument; e.g. `"6"` for the Simics 6 API.


## [4.3 Group objects](#group-objects)
Group objects are generic container objects, used to group other objects. They can appear anywhere in the object hierarchy, but some object types (currently `implement` and `interface`) may not have a group as parent.
The `group` template contains no particular methods or parameters other than what is inherited from the [`object`](#object) template.
You may not declare any `bank`, `port` or `subdevice` underneath any group named "bank" or "port". This is to avoid namespace clashes in Simics.
## [4.4 Attribute objects](#attribute-objects)
The `attribute` template contains the following methods: 

[ get() -> (attr_value_t) ](#dt:get-attr_value_t)
    
Abstract method. Returns the value of the attribute. 

[ set(attr_value_t value) throws ](#dt:set-attr_value_t-value-throws)
    
Abstract method. Sets the value of the attribute. If the provided value is not allowed, use a `throw` statement to signal the error. 

[ get_attribute -> (attr_value_t), set_attribute(attr_value_t value) -> (set_error_t) ](#dt:get_attribute-attr_value_t-set_attribute-attr_value_t-value-set_error_t)
    
Not intended to be used directly. Called by Simics for reading and writing the attribute value. Calls the `get` and `set` methods.
The `attribute` template contains the following parameters: 

[ type [string | undefined] ](#dt:type-string-undefined)
    
A Simics configuration-object attribute type description string, such as `"i"` or `"[s*]"`, specifying the type of the attribute. (See the documentation of `SIM_register_typed_attribute` in the _Model Builder Reference Manual_ for details.) For simple types this can easily be set by standard attribute templates. 

[ configuration [`"required"` | `"optional"` | `"pseudo"` | `"none"`] ](#dt:configuration-required-optional-pseudo-none)
    
Specifies how Simics treats the attribute. The default value is `"optional"`. A _required_ attribute must be initialized to a value when the object is created, while an _optional_ attribute can be left undefined. In both cases, the value is saved when a checkpoint is created. For a _pseudo_ -attribute, the value is _not_ saved when a checkpoint is created (and it is not required to be initialized upon object creation). Setting the value to `"none"` suppresses creation of the attribute. This is seldom useful in attribute objects, but can be used in related object types like `register` to suppress checkpointing. 

[ persistent [bool] ](#dt:persistent-bool)
    
If this parameter is `true`, the attribute will be treated as persistent, which means that its value will be saved when using the `save-persistent-state` command. The default value is `false`. 

[ readable [bool] ](#dt:readable-bool)
    
If false, the attribute cannot be read. This can only be used if the `configuration` parameter is set to `"pseudo"`. Normally set by the `write_only_attr` template. 

[ writable [bool] ](#dt:writable-bool)
    
If false, the attribute cannot be written. This should normally be set by instantiating the `read_only_attr` template, and requires that the `configuration` parameter is `"pseudo"`. Normally set by the `read_only_attr` template. 

[ internal [bool] ](#dt:internal-bool)
    
If this parameter is `true`, the attribute will be treated as internal, meaning that it will be excluded from documentation. The default value is `true` if the `documentation` and `desc` parameters are undefined, and `false` otherwise.
## [4.5 Attribute templates](#attribute-templates)
Four templates are used to create a simple checkpointable attribute with standard types. Each store the attribute value in a member `val`, provide default implementations of methods `get` and `set` according to the type, and provide a default implementation of `init` that initializes `val` using the `init_val` parameter also provided by the template (whose default definition simply zero-initializes `val`.) These four templates are: 

[ bool_attr ](#dt:bool_attr)
    
boolean-valued attribute, `val` has type `bool` 

[ int64_attr ](#dt:int64_attr)
    
integer-valued attribute, `val` has type `int64` 

[ uint64_attr ](#dt:uint64_attr)
    
integer-valued attribute, `val` has type `uint64` 

[ double_attr ](#dt:double_attr)
    
floating-point-valued attribute, `val` has type `double`
In addition, three templates can be used to define a pseudo attribute, and cannot be used with the above templates: 

[ pseudo_attr ](#dt:pseudo_attr)
    
Pseudo attribute. Will not be checkpointed. Methods `get` and `set` are abstract. 

[ read_only_attr ](#dt:read_only_attr)
    
Pseudo attribute that cannot be written. Method `get` is abstract. 

[ write_only_attr ](#dt:write_only_attr)
    
Pseudo attribute that cannot be read. Method `set` is abstract
These templates are not compatible with the `bool_attr`, `uint64_attr`, `int64_attr`, or `float_attr` templates.
## [4.6 Connect objects](#connect-objects)
The `connect` template contains the following methods: 

[ validate(conf_object_t *obj) -> (bool) ](#dt:validate-conf_object_t-obj-bool)
    
Called when Simics attempts to assign a new target object. If the return value is `false`, the attempted connection will fail, and any existing connection will be kept. The default is to return `true`.
If connecting to a port interface (rather than a port object), then a session variable `port`, of type `char *`, is set to the new port name during the `validate` call. This will be removed in future versions of Simics. 

[ set(conf_object_t *obj) ](#dt:set-conf_object_t-obj)
    
Called after validation, to assign a new target object. Can be overridden to add side-effects before or after the assignment 

[ get_attribute -> (attr_value_t), set_attribute(attr_value_t value) -> (set_error_t) ](#dt:get_attribute-attr_value_t-set_attribute-attr_value_t-value-set_error_t-2)
    
Internal, not intended to be used directly. Called by Simics for accessing the attribute value.
The `connect` template contains the following parameters: 

[ configuration [`"required"` | `"optional"` | `"pseudo"` | `"none"`] ](#dt:configuration-required-optional-pseudo-none-2)
    
Specifies how Simics treats the automatically created [attribute](#attribute-objects) corresponding to the connect object. The default value is `"optional"`.
The attribute can be set to a nil value only if this parameter is `"optional"` or `"pseudo"`. In an array of connects, this applies element-wise.

[ internal [bool] ](#dt:internal-bool-2)
    
Specifies whether the [attribute](#attribute-objects) should be internal.
## [4.7 Connect templates](#connect-templates)
A `connect` object can instantiate the template `init_as_subobj`. This causes the connect to automatically set itself to an automatically created object. This can be used to create a private helper object.
The `init_as_subobj` template accepts one parameter, `classname`. This defines the class of the automatically created object.
**Note:** The subobject class defined by the `classname` parameter is looked up using `SIM_get_class` while the module of the device class is being loaded. This may cause problems if the subobject class is defined within the same module as the device class: if the device class is defined before the subobject class, then the subobject class will not yet be defined, and the `SIM_get_class` call will fail. This problem can be resolved by moving the subobject class to a separate module.
The template also overrides the `configuration` parameter to `"none"` by default, which makes the connect invisible to the end-user.
The `init_as_subobj` inherits the [`init`](#init) and [`connect`](#connect-objects) templates.
## [4.8 Interface objects](#interface-objects)
The `interface` template contains one parameter, `required`. Defaults to `true`. If overridden to `false`, the interface is optional and the parent `connect` object can connect to an object that does not implement the interface.
The template provides a session variable `val` of type `const void *`. It points to the Simics interface struct of the currently connected object. If the interface is optional, then the variable can be compared to NULL to check whether the currently connected object implements the interface.
## [4.9 Port objects](#port-objects)
The `port` template exposes one parameter, `obj`. When compiling with Simics API 5 or earlier, evaluates to dev.obj. When compiling with Simics API 6 or newer, evaluates to the `conf_object_t *` of the port's port object.
## [4.10 Subdevice objects](#subdevice-objects)
The `subdevice` template exposes one parameter, `obj`, which evaluates to the `conf_object_t *` of the Simics object that represents the subdevice.
## [4.11 Implement objects](#implement-objects)
The `implement` template provides no particular parameters or methods.
## [4.12 Implement templates](#implement-templates)
There is a single template for [`implement`](#implement-objects) objects, namely `bank_io_memory`. The template can be instantiated when implementing the `io_memory` interface, and redirects the access to a bank, specified by the `bank` parameter.
Bank objects contain an implementation of `io_memory` that inherits this template.
## [4.13 Bank objects](#bank-objects)
In addition to the `object` template, the `bank` template also inherits the [`shown_desc`](#shown_desc) template.
The `bank` template contains the following methods: 

[ io_memory_access(generic_transaction_t *memop, uint64 offset, void *aux) -> (bool) ](#dt:io_memory_access-generic_transaction_t-memop-uint64-offset-void-aux-bool)
    
Entry point for an access based on `generic_transaction_t`. Extracts all needed info from `memop`, calls appropriate memop-free methods, updates the `memop` parameter accordingly, and returns `true` if the access succeeded. The `offset` parameter is the offset of the access relative to the bank. The `aux` parameter is NULL by default, and is passed on to bank methods. In order to pass additional information on the access down to register and field methods, one can override `io_memory_access`, decode needed information from the incoming memop, and call `default` with the extracted information in the `aux` argument. 

[ transaction_access(transaction_t *t, uint64 offset, void *aux) -> (exception_type_t) ](#dt:transaction_access-transaction_t-t-uint64-offset-void-aux-exception_type_t)
    
Entry point for an access based on the `transaction` interface. Extracts all needed info from `t`, calls appropriate access methods (`read`, `write`, `get`, `set`), and updates the `t` parameter accordingly. Returns `Sim_PE_No_Exception` if the access succeeded, and `Sim_PE_IO_Not_Taken` otherwise. The `offset` parameter is the offset of the access relative to the bank. The `aux` parameter is NULL by default, and is passed on to bank methods. In order to pass additional information on the access down to register and field methods, one can override `transaction_access`, decode needed information from the incoming transaction, and call `default` with the extracted information in the `aux` argument. Accesses that bigger than 8 bytes are split into smaller sized chunks before being completed, the exact details of which are _undefined_. 

[ write(uint64 offset, uint64 value, uint64 enabled_bytes, void *aux) throws ](#dt:write-uint64-offset-uint64-value-uint64-enabled_bytes-void-aux-throws)
    
A write operation at the given offset. Throwing an exception makes the access fail, and is typically signaled for writes outside registers. The default behavior is to forward the access to registers, as follows:
  1. Deduce which registers are hit by the access. The `offset` and `size` parameters of each register object is used to deduce whether the register is covered by the access. A register which is only partially covered will be considered hit if the bank parameter `partial` is true, and a register which does not fully cover the access is considered hit if the bank parameter `overlapping` is set.
  2. If any portion of the access is not covered by a hit register, then the `unmapped_write` method is called with a bit pattern showing what parts of the access are unmapped. Any exception thrown by unmapped_write is propagated, causing the access to fail.
  3. The `write_register` method is called in all hit registers, starting with the register at the lowest offset.



[ unmapped_write(uint64 offset, uint64 value, uint64 bits, void *aux) throws ](#dt:unmapped_write-uint64-offset-uint64-value-uint64-bits-void-aux-throws)
    
If an access is not fully covered by registers, then this method is called before the access is performed. Throwing an exception aborts the entire access. _bits_ is a bit pattern showing which bits are affected; in the lowest 'size' bits, each 0xff byte represents the position of one unmapped byte in the access. The _value_ parameter contains the originally written value, including parts that are mapped to registers. Both _bits_ and _value_ are expressed in the host's endianness. The default behavior is to log a `spec-viol` message on level 1, and throw an exception. 

[ read(uint64 offset, uint64 enabled_bytes, void *aux) -> (uint64 value) throws ](#dt:read-uint64-offset-uint64-enabled_bytes-void-aux-uint64-value-throws)
    
A read operation at the given offset. The access is decomposed in the same way as in `write`. If there are unmapped portions of the access, `unmapped_read` is invoked, possibly aborting the operation. The return value is composed by the results from calling `read_register` in hit registers, combined with the result of `unmapped_read` if the access is not fully mapped. 

[ unmapped_read(uint64 offset, uint64 bits, void *aux) throws ](#dt:unmapped_read-uint64-offset-uint64-bits-void-aux-throws)
    
Like `unmapped_write` but for reads. The default implementation unconditionally throws an exception.
The `bank` template contains the following parameters: 

[ mappable [boolean] ](#dt:mappable-boolean)
    
Controls whether a bank is visible as an interface port for the `io_memory` interface, which makes it mappable in a memory space. This defaults to true. 

[ overlapping [bool] ](#dt:overlapping-bool)
    
Specifies whether this bank allows accesses that cover more than one register. (This translates to one or more, possibly partial, accesses to adjacent registers.) Defaults to `true`. This parameter must have the same value among all elements in a bank array object, i.e., it must not depend on the index of the bank. 

[ partial [bool] ](#dt:partial-bool)
    
Specifies whether this bank allows accesses that cover only parts of a register. A partial read will read the touched register fields (or the whole register if there are no fields) and extract the bits covered by the read. A partial write will call the `get` method on the touched register fields (or the whole register when there are no fields) and replace the written bits with the written value and then call the `write` method on the fields (or the register) with the merged value. Defaults to `true`. This parameter must have the same value among all elements in a bank array object, i.e., it must not depend on the index of the bank. 

[ register_size [integer | undefined] ](#dt:register_size-integer-undefined)
    
Inherited from the `device` object; provides the default value for the `size` parameter of `register` objects. 

[ byte_order [string] ](#dt:byte_order-string)
    
Specifies the byte order used when accessing registers wider than a single byte; inherited from `device` objects. Allowed values are `"little-endian"` and `"big-endian"`. This parameter must have the same value among all elements in a bank array object, i.e., it must not depend on the index of the bank. 

[ be_bitorder [bool] ](#dt:be_bitorder-bool)
    
Controls the preferred bit ordering of registers within this bank. Whenever the register is presented to the user as a bitfield, bit 0 refers to the least significant bit if the parameter is `false` (the default), and to the most significant bit if the parameter is `true`. The parameter is only a presentation hint and does not affect the model's behaviour. The parameter is technically unrelated to the top-level `bitorder` declaration, though in most cases the two should match. 

[ use_io_memory [bool] ](#dt:use_io_memory-bool)
    
If `true`, this bank is exposed using the legacy `io_memory` interface. In this case, the `io_memory_access` method can be called and overridden, but the `transaction_access` method can not.
If `false`, this bank is exposed using the `transaction` interface. In this case, the `transaction_access` method can be called and overridden, but the `io_memory_access` method can not.
The default is inherited from `dev.use_io_memory`.

[ obj [conf_object_t *] ](#dt:obj-conf_object_t)
    
When compiling with Simics API 5 or earlier, evaluates to dev.obj. When compiling with Simics API 6 or newer, evaluates to the bank's port object.
## [4.14 Register objects](#register-objects)
In addition to [`object`](#object), the `register` template inherits the templates [`get`](#get), [`set`](#set), [`shown_desc`](#shown_desc), [`read_register`](#read_register), [`write_register`](#write_register), and [`init_val`](#init_val).
The `register` template contains the following parameters: 

[ val [integer] ](#dt:val-integer)
    
The contents of the register. Manipulating `val` is a simpler, but less safe alternative to using `get_val()` and `set_val()` — unlike `set_val()`, it is _undefined behavior_ to write a value to `val` larger than what the register can hold. 

[ size [integer] ](#dt:size-integer)
    
The size (width) of the register, in bytes. This parameter can also be specified using the "`size _n_`" short-hand syntax for register objects. The default value is provided by the`register_size` parameter of the enclosing `bank` object. 

[ bitsize [integer] ](#dt:bitsize-integer)
    
The size (width) of the register, in bits. This is equivalent to the value of the `size` parameter multiplied by 8, and cannot be overridden. 

[ offset [integer] ](#dt:offset-integer)
    
The address offset of the register, in bytes relative to the start address of the bank that contains it. This parameter can also be specified using the "`@ _n_`" short-hand syntax for register objects. There is no default value. If the register inherits the`unmapped` template, the register is not mapped to an address. This parameter must have the same value among all elements in a bank array object, i.e., it must not depend on the index of the bank. 

[ fields [list of references] ](#dt:fields-list-of-references)
    
A list of references to all the `field` objects of a register object. 

[ init_val [integer] ](#dt:init_val-integer)
    
The value used by the default implementation of the `init` method, when the device is instantiated. The value is also used by the default implementations of hard reset, soft reset and power-on reset. Defaults to 0. 

[ configuration [`"required"` | `"optional"` | `"pseudo"` | `"none"`] ](#dt:configuration-required-optional-pseudo-none-3)
    
Specifies how Simics treats the automatically created [attribute] (#attribute-objects) corresponding to the register. The default value is `"optional"`. 

[ persistent [bool] ](#dt:persistent-bool-2)
    
Specifies whether the register [attribute](#attribute-objects) should be persistent. 

[ internal [bool] ](#dt:internal-bool-3)
    
Specifies whether the register [attribute](#attribute-objects) should be internal, default is `true`.
The `register` template provides the following overridable methods: 

[ `read_unmapped_bits(uint64 unmapped_enabled_bits, void *aux) -> (uint64)` ](#dt:read_unmapped_bits-uint64-unmapped_enabled_bits-void-aux-uint64)
    
`read_unmapped_bits` is used by the default implementation of `read_register` to read the bits not covered by fields from a register, possibly with side-effects.
The default implementation of `read_unmapped_bits` acts similarly to if the unmapped regions of the register were covered by fields, the `value` of the register is masked by `unmapped_enabled_bits` and returned. 

[ `write_unmapped_bits(uint64 val, uint64 enabled_bits, void *aux)`. ](#dt:write_unmapped_bits-uint64-val-uint64-enabled_bits-void-aux)
    
The `write_unmapped_bits` method is called from the default implementation of the `write_register` method when `enabled_bytes` specifies bytes not completely covered by field in the register (and the register has at least one field). `unmapped_enabled_bits` is defined as in the `read_unmapped_bits` method. `val` is the `val` argument passed to `write_register`, masked with the bits not covered by fields.
Default behaviour of `write_unmapped_bits` is to compare the `unmapped_enabled_bits` in `value` to those in the register `val`; if they do not match, a message of type `spec-viol` is logged for each bitrange that does not match, but `val` is not modified.
## [4.15 Field objects](#field-objects)
In addition to [`object`](#object), the `field` template inherits the templates [`init_val`](#init_val) and [`shown_desc`](#shown_desc).
The template inherits methods `get`, `set` and `init`, and the parameter `init_val`
The `field` template contains the following parameters: 

[ val [integer] ](#dt:val-integer-2)
    
The bitslice of the parent register corresponding to the field. Manipulating `val` is a simpler alternative to using `get_val()` and `set_val()`, while being just as safe (unlike with register objects). Unlike `get_val()` and `set_val()`, `val` is not a member of the `field` template type, and thus can't be used in certain contexts. 

[ reg [reference] ](#dt:reg-reference)
    
Always refers to the containing register object. 

[ lsb [integer] ](#dt:lsb-integer)
    
Required parameter. The bit number in the containing register of the field's least significant bit. Represented in little-endian bit order, regardless of `bitorder` declarations. The preferred way of defining this parameter is to use the "`[_highbit_:_lowbit_]`" short-hand syntax for field ranges, whose interpretation _is_ dependent on the `bitorder` declaration of the file. Care must be taken when referring to this parameter in a big-endian bit numbering system - if possible, put such code in a separate file that uses little-endian bit order interpretation. 

[ msb [integer] ](#dt:msb-integer)
    
Required parameter. The bit number in the containing register of the field's most significant bit. Represented in little-endian bit order. See `lsb` for details. 

[ bitsize [integer] ](#dt:bitsize-integer-2)
    
The size (width) of the field, in bits. This is automatically set from the `lsb` and `msb` parameters and cannot be overridden. 

[ init_val [integer] ](#dt:init_val-integer-2)
    
The value used by the default implementation of the `init` method, when the device is instantiated. The value is also used by the default implementations of hard reset, soft reset and power-on reset. Defaults to 0.
## [4.16 Templates for registers and fields](#templates-for-registers-and-fields)
This section lists templates that are specific for `register` and `field` objects.
All templates (except `read_register` and `write_register`) are applicable to both registers and fields. When writing a template that is applicable to both registers and fields, one should normally inherit one or more of the `read`, `write`, `get` and `set` methods.
Some methods have an argument `void *aux`. By default, that argument is NULL. The value can be overridden to carry arbitrary extra information about the access; this is done by overriding the `io_memory_access` method in the parent [bank](#bank-objects).
### [4.16.1 get_val](#get_val)
Provides a single non-overrideable method `get_val() -> (uint64)`. In a register, it returns the value of the .val member; in a field, it returns the bits of the parent register's `val` member that are covered by the field.
`get_val` is very similar to [`get`](#get); the difference is that `get_val` is unaffected if `get` is overridden. Thus, `get_val` is slightly more efficient, at the cost of flexibility. It is generally advisable to use `get`.
### [4.16.2 set_val](#set_val)
Provides a single non-overrideable method `set_val(uint64)`. In a register, it sets the value of the .val member; in a field, it sets the bits in the parent register's `val` member that are covered by the field.
`set_val` is very similar to (`set`)[#set); the difference is that `set_val` is unaffected if `set` is overridden. Thus, `set_val` is slightly more efficient, at the cost of flexibility. It is generally advisable to use `set`.
### [4.16.3 get](#get)
Extends the [`get_val`](#get_val) template. Provides a single overrideable method `get() -> (uint64)`, which retrieves the register's value, without side-effects, used for checkpointing and inspection. The default is to retrieve the value using the `get_val` method.
In a field, this template must be explicitly instantiated in order for an override to take effect. Note however that field objects do provide a callable default implementation of the method.
### [4.16.4 set](#set)
Extends the [`set_val`](#set_val) template. Provides a single overrideable method `set(uint64)`, which modifies the register's value, without triggering other side-effects. Used for checkpointing and inspection. The default is to set the value using the `set_val` method.
In a field, this template must be explicitly instantiated in order for an override to take effect. Note however that field objects do provide a callable default implementation of the method.
### [4.16.5 read_register](#read_register)
Implemented only by registers, not applicable to fields.
Provides a single abstract method `read_register(uint64 enabled_bytes, void *aux) -> (uint64)`.
The method reads from a register, possibly with side-effects. The returned value is represented in the host's native endianness. The `enabled_bytes` argument defines which bytes of the register is accessed, as a bitmask; each byte of the returned value has significance only if the corresponding byte in `enabled_bytes` is 0xff. If the access covers more than one register, then the parts of `enabled_bytes` that correspond to other registers are still zero.
Register objects provide a default implementation of `read_register`. The implementation invokes the `read_field` method of all sub-fields at least partially covered by `enabled_bytes`, in order from least to most significant bit. Bits not covered by fields are retrieved by calling the `read_unmapped_bits`, with `unmapped_enabled_bits` set as the `enabled_bytes` not covered by fields. If a register implements no fields, then the `read_unmapped_bits` is not called by default.
If a register inherits the `read_field` or `read` templates, then that template takes precedence over `read_register`, and the register's read behaviour is specified by the `read_field` or `read` method.
### [4.16.6 write_register](#write_register)
Implemented only by registers, not applicable to fields.
Provides a single abstract method: `write_register(uint64 value, uint64 enabled_bytes, void *aux)`.
The method writes to the register, possibly with side-effects. The `enabled_bytes` parameter is defined as in the `read_register` method.
Register objects provide a default implementation of write_register. The default behaviour depends on whether the register has fields:
  * If the register has no fields, then the default behaviour is to set the register's `val` member to the new value, using the `set` method.
  * If the register has fields, then the default behavior is to invoke the `write_field` method of all sub-fields covered at least partially by `enabled_bytes`, in order from least to most significant bit. Then `write_unmapped_bits` is called with the enabled bits that were not covered by fields.
If a register inherits the `write` or `write_field` template, then that template takes precedence over `write_register`, and the register's write behaviour is specified by the `write` (or `write_field`) method.


### [4.16.7 read_field](#read_field)
Provides a single abstract method `read_field(uint64 enabled_bits, void *aux) -> (uint64)`.
The method reads from a field or register, possibly with side-effects. The returned value is represented in the host's native endianness. The `enabled_bits` argument defines which bits of the register is accessed, as a bitmask; each bit of the returned value has significance only if the corresponding bit in `enabled_bits` is 1. If the access covers more than one field, then the parts of `enabled_bits` that correspond to other fields are still zero.
The `read_field` template is _not_ implemented by fields or registers by default, and must be explicitly instantiated in order for a method override to have effect. `read_field` is the interface used for access by registers; in most cases, it is easier to express read operations using the `read` template.
Note that instantiating `read_field` on a register means that register reads behave as if the register consists of one single field; a read access will ignore any actual field subobjects in the register.
### [4.16.8 write_field](#write_field)
Provides a single abstract method `write_field(uint64 value, uint64 enabled_bits, void *aux)`.
The method writes to a field or register, possibly with side-effects. The value is represented in the host's native endianness. The `enabled_bits` argument is defined as in the `read_field` method.
The `write_field` template is _not_ implemented by fields or registers by default, and must be explicitly instantiated in order for a method override to have effect. `write_field` is the interface used for access by registers; in most cases, it is easier to express write operations using the `write` template.
Note that instantiating `write_field` on a register means that register writes behave as if the register consists of one single field; a write access will ignore any actual field subobjects in the register. This is often useful in read-only registers, as it allows reads to propagate to fields, while a violating write can be handled centrally for the whole register.
### [4.16.9 read](#read)
Extends templates [`read_field`](#read_field) and [`get_val`](#get_val).
Provides a single overrideable method `read() -> (uint64)`.
The method reads from a field or register, possibly with side-effects. The returned value is represented in the host's native endianness. The default behaviour is to retrieve the value using the `get` method.
The `read` template is _not_ implemented by fields or registers by default, and must be explicitly instantiated in order for a method override to have effect.
Note that instantiating `read` on a register means that register reads behave as if the register consists of one single field; a read access will ignore any actual field subobjects in the register.
### [4.16.10 write](#write)
Extends templates [`write_field`](#write_field), [`get_val`](#get_val) and [`set_val`](#set_val).
Provides a single overrideable method `write(uint64)`.
The method writes to a field or register, possibly with side-effects. The value is represented in the host's native endianness. The default behaviour is to set the value using the `set` method.
The `write` template is _not_ implemented by fields or registers by default, and must be explicitly instantiated in order for a method override to have effect.
Note that instantiating `write` on a register means that register writes behave as if the register consists of one single field; a write access will ignore any actual field subobjects in the register.
### [4.16.11 init_val](#init_val)
Extends the [`init`](#init) template.
Provides a parameter `init_val : uint64`, defining the initial value of the register's `val` member when the object is created. In a field, defines the initial value of the bits of `val` that are covered by this field. The parameter is also used by default reset methods.
The template is inherited by both registers and fields. The value is 0 by default. In a register with fields, parameter overrides are permitted both in the register and in the field objects:
  * if the parameter is overridden _only_ in the register, then this defines the full value of the register.
  * if the parameter is overridden both in the register and in some fields, then the field overrides take precedence and define the value of the bits covered by the field


On a technical level, the default value of `init_val` in a field is the field's corresponding bits in the parent register's `init_val`; furthermore, the `init_val` template provides a default implementation of the `init` method which in register objects sets bits in `val` not covered by fields, and in field objects sets corresponding bits of the parent register's `val` member.
## [4.17 Event objects](#event-objects)
The `event` template contains little functionality in itself; it requires one of six predefined templates `simple_time_event`, `simple_cycle_event`, `uint64_time_event`, `uint64_cycle_event`, `custom_time_event`, and `custom_cycle_event` to be instantiated. These templates expose the methods `event` and `post`, and possibly others.
In addition to the [`object`](#object) template, the `event` template inherits the [`shown_desc`](#shown_desc) template.
## [4.18 Event templates](#event-templates)
Each `event` object is required to instantiate one of six predefined templates: `simple_time_event`, `simple_cycle_event`, `uint64_time_event`, `uint64_cycle_event`, `custom_time_event`, and `custom_cycle_event`. These are defined as follows:
  * The `simple_*_event` templates are used for events that carry no data
  * The `uint64_*_event` templates are used for events parameterized with a single 64-bit integer value
  * The `custom_*_event` templates are used for events that carry more complex data; the user must supply explicit serialization and deserialization methods.
  * In the `*_time_event` templates, time is provided in seconds, as a floating-point number
  * In the `*_cycle_event` templates, time is provided in cycles, as a 64-bit integer


The following methods are defined by all six templates: 

[ event(), event(uint64 data), event(void *data) ](#dt:event-event-uint64-data-event-void-data)
    
Abstract method, called when the event is triggered. When one of the `custom_*_event` templates is used, the `event` method is responsible for deallocating the data. 

[ post(time), post(time, uint64 data), post(time, void *data) ](#dt:post-time-post-time-uint64-data-post-time-void-data)
    
Non-overrideable method. Posts the event on the associated queue of the device. The time argument is specified in cycles or seconds, depending on which template was instantiated. The event will be triggered after the specified amount of time has elapsed. The data parameter in a `uint64` or `custom` event will be passed on to the event() method.
The following methods are specific to the `simple_time_event`, `simple_cycle_event`, `uint64_time_event` and `uint64_cycle_event` templates: 

[ remove(), remove(uint64 data) ](#dt:remove-remove-uint64-data)
    
Removes all events of this type with matching data from the queue. 

[ posted() -> (bool), posted(uint64 value) -> (bool) ](#dt:posted-bool-posted-uint64-value-bool)
    
Returns `true` if the event is in the queue, and `false` otherwise. 

[ next(), next(uint64 data) -> (double or cycles_t) ](#dt:next-next-uint64-data-double-or-cycles_t)
    
Returns the time to the next occurrence of the event in the queue (relative to the current time), in cycles or seconds depending on which event template was instantiated. If there is no such event in the queue, a negative value is returned.
The following methods are specific to the `custom_time_event` and `custom_cycle_event` templates: 

[ get_event_info(void *data) -> (attr_value_t) ](#dt:get_event_info-void-data-attr_value_t)
    
This method is called once for each pending event instance when saving a checkpoint. It should create an attribute value that can be used to restore the event. The `data` parameter is the user data provided in the `post` call. The default implementation always returns a nil value. 

[ set_event_info(attr_value_t info) -> (void *) ](#dt:set_event_info-attr_value_t-info-void)
    
This method is used to restore event information when loading a checkpoint. It should use the attribute value to create a user data pointer, as if it had been provided in a `post`. The default implementation only checks that the checkpointed information is nil. 

[ destroy(void *data) ](#dt:destroy-void-data)
    
This method is called on any posted events when the device object is deleted.
If memory was allocated for the `data` argument to `post`, then `destroy` should free this memory.
The `destroy` method is _not_ called automatically when an event is triggered; therefore, the method should typically also be called explicitly from the `event` method.
[3 Device Modeling Language, version 1.4](language.html) [5 Standard Templates](utility.html)
