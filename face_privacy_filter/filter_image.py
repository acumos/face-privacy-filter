#! python
# -*- coding: utf-8 -*-
"""
Wrapper for image emotion classification task 
"""

import os.path
import sys

import numpy as np
import pandas as pd

from face_privacy_filter.transform_detect import FaceDetectTransform
from face_privacy_filter._version import MODEL_NAME


def model_create_pipeline(transformer, pipeline_type="detect"):
    #from sklearn.pipeline import Pipeline
    dependent_modules = [pd, np, 'opencv-python']  # define as dependent libraries

    # for now, do nothing specific to transformer...

    return transformer, dependent_modules


def main(config={}):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--predict_path', type=str, default='', help="save detections from model (model must be provided via 'dump_model')")
    parser.add_argument('-i', '--input', type=str, default='',help='absolute path to input image (only during prediction / dump)')
    parser.add_argument('-s', '--suppress_image', dest='suppress_image', action='store_true', default=False, help='do not create an extra row for a returned image')
    parser.add_argument('-a', '--push_address', help='server address to push the model (e.g. http://localhost:8887/v2/models)', default='')
    parser.add_argument('-d', '--dump_model', help='dump model to a pickle directory for local running', default='')
    config.update(vars(parser.parse_args()))     #pargs, unparsed = parser.parse_known_args()

    if not config['predict_path']:
        print("Attempting to create new model for dump or push...")

        # refactor the raw samples from upstream image classifier
        transform = FaceDetectTransform(include_image=not config['suppress_image'])
        inputDf = transform.generate_in_df()
        pipeline, EXTRA_DEPS = model_create_pipeline(transform, "detect")

        # formulate the pipeline to be used
        if 'push_address' in config and config['push_address']:
            from cognita_client.push import push_sklearn_model # push_skkeras_hybrid_model (keras?)
            print("Pushing new model to '{:}'...".format(config['push_address']))
            push_sklearn_model(pipeline, inputDf, api=config['push_address'], name=MODEL_NAME, extra_deps=EXTRA_DEPS)

        if 'dump_model' in config and config['dump_model']:
            from cognita_client.wrap.dump import dump_sklearn_model # dump_skkeras_hybrid_model (keras?)
            print("Dumping new model to '{:}'...".format(config['dump_model']))
            dump_sklearn_model(pipeline, inputDf, config['dump_model'], name=MODEL_NAME, extra_deps=EXTRA_DEPS)

    else:
        if not config['dump_model'] or not os.path.exists(config['dump_model']):
            print("Attempting to predict from a dumped model, but model not found.".format(config['dump_model']))
            sys.exit(-1)
        if not os.path.exists(config['input']):
            print("Predictino requested but target input '{:}' was not found, please check input arguments.".format(config['input']))
            sys.exit(-1)

        print("Attempting predict/transform on input sample...")
        from cognita_client.wrap.load import load_model
        model = load_model(config['dump_model'])
        inputDf = FaceDetectTransform.generate_in_df(config['input'])
        dfPred = model.transform.from_native(inputDf).as_native()
        dfPred = FaceDetectTransform.suppress_image(dfPred)

        if config['predict_path']:
            print("Writing prediction to file '{:}'...".format(config['predict_path']))
            dfPred.to_csv(config['predict_path'], sep=",", index=False)

        if dfPred is not None:
            print("Predictions:\n{:}".format(dfPred))

if __name__ == '__main__':
    main()
