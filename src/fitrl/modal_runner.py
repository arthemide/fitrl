import modal

app = modal.App("fitrl")

PROCESSED_DIR = "/data/processed"
OUTPUT_DIR = "/checkpoints/sft"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_sync()
    .add_local_file("pipeline/train.py", remote_path="/root/train.py")
    .add_local_dir("data/processed", remote_path=PROCESSED_DIR)
)

checkpoints_volume = modal.Volume.from_name("fitrl-checkpoints", create_if_missing=True)


@app.function(
    image=image,
    gpu="T4",
    timeout=60 * 60,
    volumes={"/checkpoints": checkpoints_volume},
    secrets=[
        modal.Secret.from_name("hf-token"),
        modal.Secret.from_name("trackio-space-id"),
    ],
)
def run() -> None:
    import sys

    sys.path.insert(0, "/root")
    from train import run_train

    run_train(data_dir=PROCESSED_DIR, output_dir=OUTPUT_DIR)
    checkpoints_volume.commit()
