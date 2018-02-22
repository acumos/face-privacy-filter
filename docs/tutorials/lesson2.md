<!---
.. ===============LICENSE_START=======================================================
.. Acumos
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
# Application server
As a means of testing the API and demonstrating functionality, two
additional components are included in this repository:
a simple [swagger-based webserver](../../testing) (documented here) and
a [demo web page](../../web_demo) (documented in the [next tutorial](lesson3.md).

## Swagger API
Using a simple [flask-based connexion server](https://github.com/zalando/connexion),
an API scaffold has been built to host a serialized/dumped model.

To utilized [this example app](../../testing), an instance should first be built and downloaded
from Acumos (or dumped to disk) and then
launched locally.  Afterwards, the sample application found in
[web_demo](web_demo) (see [the next tutorial](lesson3.md))
uses a `localhost` service to transform
and visualize the results of model operation.


```
usage: app.py [-h] [-p PORT] [-d MODELDIR_DETECT] [-a MODELDIR_ANALYZE]

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  port to launch the simple web server
  -d MODELDIR_DETECT, --modeldir_detect MODELDIR_DETECT
                        model directory for detection
  -a MODELDIR_ANALYZE, --modeldir_analyze MODELDIR_ANALYZE
                        model directory for detection
```


Example usage may be running with a detect model that was dumped to the directory `model_detect`
in the main repo source directory and a pixelate model in the
directory `model_pix` (under the same repo source directory).

```
python app.py --modeldir_detect ../model_detect --modeldir_analyze ../model_pix/
```


### Output formats
This repo provides multiple models that can be created.

* detect output - The first set, called
`detect` will analyze an image, detect face regions, and echo both the
regions and the face back to the user.  The region marked with `-1`
and a valid `mime_type` parameter will
always be the region with the original image.

```
[
    {
        "h": 143,
        "x": 0,
        "y": 0,
        "base64_data": "/9j/4AAQSkZJRgABA....",
        "w": 2048,
        "region": -1,
        "image": 0,
        "mime_type": "image/jpeg"
    },
    {
        "h": 143,
        "x": 203,
        "y": 189,
        "base64_data": "",
        "w": 143,
        "region": 0,
        "image": 0,
        "mime_type": ""
    },
    ...
    {
        "h": 212,
        "x": 886,
        "y": 409,
        "base64_data": "",
        "w": 212,
        "region": 3,
        "image": 0,
        "mime_type": ""
    }
]

```

* analyzed output - The second type of output produces processed
images as an output.  These images are base64 encoded with a decoding
mime type.
```
[
    {
        "base64_data": "/9j/4AAQSkZJRgABAQAAAQABAAD....",
        "mime_type": "image/jpeg"
    }
]

```

## Direct Evaluation

* For a graphical experience, view the swagger-generated UI at [http://localhost:8884/ui].
* Additionally, a simple command-line utility could be used to post an image
and mime type to the main interface.  Additional examples for posting base64 encoded
images from javascript can be [found on StackOverflow](https://stackoverflow.com/a/20285053).
```
curl -F base64_data=@../web_demo/images/face_renion.jpg -F mime_type="image/jpeg" "http://localhost:8884/transform"
```
