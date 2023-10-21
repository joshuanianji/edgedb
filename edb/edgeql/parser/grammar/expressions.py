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

import collections
import typing

from edb.common import parsing, context

from edb.edgeql import ast as qlast
from edb.edgeql import qltypes

from edb import errors

from . import keywords
from . import precedence
from . import tokens

from .precedence import *  # NOQA
from .tokens import *  # NOQA


class Nonterm(parsing.Nonterm):
    pass


class ExprStmt(Nonterm):
    @parsing.inline(0)
    def reduce_SimpleFor(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_SimpleSelect(self, *kids):
        pass


class SimpleFor(Nonterm):
    def reduce_For(self, *kids):
        r"%reduce FOR Identifier IN Expr \
                  UNION Expr"
        _, alias, _, iterator, _, result = kids
        self.val = qlast.ForQuery(
            iterator_alias=alias.val,
            iterator=iterator.val,
            result=result.val,
        )

    # XXX! This breaks things!!!
    def reduce_ForTwo(self, *kids):
        r"%reduce FOR Identifier IN Expr ParenExpr"
        _, alias, _, iterator, result = kids
        self.val = qlast.ForQuery(
            iterator_alias=alias.val,
            iterator=iterator.val,
            result=result.val,
        )


class SimpleSelect(Nonterm):
    def reduce_Select(self, *kids):
        r"%reduce SELECT Expr"

        self.val = qlast.SelectQuery(
            result=kids[1].val,
        )


class ParenExpr(Nonterm):
    @parsing.inline(1)
    def reduce_LPAREN_Expr_RPAREN(self, *kids):
        pass

    @parsing.inline(1)
    def reduce_LPAREN_ExprStmt_RPAREN(self, *kids):
        pass


class Expr(Nonterm):
    @parsing.precedence(precedence.P_UMINUS)
    @parsing.inline(0)
    def reduce_ParenExpr(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_FuncExpr(self, *kids):
        pass

    @parsing.precedence(precedence.P_DOT)
    def reduce_NodeName(self, *kids):
        self.val = qlast.Path(
            steps=[qlast.ObjectRef(name=kids[0].val.name,
                                   module=kids[0].val.module)])


class FuncApplication(Nonterm):
    def reduce_NodeName_LPAREN_RPAREN(self, *kids):
        module = kids[0].val.module
        func_name = kids[0].val.name
        name = func_name if not module else (module, func_name)

        last_named_seen = None
        args = []
        kwargs = {}

        self.val = qlast.FunctionCall(func=name, args=args, kwargs=kwargs)


class FuncExpr(Nonterm):
    @parsing.inline(0)
    def reduce_FuncApplication(self, *kids):
        pass


class Identifier(Nonterm):
    def reduce_IDENT(self, ident):
        self.val = ident.clean_value


# this can appear anywhere
class BaseName(Nonterm):
    def reduce_Identifier(self, *kids):
        self.val = [kids[0].val]


class NodeName(Nonterm):
    def reduce_BaseName(self, base_name):
        self.val = qlast.ObjectRef(
            module='::'.join(base_name.val[:-1]) or None,
            name=base_name.val[-1])
