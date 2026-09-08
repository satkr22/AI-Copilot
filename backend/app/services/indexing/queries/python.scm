; Definitions and imports used by the query extraction stage.
(function_definition name: (identifier) @name) @definition.function
(class_definition name: (identifier) @name) @definition.class
; Keep decorators in the symbol byte range.  The extractor also normalizes
; plain function/class matches whose parent is decorated_definition, because
; Tree-sitter can return both the inner and wrapper matches.
(decorated_definition
  definition: (function_definition name: (identifier) @name)
) @definition.function
(decorated_definition
  definition: (class_definition name: (identifier) @name)
) @definition.class
(import_statement) @definition.import
(import_from_statement) @definition.import
