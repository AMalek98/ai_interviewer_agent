import React from 'react';

const WarningBanner = ({ violationDetails, interviewType, onDismiss }) => {
  // Handle dismiss and auto-restore fullscreen
  const handleDismiss = async () => {
    try {
      // Attempt to restore fullscreen mode automatically
      await document.documentElement.requestFullscreen();
      console.log('Fullscreen restored successfully');
    } catch (err) {
      console.warn('Could not automatically restore fullscreen:', err.message);
      // Continue even if fullscreen restoration fails
      // The user can manually restore it, and the cooldown will prevent immediate re-violation
    }

    // Call the parent dismiss callback
    onDismiss();
  };

  // Get user-friendly violation message
  const getViolationMessage = (type) => {
    const messages = {
      'fullscreen_exit': 'You exited fullscreen mode',
      'copy_attempt': 'You attempted to copy content (Ctrl+C or Cmd+C)',
      'paste_attempt': 'You attempted to paste content (Ctrl+V or Cmd+V)',
      'cut_attempt': 'You attempted to cut content (Ctrl+X or Cmd+X)',
      'right_click': 'You right-clicked to open the context menu',
      'devtools_attempt': 'You attempted to open browser developer tools',
      'view_source_attempt': 'You attempted to view page source (Ctrl+U or Cmd+U)',
      'save_page_attempt': 'You attempted to save the page (Ctrl+S or Cmd+S)'
    };
    return messages[type] || `Security violation detected: ${type}`;
  };

  // Get theme colors based on interview type
  const getThemeColors = () => {
    switch (interviewType) {
      case 'text':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-400',
          text: 'text-yellow-800',
          icon: 'text-yellow-600',
          button: 'bg-yellow-600 hover:bg-yellow-700'
        };
      case 'oral':
        return {
          bg: 'bg-orange-50',
          border: 'border-orange-400',
          text: 'text-orange-800',
          icon: 'text-orange-600',
          button: 'bg-orange-600 hover:bg-orange-700'
        };
      case 'coding':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-400',
          text: 'text-amber-800',
          icon: 'text-amber-600',
          button: 'bg-amber-600 hover:bg-amber-700'
        };
      default:
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-400',
          text: 'text-yellow-800',
          icon: 'text-yellow-600',
          button: 'bg-yellow-600 hover:bg-yellow-700'
        };
    }
  };

  const theme = getThemeColors();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className={`${theme.bg} ${theme.border} border-4 rounded-lg shadow-2xl max-w-2xl w-full p-8 animate-pulse-slow`}>
        {/* Warning Icon and Title */}
        <div className="flex items-center justify-center mb-6">
          <svg
            className={`w-16 h-16 ${theme.icon} mr-4`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className={`text-3xl font-bold ${theme.text}`}>SECURITY VIOLATION WARNING</h2>
        </div>

        {/* Violation Details */}
        <div className={`${theme.text} mb-6`}>
          <p className="text-xl font-semibold mb-4">
            Violation Detected: {getViolationMessage(violationDetails?.type)}
          </p>

          <div className="bg-white bg-opacity-70 rounded-lg p-4 mb-4">
            <p className="text-lg font-bold mb-2">This is your first and only warning.</p>
            <p className="text-lg">Warning Count: <span className="font-bold">1 of 1 remaining</span></p>
          </div>
        </div>

        {/* Important Notice */}
        <div className={`${theme.text} bg-white bg-opacity-70 rounded-lg p-6 mb-6`}>
          <p className="font-bold text-xl mb-3 flex items-center">
            <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            IMPORTANT - READ CAREFULLY:
          </p>
          <ul className="space-y-2 text-base">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span><strong>A second violation of ANY type will result in immediate disqualification</strong></span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Your interview will be terminated with no option to resume</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>All your responses up to the disqualification point will be saved</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>The violation will be logged and reported</span>
            </li>
          </ul>
        </div>

        {/* Instructions */}
        <div className={`${theme.text} bg-white bg-opacity-70 rounded-lg p-4 mb-6`}>
          <p className="text-lg font-semibold">
            Please comply with all security requirements and continue your interview carefully.
          </p>
        </div>

        {/* Dismiss Button */}
        <div className="flex justify-center">
          <button
            onClick={handleDismiss}
            className={`${theme.button} text-white font-bold py-4 px-8 rounded-lg text-xl transition duration-200 shadow-lg hover:shadow-xl transform hover:scale-105`}
          >
            I Understand and Will Comply
          </button>
        </div>
      </div>
    </div>
  );
};

export default WarningBanner;
