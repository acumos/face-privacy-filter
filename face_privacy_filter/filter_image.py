#! python
# -*- coding: utf-8 -*-
"""
Wrapper for face privacy transform task
"""

import os.path
import sys

import numpy as np
import pandas as pd


def model_create_pipeline(transformer):
    from acumos.session import Requirements
    from acumos.modeling import Model, List, create_namedtuple
    import sklearn
    import cv2
    from os import path

    # derive the input type from the transformer
    type_list, type_name = transformer._type_in  # it looked like this {'test': int, 'tag': str}
    input_type = [(k, List[type_list[k]]) for k in type_list]
    type_in = create_namedtuple(type_name, input_type)

    # derive the output type from the transformer
    type_list, type_name = transformer._type_out
    output_type = [(k, List[type_list[k]]) for k in type_list]
    type_out = create_namedtuple(type_name, output_type)

    def predict_class(val_wrapped: type_in) -> type_out:
        '''Returns an array of float predictions'''
        df = pd.DataFrame(list(zip(*val_wrapped)), columns=val_wrapped._fields)
        # df = pd.DataFrame(np.column_stack(val_wrapped), columns=val_wrapped._fields)  # numpy doesn't like binary
        tags_df = transformer.predict(df)
        tags_list = type_out(*(col for col in tags_df.values.T))  # flatten to tag set
        return tags_list

    # compute path of this package to add it as a dependency
    package_path = path.dirname(path.realpath(__file__))
    return Model(transform=predict_class), Requirements(packages=[package_path], reqs=[pd, np, sklearn],
                                                        req_map={cv2: 'opencv-python'})


def main(config={}):
    from face_privacy_filter.transform_detect import FaceDetectTransform
    from face_privacy_filter.transform_region import RegionTransform
    from face_privacy_filter._version import MODEL_NAME
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--predict_path', type=str, default='', help="save detections from model (model must be provided via 'dump_model')")
    parser.add_argument('-i', '--input', type=str, default='', help='absolute path to input data (image or csv, only during prediction / dump)')
    parser.add_argument('-c', '--csv_input', dest='csv_input', action='store_true', default=False, help='input as CSV format not an image')
    parser.add_argument('-s', '--suppress_image', dest='suppress_image', action='store_true', default=False, help='do not create an extra row for a returned image')
    parser.add_argument('-f', '--function', type=str, default='detect', help='which type of model to generate', choices=['detect', 'pixelate'])
    parser.add_argument('-a', '--push_address', help='server address to push the model (e.g. http://localhost:8887/v2/models)', default='')
    parser.add_argument('-d', '--dump_model', help='dump model to a pickle directory for local running', default='')
    config.update(vars(parser.parse_args()))     # pargs, unparsed = parser.parse_known_args()

    if not config['predict_path']:
        print("Attempting to create new model for dump or push...")

        # refactor the raw samples from upstream image classifier
        if config['function'] == "detect":
            transform = FaceDetectTransform(include_image=not config['suppress_image'])
        elif config['function'] == "pixelate":
            transform = RegionTransform()
        else:
            print("Error: Functional mode '{:}' unknown, aborting create".format(config['function']))
        inputDf = transform.generate_in_df()
        pipeline, reqs = model_create_pipeline(transform)

        # formulate the pipeline to be used
        model_name = MODEL_NAME + "_" + config['function']
        if config['push_address']:
            from acumos.session import AcumosSession
            print("Pushing new model to '{:}'...".format(config['push_address']))
            session = AcumosSession(push_api=config['push_address'], auth_api=config['auth_address'])
            session.push(pipeline, model_name, reqs)  # creates ./my-iris.zip

        if config['dump_model']:
            from acumos.session import AcumosSession
            from os import makedirs
            if not os.path.exists(config['dump_model']):
                makedirs(config['dump_model'])
            print("Dumping new model to '{:}'...".format(config['dump_model']))
            session = AcumosSession()
            session.dump(pipeline, model_name, config['dump_model'], reqs)  # creates ./my-iris.zip

    else:
        if not config['dump_model'] or not os.path.exists(config['dump_model']):
            print("Attempting to predict from a dumped model, but model not found.".format(config['dump_model']))
            sys.exit(-1)
        if not os.path.exists(config['input']):
            print("Predictino requested but target input '{:}' was not found, please check input arguments.".format(config['input']))
            sys.exit(-1)

        print("Attempting predict/transform on input sample...")
        from acumos.wrapped import load_model
        model = load_model(config['dump_model'])
        if not config['csv_input']:
            inputDf = FaceDetectTransform.generate_in_df(config['input'])
        else:
            inputDf = pd.read_csv(config['input'], converters={FaceDetectTransform.COL_IMAGE_DATA: FaceDetectTransform.read_byte_arrays})

        type_in = model.transform._input_type
        transform_in = type_in(*tuple(col for col in inputDf.values.T))
        transform_out = model.transform.from_wrapped(transform_in).as_wrapped()
        dfPred = pd.DataFrame(list(zip(*transform_out)), columns=transform_out._fields)

        if not config['csv_input']:
            dfPred = FaceDetectTransform.suppress_image(dfPred)
        print("ALMOST DONE")
        print(dfPred)

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
