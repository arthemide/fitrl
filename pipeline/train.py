from datasets import Dataset
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

if __name__ == "__main__":
    train_dataset = Dataset.from_json("data/processed/train.jsonl")
    val_dataset = Dataset.from_json("data/processed/val.jsonl")

    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        task_type="CAUSAL_LM",
    )

    training_args = SFTConfig(
        output_dir="output/Llama-3.2-3B-Instruct-lora",
        max_seq_length=256,
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
    trainer.save_model("output/Llama-3.2-3B-Instruct-lora")
