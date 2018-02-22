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
 face-privacy.js - send frames to an face privacy service

 Videos or camera are displayed locally and frames are periodically sent to GPU image-net classifier service (developed by Zhu Liu) via http post.
 For webRTC, See: https://gist.github.com/greenido/6238800

 D. Gibbon 6/3/15
 D. Gibbon 4/19/17 updated to new getUserMedia api, https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
 D. Gibbon 8/1/17 adapted for system
 E. Zavesky 10/19/17 adapted for video+image
 */

"use strict";

/**
 * main entry point
 */
$(document).ready(function() {
    var urlDefault = getUrlParameter('url-image');
    if (!urlDefault)
        urlDefault = "http://localhost:8884/transform";

	$(document.body).data('hdparams', {	// store global vars in the body element
		classificationServer: urlDefault,
		protoObj: null,   // to be back-filled after protobuf load {'root':obj, 'methods':{'xx':{'typeIn':x, 'typeOut':y}} }
		protoPayloadInput: null,   //payload for encoded message download (if desired)
		protoPayloadOutput: null,   //payload for encoded message download (if desired)
		protoRes: null,  //TEMPORARY
		frameCounter: 0,
		frameInterval: 500,		// Milliseconds to sleep between sending frames to reduce server load and reduce results updates
		frameTimer: -1,		// frame clock for processing
		imageIsWaiting: false,  // blocking to prevent too many queued frames
		// Objects from DOM elements
		srcImgCanvas: document.getElementById('srcImgCanvas'),	// we have a 'src' source image
		destImg: document.getElementById('destImg'),	// we have a 'src' source image
		video: document.getElementById('srcVideo'),
	});
    $(document.body).data('hdparams')['canvasMaxH'] = $(document.body).data('hdparams')['srcImgCanvas'].height;
    $(document.body).data('hdparams')['canvasMaxW'] = $(document.body).data('hdparams')['srcImgCanvas'].width;

    $("#protoInput").prop("disabled",true).click(downloadBlobIn);
    $("#protoOutput").prop("disabled",true).click(downloadBlobOut);
    $("#resultText").hide();

	//add text input tweak
	$("#serverUrl").change(function() {
	    $(document.body).data('hdparams')['classificationServer'] = $(this).val();
        updateLink("serverLink");
	}).val($(document.body).data('hdparams')['classificationServer'])
	//set launch link at first
    updateLink("serverLink");

	// add buttons to change video
	$("#sourceRibbon div").click(function() {
	    var $this = $(this);
	    $this.siblings().removeClass('selected'); //clear other selection
	    $this.addClass('selected');
	    var objImg = $this.children('img')[0];
	    var hd = $(document.body).data('hdparams');
	    if (objImg) {
	        switchImage(objImg.src);
            clearInterval(hd.frameTimer);	// stop the processing

            var movieAttr = $(objImg).attr('movie');
            if (movieAttr) {
                // Set the video source based on URL specified in the 'videos' list, or select camera input
                $(hd.video).show();
                $(srcImgCanvas).hide();
                if (movieAttr == "Camera") {
                    var constraints = {audio: false, video: true};
                    navigator.mediaDevices.getUserMedia(constraints)
                        .then(function(mediaStream) {
                            hd.video.srcObject = mediaStream;
                            hd.video.play();
                        })
                        .catch(function(err) {
                            console.log(err.name + ": " + err.message);
                        });
                } else {
                    var mp4 = document.getElementById("mp4");
                    mp4.setAttribute("src", movieAttr);
                    hd.video.load();
                    newVideo();
                }
            }
            else {
                hd.video.pause();
                $(hd.video).hide();
                $(srcImgCanvas).show();
            }
	    }
	});

	//allow user-uploaded images
    var imageLoader = document.getElementById('imageLoader');
    imageLoader.addEventListener('change', handleImage, false);

    //if protobuf is enabled, fire load event for it as well
    $(document.body).data('hdparams').protoObj = {};  //clear from last load
    protobuf_load("model.pixelate.proto", true);
    protobuf_load("model.detect.proto");

    //trigger first click
    $("#sourceRibbon div")[0].click();
});


