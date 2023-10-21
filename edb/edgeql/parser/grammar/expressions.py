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


class ListNonterm(parsing.ListNonterm, element=None):
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
        r"%reduce FOR Identifier IN AtomicExpr \
                  UNION Expr"
        _, alias, _, iterator, _, result = kids
        self.val = qlast.ForQuery(
            iterator_alias=alias.val,
            iterator=iterator.val,
            result=result.val,
        )

    # XXX! This breaks things!!!
    def reduce_For2(self, *kids):
        r"%reduce FOR Identifier IN AtomicExpr ParenExpr"
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


class BaseAtomicExpr(Nonterm):
    # { ... } | Constant | '(' Expr ')' | FuncExpr
    # | Tuple | NamedTuple | Collection | Set
    # | '__source__' | '__subject__'
    # | '__new__' | '__old__' | '__specified__'
    # | NodeName | PathStep

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

    @parsing.precedence(precedence.P_DOT)
    def reduce_PathStep(self, *kids):
        self.val = qlast.Path(steps=[kids[0].val], partial=True)


class Expr(Nonterm):

    @parsing.inline(0)
    def reduce_BaseAtomicExpr(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_Path(self, *kids):
        pass


def ensure_path(expr):
    if not isinstance(expr, qlast.Path):
        expr = qlast.Path(steps=[expr])
    return expr


class Path(Nonterm):
    @parsing.precedence(precedence.P_DOT)
    def reduce_Expr_PathStep(self, *kids):
        path = ensure_path(kids[0].val)
        path.steps.append(kids[1].val)
        self.val = path


class AtomicExpr(Nonterm):
    @parsing.inline(0)
    def reduce_BaseAtomicExpr(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_AtomicPath(self, *kids):
        pass


# Duplication of Path above, but with BasicExpr at the root
class AtomicPath(Nonterm):
    @parsing.precedence(precedence.P_DOT)
    def reduce_AtomicExpr_PathStep(self, *kids):
        path = ensure_path(kids[0].val)
        path.steps.append(kids[1].val)
        self.val = path


class PathStep(Nonterm):
    def reduce_DOT_PathNodeName(self, *kids):
        from edb.schema import pointers as s_pointers

        self.val = qlast.Ptr(
            name=kids[1].val.name,
            direction=s_pointers.PointerDirection.Outbound
        )


class FuncApplication(Nonterm):
    def reduce_NodeName_LPAREN_OptFuncArgList_RPAREN(self, *kids):
        module = kids[0].val.module
        func_name = kids[0].val.name
        name = func_name if not module else (module, func_name)

        last_named_seen = None
        args = []
        kwargs = {}
        for argname, argname_ctx, arg in kids[2].val:
            if argname is not None:
                if argname in kwargs:
                    raise errors.EdgeQLSyntaxError(
                        f"duplicate named argument `{argname}`",
                        context=argname_ctx)

                last_named_seen = argname
                kwargs[argname] = arg

            else:
                if last_named_seen is not None:
                    raise errors.EdgeQLSyntaxError(
                        f"positional argument after named "
                        f"argument `{last_named_seen}`",
                        context=arg.context)
                args.append(arg)

        self.val = qlast.FunctionCall(func=name, args=args, kwargs=kwargs)


class FuncExpr(Nonterm):
    @parsing.inline(0)
    def reduce_FuncApplication(self, *kids):
        pass


class FuncCallArgExpr(Nonterm):
    def reduce_Expr(self, *kids):
        self.val = (
            None,
            None,
            kids[0].val,
        )

    def reduce_Identifier_ASSIGN_Expr(self, *kids):
        self.val = (
            kids[0].val,
            kids[0].context,
            kids[2].val,
        )

    def reduce_ARGUMENT_ASSIGN_Expr(self, *kids):
        if kids[0].val[1].isdigit():
            raise errors.EdgeQLSyntaxError(
                f"numeric named arguments are not supported",
                context=kids[0].context)
        else:
            raise errors.EdgeQLSyntaxError(
                f"named arguments do not need a '$' prefix, "
                f"rewrite as '{kids[0].val[1:]} := ...'",
                context=kids[0].context)


class FuncCallArg(Nonterm):
    def reduce_FuncCallArgExpr(self, *kids):
        self.val = kids[0].val


class FuncArgList(ListNonterm, element=FuncCallArg, separator=tokens.T_COMMA):
    pass


class OptFuncArgList(Nonterm):
    @parsing.inline(0)
    def reduce_FuncArgList_COMMA(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_FuncArgList(self, *kids):
        pass

    def reduce_empty(self, *kids):
        self.val = []


class Identifier(Nonterm):
    def reduce_IDENT(self, ident):
        self.val = ident.clean_value


# this can appear anywhere
class BaseName(Nonterm):
    def reduce_Identifier(self, *kids):
        self.val = [kids[0].val]

    # @parsing.inline(0)
    # def reduce_QualifiedName(self, *kids):
    #     pass


class NodeName(Nonterm):
    # NOTE: Generic short of fully-qualified name.
    #
    # This name is safe to be used anywhere as it starts with IDENT only.

    def reduce_BaseName(self, base_name):
        self.val = qlast.ObjectRef(
            module='::'.join(base_name.val[:-1]) or None,
            name=base_name.val[-1])


class PathNodeName(Nonterm):
    # NOTE: A non-qualified name that can be an identifier or
    # PARTIAL_RESERVED_KEYWORD.
    #
    # This name is used as part of paths after the DOT as well as in
    # definitions after LINK/POINTER. It can be an identifier including
    # PARTIAL_RESERVED_KEYWORD and does not need to be quoted or
    # parenthesized.

    def reduce_Identifier(self, *kids):
        self.val = qlast.ObjectRef(
            module=None,
            name=kids[0].val)
