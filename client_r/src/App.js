import { useRef, useEffect } from 'react'
import mapboxgl from 'mapbox-gl'

import 'mapbox-gl/dist/mapbox-gl.css';

import './App.css';


//importing the mapbox token from .env
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
console.log(MAPBOX_TOKEN);


//setting the intiial view
const INITIAL_CENTER = [ 25.631302 , 64.984528]
const INITIAL_ZOOM = 4.5

//creating the map
function App() {

  const mapRef = useRef()
  const mapContainerRef = useRef()

  const [center, setCenter] = useState(INITIAL_CENTER)
  const [zoom, setZoom] = useState(INITIAL_ZOOM)


    useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN 
    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: center,
      zoom: zoom
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
