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
    def reduce_Expr(self, *kids):
        pass


class SimpleFor(Nonterm):
    def reduce_For(self, *kids):
        r"%reduce FOR Identifier IN Expr UNION Expr"
        _, alias, _, iterator, _, result = kids
        self.val = qlast.ForQuery(
            iterator_alias=alias.val,
            iterator=iterator.val,
            result=result.val,
        )

    # XXX! This breaks things!!! If this is present, the SELECT thing breaks!!
    def reduce_For2(self, *kids):
        r"%reduce FOR Identifier IN Expr LPAREN Expr RPAREN"
        _, alias, _, iterator, _, result, _ = kids
        self.val = qlast.ForQuery(
            iterator_alias=alias.val,
            iterator=iterator.val,
            result=result.val,
        )

# XXXXX!!!! IT IS ABOUT x(...)!!!!
# IT IS A CONFLICT AND WE ARE NOT FINDING IT!
# BUT ALSO FUCKING OBVIOUSLY.

class Expr(Nonterm):
    @parsing.inline(0)
    def reduce_FuncExpr(self, *kids):
        pass

    # XXX: DROPPING THIS FIXES IT
    @parsing.precedence(precedence.P_DOT)
    def reduce_NodeName(self, *kids):
        self.val = qlast.Path(
            steps=[qlast.ObjectRef(name=kids[0].val.name,
                                   module=kids[0].val.module)])


class FuncExpr(Nonterm):
    def reduce_NodeName_LPAREN_RPAREN(self, *kids):
        name = kids[0].val.name
        self.val = qlast.FunctionCall(func=name, args=[], kwargs={})


class Identifier(Nonterm):
    def reduce_IDENT(self, ident):
        self.val = ident.clean_value


# COULD MERGE THIS INTO IDENTIFIER
class NodeName(Nonterm):
    def reduce_Identifier(self, base_name):
        self.val = qlast.ObjectRef(name=base_name.val)
