[D.6 Backward incompatible changes, not automatically converted](changes-manual.html)
[Device Modeling Language 1.4 Reference Manual](index.html) / 
# [E Formal Grammar](#formal-grammar) 

[_dml_ →](#dt:dml)
     _maybe_provisional_ _maybe_device_ _maybe_bitorder_ _device_statements_ 

[_maybe_provisional_ →](#dt:maybe_provisional)
     **provisional** _ident_list_ "**;** " **|** <empty> 

[_maybe_device_ →](#dt:maybe_device)
     **device** _objident_ "**;** " **|** <empty> 

[_maybe_bitorder_ →](#dt:maybe_bitorder)
     <empty> **|** **bitorder** _ident_ "**;** "  

[_device_statements_ →](#dt:device_statements)
     _device_statements_ _device_statement_ **|** <empty> 

[_device_statement_ →](#dt:device_statement)
     _toplevel_ **|** _object_ **|** _toplevel_param_ **|** _method_ **|** _bad_shared_method_ **|** _istemplate_ "**;** " **|** _toplevel_if_ **|** _error_stmt_ **|** _in_each_ 

[_toplevel_param_ →](#dt:toplevel_param)
     _param_ 

[_toplevel_if_ →](#dt:toplevel_if)
     _hashif_ "**(** " _expression_ "**)** " "**{** " _device_statements_ "**}** " _toplevel_else_ 

[_toplevel_else_ →](#dt:toplevel_else)
     <empty> **|** _hashelse_ "**{** " _device_statements_ "**}** " **|** _hashelse_ _toplevel_if_ 

[_array_list_ →](#dt:array_list)
     <empty> **|** _array_list_ "**[** " _arraydef_ "**]** "  

[_object_ →](#dt:object)
     **register** _objident_ _array_list_ _sizespec_ _offsetspec_ _maybe_istemplate_ _object_spec_ 

[_bitrangespec_ →](#dt:bitrangespec)
     "**@** " _bitrange_ **|** <empty> 

[_object_ →](#dt:object-2)
     **field** _objident_ _array_list_ _bitrangespec_ _maybe_istemplate_ _object_spec_ 

[_bitrange_ →](#dt:bitrange)
     "**[** " _expression_ "**]** " **|** "**[** " _expression_ "**:** " _expression_ "**]** "  

[_data_ →](#dt:data)
     **session** 

[_object_ →](#dt:object-3)
     _session_decl_ 

[_session_decl_ →](#dt:session_decl)
     _data_ _named_cdecl_ "**;** " **|** _data_ _named_cdecl_ "**=** " _initializer_ "**;** " **|** _data_ "**(** " _cdecl_list_nonempty_ "**)** " "**;** " **|** _data_ "**(** " _cdecl_list_nonempty_ "**)** " "**=** " _initializer_ "**;** "  

[_object_ →](#dt:object-4)
     _saved_decl_ 

[_saved_decl_ →](#dt:saved_decl)
     **saved** _named_cdecl_ "**;** " **|** **saved** _named_cdecl_ "**=** " _initializer_ "**;** " **|** **saved** "**(** " _cdecl_list_nonempty_ "**)** " "**;** " **|** **saved** "**(** " _cdecl_list_nonempty_ "**)** " "**=** " _initializer_ "**;** "  

[_object_ →](#dt:object-5)
     **connect** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **interface** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **attribute** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **bank** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **event** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **group** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **port** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **implement** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ **|** **subdevice** _objident_ _array_list_ _maybe_istemplate_ _object_spec_ 

[_maybe_default_ →](#dt:maybe_default)
     **default** **|** <empty> 

[_method_ →](#dt:method)
     _method_qualifiers_ **method** _objident_ _method_params_typed_ _maybe_default_ _compound_statement_ **|** **inline** **method** _objident_ _method_params_maybe_untyped_ _maybe_default_ _compound_statement_ 

[_arraydef_ →](#dt:arraydef)
     _ident_ "**<** " _expression_ **|** _ident_ "**<** " _"..."_ 

[_template_stmts_ →](#dt:template_stmts)
     <empty> **|** _template_stmts_ _template_stmt_ 

[_template_stmt_ →](#dt:template_stmt)
     _object_statement_or_typedparam_ **|** **shared** _method_qualifiers_ **method** _shared_method_ **|** **shared** _hook_decl_ 

[_method_qualifiers_ →](#dt:method_qualifiers)
     <empty> **|** **independent** **|** **independent** **startup** **|** **independent** **startup** **memoized** 

[_shared_method_ →](#dt:shared_method)
     _ident_ _method_params_typed_ "**;** " **|** _ident_ _method_params_typed_ **default** _compound_statement_ **|** _ident_ _method_params_typed_ _compound_statement_ 

[_toplevel_ →](#dt:toplevel)
     **template** _objident_ _maybe_istemplate_ "**{** " _template_stmts_ "**}** " **|** **header** "**%{ ... %}** " **|** **footer** "**%{ ... %}** " **|** **_header** "**%{ ... %}** " **|** **loggroup** _ident_ "**;** " **|** **constant** _ident_ "**=** " _expression_ "**;** " **|** **extern** _cdecl_ "**;** " **|** **typedef** _named_cdecl_ "**;** " **|** **extern** **typedef** _named_cdecl_ "**;** " **|** **import** _utf8_sconst_ "**;** "  

[_object_desc_ →](#dt:object_desc)
     _composed_string_literal_ **|** <empty> 

[_object_spec_ →](#dt:object_spec)
     _object_desc_ "**;** " **|** _object_desc_ "**{** " _object_statements_ "**}** "  

[_object_statements_ →](#dt:object_statements)
     _object_statements_ _object_statement_ **|** <empty> 

[_object_statement_ →](#dt:object_statement)
     _object_statement_or_typedparam_ **|** _bad_shared_method_ 

[_bad_shared_method_ →](#dt:bad_shared_method)
     **shared** _method_qualifiers_ **method** _shared_method_ 

[_toplevel_ →](#dt:toplevel-2)
     **export** _expression_ **as** _expression_ "**;** "  

[_object_statement_or_typedparam_ →](#dt:object_statement_or_typedparam)
     _object_ **|** _param_ **|** _method_ **|** _istemplate_ "**;** " **|** _object_if_ **|** _error_stmt_ **|** _in_each_ 

[_in_each_ →](#dt:in_each)
     **in** **each** _istemplate_list_ "**{** " _object_statements_ "**}** "  

[_hashif_ →](#dt:hashif)
     "**#if** " **|** **if** 

[_hashelse_ →](#dt:hashelse)
     "**#else** " **|** **else** 

[_object_if_ →](#dt:object_if)
     _hashif_ "**(** " _expression_ "**)** " "**{** " _object_statements_ "**}** " _object_else_ 

[_object_else_ →](#dt:object_else)
     <empty> **|** _hashelse_ "**{** " _object_statements_ "**}** " **|** _hashelse_ _object_if_ 

[_param_ →](#dt:param)
     **param** _objident_ _paramspec_maybe_empty_ **|** **param** _objident_ **auto** "**;** " **|** **param** _objident_ "**:** " _paramspec_ **|** **param** _objident_ "**:** " _ctypedecl_ _paramspec_maybe_empty_ 

[_paramspec_maybe_empty_ →](#dt:paramspec_maybe_empty)
     _paramspec_ **|** "**;** "  

[_paramspec_ →](#dt:paramspec)
     "**=** " _expression_ "**;** " **|** **default** _expression_ "**;** "  

[_method_outparams_ →](#dt:method_outparams)
     <empty> **|** "**- >**" "**(** " _cdecl_list_ "**)** "  

[_method_params_maybe_untyped_ →](#dt:method_params_maybe_untyped)
     "**(** " _cdecl_or_ident_list_ "**)** " _method_outparams_ _throws_ 

[_method_params_typed_ →](#dt:method_params_typed)
     "**(** " _cdecl_list_ "**)** " _method_outparams_ _throws_ 

[_throws_ →](#dt:throws)
     **throws** **|** <empty> 

[_maybe_istemplate_ →](#dt:maybe_istemplate)
     <empty> **|** _istemplate_ 

[_istemplate_ →](#dt:istemplate)
     **is** _istemplate_list_ 

[_istemplate_list_ →](#dt:istemplate_list)
     _objident_ **|** "**(** " _objident_list_ "**)** "  

[_sizespec_ →](#dt:sizespec)
     **size** _expression_ **|** <empty> 

[_offsetspec_ →](#dt:offsetspec)
     "**@** " _expression_ **|** <empty> 

[_cdecl_or_ident_ →](#dt:cdecl_or_ident)
     _named_cdecl_ **|** **inline** _ident_ 

[_named_cdecl_ →](#dt:named_cdecl)
     _cdecl_ 

[_cdecl_ →](#dt:cdecl)
     _basetype_ _cdecl2_ **|** **const** _basetype_ _cdecl2_ 

[_basetype_ →](#dt:basetype)
     _typeident_ **|** _struct_ **|** _layout_ **|** _bitfields_ **|** _typeof_ **|** **sequence** "**(** " _typeident_ "**)** " **|** **hook** "**(** " _cdecl_list_ "**)** "  

[_cdecl2_ →](#dt:cdecl2)
     _cdecl3_ **|** **const** _cdecl2_ **|** "***** " _cdecl2_ **|** **vect** _cdecl2_ 

[_cdecl3_ →](#dt:cdecl3)
     _ident_ **|** <empty> **|** _cdecl3_ "**[** " _expression_ "**]** " **|** _cdecl3_ "**(** " _cdecl_list_opt_ellipsis_ "**)** " **|** "**(** " _cdecl2_ "**)** "  

[_cdecl_list_ →](#dt:cdecl_list)
     <empty> **|** _cdecl_list_nonempty_ 

[_cdecl_list_nonempty_ →](#dt:cdecl_list_nonempty)
     _cdecl_ **|** _cdecl_list_nonempty_ "**,** " _cdecl_ 

[_cdecl_list_opt_ellipsis_ →](#dt:cdecl_list_opt_ellipsis)
     _cdecl_list_ **|** _cdecl_list_ellipsis_ 

[_cdecl_list_ellipsis_ →](#dt:cdecl_list_ellipsis)
     _"..."_ **|** _cdecl_list_nonempty_ "**,** " _"..."_ 

[_cdecl_or_ident_list_ →](#dt:cdecl_or_ident_list)
     <empty> **|** _cdecl_or_ident_list2_ 

[_cdecl_or_ident_list2_ →](#dt:cdecl_or_ident_list2)
     _cdecl_or_ident_ **|** _cdecl_or_ident_list2_ "**,** " _cdecl_or_ident_ 

[_typeof_ →](#dt:typeof)
     **typeof** _expression_ 

[_struct_ →](#dt:struct)
     **struct** "**{** " _struct_decls_ "**}** "  

[_struct_decls_ →](#dt:struct_decls)
     _struct_decls_ _named_cdecl_ "**;** " **|** <empty> 

[_layout_decl_ →](#dt:layout_decl)
     **layout** _utf8_sconst_ "**{** " _layout_decls_ "**}** "  

[_layout_ →](#dt:layout)
     _layout_decl_ 

[_layout_decls_ →](#dt:layout_decls)
     _layout_decls_ _named_cdecl_ "**;** " **|** <empty> 

[_bitfields_ →](#dt:bitfields)
     **bitfields** _integer-literal_ "**{** " _bitfields_decls_ "**}** "  

[_bitfields_decls_ →](#dt:bitfields_decls)
     _bitfields_decls_ _named_cdecl_ "**@** " "**[** " _bitfield_range_ "**]** " "**;** "  

[_bitfield_range_ →](#dt:bitfield_range)
     _expression_ **|** _expression_ "**:** " _expression_ 

[_bitfields_decls_ →](#dt:bitfields_decls-2)
     <empty> 

[_ctypedecl_ →](#dt:ctypedecl)
     _const_opt_ _basetype_ _ctypedecl_ptr_ 

[_ctypedecl_ptr_ →](#dt:ctypedecl_ptr)
     _stars_ _ctypedecl_array_ 

[_stars_ →](#dt:stars)
     <empty> **|** "***** " **const** _stars_ **|** "***** " _stars_ 

[_ctypedecl_array_ →](#dt:ctypedecl_array)
     _ctypedecl_simple_ 

[_ctypedecl_simple_ →](#dt:ctypedecl_simple)
     "**(** " _ctypedecl_ptr_ "**)** " **|** <empty> 

[_const_opt_ →](#dt:const_opt)
     **const** **|** <empty> 

[_typeident_ →](#dt:typeident)
     _ident_ **|** **char** **|** **double** **|** **float** **|** **int** **|** **long** **|** **short** **|** **signed** **|** **unsigned** **|** **void** **|** **register** 

[_assignop_ →](#dt:assignop)
     _expression_ "**+=** " _expression_ **|** _expression_ "**-=** " _expression_ **|** _expression_ "***=** " _expression_ **|** _expression_ "**/=** " _expression_ **|** _expression_ "**%=** " _expression_ **|** _expression_ "**|=** " _expression_ **|** _expression_ "**& =**" _expression_ **|** _expression_ "**^=** " _expression_ **|** _expression_ "**< <=**" _expression_ **|** _expression_ "**> >=**" _expression_ 

[_expression_ →](#dt:expression)
     _expression_ "**?** " _expression_ "**:** " _expression_ **|** _expression_ **#?** _expression_ **#:** _expression_ **|** _expression_ "**+** " _expression_ **|** _expression_ "**-** " _expression_ **|** _expression_ "***** " _expression_ **|** _expression_ "**/** " _expression_ **|** _expression_ "**%** " _expression_ **|** _expression_ "**< <**" _expression_ **|** _expression_ "**> >**" _expression_ **|** _expression_ "**==** " _expression_ **|** _expression_ "**!=** " _expression_ **|** _expression_ "**<** " _expression_ **|** _expression_ "**>** " _expression_ **|** _expression_ "**< =**" _expression_ **|** _expression_ "**> =**" _expression_ **|** _expression_ "**||** " _expression_ **|** _expression_ "**& &**" _expression_ **|** _expression_ "**|** " _expression_ **|** _expression_ "**^** " _expression_ **|** _expression_ "**&** " _expression_ **|** **cast** "**(** " _expression_ "**,** " _ctypedecl_ "**)** " **|** **sizeof** _expression_ **|** "**-** " _expression_ **|** "**+** " _expression_ **|** "**!** " _expression_ **|** "**~** " _expression_ **|** "**&** " _expression_ **|** "***** " _expression_ **|** **defined** _expression_ **|** **stringify** "**(** " _expression_ "**)** " **|** "**++** " _expression_ **|** "**--** " _expression_ **|** _expression_ "**++** " **|** _expression_ "**--** " **|** _expression_ "**(** " "**)** " **|** _expression_ "**(** " _single_initializer_list_ "**)** " **|** _expression_ "**(** " _single_initializer_list_ "**,** " "**)** " **|** _integer-literal_ **|** _hex-literal_ **|** _binary-literal_ **|** _char-literal_ **|** _float-literal_ **|** _string-literal_ 

[_utf8_sconst_ →](#dt:utf8_sconst)
     _string-literal_ 

[_expression_ →](#dt:expression-2)
     **undefined** **|** _objident_ **|** **default** **|** **this** **|** _expression_ "**.** " _objident_ **|** _expression_ "**- >**" _objident_ **|** **sizeoftype** _typeoparg_ 

[_typeoparg_ →](#dt:typeoparg)
     _ctypedecl_ **|** "**(** " _ctypedecl_ "**)** "  

[_expression_ →](#dt:expression-3)
     **new** _ctypedecl_ **|** **new** _ctypedecl_ "**[** " _expression_ "**]** " **|** "**(** " _expression_ "**)** " **|** "**[** " _expression_list_ "**]** " **|** _expression_ "**[** " _expression_ "**]** " **|** _expression_ "**[** " _expression_ "**,** " _identifier_ "**]** " **|** _expression_ "**[** " _expression_ "**:** " _expression_ _endianflag_ "**]** " **|** **each** _objident_ **in** "**(** " _expression_ "**)** "  

[_endianflag_ →](#dt:endianflag)
     "**,** " _identifier_ **|** <empty> 

[_expression_opt_ →](#dt:expression_opt)
     _expression_ **|** <empty> 

[_expression_list_ →](#dt:expression_list)
     <empty> **|** _expression_ **|** _expression_ "**,** " _expression_list_ 

[_expression_list_ntc_nonempty_ →](#dt:expression_list_ntc_nonempty)
     _expression_ **|** _expression_ "**,** " _expression_list_ntc_nonempty_ 

[_composed_string_literal_ →](#dt:composed_string_literal)
     _utf8_sconst_ **|** _composed_string_literal_ "**+** " _utf8_sconst_ 

[_bracketed_string_literal_ →](#dt:bracketed_string_literal)
     _composed_string_literal_ **|** "**(** " _composed_string_literal_ "**)** "  

[_single_initializer_ →](#dt:single_initializer)
     _expression_ **|** "**{** " _single_initializer_list_ "**}** " **|** "**{** " _single_initializer_list_ "**,** " "**}** "  

[_initializer_ →](#dt:initializer)
     _single_initializer_ **|** "**(** " _single_initializer_ "**,** " _single_initializer_list_ "**)** "  

[_single_initializer_list_ →](#dt:single_initializer_list)
     _single_initializer_ **|** _single_initializer_list_ "**,** " _single_initializer_ 

[_single_initializer_ →](#dt:single_initializer-2)
     "**{** " _designated_struct_initializer_list_ "**}** " **|** "**{** " _designated_struct_initializer_list_ "**,** " "**}** " **|** "**{** " _designated_struct_initializer_list_ "**,** " _"..."_ "**}** "  

[_designated_struct_initializer_ →](#dt:designated_struct_initializer)
     "**.** " _ident_ "**=** " _single_initializer_ 

[_designated_struct_initializer_list_ →](#dt:designated_struct_initializer_list)
     _designated_struct_initializer_ **|** _designated_struct_initializer_list_ "**,** " _designated_struct_initializer_ 

[_statement_ →](#dt:statement)
     _statement_except_hashif_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif)
     _compound_statement_ **|** _local_ "**;** " **|** _assign_stmt_ "**;** " **|** _assignop_ "**;** "  

[_assign_stmt_ →](#dt:assign_stmt)
     _assign_chain_ **|** _tuple_literal_ "**=** " _initializer_ 

[_assign_chain_ →](#dt:assign_chain)
     _expression_ "**=** " _assign_chain_ **|** _expression_ "**=** " _initializer_ 

[_tuple_literal_ →](#dt:tuple_literal)
     "**(** " _expression_ "**,** " _expression_list_ntc_nonempty_ "**)** "  

[_statement_except_hashif_ →](#dt:statement_except_hashif-2)
     "**;** " **|** _expression_ "**;** " **|** **if** "**(** " _expression_ "**)** " _statement_ **|** **if** "**(** " _expression_ "**)** " _statement_ **else** _statement_ 

[_statement_ →](#dt:statement-2)
     "**#if** " "**(** " _expression_ "**)** " _statement_ **|** "**#if** " "**(** " _expression_ "**)** " _statement_ "**#else** " _statement_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif-3)
     **while** "**(** " _expression_ "**)** " _statement_ **|** **do** _statement_ **while** "**(** " _expression_ "**)** " "**;** "  

[_for_post_ →](#dt:for_post)
     <empty> **|** _for_post_nonempty_ 

[_for_post_nonempty_ →](#dt:for_post_nonempty)
     _for_post_one_ **|** _for_post_nonempty_ "**,** " _for_post_one_ 

[_for_post_one_ →](#dt:for_post_one)
     _assign_stmt_ **|** _assignop_ **|** _expression_ 

[_for_pre_ →](#dt:for_pre)
     _local_ **|** _for_post_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif-4)
     **for** "**(** " _for_pre_ "**;** " _expression_opt_ "**;** " _for_post_ "**)** " _statement_ **|** **switch** "**(** " _expression_ "**)** " "**{** " _stmt_or_case_list_ "**}** "  

[_stmt_or_case_ →](#dt:stmt_or_case)
     _statement_except_hashif_ **|** _cond_case_statement_ **|** _case_statement_ 

[_cond_case_statement_ →](#dt:cond_case_statement)
     "**#if** " "**(** " _expression_ "**)** " "**{** " _stmt_or_case_list_ "**}** " **|** "**#if** " "**(** " _expression_ "**)** " "**{** " _stmt_or_case_list_ "**}** " "**#else** " "**{** " _stmt_or_case_list_ "**}** "  

[_stmt_or_case_list_ →](#dt:stmt_or_case_list)
     <empty> **|** _stmt_or_case_list_ _stmt_or_case_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif-5)
     **delete** _expression_ "**;** " **|** **try** _statement_ **catch** _statement_ **|** **after** _expression_ _identifier_ "**:** " _expression_ "**;** "  

[_ident_list_ →](#dt:ident_list)
     <empty> **|** _nonempty_ident_list_ 

[_nonempty_ident_list_ →](#dt:nonempty_ident_list)
     _ident_ **|** _nonempty_ident_list_ "**,** " _ident_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif-6)
     **after** _expression_ "**- >**" "**(** " _ident_list_ "**)** " "**:** " _expression_ "**;** " **|** **after** _expression_ "**- >**" _ident_ "**:** " _expression_ "**;** " **|** **after** _expression_ "**:** " _expression_ "**;** " **|** **after** "**:** " _expression_ "**;** " **|** **assert** _expression_ "**;** "  

[_log_kind_ →](#dt:log_kind)
     _identifier_ **|** **error** 

[_log_level_ →](#dt:log_level)
     _expression_ **then** _expression_ **|** _expression_ 

[_statement_except_hashif_ →](#dt:statement_except_hashif-7)
     **log** _log_kind_ "**,** " _log_level_ "**,** " _expression_ "**:** " _bracketed_string_literal_ _log_args_ "**;** " **|** **log** _log_kind_ "**,** " _log_level_ "**:** " _bracketed_string_literal_ _log_args_ "**;** " **|** **log** _log_kind_ "**:** " _bracketed_string_literal_ _log_args_ "**;** "  

[_hashselect_ →](#dt:hashselect)
     "**#select** "  

[_statement_except_hashif_ →](#dt:statement_except_hashif-8)
     _hashselect_ _ident_ **in** "**(** " _expression_ "**)** " **where** "**(** " _expression_ "**)** " _statement_ _hashelse_ _statement_ **|** **foreach** _ident_ **in** "**(** " _expression_ "**)** " _statement_ **|** "**#foreach** " _ident_ **in** "**(** " _expression_ "**)** " _statement_ 

[_case_statement_ →](#dt:case_statement)
     **case** _expression_ "**:** " **|** **default** "**:** "  

[_statement_except_hashif_ →](#dt:statement_except_hashif-9)
     **goto** _ident_ "**;** " **|** **break** "**;** " **|** **continue** "**;** " **|** **throw** "**;** " **|** **return** "**;** " **|** **return** _initializer_ "**;** " **|** _error_stmt_ 

[_error_stmt_ →](#dt:error_stmt)
     **error** "**;** " **|** **error** _bracketed_string_literal_ "**;** "  

[_statement_except_hashif_ →](#dt:statement_except_hashif-10)
     _warning_stmt_ 

[_warning_stmt_ →](#dt:warning_stmt)
     **_warning** _bracketed_string_literal_ "**;** "  

[_log_args_ →](#dt:log_args)
     <empty> **|** _log_args_ "**,** " _expression_ 

[_compound_statement_ →](#dt:compound_statement)
     "**{** " _statement_list_ "**}** "  

[_statement_list_ →](#dt:statement_list)
     <empty> **|** _statement_list_ _statement_ 

[_local_keyword_ →](#dt:local_keyword)
     **local** 

[_static_ →](#dt:static)
     **session** 

[_local_decl_kind_ →](#dt:local_decl_kind)
     _local_keyword_ **|** _static_ 

[_local_ →](#dt:local)
     _local_decl_kind_ _cdecl_ **|** **saved** _cdecl_ **|** _local_decl_kind_ _cdecl_ "**=** " _initializer_ **|** **saved** _cdecl_ "**=** " _initializer_ **|** _local_decl_kind_ "**(** " _cdecl_list_nonempty_ "**)** " **|** **saved** "**(** " _cdecl_list_nonempty_ "**)** " **|** _local_decl_kind_ "**(** " _cdecl_list_nonempty_ "**)** " "**=** " _initializer_ **|** **saved** "**(** " _cdecl_list_nonempty_ "**)** " "**=** " _initializer_ 

[_simple_array_list_ →](#dt:simple_array_list)
     <empty> **|** _simple_array_list_ "**[** " _expression_ "**]** "  

[_hook_decl_ →](#dt:hook_decl)
     **hook** "**(** " _cdecl_list_ "**)** " _ident_ _simple_array_list_ "**;** "  

[_object_ →](#dt:object-6)
     _hook_decl_ 

[_objident_list_ →](#dt:objident_list)
     _objident_ **|** _objident_list_ "**,** " _objident_ 

[_objident_ →](#dt:objident)
     _ident_ **|** **register** 

[_ident_ →](#dt:ident)
     **attribute** **|** **bank** **|** **bitorder** **|** **connect** **|** **constant** **|** **data** **|** **device** **|** **event** **|** **field** **|** **footer** **|** **group** **|** **header** **|** **implement** **|** **import** **|** **interface** **|** **loggroup** **|** **method** **|** **port** **|** **size** **|** **subdevice** **|** **nothrow** **|** **then** **|** **throws** **|** **_header** **|** **provisional** **|** **param** **|** **saved** **|** **independent** **|** **startup** **|** **memoized** **|** _identifier_ **|** **class** **|** **enum** **|** **namespace** **|** **private** **|** **protected** **|** **public** **|** **restrict** **|** **union** **|** **using** **|** **virtual** **|** **volatile** **|** **call** **|** **auto** **|** **static** **|** **select** **|** **async** **|** **await** **|** **with**
[D.6 Backward incompatible changes, not automatically converted](changes-manual.html)
