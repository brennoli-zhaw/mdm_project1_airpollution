//use lng,lat
startCoordinates = [8.2198,46.9925]
ol.proj.useGeographic();
var view = new ol.View({
    center: ol.proj.fromLonLat([0,0]),
    zoom: 4,
  });

var map = new ol.Map({
    target: 'map',
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM()
        })
    ],
    view: view
});

view.animate({center: startCoordinates,duration:500});

function toFixed(x){
    return Number.parseFloat(x).toFixed(4)
    
}

function getModelPrediction(){
    let latElement = document.getElementById("lat")
    let lngElement = document.getElementById("lng")
    lat = isNaN(latElement.value) ? startCoordinates[1] : latElement.value
    lng = isNaN(lngElement.value) ? startCoordinates[0] : lngElement.value
    fetch('/api/predict?lat='+lat+'&lng='+lng, 
        {
            method: 'GET',
        }).then(
            response => {
                response.text().then(function (text) {
                    returned_data = JSON.parse(text)
                    
                    if(("score" in returned_data) && ("category" in returned_data)){
                        predictionEle = document.getElementById("prediction");
                        predictionEle.innerHTML = "<span>Predicted Airpollution Index: </span>" + returned_data.score + "<br/>" + "<span>Predicted Classification: </span>" + returned_data.category;
                        body = document.querySelector("body")
                        body.className = "";
                        body.classList.add(returned_data.category)
                    }
                    
                });
                return response
            }
        ).then(
            success => console.log(success)
        ).catch(
            error => console.log(error)
    );
}

function updateCoordinatesByMapEvent(e = -1){
    let coordinates = map.getView().getCenter()
    let latElement = document.getElementById("lat")
    let lngElement = document.getElementById("lng")
    latElement.value = toFixed(coordinates[1] + Math.round(coordinates[1] / 360) * 360)
    lng = coordinates[0] % 360
    if (lng > 180) {  
        lng = lng - 360;
    } else if (lng < -180) {
        lng = 360 + lng;
    }
    lngElement.value = toFixed(lng)
    getModelPrediction()
}

//a feature for the future
function reverseGeocoding(lat, lng) {
    fetch('https://services.gisgraphy.com/reversegeocoding/search?format=json&lat=' + lat + '&lng=' + lng).then(function(response) {
      return response.json();
    }).then(function(json) {
      document.getElementById('place').value = json.display_name;
    })
  }

function updateMapCenter(){
    let latElement = document.getElementById("lat")
    let lngElement = document.getElementById("lng")
    lat = isNaN(latElement.value) ? startCoordinates[1] : latElement.value
    lng = isNaN(lngElement.value) ? startCoordinates[0] : lngElement.value
    view.animate({center: [lng, lat],duration:150});
}

map.on('pointermove', function (e) {
    if (e.dragging) {
        updateCoordinatesByMapEvent(e)
    }
});

map.on('moveend', function(e) {
    updateCoordinatesByMapEvent(e)
});

window.addEventListener("mousemove", function(e) {
    if(e.buttons == 1) {
        updateCoordinatesByMapEvent(e)
        
    }
});



