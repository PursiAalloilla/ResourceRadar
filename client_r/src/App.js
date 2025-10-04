import { useRef, useEffect } from 'react'
import mapboxgl from 'mapbox-gl'

import 'mapbox-gl/dist/mapbox-gl.css';

import './App.css';

const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

console.log(MAPBOX_TOKEN);

function App() {

  const mapRef = useRef()
  const mapContainerRef = useRef()

    useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN 
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [ 25.631302 , 64.984528],
      zoom: 4.5
    });

    return () => {
      mapRef.current.remove()
    }
  }, [])

  return (
    <>
      <div id='map-container' ref={mapContainerRef}/>
    </>
  )
}
export default App;
