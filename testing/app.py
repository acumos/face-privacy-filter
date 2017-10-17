#!/usr/bin/env python3
import connexion
import logging

import argparse
import json
import time
import os

from flask import Flask, request, current_app, make_response

import pandas as pd
import requests

from cognita_client.wrap.load import load_model
from face_privacy_filter.transform_detect import FaceDetectTransform
import base64

def generate_image_df(path_image="", bin_stream=b""):
    # munge stream and mimetype into input sample
    if path_image and os.path.exists(path_image):
        bin_stream = open(path_image, 'rb').read()
    bin_stream = base64.b64encode(bin_stream)
    if type(bin_stream)==bytes:
        bin_stream = bin_stream.decode()
    return pd.DataFrame([['image/jpeg', bin_stream]], columns=[FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA])

def transform(mime_type, image_binary):
    app = current_app
    time_start = time.clock()
    image_read = image_binary.stream.read()
    X = generate_image_df(bin_stream=image_read)
    print(X)

    if app.model_detect is not None:
        pred_out = app.model_detect.transform.from_native(X)
    if app.model_proc is not None:
        pred_prior = pred_out
        #pred_out = app.model_proc.transform.from_msg(pred_prior.as_msg())
        pred_out = app.model_proc.transform.from_native(pred_prior.as_native())
    time_stop = time.clock()

    retStr = json.dumps(pred_out.as_native().to_dict(orient='records'), indent=4)

    # formulate response
    resp = make_response((retStr, 200, { } ))
    # allow 'localhost' from 'file' or other;
    # NOTE: DO NOT USE IN PRODUCTION!!!
    resp.headers['Access-Control-Allow-Origin'] = '*'
    print(retStr[:min(200, len(retStr))])
    #print(pred)
    return resp


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', "--port", type=int, default=8884, help='port to launch the simple web server')
    parser.add_argument('-d', "--modeldir_detect", type=str, default='../model_detect', help='model directory for detection')
    parser.add_argument('-a', "--modeldir_analyze", type=str, default='../model_pix', help='model directory for detection')
    pargs = parser.parse_args()

    print("Configuring local application... {:}".format(__name__))
    logging.basicConfig(level=logging.INFO)
    app = connexion.App(__name__)
    app.add_api('swagger.yaml')
    # example usage:
    #     curl -F image_binary=@test.jpg -F mime_type="image/jpeg" "http://localhost:8885/transform"

    app.app.model_detect = None
    if pargs.modeldir_detect:
        if not os.path.exists(pargs.modeldir_detect):
            print("Failed loading of detect model '{:}' even though it was specified...".format(pargs.modeldir_detect))
        else:
            print("Loading detect model... {:}".format(pargs.modeldir_detect))
            app.app.model_detect = load_model(pargs.modeldir_detect)

    app.app.model_proc = None
    if pargs.modeldir_analyze:
        if not os.path.exists(pargs.modeldir_analyze):
            print("Failed loading of processing model '{:}' even though it was specified...".format(
                pargs.modeldir_analyze))
        else:
            print("Loading processing model... {:}".format(pargs.modeldir_analyze))
            app.app.model_proc = load_model(pargs.modeldir_analyze)

    # run our standalone gevent server
    app.run(port=pargs.port) #, server='gevent')
