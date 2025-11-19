import React, { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import DisqualificationScreen from './DisqualificationScreen';
import WarningBanner from './WarningBanner';
import axios from 'axios';

const SecurityMonitor = forwardRef(({
  children,
  enabled = true,
  onViolation,
  onWarning,
  interviewType = 'text'
}, ref) => {
  const [fullscreenActive, setFullscreenActive] = useState(false);
  const [isDisqualified, setIsDisqualified] = useState(false);
  const [violationDetails, setViolationDetails] = useState(null);
  const [violationCount, setViolationCount] = useState(0);
  const [showWarning, setShowWarning] = useState(false);
  const [allViolations, setAllViolations] = useState([]);

  const monitorIntervalRef = useRef(null);
  const sessionIdRef = useRef(`${interviewType}-${Date.now()}`);
  const violationCountRef = useRef(0); // Use ref for reliable counting (avoids stale closures)
  const lastViolationTimeRef = useRef(0); // Use ref for synchronous cooldown check (avoids race conditions)

  // Cooldown period to prevent re-detection of same violation (3 seconds)
  const COOLDOWN_PERIOD = 3000;

  // Monitor fullscreen status
  const startMonitoring = () => {
    // Check every 100ms
    monitorIntervalRef.current = setInterval(() => {
      if (!document.fullscreenElement && !isDisqualified) {
        handleViolation('fullscreen_exit');
      }
    }, 100);
  };

  // Stop monitoring
  const stopMonitoring = () => {
    if (monitorIntervalRef.current) {
      clearInterval(monitorIntervalRef.current);
      monitorIntervalRef.current = null;
    }
  };

  // Handle fullscreen change events
  const handleFullscreenChange = () => {
    const isCurrentlyFullscreen = !!document.fullscreenElement;
    setFullscreenActive(isCurrentlyFullscreen);

    // If we exited fullscreen, trigger violation
    if (!isCurrentlyFullscreen && !isDisqualified) {
      handleViolation('fullscreen_exit');
    }
  };

  // Handle right-click context menu
  const handleContextMenu = (event) => {
    event.preventDefault();
    event.stopPropagation();
    handleViolation('right_click');
  };

  // Handle copy attempts
  const handleCopy = (event) => {
    event.preventDefault();
    event.stopPropagation();
    handleViolation('copy_attempt');
  };

  // Handle paste attempts
  const handlePaste = (event) => {
    event.preventDefault();
    event.stopPropagation();
    handleViolation('paste_attempt');
  };

  // Handle cut attempts
  const handleCut = (event) => {
    event.preventDefault();
    event.stopPropagation();
    handleViolation('cut_attempt');
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (event) => {
    // Helper to check Ctrl (Windows) or Cmd (Mac)
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;

    // F12 - DevTools
    if (event.key === 'F12') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('devtools_attempt');
      return;
    }

    // Ctrl+Shift+I or Cmd+Option+I - DevTools
    if (isCtrlOrCmd && event.shiftKey && event.key === 'I') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('devtools_attempt');
      return;
    }

    // Ctrl+Shift+J or Cmd+Option+J - Console
    if (isCtrlOrCmd && event.shiftKey && event.key === 'J') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('devtools_attempt');
      return;
    }

    // Ctrl+Shift+C or Cmd+Option+C - Element Picker
    if (isCtrlOrCmd && event.shiftKey && event.key === 'C') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('devtools_attempt');
      return;
    }

    // Ctrl+U or Cmd+U - View Source
    if (isCtrlOrCmd && event.key === 'u') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('view_source_attempt');
      return;
    }

    // Ctrl+S or Cmd+S - Save Page
    if (isCtrlOrCmd && event.key === 's') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('save_page_attempt');
      return;
    }

    // Ctrl+C or Cmd+C - Copy (keyboard shortcut)
    if (isCtrlOrCmd && event.key === 'c' && !event.shiftKey) {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('copy_attempt');
      return;
    }

    // Ctrl+V or Cmd+V - Paste (keyboard shortcut)
    if (isCtrlOrCmd && event.key === 'v') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('paste_attempt');
      return;
    }

    // Ctrl+X or Cmd+X - Cut (keyboard shortcut)
    if (isCtrlOrCmd && event.key === 'x') {
      event.preventDefault();
      event.stopPropagation();
      handleViolation('cut_attempt');
      return;
    }
  };

  // Handle security violation
  const handleViolation = (type) => {
    // Check cooldown period to prevent re-detection of same violation
    const now = Date.now();
    if (now - lastViolationTimeRef.current < COOLDOWN_PERIOD) {
      console.log(`Violation "${type}" ignored - within cooldown period`);
      return; // Ignore if within cooldown
    }

    // Use ref for reliable counting (avoids stale closure issues with state)
    const newCount = violationCountRef.current + 1;
    violationCountRef.current = newCount; // Update ref synchronously
    console.log(`Security violation detected: ${type} (count: ${newCount})`);

    // Update last violation time (synchronous ref update prevents race conditions)
    lastViolationTimeRef.current = now;

    const details = {
      type,
      timestamp: new Date().toISOString(),
      sessionId: sessionIdRef.current,
      interviewType,
      violationCount: newCount,
      isWarning: newCount === 1
    };

    // Store all violations
    setAllViolations(prev => [...prev, details]);

    if (newCount === 1) {
      // First violation: Show warning
      setViolationCount(1); // Update state for UI
      setViolationDetails(details);
      setShowWarning(true);

      // Log to backend
      logViolationToBackend(details);

      // Call parent warning callback if provided
      if (onWarning) {
        onWarning(details);
      }
    } else {
      // Second violation: Disqualification
      setViolationCount(2); // Update state for UI
      setViolationDetails(details);
      setIsDisqualified(true);
      stopMonitoring();

      // Log to backend
      logViolationToBackend(details);

      // Call parent violation callback if provided
      if (onViolation) {
        onViolation({ ...details, allViolations: [...allViolations, details] });
      }
    }
  };

  // Log violation to backend
  const logViolationToBackend = async (details) => {
    try {
      await axios.post(
        'http://127.0.0.1:5000/api/security/violation',
        details,
        {
          withCredentials: true,
          headers: { 'Content-Type': 'application/json' }
        }
      );
      console.log('Violation logged to backend');
    } catch (error) {
      console.error('Failed to log violation:', error);
      // Don't block disqualification if logging fails
    }
  };

  // Expose stopSecurity method to parent via ref
  useImperativeHandle(ref, () => ({
    stopSecurity: () => {
      console.log('Stopping security monitoring...');

      // FIRST: Remove all event listeners to prevent violation detection during cleanup
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
      document.removeEventListener('cut', handleCut);
      document.removeEventListener('keydown', handleKeyDown);

      // SECOND: Stop interval monitoring
      stopMonitoring();

      // THIRD: Now safe to exit fullscreen (no listeners will fire)
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(err => console.error('Error exiting fullscreen:', err));
      }
    }
  }));

  // Setup and cleanup event listeners
  useEffect(() => {
    if (!enabled) return;

    // Start monitoring immediately when enabled
    startMonitoring();
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    // Add new security event listeners
    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('copy', handleCopy);
    document.addEventListener('paste', handlePaste);
    document.addEventListener('cut', handleCut);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);

      // Cleanup new event listeners
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
      document.removeEventListener('cut', handleCut);
      document.removeEventListener('keydown', handleKeyDown);

      stopMonitoring();

      // Exit fullscreen on cleanup
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(err => console.error(err));
      }
    };
  }, [enabled, isDisqualified]);

  // If security is disabled, render children directly
  if (!enabled) {
    return <>{children}</>;
  }

  // Show disqualification screen if violated
  if (isDisqualified) {
    return (
      <DisqualificationScreen
        violationDetails={violationDetails}
        allViolations={allViolations}
        interviewType={interviewType}
      />
    );
  }

  // Render interview with warning banner if needed
  return (
    <>
      {showWarning && (
        <WarningBanner
          violationDetails={violationDetails}
          interviewType={interviewType}
          onDismiss={() => setShowWarning(false)}
        />
      )}
      {children}
    </>
  );
});

export default SecurityMonitor;
