(method name: (identifier) @name) @definition.method
(singleton_method name: (_) @name) @definition.method
(class name: (constant) @name) @definition.class
(call method: (identifier) @name (#match? @name "^require")) @definition.import
