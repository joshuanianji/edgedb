#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2016-present MagicStack Inc. and the EdgeDB authors.
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


import re
import unittest  # NOQA

from edb import errors

from edb.testbase import lang as tb
from edb.edgeql import generate_source as edgeql_to_source
from edb.edgeql.parser import grammar as qlgrammar
from edb.tools import test


class EdgeQLSyntaxTest(tb.BaseSyntaxTest):
    re_filter = re.compile(r'[\s]+|(#.*?(\n|$))|(,(?=\s*[})]))')
    parser_debug_flag = 'DEBUG_EDGEQL'
    markup_dump_lexer = 'sql'
    ast_to_source = edgeql_to_source

    @classmethod
    def get_grammar_token(cls):
        return qlgrammar.tokens.T_STARTBLOCK


class TestEdgeQLParser(EdgeQLSyntaxTest):
    def test_edgeql_syntax_simple_call_01(self):
        """
        SELECT get_nested_obj()
        """
