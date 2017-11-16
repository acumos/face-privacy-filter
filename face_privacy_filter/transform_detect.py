#! python
# -*- coding: utf-8 -*-
"""
Wrapper for face detection task; wrapped in classifier for pipieline terminus
"""
import cv2
import os
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
import base64


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

    def __init__(self, cascade_path=None, include_image=True):
        self.include_image = include_image    # should output transform include image?
        self.cascade_path = cascade_path    # abs path outside of module
        self.cascade_obj = None  # late-load this component

    def get_params(self, deep=False):
        return {'include_image': self.include_image}

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
    def generate_out_dict(idx=VAL_REGION_IMAGE_ID, x=0, y=0, w=0, h=0, image=0, bin_stream=b"", media=""):
        return {FaceDetectTransform.COL_IMAGE_IDX: image, FaceDetectTransform.COL_REGION_IDX: idx,
                FaceDetectTransform.COL_FACE_X: x, FaceDetectTransform.COL_FACE_Y: y,
                FaceDetectTransform.COL_FACE_W: w, FaceDetectTransform.COL_FACE_H: h,
                FaceDetectTransform.COL_IMAGE_MIME: media, FaceDetectTransform.COL_IMAGE_DATA: bin_stream}

    @staticmethod
    def suppress_image(df):
        blank_cols = [FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA]
        # set columns that aren't in our known column list to empty strings; search where face index==-1 (no face)
        df[blank_cols] = None
        return df

    @property
    def _type_in(self):
        """Custom input type for this processing transformer"""
        return {FaceDetectTransform.COL_IMAGE_MIME: str, FaceDetectTransform.COL_IMAGE_DATA: bytes}, "FaceImage"

    @property
    def _type_out(self):
        """Custom input type for this processing transformer"""
        output_dict = FaceDetectTransform.generate_out_dict()
        return {k: type(output_dict[k]) for k in output_dict}, "DetectionFrames"

    def score(self, X, y=None):
        return 0

    def fit(self, X, y=None):
        return self

    def predict(self, X, y=None):
        """
        Assumes a numpy array of [[mime_type, binary_string] ... ]
           where mime_type is an image-specifying mime type and binary_string is the raw image bytes
        """
        # if no model exists yet, create it
        if self.cascade_obj is None:
            if self.cascade_path is not None:
                self.cascade_obj = cv2.CascadeClassifier(self.cascade_path)
            else:   # none provided, load what came with the package
                pathRoot = os.path.dirname(os.path.abspath(__file__))
                pathFile = os.path.join(pathRoot, FaceDetectTransform.CASCADE_DEFAULT_FILE)
                self.cascade_obj = cv2.CascadeClassifier(pathFile)

        dfReturn = None
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

            df = pd.DataFrame()  # start with empty DF for this image
            if self.include_image:  # create and append the image if that's requested
                dict_image = FaceDetectTransform.generate_out_dict(w=img.shape[1], h=img.shape[0], image=image_idx)
                dict_image[FaceDetectTransform.COL_IMAGE_MIME] = X[FaceDetectTransform.COL_IMAGE_MIME][image_idx]
                dict_image[FaceDetectTransform.COL_IMAGE_DATA] = X[FaceDetectTransform.COL_IMAGE_DATA][image_idx]
                df = pd.DataFrame([dict_image])
            for idxF in range(len(faces)):  # walk through detected faces
                face_rect = faces[idxF]
                df = df.append(pd.DataFrame([FaceDetectTransform.generate_out_dict(idxF, face_rect[0], face_rect[1],
                                                                                   face_rect[2], face_rect[3], image=image_idx)]),
                               ignore_index=True)
            if dfReturn is None:  # create an NP container for all image samples + features
                dfReturn = df   # df.reindex_axis(self.output_names_, axis=1)
            else:
                dfReturn = dfReturn.append(df, ignore_index=True)
            # print("IMAGE {:} found {:} total rows".format(image_idx, len(df)))

        return dfReturn

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
