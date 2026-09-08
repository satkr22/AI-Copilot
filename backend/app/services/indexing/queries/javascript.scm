(function_declaration name: (identifier) @name) @definition.function
(generator_function_declaration name: (identifier) @name) @definition.function
(lexical_declaration
  (variable_declarator
    name: (identifier) @name
    value: [(arrow_function) (function_expression)])) @definition.function
(variable_declaration
  (variable_declarator
    name: (identifier) @name
    value: [(arrow_function) (function_expression)])) @definition.function
(assignment_expression
  left: (identifier) @name
  right: [(arrow_function) (function_expression)]) @definition.function
(method_definition name: (property_identifier) @name) @definition.method
(method_definition name: (private_property_identifier) @name) @definition.method
(class_declaration name: (identifier) @name) @definition.class
(import_statement) @definition.import