function protobuf_load(pathProto, forceSelect) {
    protobuf.load(pathProto, function(err, root) {
        if (err) {
            console.log("[protobuf]: Error!: "+err);
            throw err;
        }
        var domSelect = $("#protoMethod");
        var numMethods = domSelect.children().length;
        $.each(root.nested, function(namePackage, objPackage) {    // walk all
            if ('Model' in objPackage && 'methods' in objPackage.Model) {    // walk to model and functions...
                var typeSummary = {'root':root, 'methods':{} };
                $.each(objPackage.Model.methods, function(nameMethod, objMethod) {  // walk methods
                    typeSummary['methods'][nameMethod] = {};
                    typeSummary['methods'][nameMethod]['typeIn'] = namePackage+'.'+objMethod.requestType;
                    typeSummary['methods'][nameMethod]['typeOut'] = namePackage+'.'+objMethod.responseType;
                    typeSummary['methods'][nameMethod]['service'] = namePackage+'.'+nameMethod;

                    //create HTML object as well
                    var namePretty = namePackage+"."+nameMethod;
                    var domOpt = $("<option />").attr("value", namePretty).text(
                        nameMethod+ " (input: "+objMethod.requestType
                        +", output: "+objMethod.responseType+")");
                    if (numMethods==0) {    // first method discovery
                        domSelect.append($("<option />").attr("value","").text("(disabled, not loaded)")); //add 'disabled'
                    }
                    if (forceSelect) {
                        domOpt.attr("selected", 1);
                    }
                    domSelect.append(domOpt);
                    numMethods++;
                });
                $(document.body).data('hdparams').protoObj[namePackage] = typeSummary;   //save new method set
                $("#protoContainer").show();
            }
        });
        console.log("[protobuf]: Load successful, found "+numMethods+" model methods.");
    });
}

/**
 * Called after a new video has loaded (at least the video metadata has loaded)
 */
function newVideo() {
	var hd = $(document.body).data('hdparams');
	hd.frameCounter = 0;
	hd.imageIsWaiting = false;
	hd.video.play();

	// set processing canvas size based on source video
	var pwidth = hd.video.videoWidth;
	var pheight = hd.video.videoHeight;
	if (pwidth > hd.maxSrcVideoWidth) {
		pwidth = hd.maxSrcVideoWidth;
		pheight = Math.floor((pwidth / hd.video.videoWidth) * pheight);	// preserve aspect ratio
	}
	hd.srcImgCanvas.width = pwidth;
	hd.srcImgCanvas.height = pheight;

	hd.frameTimer = setInterval(nextFrame, hd.frameInterval); // start the processing
}

/**
 * process the next video frame
 */
function nextFrame() {
	var hd = $(document.body).data('hdparams');
	if (hd.video.ended || hd.video.paused) {
		return;
	}
    switchImage(hd.video, true);
}

function updateLink(domId, newServer) {
    var sPageURL = decodeURIComponent(window.location.search.split('?')[0]);
    if (newServer==undefined) {
        newServer = $(document.body).data('hdparams')['classificationServer'];
    }
    else {
        $("#serverUrl").val(newServer);
    }
    var sNewUrl = sPageURL+"?url-image="+newServer;
    $("#"+domId).attr('href', sNewUrl);
}

