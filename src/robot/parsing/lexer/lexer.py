#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from itertools import chain

from robot.errors import DataError
from robot.utils import get_error_message, FileReader

from .blocklexers import FileLexer
from .context import InitFileContext, TestCaseFileContext, ResourceFileContext
from .tokenizer import Tokenizer
from .tokens import EOS, END, Token


# FIXME: Documentation for `lang`.
def get_tokens(source, data_only=False, tokenize_variables=False, lang=None):
    """Parses the given source to tokens.

    :param source: The source where to read the data. Can be a path to
        a source file as a string or as ``pathlib.Path`` object, an already
        opened file object, or Unicode text containing the date directly.
        Source files must be UTF-8 encoded.
    :param data_only: When ``False`` (default), returns all tokens. When set
        to ``True``, omits separators, comments, continuation markers, and
        other non-data tokens.
    :param tokenize_variables: When ``True``, possible variables in keyword
        arguments and elsewhere are tokenized. See the
        :meth:`~robot.parsing.lexer.tokens.Token.tokenize_variables`
        method for details.

    Returns a generator that yields :class:`~robot.parsing.lexer.tokens.Token`
    instances.
    """
    lexer = Lexer(TestCaseFileContext(lang=lang), data_only, tokenize_variables)
    lexer.input(source)
    return lexer.get_tokens()


def get_resource_tokens(source, data_only=False, tokenize_variables=False, lang=None):
    """Parses the given source to resource file tokens.

    Otherwise same as :func:`get_tokens` but the source is considered to be
    a resource file. This affects, for example, what settings are valid.
    """
    lexer = Lexer(ResourceFileContext(lang=lang), data_only, tokenize_variables)
    lexer.input(source)
    return lexer.get_tokens()


def get_init_tokens(source, data_only=False, tokenize_variables=False, lang=None):
    """Parses the given source to init file tokens.

    Otherwise same as :func:`get_tokens` but the source is considered to be
    a suite initialization file. This affects, for example, what settings are
    valid.
    """
    lexer = Lexer(InitFileContext(lang=lang), data_only, tokenize_variables)
    lexer.input(source)
    return lexer.get_tokens()


class Lexer:

    def __init__(self, ctx, data_only=False, tokenize_variables=False):
        self.lexer = FileLexer(ctx)
        self.data_only = data_only
        self.tokenize_variables = tokenize_variables
        self.statements = []

    def input(self, source):
        for statement in Tokenizer().tokenize(self._read(source),
                                              self.data_only):
            # Store all tokens but pass only data tokens to lexer.
            self.statements.append(statement)
            if self.data_only:
                data = statement[:]
            else:
                # Separators, comments, etc. already have type, data doesn't.
                data = [t for t in statement if t.type is None]
            if data:
                self.lexer.input(data)

    def _read(self, source):
        try:
            with FileReader(source, accept_text=True) as reader:
                return reader.read()
        except:
            raise DataError(get_error_message())

    def get_tokens(self):
        self.lexer.lex()
        statements = self.statements
        if not self.data_only:
            statements = chain.from_iterable(
                self._split_trailing_commented_and_empty_lines(s)
                for s in statements
            )
        tokens = self._get_tokens(statements)
        if self.tokenize_variables:
            tokens = self._tokenize_variables(tokens)
        return tokens

    def _get_tokens(self, statements):
        if self.data_only:
            ignored_types = {None, Token.COMMENT_HEADER, Token.COMMENT}
        else:
            ignored_types = {None}
        inline_if_type = Token.INLINE_IF
        for statement in statements:
            last = None
            inline_if = False
            for token in statement:
                token_type = token.type
                if token_type in ignored_types:
                    continue
                if token._add_eos_before and not (last and last._add_eos_after):
                    yield EOS.from_token(token, before=True)
                yield token
                if token._add_eos_after:
                    yield EOS.from_token(token)
                if token_type == inline_if_type:
                    inline_if = True
                last = token
            if last and not last._add_eos_after:
                yield EOS.from_token(last)
            if inline_if:
                yield END.from_token(last, virtual=True)
                yield EOS.from_token(last)

    def _split_trailing_commented_and_empty_lines(self, statement):
        lines = self._split_to_lines(statement)
        commented_or_empty = []
        for line in reversed(lines):
            if not self._is_commented_or_empty(line):
                break
            commented_or_empty.append(line)
        if not commented_or_empty:
            return [statement]
        lines = lines[:-len(commented_or_empty)]
        statement = list(chain.from_iterable(lines))
        return [statement] + list(reversed(commented_or_empty))

    def _split_to_lines(self, statement):
        lines = []
        current = []
        for token in statement:
            current.append(token)
            if token.type == Token.EOL:
                lines.append(current)
                current = []
        if current:
            lines.append(current)
        return lines

    def _is_commented_or_empty(self, line):
        separator_or_ignore = (Token.SEPARATOR, None)
        comment_or_eol = (Token.COMMENT, Token.EOL)
        for token in line:
            if token.type not in separator_or_ignore:
                return token.type in comment_or_eol
        return False

    def _tokenize_variables(self, tokens):
        for token in tokens:
            for t in token.tokenize_variables():
                yield t
