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
Wrapper for face detection task; wrapped in classifier for pipieline terminus
"""
import cv2
import os
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
import base64

import gzip
import sys
if sys.version_info[0] < 3:
    from cStringIO import StringIO as BytesIO
else:
    from io import BytesIO as BytesIO


class FaceDetectTransform(BaseEstimator, ClassifierMixin):
    '''
    A sklearn transformer mixin that detects faces and optionally outputa the original detected image
    '''
    CASCADE_DEFAULT_FILE = "data/haarcascade_frontalface_alt.xml.gz"
    COL_FACE_X = 'x'
    COL_FACE_Y = 'y'
    COL_FACE_W = 'w'
    COL_FACE_H = 'h'
    COL_REGION_IDX = 'region'
    COL_IMAGE_IDX = 'image'
    COL_IMAGE_MIME = 'mime_type'
    COL_IMAGE_DATA = 'image_binary'
    VAL_REGION_IMAGE_ID = -1

    def __init__(self, cascade_path=None, cascade_stream=None, include_image=True):
        self.include_image = include_image    # should output transform include image?
        self.cascade_obj = None  # late-load this component
        self.cascade_stream = cascade_stream    # compressed binary final for cascade data
        if self.cascade_stream is None:
            if cascade_path is None:   # default/included data?
                pathRoot = os.path.dirname(os.path.abspath(__file__))
                cascade_path = os.path.join(pathRoot, FaceDetectTransform.CASCADE_DEFAULT_FILE)
            raw_stream = b""
            with open(cascade_path, 'rb') as f:
                raw_stream = f.read()
                self.cascade_stream = {'name': os.path.basename(cascade_path),
                                       'data': FaceDetectTransform.string_compress(raw_stream)}

    @staticmethod
    def string_compress(string_data):
        out_data = BytesIO()
        with gzip.GzipFile(fileobj=out_data, mode="wb") as f:
            f.write(string_data)
        return out_data.getvalue()

    @staticmethod
    def string_decompress(compressed_data):
        in_data = BytesIO(compressed_data)
        ret_str = None
        with gzip.GzipFile(fileobj=in_data, mode="rb") as f:
            ret_str = f.read()
        return ret_str

    def get_params(self, deep=False):
        return {'include_image': self.include_image, 'cascade_stream': self.cascade_stream}

    @staticmethod
    def generate_in_df(path_image="", bin_stream=b""):
        # munge stream and mimetype into input sample
        if path_image and os.path.exists(path_image):
            bin_stream = open(path_image, 'rb').read()
        return pd.DataFrame([['image/jpeg', bin_stream]], columns=[FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA])

    @staticmethod
    def generate_out_image(row, path_image):
        # take image row and output to disk
        with open(path_image, 'wb') as f:
            f.write(row[FaceDetectTransform.COL_IMAGE_DATA][0])

    @staticmethod
    def output_names_():
        return [FaceDetectTransform.COL_IMAGE_IDX, FaceDetectTransform.COL_REGION_IDX,
                FaceDetectTransform.COL_FACE_X, FaceDetectTransform.COL_FACE_Y,
                FaceDetectTransform.COL_FACE_W, FaceDetectTransform.COL_FACE_H,
                FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA]

    @staticmethod
    def generate_out_dict(idx=VAL_REGION_IMAGE_ID, x=0, y=0, w=0, h=0, image=0, bin_stream=b"", media=""):
        return dict(zip(FaceDetectTransform.output_names_(), [image, idx, x, y, w, h, media, bin_stream]))

    @staticmethod
    def suppress_image(df):
        blank_cols = [FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA]
        # set columns that aren't in our known column list to empty strings; search where face index==-1 (no face)
        df[blank_cols] = None
        return df

    @property
    def _type_in(self):
        """Custom input type for this processing transformer"""
        return [(FaceDetectTransform.COL_IMAGE_MIME, str), (FaceDetectTransform.COL_IMAGE_DATA, bytes)], "Image"

    @property
    def _type_out(self):
        """Custom input type for this processing transformer"""
        output_dict = FaceDetectTransform.generate_out_dict()
        return [(k, type(output_dict[k])) for k in output_dict], "RegionDetection"

    def score(self, X, y=None):
        return 0

    def fit(self, X, y=None):
        return self

    def load_cascade(self):
        # if no model exists yet, create it; return False for deserialize required
        if self.cascade_obj is None:
            if self.cascade_stream is not None:
                import tempfile
                with tempfile.TemporaryDirectory() as tdir:
                    cascade_data = FaceDetectTransform.string_decompress(self.cascade_stream['data'])
                    cascade_path = os.path.join(tdir, self.cascade_stream['name'])
                    with open(cascade_path, 'wb') as f:
                        f.write(cascade_data)
                    self.cascade_obj = cv2.CascadeClassifier(cascade_path)
            return False
        return True

    def predict(self, X, y=None):
        """
        Assumes a numpy array of [[mime_type, binary_string] ... ]
           where mime_type is an image-specifying mime type and binary_string is the raw image bytes
        """
        self.load_cascade()  # JIT load model
        listData = []
        for image_idx in range(len(X)):
            image_byte = X[FaceDetectTransform.COL_IMAGE_DATA][image_idx]
            if type(image_byte) == str:
                image_byte = image_byte.encode()
                image_byte = base64.b64decode(image_byte)
            image_byte = bytearray(image_byte)
            file_bytes = np.asarray(image_byte, dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            # img = cv2.imread(image_set[1])
            faces = self.detect_faces(img)

            if self.include_image:  # create and append the image if that's requested
                listData.append(FaceDetectTransform.generate_out_dict(w=img.shape[1], h=img.shape[0], image=image_idx,
                                                                      media=X[FaceDetectTransform.COL_IMAGE_MIME][image_idx],
                                                                      bin_stream=X[FaceDetectTransform.COL_IMAGE_DATA][image_idx]))
            for idxF in range(len(faces)):  # walk through detected faces
                face_rect = faces[idxF]
                listData.append(FaceDetectTransform.generate_out_dict(idxF, x=face_rect[0], y=face_rect[1],
                                                                      w=face_rect[2], h=face_rect[3], image=image_idx))
            # print("IMAGE {:} found {:} total rows".format(image_idx, len(df)))

        return pd.DataFrame(listData, columns=FaceDetectTransform.output_names_())  # start with empty DF for this image

    def detect_faces(self, img):
        if self.cascade_obj is None:
            return []
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = self.cascade_obj.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Draw a rectangle around the faces
        # for (x, y, w, h) in faces:
        #    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return faces
