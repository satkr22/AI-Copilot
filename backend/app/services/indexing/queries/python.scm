; Definitions and imports used by the query extraction stage.
(function_definition name: (identifier) @name) @definition.function
(class_definition name: (identifier) @name) @definition.class
(import_statement) @definition.import
(import_from_statement) @definition.import
