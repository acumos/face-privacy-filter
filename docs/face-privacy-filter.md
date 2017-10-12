# face-privacy-filter
A model for face detection and suppression.

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

