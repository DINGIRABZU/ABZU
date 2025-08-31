"""Fine-tune Mistral model on mythological and project corpora."""

from dataclasses import dataclass, field
from typing import Dict, List

__version__ = "0.1.0"


@dataclass
class DatasetConfig:
    """Configuration for a single training dataset."""

    name: str
    path: str
    license: str


@dataclass
class FineTuneConfig:
    """Parameters for fine-tuning the Mistral model."""

    model_name: str = "mistralai/Mistral-7B-v0.3"
    output_dir: str = "models/bana_mistral_7b"
    learning_rate: float = 2e-5
    epochs: int = 3
    datasets: List[DatasetConfig] = field(
        default_factory=lambda: [
            DatasetConfig(
                name="mythology_corpus",
                path="data/mythology_corpus",
                license="CC BY 4.0",
            ),
            DatasetConfig(
                name="project_materials",
                path="data/project_materials",
                license="Proprietary",
            ),
        ]
    )


def build_training_args(config: FineTuneConfig) -> Dict[str, object]:
    """Return a dictionary of arguments for a training loop."""

    return {
        "model_name": config.model_name,
        "output_dir": config.output_dir,
        "learning_rate": config.learning_rate,
        "num_train_epochs": config.epochs,
        "datasets": [dataset.__dict__ for dataset in config.datasets],
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(build_training_args(FineTuneConfig()))
