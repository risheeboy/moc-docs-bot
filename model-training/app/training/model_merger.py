"""Model merger to combine LoRA adapters with base models."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("model_merger")


class ModelMerger:
    """Merge LoRA adapters with base models."""

    def __init__(self):
        """Initialize model merger."""
        pass

    def merge_lora_adapter(
        self,
        base_model_name: str,
        adapter_path: str,
        output_path: str,
        tokenizer_path: Optional[str] = None,
    ) -> str:
        """Merge LoRA adapter with base model.

        Args:
            base_model_name: Name or path of base model
            adapter_path: Path to LoRA adapter directory
            output_path: Path to save merged model
            tokenizer_path: Path to tokenizer (if different from adapter)

        Returns:
            Path to merged model
        """
        logger.info(
            "Starting model merge",
            extra={
                "base_model": base_model_name,
                "adapter_path": adapter_path,
                "output_path": output_path,
            },
        )

        try:
            # Load base model
            logger.info("Loading base model", extra={"model": base_model_name})
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                load_in_4bit=True,
            )

            # Load LoRA adapter
            logger.info("Loading LoRA adapter", extra={"adapter_path": adapter_path})
            model = PeftModel.from_pretrained(base_model, adapter_path)

            # Merge
            logger.info("Merging LoRA adapter with base model")
            merged_model = model.merge_and_unload()

            # Load tokenizer
            if tokenizer_path and os.path.exists(tokenizer_path):
                tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            else:
                tokenizer = AutoTokenizer.from_pretrained(
                    base_model_name,
                    trust_remote_code=True,
                )

            # Save merged model
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Saving merged model", extra={"output_path": output_path})
            merged_model.save_pretrained(str(output_dir / "model"))
            tokenizer.save_pretrained(str(output_dir / "tokenizer"))

            logger.info(
                "Model merge completed successfully",
                extra={"output_path": output_path},
            )

            return str(output_dir)

        except Exception as e:
            logger.error(
                "Model merge failed",
                extra={
                    "base_model": base_model_name,
                    "adapter_path": adapter_path,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def merge_adapters(
        self,
        base_model_name: str,
        adapter_paths: list,
        output_path: str,
        weights: Optional[list] = None,
    ) -> str:
        """Merge multiple LoRA adapters.

        Args:
            base_model_name: Base model name
            adapter_paths: List of adapter paths to merge
            output_path: Output directory
            weights: Optional weights for combining adapters

        Returns:
            Path to merged model
        """
        logger.info(
            "Merging multiple adapters",
            extra={
                "base_model": base_model_name,
                "adapter_count": len(adapter_paths),
                "output_path": output_path,
            },
        )

        if weights is None:
            weights = [1.0 / len(adapter_paths)] * len(adapter_paths)

        try:
            # Load base model
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                load_in_4bit=True,
            )

            # Load all adapters and merge
            model = base_model
            for i, adapter_path in enumerate(adapter_paths):
                logger.info(
                    f"Loading adapter {i + 1}/{len(adapter_paths)}",
                    extra={"adapter_path": adapter_path},
                )
                model = PeftModel.from_pretrained(model, adapter_path)

                if i < len(adapter_paths) - 1:
                    # Merge intermediate adapters
                    model = model.merge_and_unload()

            # Final merge
            merged_model = model.merge_and_unload()

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                trust_remote_code=True,
            )

            # Save merged model
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            merged_model.save_pretrained(str(output_dir / "model"))
            tokenizer.save_pretrained(str(output_dir / "tokenizer"))

            logger.info(
                "Multiple adapter merge completed",
                extra={"output_path": output_path},
            )

            return str(output_dir)

        except Exception as e:
            logger.error(
                "Multiple adapter merge failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise

    def convert_to_safetensors(
        self,
        model_path: str,
        output_path: str,
    ) -> str:
        """Convert model to safetensors format.

        Args:
            model_path: Path to model
            output_path: Output directory

        Returns:
            Path to converted model
        """
        logger.info(
            "Converting model to safetensors",
            extra={
                "model_path": model_path,
                "output_path": output_path,
            },
        )

        try:
            from safetensors.torch import save_file
            import glob

            model_dir = Path(model_path) / "model"

            # Load model files
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Convert pytorch_model.bin to safetensors
            pytorch_files = glob.glob(str(model_dir / "*.bin"))
            for pytorch_file in pytorch_files:
                model = torch.load(pytorch_file)
                safetensors_file = output_dir / pytorch_file.replace(".bin", ".safetensors")
                save_file(model, str(safetensors_file))
                logger.info(
                    "Converted model file",
                    extra={"input": pytorch_file, "output": str(safetensors_file)},
                )

            # Copy other files
            for ext in ["*.json", "*.txt"]:
                for file in model_dir.glob(ext):
                    import shutil
                    shutil.copy(str(file), str(output_dir / file.name))

            logger.info("Model conversion to safetensors completed")

            return str(output_dir)

        except Exception as e:
            logger.error(
                "Safetensors conversion failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise

    def validate_merged_model(self, model_path: str) -> bool:
        """Validate merged model integrity.

        Args:
            model_path: Path to merged model

        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating merged model", extra={"model_path": model_path})

        try:
            model_dir = Path(model_path)

            # Check required files
            required_files = [
                "model/config.json",
                "tokenizer/tokenizer.json",
            ]

            for required_file in required_files:
                file_path = model_dir / required_file
                if not file_path.exists():
                    logger.error(
                        "Missing required file",
                        extra={"file": required_file},
                    )
                    return False

            # Try loading model
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    str(model_dir / "model"),
                    device_map="cpu",
                    trust_remote_code=True,
                )
                tokenizer = AutoTokenizer.from_pretrained(str(model_dir / "tokenizer"))

                logger.info(
                    "Model validation successful",
                    extra={"model_path": model_path},
                )
                return True

            except Exception as e:
                logger.error(
                    "Failed to load merged model",
                    extra={"error": str(e)},
                    exc_info=True,
                )
                return False

        except Exception as e:
            logger.error(
                "Model validation failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            return False
