# Learning Pipeline

The learning pipeline pairs two utilities:

* `learning_mutator.py` proposes mutations for poorly performing intents.
* `auto_retrain.py` assembles feedback and retrains the model when the system is
  idle.

Both scripts rely on mocked training data in the test suite and ensure failure
paths roll back cleanly. The following tests exercise these flows:

* `tests/test_learning_mutator.py` – verifies existing mutation files are
  preserved when suggestion generation fails.
* `tests/test_auto_retrain.py` – ensures failed fine‑tune attempts log an error
  and trigger any available rollback hooks.

The pipeline can optionally use `vector_memory.persist_snapshot` and
`vector_memory.restore_latest_snapshot` to safeguard the embedding store before
training.
