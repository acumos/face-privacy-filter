# web_test
This directory provides a simple web server for demonstrating a face-privacy filter example.
This web demo will launch an application with a swagger page.

## Example usage
This repo provides multiple models that can be created.  Thanks to the
generic transform i/o specifications, you can run either one or two
models in composition together.

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

## Face Privacy Filtering

* For a graphical experience, view the swagger-generated UI at [http://localhost:8884/ui].
* Additionally, a simple command-line utility could be used to post an image
and mime type to the main interface.  Additional examples for posting base64 encoded
images from javascript can be [found on StackOverflow](https://stackoverflow.com/a/20285053).
```
curl -F base64_data=@../web_demo/images/face_renion.jpg -F mime_type="image/jpeg" "http://localhost:8884/transform"
```
