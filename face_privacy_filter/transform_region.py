#! python
# -*- coding: utf-8 -*-
"""
Wrapper for region processing task; wrapped in classifier for pipieline terminus
"""
import cv2
import os
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

# NOTE: If this class were built in another model (e.g. another vendor, class, etc), we would need to
#       *exactly match* the i/o for the upstream (detection) and downstream (this processing)
from face_privacy_filter.transform_detect import FaceDetectTransform

class RegionTransform(BaseEstimator, ClassifierMixin):
    '''
    A sklearn classifier mixin that manpulates image content based on input
    '''

    def __init__(self, transform_mode="pixelate"):
        self.transform_mode = transform_mode    # specific image processing mode to utilize

    def get_params(self, deep=False):
        return {'transform_mode': self.transform_mode}

    @staticmethod
    def generate_out_df(media_type="", bin_stream=b""):
        # munge stream and mimetype into input sample
        return pd.DataFrame([[media_type, bin_stream]], columns=[FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA])

    @staticmethod
    def generate_in_df(idx=FaceDetectTransform.VAL_REGION_IMAGE_ID, x=0, y=0, w=0, h=0, image=0, bin_stream=b"", media=""):
        return pd.DataFrame([[idx,x,y,w,h,image,media,bin_stream]],
                            columns=[FaceDetectTransform.COL_REGION_IDX, FaceDetectTransform.COL_FACE_X, FaceDetectTransform.COL_FACE_Y,
                                     FaceDetectTransform.COL_FACE_W, FaceDetectTransform.COL_FACE_H,
                                     FaceDetectTransform.COL_IMAGE_IDX, FaceDetectTransform.COL_IMAGE_MIME,
                                     FaceDetectTransform.COL_IMAGE_DATA])

    @property
    def output_names_(self):
        return [FaceDetectTransform.COL_IMAGE_MIME, FaceDetectTransform.COL_IMAGE_DATA]

    @property
    def output_types_(self):
        list_name = self.output_names_
        list_type = self.classes_
        return [{list_name[i]:list_type[i]} for i in range(len(list_name))]

    @property
    def n_outputs_(self):
        return 8

    @property
    def classes_(self):
        return [str, str]

    def score(self, X, y=None):
        return 0

    def fit(self, X, y=None):
        return self

    def predict(self, X, y=None):
        """
        Assumes a numpy array of [[mime_type, binary_string] ... ]
           where mime_type is an image-specifying mime type and binary_string is the raw image bytes       
        """

        # group by image index first
        #   decode image at region -1
        #   collect all remaining regions, operate with each on input image
        #   generate output image, send to output

        dfReturn = None
        image_region_list = RegionTransform.transform_raw_sample(X)
        for image_data in image_region_list:
            #print(image_data)
            img = image_data['data']
            for r in image_data['regions']:  # loop through regions
                x_max = min(r[0]+r[2], img.shape[1])
                y_max = min(r[1]+r[3], img.shape[0])
                if self.transform_mode=="pixelate":
                    img[r[1]:y_max, r[0]:x_max] = \
                        RegionTransform.pixelate_image(img[r[1]:y_max, r[0]:x_max])

            # for now, we hard code to jpg output; TODO: add more encoding output (or try to match source?)
            img_binary = cv2.imencode(".jpg", img)[1].tostring()
            img_mime = 'image/jpeg'  # image_data['mime']

            df = RegionTransform.generate_out_df(media_type=img_mime, bin_stream=img_binary)
            if dfReturn is None:  # create an NP container for all images
                dfReturn = df.reindex_axis(self.output_names_, axis=1)
            else:
                dfReturn = dfReturn.append(df, ignore_index=True)
            print("IMAGE {:} found {:} total rows".format(image_data['image'], len(df)))
        return dfReturn

    @staticmethod
    def transform_raw_sample(raw_sample):
        """Method to transform raw samples into dict of image and regions"""
        raw_sample.sort_values([FaceDetectTransform.COL_IMAGE_IDX], ascending=True, inplace=True)
        groupImage = raw_sample.groupby(FaceDetectTransform.COL_IMAGE_IDX)
        return_set = []

        for nameG, rowsG in groupImage:
            local_image = {'image': -1, 'data': b"", 'regions': [], 'mime': ''}
            image_row = rowsG[rowsG[FaceDetectTransform.COL_REGION_IDX]==FaceDetectTransform.VAL_REGION_IMAGE_ID]
            if len(image_row) < 1:  # must have at least one image set
                print("Error: RegionTransform could not find a valid image reference for image set {:}".format(nameG))
                continue
            if not len(image_row[FaceDetectTransform.COL_IMAGE_DATA]):  # must have valid image data
                print("Error: RegionTransform expected image data, but found empty binary string {:}".format(nameG))
                continue
            file_bytes = np.asarray(bytearray(FaceDetectTransform.read_byte_arrays(image_row[FaceDetectTransform.COL_IMAGE_DATA][0])), dtype=np.uint8)
            local_image['data'] = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            local_image['image'] = nameG
            local_image['mime'] = image_row[FaceDetectTransform.COL_IMAGE_MIME]

            # now proceed to loop around regions detected
            for index, row in rowsG.iterrows():
                if row[FaceDetectTransform.COL_REGION_IDX]!=FaceDetectTransform.VAL_REGION_IMAGE_ID:  # skip bad regions
                    local_image['regions'].append([row[FaceDetectTransform.COL_FACE_X], row[FaceDetectTransform.COL_FACE_Y],
                                                   row[FaceDetectTransform.COL_FACE_W], row[FaceDetectTransform.COL_FACE_H]])
            return_set.append(local_image)
        return return_set

    ################################################################
    # image processing routines (using opencv)

    # http://www.jeffreythompson.org/blog/2012/02/18/pixelate-and-posterize-in-processing/
    @staticmethod
    def pixelate_image(img, blockSize=None):
        if not img.shape[0] or not img.shape[1]:
            return img
        if blockSize is None:
            blockSize = round(max(img.shape[0], img.shape[2]) / 8)
        ratio = (img.shape[1] / img.shape[0]) if img.shape[0] < img.shape[1] else (img.shape[0] / img.shape[1])
        blockHeight = round(blockSize * ratio)  # so that we cover all image
        for x in range(0, img.shape[0], blockSize):
            for y in range(0, img.shape[1], blockHeight):
                max_x = min(x+blockSize, img.shape[0])
                max_y = min(y+blockSize, img.shape[1])
                fill_color = img[x,y] # img[x:max_x, y:max_y].mean()
                img[x:max_x, y:max_y] = fill_color
        return img

# RegionTransform.__module__ = '__main__'
