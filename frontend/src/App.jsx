import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import SecurityMonitor from './components/security/SecurityMonitor';
import WarningModal from './components/security/WarningModal';

function InterviewComponent({ onBack }) {
  // Basic interview state
  const [question, setQuestion] = useState('');
  const [questionCount, setQuestionCount] = useState(0);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [interviewLog, setInterviewLog] = useState([]);
  const [isAnswering, setIsAnswering] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState();

  // Audio recording state (parallel to speech recognition)
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [savedAudioBlobs, setSavedAudioBlobs] = useState([]);

  // Enhanced interview state (minimal)
  const [currentQuestionData, setCurrentQuestionData] = useState(null);
  const [currentPhase, setCurrentPhase] = useState('open');

  // QCM specific state
  const [qcmOptions, setQcmOptions] = useState([]);
  const [selectedQCMOption, setSelectedQCMOption] = useState('');
  const [selectedQCMOptions, setSelectedQCMOptions] = useState([]); // For multiple-choice
  const [isMultipleChoice, setIsMultipleChoice] = useState(false);

  // Editable transcript state
  const [editableTranscript, setEditableTranscript] = useState('');
  const [isWritingMode, setIsWritingMode] = useState(false);

  // Coding specific state - MOVED TO SEPARATE CODING AGENT
  // const [codingAnswer, setCodingAnswer] = useState('');

  // CV upload functionality - DEPRECATED (Job-only interview mode)
  // const [cvFile, setCvFile] = useState(null);
  // const [cvUploaded, setCvUploaded] = useState(false);
  // const [cvProcessing, setCvProcessing] = useState(false);
  // const [cvData, setCvData] = useState(null);
  // const [uploadError, setUploadError] = useState('');
  // const [dragOver, setDragOver] = useState(false);

  // Basic error handling
  const [generalError, setGeneralError] = useState('');
  const [startingInterview, setStartingInterview] = useState(false);

  // Countdown timer state
  const [countdown, setCountdown] = useState(null);
  const [isCountingDown, setIsCountingDown] = useState(false);

  // Loading state for submit
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Evaluation state
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluationData, setEvaluationData] = useState(null);
  const [expandedFeedback, setExpandedFeedback] = useState({});

  // Waveform visualization state
  const [audioLevel, setAudioLevel] = useState(0);
  const audioContextRef = React.useRef(null);
  const analyserRef = React.useRef(null);
  const animationFrameRef = React.useRef(null);

  // Security state
  const [securityEnabled, setSecurityEnabled] = useState(false);
  const [securityViolation, setSecurityViolation] = useState(null);
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);
  const securityMonitorRef = useRef(null);

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

  useEffect(() => {
    const navEntries = performance.getEntriesByType('navigation');
    const isRefresh = navEntries.length && navEntries[0].type === 'reload';

    if (isRefresh) {
      window.speechSynthesis.cancel();
      console.log('Page was refreshed — voice cancelled');
    }
  }, []);

  // Auto-download audio files when interview completes
  useEffect(() => {
    if (interviewComplete && savedAudioBlobs.length > 0) {
      // Delay to ensure state is fully settled
      setTimeout(() => {
        downloadAllAudio();
      }, 1000);
    }
  }, [interviewComplete]);

  // Audio visualization effect
  useEffect(() => {
    if (isRecording && mediaRecorder) {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      const visualize = () => {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);

        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);

        animationFrameRef.current = requestAnimationFrame(visualize);
      };

      visualize();

      return () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
      };
    } else {
      setAudioLevel(0);
    }
  }, [isRecording, mediaRecorder]);

  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } = useSpeechRecognition();

  if (!browserSupportsSpeechRecognition) {
    return <span>Browser doesn't support speech recognition.</span>;
  }

  const speakText = (text) => {
    const synth = window.speechSynthesis;
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.voice = selectedVoice;

    synth.speak(utterance);
  };

  // CV Upload Functions - DEPRECATED (Job-only interview mode)
  // const handleFileSelect = (file) => {
  //   if (file && file.type === 'application/pdf') {
  //     setCvFile(file);
  //     setUploadError('');
  //   } else {
  //     setUploadError('Please select a valid PDF file');
  //   }
  // };

  // const handleDragOver = (e) => {
  //   e.preventDefault();
  //   setDragOver(true);
  // };

  // const handleDragLeave = (e) => {
  //   e.preventDefault();
  //   setDragOver(false);
  // };

  // const handleDrop = (e) => {
  //   e.preventDefault();
  //   setDragOver(false);
  //   const files = e.dataTransfer.files;
  //   if (files.length > 0) {
  //     handleFileSelect(files[0]);
  //   }
  // };

  // const uploadCV = async () => {
  //   if (!cvFile) {
  //     setUploadError('Please select a CV file first');
  //     return;
  //   }

  //   setCvProcessing(true);
  //   setUploadError('');

  //   const formData = new FormData();
  //   formData.append('cv_file', cvFile);

  //   try {
  //     const response = await axios.post('http://127.0.0.1:5000/upload_cv', formData, {
  //       headers: {
  //         'Content-Type': 'multipart/form-data',
  //       },
  //       withCredentials: true,
  //     });

  //     if (response.status === 200) {
  //       if (response.data.cv_data) {
  //         setCvData(response.data.cv_data);
  //         setCvUploaded(true);
  //       } else {
  //         setCvData({ experiences_count: 0, education_count: 0, skills_count: 0, projects_count: 0 });
  //         setCvUploaded(true);
  //       }
  //     }
  //   } catch (error) {
  //     console.error('Error uploading CV:', error);
  //     const errorMsg = error.response?.data?.error || error.message || 'Failed to upload CV';
  //     setUploadError(`Upload Error: ${errorMsg}`);
  //   } finally {
  //     setCvProcessing(false);
  //   }
  // };

  const startInterviewWithCountdown = async () => {
    try {
      setGeneralError('');
      setStartingInterview(true);

      // Call backend and wait for analysis
      const response = await axios.get('http://127.0.0.1:5000/start_interview', {
        timeout: 60000 // Increased timeout for job analysis
      });
      const data = response.data;

      if (data.error) {
        setGeneralError(data.error);
        setStartingInterview(false);
        return;
      }

      if (data.complete) {
        setInterviewComplete(true);
        setStartingInterview(false);
        return;
      }

      // Backend analysis complete - now show countdown
      setStartingInterview(false);
      setIsCountingDown(true);
      setCountdown(10);

      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            setIsCountingDown(false);
            displayQuestion(data);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (error) {
      console.error('Error starting interview:', error);
      setGeneralError(`Error starting interview: ${error.message}`);
      setStartingInterview(false);
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

  const displayQuestion = (data) => {
    // Handle current backend structure
    setCurrentQuestionData(data);
    setCurrentPhase(data.phase || 'open');
    setQuestionCount(data.question_count || 1);

    // Handle different question types
    if (data.question_type === 'open') {
      setQuestion(data.question);
      speakText(data.question);
    } else if (data.question_type === 'qcm') {
      setQuestion(data.question);
      setQcmOptions(data.options || []);
      setIsMultipleChoice(data.is_multiple_choice || false);
      setSelectedQCMOption('');
      setSelectedQCMOptions([]);
      speakText(data.question);
    }

    setInterviewStarted(true);
  };

  const startRecording = async () => {
    setEditableTranscript('');   // Clear any previous text
    setIsWritingMode(false);     // Exit writing mode
    setIsAnswering(true);
    setIsRecording(true);
    SpeechRecognition.startListening({ continuous: true, language: 'en-US' });

    // Parallel audio recording using MediaRecorder
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

      recorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const timestamp = new Date().toISOString();
        setSavedAudioBlobs((prev) => [
          ...prev,
          { questionNumber: questionCount, blob: audioBlob, timestamp }
        ]);

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      setAudioChunks(chunks);
      setMediaRecorder(recorder);
      recorder.start();
    } catch (error) {
      console.error('Error starting audio recording:', error);
      // Continue with speech recognition even if audio recording fails
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setIsAnswering(false);
    SpeechRecognition.stopListening();

    // Copy transcript to editable version
    setEditableTranscript(transcript);

    // Stop parallel audio recording
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
  };

  const startWritingMode = () => {
    setIsWritingMode(true);
    setEditableTranscript('');  // Start with empty text
    setIsAnswering(false);      // Not submitting yet
  };

  const recordAnswer = async () => {
    try {
      setIsAnswering(true);
      setIsSubmitting(true);

      // Get the appropriate response based on question type
      let responseData = { response: editableTranscript };

      if (currentQuestionData?.question_type === 'qcm') {
        if (isMultipleChoice) {
          responseData.qcm_selected_multiple = selectedQCMOptions;
          responseData.response = `Selected options ${selectedQCMOptions.join(', ')}`;
        } else {
          responseData.qcm_selected = selectedQCMOption;
          responseData.response = `Selected option ${selectedQCMOption}`;
        }
      // CODING QUESTIONS MOVED TO SEPARATE AGENT
      // } else if (currentQuestionData?.question_type === 'coding' ||
      //            currentQuestionData?.question_type === 'coding_debug' ||
      //            currentQuestionData?.question_type === 'coding_explain') {
      //   responseData.response = codingAnswer || transcript;
      } else {
        if (!editableTranscript) {
          console.error('No answer text available.');
          return;
        }
        responseData.response = editableTranscript;
      }

      console.log('Submitting response:', responseData);

      const submitRes = await axios.post('http://127.0.0.1:5000/submit_response', responseData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = submitRes.data;

      // Save current Q&A to log
      const logEntry = {
        question: question,
        answer: responseData.response,
        question_type: currentQuestionData?.question_type || 'open',
        phase: currentPhase
      };
      setInterviewLog((prev) => [...prev, logEntry]);

      if (data.complete) {
        // Stop security monitoring when interview is complete
        if (securityMonitorRef.current && securityMonitorRef.current.stopSecurity) {
          securityMonitorRef.current.stopSecurity();
          console.log('Security monitoring stopped - interview complete');
        }

        // Check if evaluation data is included
        if (data.evaluation) {
          setEvaluationData(data.evaluation);
          setIsEvaluating(false);
        } else {
          // Evaluation is still processing
          setIsEvaluating(true);
        }
        setInterviewComplete(true);
        setQuestion('');
      } else {
        // Handle new question data
        setCurrentQuestionData(data);
        setCurrentPhase(data.phase || currentPhase);
        setQuestionCount(data.question_count || questionCount + 1);

        // Handle different question types
        if (data.question_type === 'open') {
          setQuestion(data.question);
          speakText(data.question);
        } else if (data.question_type === 'qcm') {
          setQuestion(data.question);
          setQcmOptions(data.options || []);
          setIsMultipleChoice(data.is_multiple_choice || false);
          setSelectedQCMOption('');
          setSelectedQCMOptions([]);
          speakText(data.question);
        // CODING QUESTIONS MOVED TO SEPARATE AGENT
        // } else if (data.question_type === 'coding' ||
        //            data.question_type === 'coding_debug' ||
        //            data.question_type === 'coding_explain') {
        //   setQuestion(data.title || data.question);
        //   setCodingAnswer('');
        //   if (data.question_type === 'coding_debug') {
        //     speakText(`Debug Challenge: ${data.title || data.question}`);
        //   } else if (data.question_type === 'coding_explain') {
        //     speakText(`Code Analysis: ${data.title || data.question}`);
        //   } else {
        //     speakText(`Coding Challenge: ${data.title || data.question}`);
        //   }
        }
      }

      resetTranscript();
      setEditableTranscript('');    // Clear edited text
      setIsWritingMode(false);      // Exit writing mode
    } catch (error) {
      console.error('Error during answer submission:', error);
      setGeneralError(`Error submitting response: ${error.message}`);
    } finally {
      setIsAnswering(false);
      setIsSubmitting(false);
    }
  };

  const getPhaseDisplayName = (phase) => {
    switch (phase) {
      case 'open': return 'Open Questions';
      case 'qcm': return 'Multiple Choice';
      // case 'coding': return 'Coding Challenge';  // MOVED TO SEPARATE AGENT
      default: return 'Interview';
    }
  };

  const canSubmitAnswer = () => {
    if (currentQuestionData?.question_type === 'qcm') {
      if (isMultipleChoice) {
        return selectedQCMOptions.length > 0;
      } else {
        return selectedQCMOption !== '';
      }
    }
    // CODING QUESTIONS MOVED TO SEPARATE AGENT
    // if (currentQuestionData?.question_type === 'coding' ||
    //     currentQuestionData?.question_type === 'coding_debug' ||
    //     currentQuestionData?.question_type === 'coding_explain') {
    //   return codingAnswer.trim() !== '';
    // }
    return editableTranscript.trim() !== '';
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

    // Save partial responses
    try {
      const partialData = {
        interview_log: interviewLog,
        question_count: questionCount,
        violation_details: details,
        disqualified: true,
        incomplete: true,
        timestamp: new Date().toISOString()
      };

      await axios.post('http://127.0.0.1:5000/record', partialData, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('Partial responses saved due to violation');
    } catch (error) {
      console.error('Failed to save partial responses:', error);
    }
  };

  // Handler for multiple-choice checkbox toggle
  const handleMultipleChoiceToggle = (optionLetter) => {
    setSelectedQCMOptions((prev) => {
      if (prev.includes(optionLetter)) {
        return prev.filter(opt => opt !== optionLetter);
      } else {
        return [...prev, optionLetter];
      }
    });
  };

  const downloadAllAudio = () => {
    if (savedAudioBlobs.length === 0) {
      console.log('No audio recordings to download');
      return;
    }

    console.log(`Downloading ${savedAudioBlobs.length} audio recordings...`);

    savedAudioBlobs.forEach((audioData, index) => {
      const url = URL.createObjectURL(audioData.blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;

      // Format filename: interview_q1_2025-01-15T10-30-45.webm
      const formattedTimestamp = audioData.timestamp.replace(/:/g, '-').split('.')[0];
      a.download = `interview_q${audioData.questionNumber}_${formattedTimestamp}.webm`;

      document.body.appendChild(a);

      // Stagger downloads to avoid browser blocking
      setTimeout(() => {
        a.click();
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, index * 500); // 500ms delay between each download
    });
  };

  return (
    <div className="bg-gray-50 min-h-screen flex flex-col items-center justify-center p-6 space-y-6 relative">

      {/* Back Button - Hidden during interview */}
      {onBack && !interviewStarted && (
        <button
          onClick={onBack}
          style={{
            position: 'fixed',
            top: '20px',
            left: '20px',
            padding: '10px 20px',
            background: '#2563eb',
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
            e.target.style.background = '#1d4ed8'
            e.target.style.transform = 'translateY(-2px)'
            e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#2563eb'
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)'
          }}
        >
          ← Back to Menu
        </button>
      )}

      {/* Error Display */}
      {generalError && (
        <div className="w-full max-w-lg mx-auto">
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

      {/* CV Upload Section - DEPRECATED (Job-only interview mode) */}
      {/* {!cvUploaded && (
        <div className="w-full max-w-lg mx-auto">
          <h1 className="text-center text-3xl font-bold text-gray-800 mb-6">
            AI Interview Assistant
          </h1>
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
                <p className="text-green-600 font-medium">Selected: {cvFile.name}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Size: {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-700">
                  Drag and drop your CV here, or click to browse
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
                {cvProcessing ? 'Processing CV...' : 'Upload and Process CV'}
              </button>
            </div>
          )}

          {uploadError && (
            <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {uploadError}
            </div>
          )}
        </div>
      )} */}

      {/* CV Processing Success - DEPRECATED (Job-only interview mode) */}
      {/* {cvUploaded && cvData && !isCountingDown && (
        <div className="w-full max-w-lg mx-auto">
          <div className="bg-green-100 border border-green-400 text-green-700 p-4 rounded mb-6">
            <h3 className="font-bold">✅ CV Processed Successfully!</h3>
            <div className="mt-2 text-sm">
              <p>• Work Experiences: {cvData.experiences_count}</p>
              <p>• Education Records: {cvData.education_count}</p>
              <p>• Skills Identified: {cvData.skills_count}</p>
              <p>• Projects Found: {cvData.projects_count}</p>
            </div>
          </div>
        </div>
      )} */}

      {/* Welcome Message & Voice Selection */}
      {!interviewStarted && !interviewComplete && !isCountingDown && (
        <div className="w-full max-w-lg mx-auto space-y-6">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">
              AI Interview Assistant
            </h1>
            <p className="text-gray-600 text-lg">
              Job-based interview powered by AI
            </p>
          </div>

          <div className="w-full max-w-md mx-auto">
            <h2 className="text-center text-xl font-semibold text-blue-600 mb-2">
              Step 1: Select Interview Voice
            </h2>
            <select
              onChange={(e) => {
                const selected = availableVoices.find(v => v.name === e.target.value);
                setSelectedVoice(selected);
              }}
              className="w-full p-3 rounded-lg border border-gray-300 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              {availableVoices.map((voice, idx) => (
                <option key={idx} value={voice.name}>
                  {voice.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Start Interview Button */}
      {!interviewStarted && !interviewComplete && !isCountingDown && (
        <div className="text-center">
          <h2 className="text-xl font-semibold text-green-600 mb-4">
            Step 2: Begin Interview
          </h2>
          <button
            onClick={() => setShowSecurityWarning(true)}
            disabled={startingInterview}
            className={`px-8 py-4 rounded-lg transition text-lg font-medium ${
              startingInterview
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            } text-white shadow-md`}
          >
            {startingInterview ? '🔍 Analyzing job requirements...' : '🎤 Start AI Interview'}
          </button>
        </div>
      )}

      {/* Security Warning Modal - Shows BEFORE interview starts */}
      {showSecurityWarning && !interviewStarted && (
        <WarningModal
          onAccept={handleSecurityAcceptAndStart}
          interviewType="text"
        />
      )}

      {/* Countdown Display & Interview - Wrapped with SecurityMonitor */}
      {(isCountingDown || (interviewStarted && !interviewComplete)) && (
        <SecurityMonitor
          ref={securityMonitorRef}
          enabled={securityEnabled}
          onViolation={handleSecurityViolation}
          onWarning={handleSecurityWarning}
          interviewType="text"
        >
          {/* Countdown Display */}
          {isCountingDown && (
            <div className="w-full max-w-2xl">
              <div className="bg-white rounded-2xl shadow-2xl p-12 text-center border border-gray-200">
                <h2 className="text-3xl font-bold text-gray-800 mb-8">Starting Interview</h2>

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
                  stroke="#2563eb"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 88}`}
                  strokeDashoffset={`${2 * Math.PI * 88 * (1 - countdown / 10)}`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-linear"
                />
              </svg>
              <div className="absolute text-6xl font-bold text-blue-600">
                {countdown}
              </div>
            </div>

            <p className="text-xl text-gray-600">
              Starting in <span className="font-bold text-blue-600">{countdown}</span> second{countdown !== 1 ? 's' : ''}...
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Prepare yourself for the interview
            </p>
          </div>
        </div>
      )}

          {/* Question Display */}
          {!isCountingDown && interviewStarted && !interviewComplete && question && currentQuestionData && (
            <div className="w-full max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Question {questionCount} - {getPhaseDisplayName(currentPhase)}
              </h3>
              <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                {currentQuestionData.question_type?.toUpperCase()}
              </span>
            </div>

            {/* Open Question Display */}
            {currentQuestionData.question_type === 'open' && (
              <div>
                <p className="text-gray-800 text-lg mb-4">{question}</p>
              </div>
            )}

            {/* QCM Question Display */}
            {currentQuestionData.question_type === 'qcm' && (
              <div>
                <p className="text-gray-800 text-lg mb-4">{question}</p>

                {/* Instruction text */}
                <div className="mb-3">
                  {isMultipleChoice ? (
                    <p className="text-sm font-semibold text-blue-600 bg-blue-50 px-3 py-2 rounded">
                      ✓ Select ALL correct answers (Multiple-choice)
                    </p>
                  ) : (
                    <p className="text-sm font-semibold text-green-600 bg-green-50 px-3 py-2 rounded">
                      ○ Select ONE correct answer (Single-choice)
                    </p>
                  )}
                </div>

                <div className="space-y-3">
                  {qcmOptions.map((option) => (
                    <label
                      key={option.option}
                      className={`flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer ${
                        isMultipleChoice && selectedQCMOptions.includes(option.option) ? 'bg-blue-50 border-blue-300' :
                        !isMultipleChoice && selectedQCMOption === option.option ? 'bg-green-50 border-green-300' :
                        'border-gray-300'
                      }`}
                    >
                      <input
                        type={isMultipleChoice ? "checkbox" : "radio"}
                        name={isMultipleChoice ? undefined : "qcm-answer"}
                        value={option.option}
                        checked={isMultipleChoice ? selectedQCMOptions.includes(option.option) : selectedQCMOption === option.option}
                        onChange={(e) => {
                          if (isMultipleChoice) {
                            handleMultipleChoiceToggle(option.option);
                          } else {
                            setSelectedQCMOption(e.target.value);
                          }
                        }}
                        className={`mr-3 ${isMultipleChoice ? 'text-blue-600 focus:ring-blue-500' : 'text-green-600 focus:ring-green-500'}`}
                      />
                      <div>
                        <span className="font-medium text-gray-700">{option.option})</span>
                        <span className="ml-2 text-gray-800">{option.text}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* CODING QUESTION DISPLAY - MOVED TO SEPARATE AGENT */}
            {/* {(currentQuestionData.question_type === 'coding' ||
              currentQuestionData.question_type === 'coding_debug' ||
              currentQuestionData.question_type === 'coding_explain') && (
              <div>
                <h4 className="text-xl font-bold text-gray-800 mb-3">{question}</h4>
                {currentQuestionData.description && (
                  <p className="text-gray-700 mb-4">{currentQuestionData.description}</p>
                )}

                {/* Debug Specific */}
                {/* {currentQuestionData.question_type === 'coding_debug' && currentQuestionData.buggy_code && (
                  <div className="mb-4">
                    <strong className="text-gray-800">Buggy Code:</strong>
                    <pre className="bg-red-50 border border-red-200 text-red-900 p-3 rounded mt-2 overflow-x-auto text-sm">
                      {currentQuestionData.buggy_code}
                    </pre>
                  </div>
                )} */}

                {/* Explanation Specific */}
                {/* {currentQuestionData.question_type === 'coding_explain' && currentQuestionData.working_code && (
                  <div className="mb-4">
                    <strong className="text-gray-800">Code to Analyze:</strong>
                    <pre className="bg-blue-50 border border-blue-200 text-blue-900 p-3 rounded mt-2 overflow-x-auto text-sm">
                      {currentQuestionData.working_code}
                    </pre>
                  </div>
                )} */}

                {/* <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your {currentQuestionData.question_type === 'coding_debug' ? 'Fixed Code' :
                           currentQuestionData.question_type === 'coding_explain' ? 'Analysis' : 'Solution'}:
                  </label>
                  <textarea
                    value={codingAnswer}
                    onChange={(e) => setCodingAnswer(e.target.value)}
                    className="w-full h-40 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={currentQuestionData.question_type === 'coding_debug' ? 'Paste the corrected code here...' :
                                currentQuestionData.question_type === 'coding_explain' ? 'Analyze the code and explain...' :
                                'Write your code solution here...'}
                  />
                </div> */}
              {/* </div>
            )} */}
          </div>
        </div>
      )}

      {/* Control Buttons */}
      {question && !interviewComplete && (
        <div className="w-full max-w-lg mx-auto">
          {/* Recording Controls for Open Questions */}
          {currentQuestionData?.question_type === 'open' && (
            <div className="text-center space-y-4">
              {!isRecording && !isAnswering && !editableTranscript && !isWritingMode && (
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={startRecording}
                    className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition text-lg font-medium"
                  >
                    🎤 Start Recording Answer
                  </button>
                  <button
                    onClick={startWritingMode}
                    className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition text-lg font-medium"
                  >
                    ✍️ Write Answer
                  </button>
                </div>
              )}

              {isRecording && (
                <div className="space-y-4">
                  <div className="text-lg text-green-600 font-medium animate-pulse">
                    🔴 Recording... Please speak your answer
                  </div>

                  {/* Waveform Visualization */}
                  <div className="mb-4 flex justify-center items-end gap-1 h-20 bg-gray-50 rounded-lg p-4">
                    {[...Array(20)].map((_, i) => (
                      <div
                        key={i}
                        className="bg-green-500 w-2 rounded-full transition-all duration-100"
                        style={{
                          height: `${Math.max(10, (audioLevel / 255) * 60 * (0.5 + Math.random()))}px`,
                        }}
                      />
                    ))}
                  </div>

                  <div className="text-sm text-gray-600">
                    🎧 Audio is being saved automatically
                  </div>
                  <button
                    onClick={stopRecording}
                    className="bg-red-600 text-white px-8 py-3 rounded-lg hover:bg-red-700 transition text-lg font-medium shadow-md"
                  >
                    ⏹️ Stop Recording
                  </button>
                </div>
              )}

              {(editableTranscript || isWritingMode || isSubmitting) && !isRecording && (
                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg border border-gray-300">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {isWritingMode ? '✍️ Write Your Answer:' : '✏️ Review & Edit Your Response:'}
                    </label>
                    <textarea
                      value={editableTranscript}
                      onChange={(e) => setEditableTranscript(e.target.value)}
                      className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
                      placeholder={isWritingMode ? 'Type your answer here...' : 'Edit your transcribed answer if needed...'}
                    />
                    <div className="text-sm text-gray-500 mt-1">
                      {editableTranscript.length} characters
                    </div>
                  </div>
                  <button
                    onClick={recordAnswer}
                    disabled={!editableTranscript.trim() || isSubmitting}
                    className={`px-8 py-3 rounded-lg text-lg font-medium transition shadow-md ${
                      editableTranscript.trim() && !isSubmitting
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-gray-400 text-gray-100 cursor-not-allowed'
                    }`}
                  >
                    {isSubmitting ? '⏳ Submitting Your Answer...' : '✅ Submit Answer'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* QCM Controls */}
          {currentQuestionData?.question_type === 'qcm' && (
            <div className="text-center space-y-2">
              {isMultipleChoice && selectedQCMOptions.length > 0 && (
                <div className="text-sm text-blue-600">
                  Selected: {selectedQCMOptions.join(', ')}
                </div>
              )}
              <button
                onClick={recordAnswer}
                disabled={!canSubmitAnswer() || isSubmitting}
                className={`px-8 py-3 rounded-lg text-lg font-medium transition shadow-md ${
                  canSubmitAnswer() && !isSubmitting
                    ? isMultipleChoice ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-gray-400 text-gray-100 cursor-not-allowed'
                }`}
              >
                {isSubmitting ? '⏳ Submitting Your Answer...' : isMultipleChoice ? '✅ Submit Answers' : '✅ Submit Answer'}
              </button>
            </div>
          )}

          {/* CODING CONTROLS - MOVED TO SEPARATE AGENT */}
          {/* {(currentQuestionData?.question_type === 'coding' ||
            currentQuestionData?.question_type === 'coding_debug' ||
            currentQuestionData?.question_type === 'coding_explain') && (
            <div className="text-center">
              <button
                onClick={recordAnswer}
                disabled={!canSubmitAnswer() || isAnswering}
                className={`px-8 py-3 rounded-lg text-lg font-medium transition ${
                  canSubmitAnswer() && !isAnswering
                    ? 'bg-purple-600 hover:bg-purple-700 text-white'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {isAnswering ? '⏳ Submitting...' : '💻 Submit Code'}
              </button>
            </div>
          )} */}
        </div>
      )}
        </SecurityMonitor>
      )}

      {/* Evaluating Banner */}
      {isEvaluating && interviewComplete && (
        <div className="w-full max-w-2xl mx-auto">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-2xl p-8 text-center">
            <div className="text-6xl mb-4 animate-bounce">🔍</div>
            <h2 className="text-3xl font-bold text-white mb-4">
              Evaluating Your Answers...
            </h2>
            <div className="flex justify-center items-center space-x-2 mb-4">
              <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0s' }}></div>
              <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-3 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <p className="text-white text-lg">
              Please wait while we analyze your performance...
            </p>
          </div>
        </div>
      )}

      {/* Evaluation Results Display */}
      {evaluationData && interviewComplete && !isEvaluating && !securityViolation && (
        <div className="mt-6 w-full max-w-5xl space-y-6">
          {/* Overall Score Card */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl shadow-2xl p-8 border border-gray-200">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-6">
              📊 Your Interview Evaluation
            </h2>

            {/* Circular Score Display */}
            <div className="flex flex-col items-center mb-6">
              <div className="relative inline-flex items-center justify-center mb-4">
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
                    stroke={evaluationData.overall_score >= 7 ? "#10b981" : evaluationData.overall_score >= 5 ? "#f59e0b" : "#ef4444"}
                    strokeWidth="12"
                    fill="none"
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
            </div>

            {/* Score Breakdown */}
            <div className="bg-white rounded-lg p-6 shadow-md space-y-4">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Score Breakdown</h3>

              {/* QCM Score */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Multiple Choice Questions</span>
                  <span className="text-gray-900 font-bold">
                    {evaluationData.qcm_score}/10 ({evaluationData.qcm_details.correct_answers}/{evaluationData.qcm_details.total_questions} correct)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.qcm_score >= 7 ? 'bg-green-500' : evaluationData.qcm_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.qcm_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Technical Vocabulary Score */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Technical Vocabulary & Knowledge</span>
                  <span className="text-gray-900 font-bold">{evaluationData.technical_vocab_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.technical_vocab_score >= 7 ? 'bg-green-500' : evaluationData.technical_vocab_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.technical_vocab_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Grammar & Flow Score */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700 font-medium">Grammar & Communication Flow</span>
                  <span className="text-gray-900 font-bold">{evaluationData.grammar_flow_score}/10</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${evaluationData.grammar_flow_score >= 7 ? 'bg-green-500' : evaluationData.grammar_flow_score >= 5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(evaluationData.grammar_flow_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* QCM Results Section */}
          {evaluationData.qcm_details && evaluationData.qcm_details.total_questions > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">📋 Multiple Choice Results</h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="text-center">
                  <span className="text-2xl font-bold text-blue-900">
                    {evaluationData.qcm_details.correct_answers} / {evaluationData.qcm_details.total_questions}
                  </span>
                  <span className="text-gray-700 ml-2">correct ({evaluationData.qcm_details.percentage.toFixed(1)}%)</span>
                </div>
              </div>
              <div className="space-y-4">
                {evaluationData.qcm_question_details && evaluationData.qcm_question_details.map((qcmQuestion, index) => {
                  const isCorrect = qcmQuestion.is_correct;
                  const isMultiple = qcmQuestion.is_multiple_choice;

                  // Convert to arrays for easier comparison
                  const userAnswers = Array.isArray(qcmQuestion.user_answer) ? qcmQuestion.user_answer : [qcmQuestion.user_answer];
                  const correctAnswers = qcmQuestion.correct_answers && qcmQuestion.correct_answers.length > 0
                    ? qcmQuestion.correct_answers
                    : [qcmQuestion.correct_answer];

                  // For multiple choice, determine which answers are correct/incorrect
                  const correctUserAnswers = isMultiple ? userAnswers.filter(ans => correctAnswers.includes(ans)) : [];
                  const incorrectUserAnswers = isMultiple ? userAnswers.filter(ans => !correctAnswers.includes(ans)) : [];
                  const missedAnswers = isMultiple ? correctAnswers.filter(ans => !userAnswers.includes(ans)) : [];

                  // Determine overall status
                  let statusIcon = '❌';
                  let statusColor = 'red';
                  if (isCorrect) {
                    statusIcon = '✅';
                    statusColor = 'green';
                  } else if (isMultiple && correctUserAnswers.length > 0) {
                    statusIcon = '⚠️';
                    statusColor = 'yellow';
                  }

                  return (
                    <div key={index} className={`border-2 rounded-lg p-4 ${
                      isCorrect ? 'border-green-300 bg-green-50' :
                      (isMultiple && correctUserAnswers.length > 0) ? 'border-yellow-300 bg-yellow-50' :
                      'border-red-300 bg-red-50'
                    }`}>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <span className="text-sm font-semibold text-gray-600">
                            Question {qcmQuestion.question_id} {isMultiple ? '(Multiple Choice - Select ALL)' : '(Single Choice)'}
                          </span>
                          <p className="text-gray-800 font-medium mt-1">{qcmQuestion.question_text}</p>
                        </div>
                        <div className="ml-4">
                          <span className="text-3xl">{statusIcon}</span>
                        </div>
                      </div>

                      {/* For Single Choice Questions */}
                      {!isMultiple && (
                        <div className="space-y-2">
                          <div className={`p-3 rounded border-2 ${
                            isCorrect ? 'bg-green-100 border-green-400' : 'bg-red-100 border-red-400'
                          }`}>
                            <span className="text-sm font-semibold text-gray-700">Your Answer: </span>
                            <span className={`font-bold ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                              {userAnswers.join(', ')} {isCorrect ? '✅' : '❌'}
                            </span>
                          </div>
                          {!isCorrect && (
                            <div className="p-3 rounded border-2 bg-green-100 border-green-400">
                              <span className="text-sm font-semibold text-gray-700">Correct Answer: </span>
                              <span className="font-bold text-green-800">{correctAnswers.join(', ')} ✅</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* For Multiple Choice Questions */}
                      {isMultiple && (
                        <div className="space-y-3">
                          {/* Your Answers Section */}
                          <div>
                            <span className="text-sm font-semibold text-gray-700 block mb-2">Your Answers:</span>
                            <div className="space-y-2">
                              {correctUserAnswers.length > 0 && (
                                <div className="p-3 rounded border-2 bg-green-100 border-green-400">
                                  <span className="text-sm font-semibold text-gray-700">Correct: </span>
                                  <span className="font-bold text-green-800">
                                    {correctUserAnswers.join(', ')} ✅
                                  </span>
                                </div>
                              )}
                              {incorrectUserAnswers.length > 0 && (
                                <div className="p-3 rounded border-2 bg-red-100 border-red-400">
                                  <span className="text-sm font-semibold text-gray-700">Wrong: </span>
                                  <span className="font-bold text-red-800">
                                    {incorrectUserAnswers.join(', ')} ❌
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Missed Correct Answers */}
                          {missedAnswers.length > 0 && (
                            <div>
                              <span className="text-sm font-semibold text-gray-700 block mb-2">Missed Correct Answers:</span>
                              <div className="p-3 rounded border-2 bg-green-100 border-green-400">
                                <span className="text-sm font-semibold text-gray-700">Should have selected: </span>
                                <span className="font-bold text-green-800">
                                  {missedAnswers.join(', ')} ✅
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Full Correct Answer Summary */}
                          <div className="pt-2 border-t border-gray-300">
                            <div className="p-2 rounded bg-gray-100">
                              <span className="text-sm font-semibold text-gray-700">Complete Correct Answer: </span>
                              <span className="font-bold text-green-800">{correctAnswers.join(', ')}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Open Questions Feedback */}
          {evaluationData.open_question_feedback && evaluationData.open_question_feedback.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">💬 Detailed Feedback on Open Questions</h3>
              <div className="space-y-4">
                {evaluationData.open_question_feedback.map((feedback, index) => {
                  const isExpanded = expandedFeedback[feedback.question_id];

                  return (
                    <div key={feedback.question_id} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <span className="text-sm font-semibold text-blue-600">Question {feedback.question_id}</span>
                            <p className="text-gray-800 font-medium mt-1">{feedback.question}</p>
                          </div>
                          <div className="ml-4 flex flex-col items-end space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Tech:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${feedback.technical_vocab_score >= 7 ? 'bg-green-100 text-green-800' : feedback.technical_vocab_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {feedback.technical_vocab_score}/10
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-600">Grammar:</span>
                              <span className={`px-2 py-1 rounded text-sm font-bold ${feedback.grammar_flow_score >= 7 ? 'bg-green-100 text-green-800' : feedback.grammar_flow_score >= 5 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                                {feedback.grammar_flow_score}/10
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="p-4 bg-white">
                        <div className="mb-3">
                          <span className="text-sm font-semibold text-gray-700">Your Response:</span>
                          <p className="text-gray-600 mt-1 italic">{feedback.response}</p>
                        </div>

                        <button
                          onClick={() => setExpandedFeedback(prev => ({ ...prev, [feedback.question_id]: !prev[feedback.question_id] }))}
                          className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 font-medium transition"
                        >
                          <span>{isExpanded ? '▼' : '▶'}</span>
                          <span>{isExpanded ? 'Hide Feedback' : 'Show Detailed Feedback'}</span>
                        </button>

                        {isExpanded && (
                          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                            <p className="text-gray-800 leading-relaxed">{feedback.feedback}</p>
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
                link.download = `evaluation-report-${evaluationData.candidate_name}-${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium shadow-md"
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

      {/* Interview Complete (Legacy - shown only if no evaluation data) */}
      {interviewComplete && !evaluationData && !isEvaluating && !securityViolation && (
        <div className="mt-6 w-full max-w-4xl space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-green-600">🎉 Interview Complete!</h2>
            <p className="text-gray-600 mt-2">
              Your responses have been recorded across all interview phases
            </p>
            {savedAudioBlobs.length > 0 && (
              <div className="mt-4">
                <button
                  onClick={downloadAllAudio}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                >
                  🎧 Download All Audio Recordings ({savedAudioBlobs.length} files)
                </button>
              </div>
            )}
          </div>

          {/* Interview Q&A Summary */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-center text-gray-800">
              💬 Interview Summary
            </h3>
            {interviewLog.map((entry, index) => (
              <div key={index} className="p-6 bg-white rounded-lg shadow-md">
                <div className="mb-3">
                  <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-1 rounded-full">
                    {getPhaseDisplayName(entry.phase)} - Q{index + 1}
                  </span>
                  <span className="inline-block bg-gray-100 text-gray-600 text-xs font-semibold px-2 py-1 rounded-full ml-2">
                    {entry.question_type?.toUpperCase()}
                  </span>
                </div>
                <p className="font-medium text-gray-800 mb-3">
                  <strong>Q:</strong> {entry.question}
                </p>
                <div className="text-gray-700 bg-gray-50 p-3 rounded">
                  <strong>A:</strong> {entry.answer}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default InterviewComponent;