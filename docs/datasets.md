# Lightweight dataset plan

Keep the first experiment to two downloads:

| Dataset | Direct download | Size | Purpose |
| --- | --- | ---: | --- |
| LJSpeech 1.1 | [Download TAR.BZ2](https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2) | about 2.6 GB | base English voice and text alignment |
| RAVDESS audio speech | [Download ZIP](https://zenodo.org/records/1188976/files/Audio_Speech_Actors_01-24.zip?download=1) | about 208 MB | neutral, happy, sad and angry examples |

Use VCTK only as an optional later step for real learned accent variation:

| Dataset | Direct download | Size | Purpose |
| --- | --- | ---: | --- |
| VCTK 0.92 | [Download ZIP](https://datashare.ed.ac.uk/bitstreams/535f4286-e54c-4038-838c-a02285e32cb2/download) | about 10.9 GB | multiple speakers and accent metadata |

Without VCTK, the accent picker still works through voices installed in the user's browser or operating system. A custom neural model cannot learn British, Australian or Indian delivery from LJSpeech and RAVDESS alone.

## Prepare the manifest

```bash
python -m training.prepare_datasets \
  --ljspeech data/raw/ljspeech \
  --ravdess data/raw/ravdess
```

To include VCTK later, add:

```bash
  --vctk data/raw/vctk
```

Then train with:

```bash
python -m training.train --config training/config.json
```

The included CPU-sized config is suitable for testing the pipeline. Expect training to take a long time and speech quality to remain experimental without a GPU and a stronger model/vocoder.

Review each dataset's official license before redistribution or commercial use. RAVDESS is non-commercial by default; its official record describes licensing options.
