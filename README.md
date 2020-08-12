# DVC Tutorial (YOLOv3 usecase)

DVC is a version control system built to make models shareable and reproducible. This tutorial will walk you through how to set up your first pipeline with DVC using this Github repository.

# Example to get started

### Installation

We recommend you to fork this repository ([DVC-shell-scripts][PlDb]) to your own Github first. 

Open your local working directory and clone the repository.

```sh
$ cd <directory>
$ git clone https://github.com/<your_Github_account>/DVC-shell-scripts.git
```

The repository you get have a layout like this, 

It helps you to build a complete pipeline using DVC. But first you need to specify your confifguration in the pipelines folder. Here we provide a example dvc config file ([pipelines/pipeline1.dvc.data][PlDb])

### Usage

##### Config the dvc pipeline

The DVC config file strictly follows the steps we build a ML/DL model. It consists of 

  - Basics
  - Remote
  - Data
  - TrainSet
  - TestSet
  - Train
  - Validate
  - ResultConvert
  - Evaluation

For detailed tutorials, please refer to [DVC tutorial - YOLO usecase][PlDb].



[PlDb]: <https://github.com/ZhengYQi6427/DVC-shell-scripts.git>
[PlDb]: <https://github.com/ZhengYQi6427/DVC-shell-scripts/blob/master/pipelines/pipeline1.dvc.data>
[PlDb]: <https://docs.google.com/document/d/1jGCSVIhT5bfg1ace74jKn1zUTi6E9tH0z47PfmZkhfk/edit?usp=sharing>
