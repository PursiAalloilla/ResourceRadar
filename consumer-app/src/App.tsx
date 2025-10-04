import { useState, useEffect } from 'react'
import axios from 'axios'
import logo from './assets/logo.png';
import './App.css'

interface Message {
  id: number;
  text: string;
  isSystem: boolean;
  timestamp: Date;
}

function App() {
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [canUserInput, setCanUserInput] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Show logo for 3 minutes (180000ms) then switch to chat
    const timer = setTimeout(() => {
      setShowChat(true);
      // Add initial system messages
      const systemMessages: Message[] = [
        {
          id: 1,
          text: "🚨 EMERGENCY ALERT: A severe weather event has been detected in your area. Local authorities are coordinating emergency response efforts.",
          isSystem: true,
          timestamp: new Date()
        },
        {
          id: 2,
          text: "We need volunteers to assist with emergency response coordination. Can you help? Please describe what resources you have available and provide your location (zipcode or proximity to a landmark).",
          isSystem: true,
          timestamp: new Date()
        }
      ];
      setMessages(systemMessages);
      setCanUserInput(true);
    }, 5000); // Reduced to 5 seconds for demo purposes

    return () => clearTimeout(timer);
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || !canUserInput) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: userInput,
      isSystem: false,
      timestamp: new Date()
    };

    // Add user message immediately
    setMessages(prevMessages => [...prevMessages, userMessage]);
    const messageText = userInput;
    setUserInput('');
    setIsProcessing(true);

    // Create processing message with dots
    const processingMessage: Message = {
      id: Date.now() + 1,
      text: "Processing message...",
      isSystem: true,
      timestamp: new Date()
    };

    setMessages(prevMessages => [...prevMessages, processingMessage]);

    // Prepare API request data
    const apiData = {
      text: messageText,
      metadata: {
        incident_location: {
          type: "Point",
          coordinates: [22.2705, 60.4518] // Turku coordinates
        },
        phone_number: "+358401234567",
        user_type: "civilian"
      }
    };

    try {
      // Call the API
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/process_message/`,
        apiData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('API Response:', response.data);

      // Remove processing message and add acknowledgment
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => msg.id !== processingMessage.id);
        const acknowledgmentMessage: Message = {
          id: Date.now() + 2,
          text: "✅ Message received and logged in our emergency response system. Your assistance has been noted and will be coordinated by our team. Thank you for your willingness to help during this critical situation.",
          isSystem: true,
          timestamp: new Date()
        };
        return [...filtered, acknowledgmentMessage];
      });

    } catch (error) {
      console.error('API Error:', error);
      
      // Remove processing message and add error message
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => msg.id !== processingMessage.id);
        const errorMessage: Message = {
          id: Date.now() + 2,
          text: "⚠️ Message received locally. System connection temporarily unavailable, but your information has been logged for emergency response coordination.",
          isSystem: true,
          timestamp: new Date()
        };
        return [...filtered, errorMessage];
      });
    }

    setIsProcessing(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        setAudioChunks([audioBlob]);
        stream.getTracks().forEach(track => track.stop());
      };

      setMediaRecorder(recorder);
      setAudioChunks([]);
      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Microphone access denied. Please allow microphone access to record voice messages.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const sendAudioMessage = async () => {
    if (audioChunks.length === 0) return;

    const audioBlob = audioChunks[0];
    
    // Create user message for UI
    const userMessage: Message = {
      id: Date.now(),
      text: "🎤 Voice message recorded",
      isSystem: false,
      timestamp: new Date()
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);

    // Close the overlay and show processing state
    setAudioChunks([]);
    setMediaRecorder(null);
    setIsProcessing(true);

    // Create processing message with dots
    const processingMessage: Message = {
      id: Date.now() + 1,
      text: "Processing voice message...",
      isSystem: true,
      timestamp: new Date()
    };

    setMessages(prevMessages => [...prevMessages, processingMessage]);

    // Prepare form data for multipart upload
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    
    const metadata = {
      incident_location: {
        type: "Point",
        coordinates: [22.2705, 60.4518] // Turku coordinates
      },
      phone_number: "+358401234567",
      user_type: "civilian"
    };
    
    formData.append('metadata', JSON.stringify(metadata));

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/process_message/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      console.log('Audio API Response:', response.data);

      // Remove processing message and add acknowledgment
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => msg.id !== processingMessage.id);
        const acknowledgmentMessage: Message = {
          id: Date.now() + 2,
          text: "✅ Voice message received and processed. Your assistance has been noted and will be coordinated by our team. Thank you for your willingness to help during this critical situation.",
          isSystem: true,
          timestamp: new Date()
        };
        return [...filtered, acknowledgmentMessage];
      });

    } catch (error) {
      console.error('Audio API Error:', error);
      
      // Remove processing message and add error message
      setMessages(prevMessages => {
        const filtered = prevMessages.filter(msg => msg.id !== processingMessage.id);
        const errorMessage: Message = {
          id: Date.now() + 2,
          text: "⚠️ Voice message received locally. System connection temporarily unavailable, but your information has been logged for emergency response coordination.",
          isSystem: true,
          timestamp: new Date()
        };
        return [...filtered, errorMessage];
      });
    }

    setIsProcessing(false);
  };

  if (!showChat) {
    return (
      <div className="logo-screen">
        <div className="powered-by">Powered by</div>
        <div className="logo-container">
          <div className="app-logo">
            <img src={logo} alt="Emergency Response Logo" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Emergency Response Chat</h2>
        <div className="status-indicator">🟢 Connected</div>
      </div>
      
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.isSystem ? 'system' : 'user'}`}>
            <div className="message-content">
              {message.text}
            </div>
            <div className="message-time">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      {canUserInput && (
        <form onSubmit={handleSendMessage} className="input-form">
          <div className="input-container">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Describe your resources and location..."
              className="message-input"
            />
            <button 
              type="button" 
              className={`voice-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
              onClick={startRecording}
              disabled={isRecording || isProcessing}
            >
              🎤
            </button>
            <button 
              type="submit" 
              className={`send-button ${isProcessing ? 'processing' : ''}`}
              disabled={isProcessing}
            >
              Send
            </button>
          </div>
        </form>
      )}

      {/* Recording Overlay */}
      {isRecording && (
        <div className="recording-overlay">
          <div className="recording-content">
            <div className="recording-animation">
              <div className="recording-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
              <p>Recording voice message...</p>
            </div>
            <div className="recording-controls">
              <button onClick={stopRecording} className="stop-button">
                Stop Recording
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Audio Send Overlay */}
      {audioChunks.length > 0 && !isRecording && (
        <div className="recording-overlay">
          <div className="recording-content">
            <div className="audio-preview">
              <p>🎤 Voice message ready</p>
              <div className="audio-controls">
                <button onClick={sendAudioMessage} className="send-audio-button">
                  Send Voice Message
                </button>
                <button onClick={() => setAudioChunks([])} className="cancel-button">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App
