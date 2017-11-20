

var phenoclim = phenoclim || {};
var geojsonMarkerOptions = {
    radius: 8,
    fillColor: "#ff7800",
    color: "#000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.3
};

var phenoMarker = L.AwesomeMarkers.icon({
  icon: 'leaf',
  prefix: 'ion',
  markerColor: 'green'
});

var areaMarker = L.AwesomeMarkers.icon({
  icon: 'ios-analytics',
  prefix: 'ion',
  markerColor: 'blue'
});

phenoclim.map = function(options){
  self = this;

  var defaults = {
    draggable: false,
    filter_draggable: false,
  };
  options = $.extend(defaults, options);

  self.draggableLayer;

  function onEachFeature(feature, layer) {
      // does this feature have a property named popupContent?
      if (feature.properties
          && feature.properties.draggable === true
          && options.draggable === true) {
        layer.options.draggable = true;
        self.draggableLayer = layer;

        layer.on("dragend", function(e){
          var latlng = e.target.getLatLng();
          $("[name=lat]").val(latlng.lat);
          $("[name=lon]").val(latlng.lng);
        });
      }
  }

  // initialize the map on the "map" div with a given center and zoom
    this._map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 11,
        maxZoom: 19
    });

    this.geojson = undefined;
    // add an OpenStreetMap tile layer
    // 'http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png'
    // 'http://tile.mtbmap.cz/mtbmap_tiles/{z}/{x}/{y}.png'
    var API_KEY = '851c476fad9743cca9b16af9c72ecc05';
    L.tileLayer('http://{s}.tile.thunderforest.com/landscape/{z}/{x}/{y}.png?apikey=' + API_KEY, {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this._map);

    L.control.scale({ imperial : false }).addTo(self._map);
    var bounds2 = [[46.38, -1.51],[42.71, 7.95]];
    if(options.geojson && options.geojson.features && options.geojson.features.length > 0){
      self.geojson = L.geoJson(options.geojson,{
          filter: function(feature){
            if (options.filter_draggable === true) {
              return (feature.properties && feature.properties.draggable === true);
            }
            return true;
          },
          pointToLayer: function (feature, latlng) {
            var ftype = feature.properties.object
            var layer;
            if(ftype)
            {
              if(ftype == "individual"){
                  layer = L.marker(latlng, {icon: phenoMarker});
              }
              else{
                  if (feature.properties
                    && feature.properties.draggable === true){
                    layer = L.marker(latlng, {icon: areaMarker});
                  }
                  else{
                    layer = L.circle(latlng, 500, geojsonMarkerOptions);
                  }
              }
            }
            return layer;
          },
          onEachFeature: onEachFeature
      }
      ).addTo(self._map);
      var bounds = self.geojson.getBounds();
      self._map.fitBounds(bounds, { maxZoom: 18, padding: [10, 10] });
    }
    else{
      self._map.fitBounds(bounds2);
    }

     $(".change_position").on("click",function(event){
       var rel = $(this).attr("data-rel");
       var id = $(this).attr("data-id");
       var layers = self.geojson.getLayers();
        for (var i = 0; i < layers.length; i++) {
          var properties = layers[i].feature.geometry.properties;
          if(properties.object == rel && properties.id == id){
            layers[i].dragging.enable();
            layers[i].on("dragend", function(e){
              var latlng = e.target.getLatLng();
              $("[name=lat]").val(latlng.lat);
              $("[name=lon]").val(latlng.lng);
            });
          }

        };
    });

    if(options.isLinked == true){
      self.geojson.eachLayer(function(layer){
        layer.on("click", function(event){
          var prop = event.target.feature.geometry.properties;
          if(prop.object=="individual" && prop.id){
            setTimeout(function(){ $(".display__individual[data-id=" + prop.id + "]").show();$(".display__individual[data-id=" + prop.id + "]>a").click(); }, 10);
            }
        });
      });
      $(".display__individual>a").on("click", function(event){
        event.preventDefault();
        var id=$(this).parent().attr("data-id");
        self.geojson.eachLayer(function(layer){
          var prop =layer.feature.geometry.properties;
          if(prop.object=="individual" && id==prop.id){
            layer.bindPopup("<div><img class='popup__picture' src='" + prop.picture + "'/><p class='text-center'>"+prop.name+"</p>");
            layer.openPopup();
            return false;
          }
        });
      });
    }
}

$.arrayIntersect = function(a, b)
{
    return $.grep(a, function(i)
    {
        return $.inArray(i, b) > -1;
    });
};

$.getKeys = function(dict){
  return $.map(dict, function(element,index) {return index})
};

$( document ).ready(function() {
  phenoclim.session = phenoclim.session || {}
  if($("#map").length > 0){
    phenoclim.session.map = new phenoclim.map(phenoclim.options);
    $(".map").trigger( "map_init");
  }
});
