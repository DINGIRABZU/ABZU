# Crown Servant Models

Servant models provide auxiliary language capabilities alongside the primary GLM. Registration follows a simple sequence:

1. **Download weights** with `download_models.py` for each servant (DeepSeek, Mistral, Kimi-K2).
2. **Expose endpoints** by setting environment variables such as `DEEPSEEK_URL`, `MISTRAL_URL`, and `KIMI_K2_URL` or by using the aggregated `SERVANT_MODELS` variable.
3. **Initialize Crown** via `init_crown_agent.initialize_crown()`. During startup the script reads the environment and registers each servant with `servant_model_manager.register_model`.
4. **Invoke through the orchestrator**. Once registered, `crown_prompt_orchestrator` can delegate requests to these servants based on `crown_decider.recommend_llm`; failures fall back to GLM.

This flow keeps servant availability explicit and enables health-based routing across DeepSeek, Mistral, and Kimi-K2.
