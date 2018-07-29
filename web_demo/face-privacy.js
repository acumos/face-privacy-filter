/*
  ===============LICENSE_START=======================================================
  Acumos Apache-2.0
  ===================================================================================
  Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
  ===================================================================================
  This Acumos software file is distributed by AT&T and Tech Mahindra
  under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  This file is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
  ===============LICENSE_END=========================================================
*/
/**
 face-privacy.js - send frames to an face privacy service; clone from image-classes.js

 Videos or camera are displayed locally and frames are periodically sent to GPU image-net classifier service (developed by Zhu Liu) via http post.
 For webRTC, See: https://gist.github.com/greenido/6238800

 D. Gibbon 6/3/15
 D. Gibbon 4/19/17 updated to new getUserMedia api, https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
 D. Gibbon 8/1/17 adapted for system
 E. Zavesky 10/19/17 adapted for video+image
 E. Zavesky 05/05/18 adapted for row-based image and other results
 E. Zavesky 05/30/18 forked model generic code to `demo-framework.js`, switch to flat image
 */

"use strict";

/**
 * main entry point
 */

// called one time when document is ready
$(document).ready(function() {
    var urlDefault = getUrlParameter('url-image');
    if (!urlDefault)
        urlDefault = "http://localhost:8884/classify";
    demo_init({
        classificationServer: urlDefault,
        protoList: [["model.pixelate.proto", true], ["model.detect.proto", false], ["model.recognize.proto", false] ],
        mediaList: [
            {
                'img': 'images/face_reunion.jpg',
                'source': 'https://flic.kr/p/bEgYbs',
                'name': 'reuninon (flickr)'
            },
            {
                'img': 'images/face_family.jpg',
                'source': 'https://www.pexels.com/photo/adult-affection-beautiful-beauty-265764',
                'name': 'family (pexels)'
            },
            {
                'img': 'images/commercial.jpg',
                'movie': "images/commercial.mp4",
                'source': 'https://www.youtube.com/watch?v=34KfCNapnUg',
                'name': 'family (pexels)'
            },
            {
                'img': 'images/face_Schwarzenegger.jpg',
                'source': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/A._Schwarzenegger.jpg/220px-A._Schwarzenegger.jpg',
                'name': 'Schwarzenegger (wikipedia)'
            },            {
                'img': 'images/face_DeGeneres.jpg',
                'source': 'https://en.wikipedia.org/wiki/Ellen_DeGeneres#/media/File:Ellen_DeGeneres-2009.jpg',
                'name': 'DeGeneres (wikipedia)'
            },
        ]
    });
});



// what do we do with a good processing result?
//
//  data: the raw body from the response
//  dstImg: the dom element of a destination image
//  methodKeys: which protomethod was selected
//  dstImg: the dom element of a destination image (if available)
//  imgPlaceholder: the exported canvas image from last source
//
function processResult(data, dstDiv, methodKeys, dstImg, imgPlaceholder) {
    var hd = $(document.body).data('hdparams');
    if (methodKeys) {
        //console.log(request);
        var bodyEncodedInString = new Uint8Array(data);
        //console.log(bodyEncodedInString);
        //console.log(bodyEncodedInString.length);
        $("#protoOutput").prop("disabled",false);
        hd.protoPayloadOutput = bodyEncodedInString;

        // ---- method for processing from a type ----
        var msgOutput = hd.protoObj[methodKeys[0]]['root'].lookupType(hd.protoObj[methodKeys[0]]['methods'][methodKeys[1]]['typeOut']);
        var objOutput = null;
        try {
            objOutput = msgOutput.decode(hd.protoPayloadOutput);
        }
        catch(err) {
            var errStr = "Error: Failed to parse protobuf response, was the right method chosen? (err: "+err.message+")";
            console.log(errStr);
            dstDiv.html(errStr);
            return false;
        }
        var nameRepeated = null;

        // NOTE: this code expects one top-level item to be an array of nested results
        //  e.g.   Image{mime_type, image_binary}
        //  e.g.   DetectionFrameSet [ DetectionFrame{x, y, ...., mime_type, image_binary}, .... ]

        //try to crawl the fields in the protobuf....
        var numFields = 0;
        $.each(msgOutput.fields, function(name, val) {           //collect field names
            if (val.repeated) {     //indicates it's a repeated field (likely an array)
                nameRepeated = name;      //save this as last repeated field (ideally there is just one)
            }
            numFields += 1;
        });

        var typeNested = methodKeys[0]+"."+msgOutput.name;
        if (nameRepeated) {
            objOutput = objOutput[nameRepeated];  // dereference neseted object
            typeNested = methodKeys[0]+"."+msgOutput.fields[nameRepeated].type;
        }
        else {
            objOutput = [objOutput];    // simple singleton wrapper for uniform code below
        }

        //grab the nested array type and print out the fields of interest
        var msgOutputNested = hd.protoObj[methodKeys[0]]['root'].lookupType(typeNested);
        //console.log(msgOutputNested);
        var domTable = $("<tr />");
        var arrNames = [];
        $.each(msgOutputNested.fields, function(name, val) {           //collect field names
            var nameClean = val.name;
            if (nameClean != 'imageBinary') {
                domTable.append($("<th />").html(nameClean));
                arrNames.push([nameClean, val.repeated]);
            }
        });
        domTable = $("<table />").append(domTable);     // create embedded table

        // loop through all members of array to do two things:
        //  (1) find the biggest/best image
        //  (2) print out the textual fields
        var objBest = null;
        $.each(objOutput, function(idx, val) {
            if ('imageBinary' in val) {
                // at this time, we only support ONE output image, so we will loop through
                //  to grab the largest image (old code could grab the one with region == -1)
                if (objBest==null || val.imageBinary.length>objBest.imageBinary.length) {
                    objBest = val;
                }
            }

            var domRow = $("<tr />");
            $.each(arrNames, function(idx, field_data) {      //collect data from each column
                //add safety to avoid printing repeated rows!
                domRow.append($("<td />").html(!field_data[1] ?
                    val[field_data[0]] : val[field_data[0]].length + " items"));
            });
            if (val.x && val.y) {  //valid bounding box examples?
                canvas_rect(false, val.x, val.y, val.w, val.h, hd.colorSet[idx % hd.colorSet.length]);
                domRow.children(":nth-child(2)").append($("<div class='colorblock'/>").css(
                    "background-color", hd.colorSet[idx % hd.colorSet.length]));
            }
            domTable.append(domRow);
        });
        dstDiv.empty().append($("<strong />").html("Results")).show();
        dstDiv.append(domTable);

        //did we find an image? show it now!
        if (objBest != null) {
            //some images are too big for direct btoa/array processing...
            //dstImg.attr('src', "data:"+objBest.mimeType+";base64,"+strImage).removeClass('workingImage');
            dstImg.attr('src', BlobToDataURI(objBest.imageBinary, objBest.mimeType)).removeClass('workingImage');
        }
        else if (imgPlaceholder) {
            dstImg.attr('src', imgPlaceholder).removeClass('workingImage');
        }
        else {
            var errStr = "Error: No valid image data was found and no placeholder, aborting display.";
            console.log(errStr);
            dstDiv.html(errStr);
            return false;
        }
    }
    else {       //legacy code where response was in base64 encoded image...
        var responseJson = $.parseJSON(data);
        var respImage = responseJson[0];
        // https://stackoverflow.com/questions/21227078/convert-base64-to-image-in-javascript-jquery
        dstImg.attr('src', "data:"+respImage['mime_type']+";base64,"+respImage['image_binary']).removeClass('workingImage');
    }
}


