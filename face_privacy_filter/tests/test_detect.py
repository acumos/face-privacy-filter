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

from os import path
import pytest


def test_detect_single(monkeypatch):
    pathRoot = env_update(monkeypatch)
    from face_privacy_filter.transform_detect import FaceDetectTransform
    transform = FaceDetectTransform(include_image=False)
    inputDf = FaceDetectTransform.generate_in_df(path.join(pathRoot, 'testing', 'single-face_pexels.jpg'))
    outputDf = transform.predict(inputDf)
    assert len(outputDf) == 1                       # just one face, no image
    assert outputDf['w'][0] == outputDf['h'][0]     # make sure width/height is equal
    assert outputDf['w'][0] > 680                    # reasonable face size detection
    assert len(outputDf['image_binary'][0]) == 0     # there should be no binary data on detect regions
    print(outputDf)   # run `pytest -s` for more verbosity


def test_detect_multi(monkeypatch):
    pathRoot = env_update(monkeypatch)
    from face_privacy_filter.transform_detect import FaceDetectTransform
    transform = FaceDetectTransform(include_image=True)
    inputDf = FaceDetectTransform.generate_in_df(path.join(pathRoot, 'testing', 'multi-face_pexels.jpg'))
    outputDf = transform.predict(inputDf)
    assert len(outputDf) == 5       # note ONE face will be missed, but we get the original image, too
    imageDf = outputDf[outputDf['region']==-1]
    assert len(imageDf) == 1       # note ONE face will be missed, but we get the original image, too
    assert imageDf['w'][0] == 1280  # should be the original image size
    assert len(imageDf['image_binary'][0]) > 1  # should be the original image size
    assert len(outputDf[outputDf['image']==0]) == len(outputDf)  # all responses belong to image 0
    print(outputDf)


def env_update(monkeypatch):
    import sys

    pathRoot = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    print("Adding '{:}' to sys path".format(pathRoot))
    if pathRoot not in sys.path:
        monkeypatch.syspath_prepend(pathRoot)
    return pathRoot
