# Technology choices and primary evidence

Checked on **9 October 2026**. The three-year research window is **9 October 2023 to 9 October 2026**; the five-year window starts on **9 October 2021**. All three selected papers are peer-reviewed NeurIPS 2024 publications and therefore satisfy both windows.

## Choice for this task

**Use ordinary Python for corpus preparation.** There are 47 short text rows and no supplied images, audio, model weights, or training pairs. Timestamp parsing, checksums, JSONL writing, and grouping need no neural network. This is an engineering choice from the actual input and code structure, not a measured claim that one framework trains faster than another.

| Candidate | Official repository stars at check time | Appropriate job | Decision here |
| --- | ---: | --- | --- |
| Python built-in modules | Not applicable | Parse text; write JSONL; compute hashes; audit metadata | Selected; zero third-party dependencies |
| [TensorFlow](https://github.com/tensorflow/tensorflow) | 200,573 | Tensor/model computation and `tf.data` pipelines | Compare; no training to perform |
| [PyTorch](https://github.com/pytorch/pytorch) | 103,946 | Tensor/model computation and Dataset/DataLoader interfaces | Compare; possible future trainer |
| [OpenCV](https://github.com/opencv/opencv) | 91,127 | Image/video processing | Compare; no visual processing required |
| [Hugging Face Datasets](https://github.com/huggingface/datasets) | 22,043 | Larger reusable datasets and structured dataset operations | Optional later; not imported |

This is a ranking **among inspected official repositories**, not a worldwide top-star ranking. Stars measure popularity; they do not demonstrate reproducibility, correctness, suitability, or the value of this submission. No external ML implementation is copied into the converter. Reproducibility here is supported by the committed input, recorded editorial decisions, deterministic output, and regression checks.

Latest release tags returned by the official GitHub `releases/latest` endpoint were **PyTorch v2.14.1**, **TensorFlow v2.21.0**, and **OpenCV 5.0.0**. Full counts, release dates, and links are recorded in [github_snapshot.json](github_snapshot.json). They are a dated snapshot and can change.

## Official documentation and reference implementations

1. [PyTorch current stable data documentation](https://docs.pytorch.org/docs/stable/data.html), resolving to the [2.14 data API](https://docs.pytorch.org/docs/2.14/data.html), and [official Dataset source](https://github.com/pytorch/pytorch/blob/main/torch/utils/data/dataset.py). Iterable datasets need correctly configured worker copies to avoid repeated data. The docs also warn that out-of-order loading can skew an imbalanced training stream. The current converter uses one process, no loader workers, and no model tensors.
2. [TensorFlow Dataset API](https://www.tensorflow.org/api_docs/python/tf/data/Dataset) and the [v2.21.0 official generator implementation](https://github.com/tensorflow/tensorflow/blob/v2.21.0/tensorflow/python/data/ops/from_generator_op.py). The API page returned a v2.16.1 header, so the relevant behaviour was also checked in the latest-release source. `from_generator` has Python-process and serialisation limits; nested `tf.data` operations inside a generator can grow memory. No such generator, TensorFlow graph, or mutable dataset global is created here.
3. [OpenCV latest-release introduction source](https://github.com/opencv/opencv/blob/5.0.0/modules/core/doc/intro.markdown) and the [5.0.0 official repository README](https://github.com/opencv/opencv/blob/5.0.0/README.md). The served [official introduction](https://docs.opencv.org/4.x/d1/dfb/intro.html) resolved to 4.13.0, and the latest-release website routes checked did not return a readable manual. The documentation was therefore checked directly in the **5.0.0 tagged source**, which describes the image, video, and other computer-vision modules. No OpenCV API is used in this text-only program.

Current official source was checked where the retrieved manual lagged the latest release. No unverified release API is assumed. These are implementation specifications, separate from the peer-reviewed research evidence below. There is no observed framework crash or memory leak to diagnose, so no resolved issue-tracker claim is invented.

## Peer-reviewed research

### 1. DataComp-LM — NeurIPS 2024, Datasets and Benchmarks Track

Li et al., **DataComp-LM: In search of the next generation of training sets for language models**.

- [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/19e4ea30dded58259665db375885e412-Abstract-Datasets_and_Benchmarks_Track.html)
- [Official paper PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/19e4ea30dded58259665db375885e412-Paper-Datasets_and_Benchmarks_Track.pdf)
- [Authors' reference repository](https://github.com/mlfoundations/dclm): 1,475 stars at check time; documented as a research reference, not a high-star dependency selected for this project.

The paper compares data-curation strategies under controlled language-model training and evaluation. It supports treating data design as an experimental choice. **Project inference:** record filtering, edits, and provenance before claiming a dataset is useful. Its large-scale pretraining results do not establish that 47 stream translations improve a model or have commercial demand. This project does not implement DCLM or reproduce its experiments.

### 2. ConStat — NeurIPS 2024, Main Conference Track

Dekoninck, Müller, and Vechev, **ConStat: Performance-Based Contamination Detection in Large Language Models**.

- [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a7f89793b9e6f8c6568dbbb6ff727b9b-Abstract-Conference.html)
- [Official paper PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/a7f89793b9e6f8c6568dbbb6ff727b9b-Paper-Conference.pdf)

The paper studies inflated benchmark performance and a statistical comparison with reference benchmarks and models. **Project inference:** repeated text and one conversation should not support an independent generalisation claim. Hashes and stream grouping check known overlap only; they are not ConStat and cannot establish whether a base model saw the text during pretraining. No contamination-detection p-value is reported here.

### 3. Paloma — NeurIPS 2024, Datasets and Benchmarks Track

Magnusson et al., **Paloma: A Benchmark for Evaluating Language Model Fit**.

- [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/760b2d94398aa61468aa3bc11506d9ea-Abstract-Datasets_and_Benchmarks_Track.html)
- [Official paper PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/760b2d94398aa61468aa3bc11506d9ea-Paper-Datasets_and_Benchmarks_Track.pdf)

Paloma measures language-model fit across 546 domains instead of relying on a single pooled distribution. **Project inference:** show topic/genre/stream counts and group results, so frequent content does not conceal a weak group. Our original human-review summary is not Paloma perplexity, a validated translation metric, or evidence that sampling bias has disappeared.

## What the evidence does not establish

These papers address data curation and evaluation. They do not verify the submitted Nobel Prize attributions, Japanese source meaning, regional dialect, scientific claims, third-party permissions, or buyer interest. Those unknowns are recorded explicitly. Function complexity is derived by inspecting the original algorithms; it is not attributed to an ML paper or an issue thread.
