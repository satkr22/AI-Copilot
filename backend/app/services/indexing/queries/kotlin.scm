(function_declaration (simple_identifier) @name) @definition.function
(class_declaration "class" (type_identifier) @name) @definition.class
(class_declaration "interface" (type_identifier) @name) @definition.interface
(class_declaration "enum" "class" (type_identifier) @name) @definition.enum
(type_alias (type_identifier) @name) @definition.type_alias
(object_declaration (type_identifier) @name) @definition.class
(import_header) @definition.import
