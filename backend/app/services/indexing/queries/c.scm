; Definitions and imports for C extraction.
(function_definition declarator: (function_declarator declarator: (identifier) @name)) @definition.function
; Pointer-returning functions: `PyObject* _binding_language(...)` where the
; declarator chain is pointer_declarator > function_declarator > identifier.
(function_definition declarator: (pointer_declarator declarator: (function_declarator declarator: (identifier) @name))) @definition.function
(struct_specifier name: (type_identifier) @name) @definition.struct
(enum_specifier name: (type_identifier) @name) @definition.enum
(union_specifier name: (type_identifier) @name) @definition.struct
(type_definition declarator: (type_identifier) @name) @definition.type_alias
(preproc_include) @definition.import