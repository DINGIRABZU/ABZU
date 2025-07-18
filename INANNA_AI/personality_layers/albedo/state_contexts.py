"""Prompt templates for each alchemical state."""

CONTEXTS = {
    "nigredo": "[Nigredo] ({entity}) {text} {triggers} {qcontext}",
    "albedo": "[Albedo] ({entity}) {text} {triggers} {qcontext}",
    "rubedo": "[Rubedo] ({entity}) {text} {triggers} {qcontext}",
}

__all__ = ["CONTEXTS"]
