import React from 'react';

const DisqualificationScreen = ({ violationDetails, allViolations = [], interviewType = 'text' }) => {
  const formatTime = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getViolationMessage = (type) => {
    switch (type) {
      case 'fullscreen_exit':
        return 'You exited fullscreen mode';
      case 'tab_switch':
        return 'You switched tabs or windows';
      case 'esc_key':
        return 'You pressed the ESC key';
      case 'copy_attempt':
        return 'You attempted to copy content (Ctrl+C or Cmd+C)';
      case 'paste_attempt':
        return 'You attempted to paste content (Ctrl+V or Cmd+V)';
      case 'cut_attempt':
        return 'You attempted to cut content (Ctrl+X or Cmd+X)';
      case 'right_click':
        return 'You right-clicked during the interview';
      case 'devtools_attempt':
        return 'You attempted to open browser developer tools';
      case 'view_source_attempt':
        return 'You attempted to view the page source code';
      case 'save_page_attempt':
        return 'You attempted to save the page';
      default:
        return 'A security violation was detected';
    }
  };

  const handleReturnHome = () => {
    // Exit fullscreen if still active
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(err => console.error(err));
    }
    // Reload to return to interview selection
    window.location.href = '/';
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-red-900 via-red-800 to-red-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-10 max-w-lg w-full text-center">
        {/* Icon */}
        <div className="w-24 h-24 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
          <svg
            className="w-16 h-16 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
            />
          </svg>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-bold text-red-600 mb-4">
          Security Violations Detected ({allViolations.length > 0 ? allViolations.length : violationDetails?.violationCount || 2})
        </h1>

        {/* Violation Messages */}
        {allViolations.length > 0 ? (
          <div className="space-y-3 mb-6">
            {allViolations.map((violation, index) => (
              <div key={index} className="bg-red-50 rounded-lg p-4 border-2 border-red-200">
                <p className="text-lg text-gray-800 font-semibold mb-1">
                  Violation {index + 1}: {getViolationMessage(violation.type)}
                </p>
                <p className="text-sm text-gray-600">
                  Time: {formatTime(violation.timestamp)}
                  {violation.isWarning && <span className="ml-2 text-yellow-600 font-semibold">(Warning)</span>}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-red-50 rounded-lg p-6 mb-6 border-2 border-red-200">
            <p className="text-xl text-gray-800 font-semibold mb-2">
              {getViolationMessage(violationDetails?.type)}
            </p>
            <p className="text-sm text-gray-600">
              Time: {formatTime(violationDetails?.timestamp)}
            </p>
          </div>
        )}

        {/* Status Messages */}
        <div className="space-y-3 mb-8 text-left bg-gray-50 rounded-lg p-6">
          <div className="flex items-start">
            <span className="text-red-500 mr-3 text-xl">✗</span>
            <p className="text-gray-700 font-medium">This interview has been terminated</p>
          </div>
          <div className="flex items-start">
            <span className="text-green-500 mr-3 text-xl">✓</span>
            <p className="text-gray-700 font-medium">Your partial responses have been saved</p>
          </div>
          <div className="flex items-start">
            <span className="text-red-500 mr-3 text-xl">✗</span>
            <p className="text-gray-700 font-medium">You cannot resume this interview</p>
          </div>
          <div className="flex items-start">
            <span className="text-yellow-500 mr-3 text-xl">⚠</span>
            <p className="text-gray-700 font-medium">Violations have been logged and will be reported</p>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={handleReturnHome}
          className="w-full bg-gray-700 hover:bg-gray-800 text-white font-bold py-4 px-6 rounded-xl transition duration-200 text-lg shadow-lg"
        >
          Return to Home
        </button>

        {/* Footer */}
        <p className="text-sm text-gray-500 mt-6">
          Contact support if you believe this is an error
        </p>
      </div>
    </div>
  );
};

export default DisqualificationScreen;
