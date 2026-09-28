import typer

from fitrl import annotate, dataset, parse, split, train

app = typer.Typer()


@app.command()
def parse() -> None:
    """Parse raw .fit files into data/processed/output.csv."""
    parse.run_parse()


@app.command()
def annotate() -> None:
    """Interactively review and correct session labels."""
    annotate.run_annotate()


@app.command()
def split() -> None:
    """Build chronological train/val/test day splits."""
    split.run_split()


@app.command()
def dataset() -> None:
    """Build prompt/completion JSONL datasets from the splits."""
    dataset.run_dataset()


@app.command()
def train(
    data_dir: str = typer.Option("data/processed", help="Directory with train/val JSONL files."),
    output_dir: str = typer.Option("output/sft", help="Directory to save the trained model."),
) -> None:
    """Run SFT training."""
    train.run_train(data_dir=data_dir, output_dir=output_dir)


if __name__ == "__main__":
    app()
