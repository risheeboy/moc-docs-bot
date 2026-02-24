"""QLoRA fine-tuning implementation."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import time

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments as HFTrainingArguments,
    Trainer,
)
from datasets import Dataset, load_dataset
from peft import get_peft_model, LoraConfig, TaskType

from app.training.training_config import TrainingConfig
from app.utils.logging_config import setup_json_logging
from app.utils.metrics import record_training_job, record_training_duration


logger = setup_json_logging("lora_trainer")


class LoRATrainer:
    """QLoRA fine-tuning trainer for LLMs."""

    def __init__(self, config: TrainingConfig):
        """Initialize LoRA trainer.

        Args:
            config: Training configuration
        """
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.training_state = {
            "status": "initialized",
            "steps_completed": 0,
            "total_steps": 0,
            "current_loss": None,
            "eval_loss": None,
        }

    def prepare_model_and_tokenizer(self) -> Tuple[Any, Any]:
        """Prepare model and tokenizer for training.

        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info(
            "Loading model and tokenizer",
            extra={"model_name": self.config.model_name, "device": self.device},
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
            padding_side="right",
            use_fast=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model with 4-bit quantization
        bnb_config = self._get_bnb_config()

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,
            load_in_4bit=True,
        )

        # Setup LoRA
        lora_config = LoraConfig(
            r=self.config.lora.lora_r,
            lora_alpha=self.config.lora.lora_alpha,
            target_modules=self.config.lora.target_modules,
            lora_dropout=self.config.lora.lora_dropout,
            bias=self.config.lora.bias,
            task_type=TaskType.CAUSAL_LM,
        )

        self.model = get_peft_model(self.model, lora_config)

        logger.info(
            "Model and tokenizer loaded successfully",
            extra={
                "model_name": self.config.model_name,
                "lora_rank": self.config.lora.lora_r,
                "lora_alpha": self.config.lora.lora_alpha,
                "trainable_params": self._count_trainable_params(),
            },
        )

        return self.model, self.tokenizer

    def _get_bnb_config(self) -> Any:
        """Get BitsAndBytes quantization config.

        Returns:
            BnbQuantizationConfig instance
        """
        from transformers import BitsAndBytesConfig

        return BitsAndBytesConfig(
            load_in_4bit=self.config.bnb.load_in_4bit,
            bnb_4bit_quant_type=self.config.bnb.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.config.bnb.bnb_4bit_use_double_quant,
            bnb_4bit_compute_dtype=torch.float16,
        )

    def _count_trainable_params(self) -> int:
        """Count trainable parameters.

        Returns:
            Number of trainable parameters
        """
        trainable_params = 0
        all_params = 0

        for _, param in self.model.named_parameters():
            all_params += param.numel()
            if param.requires_grad:
                trainable_params += param.numel()

        return trainable_params

    def load_dataset(self, dataset_path: str) -> Dataset:
        """Load training dataset from JSONL file.

        Args:
            dataset_path: Path to JSONL dataset

        Returns:
            HuggingFace Dataset
        """
        logger.info("Loading dataset", extra={"dataset_path": dataset_path})

        # Load from JSONL
        examples = []
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))

        # Convert to Dataset
        dataset = Dataset.from_list(examples)

        logger.info(
            "Dataset loaded",
            extra={"dataset_size": len(dataset), "dataset_path": dataset_path},
        )

        return dataset

    def preprocess_dataset(
        self,
        dataset: Dataset,
        max_seq_length: int = 2048,
    ) -> Dataset:
        """Preprocess dataset for training.

        Args:
            dataset: Input dataset
            max_seq_length: Maximum sequence length

        Returns:
            Preprocessed dataset
        """
        logger.info("Preprocessing dataset", extra={"original_size": len(dataset)})

        def formatting_func(examples):
            """Format examples for instruction tuning."""
            output_texts = []
            for instruction, input_text, output_text in zip(
                examples.get("instruction", []),
                examples.get("input", []),
                examples.get("output", []),
            ):
                # Format: [INST] instruction input [/INST] output
                text = f"[INST] {instruction} {input_text} [/INST] {output_text}"
                output_texts.append(text)

            return {
                "text": output_texts,
                "instruction": examples.get("instruction", []),
                "input": examples.get("input", []),
                "output": examples.get("output", []),
            }

        # Apply formatting
        dataset = dataset.map(formatting_func, batched=True, remove_columns=dataset.column_names)

        # Tokenize
        def tokenize_function(examples):
            tokenized = self.tokenizer(
                examples["text"],
                padding="max_length",
                max_length=max_seq_length,
                truncation=True,
                return_tensors=None,
            )
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized

        dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc="Tokenizing dataset",
        )

        logger.info("Dataset preprocessing complete", extra={"processed_size": len(dataset)})

        return dataset

    def train(
        self,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
        job_id: str = "training_job",
    ) -> Dict[str, Any]:
        """Run QLoRA fine-tuning.

        Args:
            train_dataset: Training dataset
            eval_dataset: Evaluation dataset (optional)
            job_id: Job ID for tracking

        Returns:
            Training results dictionary
        """
        start_time = time.time()

        logger.info(
            "Starting QLoRA training",
            extra={
                "job_id": job_id,
                "model_name": self.config.model_name,
                "train_size": len(train_dataset),
                "eval_size": len(eval_dataset) if eval_dataset else 0,
                "epochs": self.config.training_args.num_train_epochs,
                "batch_size": self.config.training_args.per_device_train_batch_size,
            },
        )

        # Record job start
        record_training_job(self.config.model_name, job_id, "started")

        # Prepare training arguments
        training_args = HFTrainingArguments(
            **self.config.training_args.to_dict(),
            run_name=job_id,
        )

        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            callbacks=[
                self._get_progress_callback(job_id),
            ],
        )

        # Run training
        try:
            result = trainer.train()

            duration = time.time() - start_time
            record_training_duration(self.config.model_name, duration)

            logger.info(
                "Training completed successfully",
                extra={
                    "job_id": job_id,
                    "duration_seconds": round(duration, 2),
                    "final_loss": result.training_loss,
                    "final_eval_loss": getattr(result, "eval_loss", None),
                },
            )

            record_training_job(self.config.model_name, job_id, "completed")

            return {
                "status": "completed",
                "job_id": job_id,
                "duration_seconds": duration,
                "training_loss": result.training_loss,
                "eval_loss": getattr(result, "eval_loss", None),
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Training failed",
                extra={
                    "job_id": job_id,
                    "error": str(e),
                    "duration_seconds": round(duration, 2),
                },
                exc_info=True,
            )

            record_training_job(self.config.model_name, job_id, "failed")

            return {
                "status": "failed",
                "job_id": job_id,
                "error": str(e),
                "duration_seconds": duration,
            }

    def _get_progress_callback(self, job_id: str):
        """Get training progress callback.

        Args:
            job_id: Job ID for logging

        Returns:
            Progress callback
        """
        from transformers import TrainerCallback

        class ProgressCallback(TrainerCallback):
            def __init__(self, job_id: str):
                self.job_id = job_id

            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs:
                    logger.debug(
                        "Training progress",
                        extra={
                            "job_id": self.job_id,
                            "step": state.global_step,
                            "loss": logs.get("loss"),
                            "eval_loss": logs.get("eval_loss"),
                        },
                    )

        return ProgressCallback(job_id)

    def save_model(self, output_dir: str) -> str:
        """Save fine-tuned model and LoRA adapter.

        Args:
            output_dir: Directory to save model

        Returns:
            Path to saved model
        """
        logger.info("Saving model", extra={"output_dir": output_dir})

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save LoRA adapter
        self.model.save_pretrained(str(output_path / "adapter"))

        # Save tokenizer
        self.tokenizer.save_pretrained(str(output_path / "tokenizer"))

        # Save config
        config_dict = self.config.to_dict()
        with open(output_path / "training_config.json", "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info("Model saved successfully", extra={"output_dir": output_dir})

        return str(output_path)
