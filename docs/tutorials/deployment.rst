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

.. _deployment:

=========================================
Deployment: Wrapping and Executing Models
=========================================

To utilize this transformer model set, it first creates a detect
transformer and then a pixelate transformer. Continue to the
`demo tutorial <demonstration.rst>`__  to see how to utilize these models with a
simple demo API server.


Model Deployment
----------------

Following similar use pattens described by the main client library,
there are two primary modes to export and deploy the generated
classifier: by dumping it to disk or by pushing it to an onboarding
server. Please consult the
`reference manual <../face-privacy-filter.rst#usage>`__ for more specific arguments
but the examples below demonstrate basic capabilities.

This single repo has a number of different models that can be composed
together for operation.

-  Dump the ``detect`` model to disk.

   ::

       python face_privacy_filter/filter_image.py -f detect  -d model_detect

-  Dump the ``pixelate`` model to disk.

   ::

       python face_privacy_filter/filter_image.py -f pixelate -d model_pix

Below is an extended for training a model, dumping it to disk, and
pushing that model. **(recommended)**

::

    export ACUMOS_USERNAME="user"; \
    export ACUMOS_PASSWORD="password";
    or
    export ACUMOS_TOKEN="a_very_long_token";

    export ACUMOS_PUSH="https://acumos-challenge.org/onboarding-app/v2/models"; \
    export ACUMOS_AUTH="https://acumos-challenge.org/onboarding-app/v2/auth"; \
    python face_privacy_filter/filter_image.py -f detect


In-place Evaluation
-------------------

In-place evaluation **will utilize** a serialized version of the model
and load it into memory for use in-place. This mode is handy for quick
evaluation of images or image sets for use in other classifiers.

-  Evaluate the ``detect`` model from disk and a previously produced
   detect object

   ::

       python face_privacy_filter/filter_image.py -d model_detect -p output.csv -i web_demo/images/face_DiCaprio.jpg

-  Example for evaluating the ``pixelate`` model from disk and a
   previously produced detect object

   ::

       python face_privacy_filter/filter_image.py -d model_pix -i detect.csv -p output.jpg --csv_input


Using the client model runner
-----------------------------

Getting even closer to what it looks like in a deployed model, you can
also use the model runner code to run your full cascade (detection +
pixelate) transform locally. *(added v0.3.0)*

1. First, decide the ports to run your detection and pixelate models. In
   the example below, detection runs on port ``8884`` and pixelation
   runs on port ``8885``. For the runner to properly forward requests
   for you, provide a simple JSON file example called ``runtime.json``
   in the working directory that you run the model runner.

::

    # cat runtime.json
    {downstream": ["http://127.0.0.1:8885/pixelate"]}

2. Second, dump and launch the face detection model. If you modify the
   ports to run the models, please change them accordingly. This command
   example assumes that you have cloned the client library in a relative
   path of ``../acumos-python-client``. The first line removes any prior
   model directory, the second dumps the detect model to disk, and the
   third runs the model.

::

    rm -rf model_detect/;  \
        python face_privacy_filter/filter_image.py -d model_detect -f detect; \
        python ../acumos-python-client/testing/wrap/runner.py --port 8884 --modeldir model_detect/face_privacy_filter_detect

3. Finally, dump and launch the face pixelation model. Again, if you
   modify the ports to run the models, please change them accordingly.
   Aside from the model and port, the main difference between the above
   line is that the model runner is instructed to *ignore* the
   downstream forward (``runtime.json``) file so that it doesn't attempt
   to forward the request to itself.

::

    rm -rf model_pix;  \
        python face_privacy_filter/filter_image.py -d model_pix -f pixelate; \
        python ../acumos-python-client/testing/wrap/runner.py --port 8885 --modeldir model_pix/face_privacy_filter_pixelate  --no_downstream

Installation Troubleshoting
===========================

Using some environment-based versions of python (e.g. conda), one
problem seemed to come up with the installation of the dependent package
``opencv-python``. If you launch your python instance and see an error
like the one below, keep reading.

::

    >>> import cv2
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: dynamic module does not define module export function (PyInit_cv2)
    >>>

This is likely because your ``PYTHONPATH`` is not correctly configured
to point to the additional installed libraries.

-  From the `simple example
   here <https://stackoverflow.com/a/42160595>`__ you can check your
   environment with ``echo $PYTHONPATH``. If it does not contain the
   directory that you installed to, then you have a problem.
-  Please check your installation by running
   ``python -v -v; import cv2`` and checking that the last loaded
   library is in the right location.
-  In some instances, this variable needed to be blank to work properly
   (i.e. ``export PYTHONPATH=``) run at some time during start up.
