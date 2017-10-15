# web_test
This directory provides a simple web server for demonstrating a face-privacy filter example.
This web demo will launch an application with a swagger page.

## Example usage

```
$ python app.py
usage: app.py [-h] [--port PORT] [--modeldir MODELDIR] [--rich_return]

optional arguments:
  -h, --help           show this help message and exit
  --port PORT          port to launch the simple web server
  --modeldir MODELDIR  model directory to load dumped artifact
```

### Output formats
The optional HTTP parameter `rich_output` will generate a more decorated JSON output
 that is also understood by the included web application.

* standard output - from `DataFrame` version of the transform
```


```


* rich output - formatted form of the transform
```
```

## Face Privacy Filtering

* For a graphical experience, view the swagger-generated UI at [http://localhost:8884/ui].
* Additionally, a simple command-line utility could be used to post an image
and mime type to the main interface.
```
curl -F image_binary=@test.jpg -F rich_output="true" -F mime_type="image/jpeg" "http://localhost:8884/transform"
```