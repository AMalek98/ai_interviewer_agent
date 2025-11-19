import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import SecurityMonitor from './components/security/SecurityMonitor';
import WarningModal from './components/security/WarningModal';

function OralInterview({ onBack }) {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  // Interview state
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [startTime, setStartTime] = useState(null);

  // Conversation state
  const [isInterviewerSpeaking, setIsInterviewerSpeaking] = useState(false);
  const [isCandidateSpeaking, setIsCandidateSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Audio recording
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

  // CV upload state
  const [cvFile, setCvFile] = useState(null);
  const [cvUploaded, setCvUploaded] = useState(false);
  const [cvProcessing, setCvProcessing] = useState(false);
  const [cvData, setCvData] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  // Speech recognition
  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } = useSpeechRecognition();

  // Voice selection
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState();

  // Voice Activity Detection (VAD)
  const silenceTimerRef = useRef(null);
  const [lastTranscriptLength, setLastTranscriptLength] = useState(0);

  // Error handling
  const [generalError, setGeneralError] = useState('');

  // Countdown timer state
  const [countdown, setCountdown] = useState(null);
  const [isCountingDown, setIsCountingDown] = useState(false);

  // Evaluation state
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationData, setEvaluationData] = useState(null);
  const [evaluationError, setEvaluationError] = useState('');
  const [expandedFeedback, setExpandedFeedback] = useState({});
  const [interviewFilename, setInterviewFilename] = useState('');

  // Security state
  const [securityEnabled, setSecurityEnabled] = useState(false);
  const [securityViolation, setSecurityViolation] = useState(null);
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);
  const securityMonitorRef = useRef(null);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices);
    };

    if (typeof window !== 'undefined') {
      window.speechSynthesis.onvoiceschanged = loadVoices;
      loadVoices();
    }
  }, []);

  // Cancel speech on page refresh
  useEffect(() => {
    const navEntries = performance.getEntriesByType('navigation');
    const isRefresh = navEntries.length && navEntries[0].type === 'reload';

    if (isRefresh) {
      window.speechSynthesis.cancel();
      console.log('Page refreshed — voice cancelled');
    }
  }, []);

  // Voice Activity Detection (VAD)
  useEffect(() => {
    if (!isCandidateSpeaking || !listening) return;

    // Check if transcript is still growing
    if (transcript.length > lastTranscriptLength) {
      setLastTranscriptLength(transcript.length);

      // Reset silence timer
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }

      // Start new silence timer (2.5 seconds)
      silenceTimerRef.current = setTimeout(() => {
        console.log('Silence detected - auto-submitting answer');
        submitAnswer();
      }, 2500);
    }
  }, [transcript, isCandidateSpeaking, listening]);

  // Cleanup VAD timer
  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, []);

  // Browser compatibility check
  if (!browserSupportsSpeechRecognition) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50">
        <div className="text-center p-8 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Browser Not Supported</h2>
          <p className="text-gray-700">
            Your browser doesn't support speech recognition.
            <br />
            Please use Chrome, Edge, or Safari.
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // SPEECH FUNCTIONS
  // ============================================================================

  const speakText = (text) => {
    const synth = window.speechSynthesis;
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.voice = selectedVoice;

    synth.speak(utterance);
  };

  // Promisified speech synthesis for sequential flow
  const speakTextAsync = (text) => {
    return new Promise((resolve) => {
      const synth = window.speechSynthesis;
      synth.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      utterance.voice = selectedVoice;

      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();

      synth.speak(utterance);
    });
  };

  // ============================================================================
  // CV UPLOAD FUNCTIONS
  // ============================================================================

  const handleFileSelect = (file) => {
    if (file && file.type === 'application/pdf') {
      setCvFile(file);
      setUploadError('');
    } else {
      setUploadError('Please select a valid PDF file');
      setCvFile(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const uploadCV = async () => {
    if (!cvFile) return;

    setCvProcessing(true);
    setUploadError('');

    const formData = new FormData();
    formData.append('cv', cvFile);

    try {
      const response = await axios.post('http://127.0.0.1:5000/oral/upload_cv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });

      if (response.data.success) {
        setCvData(response.data);
        setCvUploaded(true);
      } else {
        setUploadError(response.data.error || 'Failed to process CV');
      }
    } catch (error) {
      console.error('CV upload error:', error);
      setUploadError(error.response?.data?.error || 'Failed to upload CV');
    } finally {
      setCvProcessing(false);
    }
  };

  // ============================================================================
  // INTERVIEW FUNCTIONS
  // ============================================================================

  const startInterviewWithCountdown = async () => {
    try {
      setGeneralError('');
      setIsProcessing(true);

      // Call backend and wait for analysis
      const response = await axios.get('http://127.0.0.1:5000/oral/start', {
        withCredentials: true,
        timeout: 60000 // Increased timeout for job analysis
      });

      const data = response.data;

      if (!data.success || !data.question) {
        setGeneralError('Failed to start interview');
        setIsProcessing(false);
        return;
      }

      // Backend analysis complete - now show countdown
      setIsProcessing(false);
      setIsCountingDown(true);
      setCountdown(10);

      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            setIsCountingDown(false);
            startOralInterview(data);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (error) {
      console.error('Error starting interview:', error);
      setGeneralError(error.response?.data?.error || 'Failed to start interview');
      setIsProcessing(false);
    }
  };

  const handleSecurityAcceptAndStart = async () => {
    // Request fullscreen FIRST
    try {
      await document.documentElement.requestFullscreen();
      setShowSecurityWarning(false);
      setSecurityEnabled(true);

      // NOW call the backend
      await startInterviewWithCountdown();
    } catch (error) {
      console.error('Failed to enter fullscreen:', error);
      alert('Fullscreen is required. Please allow fullscreen access and try again.');
      setShowSecurityWarning(true); // Keep showing warning
    }
  };

  const startOralInterview = async (data) => {
    try {
      setInterviewStarted(true);
      setStartTime(Date.now());
      setCurrentTurn(data.turn);

      // AI speaks the first question
      setIsInterviewerSpeaking(true);
      await speakTextAsync(data.question);
      setIsInterviewerSpeaking(false);

      // Auto-start recording for answer
      resetTranscript();
      setLastTranscriptLength(0);
      startRecording();
    } catch (error) {
      console.error('Error in oral interview:', error);
      setGeneralError('Failed to start oral interview');
    }
  };

  const startRecording = async () => {
    setIsCandidateSpeaking(true);
    SpeechRecognition.startListening({ continuous: true, language: 'en-US' });

    // Start audio recording using MediaRecorder
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000
      });

      const chunks = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const timestamp = new Date().toISOString();

        // Upload audio file to backend
        await uploadAudioFile(audioBlob, currentTurn, timestamp);

        // Release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      setAudioChunks(chunks);
      setMediaRecorder(recorder);
      recorder.start();
    } catch (error) {
      console.error('Error starting audio recording:', error);
      setGeneralError('Microphone access denied. Please allow microphone permissions.');
      // Continue with speech recognition even if audio recording fails
    }
  };

  const submitAnswer = async () => {
    // Stop recording
    setIsCandidateSpeaking(false);
    SpeechRecognition.stopListening();

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }

    if (!transcript.trim()) {
      console.error('No transcript to submit');
      // Restart recording if no speech detected
      resetTranscript();
      setLastTranscriptLength(0);
      startRecording();
      return;
    }

    // Clear silence timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    try {
      setIsProcessing(true);

      // Submit to backend
      const response = await axios.post('http://127.0.0.1:5000/oral/continue', {
        response: transcript
      }, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });

      const data = response.data;

      if (data.complete) {
        // Interview is complete
        setInterviewComplete(true);
        await speakTextAsync(data.message || "Thank you for your time!");

        // Save final conversation
        const completeResponse = await axios.post('http://127.0.0.1:5000/oral/complete', {}, {
          withCredentials: true
        });

        // Extract filename from response and trigger evaluation
        if (completeResponse.data.filepath) {
          const filename = completeResponse.data.filepath.split(/[/\\]/).pop();
          setInterviewFilename(filename);
          console.log('Interview saved:', filename);

          // Trigger evaluation automatically
          triggerEvaluation(filename);
        }

        return;
      }

      // Get next question
      setCurrentTurn(data.turn);

      // AI speaks the question
      setIsInterviewerSpeaking(true);
      await speakTextAsync(data.question);
      setIsInterviewerSpeaking(false);

      // Auto-start recording for next answer
      resetTranscript();
      setLastTranscriptLength(0);
      startRecording();

    } catch (error) {
      console.error('Error submitting answer:', error);
      setGeneralError(error.response?.data?.error || 'Failed to submit answer');
    } finally {
      setIsProcessing(false);
    }
  };

  const uploadAudioFile = async (audioBlob, turn, timestamp) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('turn', turn);
    formData.append('timestamp', timestamp.replace(/:/g, '-').split('.')[0]);

    try {
      const response = await axios.post(
        'http://127.0.0.1:5000/oral/upload_audio',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          withCredentials: true
        }
      );
      console.log('Audio uploaded:', response.data.filename);
    } catch (error) {
      console.error('Error uploading audio:', error);
    }
  };

  const pauseInterview = () => {
    // Emergency pause
    setIsCandidateSpeaking(false);
    SpeechRecognition.stopListening();

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
  };

  const triggerEvaluation = async (filename) => {
    try {
      // Stop security monitoring when evaluation starts
      if (securityMonitorRef.current && securityMonitorRef.current.stopSecurity) {
        securityMonitorRef.current.stopSecurity();
        console.log('Security monitoring stopped - evaluation starting');
      }

      setIsEvaluating(true);
      setEvaluationError('');

      console.log('Starting evaluation for:', filename);

      const response = await axios.post(
        'http://127.0.0.1:5000/oral/evaluate',
        { interview_filename: filename },
        {
          withCredentials: true,
          headers: { 'Content-Type': 'application/json' },
          timeout: 300000 // 5 minute timeout for evaluation
        }
      );

      if (response.data.success) {
        setEvaluationData(response.data.report);
        console.log('Evaluation completed:', response.data.overall_score);
      } else {
        setEvaluationError('Evaluation failed');
      }
    } catch (error) {
      console.error('Evaluation error:', error);
      setEvaluationError(error.response?.data?.error || 'Failed to evaluate interview');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleSecurityWarning = (details) => {
    console.log('Security warning (1st violation):', details);
    // Just log the warning, interview continues
  };

  const handleSecurityViolation = async (details) => {
    console.log('Security violation detected (2nd violation - disqualification):', details);
    setSecurityViolation(details);
    setInterviewComplete(true);
    setInterviewStarted(false);

    // Stop media recording if active
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }

    // Release microphone
    if (mediaRecorder && mediaRecorder.stream) {
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }

    // Stop speech recognition if active
    if (listening) {
      SpeechRecognition.stopListening();
    }

    // Save partial responses
    try {
      const partialData = {
        current_turn: currentTurn,
        violation_details: details,
        disqualified: true,
        incomplete: true,
        timestamp: new Date().toISOString()
      };

      await axios.post('http://127.0.0.1:5000/oral/complete', partialData, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('Partial responses saved due to violation');
    } catch (error) {
      console.error('Failed to save partial responses:', error);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 min-h-screen flex flex-col items-center justify-center p-6">

      {/* Back Button - Hidden during interview */}
      {onBack && !interviewStarted && (
        <button
          onClick={onBack}
          style={{
            position: 'fixed',
            top: '20px',
            left: '20px',
            padding: '10px 20px',
            background: '#764ba2',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            zIndex: 1000,
            fontSize: '14px',
            fontWeight: 'bold',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#5f3c85'
            e.target.style.transform = 'translateY(-2px)'
            e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#764ba2'
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)'
          }}
        >
          ← Back to Menu
        </button>
      )}

      {/* Error Display */}
      {generalError && (
        <div className="w-full max-w-lg mx-auto mb-6">
          <div className="p-4 rounded-lg border bg-red-100 border-red-400 text-red-700">
            <div className="flex items-center">
              <div className="flex-shrink-0">⚠️</div>
              <div className="ml-3">
                <h3 className="text-sm font-medium">Error</h3>
                <div className="mt-1 text-sm">{generalError}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CV Upload Section */}
      {!cvUploaded && (
        <div className="w-full max-w-lg mx-auto">
          <h1 className="text-center text-4xl font-bold text-gray-800 mb-2">
            🎤 Oral Interview System
          </h1>
          <p className="text-center text-gray-600 mb-8">
            Natural voice-to-voice technical interviews
          </p>
          <h2 className="text-center text-xl font-semibold text-blue-600 mb-4">
            Step 1: Upload Your CV (PDF)
          </h2>

          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {cvFile ? (
              <div>
                <p className="text-green-600 font-medium">✅ Selected: {cvFile.name}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Size: {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-700">
                  📄 Drag and drop your CV here, or click to browse
                </p>
                <p className="text-sm text-gray-500 mt-2">PDF files only</p>
              </div>
            )}

            <input
              type="file"
              accept=".pdf"
              onChange={(e) => handleFileSelect(e.target.files[0])}
              className="hidden"
              id="cv-upload"
            />
            <label
              htmlFor="cv-upload"
              className="mt-4 inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 cursor-pointer transition"
            >
              Browse Files
            </label>
          </div>

          {cvFile && (
            <div className="mt-4 text-center">
              <button
                onClick={uploadCV}
                disabled={cvProcessing}
                className={`px-8 py-3 rounded font-medium transition ${
                  cvProcessing
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                } text-white`}
              >
                {cvProcessing ? '⏳ Processing CV...' : '🚀 Upload and Process CV'}
              </button>
            </div>
          )}

          {uploadError && (
            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {uploadError}
            </div>
          )}
        </div>
      )}

      {/* CV Processing Success + Voice Selection */}
      {cvUploaded && !interviewStarted && !isCountingDown && (
        <div className="w-full max-w-md mx-auto">
          <div className="bg-green-100 border border-green-400 text-green-700 p-4 rounded mb-6">
            <h3 className="font-bold">✅ CV Processed Successfully!</h3>
            <div className="mt-2 text-sm">
              <p>• Work Experiences: {cvData?.experiences_count || 0}</p>
              <p>• Skills: {cvData?.skills_count || 0}</p>
              <p>• Education: {cvData?.education_count || 0}</p>
            </div>
          </div>

          <h2 className="text-xl font-semibold text-purple-600 mb-4 text-center">
            Step 2: Select Interview Voice
          </h2>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Choose AI Interviewer Voice:
            </label>
            <select
              value={selectedVoice?.name || ''}
              onChange={(e) => {
                const voice = availableVoices.find(v => v.name === e.target.value);
                setSelectedVoice(voice);
              }}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">Select a voice...</option>
              {availableVoices
                .filter(voice => voice.lang.startsWith('en'))
                .map(voice => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
            </select>

            <button
              onClick={() => setShowSecurityWarning(true)}
              disabled={!selectedVoice || isProcessing || isCountingDown}
              className={`mt-6 w-full px-8 py-4 rounded-lg font-semibold transition ${
                !selectedVoice || isProcessing || isCountingDown
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-700'
              } text-white text-lg`}
            >
              {isProcessing ? '🔍 Analyzing your profile and job requirements...' : '🎤 Start Oral Interview'}
            </button>
          </div>
        </div>
      )}

      {/* Security Warning Modal - Shows BEFORE interview starts */}
      {showSecurityWarning && !interviewStarted && (
        <WarningModal
          onAccept={handleSecurityAcceptAndStart}
          interviewType="oral"
        />
      )}

      {/* Countdown Display & Interview - Wrapped with SecurityMonitor */}
      {(isCountingDown || (interviewStarted && !interviewComplete)) && (
        <SecurityMonitor
          ref={securityMonitorRef}
          enabled={securityEnabled}
          onViolation={handleSecurityViolation}
          onWarning={handleSecurityWarning}
          interviewType="oral"
        >
          {/* Countdown Display */}
          {isCountingDown && (
            <div className="w-full max-w-2xl">
              <div className="bg-white rounded-2xl shadow-2xl p-12 text-center border border-gray-200">
                <h2 className="text-3xl font-bold text-gray-800 mb-8">Starting Oral Interview</h2>

            {/* Circular Countdown */}
            <div className="relative inline-flex items-center justify-center mb-8">
              <svg className="w-48 h-48 transform -rotate-90">
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="#e5e7eb"
                  strokeWidth="12"
                  fill="none"
                />
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke="#764ba2"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 88}`}
                  strokeDashoffset={`${2 * Math.PI * 88 * (1 - countdown / 10)}`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-linear"
                />
              </svg>
              <div className="absolute text-6xl font-bold text-purple-600">
                {countdown}
              </div>
            </div>

            <p className="text-xl text-gray-600">
              Starting in <span className="font-bold text-purple-600">{countdown}</span> second{countdown !== 1 ? 's' : ''}...
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Prepare yourself for the interview
            </p>
          </div>
        </div>
      )}

          {/* Interview Status Display - MINIMAL UI */}
          {!isCountingDown && interviewStarted && !interviewComplete && (
          <div className="w-full max-w-2xl">
          <div className="bg-white rounded-2xl shadow-2xl p-12 text-center">

            {/* Status Indicator */}
            <div className="mb-8">
              {isInterviewerSpeaking && (
                <div className="text-6xl mb-4 animate-pulse">🔊</div>
              )}
              {isCandidateSpeaking && (
                <div className="text-6xl mb-4 animate-pulse">🎤</div>
              )}
              {isProcessing && (
                <div className="text-6xl mb-4 animate-spin">⚙️</div>
              )}
            </div>

            {/* Status Text */}
            <div className="text-3xl font-semibold text-gray-800 mb-6">
              {isInterviewerSpeaking && "🎙️ Interviewer speaking..."}
              {isCandidateSpeaking && "💬 Your turn to speak..."}
              {isProcessing && "🔄 Processing your response..."}
            </div>

            {/* Progress */}
            <div className="text-lg text-gray-500">
              Turn: {currentTurn} | Duration: {startTime ? Math.floor((Date.now() - startTime) / 60000) : 0} min
            </div>
          </div>
        </div>
          )}
        </SecurityMonitor>
      )}

      {/* Evaluating Banner */}
      {isEvaluating && interviewComplete && (() => {
        // Estimate: ~13 seconds per Q&A pair + 5 seconds for summary
        const estimatedSeconds = (currentTurn * 13) + 5;
        const estimatedMinutes = Math.ceil(estimatedSeconds / 60);

        return (
          <div className="w-full max-w-2xl">
            <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl shadow-2xl p-12 text-center border border-gray-200">
              <div className="text-6xl mb-4 animate-bounce">🔍</div>
              <h2 className="text-3xl font-bold text-white mb-4">
                Evaluating Your Oral Interview Performance...
              </h2>
              <div className="flex justify-center items-center space-x-2 mb-4">
                <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0s' }}></div>
                <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
              <p className="text-white text-lg">
                Analyzing your responses, technical vocabulary, coherence, and communication clarity...
                <br />
                <span className="font-semibold mt-2 block">
                  Estimated time: ~{estimatedMinutes} minute{estimatedMinutes !== 1 ? 's' : ''}
                </span>
              </p>
              <p className="text-purple-100 text-sm mt-2">
                Please wait while we process {currentTurn} Q&A pair{currentTurn !== 1 ? 's' : ''}...
              </p>
            </div>
          </div>
        );
      })()}

      {/* Evaluation Results Display */}
      {evaluationData && interviewComplete && !isEvaluating && !securityViolation && (
        <div className="mt-6 w-full max-w-5xl space-y-6">
          {/* Overall Score Card */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl shadow-2xl p-8 border border-gray-200">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-6">
              📊 Your Oral Interview Evaluation
            </h2>

            {/* Circular Score Display */}
            <div className="flex flex-col items-center mb-6">
              <div className="relative inline-flex items-center justify-center mb-4">
                <svg className="w-48 h-48 transform -rotate-90">
                  <circle cx="96" cy="96" r="88" stroke="#e5e7eb" strokeWidth="12" fill="none" />
                  <circle
                    cx="96" cy="96" r="88"
                    stroke={evaluationData.overall_score >= 7 ? "#10b981" : evaluationData.overall_score >= 5 ? "#f59e0b" : "#ef4444"}
                    strokeWidth="12" fill="none"
                    strokeDasharray={`${2 * Math.PI * 88}`}
                    strokeDashoffset={`${2 * Math.PI * 88 * (1 - evaluationData.overall_score / 10)}`}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute text-center">
                  <div className={`text-5xl font-bold ${evaluationData.overall_score >= 7 ? 'text-green-600' : evaluationData.overall_score >= 5 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {evaluationData.overall_score}
                  </div>
                  <div className="text-gray-500 text-sm">out of 10</div>
                </div>
              </div>

              {/* Evaluation Summary */}
              <div className="bg-white rounded-lg p-6 shadow-md max-w-2xl">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Summary</h3>
                <p className="text-gray-700 leading-relaxed">
                  {evaluationData.evaluation_summary}
                </p>
              </div>

              {/* Metadata */}
              <div className="mt-4 text-center text-sm text-gray-600">
                <p>Duration: {evaluationData.duration_minutes} minutes | Total Questions: {evaluationData.total_turns} | Difficulty: {evaluationData.difficulty_score}/10</p>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="bg-white rounded-lg p-6 shadow-md space-y-4">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Score Breakdown</h3>

              {/* Technical Vocabulary */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Technical Vocabulary (30% weight)</span>
                  <span className="text-gray-900 font-bold">{evaluationData.technical_vocab_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.technical_vocab_score >= 7 ? 'bg-green-500' : evaluationData.technical_vocab_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.technical_vocab_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Coherence */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Coherence & Completeness (30% weight)</span>
                  <span className="text-gray-900 font-bold">{evaluationData.coherence_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.coherence_score >= 7 ? 'bg-green-500' : evaluationData.coherence_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.coherence_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Relevance */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Answer Relevance (25% weight)</span>
                  <span className="text-gray-900 font-bold">{evaluationData.relevance_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.relevance_score >= 7 ? 'bg-green-500' : evaluationData.relevance_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.relevance_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Clarity */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Clarity & Expression (15% weight)</span>
                  <span className="text-gray-900 font-bold">{evaluationData.clarity_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.clarity_score >= 7 ? 'bg-green-500' : evaluationData.clarity_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.clarity_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Question Feedback */}
          {evaluationData.question_evaluations && evaluationData.question_evaluations.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">💬 Detailed Feedback per Question</h3>
              <div className="space-y-4">
                {evaluationData.question_evaluations.map((qeval, index) => {
                  const isExpanded = expandedFeedback[qeval.turn];

                  return (
                    <div key={qeval.turn} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-purple-50 p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <span className="text-sm font-semibold text-purple-600">Turn {qeval.turn}</span>
                            <p className="text-gray-800 font-medium mt-1">{qeval.question}</p>
                          </div>
                          <div className="ml-4 flex flex-col items-end space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Tech:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${qeval.technical_vocab_score >= 7 ? 'bg-green-100 text-green-800' : qeval.technical_vocab_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {qeval.technical_vocab_score}/10
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Coherence:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${qeval.coherence_score >= 7 ? 'bg-green-100 text-green-800' : qeval.coherence_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {qeval.coherence_score}/10
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Relevance:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${qeval.relevance_score >= 7 ? 'bg-green-100 text-green-800' : qeval.relevance_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {qeval.relevance_score}/10
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Clarity:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${qeval.clarity_score >= 7 ? 'bg-green-100 text-green-800' : qeval.clarity_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {qeval.clarity_score}/10
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-white">
                        <div className="mb-3">
                          <span className="text-sm font-semibold text-gray-700">Your Response:</span>
                          <p className="text-gray-600 mt-1 italic">{qeval.response}</p>
                          <div className="text-xs text-gray-500 mt-1">
                            {qeval.word_count} words, {qeval.sentence_count} sentences
                            {qeval.audio_file && <span className="ml-2">🎤 {qeval.audio_file}</span>}
                          </div>
                        </div>

                        <button
                          onClick={() => setExpandedFeedback(prev => ({ ...prev, [qeval.turn]: !prev[qeval.turn] }))}
                          className="flex items-center space-x-2 text-purple-600 hover:text-purple-800 font-medium transition"
                        >
                          <span>{isExpanded ? '▼' : '▶'}</span>
                          <span>{isExpanded ? 'Hide Feedback' : 'Show Detailed Feedback'}</span>
                        </button>

                        {isExpanded && (
                          <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                            <p className="text-gray-800 leading-relaxed">{qeval.feedback}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => {
                const dataStr = JSON.stringify(evaluationData, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `oral-evaluation-${evaluationData.candidate_name}-${evaluationData.interview_date}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium shadow-md"
            >
              💾 Download Evaluation Report
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium shadow-md"
            >
              🔄 Start New Interview
            </button>
          </div>
        </div>
      )}

      {/* Evaluation Error */}
      {evaluationError && interviewComplete && !isEvaluating && !securityViolation && (
        <div className="w-full max-w-2xl">
          <div className="bg-red-100 border border-red-400 rounded-lg p-6">
            <h3 className="text-red-800 font-bold mb-2">❌ Evaluation Failed</h3>
            <p className="text-red-700 mb-4">{evaluationError}</p>
            <button
              onClick={() => interviewFilename && triggerEvaluation(interviewFilename)}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
            >
              🔄 Retry Evaluation
            </button>
          </div>
        </div>
      )}

      {/* Interview Complete (Legacy - shown only if no evaluation) */}
      {interviewComplete && !evaluationData && !isEvaluating && !evaluationError && !securityViolation && (
        <div className="w-full max-w-2xl text-center">
          <div className="bg-white rounded-2xl shadow-2xl p-12">
            <div className="text-8xl mb-6">🎉</div>
            <h2 className="text-4xl font-bold text-green-600 mb-4">
              Interview Complete!
            </h2>
            <p className="text-xl text-gray-600 mb-4">
              Great conversation! Your interview has been saved.
            </p>
            <div className="text-lg text-gray-500 mb-8">
              <p>Total Duration: {startTime ? Math.floor((Date.now() - startTime) / 60000) : 0} minutes</p>
              <p>Total Turns: {currentTurn}</p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-lg font-semibold"
            >
              🔄 Start New Interview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OralInterview;
