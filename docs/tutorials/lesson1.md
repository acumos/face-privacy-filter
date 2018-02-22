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

# Wrapping Models for Deployment
To utilize this transformer model set, it first creates a detect transformer
and then a pixelate transformer.
Continue to the [next tutorial](lesson2.md)
to see how to utilize these models with a simple demo API server.


## Model Deployment
Following similar use pattens described by the main client library, there are
two primary modes to export and deploy the generated classifier: by dumping
it to disk or by pushing it to an onboarding server.  Please consult the
[reference manual](../image-classification.md#usage) for more specific arguments
but the examples below demonstrate basic capabilities.

This single repo has a number of different models that can be
composed together for operation.

* Dump the `detect` model to disk.
```
python face_privacy_filter/filter_image.py -d model_detect -f detect
```
* Dump the `pixelate` model to disk.
```
python face_privacy_filter/filter_image.py -d model_pix -f pixelate
```


## In-place Evaluation
In-place evaluation **will utilize** a serialized version of the model and load
it into memory for use in-place.  This mode is handy for quick
evaluation of images or image sets for use in other classifiers.

* Evaluate the `detect` model from disk and a previously produced detect object
```
python face_privacy_filter/filter_image.py -d model_detect -p output.csv -i web_demo/images/face_DiCaprio.jpg
```
* Example for evaluating the `pixelate` model from disk and a previously produced detect object
```
python face_privacy_filter/filter_image.py -d model_pix -i detect.csv -p output.jpg --csv_input
```


# Installation Troubleshoting
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

