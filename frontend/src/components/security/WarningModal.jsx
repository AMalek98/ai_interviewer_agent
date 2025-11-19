import React from 'react';

const WarningModal = ({ onAccept, interviewType = 'text' }) => {
  const getColorClasses = () => {
    switch (interviewType) {
      case 'text':
        return {
          iconBg: 'bg-blue-100',
          iconText: 'text-blue-600',
          button: 'bg-blue-600 hover:bg-blue-700'
        };
      case 'oral':
        return {
          iconBg: 'bg-purple-100',
          iconText: 'text-purple-600',
          button: 'bg-purple-600 hover:bg-purple-700'
        };
      case 'coding':
        return {
          iconBg: 'bg-green-100',
          iconText: 'text-green-600',
          button: 'bg-green-600 hover:bg-green-700'
        };
      default:
        return {
          iconBg: 'bg-blue-100',
          iconText: 'text-blue-600',
          button: 'bg-blue-600 hover:bg-blue-700'
        };
    }
  };

  const colors = getColorClasses();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        {/* Icon */}
        <div className={`w-20 h-20 mx-auto mb-6 ${colors.iconBg} rounded-full flex items-center justify-center`}>
          <svg
            className={`w-12 h-12 ${colors.iconText}`}
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
        </div>

        {/* Title */}
        <h2 className="text-3xl font-bold text-gray-800 mb-4 text-center">
          Interview Security Notice
        </h2>

        {/* Message */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6 border-l-4 border-red-500">
          <p className="text-gray-700 text-lg leading-relaxed mb-3">
            This interview <span className="font-bold text-red-600">must be completed in fullscreen mode</span>.
          </p>
          <p className="text-gray-700 text-base leading-relaxed">
            Exiting fullscreen for any reason will result in <span className="font-bold text-red-600">immediate disqualification</span> with no option to resume.
          </p>
        </div>

        {/* Requirements List */}
        <div className="mb-6 text-left">
          <p className="font-semibold text-gray-800 mb-2">Requirements:</p>
          <ul className="text-sm text-gray-600 space-y-1">
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not press ESC or F11</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not switch tabs or windows</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not minimize your browser</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Stay in fullscreen until the interview ends</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not use copy, paste, or cut (Ctrl+C/V/X or Cmd+C/V/X)</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not right-click anywhere on the page</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not open browser developer tools (F12 or Ctrl+Shift+I)</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not attempt to view source code (Ctrl+U)</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-500 mr-2">•</span>
              <span>Do not attempt to save the page (Ctrl+S)</span>
            </li>
          </ul>
        </div>

        {/* Accept Button */}
        <button
          onClick={onAccept}
          className={`w-full ${colors.button} text-white font-bold py-4 px-6 rounded-xl transition duration-200 text-lg shadow-lg hover:shadow-xl transform hover:scale-105`}
        >
          I Accept - Start Interview
        </button>

        {/* Footer */}
        <p className="text-xs text-gray-500 text-center mt-4">
          By clicking "I Accept", you agree to these security terms
        </p>
      </div>
    </div>
  );
};

export default WarningModal;
