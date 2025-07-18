import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import model  # type: ignore

from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import WordLevelTrainer


def create_dummy_model(dir_path: Path) -> None:
    tok = Tokenizer(WordLevel(unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    trainer = WordLevelTrainer(special_tokens=["[UNK]"])
    tok.train_from_iterator(["hello world"], trainer=trainer)
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="[UNK]")
    fast.save_pretrained(dir_path)

    config = GPT2Config(
        vocab_size=fast.vocab_size,
        n_positions=8,
        n_embd=8,
        n_layer=1,
        n_head=1,
    )
    model_instance = GPT2LMHeadModel(config)
    model_instance.save_pretrained(dir_path)


def test_load_model_returns_objects(tmp_path):
    create_dummy_model(tmp_path)
    mdl, tok = model.load_model(tmp_path)
    assert mdl is not None
    assert tok is not None
