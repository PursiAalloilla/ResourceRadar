import { useRef, useEffect, useState } from 'react'
import axios from 'axios'
import mapboxgl from 'mapbox-gl'

import 'mapbox-gl/dist/mapbox-gl.css';

import './App.css';

import {markerHelper } from './helpers/marker'

//importing the mapbox token from .env
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000'

//setting the initial view
const INITIAL_CENTER = [ 25.631302 , 64.984528]
const INITIAL_ZOOM = 4.5

//creating the map
function App() {

  const mapRef = useRef()
  const mapContainerRef = useRef()
  const markersRef = useRef([])

  const [center, setCenter] = useState(INITIAL_CENTER)
  const [zoom, setZoom] = useState(INITIAL_ZOOM)
  const [resources, setResources] = useState([])
  const [flaggedResources, setFlaggedResources] = useState([])
  const [showFlaggedTable, setShowFlaggedTable] = useState(false)
  const [loading, setLoading] = useState(true)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [error, setError] = useState(null)

  // Fetch resources from API
  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true)
        const response = await axios.get(`${API_URL}/api/resources/`)
        const allResources = response.data.resources || []
        
        // Separate flagged and non-flagged resources
        const flagged = allResources.filter(resource => resource.flagged === true)
        const nonFlagged = allResources.filter(resource => resource.flagged !== true)
        
        setResources(nonFlagged)
        setFlaggedResources(flagged)
        setError(null)
      } catch (err) {
        console.error('Error fetching resources:', err)
        setError('Failed to fetch resources')
      } finally {
        setLoading(false)
      }
    }

    fetchResources()
  }, [])

  // Initialize map
  useEffect(() => {
    if (!MAPBOX_TOKEN) {
      setError('Mapbox token not found')
      return
    }

    // Use a small delay to ensure DOM is ready
    const initializeMap = () => {
      if (!mapContainerRef.current) {
        console.error('Map container not found')
        return
      }

      try {
        mapboxgl.accessToken = MAPBOX_TOKEN 
        mapRef.current = new mapboxgl.Map({
          container: mapContainerRef.current,
          center: center,
          zoom: zoom
        });

        mapRef.current.on('move', () => {
          const mapCenter = mapRef.current.getCenter()
          const mapZoom = mapRef.current.getZoom()
          setCenter([ mapCenter.lng, mapCenter.lat ])
          setZoom(mapZoom)
        })

        // Wait for map to load before adding markers
        mapRef.current.on('load', () => {
          console.log('Map loaded successfully')
          setMapLoaded(true)
        })

      } catch (error) {
        console.error('Error initializing map:', error)
        setError('Failed to initialize map')
      }
    }

    // Try to initialize immediately, if that fails, try after a short delay
    if (mapContainerRef.current) {
      initializeMap()
    } else {
      // Use setTimeout to ensure DOM is ready
      const timer = setTimeout(() => {
        if (mapContainerRef.current) {
          initializeMap()
        } else {
          console.error('Map container still not found after delay')
          setError('Map container not available')
        }
      }, 100)

      return () => {
        clearTimeout(timer)
        if (mapRef.current) {
          mapRef.current.remove()
        }
      }
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
      }
    }
  }, []);

  // Add markers to map when resources change
  useEffect(() => {
    if (!mapRef.current || !resources.length || !mapLoaded) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    // Add new markers for non-flagged resources
    resources.forEach(resource => {
      if (resource.location_geojson) {
        try {
          const geoJson = JSON.parse(resource.location_geojson);
          const coordinates = geoJson.coordinates || geoJson.geometry?.coordinates;
          
          if (coordinates && coordinates.length >= 2) {
            const marker = new mapboxgl.Marker(markerHelper(resource.category))
              .setLngLat(coordinates)
              .setPopup(
                new mapboxgl.Popup({ offset: 25 })
                  .setHTML(
                    `<h3>${resource.category}</h3>
                     <p><strong>${resource.name}</strong></p>
                     <p>Quantity: ${resource.quantity || 'N/A'}</p>
                     <p>Type: ${resource.user_type || 'N/A'}</p>
                     <p>Phone: ${resource.phone_number || 'N/A'}</p>
                     <p>Created: ${new Date(resource.created_at).toLocaleDateString()}</p>`
                  )
              )
              .addTo(mapRef.current);
            
            markersRef.current.push(marker)
          }
        } catch (err) {
          console.error('Error parsing location for resource:', resource.id, err)
        }
      }
    });
  }, [resources, mapLoaded]);

  const handleResetClick = () => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: INITIAL_CENTER,
        zoom: INITIAL_ZOOM
      })
    }
  }

  const handleShowFlaggedClick = () => {
    setShowFlaggedTable(!showFlaggedTable)
  }

  const handleCloseFlaggedTable = () => {
    setShowFlaggedTable(false)
  }

  if (loading) {
    return (
      <div className="loading">
        <p>Loading resources...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
      </div>
    )
  }

  return (
    <>
      <div className="sidebar">
        Longitude: {center[0].toFixed(4)} | Latitude: {center[1].toFixed(4)} | Zoom: {zoom.toFixed(2)}
        <br />
        Resources: {resources.length} | Flagged: {flaggedResources.length}
      </div>
      
      <button className='reset-button' onClick={handleResetClick}>
        Reset View
      </button>
      
      {flaggedResources.length > 0 && (
        <button className='flagged-button' onClick={handleShowFlaggedClick}>
          View Flagged Resources ({flaggedResources.length})
        </button>
      )}
      
      {showFlaggedTable && (
        <div className="flagged-table-overlay">
          <div className="flagged-table-container">
            <div className="flagged-table-header">
              <h3>Flagged Resources ({flaggedResources.length})</h3>
              <button className="close-button" onClick={handleCloseFlaggedTable}>×</button>
            </div>
            <div className="flagged-table-content">
              <table className="flagged-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Name</th>
                    <th>Quantity</th>
                    <th>Type</th>
                    <th>Phone</th>
                    <th>Reason</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {flaggedResources.map(resource => (
                    <tr key={resource.id}>
                      <td>{resource.category}</td>
                      <td>{resource.name}</td>
                      <td>{resource.quantity || 'N/A'}</td>
                      <td>{resource.user_type || 'N/A'}</td>
                      <td>{resource.phone_number || 'N/A'}</td>
                      <td>{resource.abuse_reason || 'N/A'}</td>
                      <td>{new Date(resource.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
      
      <div id='map-container' ref={mapContainerRef} style={{ width: '100%', height: '100%' }}/>
    </>
  );
}

export default App;