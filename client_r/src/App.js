import { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'

import 'mapbox-gl/dist/mapbox-gl.css';

import './App.css';

import testData from './testData.json';

import {markerHelper } from './helpers/marker'

//importing the mapbox token from .env
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
const API_URL = process.env.REACT_APP_API_URL

//setting the intiial view
const INITIAL_CENTER = [ 25.631302 , 64.984528]
const INITIAL_ZOOM = 4.5

//creating the map
function App() {

  const mapRef = useRef()
  const mapContainerRef = useRef()

  const [center, setCenter] = useState(INITIAL_CENTER)
  const [zoom, setZoom, icons] = useState(INITIAL_ZOOM)

  const dataString = JSON.stringify(testData);



  const data = JSON.parse(dataString);

  /*
  useEffect(() => {
    const Edata = async() =>{
       const response = await fetch(`${API_URL}/resources/`);
       const sData = await response.json();
       const parsedData = JSON.parse(sData);
    }

  })
  */

  useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN 
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: center,
      zoom: zoom
    });

      mapRef.current.on('move', () => {
      // get the current center coordinates and zoom level from the map
      const mapCenter = mapRef.current.getCenter()
      const mapZoom = mapRef.current.getZoom()
      // update state
      setCenter([ mapCenter.lng, mapCenter.lat ])
      setZoom(mapZoom)


    })

  
    return () => {
      mapRef.current.remove()
    }
  }, []);

   useEffect(() => {
    if (!mapRef.current) return;
    data.forEach(feature => {
      if (feature.location_geojson) {
        // extracting the geo.json and parsing it (stored in string inside the JSON)
        const geoJson = JSON.parse(feature.location_geojson);
        new mapboxgl.Marker(markerHelper(feature.category))
          .setLngLat(geoJson.coordinates || geoJson.geometry.coordinates)
          .setPopup(
            new mapboxgl.Popup({ offset: 25 }) // add popups
              .setHTML(
                 `<h3>${feature.category}</h3><p>${feature.name}: ${feature.quantity} <br> ${feature.user_type}</p>`
               )
              )
          .addTo(mapRef.current);
      }
    });
  }, [data]);

const handleButtonClick = () => {
  mapRef.current.flyTo({
    center: INITIAL_CENTER,
    zoom: INITIAL_ZOOM
  })
}


return (
    <>
      <div className="sidebar">
        Longitude: {center[0].toFixed(4)} | Latitude: {center[1].toFixed(4)} | Zoom: {zoom.toFixed(2)}
      </div>
      <button className='reset-button' onClick={handleButtonClick}>
        Reset
      </button>
      <div id='map-container' ref={mapContainerRef}/>
    </>
  );
}
export default App;
