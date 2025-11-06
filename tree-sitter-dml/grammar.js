/**
 * @file DML (Device Modeling Language) 1.4 grammar for tree-sitter
 * @author wangli-ustc
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

const PREC = {
  COMMA: 1,
  ASSIGNMENT: 20,
  CONDITIONAL: 30,
  LOGICAL_OR: 40,
  LOGICAL_AND: 50,
  BITWISE_OR: 60,
  BITWISE_XOR: 70,
  BITWISE_AND: 80,
  EQUALITY: 90,
  RELATIONAL: 100,
  SHIFT: 110,
  ADDITIVE: 120,
  MULTIPLICATIVE: 130,
  CAST: 140,
  UNARY: 150,
  POSTFIX: 160,
};

export default grammar({
  name: 'dml',

  extras: $ => [
    /\s/,
    $.comment,
  ],

  word: $ => $.identifier,

  conflicts: $ => [
    [$.type_declaration, $.expression],
    [$.c_declaration, $.declarator],
    [$.parameter_list, $.expression],
    [$.method_params, $.expression],
    [$.array_spec],
    [$.bitrange_spec],
    [$.object_declaration],
  ],

  rules: {
    // Top-level structure
    source_file: $ => seq(
      optional($.provisional_declaration),
      optional($.device_declaration),
      optional($.bitorder_declaration),
      repeat($._device_statement)
    ),

    provisional_declaration: $ => seq(
      'provisional',
      $.identifier_list,
      ';'
    ),

    device_declaration: $ => seq(
      'device',
      $.identifier,
      ';'
    ),

    bitorder_declaration: $ => seq(
      'bitorder',
      choice('be', 'le'),
      ';'
    ),

    // Device statements
    _device_statement: $ => choice(
      $.template_definition,
      $.object_declaration,
      $.parameter_declaration,
      $.method_declaration,
      $.is_template_statement,
      $.conditional_statement,
      $.error_statement,
      $.in_each_statement,
      $.header_block,
      $.footer_block,
      $.loggroup_declaration,
      $.constant_declaration,
      $.extern_declaration,
      $.typedef_declaration,
      $.import_statement,
      $.export_statement
    ),

    // Template definition
    template_definition: $ => seq(
      'template',
      $.identifier,
      optional(seq('is', $._template_list)),
      '{',
      repeat($._template_statement),
      '}'
    ),

    _template_list: $ => choice(
      $.identifier,
      seq('(', $.identifier_list, ')')
    ),

    _template_statement: $ => choice(
      $.object_declaration,
      $.parameter_declaration,
      $.method_declaration,
      $.shared_method_declaration,
      $.shared_hook_declaration,
      $.is_template_statement,
      $.conditional_statement
    ),

    // Object declarations
    object_declaration: $ => choice(
      $.register_declaration,
      $.field_declaration,
      $.bank_declaration,
      $.group_declaration,
      $.port_declaration,
      $.attribute_declaration,
      $.connect_declaration,
      $.interface_declaration,
      $.event_declaration,
      $.implement_declaration,
      $.subdevice_declaration,
      $.session_declaration,
      $.saved_declaration,
      $.hook_declaration
    ),

    register_declaration: $ => seq(
      'register',
      $.identifier,
      repeat($.array_spec),
      optional($.size_spec),
      optional($.offset_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    field_declaration: $ => seq(
      'field',
      $.identifier,
      repeat($.array_spec),
      optional($.bitrange_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    bank_declaration: $ => seq(
      'bank',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    group_declaration: $ => seq(
      'group',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    port_declaration: $ => seq(
      'port',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    attribute_declaration: $ => seq(
      'attribute',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    connect_declaration: $ => seq(
      'connect',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    interface_declaration: $ => seq(
      'interface',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    event_declaration: $ => seq(
      'event',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    implement_declaration: $ => seq(
      'implement',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    subdevice_declaration: $ => seq(
      'subdevice',
      $.identifier,
      repeat($.array_spec),
      optional(seq('is', $._template_list)),
      $._object_body
    ),

    array_spec: $ => choice(
      seq('[', $.identifier, '<', $.expression, ']'),
      seq('[', $.identifier, '<', '...', ']')
    ),

    size_spec: $ => seq('size', $.expression),

    offset_spec: $ => seq('@', $.expression),

    bitrange_spec: $ => seq(
      '@',
      choice(
        seq('[', $.expression, ']'),
        seq('[', $.expression, ':', $.expression, ']')
      )
    ),

    _object_body: $ => choice(
      seq(optional($.description), ';'),
      seq(optional($.description), '{', repeat($._object_statement), '}')
    ),

    _object_statement: $ => choice(
      $.object_declaration,
      $.parameter_declaration,
      $.method_declaration,
      $.is_template_statement,
      $.conditional_statement,
      $.error_statement
    ),

    description: $ => prec.left(seq(
      $.string_literal,
      repeat(seq('+', $.string_literal))
    )),

    // Data declarations
    session_declaration: $ => choice(
      seq('session', $.c_declaration, ';'),
      seq('session', $.c_declaration, '=', $.initializer, ';'),
      seq('session', '(', $.c_declaration_list, ')', ';'),
      seq('session', '(', $.c_declaration_list, ')', '=', $.initializer, ';')
    ),

    saved_declaration: $ => choice(
      seq('saved', $.c_declaration, ';'),
      seq('saved', $.c_declaration, '=', $.initializer, ';'),
      seq('saved', '(', $.c_declaration_list, ')', ';'),
      seq('saved', '(', $.c_declaration_list, ')', '=', $.initializer, ';')
    ),

    hook_declaration: $ => seq(
      'hook',
      '(',
      $.c_declaration_list,
      ')',
      $.identifier,
      repeat($.array_spec),
      ';'
    ),

    // Parameter declarations
    parameter_declaration: $ => choice(
      seq('param', $.identifier, $._param_spec),
      seq('param', $.identifier, 'auto', ';'),
      seq('param', $.identifier, ':', $._param_spec),
      seq('param', $.identifier, ':', $.type_declaration, $._param_spec)
    ),

    _param_spec: $ => choice(
      ';',
      seq('=', $.expression, ';'),
      seq('default', $.expression, ';')
    ),

    // Method declarations
    method_declaration: $ => choice(
      seq(
        optional($._method_qualifiers),
        'method',
        $.identifier,
        $.method_params,
        optional('default'),
        $.compound_statement
      ),
      seq(
        'inline',
        'method',
        $.identifier,
        $.method_params,
        optional('default'),
        $.compound_statement
      )
    ),

    _method_qualifiers: $ => choice(
      'independent',
      seq('independent', 'startup'),
      seq('independent', 'startup', 'memoized')
    ),

    shared_method_declaration: $ => seq(
      'shared',
      optional($._method_qualifiers),
      'method',
      $.identifier,
      $.method_params,
      choice(
        ';',
        seq('default', $.compound_statement),
        $.compound_statement
      )
    ),

    shared_hook_declaration: $ => seq(
      'shared',
      'hook',
      '(',
      $.c_declaration_list,
      ')',
      $.identifier,
      ';'
    ),

    method_params: $ => seq(
      '(',
      optional($.c_declaration_list),
      ')',
      optional($.output_params),
      optional($.throws_spec)
    ),

    output_params: $ => seq(
      '->',
      '(',
      $.c_declaration_list,
      ')'
    ),

    throws_spec: $ => choice(
      'throws',
      'nothrow'
    ),

    // Type system
    type_declaration: $ => seq(
      optional('const'),
      $._base_type,
      optional($._pointer_spec)
    ),

    _base_type: $ => choice(
      $.type_identifier,
      $.struct_type,
      $.layout_type,
      $.bitfields_type,
      $.typeof_expression,
      $.sequence_type,
      $.hook_type
    ),

    type_identifier: $ => choice(
      $.identifier,
      'char',
      'int',
      'short',
      'long',
      'float',
      'double',
      'signed',
      'unsigned',
      'void',
      'bool'
    ),

    struct_type: $ => seq(
      'struct',
      '{',
      repeat(seq($.c_declaration, ';')),
      '}'
    ),

    layout_type: $ => seq(
      'layout',
      $.string_literal,
      '{',
      repeat(seq($.c_declaration, ';')),
      '}'
    ),

    bitfields_type: $ => seq(
      'bitfields',
      $.integer_literal,
      '{',
      repeat($.bitfield_member),
      '}'
    ),

    bitfield_member: $ => seq(
      $.c_declaration,
      '@',
      '[',
      $._bitfield_range,
      ']',
      ';'
    ),

    _bitfield_range: $ => choice(
      $.expression,
      seq($.expression, ':', $.expression)
    ),

    sequence_type: $ => seq(
      'sequence',
      '(',
      $.type_identifier,
      ')'
    ),

    hook_type: $ => seq(
      'hook',
      '(',
      $.c_declaration_list,
      ')'
    ),

    typeof_expression: $ => seq(
      'typeof',
      $.expression
    ),

    _pointer_spec: $ => repeat1(choice(
      seq('*', optional('const')),
      'vect'
    )),

    // C declarations
    c_declaration: $ => seq(
      optional('const'),
      $._base_type,
      optional($.declarator)
    ),

    declarator: $ => choice(
      $.identifier,
      seq($.declarator, '[', $.expression, ']'),
      seq($.declarator, '(', optional($._c_declaration_list_opt_ellipsis), ')'),
      seq('(', $.declarator, ')'),
      seq('*', optional('const'), $.declarator),
      seq('vect', $.declarator)
    ),

    c_declaration_list: $ => seq(
      $.c_declaration,
      repeat(seq(',', $.c_declaration))
    ),

    _c_declaration_list_opt_ellipsis: $ => choice(
      $.c_declaration_list,
      seq($.c_declaration_list, ',', '...'),
      '...'
    ),

    // Expressions
    expression: $ => choice(
      // Literals
      $.integer_literal,
      $.hex_literal,
      $.binary_literal,
      $.float_literal,
      $.char_literal,
      $.string_literal,
      $.true,
      $.false,
      $.undefined,

      // Identifiers
      $.identifier,
      $.this,
      $.default,

      // Unary operators
      prec(PREC.UNARY, seq('+', $.expression)),
      prec(PREC.UNARY, seq('-', $.expression)),
      prec(PREC.UNARY, seq('!', $.expression)),
      prec(PREC.UNARY, seq('~', $.expression)),
      prec(PREC.UNARY, seq('&', $.expression)),
      prec(PREC.UNARY, seq('*', $.expression)),
      prec(PREC.UNARY, seq('++', $.expression)),
      prec(PREC.UNARY, seq('--', $.expression)),
      prec(PREC.POSTFIX, seq($.expression, '++')),
      prec(PREC.POSTFIX, seq($.expression, '--')),
      prec(PREC.UNARY, seq('sizeof', $.expression)),
      prec(PREC.UNARY, seq('sizeoftype', $.type_declaration)),
      prec(PREC.UNARY, seq('defined', $.expression)),

      // Binary operators
      prec.left(PREC.MULTIPLICATIVE, seq($.expression, '*', $.expression)),
      prec.left(PREC.MULTIPLICATIVE, seq($.expression, '/', $.expression)),
      prec.left(PREC.MULTIPLICATIVE, seq($.expression, '%', $.expression)),
      prec.left(PREC.ADDITIVE, seq($.expression, '+', $.expression)),
      prec.left(PREC.ADDITIVE, seq($.expression, '-', $.expression)),
      prec.left(PREC.SHIFT, seq($.expression, '<<', $.expression)),
      prec.left(PREC.SHIFT, seq($.expression, '>>', $.expression)),
      prec.left(PREC.RELATIONAL, seq($.expression, '<', $.expression)),
      prec.left(PREC.RELATIONAL, seq($.expression, '>', $.expression)),
      prec.left(PREC.RELATIONAL, seq($.expression, '<=', $.expression)),
      prec.left(PREC.RELATIONAL, seq($.expression, '>=', $.expression)),
      prec.left(PREC.EQUALITY, seq($.expression, '==', $.expression)),
      prec.left(PREC.EQUALITY, seq($.expression, '!=', $.expression)),
      prec.left(PREC.BITWISE_AND, seq($.expression, '&', $.expression)),
      prec.left(PREC.BITWISE_XOR, seq($.expression, '^', $.expression)),
      prec.left(PREC.BITWISE_OR, seq($.expression, '|', $.expression)),
      prec.left(PREC.LOGICAL_AND, seq($.expression, '&&', $.expression)),
      prec.left(PREC.LOGICAL_OR, seq($.expression, '||', $.expression)),

      // Ternary
      prec.right(PREC.CONDITIONAL, seq($.expression, '?', $.expression, ':', $.expression)),
      prec.right(PREC.CONDITIONAL, seq($.expression, '#?', $.expression, '#:', $.expression)),

      // Member access
      prec(PREC.POSTFIX, seq($.expression, '.', $.identifier)),
      prec(PREC.POSTFIX, seq($.expression, '->', $.identifier)),

      // Array/bit access
      prec(PREC.POSTFIX, seq($.expression, '[', $.expression, ']')),
      prec(PREC.POSTFIX, seq($.expression, '[', $.expression, ',', $.identifier, ']')),
      prec(PREC.POSTFIX, seq($.expression, '[', $.expression, ':', $.expression, ']')),
      prec(PREC.POSTFIX, seq($.expression, '[', $.expression, ':', $.expression, ',', $.identifier, ']')),

      // Function call
      prec(PREC.POSTFIX, seq($.expression, '(', ')')),
      prec(PREC.POSTFIX, seq($.expression, '(', $.expression_list, ')')),
      prec(PREC.POSTFIX, seq($.expression, '(', $.expression_list, ',', ')')),

      // Type operations
      prec(PREC.CAST, seq('cast', '(', $.expression, ',', $.type_declaration, ')')),
      prec(PREC.UNARY, seq('new', $.type_declaration)),
      prec(PREC.UNARY, seq('new', $.type_declaration, '[', $.expression, ']')),

      // Array literal
      seq('[', $.expression_list, ']'),

      // Each expression
      seq('each', $.identifier, 'in', '(', $.expression, ')'),

      // Grouping
      seq('(', $.expression, ')')
    ),

    expression_list: $ => seq(
      $.expression,
      repeat(seq(',', $.expression))
    ),

    // Statements
    statement: $ => choice(
      $.compound_statement,
      $.expression_statement,
      $.declaration_statement,
      $.assignment_statement,
      $.if_statement,
      $.while_statement,
      $.do_while_statement,
      $.for_statement,
      $.switch_statement,
      $.try_catch_statement,
      $.log_statement,
      $.assert_statement,
      $.after_statement,
      $.foreach_statement,
      $.select_statement,
      $.goto_statement,
      $.break_statement,
      $.continue_statement,
      $.return_statement,
      $.throw_statement,
      $.delete_statement,
      $.error_statement,
      $.warning_statement,
      $.empty_statement
    ),

    compound_statement: $ => seq(
      '{',
      repeat($.statement),
      '}'
    ),

    expression_statement: $ => seq($.expression, ';'),

    declaration_statement: $ => seq($.local_declaration, ';'),

    local_declaration: $ => seq(
      choice('local', 'session', 'saved'),
      choice(
        seq($.c_declaration, optional(seq('=', $.initializer))),
        seq('(', $.c_declaration_list, ')', optional(seq('=', $.initializer)))
      )
    ),

    assignment_statement: $ => choice(
      seq($.expression, '=', $.expression, ';'),
      seq($.expression, '=', $.initializer, ';'),
      seq($.tuple_literal, '=', $.initializer, ';'),
      seq($.expression, '+=', $.expression, ';'),
      seq($.expression, '-=', $.expression, ';'),
      seq($.expression, '*=', $.expression, ';'),
      seq($.expression, '/=', $.expression, ';'),
      seq($.expression, '%=', $.expression, ';'),
      seq($.expression, '&=', $.expression, ';'),
      seq($.expression, '|=', $.expression, ';'),
      seq($.expression, '^=', $.expression, ';'),
      seq($.expression, '<<=', $.expression, ';'),
      seq($.expression, '>>=', $.expression, ';')
    ),

    tuple_literal: $ => seq(
      '(',
      $.expression,
      ',',
      $.expression_list,
      ')'
    ),

    if_statement: $ => choice(
      seq('if', '(', $.expression, ')', $.statement),
      seq('if', '(', $.expression, ')', $.statement, 'else', $.statement),
      seq('#if', '(', $.expression, ')', $.statement),
      seq('#if', '(', $.expression, ')', $.statement, '#else', $.statement)
    ),

    while_statement: $ => seq(
      'while',
      '(',
      $.expression,
      ')',
      $.statement
    ),

    do_while_statement: $ => seq(
      'do',
      $.statement,
      'while',
      '(',
      $.expression,
      ')',
      ';'
    ),

    for_statement: $ => seq(
      'for',
      '(',
      optional($._for_init),
      ';',
      optional($.expression),
      ';',
      optional($._for_post),
      ')',
      $.statement
    ),

    _for_init: $ => choice(
      $.local_declaration,
      $.assignment_statement,
      $.expression
    ),

    _for_post: $ => seq(
      $._for_post_item,
      repeat(seq(',', $._for_post_item))
    ),

    _for_post_item: $ => choice(
      $.assignment_statement,
      $.expression
    ),

    switch_statement: $ => seq(
      'switch',
      '(',
      $.expression,
      ')',
      '{',
      repeat($._switch_case),
      '}'
    ),

    _switch_case: $ => choice(
      $.statement,
      seq('case', $.expression, ':'),
      seq('default', ':'),
      seq('#if', '(', $.expression, ')', '{', repeat($._switch_case), '}'),
      seq('#if', '(', $.expression, ')', '{', repeat($._switch_case), '}', '#else', '{', repeat($._switch_case), '}')
    ),

    try_catch_statement: $ => seq(
      'try',
      $.statement,
      'catch',
      $.statement
    ),

    log_statement: $ => choice(
      seq('log', $._log_kind, ',', $._log_level, ',', $.expression, ':', $.string_literal, repeat(seq(',', $.expression)), ';'),
      seq('log', $._log_kind, ',', $._log_level, ':', $.string_literal, repeat(seq(',', $.expression)), ';'),
      seq('log', $._log_kind, ':', $.string_literal, repeat(seq(',', $.expression)), ';')
    ),

    _log_kind: $ => choice(
      $.identifier,
      'error'
    ),

    _log_level: $ => choice(
      $.expression,
      seq($.expression, 'then', $.expression)
    ),

    assert_statement: $ => seq('assert', $.expression, ';'),

    after_statement: $ => choice(
      seq('after', $.expression, $.identifier, ':', $.expression, ';'),
      seq('after', $.expression, '->', '(', $.identifier_list, ')', ':', $.expression, ';'),
      seq('after', $.expression, '->', $.identifier, ':', $.expression, ';'),
      seq('after', $.expression, ':', $.expression, ';'),
      seq('after', ':', $.expression, ';')
    ),

    foreach_statement: $ => choice(
      seq('foreach', $.identifier, 'in', '(', $.expression, ')', $.statement),
      seq('#foreach', $.identifier, 'in', '(', $.expression, ')', $.statement)
    ),

    select_statement: $ => seq(
      '#select',
      $.identifier,
      'in',
      '(',
      $.expression,
      ')',
      'where',
      '(',
      $.expression,
      ')',
      $.statement,
      'else',
      $.statement
    ),

    goto_statement: $ => seq('goto', $.identifier, ';'),

    break_statement: $ => seq('break', ';'),

    continue_statement: $ => seq('continue', ';'),

    return_statement: $ => choice(
      seq('return', ';'),
      seq('return', $.initializer, ';')
    ),

    throw_statement: $ => seq('throw', ';'),

    delete_statement: $ => seq('delete', $.expression, ';'),

    error_statement: $ => choice(
      seq('error', ';'),
      seq('error', $.string_literal, ';')
    ),

    warning_statement: $ => seq('_warning', $.string_literal, ';'),

    empty_statement: $ => ';',

    // Initializers
    initializer: $ => choice(
      $._single_initializer,
      seq('(', $._single_initializer, ',', $._single_initializer_list, ')')
    ),

    _single_initializer: $ => choice(
      $.expression,
      seq('{', $._single_initializer_list, '}'),
      seq('{', $._single_initializer_list, ',', '}'),
      seq('{', $._designated_initializer_list, '}'),
      seq('{', $._designated_initializer_list, ',', '}'),
      seq('{', $._designated_initializer_list, ',', '...', '}')
    ),

    _single_initializer_list: $ => seq(
      $._single_initializer,
      repeat(seq(',', $._single_initializer))
    ),

    _designated_initializer: $ => seq(
      '.',
      $.identifier,
      '=',
      $._single_initializer
    ),

    _designated_initializer_list: $ => seq(
      $._designated_initializer,
      repeat(seq(',', $._designated_initializer))
    ),

    // Conditional compilation
    conditional_statement: $ => choice(
      seq('#if', '(', $.expression, ')', '{', repeat($._device_statement), '}'),
      seq('#if', '(', $.expression, ')', '{', repeat($._device_statement), '}', '#else', '{', repeat($._device_statement), '}'),
      seq('#if', '(', $.expression, ')', '{', repeat($._device_statement), '}', '#else', $.conditional_statement)
    ),

    in_each_statement: $ => seq(
      'in',
      'each',
      $._template_list,
      '{',
      repeat($._object_statement),
      '}'
    ),

    is_template_statement: $ => seq(
      'is',
      $._template_list,
      ';'
    ),

    // Import and Export
    import_statement: $ => seq(
      'import',
      $.string_literal,
      ';'
    ),

    export_statement: $ => seq(
      'export',
      $.expression,
      'as',
      $.expression,
      ';'
    ),

    // Header and Footer blocks
    header_block: $ => choice(
      seq('header', '%{', $.c_code, '}%'),
      seq('_header', '%{', $.c_code, '}%')
    ),

    footer_block: $ => seq(
      'footer',
      '%{',
      $.c_code,
      '}%'
    ),

    c_code: $ => /[^}]*(?:}(?!%)[^}]*)*/,

    // Other top-level declarations
    loggroup_declaration: $ => seq(
      'loggroup',
      $.identifier,
      ';'
    ),

    constant_declaration: $ => seq(
      'constant',
      $.identifier,
      '=',
      $.expression,
      ';'
    ),

    extern_declaration: $ => seq(
      'extern',
      $.c_declaration,
      ';'
    ),

    typedef_declaration: $ => choice(
      seq('typedef', $.c_declaration, ';'),
      seq('extern', 'typedef', $.c_declaration, ';')
    ),

    // Literals and identifiers
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,

    identifier_list: $ => seq(
      $.identifier,
      repeat(seq(',', $.identifier))
    ),

    integer_literal: $ => /[0-9]+/,

    hex_literal: $ => /0[xX][0-9a-fA-F]+/,

    binary_literal: $ => /0[bB][01]+/,

    float_literal: $ => /[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?/,

    char_literal: $ => /'([^'\\]|\\.)'/,

    string_literal: $ => /"([^"\\]|\\(.|\n))*"/,

    true: $ => 'true',

    false: $ => 'false',

    undefined: $ => 'undefined',

    this: $ => 'this',

    default: $ => 'default',

    // Comments
    comment: $ => choice(
      seq('//', /.*/),
      seq('/*', /[^*]*\*+(?:[^/*][^*]*\*+)*/, '/')
    ),
  }
});
