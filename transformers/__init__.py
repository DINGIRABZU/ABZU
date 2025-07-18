import json
from pathlib import Path

class GPT2Config:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)

    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path)/"config.json").write_text(json.dumps(self.to_dict()))

    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        data = json.loads((Path(path)/"config.json").read_text())
        return cls(**data)

class GPT2LMHeadModel:
    def __init__(self, config):
        self.config = config

    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        cfg = GPT2Config.from_pretrained(path)
        return cls(cfg)

    @classmethod
    def from_config(cls, config):
        return cls(config)

    def save_pretrained(self, path):
        self.config.save_pretrained(path)

    def generate(self, **kwargs):
        return [[0]]

class AutoConfig:
    from_pretrained = GPT2Config.from_pretrained

class AutoModelForCausalLM:
    from_pretrained = GPT2LMHeadModel.from_pretrained
    from_config = GPT2LMHeadModel.from_config

class PreTrainedTokenizerFast:
    def __init__(self, tokenizer_object=None, unk_token="[UNK]"):
        self.tokenizer_object = tokenizer_object
        self.unk_token = unk_token
        self.vocab_size = len(tokenizer_object.get_vocab()) if tokenizer_object else 0

    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path)/"tokenizer.json").write_text("{}")

class AutoTokenizer:
    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        return PreTrainedTokenizerFast()

class GenerationMixin:
    pass

__all__ = [
    "GPT2Config",
    "GPT2LMHeadModel",
    "PreTrainedTokenizerFast",
    "AutoConfig",
    "AutoModelForCausalLM",
    "AutoTokenizer",
    "GenerationMixin",
]
