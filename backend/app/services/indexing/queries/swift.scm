(function_declaration name: (simple_identifier) @name) @definition.function
(class_declaration "class" name: (type_identifier) @name) @definition.class
(class_declaration "struct" name: (type_identifier) @name) @definition.struct
(protocol_declaration name: (type_identifier) @name) @definition.interface
(class_declaration "enum" name: (type_identifier) @name) @definition.enum
(typealias_declaration name: (type_identifier) @name) @definition.type_alias
(import_declaration) @definition.import
