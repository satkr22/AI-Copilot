; Definitions and imports for JavaScript extraction.
(function_declaration name: (identifier) @name) @definition.function
(generator_function_declaration name: (identifier) @name) @definition.function
; Arrow functions and function expressions assigned to variables
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
; Method definitions (including shorthand, getter, setter)
(method_definition name: (property_identifier) @name) @definition.method
(method_definition name: (private_property_identifier) @name) @definition.method
; Class declaration
(class_declaration name: (identifier) @name) @definition.class
; Named exports: export function foo() {}, export class Foo {}
(export_statement
  declaration: (function_declaration name: (identifier) @name)) @definition.function
(export_statement
  declaration: (class_declaration name: (identifier) @name)) @definition.class
; Default exports: export default function App() {}, export default class App {}
(export_statement
  value: (function_declaration name: (identifier) @name)) @definition.function
(export_statement
  value: (class_declaration name: (identifier) @name)) @definition.class
; Imports (including re-exports)
(import_statement) @definition.import
(export_statement
  source: (string)
  (export_clause)) @definition.import