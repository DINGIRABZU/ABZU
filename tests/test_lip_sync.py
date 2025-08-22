from ai_core.avatar.lip_sync import align_phonemes


def test_align_phonemes_basic():
    phonemes = ["A", "B", "C"]
    durations = [0.5, 0.25, 0.25]
    fps = 20
    mapping = align_phonemes(phonemes, durations, fps)
    # Total frames = 20 fps * 1s
    assert len(mapping) == 20
    # First phoneme spans 10 frames, second and third span 5 each
    assert mapping[0] == (0, "A")
    assert mapping[9] == (9, "A")
    assert mapping[10] == (10, "B")
    assert mapping[14] == (14, "B")
    assert mapping[15] == (15, "C")
    assert mapping[-1] == (19, "C")
    # Verify counts
    assert sum(1 for _, p in mapping if p == "A") == 10
    assert sum(1 for _, p in mapping if p == "B") == 5
    assert sum(1 for _, p in mapping if p == "C") == 5
