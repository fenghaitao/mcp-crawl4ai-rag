[4 Libraries and Built-ins](dml-builtins.html) [A Messages](messages.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [5 Standard Templates](#standard-templates)
This chapter describes the standard templates included the Device Modeling Language (DML) library. The templates can be used for both registers and fields. The templates can be accessed after importing `utility.dml`.
The most common device register functionality is included in the standard templates.
Note that many standard templates has the same functionality and only differ by name or log-messages printed when writing or reading them. The name of the template help developers to get a quick overview of the device functionality. An example are the _undocumented_ and _reserved_ templates. Both have the same functionality. However, the _undocumented_ template hints that something in the device documentation is unclear or missing, and the _reserved_ template that the register or field should not be used by software.
The sub-sections use _object_ as a combined name for registers and fields. The sub-sections refers to software and hardware reads and writes. Software reads and writes are defined as accesses using the `io_memory` interface (write/reads to memory/io mapped device). Software reads and writes use the DML built-in read and write methods. Hardware read writes are defined as accesses using Simics configuration attributes, using the DML built-in set and get methods. Device code can still modify a register or device even if hardware modification is prohibited.
## [5.1 Templates for reset](#templates-for-reset)
Reset behavior can vary quite a bit between different devices. DML has no built-in support for handling reset, but there are standard templates in `utility.dml` to cover some common reset mechanisms.
There are three standard reset types: 

[ Power-on reset ](#dt:power-on-reset)
    
The reset that happens when power is first supplied to a device. 

[ Hard reset ](#dt:hard-reset)
    
Typically triggered by a physical hard reset line that can be controlled from various sources, such as a watchdog timer or a physical button. Often the same as a power-on reset. 

[ Soft reset ](#dt:soft-reset)
    
This usually refers to a reset induced by software, e.g. by a register write. Not all devices have a soft reset, and some systems may support more than one type of soft reset.
Usually, the effect of a reset is that all registers are restored to some pre-defined value.
In DML, the reset types can be enabled by instantiating the templates [`poreset`, `hreset` and `sreset`](#poreset), respectively. These will define a port with the corresponding upper-case name (`POWER`, `HRESET`, `SRESET`), which implements the `signal` interface, triggering the corresponding reset type on raising edge. This happens by invoking a corresponding method (`power_on_reset`, `hard_reset` and `soft_reset`, respectively), in all objects implementing a given template ([`power_on_reset`, `hard_reset` and `soft_reset`](#power_on_reset), respectively). The default is that all registers and fields implement these templates, with the default behavior being to restore to the value of the `init_val` parameter. The methods `signal_raise` and `signal_lower` can be overridden to add additional side effects upon device reset. One example would be to track if the reset signal is asserted to prevent interaction with the device during reset.
The default implementation of all reset methods recursively calls the corresponding reset method in all sub-objects. Thus, if a reset method is overridden in an object without calling `default()`, then reset is effectively suppressed in all sub-objects.
The two most common overrides of reset behavior are:
  * to reset to a different value. In the general case, this can be done with an explicit method override. In the case of soft reset, you can also use the standard template [`soft_reset_val`](#soft_reset_val) which allows you to configure the reset value with a parameter `soft_reset_val`.
  * to suppress reset. This can be done with a standard template: [`sticky`](#sticky) suppresses soft reset only, while [`no_reset`](#no_reset) suppresses all resets.
It is quite common that hard reset and power-on reset behave identically. In this case, we recommend that only a `HRESET` port is created; this way, the presence of a `POWER` port is an indication that the device actually provides a distinct behavior on power cycling.
There are some less common reset use cases:
  * In some devices, the standard reset types may not map well to the hardware, typically because there may be more than one reset type that could be viewed as a soft reset. In this case, we recommend that `SRESET` is replaced with device-specific port names that map better to the hardware, but that the `POWER` and `HRESET` port names are preserved if they are unambiguous.
  * In some cases, it is desirable to accurately simulate how a device acts in a powered-off state. This would typically mean that the device does not react to other stimuli until power is turned on again.
The recommended way to simulate a powered-off state, is to let the high signal level of the `POWER` port represent that the device has power, and react as if power is down while the signal is low. Furthermore, the device is reset when the `POWER` signal is lowered.
If this scheme is used by a device, then a device will be considered turned off after instantiation, so the `POWER` signal must be raised explicitly before the device can function normally.
Thus, there are two rather different ways to handle devices that have a `POWER` port:
    * `POWER` can be treated as a pure reset port, which stays low for most of the time and is rapidly raised and lowered to mark a power-on reset. This is the most convenient way to provide a power signal, but it only works if the device only uses `POWER` for power-on reset. If the device models power supply accurately, then it will not function as expected, because it will consider power to be off.
    * `POWER` can be accurately treated as a power supply, meaning that the signal is raised before simulation starts, and lowered when power goes down. A reset is triggered by a lower followed by a raise. This approach is less convenient to implement, but more correct: The device will function correctly both if the device does an accurate power supply simulation, and if it only uses `POWER` for power-on reset.

[5.1.1 power_on_reset, hard_reset, soft_reset](#power_on_reset-hard_reset-soft_reset) [5.1.1.1 Description](#description) Implemented on any object to get a callback on the corresponding reset event. Automatically implemented by registers and fields. [5.1.1.2 Related Templates](#related-templates)
[`poreset`, `hreset`, `sreset`](#poreset)
[5.1.2 poreset, hreset, sreset](#poreset-hreset-sreset) [5.1.2.1 Description](#description-2) Implemented on the top level to get standard reset behaviour, for power-on reset, hard reset and soft reset, respectively. [5.1.2.2 Related Templates](#related-templates-2)
[`power_on_reset`, `hard_reset`, `soft_reset`](#power_on_reset)
## [5.2 Templates for registers and fields](#templates-for-registers-and-fields)
The following templates can be applied to both registers and fields. Most of them affect either the write or read operation; if applied on a register it will disregard fields. For instance, when applying the [`read_unimpl`](#read_unimpl) template on a register with fields, then the read will ignore any implementations of `read` or `read_field` in fields, and return the current register value (through `get`), ignoring any `read` overrides in fields. However, writes will still propagate to the fields.
### [5.2.1 soft_reset_val](#soft_reset_val)
#### [5.2.1.1 Description](#description-3)
Implemented on a register or field. Upon soft reset, the reset value is defined by the required `soft_reset_val` parameter, instead of the default `init_val`.
#### [5.2.1.2 Related Templates](#related-templates-3)
[`soft_reset`](#power_on_reset)
### [5.2.2 ignore_write](#ignore_write)
#### [5.2.2.1 Description](#description-4)
Writes are ignored. This template might also be useful for read-only fields inside an otherwise writable register. See the documentation for the [`read_only`](#read_only) template for more information.
### [5.2.3 read_zero](#read_zero)
#### [5.2.3.1 Description](#description-5)
Reads return 0, regardless of register/field value. Writes are unaffected by this template.
#### [5.2.3.2 Related Templates](#related-templates-4)
[`read_constant`](#read_constant)
### [5.2.4 read_only](#read_only)
#### [5.2.4.1 Description](#description-6)
The object value is read-only for software, the object value can be modified by hardware.
#### [5.2.4.2 Log Output](#log-output)
First software write results in a spec_violation log-message on log-level 1, remaining writes on log-level 2. Fields will only log if the written value is different from the old value.
If the register containing the read-only field also contains writable fields, it may be better to use the [`ignore_write`](#ignore_write) template instead, since software often do not care about what gets written to a read-only field, causing unnecessary logging.
### [5.2.5 write_only](#write_only)
#### [5.2.5.1 Description](#description-7)
The register value can be modified by software but can't be read back, reads return 0. Only for use on registers; use [`read_zero`](#read_zero) for write-only fields.
#### [5.2.5.2 Log Output](#log-output-2)
The first time the object is read there is a spec_violation log-message on log-level 1, remaining reads on log-level 2.
### [5.2.6 write_1_clears](#write_1_clears)
#### [5.2.6.1 Description](#description-8)
Software can only clear bits. This feature is often used when hardware sets bits and software clears them to acknowledge. Software write 1's to clear bits. The new object value is a bitwise AND of the old object value and the bitwise complement of the value written by software.
### [5.2.7 clear_on_read](#clear_on_read)
#### [5.2.7.1 Description](#description-9)
Software reads return the object value. The object value is then reset to 0 as a side-effect of the read.
### [5.2.8 write_1_only](#write_1_only)
#### [5.2.8.1 Description](#description-10)
Software can only set bits to 1. The new object value is the bitwise OR of the old object value and the value written by software.
#### [5.2.8.2 Related Templates](#related-templates-5)
[`write_0_only`](#write_0_only)
### [5.2.9 write_0_only](#write_0_only)
#### [5.2.9.1 Description](#description-11)
Software can only set bits to 0. The new object value is the bitwise AND of the old object value and the value written by software.
#### [5.2.9.2 Related Templates](#related-templates-6)
[`write_1_only`](#write_1_only)
### [5.2.10 read_constant](#read_constant)
#### [5.2.10.1 Description](#description-12)
Reads return a constant value.
Writes are unaffected by this template. The read value is unaffected by the value of the register or field.
The template is intended for registers or fields that have a stored value that is affected by writes, but where reads disregard the stored value and return a constant value. The attribute for the register will reflect the stored value, not the value that is returned by read operations. For constant registers or fields that do not store a value, use the [`constant`](#constant) template instead.
#### [5.2.10.2 Parameters](#parameters)
`read_val`: the constant value
#### [5.2.10.3 Related Templates](#related-templates-7)
[`constant`](#constant), [`silent_constant`](#silent_constant), [`read_zero`](#read_zero)
### [5.2.11 constant](#constant)
#### [5.2.11.1 Description](#description-13)
Writes are forbidden and have no effect.
The object still has backing storage, which affects the value being read. Thus, an end-user can modify the constant value by writing to the register's attribute. Such tweaks will survive a reset.
Using the `constant` template marks that the object is intended to stay constant, so the model should not update the register value, and not override the `read` method. Use the template [`read_only`](#read_only) if that is desired.
#### [5.2.11.2 Log Output](#log-output-3)
First write to register or field (if field value is not equal to write value) results in a spec_violation log-message on log-level 1, remaining writes on log-level 2.
#### [5.2.11.3 Parameters](#parameters-2)
init_val: the constant value
#### [5.2.11.4 Related Templates](#related-templates-8)
[`read_constant`](#read_constant), [`silent_constant`](#silent_constant), [`read_only`](#read_only)
### [5.2.12 silent_constant](#silent_constant)
#### [5.2.12.1 Description](#description-14)
The object value will remain constant. Writes are ignored and do not update the object value.
The end-user can tweak the constant value; any tweaks will survive a reset.
By convention, the object value should not be modified by the model; if that behaviour is wanted, use the [`ignore_write`](#ignore_write) template instead.
#### [5.2.12.2 Parameters](#parameters-3)
init_val: the constant value
#### [5.2.12.3 Related Templates](#related-templates-9)
[`constant`](#constant), [`read_constant`](#read_constant)
### [5.2.13 zeros](#zeros)
#### [5.2.13.1 Description](#description-15)
The object value is constant 0. Software writes are forbidden and do not update the object value.
#### [5.2.13.2 Log Output](#log-output-4)
First software write to register or field (if field value is not equal to write value) results in a spec_violation log-message on log-level 1, remaining writes on log-level 2.
### [5.2.14 ones](#ones)
#### [5.2.14.1 Description](#description-16)
The object is constant all 1's. Software writes do not update the object value. The object value is all 1's.
#### [5.2.14.2 Log Output](#log-output-5)
First software write to register or field (if field value is not equal to write value) results in a spec_violation log-message on log-level 1, remaining writes on log-level 2.
### [5.2.15 ignore](#ignore)
#### [5.2.15.1 Description](#description-17)
The object's functionality is unimportant. Reads return 0. Writes are ignored.
### [5.2.16 reserved](#reserved)
#### [5.2.16.1 Description](#description-18)
The object is marked reserved and should not be used by software. Writes update the object value. Reads return the object value.
#### [5.2.16.2 Log Output](#log-output-6)
First software write to register or field (if field value is not equal to write value) results in a `spec-viol` log-message on log-level 2. No logs on subsequent writes.
### [5.2.17 unimpl](#unimpl)
#### [5.2.17.1 Description](#description-19)
The object functionality is unimplemented. Warn when software is using the object. Writes and reads are implemented as default writes and reads.
#### [5.2.17.2 Log Output](#log-output-7)
First read from a register results in an unimplemented log-message on log-level 1, remaining reads on log-level 3. Reads from a field does not result in a log-message. First write to a register results in an unimplemented log-message on log-level 1, remaining writes on log-level 3. First write to a field (if field value is not equal to write value) results in an unimplemented log-message on log-level 1, remaining writes on log-level 3.
#### [5.2.17.3 Related Templates](#related-templates-10)
[`read_unimpl`](#read_unimpl), [`write_unimpl`](#write_unimpl), [`silent_unimpl`](#silent_unimpl), [`design_limitation`](#design_limitation)
### [5.2.18 read_unimpl](#read_unimpl)
#### [5.2.18.1 Description](#description-20)
The object functionality associated to a read access is unimplemented. Write access is using default implementation and can be overridden (for instance by the [`read_only`](#read_only) template).
#### [5.2.18.2 Log Output](#log-output-8)
First software read to a register results in an unimplemented log-message on log-level 1, remaining reads on log-level 3. Software reads to fields does not result in a log-message.
#### [5.2.18.3 Related Templates](#related-templates-11)
[`unimpl`](#unimpl), [`write_unimpl`](#write_unimpl), [`silent_unimpl`](#silent_unimpl), [`design_limitation`](#design_limitation)
### [5.2.19 write_unimpl](#write_unimpl)
#### [5.2.19.1 Description](#description-21)
The object functionality associated to a write access is unimplemented. Read access is using default implementation and can be overridden (for instance by the [`write_only`](#write_only) template).
#### [5.2.19.2 Log Output](#log-output-9)
First software write to registers results in an unimplemented log-message on log-level 1, remaining writes on log-level 3. First write to a field (if field value is not equal to write value) results in an unimplemented log-message on log-level 1, remaining writes on log-level 3.
#### [5.2.19.3 Related Templates](#related-templates-12)
[`unimpl`](#unimpl), [`read_unimpl`](#read_unimpl), [`silent_unimpl`](#silent_unimpl), [`design_limitation`](#design_limitation)
### [5.2.20 silent_unimpl](#silent_unimpl)
#### [5.2.20.1 Description](#description-22)
The object functionality is unimplemented, but do not print a lot of log-messages when reading or writing. Writes and reads are implemented as default writes and reads.
#### [5.2.20.2 Log Output](#log-output-10)
First software read to a register results in an unimplemented log-message on log-level 2, remaining reads on log-level 3. Software reads to fields does not result in a log-message. First software write to a register results in an unimplemented log-message on log-level 2, remaining writes on log-level 3. First write to a field (if field value is not equal to write value) results in an unimplemented log-message on log-level 2, remaining writes on log-level 3.
#### [5.2.20.3 Related Templates](#related-templates-13)
[`unimpl`](#unimpl), [`design_limitation`](#design_limitation)
### [5.2.21 undocumented](#undocumented)
#### [5.2.21.1 Description](#description-23)
The object functionality is undocumented or poorly documented. Writes and reads are implemented as default writes and reads.
#### [5.2.21.2 Log Output](#log-output-11)
First software write and read result in a spec_violation log-message on log-level 1, remaining on log-level 2.
### [5.2.22 unmapped](#unmapped)
#### [5.2.22.1 Description](#description-24)
The register is excluded from the address space of the containing bank.
### [5.2.23 sticky](#sticky)
#### [5.2.23.1 Description](#description-25)
Do not reset object value on soft-reset, keep current value.
### [5.2.24 design_limitation](#design_limitation)
#### [5.2.24.1 Description](#description-26)
The object's functionality is not in the model's scope and has been left unimplemented as a design decision. Software and hardware writes and reads are implemented as default writes and reads. Debug registers are a prime example of when to use this template. This is different from _unimplemented_ which is intended to be implement (if required) but is a limitation in the current model.
#### [5.2.24.2 Related Templates](#related-templates-14)
[`unimpl`](#unimpl), [`silent_unimpl`](#silent_unimpl)
### [5.2.25 no_reset](#no_reset)
#### [5.2.25.1 Description](#description-27)
The register's or field's value will not be changed on a hard or soft reset.
## [5.3 Bank related templates](#bank-related-templates)
### [5.3.1 function_mapped_bank](#function_mapped_bank)
#### [5.3.1.1 Description](#description-28)
Only valid in `bank` objects. The bank is recognized as a function mapped bank by the [`function_io_memory`](#function_io_memory) template, and is mapped to a specified function by whoever instantiates that template.
#### [5.3.1.2 Parameters](#parameters-4)
function: the function number, an integer
#### [5.3.1.3 Related Templates](#related-templates-15)
[`function_io_memory`](#function_io_memory)
### [5.3.2 function_io_memory](#function_io_memory)
#### [5.3.2.1 Description](#description-29)
Only valid in `implement` objects named `io_memory`. Implements the `io_memory` interface by function mapping: An incoming memory transaction is handled by finding a bank that instantiates the [`function_mapped_bank`](#function_mapped_bank) template inside the same (sub)device as `implement`, and has a function number that matches the memory transaction's. If such a bank exists, the transaction is handled by that bank. If no such bank exists, an error message is logged and a miss is reported for the access.
Mapping banks by function number is a deprecated practice, still used by PCI devices for legacy reasons. It is usually easier to map a bank directly into a memory space, than using a function number as an indirection.
Note also that function numbers as defined by the PCI standard are unrelated to the function numbers of banks. They can sometimes coincide, though.
#### [5.3.2.2 Parameters](#parameters-5)
function: the function number, an integer
#### [5.3.2.3 Related Templates](#related-templates-16)
[`function_mapped_bank`](#function_mapped_bank)
### [5.3.3 miss_pattern_bank](#miss_pattern_bank)
#### [5.3.3.1 Description](#description-30)
Only valid in `bank` objects. Handles unmapped accesses by ignoring write accesses, and returning a given value for each unmapped byte. If you want to customize this behaviour, overriding `unmapped_get` is sufficient to also customize `unmapped_read`.
#### [5.3.3.2 Parameters](#parameters-6)
miss_pattern: each missed byte in a miss read is set to this value
## [5.4 Connect related templates](#connect-related-templates)
### [5.4.1 map_target](#map_target)
A `connect` object can instantiate the template `map_target`. The template provides an easy way to send memory transactions to objects that can be mapped into Simics memory maps. It defines a default implementation of `set` which assigns the session variable `map_target` of type `map_target_t *`, which can be used to issue transactions to the connected object. It also defines a default implementation of `validate` which verifies that the object can be used to create a map target, i.e. the Simics API `SIM_new_map_target` returns a valid pointer.
The template defines the following methods:
  * `read(uint64 addr, uint64 size) -> (uint64) throws`
Reads `size` bytes starting at `addr` in the connected object. Size must be 8 or less. Byte order is little-endian. Throws an exception if the read fails.
  * `read_bytes(uint64 addr, uint64 size, uint8 *bytes) throws`
Reads `size` bytes into `bytes`, starting at `addr` in the connected object. Throws an exception if the read fails.
  * `write(uint64 addr, uint64 size, uint64 value) throws`
Writes `value` of `size` bytes, starting at `addr` in the connected object. Size must be 8 or less. Byte order is little-endian. Throws an exception if the write fails.
  * `write_bytes(uint64 addr, uint64 size, const uint8 *bytes) throws`
Writes `size` bytes from `bytes`, starting at `addr` in the connected object. Throws an exception if the write fails.
  * `issue(transaction_t *t, uint64 addr) -> (exception_type_t)`
Provides a shorthand to the API function `SIM_issue_transaction`. This method is called by the read/write methods in this template. It can be overridden, e.g. to add additional atoms to the transactions, while still allowing the ease-of-use from the simpler methods.


## [5.5 Signal related templates](#signal-related-templates)
### [5.5.1 signal_port](#signal_port)
Implements a signal interface with saved state. The current state of the signal is stored in the saved boolean `high`, and a spec-violation message is logged on level 2 if the signal is raised or lowered when already high or low. The methods `signal_raise` and `signal_lower` can be overridden to add additional side effects.
### [5.5.2 signal_connect](#signal_connect)
Implements a connect with a signal interface, with saved state. The current state of the signal is stored in the saved boolean `signal.high`. If the connect is changed while `signal.high` is `true` and the device is configured, the `signal_lower` method will be called on the old object, and the `signal_raise` method will be called on the new object. Similarly, if the device is created with `signal.high` set to `true`, the `signal_raise` method will be called on the connected object in the finalize phase. This behaviour can be changed by overriding the `set` method and/or the `post_init` method. The template defines the following method:
  * `set_level(uint1 high)`: Sets the level of the signal, by calling `signal_raise` or `signal_lower`, as required. Also sets `signal.high` to `high`.


#### [5.5.2.1 Related Templates](#related-templates-17)
[`signal_port`](#signal_port)
[4 Libraries and Built-ins](dml-builtins.html) [A Messages](messages.html)
