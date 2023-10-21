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

    @parsing.inline(0)
    def reduce_Set(self, *kids):
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


class Set(Nonterm):
    def reduce_LBRACE_OptExprList_RBRACE(self, *kids):
        self.val = qlast.Set(elements=kids[1].val)


class OptExprList(Nonterm):
    @parsing.inline(0)
    def reduce_ExprList_COMMA(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_ExprList(self, *kids):
        pass

    def reduce_empty(self, *kids):
        self.val = []


class ExprList(ListNonterm, element=Expr, separator=tokens.T_COMMA):
    pass


class Constant(Nonterm):
    # ARGUMENT
    # | BaseNumberConstant
    # | BaseStringConstant
    # | BaseBooleanConstant
    # | BaseBytesConstant

    def reduce_ARGUMENT(self, *kids):
        self.val = qlast.Parameter(name=kids[0].val[1:])

    @parsing.inline(0)
    def reduce_BaseNumberConstant(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_BaseStringConstant(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_BaseBooleanConstant(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_BaseBytesConstant(self, *kids):
        pass


class BaseNumberConstant(Nonterm):
    def reduce_ICONST(self, *kids):
        self.val = qlast.IntegerConstant(value=kids[0].val)

    def reduce_FCONST(self, *kids):
        self.val = qlast.FloatConstant(value=kids[0].val)

    def reduce_NICONST(self, *kids):
        self.val = qlast.BigintConstant(value=kids[0].val)

    def reduce_NFCONST(self, *kids):
        self.val = qlast.DecimalConstant(value=kids[0].val)


class BaseStringConstant(Nonterm):

    def reduce_SCONST(self, token):
        self.val = qlast.StringConstant(value=token.clean_value)


class BaseBytesConstant(Nonterm):

    def reduce_BCONST(self, bytes_tok):
        self.val = qlast.BytesConstant(value=bytes_tok.clean_value)


class BaseBooleanConstant(Nonterm):
    def reduce_TRUE(self, *kids):
        self.val = qlast.BooleanConstant(value='true')

    def reduce_FALSE(self, *kids):
        self.val = qlast.BooleanConstant(value='false')


def ensure_path(expr):
    if not isinstance(expr, qlast.Path):
        expr = qlast.Path(steps=[expr])
    return expr


def _float_to_path(self, token, context):
    from edb.schema import pointers as s_pointers

    # make sure that the float is of the type 0.1
    parts = token.val.split('.')
    if not (len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()):
        raise errors.EdgeQLSyntaxError(
            f"Unexpected {token.val!r}",
            context=token.context)

    # context for the AST is established manually here
    return [
        qlast.Ptr(
            name=parts[0],
            direction=s_pointers.PointerDirection.Outbound,
            context=context,
        ),
        qlast.Ptr(
            name=parts[1],
            direction=s_pointers.PointerDirection.Outbound,
            context=token.context,
        )
    ]


class Path(Nonterm):
    @parsing.precedence(precedence.P_DOT)
    def reduce_Expr_PathStep(self, *kids):
        path = ensure_path(kids[0].val)
        path.steps.append(kids[1].val)
        self.val = path

    # special case of Path.0.1 etc.
    @parsing.precedence(precedence.P_DOT)
    def reduce_Expr_DOT_FCONST(self, *kids):
        # this is a valid link-like syntax for accessing unnamed tuples
        path = ensure_path(kids[0].val)
        path.steps.extend(_float_to_path(kids[2], kids[1].context))
        self.val = path


class AtomicExpr(Nonterm):
    @parsing.inline(0)
    def reduce_BaseAtomicExpr(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_AtomicPath(self, *kids):
        pass

    @parsing.precedence(precedence.P_TYPECAST)
    def reduce_LANGBRACKET_FullTypeExpr_RANGBRACKET_AtomicExpr(
            self, *kids):
        self.val = qlast.TypeCast(
            expr=kids[3].val,
            type=kids[1].val,
            cardinality_mod=None,
        )


# Duplication of Path above, but with BasicExpr at the root
class AtomicPath(Nonterm):
    @parsing.precedence(precedence.P_DOT)
    def reduce_AtomicExpr_PathStep(self, *kids):
        path = ensure_path(kids[0].val)
        path.steps.append(kids[1].val)
        self.val = path

    # special case of Path.0.1 etc.
    @parsing.precedence(precedence.P_DOT)
    def reduce_AtomicExpr_DOT_FCONST(self, *kids):
        # this is a valid link-like syntax for accessing unnamed tuples
        path = ensure_path(kids[0].val)
        path.steps.extend(_float_to_path(kids[2], kids[1].context))
        self.val = path


class PathStep(Nonterm):
    def reduce_DOT_PathStepName(self, *kids):
        from edb.schema import pointers as s_pointers

        self.val = qlast.Ptr(
            name=kids[1].val.name,
            direction=s_pointers.PointerDirection.Outbound
        )

    def reduce_DOT_ICONST(self, *kids):
        # this is a valid link-like syntax for accessing unnamed tuples
        from edb.schema import pointers as s_pointers

        self.val = qlast.Ptr(
            name=kids[1].val,
            direction=s_pointers.PointerDirection.Outbound
        )

    def reduce_DOTBW_PathStepName(self, *kids):
        from edb.schema import pointers as s_pointers

        self.val = qlast.Ptr(
            name=kids[1].val.name,
            direction=s_pointers.PointerDirection.Inbound
        )

    def reduce_AT_PathNodeName(self, *kids):
        from edb.schema import pointers as s_pointers

        self.val = qlast.Ptr(
            name=kids[1].val.name,
            direction=s_pointers.PointerDirection.Outbound,
            type='property'
        )

    @parsing.inline(0)
    def reduce_TypeIntersection(self, *kids):
        pass


class TypeIntersection(Nonterm):
    def reduce_LBRACKET_IS_FullTypeExpr_RBRACKET(self, *kids):
        self.val = qlast.TypeIntersection(
            type=kids[2].val,
        )


class OptTypeIntersection(Nonterm):
    @parsing.inline(0)
    def reduce_TypeIntersection(self, *kids):
        pass

    def reduce_empty(self):
        self.val = None


# Used in free shapes
class FreeStepName(Nonterm):
    @parsing.inline(0)
    def reduce_ShortNodeName(self, *kids):
        pass

    def reduce_DUNDERTYPE(self, *kids):
        self.val = qlast.ObjectRef(name=kids[0].val)


# Used in shapes, paths and in PROPERTY/LINK definitions.
class PathStepName(Nonterm):
    @parsing.inline(0)
    def reduce_PathNodeName(self, *kids):
        pass

    def reduce_DUNDERTYPE(self, *kids):
        self.val = qlast.ObjectRef(name=kids[0].val)


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

    def reduce_AnyIdentifier_ASSIGN_Expr(self, *kids):
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


class PosCallArg(Nonterm):
    def reduce_Expr(self, *kids):
        self.val = kids[0].val


class PosCallArgList(ListNonterm, element=PosCallArg,
                     separator=tokens.T_COMMA):
    pass


class OptPosCallArgList(Nonterm):
    @parsing.inline(0)
    def reduce_PosCallArgList(self, *kids):
        pass

    def reduce_empty(self, *kids):
        self.val = []


class Identifier(Nonterm):
    def reduce_IDENT(self, ident):
        self.val = ident.clean_value

    @parsing.inline(0)
    def reduce_UnreservedKeyword(self, *_):
        pass


class PtrIdentifier(Nonterm):
    @parsing.inline(0)
    def reduce_Identifier(self, *_):
        pass

    @parsing.inline(0)
    def reduce_PartialReservedKeyword(self, *_):
        pass


class AnyIdentifier(Nonterm):
    @parsing.inline(0)
    def reduce_PtrIdentifier(self, *kids):
        pass

    def reduce_ReservedKeyword(self, *kids):
        name = kids[0].val
        if name[:2] == '__' and name[-2:] == '__':
            # There are a few reserved keywords like __std__ and __subject__
            # that can be used in paths but are prohibited to be used
            # anywhere else. So just as the tokenizer prohibits using
            # __names__ in general, we enforce the rule here for the
            # few remaining reserved __keywords__.
            raise errors.EdgeQLSyntaxError(
                "identifiers surrounded by double underscores are forbidden",
                context=kids[0].context)

        self.val = name


class DottedIdents(
        ListNonterm, element=AnyIdentifier, separator=tokens.T_DOT):
    pass


class DotName(Nonterm):
    def reduce_DottedIdents(self, *kids):
        self.val = '.'.join(part for part in kids[0].val)


class ModuleName(
        ListNonterm, element=DotName, separator=tokens.T_DOUBLECOLON):
    pass


class ColonedIdents(
        ListNonterm, element=AnyIdentifier, separator=tokens.T_DOUBLECOLON):
    pass


class QualifiedName(Nonterm):
    def reduce_Identifier_DOUBLECOLON_ColonedIdents(self, ident, _, idents):
        assert ident.val
        assert idents.val
        self.val = [ident.val, *idents.val]

    def reduce_DUNDERSTD_DOUBLECOLON_ColonedIdents(self, _s, _c, idents):
        assert idents.val
        self.val = ['__std__', *idents.val]


# this can appear anywhere
class BaseName(Nonterm):
    def reduce_Identifier(self, *kids):
        self.val = [kids[0].val]

    @parsing.inline(0)
    def reduce_QualifiedName(self, *kids):
        pass


# this can appear in link/property definitions
class PtrName(Nonterm):
    def reduce_PtrIdentifier(self, ptr_identifier):
        assert ptr_identifier.val
        self.val = [ptr_identifier.val]

    @parsing.inline(0)
    def reduce_QualifiedName(self, *_):
        pass


# Non-collection type.
class SimpleTypeName(Nonterm):
    def reduce_PtrNodeName(self, *kids):
        self.val = qlast.TypeName(maintype=kids[0].val)

    def reduce_ANYTYPE(self, *kids):
        self.val = qlast.TypeName(
            maintype=qlast.PseudoObjectRef(name='anytype')
        )

    def reduce_ANYTUPLE(self, *kids):
        self.val = qlast.TypeName(
            maintype=qlast.PseudoObjectRef(name='anytuple')
        )

    def reduce_ANYOBJECT(self, *kids):
        self.val = qlast.TypeName(
            maintype=qlast.PseudoObjectRef(name='anyobject')
        )


class SimpleTypeNameList(ListNonterm, element=SimpleTypeName,
                         separator=tokens.T_COMMA):
    pass


class CollectionTypeName(Nonterm):

    def validate_subtype_list(self, lst):
        has_nonstrval = has_strval = has_items = False
        for el in lst.val:
            if isinstance(el, qlast.TypeExprLiteral):
                has_strval = True
            elif isinstance(el, qlast.TypeName):
                if el.name:
                    has_items = True
                else:
                    has_nonstrval = True

        if (has_nonstrval or has_items) and has_strval:
            # Prohibit cases like `tuple<a: int64, 'aaaa'>` and
            # `enum<bbbb, 'aaaa'>`
            raise errors.EdgeQLSyntaxError(
                "mixing string type literals and type names is not supported",
                context=lst.context)

        if has_items and has_nonstrval:
            # Prohibit cases like `tuple<a: int64, int32>`
            raise errors.EdgeQLSyntaxError(
                "mixing named and unnamed subtype declarations "
                "is not supported",
                context=lst.context)

    def reduce_NodeName_LANGBRACKET_RANGBRACKET(self, *kids):
        # Constructs like `enum<>` or `array<>` aren't legal.
        raise errors.EdgeQLSyntaxError(
            'parametrized type must have at least one argument',
            context=kids[1].context,
        )

    def reduce_NodeName_LANGBRACKET_SubtypeList_RANGBRACKET(self, *kids):
        self.validate_subtype_list(kids[2])
        self.val = qlast.TypeName(
            maintype=kids[0].val,
            subtypes=kids[2].val,
        )

    def reduce_NodeName_LANGBRACKET_SubtypeList_COMMA_RANGBRACKET(self, *kids):
        self.validate_subtype_list(kids[2])
        self.val = qlast.TypeName(
            maintype=kids[0].val,
            subtypes=kids[2].val,
        )


class TypeName(Nonterm):
    @parsing.inline(0)
    def reduce_SimpleTypeName(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_CollectionTypeName(self, *kids):
        pass


class TypeNameList(ListNonterm, element=TypeName,
                   separator=tokens.T_COMMA):
    pass


# A type expression that is not a simple type.
class NontrivialTypeExpr(Nonterm):
    def reduce_TYPEOF_Expr(self, *kids):
        self.val = qlast.TypeOf(expr=kids[1].val)

    @parsing.inline(1)
    def reduce_LPAREN_FullTypeExpr_RPAREN(self, *kids):
        pass

    def reduce_TypeExpr_PIPE_TypeExpr(self, *kids):
        self.val = qlast.TypeOp(left=kids[0].val, op='|',
                                right=kids[2].val)

    def reduce_TypeExpr_AMPER_TypeExpr(self, *kids):
        self.val = qlast.TypeOp(left=kids[0].val, op='&',
                                right=kids[2].val)


# This is a type expression without angle brackets, so it
# can be used without parentheses in a context where the
# angle bracket has a different meaning.
class TypeExpr(Nonterm):
    @parsing.inline(0)
    def reduce_SimpleTypeName(self, *kids):
        pass

    @parsing.inline(0)
    def reduce_NontrivialTypeExpr(self, *kids):
        pass


# A type expression enclosed in parentheses
class ParenTypeExpr(Nonterm):
    @parsing.inline(1)
    def reduce_LPAREN_FullTypeExpr_RPAREN(self, *kids):
        pass


# This is a type expression which includes collection types,
# so it can only be directly used in a context where the
# angle bracket is unambiguous.
class FullTypeExpr(Nonterm):
    @parsing.inline(0)
    def reduce_TypeName(self, *kids):
        pass

    def reduce_TYPEOF_Expr(self, *kids):
        self.val = qlast.TypeOf(expr=kids[1].val)

    @parsing.inline(1)
    def reduce_LPAREN_FullTypeExpr_RPAREN(self, *kids):
        pass

    def reduce_FullTypeExpr_PIPE_FullTypeExpr(self, *kids):
        self.val = qlast.TypeOp(left=kids[0].val, op='|',
                                right=kids[2].val)

    def reduce_FullTypeExpr_AMPER_FullTypeExpr(self, *kids):
        self.val = qlast.TypeOp(left=kids[0].val, op='&',
                                right=kids[2].val)


class Subtype(Nonterm):
    @parsing.inline(0)
    def reduce_FullTypeExpr(self, *kids):
        pass

    def reduce_Identifier_COLON_FullTypeExpr(self, *kids):
        self.val = kids[2].val
        self.val.name = kids[0].val

    def reduce_BaseStringConstant(self, *kids):
        # TODO: Raise a DeprecationWarning once we have facility for that.
        self.val = qlast.TypeExprLiteral(
            val=kids[0].val,
        )

    def reduce_BaseNumberConstant(self, *kids):
        self.val = qlast.TypeExprLiteral(
            val=kids[0].val,
        )


class SubtypeList(ListNonterm, element=Subtype, separator=tokens.T_COMMA):
    pass


class NodeName(Nonterm):
    # NOTE: Generic short of fully-qualified name.
    #
    # This name is safe to be used anywhere as it starts with IDENT only.

    def reduce_BaseName(self, base_name):
        self.val = qlast.ObjectRef(
            module='::'.join(base_name.val[:-1]) or None,
            name=base_name.val[-1])


class NodeNameList(ListNonterm, element=NodeName, separator=tokens.T_COMMA):
    pass


class PtrNodeName(Nonterm):
    # NOTE: Generic short of fully-qualified name.
    #
    # This name is safe to be used in most DDL and SDL definitions.

    def reduce_PtrName(self, ptr_name):
        self.val = qlast.ObjectRef(
            module='::'.join(ptr_name.val[:-1]) or None,
            name=ptr_name.val[-1])


class PtrQualifiedNodeName(Nonterm):
    def reduce_QualifiedName(self, *kids):
        self.val = qlast.ObjectRef(
            module='::'.join(kids[0].val[:-1]),
            name=kids[0].val[-1])


class ShortNodeName(Nonterm):
    # NOTE: A non-qualified name that can be an identifier or
    # UNRESERVED_KEYWORD.
    #
    # This name is used as part of paths after the DOT. It can be an
    # identifier including UNRESERVED_KEYWORD and does not need to be
    # quoted or parenthesized.

    def reduce_Identifier(self, *kids):
        self.val = qlast.ObjectRef(
            module=None,
            name=kids[0].val)


# ShortNodeNameList is needed in DDL, but it's worthwhile to define it
# here, near ShortNodeName.
class ShortNodeNameList(ListNonterm, element=ShortNodeName,
                        separator=tokens.T_COMMA):
    pass


class PathNodeName(Nonterm):
    # NOTE: A non-qualified name that can be an identifier or
    # PARTIAL_RESERVED_KEYWORD.
    #
    # This name is used as part of paths after the DOT as well as in
    # definitions after LINK/POINTER. It can be an identifier including
    # PARTIAL_RESERVED_KEYWORD and does not need to be quoted or
    # parenthesized.

    def reduce_PtrIdentifier(self, *kids):
        self.val = qlast.ObjectRef(
            module=None,
            name=kids[0].val)


class AnyNodeName(Nonterm):
    # NOTE: A non-qualified name that can be ANY identifier.
    #
    # This name is used as part of paths after the DOT. It can be any
    # identifier including RESERVED_KEYWORD and UNRESERVED_KEYWORD and
    # does not need to be quoted or parenthesized.
    #
    # This is mainly used in DDL statements that have another keyword
    # completely disambiguating that what comes next is a name. It
    # CANNOT be used in Expr productions because it will cause
    # ambiguity with NodeName, etc.

    def reduce_AnyIdentifier(self, *kids):
        self.val = qlast.ObjectRef(
            module=None,
            name=kids[0].val)


class KeywordMeta(parsing.NontermMeta):
    def __new__(mcls, name, bases, dct, *, type):
        result = super().__new__(mcls, name, bases, dct)

        assert type in keywords.keyword_types

        for token in keywords.by_type[type].values():
            def method(inst, *kids):
                inst.val = kids[0].val
            method = context.has_context(method)
            method.__doc__ = "%%reduce %s" % token
            method.__name__ = 'reduce_%s' % token
            setattr(result, method.__name__, method)

        return result

    def __init__(cls, name, bases, dct, *, type):
        super().__init__(name, bases, dct)


class UnreservedKeyword(Nonterm, metaclass=KeywordMeta,
                        type=keywords.UNRESERVED_KEYWORD):
    pass


class PartialReservedKeyword(Nonterm, metaclass=KeywordMeta,
                             type=keywords.PARTIAL_RESERVED_KEYWORD):
    pass


class ReservedKeyword(Nonterm, metaclass=KeywordMeta,
                      type=keywords.RESERVED_KEYWORD):
    pass