function switchImage(imgSrc, isVideo) {
    var canvas = $(document.body).data('hdparams')['srcImgCanvas'];
    if (!isVideo) {
        var img = new Image();
        img.onload = function () {
            var ctx = canvas.getContext('2d');
            var canvasCopy = document.createElement("canvas");
            var copyContext = canvasCopy.getContext("2d");

            var ratio = 1;

            //console.log( $(document.body).data('hdparams'));
            //console.log( [ img.width, img.height]);
            // https://stackoverflow.com/a/2412606
            if(img.width > $(document.body).data('hdparams')['canvasMaxW'])
                ratio = $(document.body).data('hdparams')['canvasMaxW'] / img.width;
            if(ratio*img.height > $(document.body).data('hdparams')['canvasMaxH'])
                ratio = $(document.body).data('hdparams')['canvasMaxH'] / img.height;

            canvasCopy.width = img.width;
            canvasCopy.height = img.height;
            copyContext.drawImage(img, 0, 0);

            canvas.width = img.width * ratio;
            canvas.height = img.height * ratio;
            ctx.drawImage(canvasCopy, 0, 0, canvasCopy.width, canvasCopy.height, 0, 0, canvas.width, canvas.height);
            //document.removeChild(canvasCopy);
            doPostImage(canvas, '#destImg', canvas.toDataURL());
        }
        img.src = imgSrc;  //copy source, let image load
    }
    else if (!$(document.body).data('hdparams').imageIsWaiting) {
        var ctx = canvas.getContext('2d');
        var canvasCopy = document.createElement("canvas");
        var copyContext = canvasCopy.getContext("2d");
        var ratio = 1;

        if(imgSrc.videoWidth > $(document.body).data('hdparams')['canvasMaxW'])
            ratio = $(document.body).data('hdparams')['canvasMaxW'] / imgSrc.videoWidth;
        if(ratio*imgSrc.videoHeight > $(document.body).data('hdparams')['canvasMaxH'])
            ratio = $(document.body).data('hdparams')['canvasMaxH'] / canvasCopy.height;

        //console.log("Canvas Copy:"+canvasCopy.width+"/"+canvasCopy.height);
        //console.log("Canvas Ratio:"+ratio);
        //console.log("Video: "+imgSrc.videoWidth+"x"+imgSrc.videoHeight);
        canvasCopy.width = imgSrc.videoWidth;     //large as possible
        canvasCopy.height = imgSrc.videoHeight;
        copyContext.drawImage(imgSrc, 0, 0);

        canvas.width = canvasCopy.width * ratio;
        canvas.height = canvasCopy.height * ratio;
        ctx.drawImage(canvasCopy, 0, 0, canvasCopy.width, canvasCopy.height, 0, 0, canvas.width, canvas.height);
        //document.removeChild(canvasCopy);
        doPostImage(canvas, '#destImg', canvas.toDataURL());
    }
}


//load image that has been uploaded into a vancas
function handleImage(e){
    var reader = new FileReader();
    reader.onload = function(event){
        switchImage(event.target.result);
    }
    reader.readAsDataURL(e.target.files[0]);
}



// https://stackoverflow.com/questions/19491336/get-url-parameter-jquery-or-how-to-get-query-string-values-in-js
function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};


/**
 * post an image from the canvas to the service
 */
