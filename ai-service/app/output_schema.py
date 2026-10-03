"""Provider grammar schema; length/range validation remains enforced locally."""

import copy

from .models import SemanticResult


def strict_output_schema():
    schema = SemanticResult.model_json_schema()
    definitions = schema.pop("$defs", {})

    def inline(node):
        if isinstance(node, dict):
            if "$ref" in node:
                name = node.pop("$ref").rsplit("/", 1)[-1]
                return inline(copy.deepcopy(definitions[name]) | node)
            return {key: inline(value) for key, value in node.items()}
        if isinstance(node, list):
            return [inline(value) for value in node]
        return node

    schema = inline(schema)

    def normalize(node):
        if isinstance(node, dict):
            for key in (
                "default",
                "title",
                "minLength",
                "maxLength",
                "minimum",
                "maximum",
                "minItems",
                "maxItems",
            ):
                node.pop(key, None)
            if node.get("type") == "object":
                node["required"] = list(node.get("properties", {}))
                node["additionalProperties"] = False
            for value in node.values():
                normalize(value)
        elif isinstance(node, list):
            for value in node:
                normalize(value)

    normalize(schema)
    return schema
