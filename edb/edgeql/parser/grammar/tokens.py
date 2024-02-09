#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2008-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from __future__ import annotations

import re
import sys
import types

from edb.common import parsing

from . import keywords
from . import precedence


clean_string = re.compile(r"'(?:\s|\n)+'")
string_quote = re.compile(r'\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$')


class TokenMeta(parsing.TokenMeta):
    pass


class Token(parsing.Token, metaclass=TokenMeta,
            precedence_class=precedence.PrecedenceMeta):
    pass


class GrammarToken(Token):
    """
    Instead of having different grammars, we prefix each query with a special
    grammar token which directs the parser to appropriate grammar.

    This greatly reduces the combined size of grammar specifications, since the
    overlap between grammars is substantial.
    """


class T_STARTBLOCK(GrammarToken):
    pass


class T_LPAREN(Token, lextoken='('):
    pass


class T_RPAREN(Token, lextoken=')'):
    pass


class T_IDENT(Token):
    pass


class T_IN(Token, token="IN"):
    pass


class T_FOR(Token, token="FOR"):
    pass


class T_EOF(Token):
    pass
