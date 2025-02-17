#!/usr/bin/env python3

"""Libdoc JSON schema model definition.

The schema is modeled using pydantic in this file. After updating the model,
execute this file to regenerate the actual schema file in libdoc.json.

https://pydantic-docs.helpmanual.io/usage/schema/
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field, PositiveInt


class SpecVersion(int, Enum):
    """Version of the spec."""
    VERSION = 1


class DocumentationType(str, Enum):
    """Type of the doc: LIBRARY or RESOURCE."""
    LIBRARY = 'LIBRARY'
    RESOURCE = 'RESOURCE'


class LibraryScope(str, Enum):
    "Library scope: GLOBAL, SUITE or TEST."
    GLOBAL = 'GLOBAL'
    SUITE = 'SUITE'
    TEST = 'TEST'


class DocumentationFormat(str, Enum):
    """Documentation format, typically HTML."""
    ROBOT = 'ROBOT'
    HTML = 'HTML'
    TEXT = 'TEXT'
    REST = 'REST'


class ArgumentKind(str, Enum):
    """Argument kind: positional, named, vararg, etc."""
    POSITIONAL_ONLY = 'POSITIONAL_ONLY'
    POSITIONAL_ONLY_MARKER = 'POSITIONAL_ONLY_MARKER'
    POSITIONAL_OR_NAMED = 'POSITIONAL_OR_NAMED'
    VAR_POSITIONAL = 'VAR_POSITIONAL'
    NAMED_ONLY_MARKER = 'NAMED_ONLY_MARKER'
    NAMED_ONLY = 'NAMED_ONLY'
    VAR_NAMED = 'VAR_NAMED'


class Argument(BaseModel):
    """Keyword argument."""
    name: str
    types: List[str]
    typedocs: dict = Field(description="Maps types to type information in 'typedocs'.")
    defaultValue: Union[str, None] = Field(description="Possible default value or 'null'.")
    kind: ArgumentKind
    required: bool
    repr: str

    # Workaround for Pydantic not supporting nullable types.
    # https://github.com/samuelcolvin/pydantic/issues/1270
    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema['properties']['defaultValue']['type'] = ['string', 'null']


class Keyword(BaseModel):
    name: str
    args: List[Argument]
    doc: str
    shortdoc: str
    tags: List[str]
    private: Optional[bool]
    deprecated: Optional[bool]
    source: Path
    lineno: int


class TypeDocType(str, Enum):
    """Type of the type: Standard, Enum, TypedDict or Custom."""
    Standard = 'Standard'
    Enum = 'Enum'
    TypedDict = 'TypedDict'
    Custom = 'Custom'


class EnumMember(BaseModel):
    name: str
    value: str


class TypedDictItem(BaseModel):
    key: str
    type: str
    required: Union[bool, None]    # This is overridden below.

    # Workaround for Pydantic not supporting nullable types.
    # https://github.com/samuelcolvin/pydantic/issues/1270
    class Config:
        @staticmethod
        def schema_extra(schema, model):
            schema['properties']['required']['type'] = ['boolean', 'null']


class TypeDoc(BaseModel):
    type: TypeDocType
    name: str
    doc: str
    usages: List[str] = Field(description='List of keywords using this type.')
    accepts: List[str] = Field(description='List of accepted argument types.')
    members: Optional[List[EnumMember]] = Field(description='Used only with Enum type.')
    items: Optional[List[TypedDictItem]] = Field(description='Used only with TypedDict type.')


class Libdoc(BaseModel):
    """Libdoc JSON spec file schema.

    Compatible with JSON Schema Draft 2020-12.
    """
    specversion: SpecVersion
    name: str
    doc: str
    version: str
    generated: datetime
    type: DocumentationType
    scope: LibraryScope
    docFormat: DocumentationFormat
    source: Path
    lineno: PositiveInt
    tags: List[str] = Field(description='List of all tags used by keywords.')
    inits: List[Keyword]
    keywords: List[Keyword]
    dataTypes: dict = Field({}, description="Deprecated. Use 'typedocs' instead.")
    typedocs: List[TypeDoc]

    # pydantic doesn't add schema version automatically.
    # https://github.com/samuelcolvin/pydantic/issues/1478
    class Config:
        schema_extra = {
            '$schema': 'https://json-schema.org/draft/2020-12/schema'
        }


if __name__ == '__main__':
    path = Path(__file__).parent / 'libdoc.json'
    with open(path, 'w') as f:
        f.write(Libdoc.schema_json(indent=2))
    print(path.absolute())
