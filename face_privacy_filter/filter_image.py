#! python
# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# ===================================================================================
# This Acumos software file is distributed by AT&T and Tech Mahindra
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
"""
Wrapper for face privacy transform task
"""

import os.path
import sys

import numpy as np
import pandas as pd


def model_create_pipeline(transformer, funcName, inputIsSet, outputIsSet):
    from acumos.session import Requirements
    from acumos.modeling import Model, List, create_namedtuple
    from face_privacy_filter._version import MODEL_NAME, __version__ as VERSION
    import sklearn
    import cv2
    from os import path

    # derive the input type from the transformer
    input_type, type_name = transformer._type_in  # it looked like this [('test', int), ('tag', str)]
    type_in = create_namedtuple(type_name, input_type)
    input_set = type_in
    name_multiple_in = type_name
    if inputIsSet:
        name_multiple_in = type_name + "s"
        input_set = create_namedtuple(type_name + "Set", [(name_multiple_in, List[type_in])])

    # derive the output type from the transformer
    output_type, type_name = transformer._type_out
    type_out = create_namedtuple(type_name, output_type)
    output_set = type_out
    if outputIsSet:
        name_multiple_out = type_name + "s"
        output_set = create_namedtuple(type_name + "Set", [(name_multiple_out, List[type_out])])

    def transform(val_wrapped: input_set) -> output_set:
        '''Transform from image or detection and return score or image'''
        # print("-===== input -===== ")
        # print(input_set)
        if inputIsSet:
            df = pd.DataFrame(getattr(val_wrapped, name_multiple_in), columns=type_in._fields)
        else:
            df = pd.DataFrame([val_wrapped], columns=type_in._fields)
        # print("-===== df -===== ")
        # print(df)
        result_df = transformer.predict(df)
        # print("-===== out df -===== ")
        # print(result_df)
        # print(result_parts)
        result_parts = result_df.to_dict('split')
        print("[{} - {}:{}]: Input {} row(s) ({}), output {} row(s) ({}))".format(
              "classify", MODEL_NAME, VERSION, len(df), type_in, len(result_df), output_set))
        output_obj = []
        if len(df):
            if outputIsSet:
                output_obj = output_set([type_out(*r) for r in result_parts['data']])
            else:
                output_obj = output_set(*result_parts['data'][0])
        # print("-===== out list -===== ")
        # print(output_obj)
        return output_obj

    # compute path of this package to add it as a dependency
    package_path = path.dirname(path.realpath(__file__))
    objModelDeclare = {}
    objModelDeclare[funcName] = transform
    # add the model dependency manually because of the way we constructed the package;
    # the opencv-python/cv2 dependency is not picked up automagically
    return Model(**objModelDeclare), Requirements(packages=[package_path], reqs=[pd, np, sklearn, 'opencv-python'],
                                                  req_map={cv2: 'opencv-python'})


def main(config={}):
    from face_privacy_filter.transform_detect import FaceDetectTransform
    from face_privacy_filter.transform_region import RegionTransform
    from face_privacy_filter._version import MODEL_NAME
    import argparse
    parser = argparse.ArgumentParser()
    submain = parser.add_argument_group('main execution and evaluation functionality')
    submain.add_argument('-p', '--predict_path', type=str, default='', help="save detections from model (model must be provided via 'dump_model')")
    submain.add_argument('-i', '--input', type=str, default='', help='absolute path to input data (image or csv, only during prediction / dump)')
    submain.add_argument('-c', '--csv_input', dest='csv_input', action='store_true', default=False, help='input as CSV format not an image')
    submain.add_argument('-f', '--function', type=str, default='detect', help='which type of model to generate', choices=['detect', 'pixelate'])
    submain.add_argument('-s', '--suppress_image', dest='suppress_image', action='store_true', default=False, help='do not create an extra row for a returned image')
    subopts = parser.add_argument_group('model creation and configuration options')
    subopts.add_argument('-a', '--push_address', help='server address to push the model (e.g. http://localhost:8887/v2/models)', default=os.getenv('ACUMOS_PUSH', ""))
    subopts.add_argument('-A', '--auth_address', help='server address for login and push of the model (e.g. http://localhost:8887/v2/auth)', default=os.getenv('ACUMOS_AUTH', ""))
    subopts.add_argument('-d', '--dump_model', help='dump model to a pickle directory for local running', default='')
    config.update(vars(parser.parse_args()))     # pargs, unparsed = parser.parse_known_args()

    if not config['predict_path']:
        print("Attempting to create new model for dump or push...")
    elif not os.path.exists(config['input']):
        print("Prediction requested but target input '{:}' was not found, please check input arguments.".format(config['input']))
        sys.exit(-1)

    # refactor the raw samples from upstream image classifier
    if config['function'] == "detect":
        transform = FaceDetectTransform(include_image=not config['suppress_image'])
        pipeline, reqs = model_create_pipeline(transform, config['function'], False, True)
    elif config['function'] == "pixelate":
        transform = RegionTransform()
        pipeline, reqs = model_create_pipeline(transform, config['function'], True, False)
    else:
        print("Error: Functional mode '{:}' unknown, aborting create".format(config['function']))
    print(pipeline)
    print(getattr(pipeline, config['function']))

    # formulate the pipeline to be used
    model_name = MODEL_NAME + "_" + config['function']
    if config['push_address'] and config['auth_address']:
        from acumos.session import AcumosSession
        print("Pushing new model to '{:}'...".format(config['push_address']))
        session = AcumosSession(push_api=config['push_address'], auth_api=config['auth_address'])
        session.push(pipeline, model_name, reqs)  # pushes model directly to servers

    if config['dump_model']:
        from acumos.session import AcumosSession
        from os import makedirs
        if not os.path.exists(config['dump_model']):
            makedirs(config['dump_model'])
        print("Dumping new model to '{:}'...".format(config['dump_model']))
        session = AcumosSession()
        session.dump(pipeline, model_name, config['dump_model'], reqs)  # creates model subdirectory

    if config['predict_path']:
        print("Using newly created model for local prediction...")
        if not config['csv_input']:
            inputDf = FaceDetectTransform.generate_in_df(config['input'])
        else:
            inputDf = pd.read_csv(config['input'], converters={FaceDetectTransform.COL_IMAGE_DATA: FaceDetectTransform.read_byte_arrays})

        func_action = getattr(pipeline, config['function'])  # simplify to just use loaded model 6/1
        pred_raw = func_action.wrapped(inputDf)
        transform_out = func_action.from_wrapped(pred_raw).as_wrapped()
        dfPred = pd.DataFrame(list(zip(*transform_out)), columns=transform_out._fields)

        if not config['csv_input']:
            dfPred = FaceDetectTransform.suppress_image(dfPred)

        if config['predict_path']:
            print("Writing prediction to file '{:}'...".format(config['predict_path']))
            if not config['csv_input']:
                dfPred.to_csv(config['predict_path'], sep=",", index=False)
            else:
                FaceDetectTransform.generate_out_image(dfPred, config['predict_path'])

        if dfPred is not None:
            print("Predictions:\n{:}".format(dfPred))


if __name__ == '__main__':
    # patch the path to include this object
    pathRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if pathRoot not in sys.path:
        sys.path.append(pathRoot)
    main()
