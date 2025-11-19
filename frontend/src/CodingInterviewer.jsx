import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import MonacoEditor from 'react-monaco-editor';
import { getMonacoLanguage } from './utils/languageMapper';
import SecurityMonitor from './components/security/SecurityMonitor';
import WarningModal from './components/security/WarningModal';

function CodingInterviewer({ onBack }) {
  // Basic interview state
  const [question, setQuestion] = useState('');
  const [questionCount, setQuestionCount] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [interviewLog, setInterviewLog] = useState([]);

  // Current question data
  const [currentQuestionData, setCurrentQuestionData] = useState(null);

  // Coding specific state
  const [codingAnswer, setCodingAnswer] = useState('');
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);
  const [isGeneratingQuestion, setIsGeneratingQuestion] = useState(false);

  // Separate state for different answer types
  const [debugFixedCode, setDebugFixedCode] = useState('');
  const [debugExplanation, setDebugExplanation] = useState('');
  const [explainAnalysis, setExplainAnalysis] = useState('');
  const [dbSchemaSQL, setDbSchemaSQL] = useState('');
  const [dbSchemaExplanation, setDbSchemaExplanation] = useState('');
  const [dbSchemaQueries, setDbSchemaQueries] = useState('');

  // Error handling
  const [generalError, setGeneralError] = useState('');
  const [startingInterview, setStartingInterview] = useState(false);
  const [submitSuccessMessage, setSubmitSuccessMessage] = useState('');

  // Countdown timer state
  const [countdown, setCountdown] = useState(null);
  const [isCountingDown, setIsCountingDown] = useState(false);

  // NEW: Test cases and evaluation state
  const [currentTestCases, setCurrentTestCases] = useState([]);
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Security state
  const [securityEnabled, setSecurityEnabled] = useState(false);
  const [securityViolation, setSecurityViolation] = useState(null);
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);
  const securityMonitorRef = useRef(null);

  // Navigation state - NEW
  const [allQuestions, setAllQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answersMap, setAnswersMap] = useState({
    1: { code: '', explanation: '', analysis: '', sql: '', sqlExplanation: '', sqlQueries: '' },
    2: { code: '', explanation: '', analysis: '', sql: '', sqlExplanation: '', sqlQueries: '' },
    3: { code: '', explanation: '', analysis: '', sql: '', sqlExplanation: '', sqlQueries: '' },
    4: { code: '', explanation: '', analysis: '', sql: '', sqlExplanation: '', sqlQueries: '' },
    5: { code: '', explanation: '', analysis: '', sql: '', sqlExplanation: '', sqlQueries: '' }
  });
  const [submittedQuestions, setSubmittedQuestions] = useState(new Set());
  const [codingTestFilename, setCodingTestFilename] = useState('');  // For evaluation

  // Auto-disable security monitoring when all questions are submitted
  useEffect(() => {
    if (submittedQuestions.size >= totalQuestions && securityEnabled && interviewStarted && !interviewComplete) {
      console.log('✅ All questions submitted - disabling security monitoring');
      if (securityMonitorRef.current?.stopSecurity) {
        securityMonitorRef.current.stopSecurity();
      }
      setSecurityEnabled(false);
    }
  }, [submittedQuestions.size, totalQuestions, securityEnabled, interviewStarted, interviewComplete]);

  const startInterviewWithCountdown = async () => {
    try {
      setGeneralError('');
      setStartingInterview(true);

      // Call backend and wait for analysis
      const response = await axios.get('http://127.0.0.1:5000/start_coding_interview', {
        timeout: 90000 // Increased timeout for job analysis and question generation
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

      // Backend returns single first question - store it in array
      setAllQuestions([data]);  // Initialize with first question
      setTotalQuestions(data.total_questions || 5);
      setCurrentQuestionIndex(0);
      setCodingTestFilename(data.coding_test_filename || '');  // Store for evaluation

      // Now show countdown
      setStartingInterview(false);
      setIsCountingDown(true);
      setCountdown(10);

      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            setIsCountingDown(false);
            // Display first question
            displayCodingQuestion(data);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (error) {
      console.error('Error starting coding interview:', error);
      setGeneralError(`Error starting coding interview: ${error.message}`);
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

  const displayCodingQuestion = (data) => {
    // Handle coding question data
    setCurrentQuestionData(data);
    setQuestionCount(data.question_count || 1);
    setTotalQuestions(data.total_questions || 5);
    setQuestion(data.title || data.question);

    // NEW: Set test cases if available
    if (data.test_cases && data.test_cases.length > 0) {
      setCurrentTestCases(data.test_cases);
    } else {
      setCurrentTestCases([]);
    }

    // Clear all input fields when starting interview
    setCodingAnswer('');
    setDebugFixedCode('');
    setDebugExplanation('');
    setExplainAnalysis('');
    setDbSchemaSQL('');
    setDbSchemaExplanation('');
    setDbSchemaQueries('');

    setInterviewStarted(true);
  };

  // Navigation functions - NEW
  const saveCurrentAnswer = () => {
    const questionNum = currentQuestionIndex + 1;
    const questionType = currentQuestionData?.question_type;

    setAnswersMap(prev => ({
      ...prev,
      [questionNum]: {
        code: questionType === 'coding_debug' ? debugFixedCode : '',
        explanation: questionType === 'coding_debug' ? debugExplanation : '',
        analysis: questionType === 'coding_explain' ? explainAnalysis : '',
        sql: questionType === 'db_schema' ? dbSchemaSQL : '',
        sqlExplanation: questionType === 'db_schema' ? dbSchemaExplanation : '',
        sqlQueries: questionType === 'db_schema' ? dbSchemaQueries : ''
      }
    }));
  };

  const loadAnswerForQuestion = (questionNum) => {
    const savedAnswer = answersMap[questionNum];
    if (savedAnswer) {
      setDebugFixedCode(savedAnswer.code || '');
      setDebugExplanation(savedAnswer.explanation || '');
      setExplainAnalysis(savedAnswer.analysis || '');
      setDbSchemaSQL(savedAnswer.sql || '');
      setDbSchemaExplanation(savedAnswer.sqlExplanation || '');
      setDbSchemaQueries(savedAnswer.sqlQueries || '');
    } else {
      // Clear all fields if no saved answer
      setDebugFixedCode('');
      setDebugExplanation('');
      setExplainAnalysis('');
      setDbSchemaSQL('');
      setDbSchemaExplanation('');
      setDbSchemaQueries('');
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      saveCurrentAnswer();  // Save current answer before navigating
      const prevIndex = currentQuestionIndex - 1;
      setCurrentQuestionIndex(prevIndex);
      displayCodingQuestion(allQuestions[prevIndex]);
      loadAnswerForQuestion(prevIndex + 1);  // Load saved answer (question numbers are 1-indexed)
    }
  };

  const completeInterview = async () => {
    // GUARD: Prevent multiple simultaneous calls (race condition protection)
    if (isEvaluating || interviewComplete) {
      console.log('Already evaluating or complete - ignoring duplicate call');
      return;
    }

    // Check if all questions submitted
    if (submittedQuestions.size < totalQuestions) {
      const unanswered = totalQuestions - submittedQuestions.size;
      alert(`Please submit all questions first. ${unanswered} question(s) remaining.`);
      return;
    }

    // Trigger evaluation
    try {
      setIsEvaluating(true);
      setGeneralError('');

      // Note: Security monitoring already disabled by useEffect when all questions submitted

      // Call evaluation endpoint
      const evalResponse = await axios.post(
        'http://127.0.0.1:5000/coding/evaluate',
        { coding_test_filename: codingTestFilename },
        {
          withCredentials: true,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      // Handle evaluation results
      const evalData = evalResponse.data;

      if (evalData.evaluation_results) {
        setEvaluationResults(evalData.evaluation_results);
        setInterviewComplete(true);
      } else {
        // If no evaluation_results yet, show waiting state
        setInterviewComplete(true);
      }

      // FIXED: Always exit evaluating state on success
      setIsEvaluating(false);

    } catch (error) {
      console.error('Error completing interview:', error);
      setGeneralError(`Error evaluating interview: ${error.message}`);
      setIsEvaluating(false);
    }
  };

  const goToNextQuestion = async () => {
    const nextIndex = currentQuestionIndex + 1;
    const nextQuestionNumber = nextIndex + 1;

    // Don't allow going beyond Q5
    if (nextIndex >= totalQuestions) {
      return;
    }

    // Check if next question exists in cache
    if (nextIndex < allQuestions.length) {
      // Already generated - just navigate
      saveCurrentAnswer();
      setCurrentQuestionIndex(nextIndex);
      displayCodingQuestion(allQuestions[nextIndex]);
      loadAnswerForQuestion(nextQuestionNumber);
    } else {
      // Not generated yet - fetch it from backend
      saveCurrentAnswer();

      try {
        setIsGeneratingQuestion(true); // Show loading state

        const response = await axios.get(
          `http://127.0.0.1:5000/coding/generate_question?question_number=${nextQuestionNumber}`,
          { withCredentials: true }
        );

        const nextQuestion = response.data;

        // Add to cache
        setAllQuestions(prev => [...prev, nextQuestion]);
        setCurrentQuestionIndex(nextIndex);
        displayCodingQuestion(nextQuestion);
        loadAnswerForQuestion(nextQuestionNumber);

      } catch (error) {
        console.error('Error generating next question:', error);
        setGeneralError(`Failed to generate next question: ${error.message}`);
      } finally {
        setIsGeneratingQuestion(false);
      }
    }
  };

  const submitCodingAnswer = async () => {
    try {
      setIsSubmittingAnswer(true);
      const questionNum = currentQuestionIndex + 1;

      // Save answer before submitting
      saveCurrentAnswer();

      // Construct response based on question type
      let responseText = '';

      if (currentQuestionData.question_type === 'coding_debug') {
        if (!debugFixedCode.trim() || !debugExplanation.trim()) {
          setGeneralError('Please provide both fixed code and explanation');
          setIsSubmittingAnswer(false);
          return;
        }
        responseText = `FIXED CODE:\n${debugFixedCode}\n\nEXPLANATION:\n${debugExplanation}`;

      } else if (currentQuestionData.question_type === 'coding_explain') {
        if (!explainAnalysis.trim()) {
          setGeneralError('Please provide your analysis');
          setIsSubmittingAnswer(false);
          return;
        }
        responseText = explainAnalysis;

      } else if (currentQuestionData.question_type === 'db_schema') {
        if (!dbSchemaSQL.trim() || !dbSchemaExplanation.trim()) {
          setGeneralError('Please provide both schema and explanation');
          setIsSubmittingAnswer(false);
          return;
        }
        responseText = `SQL SCHEMA:\n${dbSchemaSQL}\n\nDESIGN EXPLANATION:\n${dbSchemaExplanation}`;
        if (dbSchemaQueries.trim()) {
          responseText += `\n\nEXAMPLE QUERIES:\n${dbSchemaQueries}`;
        }
      } else {
        // Fallback for backward compatibility
        if (!codingAnswer.trim()) {
          setGeneralError('Please provide an answer before submitting');
          setIsSubmittingAnswer(false);
          return;
        }
        responseText = codingAnswer;
      }

      const responseData = {
        response: responseText,
        question_number: questionNum  // Send which question is being submitted
      };

      const submitRes = await axios.post('http://127.0.0.1:5000/coding/submit', responseData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = submitRes.data;

      // Save current Q&A to log
      const logEntry = {
        question: question,
        answer: responseText,
        question_type: currentQuestionData?.question_type || 'coding',
        question_number: questionNum
      };
      setInterviewLog((prev) => [...prev, logEntry]);

      // Mark question as submitted
      setSubmittedQuestions(prev => new Set(prev).add(questionNum));

      // Calculate new submission count (including current question)
      const newSubmissionCount = submittedQuestions.has(questionNum)
        ? submittedQuestions.size
        : submittedQuestions.size + 1;

      // Question submitted successfully
      // Don't auto-navigate - user can navigate manually
      setGeneralError(''); // Clear any errors

      // Show success message (no alert to avoid fullscreen exit)
      setSubmitSuccessMessage(`✅ Answer submitted successfully! (${newSubmissionCount}/${totalQuestions} submitted)`);

      // Auto-clear message after 3 seconds
      setTimeout(() => {
        setSubmitSuccessMessage('');
      }, 3000);

      // Note: Backend no longer generates next question or triggers evaluation
      // Frontend controls all navigation via Next button and completeInterview()

    } catch (error) {
      console.error('Error submitting coding answer:', error);
      setGeneralError(`Error submitting response: ${error.message}`);
    } finally {
      setIsSubmittingAnswer(false);
    }
  };

  const getQuestionTypeLabel = (questionType) => {
    switch (questionType) {
      case 'coding_debug': return 'Debug Challenge';
      case 'coding_explain': return 'Code Analysis';
      case 'db_schema': return 'Database Design';
      default: return 'Coding Challenge';
    }
  };

  const getLanguageDisplayName = (languageCode) => {
    const displayNames = {
      'python': 'Python',
      'javascript': 'JavaScript',
      'typescript': 'TypeScript',
      'java': 'Java',
      'csharp': 'C#',
      'go': 'Go',
      'rust': 'Rust',
      'php': 'PHP',
      'ruby': 'Ruby',
      'sql': 'SQL',
    };
    return displayNames[languageCode] || languageCode.toUpperCase();
  };

  const getLanguageBadgeColor = (languageCode) => {
    const colors = {
      'python': 'bg-blue-100 text-blue-800 border-blue-300',
      'javascript': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'typescript': 'bg-blue-100 text-blue-800 border-blue-300',
      'java': 'bg-orange-100 text-orange-800 border-orange-300',
      'csharp': 'bg-purple-100 text-purple-800 border-purple-300',
      'go': 'bg-cyan-100 text-cyan-800 border-cyan-300',
      'rust': 'bg-orange-100 text-orange-800 border-orange-300',
      'sql': 'bg-indigo-100 text-indigo-800 border-indigo-300',
    };
    return colors[languageCode] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const isSubmitDisabled = () => {
    if (isSubmittingAnswer) return true;

    switch(currentQuestionData?.question_type) {
      case 'coding_debug':
        return !debugFixedCode.trim() || !debugExplanation.trim();
      case 'coding_explain':
        return !explainAnalysis.trim();
      case 'db_schema':
        return !dbSchemaSQL.trim() || !dbSchemaExplanation.trim();
      default:
        return !codingAnswer.trim(); // Fallback
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

      await axios.post('http://127.0.0.1:5000/coding/evaluate', partialData, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('Partial responses saved due to violation');
    } catch (error) {
      console.error('Failed to save partial responses:', error);
    }
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
            background: '#48bb78',
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
            e.target.style.background = '#38a169'
            e.target.style.transform = 'translateY(-2px)'
            e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#48bb78'
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)'
          }}
        >
          ← Back to Menu
        </button>
      )}

      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          🖥️ Coding Interview Agent
        </h1>
        <p className="text-lg text-gray-600">
          Specialized AI interviewer focused on coding challenges
        </p>
      </div>

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

      {/* Job Description Info Banner */}
      {!interviewStarted && !interviewComplete && !isCountingDown && (
        <div className="w-full max-w-lg mx-auto mb-6">
          <div className="bg-blue-100 border border-blue-400 text-blue-700 p-4 rounded">
            <h3 className="font-bold">📋 About This Interview</h3>
            <div className="mt-2 text-sm">
              <p>• Coding questions are generated based on the job description requirements</p>
              <p>• Make sure <code className="bg-blue-200 px-1 rounded">backend/uploads/job_description.txt</code> contains the target role details</p>
              <p>• Questions will test skills and technologies mentioned in the job posting</p>
            </div>
          </div>
        </div>
      )}

      {/* Start Interview Button */}
      {!interviewStarted && !interviewComplete && !isCountingDown && (
        <div className="text-center">
          <h2 className="text-xl font-semibold text-green-600 mb-4">
            Ready to Start Coding Interview?
          </h2>
          <button
            onClick={() => setShowSecurityWarning(true)}
            disabled={startingInterview}
            className={`px-8 py-4 rounded-lg transition text-lg font-medium shadow-md ${
              startingInterview
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            } text-white`}
          >
            {startingInterview ? '🔍 Analyzing job requirements and preparing coding challenges...' : '💻 Start Coding Interview'}
          </button>
          <p className="text-sm text-gray-600 mt-2">
            You'll face {totalQuestions} coding challenges alternating between debug and analysis tasks
          </p>
        </div>
      )}

      {/* Security Warning Modal - Shows BEFORE interview starts */}
      {showSecurityWarning && !interviewStarted && (
        <WarningModal
          onAccept={handleSecurityAcceptAndStart}
          interviewType="coding"
        />
      )}

      {/* Countdown Display & Interview - Wrapped with SecurityMonitor */}
      {(isCountingDown || (interviewStarted && !interviewComplete)) && (
        <SecurityMonitor
          ref={securityMonitorRef}
          enabled={securityEnabled}
          onViolation={handleSecurityViolation}
          onWarning={handleSecurityWarning}
          interviewType="coding"
        >
          {/* Countdown Display */}
          {isCountingDown && (
            <div className="w-full max-w-2xl">
              <div className="bg-white rounded-2xl shadow-2xl p-12 text-center border border-gray-200">
                <h2 className="text-3xl font-bold text-gray-800 mb-8">Starting Coding Interview</h2>

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
                  stroke="#16a34a"
                  strokeWidth="12"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 88}`}
                  strokeDashoffset={`${2 * Math.PI * 88 * (1 - countdown / 10)}`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-linear"
                />
              </svg>
              <div className="absolute text-6xl font-bold text-green-600">
                {countdown}
              </div>
            </div>

            <p className="text-xl text-gray-600">
              Starting in <span className="font-bold text-green-600">{countdown}</span> second{countdown !== 1 ? 's' : ''}...
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Prepare yourself for the coding challenges
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
                Question {questionCount}/{totalQuestions} - {getQuestionTypeLabel(currentQuestionData.question_type)}
              </h3>
              <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                {currentQuestionData.question_type?.toUpperCase()}
              </span>
            </div>

            <div>
              <h4 className="text-xl font-bold text-gray-800 mb-4">{question}</h4>

              {/* PART 1: Context Paragraph - NEW STRUCTURED FORMAT */}
              {currentQuestionData.context_paragraph && (
                <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                  <strong className="text-blue-800 flex items-center gap-2">
                    📋 Context
                  </strong>
                  <p className="text-gray-700 mt-2 leading-relaxed">{currentQuestionData.context_paragraph}</p>
                </div>
              )}

              {/* PART 2: Code/Challenge Section (Type-Specific) */}

              {/* Debug Challenge: Buggy Code */}
              {currentQuestionData.question_type === 'coding_debug' && currentQuestionData.buggy_code && (
                <div className="mb-4">
                  <strong className="text-gray-800 block mb-2">🐛 Buggy Code:</strong>
                  <pre className="bg-red-50 border border-red-200 text-red-900 p-4 rounded overflow-x-auto text-sm font-mono leading-relaxed">
                    {currentQuestionData.buggy_code}
                  </pre>
                </div>
              )}

              {/* Code Analysis: Working Code */}
              {currentQuestionData.question_type === 'coding_explain' && currentQuestionData.working_code && (
                <div className="mb-4">
                  <strong className="text-gray-800 block mb-2">💻 Code to Analyze:</strong>
                  <pre className="bg-blue-50 border border-blue-200 text-blue-900 p-4 rounded overflow-x-auto text-sm font-mono leading-relaxed">
                    {currentQuestionData.working_code}
                  </pre>
                </div>
              )}

              {/* Database Schema: Requirements */}
              {currentQuestionData.question_type === 'db_schema' && (
                <div className="mb-4">
                  <div className="mb-3">
                    <strong className="text-gray-800">🗄️ Database Technology: </strong>
                    <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                      {currentQuestionData.db_technology || 'SQL'}
                    </span>
                  </div>
                  {currentQuestionData.requirements && currentQuestionData.requirements.length > 0 && (
                    <div className="bg-indigo-50 border border-indigo-200 p-4 rounded">
                      <strong className="text-gray-800 block mb-2">Requirements:</strong>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        {currentQuestionData.requirements.map((req, index) => (
                          <li key={index} className="ml-2">{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* PART 3: Your Task - NEW STRUCTURED FORMAT */}
              {currentQuestionData.task_instruction && (
                <div className="mb-4 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
                  <strong className="text-yellow-800 flex items-center gap-2">
                    ✏️ Your Task
                  </strong>
                  <p className="text-gray-700 mt-2 leading-relaxed">{currentQuestionData.task_instruction}</p>
                </div>
              )}

              {/* PART 4: Expected Outcome - NEW STRUCTURED FORMAT */}
              {currentQuestionData.expected_outcome && (
                <div className="mb-4 p-4 bg-green-50 border-l-4 border-green-500 rounded">
                  <strong className="text-green-800 flex items-center gap-2">
                    ✅ Expected Outcome
                  </strong>
                  <p className="text-gray-700 mt-2 leading-relaxed">{currentQuestionData.expected_outcome}</p>
                </div>
              )}

              {/* NEW: Test Cases Display */}
              {currentTestCases && currentTestCases.length > 0 && (
                <div className="mb-4 p-4 bg-purple-50 border-l-4 border-purple-500 rounded">
                  <details className="cursor-pointer">
                    <summary className="font-semibold text-purple-800 flex items-center gap-2">
                      📝 Test Cases You Need to Pass ({currentTestCases.length})
                    </summary>
                    <div className="mt-3 space-y-2">
                      {currentTestCases.map((tc, idx) => (
                        <div key={idx} className="p-3 bg-white border border-purple-200 rounded">
                          <p className="text-sm text-gray-600 mb-1">
                            <span className="font-medium">Test {idx + 1}:</span> {tc.description}
                            <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                              tc.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                              tc.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {tc.difficulty}
                            </span>
                          </p>
                          {tc.input && (
                            <div className="grid grid-cols-2 gap-2 text-xs font-mono mt-2">
                              <div>
                                <strong className="text-gray-700">Input:</strong>
                                <pre className="bg-gray-50 p-2 rounded mt-1 overflow-x-auto">{tc.input || '(none)'}</pre>
                              </div>
                              <div>
                                <strong className="text-gray-700">Expected Output:</strong>
                                <pre className="bg-gray-50 p-2 rounded mt-1 overflow-x-auto">{tc.expected_output}</pre>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}

              {/* BACKWARD COMPATIBILITY: Fallback to old fields if new ones don't exist */}
              {!currentQuestionData.context_paragraph && currentQuestionData.description && (
                <p className="text-gray-700 mb-4">{currentQuestionData.description}</p>
              )}
              {!currentQuestionData.expected_outcome && currentQuestionData.expected_behavior && (
                <div className="mb-4 p-3 bg-gray-50 rounded">
                  <strong className="text-gray-800">Expected Behavior:</strong>
                  <p className="text-gray-700 mt-1">{currentQuestionData.expected_behavior}</p>
                </div>
              )}
              {!currentQuestionData.task_instruction && currentQuestionData.analysis_questions && (
                <div className="mb-4">
                  <strong className="text-gray-800">Analysis Questions:</strong>
                  <ul className="list-disc list-inside mt-2 text-gray-700">
                    {currentQuestionData.analysis_questions.map((q, index) => (
                      <li key={index} className="mb-1">{q}</li>
                    ))}
                  </ul>
                </div>
              )}
              {!currentQuestionData.context_paragraph && currentQuestionData.context && (
                <div className="mb-4 p-3 bg-gray-50 rounded">
                  <strong className="text-gray-800">Context:</strong>
                  <p className="text-gray-700 mt-1">{currentQuestionData.context}</p>
                </div>
              )}

              {/* Type-Specific Input Components */}
              <div className="mb-4">
                {/* A. Debug Question Input */}
                {currentQuestionData.question_type === 'coding_debug' && (
                  <div className="space-y-4">
                    {/* Fixed Code Editor */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🔧 Your Fixed Code:
                      </label>
                      {/* Language Indicator Badge */}
                      <div className="flex items-center justify-between mb-0 px-3 py-2 bg-gray-50 rounded-t-lg border border-b-0 border-red-300">
                        <span className="text-xs font-semibold text-gray-600">CODE EDITOR</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getLanguageBadgeColor(getMonacoLanguage(currentQuestionData.debug_data?.target_language || 'python'))}`}>
                          {getLanguageDisplayName(getMonacoLanguage(currentQuestionData.debug_data?.target_language || 'python'))}
                        </span>
                      </div>
                      <div className="border-2 border-red-300 rounded-b-lg overflow-hidden">
                        <MonacoEditor
                          height="300"
                          language={getMonacoLanguage(currentQuestionData.debug_data?.target_language || 'python')}
                          theme="vs-dark"
                          value={debugFixedCode}
                          onChange={(value) => setDebugFixedCode(value)}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                            quickSuggestions: true,
                            suggestOnTriggerCharacters: true,
                            acceptSuggestionOnEnter: 'on',
                            tabCompletion: 'on',
                            wordBasedSuggestions: true,
                            renderValidationDecorations: 'on',
                          }}
                        />
                      </div>
                      {/* Info Message */}
                      <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700 flex items-center gap-2">
                        <span>ℹ️</span>
                        <span>
                          <strong>Note:</strong> This editor provides syntax highlighting and validation.
                          Your code will be submitted for evaluation - it does not execute in real-time.
                        </span>
                      </div>
                    </div>

                    {/* Explanation Text Area */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        📝 Explain what you fixed:
                      </label>
                      <textarea
                        value={debugExplanation}
                        onChange={(e) => setDebugExplanation(e.target.value)}
                        className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
                        placeholder="Explain the bugs you found and how you fixed them..."
                      />
                    </div>
                  </div>
                )}

                {/* B. Explain Question Input */}
                {currentQuestionData.question_type === 'coding_explain' && (
                  <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📊 Your Code Analysis:
                    </label>
                    <textarea
                      value={explainAnalysis}
                      onChange={(e) => setExplainAnalysis(e.target.value)}
                      className="w-full h-80 p-4 border-2 border-blue-300 rounded-lg font-sans text-sm focus:ring-2 focus:ring-blue-500"
                      placeholder="Provide detailed analysis:
• Explain what the code does
• Time/space complexity analysis
• Potential improvements
• Edge cases to consider
• Best practices evaluation"
                    />
                    <p className="text-sm text-gray-500">
                      💡 Tip: Write at least 100 words for a comprehensive analysis
                    </p>
                  </div>
                )}

                {/* C. Database Schema Input */}
                {currentQuestionData.question_type === 'db_schema' && (
                  <div className="space-y-4">
                    {/* SQL Schema Editor */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🗄️ Database Schema (CREATE TABLE statements):
                      </label>
                      {/* Language Indicator Badge */}
                      <div className="flex items-center justify-between mb-0 px-3 py-2 bg-gray-50 rounded-t-lg border border-b-0 border-purple-300">
                        <span className="text-xs font-semibold text-gray-600">SQL EDITOR</span>
                        <span className="px-3 py-1 rounded-full text-xs font-bold border bg-indigo-100 text-indigo-800 border-indigo-300">
                          SQL
                        </span>
                      </div>
                      <div className="border-2 border-purple-300 rounded-b-lg overflow-hidden">
                        <MonacoEditor
                          height="250"
                          language="sql"
                          theme="vs-dark"
                          value={dbSchemaSQL}
                          onChange={(value) => setDbSchemaSQL(value)}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                            quickSuggestions: true,
                            suggest: {
                              snippetsPreventQuickSuggestions: false,
                            },
                            renderValidationDecorations: 'on',
                          }}
                        />
                      </div>
                      {/* Info Message */}
                      <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700 flex items-center gap-2">
                        <span>ℹ️</span>
                        <span>
                          <strong>Note:</strong> Write your CREATE TABLE statements with constraints.
                          Your schema will be submitted for evaluation - it does not execute in real-time.
                        </span>
                      </div>
                    </div>

                    {/* Design Explanation */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        📋 Design Explanation:
                      </label>
                      <textarea
                        value={dbSchemaExplanation}
                        onChange={(e) => setDbSchemaExplanation(e.target.value)}
                        className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="Explain your schema design decisions, relationships, and constraints..."
                      />
                    </div>

                    {/* Example Queries */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🔍 Example Queries (Optional):
                      </label>
                      {/* Language Indicator Badge */}
                      <div className="flex items-center justify-between mb-0 px-3 py-2 bg-gray-50 rounded-t-lg border border-b-0 border-purple-200">
                        <span className="text-xs font-semibold text-gray-600">SQL EDITOR</span>
                        <span className="px-3 py-1 rounded-full text-xs font-bold border bg-indigo-100 text-indigo-800 border-indigo-300">
                          SQL
                        </span>
                      </div>
                      <div className="border-2 border-purple-200 rounded-b-lg overflow-hidden">
                        <MonacoEditor
                          height="150"
                          language="sql"
                          theme="vs-light"
                          value={dbSchemaQueries}
                          onChange={(value) => setDbSchemaQueries(value)}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 13,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                            quickSuggestions: true,
                            suggest: {
                              snippetsPreventQuickSuggestions: false,
                            },
                            renderValidationDecorations: 'on',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      {question && !interviewComplete && (
        <div className="w-full max-w-lg mx-auto text-center">
          <button
            onClick={submitCodingAnswer}
            disabled={isSubmitDisabled() || isSubmittingAnswer}
            className={`px-8 py-3 rounded-lg text-lg font-medium transition shadow-md ${
              !isSubmitDisabled() && !isSubmittingAnswer
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-400 text-gray-100 cursor-not-allowed'
            }`}
          >
            {isSubmittingAnswer
              ? '⏳ Submitting Your Answer...'
              : currentQuestionIndex === allQuestions.length - 1 && submittedQuestions.size === allQuestions.length - 1
                ? '✅ Submit Final Answer & Complete Interview'
                : '✅ Submit This Answer'
            }
          </button>

          {/* Success Message */}
          {submitSuccessMessage && (
            <div className="mt-3 text-green-600 font-medium text-center">
              {submitSuccessMessage}
            </div>
          )}
        </div>
      )}

      {/* Navigation Controls - NEW */}
      {question && !interviewComplete && allQuestions.length > 0 && (
        <div className="w-full max-w-3xl mx-auto mt-6">
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '15px 20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            border: '1px solid #dee2e6',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            {/* Previous Button */}
            <button
              onClick={goToPreviousQuestion}
              disabled={currentQuestionIndex === 0}
              style={{
                padding: '10px 20px',
                backgroundColor: currentQuestionIndex === 0 ? '#e9ecef' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: currentQuestionIndex === 0 ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'background-color 0.2s',
                opacity: currentQuestionIndex === 0 ? 0.5 : 1
              }}
            >
              <span>←</span> Previous
            </button>

            {/* Question Progress Indicator */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '15px',
              flexDirection: 'column'
            }}>
              <span style={{
                fontSize: '16px',
                fontWeight: 'bold',
                color: '#495057'
              }}>
                Question {currentQuestionIndex + 1} of {totalQuestions}
              </span>

              {/* Visual Progress Dots */}
              <div style={{ display: 'flex', gap: '8px' }}>
                {Array.from({ length: totalQuestions }).map((_, idx) => {
                  const questionNum = idx + 1;
                  const isSubmitted = submittedQuestions.has(questionNum);
                  const isCurrent = idx === currentQuestionIndex;

                  return (
                    <div
                      key={idx}
                      style={{
                        width: '14px',
                        height: '14px',
                        borderRadius: '50%',
                        backgroundColor: isSubmitted
                          ? '#28a745'  // Green if submitted
                          : isCurrent
                            ? '#007bff'  // Blue if current
                            : '#dee2e6', // Gray if not visited
                        border: isCurrent ? '3px solid #0056b3' : 'none',
                        transition: 'all 0.3s ease',
                        cursor: 'default'
                      }}
                      title={`Question ${questionNum}${isSubmitted ? ' (✓ Submitted)' : isCurrent ? ' (Current)' : ''}`}
                    />
                  );
                })}
              </div>

              {/* Progress Text */}
              <div style={{ fontSize: '12px', color: '#6c757d' }}>
                {submittedQuestions.size} of {totalQuestions} submitted
              </div>
            </div>

            {/* Next Button OR Complete Interview Button */}
            {currentQuestionIndex === totalQuestions - 1 ? (
              // On Q5: Show "Complete Interview" button
              <button
                onClick={completeInterview}
                disabled={submittedQuestions.size < totalQuestions || isEvaluating || interviewComplete}
                style={{
                  padding: '10px 20px',
                  backgroundColor: (submittedQuestions.size < totalQuestions || isEvaluating || interviewComplete)
                    ? (submittedQuestions.size < totalQuestions ? '#ffc107' : '#6c757d')  // Yellow warning or gray disabled
                    : '#28a745',  // Green success
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: (submittedQuestions.size < totalQuestions || isEvaluating || interviewComplete) ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.3s ease',
                  opacity: (submittedQuestions.size < totalQuestions || isEvaluating || interviewComplete) ? 0.7 : 1,
                  minWidth: '160px',
                  justifyContent: 'center'
                }}
                title={
                  isEvaluating ? "Evaluating your responses..." :
                  interviewComplete ? "Interview already completed" :
                  submittedQuestions.size < totalQuestions
                    ? `Submit all questions first (${submittedQuestions.size}/${totalQuestions} completed)`
                    : "Complete interview and view results"
                }
              >
                {isEvaluating ? <><span>⏳</span> Evaluating...</> :
                 submittedQuestions.size < totalQuestions
                  ? <><span>⚠️</span> Complete All ({submittedQuestions.size}/{totalQuestions})</>
                  : <><span>✅</span> Complete Interview</>
                }
              </button>
            ) : (
              // On Q1-Q4: Show Next button
              <button
                onClick={goToNextQuestion}
                disabled={isGeneratingQuestion || currentQuestionIndex >= totalQuestions - 1}
                style={{
                  padding: '10px 20px',
                  backgroundColor: (isGeneratingQuestion || currentQuestionIndex >= totalQuestions - 1) ? '#e9ecef' : '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: (isGeneratingQuestion || currentQuestionIndex >= totalQuestions - 1) ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s',
                  opacity: (isGeneratingQuestion || currentQuestionIndex >= totalQuestions - 1) ? 0.5 : 1,
                  minWidth: '120px',
                  justifyContent: 'center'
                }}
                title={isGeneratingQuestion ? "Generating question..." : "Navigate to next question"}
              >
                {isGeneratingQuestion ? 'Generating...' : <>{/* Next */}Next <span>→</span></>}
              </button>
            )}
          </div>
        </div>
      )}
        </SecurityMonitor>
      )}

      {/* Evaluating Loading State */}
      {isEvaluating && (
        <div className="w-full max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Evaluating Your Code...
            </h2>
            <p className="text-gray-600">
              Compiling and testing your solutions. This may take a minute.
            </p>
          </div>
        </div>
      )}

      {/* Evaluation Results Display */}
      {interviewComplete && evaluationResults && !isEvaluating && !securityViolation && (
        <div className="w-full max-w-4xl mx-auto space-y-6">
          {/* Overall Score Card */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-xl p-6 text-center">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              🎉 Interview Complete!
            </h2>
            <div className="text-6xl font-bold text-green-600 my-4">
              {evaluationResults.overall_score.toFixed(1)}/10
            </div>
            <p className="text-lg text-gray-700">
              {evaluationResults.overall_feedback}
            </p>
          </div>

          {/* Per-Question Results */}
          <div className="space-y-4">
            <h3 className="text-2xl font-semibold text-gray-800 text-center">
              Question-by-Question Breakdown
            </h3>

            {evaluationResults.questions && evaluationResults.questions.map((q, idx) => {
              const score = q.score || 0;
              const scoreColor = score >= 8 ? 'green' : score >= 5 ? 'yellow' : 'red';
              const scoreBgColor = score >= 8 ? 'bg-green-100' : score >= 5 ? 'bg-yellow-100' : 'bg-red-100';
              const scoreBorderColor = score >= 8 ? 'border-green-300' : score >= 5 ? 'border-yellow-300' : 'border-red-300';
              const scoreTextColor = score >= 8 ? 'text-green-600' : score >= 5 ? 'text-yellow-600' : 'text-red-600';

              return (
                <div key={idx} className={`bg-white border-2 ${scoreBorderColor} rounded-lg p-6 shadow-md`}>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold text-lg text-gray-800">
                        Q{idx + 1}: {q.question_title}
                      </h4>
                      <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded mt-1 inline-block">
                        {q.question_type.toUpperCase()}
                      </span>
                    </div>
                    <div className={`text-3xl font-bold ${scoreTextColor}`}>
                      {score}/10
                    </div>
                  </div>

                  {/* Feedback Phrases */}
                  {q.feedback && q.feedback.length > 0 && (
                    <div className="space-y-1 mb-4">
                      {q.feedback.map((phrase, i) => (
                        <p key={i} className="text-sm text-gray-700">
                          {i === 0 ? '✅' : i === 1 ? '💡' : '📊'} {phrase}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Test Results (for debug questions) */}
                  {q.details?.test_results && q.details.test_results.length > 0 && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-sm font-medium text-gray-700">
                        View Test Results ({q.details.test_results.filter(t => t.passed).length}/{q.details.test_results.length} passed)
                      </summary>
                      <div className="mt-2 space-y-1">
                        {q.details.test_results.map((test, i) => (
                          <div key={i} className={`text-xs p-2 rounded ${test.passed ? 'bg-green-50' : 'bg-red-50'}`}>
                            {test.passed ? '✅' : '❌'} {test.description || `Test ${i + 1}`}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  {/* Compilation Errors (if any) */}
                  {q.details?.compilation?.fixed_results?.stderr && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                      <strong className="text-red-800 text-sm">Compilation Error:</strong>
                      <pre className="text-xs text-red-700 mt-1 overflow-x-auto whitespace-pre-wrap">
                        {q.details.compilation.fixed_results.stderr}
                      </pre>
                    </div>
                  )}

                  {/* SQL Validation (for db_schema questions) */}
                  {q.details?.sql_validation && (
                    <div className={`mt-3 p-3 rounded ${q.details.sql_validation.valid_syntax ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                      <strong className={`text-sm ${q.details.sql_validation.valid_syntax ? 'text-green-800' : 'text-red-800'}`}>
                        SQL Syntax: {q.details.sql_validation.valid_syntax ? '✅ Valid' : '❌ Invalid'}
                      </strong>
                      {q.details.sql_validation.error && (
                        <pre className="text-xs text-red-700 mt-1 overflow-x-auto whitespace-pre-wrap">
                          {q.details.sql_validation.error}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Restart Option */}
          <div className="text-center mt-8">
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              🔄 Start New Coding Interview
            </button>
          </div>
        </div>
      )}

      {/* Fallback: Interview Complete without Evaluation */}
      {interviewComplete && !evaluationResults && !isEvaluating && !securityViolation && (
        <div className="mt-6 w-full max-w-4xl space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-green-600">🎉 Coding Interview Complete!</h2>
            <p className="text-gray-600 mt-2">
              You successfully completed all {totalQuestions} coding challenges
            </p>
            <p className="text-sm text-yellow-600 mt-2">
              Evaluation results will be available shortly...
            </p>
          </div>

          {/* Restart Option */}
          <div className="text-center mt-8">
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              🔄 Start New Coding Interview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CodingInterviewer;