#
# MIT License
#
# Copyright (c) 2020 Airbyte
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import pytest
from airbyte_cdk.sources.utils.transform import TransformConfig, Transformer

COMPLEX_SCHEMA = {
    "type": "object",
    "properties": {
        "value": {"type": "boolean", "format": "even", "is_positive": True},
        "prop": {"type": "string"},
        "prop_with_null": {"type": ["string", "null"]},
        "number_prop": {"type": "number"},
        "int_prop": {"type": ["integer", "null"]},
        "too_many_types": {"type": ["boolean", "null", "string"]},
        "def": {
            "type": "object",
            "properties": {"dd": {"$ref": "#/definitions/my_type"}},
        },
        "array": {"type": "array", "items": {"$ref": "#/definitions/str_type"}},
        "nested": {"$ref": "#/definitions/nested_type"},
        "list_of_lists": {
            "type": "array",
            "items": {"type": "array", "items": {"type": "string"}},
        },
    },
    "definitions": {
        "str_type": {"type": "string"},
        "nested_type": {"type": "object", "properties": {"a": {"type": "string"}}},
    },
}
VERY_NESTED_SCHEMA = {
    "type": ["null", "object"],
    "properties": {
        "very_nested_value": {
            "type": ["null", "object"],
            "properties": {
                "very_nested_value": {
                    "type": ["null", "object"],
                    "properties": {
                        "very_nested_value": {
                            "type": ["null", "object"],
                            "properties": {
                                "very_nested_value": {
                                    "type": ["null", "object"],
                                    "properties": {"very_nested_value": {"type": ["null", "number"]}},
                                }
                            },
                        }
                    },
                }
            },
        }
    },
}


@pytest.mark.parametrize(
    "schema, actual, expected",
    [
        (
            {"type": "object", "properties": {"value": {"type": "string"}}},
            {"value": 12},
            {"value": "12"},
        ),
        (
            {"type": "object", "properties": {"value": {"type": "string"}}},
            {"value": 12},
            {"value": "12"},
        ),
        (
            COMPLEX_SCHEMA,
            {"value": 1, "array": ["111", 111, {1: 111}]},
            {"value": True, "array": ["111", "111", "{1: 111}"]},
        ),
        (
            COMPLEX_SCHEMA,
            {"value": 1, "list_of_lists": [["111"], [111], [11], [{1: 1}]]},
            {"value": True, "list_of_lists": [["111"], ["111"], ["11"], ["{1: 1}"]]},
        ),
        (
            COMPLEX_SCHEMA,
            {"value": 1, "nested": {"a": [1, 2, 3]}},
            {"value": True, "nested": {"a": "[1, 2, 3]"}},
        ),
        (COMPLEX_SCHEMA, {}, {}),
        (COMPLEX_SCHEMA, {"int_prop": "12"}, {"int_prop": 12}),
        # Skip invalid formattted field and process other fields.
        (
            COMPLEX_SCHEMA,
            {"prop": 12, "number_prop": "aa12", "array": [12]},
            {"prop": "12", "number_prop": "aa12", "array": ["12"]},
        ),
        # Field too_many_types have ambigious type, skip formatting
        (
            COMPLEX_SCHEMA,
            {"prop": 12, "too_many_types": 1212, "array": [12]},
            {"prop": "12", "too_many_types": 1212, "array": ["12"]},
        ),
        # Test null field
        (
            COMPLEX_SCHEMA,
            {"prop": None, "array": [12]},
            {"prop": "None", "array": ["12"]},
        ),
        # If field can be null do not convert
        (
            COMPLEX_SCHEMA,
            {"prop_with_null": None, "array": [12]},
            {"prop_with_null": None, "array": ["12"]},
        ),
        (
            VERY_NESTED_SCHEMA,
            {"very_nested_value": {"very_nested_value": {"very_nested_value": {"very_nested_value": {"very_nested_value": "2"}}}}},
            {"very_nested_value": {"very_nested_value": {"very_nested_value": {"very_nested_value": {"very_nested_value": 2}}}}},
        ),
        (
            VERY_NESTED_SCHEMA,
            {"very_nested_value": {"very_nested_value": None}},
            {"very_nested_value": {"very_nested_value": None}},
        ),
    ],
)
def test_transform(schema, actual, expected):
    t = Transformer(TransformConfig.DefaultSchemaNormalization)
    t.transform(actual, schema)
    assert actual == expected


def test_transform_wrong_config():
    with pytest.raises(Exception, match="NoTransform option cannot be combined with another flags."):
        Transformer(TransformConfig.NoTransform | TransformConfig.DefaultSchemaNormalization)
