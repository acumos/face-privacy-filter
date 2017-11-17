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

### Usage
This package contains runable scripts for command-line evaluation,
packaging of a model (both dump and posting), and simple web-test
uses.   All functionality is encapsulsted in the `filter_image.py`
script and has the following arguments.

```
usage: run_face-privacy-filter_reference.py [-h] [-p PREDICT_PATH] [-i INPUT]
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


### Examples
This single repo has a number of different models that can be
composed together for operation.

* Dump the `detect` model to disk.
```
./bin/run_local.sh -d model_detect -f detect
```
* Dump the `pixelate` model to disk.
```
./bin/run_local.sh -d model_pix -f pixelate
```
* Evaluate the `detect` model from disk and a previously produced detect object
```
./bin/run_local.sh -d model_detect -p output.csv -i web_demo/images/face_DiCaprio.jpg
```
* Example for evaluating the `pixelate` model from disk and a previously produced detect object
```
./bin/run_local.sh -d model_pix -i detect.csv -p output.jpg --csv_input
```



### Installation Troubleshoting
Using some environment-based versions of python (e.g. conda),
one problem seemed to come up with the installation of the dependent
package `opencv-python`.  If you launch your python instance and see
an error like the one below, keep reading.

```
>>> import cv2
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: dynamic module does not define module export function (PyInit_cv2)
>>>
```

This is likely because your `PYTHONPATH` is not correctly configured to
point to the additional installed libraries.

* From the [simple example here](https://stackoverflow.com/a/42160595)
you can check your environment with `echo $PYTHONPATH`.  If it does not
contain the directory that you installed to, then you have a problem.
* Please check your installation by running `python -v -v; import cv2` and checking
that the last loaded library is in the right location.
* In some instances, this variable needed to be blank to work properly (i.e.
`export PYTHONPATH=`) run at some time during start up.


## Face-based Use Cases
This project includes a number of face-based use cases including raw
detection, blurring, and other image-based modifications based on
detected image regions.

* **Face Detection Use-case** - This source code creates and pushes a model that processes
incoming images and outputs detected faces.

## Example Interface
An instance should first be built and downloaded and then
launched locally.  Afterwards, the sample application found in
[web_demo](web_demo) uses a `localhost` service to classify
and visualize the results of image classification.

* [Commercial example](web_demo/images/commercial.jpg) ([youtube source](https://www.youtube.com/watch?v=34KfCNapnUg))
* [Reunion face sample](web_demo/images/face_reunion.jpg) ([flickr source](https://flic.kr/p/bEgYbs))
* [family face example](web_demo/images/face_family.jpg) ([pexel source](https://www.pexels.com/photo/adult-affection-beautiful-beauty-265764/))
* [DiCaprio celebrity face sample](web_demo/images/face_DiCaprio.jpg) ([wikimedia source](https://en.wikipedia.org/wiki/Celebrity#/media/File:Leonardo_DiCaprio_visited_Goddard_Saturday_to_discuss_Earth_science_with_Piers_Sellers_(26105091624)_cropped.jpg))
* [Schwarzenegger celebrity face sample](web_demo/images/face_Schwarzenegger.jpg) ([wikimedia source](https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/A._Schwarzenegger.jpg/220px-A._Schwarzenegger.jpg))


before  | after
------- | -------
![raw commercial](web_demo/images/commercial.jpg)  | ![pixelated commercial](web_demo/images/commercial_pixelate.jpg)
![raw face](web_demo/images/face_family.jpg)  | ![pixelated commercial](web_demo/images/face_family_pixelate.jpg)