function doPostImage(srcCanvas, dstImg, dataPlaceholder) {
    var dataURL = srcCanvas.toDataURL('image/jpeg', 1.0);
    var hd = $(document.body).data('hdparams');
    var sendPayload = null;

    var nameProtoMethod = $("#protoMethod option:selected").attr('value');
    var methodKeys = null;
    if (nameProtoMethod && nameProtoMethod.length) {     //valid protobuf type?
        var partsURL = hd.classificationServer.split("/");
        methodKeys = nameProtoMethod.split(".", 2);       //modified for multiple detect/pixelate models
        partsURL[partsURL.length-1] = methodKeys[1];
        hd.classificationServer = partsURL.join("/");   //rejoin with new endpoint
        updateLink("serverLink", hd.classificationServer);
    }

    var serviceURL = hd.classificationServer;
    var request = new XMLHttpRequest();     // create request to manipulate
    request.open("POST", serviceURL, true);

    //console.log("[doPostImage]: Selected method ... '"+typeInput+"'");
    if (nameProtoMethod && nameProtoMethod.length) {     //valid protobuf type?
        var blob = dataURItoBlob(dataURL, true);

        // fields from .proto file at time of writing...
        //    message FaceImage {
        //      repeated string mime_type = 1;   -> becomes "mimeType" (NOTE repeated type)
        //      repeated bytes image_binary = 2; -> becomes "imageBinary"
        //    }

        //TODO: should we always assume this is input? answer: for now, YES, always image input!
        var inputPayload = { "mimeType": [blob.type], "imageBinary": [blob.bytes] };

        // ---- method for processing from a type ----
        var msgInput = hd.protoObj[methodKeys[0]]['root'].lookupType(hd.protoObj[methodKeys[0]]['methods'][methodKeys[1]]['typeIn']);
        // Verify the payload if necessary (i.e. when possibly incomplete or invalid)
        var errMsg = msgInput.verify(inputPayload);
        if (errMsg) {
            console.log("[doPostImage]: Error during type verify for object input into protobuf method.");
            throw Error(errMsg);
        }
        // Create a new message
        var msgTransmit = msgInput.create(inputPayload);
        // Encode a message to an Uint8Array (browser) or Buffer (node)
        sendPayload = msgInput.encode(msgTransmit).finish();

        // ----------

        /*
        // ---- method for processing from a service ----
        var serviceInput = hd.protoObj['root'].lookup(hd.protoObj['methods'][nameProtoMethod]['service']);

        function rpcImpl(method, requestData, callback) {
            // perform the request using an HTTP request or a WebSocket for example
            var responseData = ...;
            // and call the callback with the binary response afterwards:
            callback(null, responseData);
        }
        var serviceCall = serviceInput.create(rpcImpl, false, false); //request dlimited? response delimited?

        serviceCall.sayHello(sendPayload).then(response) {
            console.log('Greeting:', response.message);
        });
        // ---------------------------
        */

        //downloadBlob(sendPayload, 'protobuf.bin', 'application/octet-stream');
        // NOTE: TO TEST THIS BINARY BLOB, use some command-line magic like this...
        //  protoc --decode=mMJuVapnmIbrHlZGKyuuPDXsrkzpGqcr.FaceImage model.proto < protobuf.bin
        $("#protoInput").prop("disabled",false);
        hd.protoPayloadInput = sendPayload;

        // append our encoded chunk
        //console.log(sendPayload);
        //console.log(typeof(blob.type));
        // console.log(nameProtoMethod);
        request.setRequestHeader("Content-type", "text/plain;charset=UTF-8");
        request.responseType = 'arraybuffer';
    }
    else {
        var blob = dataURItoBlob(dataURL, false);
        sendPayload = new FormData();
        sendPayload.append("image_binary", blob);
        sendPayload.append("mime_type", blob.type);
    }
    //$(dstImg).addClaas('workingImage').siblings('.spinner').remove().after($("<span class='spinner'>&nbsp;</span>"));
    $(document.body).data('hdparams').imageIsWaiting = true;
    var $dstImg = $(dstImg);
    if ($dstImg.attr('src')=='') {
        $dstImg.attr('src', dataPlaceholder);
        //$(dstImg).addClass('workingImage').attr('src', dataPlaceholder);
    }

    hd.imageIsWaiting = true;
    request.onreadystatechange=function() {
        if (request.readyState==4 && request.status>=200 && request.status<300) {
            if (methodKeys!=null) {     //valid protobuf type?
                //console.log(request);
                var bodyEncodedInString = new Uint8Array(request.response);
                //console.log(bodyEncodedInString);
                //console.log(bodyEncodedInString.length);
                $("#protoOutput").prop("disabled",false);
                hd.protoPayloadOutput = bodyEncodedInString;

                // ---- method for processing from a type ----
                var msgOutput = hd.protoObj[methodKeys[0]]['root'].lookupType(hd.protoObj[methodKeys[0]]['methods'][methodKeys[1]]['typeOut']);
                var objRecv = msgOutput.decode(hd.protoPayloadOutput);
                //console.log(objRecv);
                hd.protoRes = objRecv;

                // detect what mode we're in (detect alone or processed?)...
                if (!Array.isArray(objRecv.mimeType)) {
                    $dstImg.attr('src', "data:"+objRecv.mimeType+";base64,"+objRecv.imageBinary).removeClass('workingImage');
                }
                else {
                    var domResult = $("#resultText");
                    var domTable = $("<tr />");
                    var arrNames = [];
                    $.each(msgOutput.fields, function(name, val) {           //collect field names
                        var nameClean = val.name;
                        if (nameClean != 'imageBinary') {
                            domTable.append($("<th />").html(nameClean));
                            arrNames.push(nameClean);
                        }
                    });
                    domTable = $("<table />").append(domTable);     // create embedded table

                    var idxImg = -1;
                    if ('region' in msgOutput.fields) {             // did we get regions?
                        for (var i=0; i<objRecv.region.length; i++) {       //find the right region
                            if (objRecv.region[i]==-1) {                    //special indicator for original image
                                idxImg = i;
                            }
                            var domRow = $("<tr />");
                            var strDisplay = [];
                            $.each(arrNames, function(idx, name) {      //collect data from each column
                                domRow.append($("<td />").html(objRecv[name][i]));
                            });
                            domTable.append(domRow);
                            //domResult.append($("div").html(objRecv.region));
                        }
                        domResult.empty().append($("<strong />").html("Results")).show();
                        domResult.append(domTable);
                    }
                    else {                                  //got images, get that chunk directly
                        idxImg = 0;
                    }

                    if (idxImg != -1) {                     //got any valid image? display it
                        //console.log(objRecv.mimeType[idxImg]);
                        //console.log(objRecv.imageBinary[idxImg]);
                        //var strImage = Uint8ToString(objRecv.imageBinary[idxImg]);
                        var strImage = btoa(String.fromCharCode.apply(null, objRecv.imageBinary[idxImg]));
                        $dstImg.attr('src', "data:"+objRecv.mimeType[idxImg]+";base64,"+strImage).removeClass('workingImage');
                    }
                }

            }
            else {
                var responseJson = $.parseJSON(request.responseText);
                var respImage = responseJson[0];
                // https://stackoverflow.com/questions/21227078/convert-base64-to-image-in-javascript-jquery
                $dstImg.attr('src', "data:"+respImage['mime_type']+";base64,"+respImage['image_binary']).removeClass('workingImage');
                //genClassTable($.parseJSON(request.responseText), dstDiv);
            }
            hd.imageIsWaiting = false;
        }
	}
	request.send(sendPayload);
	$(document.body).data('hdparams').imageIsWaiting = false;
}


