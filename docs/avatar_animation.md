# Avatar Animation Modules

This document describes the lightweight avatar animation helpers found in
`ai_core.avatar`.

## LTXAvatar

```python
from ai_core.avatar import LTXAvatar

avatar = LTXAvatar()
# Produce two seconds of frames.
for frame in avatar.stream("Hello there", seconds=2):
    pass  # send frame to your video pipeline
```

## Expression Controller

```python
from ai_core.avatar import generate_landmarks

landmarks = generate_landmarks("smile please")
print(landmarks["mouth"])
```

## Lip Sync

```python
from ai_core.avatar import align_phonemes

phonemes = ["a", "b", "c"]
durations = [0.5, 0.25, 0.25]  # seconds
mapping = align_phonemes(phonemes, durations, fps=30)
print(mapping[:5])
```
