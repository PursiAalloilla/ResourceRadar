import { useState, useEffect } from 'react'
import logo from './assets/logo.png'
import './App.css'

type UserType = 'NGO' | 'GOVERNMENT_AGENCY' | 'CORPORATE_ENTITY' | 'LOCAL_AUTHORITY'

type VerificationResponse = {
  domain: string
  email: string
  message?: string
  ok: boolean
  reason?: string
  user_type: string
}

type ConfirmationResponse = {
  verified: boolean
  message?: string
}

type AppState = 'splash' | 'form' | 'email-code' | 'success' | 'error' | 'resource-form'

const userTypeLabels: Record<UserType, string> = {
  NGO: 'Non-Governmental Organization',
  GOVERNMENT_AGENCY: 'Government Agency',
  CORPORATE_ENTITY: 'Corporate Entity',
  LOCAL_AUTHORITY: 'Local Authority'
}

// Subcategory definitions based on backend models
const subcategories = {
  SKILLS: {
    MEDICAL: 'Medical',
    CONSTRUCTION: 'Construction',
    IT: 'IT',
    LANGUAGE: 'Language',
    MECHANIC: 'Mechanic',
    OTHER: 'Other'
  },
  FUEL: {
    DIESEL: 'Diesel',
    GASOLINE: 'Gasoline',
    PROPANE: 'Propane',
    BATTERIES: 'Batteries'
  },
  FOOD: {
    NON_PERISHABLE: 'Non-Perishable',
    PERISHABLE: 'Perishable',
    BABY_FOOD: 'Baby Food',
    PET_FOOD: 'Pet Food'
  },
  WATER: {
    BOTTLED: 'Bottled',
    FILTERS: 'Filters',
    PURIFICATION_TABLETS: 'Purification Tablets'
  },
  MEDICAL_SUPPLIES: {
    FIRST_AID: 'First Aid',
    MEDICATION: 'Medication',
    EQUIPMENT: 'Equipment'
  },
  SHELTER: {
    TENTS: 'Tents',
    BLANKETS: 'Blankets'
  },
  TRANSPORT: {
    VEHICLES: 'Vehicles',
    BOATS: 'Boats',
    FUEL_TRUCKS: 'Fuel Trucks'
  },
  EQUIPMENT: {
    GENERATORS: 'Generators',
    TOOLS: 'Tools',
    PROTECTIVE_GEAR: 'Protective Gear'
  },
  COMMUNICATION: {
    RADIOS: 'Radios',
    SATPHONES: 'Satellite Phones',
    POWER_BANKS: 'Power Banks'
  },
  OTHER: {
    UNKNOWN: 'Unknown'
  }
}

// Helper function to check if category is skills
const isSkillsCategory = (category: string) => category === 'SKILLS'

