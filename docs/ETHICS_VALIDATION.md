# Ethics Validation

`EthicalValidator` inspects prompts before they reach the language models. Keyword scanning is combined with a semantic layer powered by optional [SentenceTransformer](https://www.sbert.net/) models.

## Semantic Categories

The validator embeds configured phrases for categories such as **explicit harm**, **lack of consent**, and **bias**. A prompt's embedding is compared to these phrases and any category exceeding the similarity threshold triggers rejection.

```python
validator = EthicalValidator(banned_categories={"harm": ["cause injury"]}, threshold=0.6)
```

If the sentence‑transformers library is unavailable, only keyword checks run.

## Existential Reflection

`ExistentialReflector` offers brief philosophical responses based on the current
emotion and a short history of prompts. The method `reflect_on_dilemma()`
packages the user's question, detected emotion and recent context lines into a
request for the GLM. The returned insight is saved to
`audit_logs/existential_insights.txt` for transparency.

## Reinforcement Learning

User feedback recorded with `db_storage.log_feedback()` provides three reward signals:
`satisfaction`, `ethical_alignment` and `existential_clarity`. `EthicalValidator.apply_feedback()`
passes these rewards to `adaptive_learning` which tunes the validator's similarity threshold
and category lists. The `THRESHOLD_AGENT` adjusts the value after every update so stricter
rules emerge when alignment scores are low.

A Streamlit dashboard at `dashboard/rl_metrics.py` visualises the latest feedback trends
and the current threshold. Launch it with:

```bash
streamlit run dashboard/rl_metrics.py
```

The line chart plots the reward values over time while the threshold display shows the
value used by the validator for semantic checks.

## Emotional‑Quantum Fusion

`apply_emotional_quantum_state()` in `qnl_engine` modulates waveform
properties using the speaker's detected emotion. The helper
`get_emotion_and_tone()` exposes the current emotion alongside a short
"quantum tone" label. When a response is generated, the tone feeds into
the QNL phrase so the resulting audio reflects the emotional state.

