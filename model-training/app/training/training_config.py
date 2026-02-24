"""Training configuration and hyperparameters."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

from app.config import get_config


@dataclass
class LoRAConfig:
    """LoRA (Low-Rank Adaptation) configuration."""

    lora_r: int
    lora_alpha: int
    lora_dropout: float = 0.05
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    target_modules: Optional[list] = None

    def __post_init__(self):
        """Set default target modules if not provided."""
        if self.target_modules is None:
            # For Llama and Mistral models
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]


@dataclass
class BitsAndBytesConfig:
    """4-bit quantization configuration."""

    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_compute_dtype: str = "float16"


@dataclass
class TrainingArguments:
    """Hugging Face TrainingArguments configuration."""

    output_dir: str
    num_train_epochs: int
    per_device_train_batch_size: int
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    optim: str = "paged_adamw_8bit"
    save_strategy: str = "steps"
    save_steps: int = 100
    eval_strategy: str = "steps"
    eval_steps: int = 100
    logging_steps: int = 10
    logging_dir: str = "/tmp/logs"
    log_level: str = "info"
    report_to: list = None
    dataloader_pin_memory: bool = True
    remove_unused_columns: bool = False
    seed: int = 42
    bf16: bool = True
    tf32: bool = False
    push_to_hub: bool = False
    hub_strategy: str = "every_save"
    gradient_checkpointing: bool = True

    def __post_init__(self):
        """Set defaults for mutable fields."""
        if self.report_to is None:
            self.report_to = ["tensorboard"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DataConfig:
    """Data processing configuration."""

    max_seq_length: int = 2048
    preprocessing_num_workers: int = 4
    cache_dir: Optional[str] = None
    dataset_cache_dir: Optional[str] = None


class TrainingConfig:
    """Complete training configuration."""

    def __init__(
        self,
        model_name: str,
        output_dir: str,
        train_dataset_path: str,
        eval_dataset_path: Optional[str] = None,
        use_custom_hyperparams: bool = False,
    ):
        """Initialize training config.

        Args:
            model_name: Base model name/ID
            output_dir: Output directory for checkpoints
            train_dataset_path: Path to training data
            eval_dataset_path: Path to evaluation data
            use_custom_hyperparams: Use config from environment variables
        """
        self.model_name = model_name
        self.output_dir = output_dir
        self.train_dataset_path = train_dataset_path
        self.eval_dataset_path = eval_dataset_path

        config = get_config()

        # LoRA configuration
        self.lora = LoRAConfig(
            lora_r=config.TRAINING_LORA_RANK,
            lora_alpha=config.TRAINING_LORA_ALPHA,
        )

        # BitsAndBytes (4-bit quantization)
        self.bnb = BitsAndBytesConfig()

        # Training arguments
        self.training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=config.TRAINING_EPOCHS,
            per_device_train_batch_size=config.TRAINING_BATCH_SIZE,
            gradient_accumulation_steps=config.TRAINING_GRADIENT_ACCUMULATION_STEPS,
            learning_rate=config.TRAINING_LEARNING_RATE,
            warmup_ratio=config.TRAINING_WARMUP_RATIO,
            weight_decay=config.TRAINING_WEIGHT_DECAY,
            max_grad_norm=config.TRAINING_MAX_GRAD_NORM,
        )

        # Data configuration
        self.data = DataConfig(
            max_seq_length=config.TRAINING_MAX_SEQ_LENGTH,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of config
        """
        return {
            "model_name": self.model_name,
            "output_dir": self.output_dir,
            "train_dataset_path": self.train_dataset_path,
            "eval_dataset_path": self.eval_dataset_path,
            "lora": asdict(self.lora),
            "bnb": asdict(self.bnb),
            "training_args": self.training_args.to_dict(),
            "data": asdict(self.data),
        }


def get_default_training_config(
    model_name: str,
    output_dir: str,
    train_dataset_path: str,
    eval_dataset_path: Optional[str] = None,
) -> TrainingConfig:
    """Get default training configuration.

    Args:
        model_name: Base model name
        output_dir: Output directory
        train_dataset_path: Training data path
        eval_dataset_path: Evaluation data path

    Returns:
        Configured TrainingConfig instance
    """
    return TrainingConfig(
        model_name=model_name,
        output_dir=output_dir,
        train_dataset_path=train_dataset_path,
        eval_dataset_path=eval_dataset_path,
        use_custom_hyperparams=True,
    )
