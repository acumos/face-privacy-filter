/*
  ===============LICENSE_START=======================================================
  Acumos
  ===================================================================================
  Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
  ===================================================================================
  This Acumos documentation file is distributed by AT&T and Tech Mahindra
  under the Creative Commons Attribution 4.0 International License (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://creativecommons.org/licenses/by/4.0

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

    //trigger first click
    $("#sourceRibbon div")[0].click();
});


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

function updateLink(domId) {
    var sPageURL = decodeURIComponent(window.location.search.split('?')[0]);
    var newServer = $(document.body).data('hdparams')['classificationServer'];
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
	var serviceURL = "";
	var dataURL = srcCanvas.toDataURL('image/jpeg', 1.0);
	var blob = dataURItoBlob(dataURL);
	var hd = $(document.body).data('hdparams');
	var fd = new FormData();

	$(document.body).data('hdparams').imageIsWaiting = true;
    serviceURL = hd.classificationServer;
    fd.append("image_binary", blob);
    fd.append("mime_type", "image/jpeg");
    var $dstImg = $(dstImg);
    if ($dstImg.attr('src')=='') {
        $dstImg.attr('src', dataPlaceholder);
        //$(dstImg).addClass('workingImage').attr('src', dataPlaceholder);
    }
    //$(dstImg).addClaas('workingImage').siblings('.spinner').remove().after($("<span class='spinner'>&nbsp;</span>"));

	var request = new XMLHttpRequest();
	hd.imageIsWaiting = true;
	request.onreadystatechange=function() {
		if (request.readyState==4 && request.status==200) {
		    var responseJson = $.parseJSON(request.responseText);
		    var respImage = responseJson[0];
		    // https://stackoverflow.com/questions/21227078/convert-base64-to-image-in-javascript-jquery
            $dstImg.attr('src', "data:"+respImage['mime_type']+";base64,"+respImage['image_binary']).removeClass('workingImage');
			//genClassTable($.parseJSON(request.responseText), dstDiv);
			hd.imageIsWaiting = false;
		}
	}
	request.open("POST", serviceURL, true);
	request.send(fd);
	$(document.body).data('hdparams').imageIsWaiting = false;
}


/**
 * convert base64/URLEncoded data component to raw binary data held in a string
 *
 * Stoive, http://stackoverflow.com/questions/4998908/convert-data-uri-to-file-then-append-to-formdata
 */
function dataURItoBlob(dataURI) {
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

    return new Blob([ia], {type:mimeString});
}

