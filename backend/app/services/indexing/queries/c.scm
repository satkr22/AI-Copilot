(function_definition declarator: (function_declarator declarator: (identifier) @name)) @definition.function
(struct_specifier name: (type_identifier) @name) @definition.struct
(enum_specifier name: (type_identifier) @name) @definition.enum
(union_specifier name: (type_identifier) @name) @definition.struct
(type_definition declarator: (type_identifier) @name) @definition.type_alias
(preproc_include) @definition.import