/**
 * convert base64/URLEncoded data component to raw binary data held in a string
 *
 * Stoive, http://stackoverflow.com/questions/4998908/convert-data-uri-to-file-then-append-to-formdata
 */
function dataURItoBlob(dataURI, wantBytes) {
    // convert base64/URLEncoded data component to raw binary data held in a string
    var byteString;
    if (dataURI.split(',')[0].indexOf('base64') >= 0)
        byteString = atob(dataURI.split(',')[1]);
    else
        byteString = unescape(dataURI.split(',')[1]);

    // separate out the mime component
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

    // write the bytes of the string to a typed array
    var ia = new Uint8Array(byteString.length);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    //added for returning bytes directly
    if (wantBytes) {
        return {'bytes':ia, 'type':mimeString};
    }
    return new Blob([ia], {type:mimeString});
}

function Uint8ToString(u8a){
  var CHUNK_SZ = 0x8000;
  var c = [];
  for (var i=0; i < u8a.length; i+=CHUNK_SZ) {
    c.push(String.fromCharCode.apply(null, u8a.subarray(i, i+CHUNK_SZ)));
  }
  return c.join("");
}


// ----- diagnostic tool to download binary blobs ----
function downloadBlobOut() {
    return downloadBlob($(document.body).data('hdparams').protoPayloadOutput, "protobuf.out.bin");
}

function downloadBlobIn() {
    return downloadBlob($(document.body).data('hdparams').protoPayloadInput, "protobuf.in.bin");
}

//  https://stackoverflow.com/a/33622881
function downloadBlob(data, fileName, mimeType) {
  //if there is no data, filename, or mime provided, make our own
  if (!data)
      data = $(document.body).data('hdparams').protoPayloadInput;
  if (!fileName)
      fileName = "protobuf.bin";
  if (!mimeType)
      mimeType = "application/octet-stream";

  var blob, url;
  blob = new Blob([data], {
    type: mimeType
  });
  url = window.URL.createObjectURL(blob);
  downloadURL(url, fileName, mimeType);
  setTimeout(function() {
    return window.URL.revokeObjectURL(url);
  }, 1000);
};

function downloadURL(data, fileName) {
  var a;
  a = document.createElement('a');
  a.href = data;
  a.download = fileName;
  document.body.appendChild(a);
  a.style = 'display: none';
  a.click();
  a.remove();
};
