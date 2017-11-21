# -*- coding: utf-8 -*-
# ================================================================================
# ACUMOS
# ================================================================================
# Copyright © 2017 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# ================================================================================
# This Acumos software file is distributed by AT&T and Tech Mahindra
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ================================================================================
import connexion
import logging

import argparse
import json
import time
import os

from flask import current_app, make_response

import pandas as pd
import numpy as np

from acumos.wrapped import load_model
import base64


def generate_image_df(path_image="", bin_stream=b""):
    # munge stream and mimetype into input sample
    if path_image and os.path.exists(path_image):
        bin_stream = open(path_image, 'rb').read()
    # bin_stream = base64.b64encode(bin_stream)
    # if type(bin_stream) == bytes:
    #     bin_stream = bin_stream.decode()
    return pd.DataFrame([['image/jpeg', bin_stream]], columns=["mime_type", "image_binary"])


def transform(mime_type, image_binary):
    app = current_app
    time_start = time.clock()
    image_read = image_binary.stream.read()
    X = generate_image_df(bin_stream=image_read)

    pred_out = None
    if app.model_detect is not None:    # first translate to input type
        type_in = app.model_detect.transform._input_type
        detect_in = type_in(*tuple(col for col in X.values.T))
        pred_out = app.model_detect.transform.from_wrapped(detect_in)
    if app.model_proc is not None and pred_out is not None:  # then transform to output type
        pred_out = app.model_proc.transform.from_pb_msg(pred_out.as_pb_msg()).as_wrapped()
    time_stop = time.clock()-time_start

    pred = None
    if pred_out is not None:
        pred = pd.DataFrame(list(zip(*pred_out)), columns=pred_out._fields)
        pred['image_binary'] = pred['image_binary'].apply(lambda x: base64.b64encode(x).decode())
    retStr = json.dumps(pred.to_dict(orient='records'), indent=4)

    # formulate response
    resp = make_response((retStr, 200, {}))
    # allow 'localhost' from 'file' or other;
    # NOTE: DO NOT USE IN PRODUCTION!!!
    resp.headers['Access-Control-Allow-Origin'] = '*'
    print(retStr[:min(200, len(retStr))])
    # print(pred)
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
