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

# Web Demo
This web page sample allows the user to submit an image to
an image classification and image mood classification service
in serial progression.

** Image Copyrights May Apply ** - the included sample videos may carry
additional copyrights and are not meant for public resale or consumption.

## Browser Interaction
Most browsers should have no
CORS or other cross-domain objections to dropping the file `face-privacy.html`
into the browser and accesing a locally hosted server API, as configured
in [the previous tutorial](lesson2.md).

## Example mood classification demo
To customize this demo, one should change either the included javascript
or simply update the primary classification URL on the page itself during runtime.

* confirm that your local instance is configured and running
* download this directory to your local machine
    * confirm the host port and classification service URL in the file `face-privacy.js`
```
classificationServer: "http://localhost:8884/transform",
```
* view the page `face-privacy.html` in a Crome or Firefox browser
* probabilities will be updated on the right side fo the screen
* you can switch between a few sample images or upload your own by clicking on the buttons below the main image window

Example web application with *awe* mood classification

* ![example web application blurring multiple facs](example_running.jpg "Example multi-face blur")


# Example Interface
An instance should first be built and downloaded and then
launched locally.  Afterwards, the sample application found in
[web_demo](web_demo) uses a `localhost` service to classify
and visualize the results of image classification.

* [Commercial example](../../web_demo/images/commercial.jpg) ([youtube source](https://www.youtube.com/watch?v=34KfCNapnUg))
* [Reunion face sample](../../web_demo/images/face_reunion.jpg) ([flickr source](https://flic.kr/p/bEgYbs))
* [family face example](../../web_demo/images/face_family.jpg) ([pexel source](https://www.pexels.com/photo/adult-affection-beautiful-beauty-265764/))
* [DiCaprio celebrity face sample](../../web_demo/images/face_DiCaprio.jpg) ([wikimedia source](https://en.wikipedia.org/wiki/Celebrity#/media/File:Leonardo_DiCaprio_visited_Goddard_Saturday_to_discuss_Earth_science_with_Piers_Sellers_(26105091624)_cropped.jpg))
* [Schwarzenegger celebrity face sample](../../web_demo/images/face_Schwarzenegger.jpg) ([wikimedia source](https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/A._Schwarzenegger.jpg/220px-A._Schwarzenegger.jpg))


before  | after
------- | -------
![raw commercial](../../web_demo/images/commercial.jpg)  | ![pixelated commercial](../../web_demo/images/commercial_pixelate.jpg)
![raw face](../../web_demo/images/face_family.jpg)  | ![pixelated commercial](../../web_demo/images/face_family_pixelate.jpg)
