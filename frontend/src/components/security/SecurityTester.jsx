import React, { useState } from 'react';
import SecurityMonitor from './SecurityMonitor';

/**
 * SecurityTester Component
 *
 * A test harness for the SecurityMonitor component.
 * This allows you to test the fullscreen security system independently.
 *
 * Usage:
 * 1. Import this component in Router.jsx temporarily
 * 2. Add a route to access it (e.g., /security-test)
 * 3. Test all security features
 * 4. Remove after verification
 */
const SecurityTester = () => {
  const [interviewType, setInterviewType] = useState('text');
  const [testStarted, setTestStarted] = useState(false);
  const [violationLog, setViolationLog] = useState([]);

  const handleViolation = (details) => {
    console.log('Violation detected in tester:', details);
    setViolationLog(prev => [...prev, details]);
  };

  const handleStartTest = () => {
    setTestStarted(true);
  };

  const handleReset = () => {
    setTestStarted(false);
    setViolationLog([]);
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  };

  if (!testStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Security System Tester
          </h1>
          <p className="text-gray-600 mb-6">
            Test the fullscreen security monitor before integrating it into interviews.
          </p>

          {/* Interview Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select Interview Type:
            </label>
            <div className="space-y-2">
              <label className="flex items-center p-3 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-blue-400 transition">
                <input
                  type="radio"
                  name="interviewType"
                  value="text"
                  checked={interviewType === 'text'}
                  onChange={(e) => setInterviewType(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-semibold text-gray-800">Text Interview</div>
                  <div className="text-sm text-gray-500">Blue theme</div>
                </div>
              </label>

              <label className="flex items-center p-3 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-purple-400 transition">
                <input
                  type="radio"
                  name="interviewType"
                  value="oral"
                  checked={interviewType === 'oral'}
                  onChange={(e) => setInterviewType(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-semibold text-gray-800">Oral Interview</div>
                  <div className="text-sm text-gray-500">Purple theme</div>
                </div>
              </label>

              <label className="flex items-center p-3 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-green-400 transition">
                <input
                  type="radio"
                  name="interviewType"
                  value="coding"
                  checked={interviewType === 'coding'}
                  onChange={(e) => setInterviewType(e.target.value)}
                  className="mr-3"
                />
                <div>
                  <div className="font-semibold text-gray-800">Coding Interview</div>
                  <div className="text-sm text-gray-500">Green theme</div>
                </div>
              </label>
            </div>
          </div>

          {/* Test Instructions */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <h3 className="font-semibold text-yellow-800 mb-2">Test Instructions:</h3>
            <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
              <li>Click "Start Test" below</li>
              <li>You'll see the security warning modal</li>
              <li>Click "I Accept - Start Interview"</li>
              <li>Browser will enter fullscreen</li>
              <li>You'll see the test content</li>
              <li>Press ESC to test violation detection</li>
              <li>Verify disqualification screen appears</li>
            </ol>
          </div>

          {/* Start Button */}
          <button
            onClick={handleStartTest}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl transition duration-200 text-lg shadow-lg"
          >
            Start Test
          </button>

          {/* Violation Log */}
          {violationLog.length > 0 && (
            <div className="mt-6 p-4 bg-red-50 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-2">Violation Log:</h3>
              <ul className="text-sm text-red-700 space-y-1">
                {violationLog.map((v, idx) => (
                  <li key={idx} className="flex items-center justify-between">
                    <span>{v.type}</span>
                    <span className="text-xs">{new Date(v.timestamp).toLocaleTimeString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <SecurityMonitor
      enabled={true}
      onViolation={handleViolation}
      interviewType={interviewType}
    >
      {/* Mock Interview Content */}
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full">
          <div className="text-center mb-6">
            <div className="w-20 h-20 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
              <svg
                className="w-12 h-12 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              ✅ Fullscreen Security Active
            </h2>
            <p className="text-gray-600">
              Interview Type: <span className="font-semibold capitalize">{interviewType}</span>
            </p>
          </div>

          {/* Test Content */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">
              Mock Interview Question
            </h3>
            <p className="text-gray-700 mb-4">
              This is a test question to simulate interview content. The security monitor is
              now active and watching for fullscreen violations.
            </p>
            <textarea
              className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-400 focus:outline-none"
              rows="4"
              placeholder="Type your answer here..."
            />
          </div>

          {/* Test Instructions */}
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <h4 className="font-semibold text-blue-800 mb-2">🧪 Testing Instructions:</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• You are currently in fullscreen mode</li>
              <li>• Try pressing <kbd className="px-2 py-1 bg-white rounded">ESC</kbd> to test violation detection</li>
              <li>• Try pressing <kbd className="px-2 py-1 bg-white rounded">F11</kbd> to test another violation</li>
              <li>• You should be immediately disqualified</li>
            </ul>
          </div>

          {/* Status Indicators */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">✓</div>
              <div className="text-sm text-gray-600 mt-1">Fullscreen Active</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">✓</div>
              <div className="text-sm text-gray-600 mt-1">Monitoring Active</div>
            </div>
          </div>

          {/* Reset Button */}
          <button
            onClick={handleReset}
            className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-xl transition duration-200"
          >
            Exit Test & Reset
          </button>

          {/* Footer */}
          <p className="text-xs text-center text-gray-500 mt-4">
            Press ESC to trigger a security violation and test the disqualification screen
          </p>
        </div>
      </div>
    </SecurityMonitor>
  );
};

export default SecurityTester;