function App() {
  const [appState, setAppState] = useState<AppState>('splash')
  const [email, setEmail] = useState('')
  const [userType, setUserType] = useState<UserType>('CORPORATE_ENTITY')
  const [verificationCode, setVerificationCode] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Resource form state
  const [resourceData, setResourceData] = useState({
    category: '',
    subcategory: '',
    name: '',
    quantity: '',
    phone_number: '',
    user_type: userType,
    location_coordinates: [23.7610, 61.4981] as [number, number], // Default to Tampere
    location_input: ''
  })
  const [locationPermission, setLocationPermission] = useState<'unknown' | 'granted' | 'denied'>('unknown')
  const [isGettingLocation, setIsGettingLocation] = useState(false)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

  // Show splash screen for 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setAppState('form')
    }, 3000)
    return () => clearTimeout(timer)
  }, [])

  // Request location when resource form is shown
  useEffect(() => {
    if (appState === 'resource-form' && locationPermission === 'unknown') {
      // Auto-request location when form first loads
      getUserLocation()
    }
  }, [appState])

  const handleVerify = async () => {
    if (!email || !userType) {
      setErrorMessage('Please fill in all fields')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      const response = await fetch(`${API_URL}/api/verify-legal-entity/request/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          user_type: userType
        })
      })

      const data: VerificationResponse = await response.json()

      if (data.ok) {
        setAppState('email-code')
      } else {
        setErrorMessage(data.reason || 'Verification failed')
        setAppState('error')
      }
    } catch (error) {
      setErrorMessage('Network error. Please try again.')
      setAppState('error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCodeSubmit = async () => {
    if (verificationCode.length !== 6) {
      setErrorMessage('Please enter all 6 digits')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      const response = await fetch(`${API_URL}/api/verify-legal-entity/confirm/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          code: verificationCode
        })
      })

      const data: ConfirmationResponse = await response.json()

      if (data.verified) {
        setAppState('resource-form')
      } else {
        setErrorMessage(data.message || 'Invalid verification code')
        setAppState('error')
      }
    } catch (error) {
      setErrorMessage('Network error. Please try again.')
      setAppState('error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    // Only allow numeric input and max 6 digits
    if (/^\d{0,6}$/.test(value)) {
      setVerificationCode(value)
    }
  }

  const handleCreateResource = async () => {
    if (!resourceData.name.trim()) {
      setErrorMessage('Resource name is required')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      const response = await fetch(`${API_URL}/api/resources/create/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: resourceData.category || undefined,
          subcategory: resourceData.subcategory || undefined,
          name: resourceData.name,
          quantity: resourceData.quantity ? parseInt(resourceData.quantity) : undefined,
          phone_number: resourceData.phone_number || undefined,
          user_type: resourceData.user_type,
          location_geojson: {
            type: "Point",
            coordinates: resourceData.location_coordinates
          },
          source_text: "manual entry"
        })
      })

      const data = await response.json()

      if (data.ok) {
        // Reset form data for next resource creation
        setResourceData({
          category: '',
          subcategory: '',
          name: '',
          quantity: '',
          phone_number: '',
          user_type: userType,
          location_coordinates: [23.7610, 61.4981] as [number, number],
          location_input: ''
        })
        setAppState('success')
        setErrorMessage('')
      } else {
        setErrorMessage(data.error || 'Failed to create resource')
      }
    } catch (error) {
      setErrorMessage('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const resetApp = () => {
    setAppState('form')
    setEmail('')
    setUserType('CORPORATE_ENTITY')
    setVerificationCode('')
    setErrorMessage('')
    setLocationPermission('unknown')
    setIsGettingLocation(false)
  }

  const handleResourceInputChange = (field: string, value: string) => {
    setResourceData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by this browser.')
      return
    }

    setIsGettingLocation(true)
    setErrorMessage('')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords
        setResourceData(prev => ({
          ...prev,
          location_coordinates: [longitude, latitude] as [number, number],
          location_input: prev.location_input || 'Current location'
        }))
        setLocationPermission('granted')
        setIsGettingLocation(false)
      },
      (error) => {
        setIsGettingLocation(false)
        setLocationPermission('denied')
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setErrorMessage('Location access denied. Please enable location permissions or enter coordinates manually.')
            break
          case error.POSITION_UNAVAILABLE:
            setErrorMessage('Location information is unavailable. Please enter coordinates manually.')
            break
          case error.TIMEOUT:
            setErrorMessage('Location request timed out. Please try again or enter coordinates manually.')
            break
          default:
            setErrorMessage('An unknown error occurred while retrieving location.')
            break
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    )
  }

  if (appState === 'splash') {
    return (
      <div className="splash-screen">
        <div className="logo-placeholder">
          <div style={{ 
            width: '120px', 
            height: '120px', 
            borderRadius: '50%', 
            backgroundColor: '#ffffff', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            marginBottom: '1rem',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)'
          }}>
            <div style={{ fontSize: '3em' }}>🏢</div>
          </div>
        </div>
        <div className="powered-by">
          <span>Powered by </span>
        </div>
        <img src={logo} alt="Platform Logo" style={{ width: '500px', height: 'auto' }} />
        <h1>Emergency Resource Portal</h1>
      </div>
    )
  }

  if (appState === 'form') {
    return (
      <div className="container">
        <h1>Emergency Resource Portal</h1>
        <div className="form-container">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="userType">Organization Type</label>
            <select
              id="userType"
              value={userType}
              onChange={(e) => setUserType(e.target.value as UserType)}
            >
              {Object.entries(userTypeLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {errorMessage && (
            <div className="error-message">{errorMessage}</div>
          )}

          <button onClick={handleVerify} disabled={isLoading}>
            {isLoading ? 'Verifying...' : 'Verify'}
          </button>
        </div>
      </div>
    )
  }

  if (appState === 'email-code') {
    return (
      <div className="container">
        <h1>Email Verification</h1>
        <div className="form-container">
          <p>We've sent a 6-digit verification code to:</p>
          <p style={{ fontWeight: 'bold', marginBottom: '2rem' }}>{email}</p>
          
          <div className="form-group">
            <label htmlFor="verificationCode">Verification Code</label>
            <input
              id="verificationCode"
              type="text"
              maxLength={6}
              value={verificationCode}
              onChange={handleCodeChange}
              placeholder="Enter 6-digit code"
              autoComplete="off"
              style={{
                textAlign: 'center',
                fontSize: '1.5em',
                letterSpacing: '0.5em',
                fontFamily: 'monospace'
              }}
            />
          </div>

          {errorMessage && (
            <div className="error-message">{errorMessage}</div>
          )}

          <button onClick={handleCodeSubmit} disabled={isLoading}>
            {isLoading ? 'Verifying...' : 'Verify Code'}
          </button>
        </div>
      </div>
    )
  }

  if (appState === 'resource-form') {
    return (
      <div className="container">
        <h1>Create Resource</h1>
        <div className="form-container">
          <p style={{ marginBottom: '2rem', color: '#666' }}>
            You are now authorized to create resources. Fill in the details below.
          </p>
          
          <div className="form-group">
            <label htmlFor="resourceName">
              {isSkillsCategory(resourceData.category) ? 'Profession *' : 'Resource Name *'}
            </label>
            <input
              id="resourceName"
              type="text"
              value={resourceData.name}
              onChange={(e) => handleResourceInputChange('name', e.target.value)}
              placeholder={isSkillsCategory(resourceData.category) ? 'e.g., Doctor, Engineer, Translator' : 'e.g., First aid kit, Emergency generator'}
            />
          </div>

          <div className="form-group">
            <label htmlFor="category">Category</label>
            <select
              id="category"
              value={resourceData.category}
              onChange={(e) => {
                handleResourceInputChange('category', e.target.value)
                // Reset subcategory when category changes
                handleResourceInputChange('subcategory', '')
              }}
            >
              <option value="">Select a category</option>
              <option value="SKILLS">Skills</option>
              <option value="FUEL">Fuel</option>
              <option value="FOOD">Food</option>
              <option value="WATER">Water</option>
              <option value="MEDICAL_SUPPLIES">Medical Supplies</option>
              <option value="SHELTER">Shelter</option>
              <option value="TRANSPORT">Transport</option>
              <option value="EQUIPMENT">Equipment</option>
              <option value="COMMUNICATION">Communication</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          {resourceData.category && (
            <div className="form-group">
              <label htmlFor="subcategory">Subcategory</label>
              <select
                id="subcategory"
                value={resourceData.subcategory}
                onChange={(e) => handleResourceInputChange('subcategory', e.target.value)}
              >
                <option value="">Select a subcategory</option>
                {Object.entries(subcategories[resourceData.category as keyof typeof subcategories] || {}).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="quantity">
              {isSkillsCategory(resourceData.category) ? 'No. Available People' : 'Quantity'}
            </label>
            <input
              id="quantity"
              type="number"
              value={resourceData.quantity}
              onChange={(e) => handleResourceInputChange('quantity', e.target.value)}
              placeholder={isSkillsCategory(resourceData.category) ? 'Number of people available' : 'Number of items'}
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Contact Phone Number</label>
            <input
              id="phone"
              type="tel"
              value={resourceData.phone_number}
              onChange={(e) => handleResourceInputChange('phone_number', e.target.value)}
              placeholder="+358401234567"
            />
          </div>

          <div className="form-group">
            <label htmlFor="locationInput">Location Description</label>
            <input
              id="locationInput"
              type="text"
              value={resourceData.location_input}
              onChange={(e) => handleResourceInputChange('location_input', e.target.value)}
              placeholder="e.g., Tampere central hospital"
            />
            <button
              type="button"
              onClick={getUserLocation}
              disabled={isGettingLocation}
              style={{
                marginTop: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isGettingLocation ? 'not-allowed' : 'pointer',
                opacity: isGettingLocation ? 0.6 : 1
              }}
            >
              {isGettingLocation ? 'Getting location...' : '📍 Use My Location'}
            </button>
            {locationPermission === 'granted' && (
              <small style={{ color: '#28a745', fontSize: '0.8em', display: 'block', marginTop: '0.5rem' }}>
                ✅ Location permission granted
              </small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="coordinates">Location Coordinates</label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                type="number"
                step="0.0001"
                value={resourceData.location_coordinates[1]}
                onChange={(e) => {
                  const lat = parseFloat(e.target.value) || 61.4981
                  setResourceData(prev => ({
                    ...prev,
                    location_coordinates: [prev.location_coordinates[0], lat] as [number, number]
                  }))
                }}
                placeholder="Latitude"
                style={{ flex: 1 }}
              />
              <span>,</span>
              <input
                type="number"
                step="0.0001"
                value={resourceData.location_coordinates[0]}
                onChange={(e) => {
                  const lng = parseFloat(e.target.value) || 23.7610
                  setResourceData(prev => ({
                    ...prev,
                    location_coordinates: [lng, prev.location_coordinates[1]] as [number, number]
                  }))
                }}
                placeholder="Longitude"
                style={{ flex: 1 }}
              />
            </div>
            <small style={{ color: '#666', fontSize: '0.8em' }}>
              Enter coordinates manually or use the preset locations below
            </small>
          </div>

          <div className="form-group">
            <label>Quick Location Selection</label>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => setResourceData(prev => ({
                  ...prev,
                  location_coordinates: [23.7610, 61.4981] as [number, number],
                  location_input: prev.location_input || 'Tampere'
                }))}
                style={{ fontSize: '0.9em', padding: '0.5rem', backgroundColor: '#495057', color: '#ffffff' }}
              >
                Tampere
              </button>
              <button
                type="button"
                onClick={() => setResourceData(prev => ({
                  ...prev,
                  location_coordinates: [24.9458, 60.1699] as [number, number],
                  location_input: prev.location_input || 'Helsinki'
                }))}
                style={{ fontSize: '0.9em', padding: '0.5rem', backgroundColor: '#495057', color: '#ffffff' }}
              >
                Helsinki
              </button>
              <button
                type="button"
                onClick={() => setResourceData(prev => ({
                  ...prev,
                  location_coordinates: [22.2783, 60.4506] as [number, number],
                  location_input: prev.location_input || 'Turku'
                }))}
                style={{ fontSize: '0.9em', padding: '0.5rem', backgroundColor: '#495057', color: '#ffffff' }}
              >
                Turku
              </button>
              <button
                type="button"
                onClick={() => setResourceData(prev => ({
                  ...prev,
                  location_coordinates: [25.7350, 62.2415] as [number, number],
                  location_input: prev.location_input || 'Oulu'
                }))}
                style={{ fontSize: '0.9em', padding: '0.5rem', backgroundColor: '#495057', color: '#ffffff' }}
              >
                Oulu
              </button>
            </div>
          </div>


          {errorMessage && (
            <div className="error-message">{errorMessage}</div>
          )}

          <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
            <button onClick={handleCreateResource} disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Resource'}
            </button>
            <button onClick={resetApp} style={{ backgroundColor: '#666' }}>
              Logout
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (appState === 'success') {
    return (
      <div className="container">
        <h1>🎉 Resource Created Successfully!</h1>
        <div className="form-container">
          <p>Your resource has been successfully added to the system.</p>
          <button onClick={() => setAppState('resource-form')}>
            Create Another Resource
          </button>
          <button onClick={resetApp} style={{ backgroundColor: '#666', marginLeft: '1rem' }}>
            Logout
          </button>
        </div>
      </div>
    )
  }

  if (appState === 'error') {
    return (
      <div className="container">
        <h1>❌ Verification Failed</h1>
        <div className="form-container">
          <p>{errorMessage}</p>
          <p>You cannot access the platform at this time.</p>
          <button onClick={resetApp}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return null
}

export default App
