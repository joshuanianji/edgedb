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

from edb.common import parsing
from edb.edgeql import ast as qlast

from .expressions import *
from .precedence import *  # NOQA
from .tokens import *  # NOQA


# The main EdgeQL grammar, all of whose productions should start with a
# GrammarToken, that determines the "subgrammar" to use.
#
# To add a new "subgrammar":
# - add a new GrammarToken in tokens.py,
# - add a new production here,
# - add a new token kind in tokenizer.rs,
# - add a mapping from the Python token name into the Rust token kind
#   in parser.rs `fn get_token_kind`
class EdgeQLGrammar(Nonterm):
    "%start"

    @parsing.inline(1)
    def reduce_STARTBLOCK_EdgeQLBlock_EOF(self, *kids):
        pass

    # @parsing.inline(1)
    # def reduce_STARTEXTENSION_CreateExtensionPackageCommandsBlock_EOF(self, *k):
    #     pass

    # @parsing.inline(1)
    # def reduce_STARTMIGRATION_CreateMigrationCommandsBlock_EOF(self, *kids):
    #     pass

    # @parsing.inline(1)
    # def reduce_STARTFRAGMENT_ExprStmt_EOF(self, *kids):
    #     pass

    # @parsing.inline(1)
    # def reduce_STARTFRAGMENT_Expr_EOF(self, *kids):
    #     pass

    # @parsing.inline(1)
    # def reduce_STARTSDLDOCUMENT_SDLDocument(self, *kids):
    #     pass


class Semicolons(Nonterm):
    # one or more semicolons
    @parsing.inline(0)
    def reduce_SEMICOLON(self, tok):
        pass

    @parsing.inline(0)
    def reduce_Semicolons_SEMICOLON(self, semicolons, semicolon):
        pass


class OptSemicolons(Nonterm):
    @parsing.inline(0)
    def reduce_Semicolons(self, semicolons):
        pass

    def reduce_empty(self):
        self.val = None


class EdgeQLBlock(Nonterm):
    @parsing.inline(0)
    def reduce_StatementBlock_OptSemicolons(self, _, _semicolon):
        pass

    def reduce_OptSemicolons(self, _semicolon):
        self.val = []


class SingleStatement(Nonterm):
    @parsing.inline(0)
    def reduce_ExprStmt(self, _):
        # Expressions
        pass


class StatementBlock(
    parsing.ListNonterm, element=SingleStatement, separator=Semicolons
):  # NOQA, Semicolons are from .ddl
    pass
