import { useRef, useEffect, useState } from 'react'
import axios from 'axios'
import mapboxgl from 'mapbox-gl'

import 'mapbox-gl/dist/mapbox-gl.css';

import './App.css';

import {markerHelper } from './helpers/marker'

//importing the mapbox token from .env
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000'

//setting the initial view for Nordic countries
const INITIAL_CENTER = [ 15.0, 63.0] // Center of Nordic region
const INITIAL_ZOOM = 4.5

// Nordic countries bounds
const NORDIC_BOUNDS = [
  [4.0, 55.0], // Southwest corner (west of Denmark, south of Denmark)
  [32.0, 71.0] // Northeast corner (east of Finland, north of Norway)
]

// Helper function to get category icon
const getCategoryIcon = (category) => {
  const icons = {
    'SKILLS': '👥',
    'FUEL': '⛽',
    'FOOD': '🍽️',
    'WATER': '💧',
    'MEDICAL_SUPPLIES': '🏥',
    'SHELTER': '🏠',
    'TRANSPORT': '🚗',
    'EQUIPMENT': '🔧',
    'COMMUNICATION': '📡',
    'OTHER': '📦'
  }
  return icons[category] || '📦'
}

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
  
  // Emergency location
  const emergencyLocation = {
    name: "Turku center",
    coordinates: [22.2705, 60.4518] // Turku coordinates
  }

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
          zoom: zoom,
          maxBounds: NORDIC_BOUNDS, // Restrict map to Nordic countries
          maxZoom: 10 // Prevent zooming in too much
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
          
          // Add emergency location marker
          const emergencyMarker = new mapboxgl.Marker({ color: 'red' })
            .setLngLat(emergencyLocation.coordinates)
            .setPopup(
              new mapboxgl.Popup({ offset: 25 })
                .setHTML(`<h3 style="color: red; margin: 0;">🚨 Emergency Location</h3><p style="margin: 0;">${emergencyLocation.name}</p>`)
            )
            .addTo(mapRef.current)
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
            // Location is already a GeoJSON object, not a string
            const coordinates = resource.location_geojson.coordinates;
            
            if (coordinates && coordinates.length >= 2) {
              // Build popup content dynamically
              const popupContent = `
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 250px;">
                  <div style="display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e1e5e9;">
                    <div style="font-size: 1.5em; margin-right: 8px;">${getCategoryIcon(resource.category)}</div>
                    <div>
                      <h3 style="margin: 0; color: #2c3e50; font-size: 1.1em; font-weight: 600;">${resource.category}</h3>
                      ${resource.subcategory ? `<div style="font-size: 0.9em; color: #7f8c8d; margin-top: 2px;">${resource.subcategory}</div>` : ''}
                    </div>
                  </div>
                  
                  <div style="margin-bottom: 10px;">
                    <div style="font-weight: 600; color: #34495e; margin-bottom: 4px;">Resource</div>
                    <div style="color: #2c3e50; font-size: 1.05em;">${resource.name}</div>
                  </div>
                  
                  ${resource.quantity ? `
                    <div style="margin-bottom: 10px;">
                      <div style="font-weight: 600; color: #34495e; margin-bottom: 4px;">Available</div>
                      <div style="color: #27ae60; font-weight: 500;">${resource.quantity} ${resource.quantity === 1 ? 'unit' : 'units'}</div>
                    </div>
                  ` : ''}
                  
                  ${resource.user_type ? `
                    <div style="margin-bottom: 10px;">
                      <div style="font-weight: 600; color: #34495e; margin-bottom: 4px;">Provider Type</div>
                      <div style="color: #3498db; font-weight: 500;">${resource.user_type.replace(/_/g, ' ')}</div>
                    </div>
                  ` : ''}
                  
                  ${resource.phone_number ? `
                    <div style="margin-bottom: 10px;">
                      <div style="font-weight: 600; color: #34495e; margin-bottom: 4px;">Contact</div>
                      <div style="color: #e74c3c; font-weight: 500;">
                        <a href="tel:${resource.phone_number}" style="color: #e74c3c; text-decoration: none;">📞 ${resource.phone_number}</a>
                      </div>
                    </div>
                  ` : ''}
                  
                  ${resource.first_name || resource.last_name ? `
                    <div style="margin-bottom: 10px;">
                      <div style="font-weight: 600; color: #34495e; margin-bottom: 4px;">Contact Person</div>
                      <div style="color: #2c3e50;">${[resource.first_name, resource.last_name].filter(Boolean).join(' ')}</div>
                    </div>
                  ` : ''}
                  
                  <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #ecf0f1; font-size: 0.85em; color: #95a5a6;">
                    Added ${new Date(resource.created_at).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'short', 
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              `;

              const marker = new mapboxgl.Marker(markerHelper(resource.category, resource.subcategory))
                .setLngLat(coordinates)
                .setPopup(
                  new mapboxgl.Popup({ offset: 25, maxWidth: '300px' })
                    .setHTML(popupContent)
                )
                .addTo(mapRef.current);
              
              markersRef.current.push(marker)
            }
          } catch (err) {
            console.error('Error processing location for resource:', resource.id, err)
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
      
      <div className="emergency-location">
        <div className="emergency-location-content">
          <div className="emergency-indicator">🚨</div>
          <div className="emergency-text">
            <div className="emergency-label">Emergency Location</div>
            <div className="emergency-name">{emergencyLocation.name}</div>
          </div>
        </div>
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