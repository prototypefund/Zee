import helper
import torchaudio

from timething import align, cutter, dataset  # type: ignore


def test_pause_durations():
    alignment = helper.alignment(
        n_model_frames=30,
        words=[
            align.Segment("hello", 2, 8, 1.0),
            align.Segment("world", 11, 20, 1.0),
        ],
    )

    pauses = cutter.pause_durations(alignment)
    assert pauses == [3, 10]


def test_no_cut():
    alignment = helper.alignment(
        n_model_frames=30,
        words=[
            align.Segment("hello", 2, 8, 1.0),
            align.Segment("world", 11, 20, 1.0),
        ],
    )

    cuts = cutter.pause_cuts(alignment, pause_threshold_model_frames=100)
    assert len(cuts) == 1
    assert cuts[0].label == "hello world"
    assert cuts[0].start == 2
    assert cuts[0].end == 20


def test_one_cut():
    alignment = helper.alignment(
        n_model_frames=30,
        words=[
            align.Segment("hello", 2, 8, 1.0),
            align.Segment("world", 15, 30, 1.0),
        ],
    )

    cuts = cutter.pause_cuts(alignment, pause_threshold_model_frames=5)
    assert len(cuts) == 2
    assert cuts[0].label == "hello"
    assert cuts[0].start == 2
    assert cuts[0].end == 8
    assert cuts[1].label == "world"
    assert cuts[1].start == 15
    assert cuts[1].end == 30


def test_dataset_cut():
    meta = helper.fixtures / "text.csv"
    alignments_path = helper.fixtures / "alignments"
    ds = dataset.SpeechDataset(meta, 16000, alignments_path)
    cuts = cutter.dataset_pause_cuts(
        ds, cut_threshold_seconds=0.15, pause_threshold_model_frames=1
    )

    # note that we can split up a single word, so the cutter just keeps things
    # as they are when applied to the fixtures dataset.
    assert len(cuts) == 1
    assert len(cuts[0].cuts) == 1
    assert cuts[0].cuts[0].label == "One!"


def test_dataset_recut():
    with helper.tempdir() as tmp:
        from_meta = helper.fixtures / "text.csv"
        to_meta = tmp / "recut.csv"
        from_alignments = helper.fixtures / "alignments"
        cut_threshold_seconds = 0.15
        pause_threshold_model_frames = 1
        cutter.dataset_recut(
            from_meta,
            to_meta,
            from_alignments,
            cut_threshold_seconds,
            pause_threshold_model_frames,
        )

        # audio one exists
        one_path = tmp / "audio" / "one-0.mp3"
        one = torchaudio.info(one_path)
        assert one.sample_rate == 44100
        assert one.num_frames > 6000
        assert one.num_channels == 2
        assert one.encoding == "MP3"

        # audio two exists
        two_path = tmp / "audio" / "two.mp3"
        two = torchaudio.info(two_path)
        assert two.sample_rate == 44100
        assert two.num_frames > 6000
        assert two.num_channels == 2
        assert two.encoding == "MP3"

        # csv exists
        df = dataset.read_meta(to_meta).set_index("id")
        assert len(df) == 2

        # text one exists
        one_text = df.loc["audio/one-0.mp3"].transcript
        assert one_text == "One!"

        # text two exists
        two_text = df.loc["audio/two.mp3"].transcript
        assert two_text == "Two?"
