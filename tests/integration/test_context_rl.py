import pytest


@pytest.mark.integration
def test_context_env_training_loop():
    pytest.importorskip("gymnasium")
    pytest.importorskip("numpy")
    pytest.importorskip("stable_baselines3")

    from memory.context_env import ContextEnv
    from memory import mental

    mental.init_rl_model()
    assert mental._RL_MODEL is not None

    env = ContextEnv()
    obs, _ = env.reset()
    assert env.observation_space.contains(obs)
    action = env.action_space.sample()
    obs, reward, terminated, truncated, _info = env.step(action)
    assert env.observation_space.contains(obs)

    size_before = mental._RL_MODEL.replay_buffer.size()
    mental._update_rl({"a": 1}, reward)
    assert mental._RL_MODEL.replay_buffer.size() == size_before + 1
