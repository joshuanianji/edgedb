pub const UNRESERVED_KEYWORDS: &[&str] = &[
    "abstract",
    "after",
    "alias",
    "allow",
    "all",
    "annotation",
    "applied",
    "as",
    "asc",
    "assignment",
    "before",
    "by",
    "cardinality",
    "cast",
    "config",
    "conflict",
    "constraint",
    "current",
    "database",
    "ddl",
    "deferrable",
    "deferred",
    "delegated",
    "desc",
    "emit",
    "explicit",
    "expression",
    "extension",
    "final",
    "first",
    "from",
    "function",
    "implicit",
    "index",
    "infix",
    "inheritable",
    "into",
    "isolation",
    "json",
    "last",
    "link",
    "migration",
    "multi",
    "named",
    "object",
    "of",
    "oids",
    "on",
    "only",
    "onto",
    "operator",
    "optionality",
    "overloaded",
    "owned",
    "package",
    "postfix",
    "prefix",
    "property",
    "proposed",
    "pseudo",
    "read",
    "reject",
    "rename",
    "required",
    "repeatable",
    "restrict",
    "role",
    "roles",
    "savepoint",
    "scalar",
    "schema",
    "sdl",
    "serializable",
    "session",
    "single",
    "source",
    "superuser",
    "system",
    "target",
    "ternary",
    "text",
    "then",
    "to",
    "transaction",
    "type",
    "unless",
    "using",
    "verbose",
    "version",
    "view",
    "write",
];


pub const FUTURE_RESERVED_KEYWORDS: &[&str] = &[
    // Keep in sync with `tokenizer::is_keyword`
    "analyze",
    "anyarray",
    "begin",
    "case",
    "check",
    "deallocate",
    "discard",
    "do",
    "end",
    "execute",
    "explain",
    "fetch",
    "get",
    "global",
    "grant",
    "import",
    "listen",
    "load",
    "lock",
    "match",
    "move",
    "notify",
    "prepare",
    "partition",
    "policy",
    "raise",
    "refresh",
    "reindex",
    "revoke",
    "over",
    "when",
    "window",
    // Keep in sync with `tokenizer::is_keyword`
];

pub const CURRENT_RESERVED_KEYWORDS: &[&str] = &[
    // Keep in sync with `tokenizer::is_keyword`
    "__source__",
    "__subject__",
    "__type__",
    "__std__",
    "__edgedbsys__",
    "__edgedbtpl__",
    "__std__",
    "abort",
    "alter",
    "and",
    "anytuple",
    "anytype",
    "commit",
    "configure",
    "create",
    "declare",
    "delete",
    "describe",
    "detached",
    "distinct",
    "drop",
    "else",
    "empty",
    "exists",
    "extending",
    "false",
    "filter",
    "for",
    "group",
    "if",
    "ilike",
    "in",
    "insert",
    "introspect",
    "is",
    "like",
    "limit",
    "module",
    "not",
    "offset",
    "optional",
    "or",
    "order",
    "populate",
    "release",
    "reset",
    "rollback",
    "select",
    "set",
    "start",
    "true",
    "typeof",
    "update",
    "union",
    "variadic",
    "with",
    // Keep in sync with `tokenizer::is_keyword`
];
