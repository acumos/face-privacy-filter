<!---
.. ===============LICENSE_START=======================================================
.. Acumos CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
.. ===================================================================================
.. This Acumos documentation file is distributed by AT&T and Tech Mahindra
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..      http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================
-->

# Face Privacy Filter Guide
This model contains the capability to generate two submodels:
one for face detection and oen for face suppression through pixelation.

# Face Detection Model Guide
A model example for face detection from images within Acumos.

## Background
This model analyzes static images to detect frontal faces.  It utilizes a
frontal face cascade from the
[OpenCV](https://opencv.org/) image processing library.
Model load time is optimized by creating and maintaining the fixed cascade
in memory while operating.  Demonstrating the capability of custom classes
and requisite member variables, the cascade is serialized with the model as
a string asset which is deserialized and loaded from disk upon startup.

## Usage
Input to the model is an array of one or more tuples of image binary data
and a binary mime type.  The position of the image within the array is utilized
in the output signature as a zero-based index.  For example if three images
were sent, the output probabilities would have 0, 1, and 2 as index values.
The output from this model is a repeated array of detected regions for each
face in each input image.  So that image data can be cascaded to other models,
the original image and mime type are also embedded with the special
region code `-1` within the output.

A web demo is included with the source code, available via the
[Acumos Gerrit repository](https://gerrit.acumos.org/r/gitweb?p=face-privacy-filter.git;a=summary)
or the mirrored [Acumos Github repository](https://github.com/acumos/face-privacy-filter).
It utilizes a protobuf javascript library and processes
input images to detect all faces within an image.

## Performance
As this model wraps a preexisting cascade, no formal testing evaluation
was performed.  However, experimental usage indicates the following highlights.

* Faces that are too small can easily be missed.
* Frontal faces perform best, with some tolerance of about 5-10 degrees off-plane rotation.
* Detection is fairly sensitive to rotation in plane, so try not to let subject faces rotate more than 15 degrees.
* Dark or low contrast images generally do not perform well for detection.

## More Information
As this model uses a generic cascade from OpenCV, readers can easily
substituted or update those models with no change in API endpoint required.
Additionally, secondary verification methods using pixel validation (e.g.
sub-part verification, symmetry tests, or more advanced parts-based
verifications) may dramatically improve the false alarm rate, although
the current model was tuned for precision (instead of recall) already.



# Face Pixelation Model Guide
A model example to anonymize faces from images via pixelation within Acumos.

## Background
This model accepts detected faces and their source image and produces
pixelated image results.  It utilizes simple image manipulation methods
from the [OpenCV](https://opencv.org/) image processing library.
This model is a demonstration of a
transform operation: there is neither state nor static model data
utilized and all data comes from the upstream input.


## Usage
Input to the model is an array of one or more tuples of detected face regions
as well as the original image binary data and a binary mime type.  The row or
sample containing the original image is specially marked by a region code
of ‘-1’.  The output from this model is an array of images (one for each
unique image input) with the detected face regions blurred via pixelation.

A web demo is included with the source code, available via the
[Acumos Gerrit repository](https://gerrit.acumos.org/r/gitweb?p=face-privacy-filter.git;a=summary).
It utilizes a protobuf javascript library and processes
input images to detect all faces within an image.

## Performance
As this model is a data transform example that flattens detected image regions into images.

* Faces not included in the detected regions are ignored.
* Faces whose images do not exist in the input (e.g. region and image indices
  are provided, but no original image) are ignored.
* The mime type for the output image is constructed to mimic the input image and mime type.

## More Information
This model uses processing methods from OpenCV, so any number of additional
privacy methods could be employed, like blurring, substitution, etc. More
advanced techniques that still allow some information processing (e.g.
demographics but not recognition) may also be easily employed with this
system, should the right method arise.



# Source Installation
This section is useful for source-based installations and is not generally intended
for catalog documentation.

## Image Analysis for Face-based Privacy Filtering
This source code creates and pushes a model into Acumos that processes
incoming images and outputs a detected faces as well as the original image
input (if configured that way).  The model uses a [python interface](https://pypi.python.org/pypi/opencv-python)
to the [OpenCV library](https://opencv.org/) to detect faces and perform
subsequent image processing.  This module does not support training
at this time and instead uses a pre-trained face cascade, which is
included (from OpenCV) in this module.

### Package dependencies
Package dependencies for the core code and testing have been flattened into a
single file for convenience. Instead of installing this package into your
your local environment, execute the command below.

```
pip install -r requirments.txt
```

**Note:** If you are using an [anaconda-based environment](https://anaconda.org),
you may want to try
installing these packages [directly](https://docs.anaconda.com/anaconda-repository/user-guide/tasks/pkgs/download-install-pkg).
to avoid mixing of `pip` and `conda` package stores.

### Usage
This package contains runable scripts for command-line evaluation,
packaging of a model (both dump and posting), and simple web-test
uses.   All functionality is encapsulsted in the `filter_image.py`
script and has the following arguments.

```
usage: filter_image.py [-h] [-p PREDICT_PATH] [-i INPUT]
                       [-c] [-s] [-f {detect,pixelate}]
                       [-a PUSH_ADDRESS] [-d DUMP_MODEL]

optional arguments:
  -h, --help            show this help message and exit
  -p PREDICT_PATH, --predict_path PREDICT_PATH
                        save detections from model (model must be provided via
                        'dump_model')
  -i INPUT, --input INPUT
                        absolute path to input data (image or csv, only during
                        prediction / dump)
  -c, --csv_input       input as CSV format not an image
  -s, --suppress_image  do not create an extra row for a returned image
  -f {detect,pixelate}, --function {detect,pixelate}
                        which type of model to generate
  -a PUSH_ADDRESS, --push_address PUSH_ADDRESS
                        server address to push the model (e.g.
                        http://localhost:8887/v2/models)
  -d DUMP_MODEL, --dump_model DUMP_MODEL
                        dump model to a pickle directory for local running
```



# Example Usages
Please consult the [tutorials](tutorials) dirctory for usage examples
including an in-place [web page demonstration](tutorials/lesson3.md).

## Face-based Use Cases
This project includes a number of face-based use cases including raw
detection, blurring, and other image-based modifications based on
detected image regions.

* **Face Detection Use-case** - This source code creates and pushes a model that processes
incoming images and outputs detected faces.

# Release Notes
The [release notes](release-notes.md) catalog additions and modifications
over various version changes.

# Metadata Examples
* [example detect catalog image](catalog_image_detect.png) - [url source](https://flic.kr/p/xqw25C)
* [example blur catalog image](catalog_image_blur.png)  - [url source](https://flic.kr/p/bEgYbs)
