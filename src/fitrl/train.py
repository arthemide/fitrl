import os

from datasets import Dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer
import trackio

SPACE_ID = os.getenv("TRACKIO_SPACE_ID")


def run_train(
    data_dir: str = "data/processed",
    output_dir: str = "output/sft",
) -> None:
    if not SPACE_ID:
        raise ValueError("TRACKIO_SPACE_ID environment variable is not set.")

    trackio.init(project="fitrl-sft", space_id=SPACE_ID)

    train_dataset = Dataset.from_json(f"{data_dir}/train.jsonl")
    val_dataset = Dataset.from_json(f"{data_dir}/val.jsonl")

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
        rank_pattern={"default": 8},
        alpha_pattern={"default": 16},
    )

    training_args = SFTConfig(
        output_dir=output_dir,
        max_length=256,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        report_to="trackio",
    )

    trainer = SFTTrainer(
        model="meta-llama/Llama-3.2-3B-Instruct",
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        peft_config=peft_config,
        args=training_args,
    )

    trainer.train()
    trainer.save_model(output_dir)
