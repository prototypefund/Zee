from pathlib import Path

import click

from timething import dataset, job, text, utils  # type: ignore


@click.command()
@click.option("--model", required=True, help="Key in timething/models.yaml.")
@click.option(
    "--metadata",
    required=True,
    type=click.Path(exists=True),
    help="Full path to metadata csv.",
)
@click.option(
    "--alignments-dir",
    required=True,
    type=click.Path(exists=True),
    help="Dir to write results to.",
)
@click.option(
    "--batch-size",
    required=True,
    type=int,
    help="Number of examples per batch",
)
@click.option(
    "--n-workers",
    required=True,
    type=int,
    help="Number of worker processes to use",
)
def main(
    model: str,
    metadata: str,
    alignments_dir: str,
    batch_size: int,
    n_workers: int,
):
    """Timething is a library for aligning text transcripts with audio.

    You provide a audio files, as well as a text file with the complete text
    transcripts. Timething will output a list of time-codes for each word and
    character that indicate when this word or letter was spoken in the audio
    you provided.
    """

    # retrieve the config for the given model
    cfg = utils.load_config(model)

    # construct the dataset
    ds = dataset.SpeechDataset(Path(metadata), cfg.sampling_rate)

    # construct and run the job
    print("setting up aligment job...")
    j = job.Job(
        cfg,
        ds,
        Path(alignments_dir),
        batch_size=batch_size,
        n_workers=n_workers,
    )

    # construct the generic model text cleaner
    ds.clean_text_fn = text.clean_text_fn(cfg.language, j.aligner.vocab())

    # go
    print("starting aligment job...")
    j.run()