# Security Components - Phase 1

This directory contains the fullscreen security monitoring system for AI Interviewer.

## Components

### 1. SecurityMonitor.jsx
Main wrapper component that enforces fullscreen mode during interviews.

**Features:**
- Shows warning modal before interview starts
- Requests and monitors fullscreen mode
- Detects violations (ESC key, fullscreen exit)
- Logs violations to backend
- Displays disqualification screen on violation

**Props:**
```jsx
<SecurityMonitor
  enabled={true}              // Enable/disable security
  onViolation={(details) => {}} // Callback when violation occurs
  interviewType="text"        // "text" | "oral" | "coding"
>
  {/* Your interview component */}
</SecurityMonitor>
```

### 2. WarningModal.jsx
Pre-interview warning that explains security requirements.

**Features:**
- Clear security notice
- List of prohibited actions
- Themed styling based on interview type
- "I Accept" button to trigger fullscreen

### 3. DisqualificationScreen.jsx
Full-screen message shown when security violation occurs.

**Features:**
- Shows violation type and timestamp
- Lists consequences (termination, no resume)
- "Return to Home" button
- Red alert theme

### 4. SecurityTester.jsx
Test harness for verifying security components work correctly.

---

## Testing Phase 1 Components

### Step 1: Add Test Route

Edit `frontend/src/Router.jsx` and temporarily add a test route:

```jsx
import SecurityTester from './components/security/SecurityTester';

// Add this state
const [showSecurityTester, setShowSecurityTester] = useState(false);

// Add this button to the selection screen
<button
  onClick={() => setShowSecurityTester(true)}
  className="mt-4 bg-gray-600 text-white px-6 py-3 rounded-lg"
>
  🧪 Test Security System
</button>

// Add this conditional render
{showSecurityTester && <SecurityTester />}
```

### Step 2: Run the Frontend

```bash
cd frontend
npm run dev
```

### Step 3: Test the Components

1. Open browser to `http://localhost:5173`
2. Click "🧪 Test Security System"
3. Select an interview type (Text/Oral/Coding)
4. Click "Start Test"
5. Verify warning modal appears with correct theme color
6. Click "I Accept - Start Interview"
7. Verify browser enters fullscreen
8. Verify test content displays
9. Press **ESC** key
10. Verify disqualification screen appears
11. Click "Return to Home"

### Step 4: Verify Backend Integration

Make sure backend is running:
```bash
cd backend
python main.py
```

Check if violations are logged:
```bash
# Check backend console for:
# [SECURITY] Violation logged: violation-text-20251030_143045.json

# Check the file was created:
ls backend/data/security_logs/
```

---

## Integration Checklist

Before integrating with actual interview components:

- [ ] ✅ Components render without errors
- [ ] ✅ Warning modal displays correctly
- [ ] ✅ Fullscreen request works
- [ ] ✅ Browser enters fullscreen
- [ ] ✅ ESC key triggers violation
- [ ] ✅ F11 key triggers violation
- [ ] ✅ Disqualification screen appears
- [ ] ✅ Backend receives violation log
- [ ] ✅ All three themes work (blue/purple/green)
- [ ] ✅ "Return to Home" button works

---

## Next Steps (Phase 2)

Once Phase 1 testing is complete:

1. Integrate SecurityMonitor into App.jsx (Text Interview)
2. Integrate SecurityMonitor into OralInterview.jsx
3. Integrate SecurityMonitor into CodingInterviewer.jsx
4. Test full interview flow with security
5. Handle edge cases (interview completion, errors)

---

## Common Issues & Solutions

### Issue: Fullscreen request denied
**Solution:** User must interact with the page first. Ensure warning modal button is clicked.

### Issue: Multiple violations logged
**Solution:** Check that monitoring interval is cleared properly when violation occurs.

### Issue: Can't exit fullscreen after interview
**Solution:** Ensure cleanup in useEffect removes fullscreen on component unmount.

### Issue: Tailwind classes not working
**Solution:** Verify Tailwind CSS is properly configured in frontend. Check `tailwind.config.js`.

### Issue: Backend endpoint not found
**Solution:** Add the `/api/security/violation` endpoint to `backend/main.py` (Phase 3).

---

## File Structure

```
frontend/src/components/security/
├── SecurityMonitor.jsx          # Main security wrapper (180 lines)
├── WarningModal.jsx             # Pre-interview warning (115 lines)
├── DisqualificationScreen.jsx   # Violation screen (110 lines)
├── SecurityTester.jsx           # Test component (250 lines)
├── index.js                     # Barrel export (3 lines)
└── README.md                    # This file
```

---

## Dependencies

All dependencies are already in the project:
- React 19.1.0
- Axios 1.9.0 (for backend communication)
- Tailwind CSS 4.1.6 (for styling)

No additional packages needed for Phase 1.

---

## Security Features

✅ **Implemented:**
- Fullscreen enforcement
- Violation detection (ESC, F11, fullscreen exit)
- Warning modal
- Disqualification screen
- Backend logging
- Session tracking
- Interview type tracking

❌ **Not Yet Implemented (Future Phases):**
- Camera/face detection
- Tab switch detection
- DevTools monitoring
- Copy/paste blocking
- Heartbeat system
- Multi-monitor detection

---

## Testing Scenarios

| Scenario | Expected Behavior | Status |
|----------|-------------------|--------|
| Click "I Accept" | Browser requests fullscreen | ⬜ Test |
| Fullscreen granted | Interview content displays | ⬜ Test |
| Press ESC | Disqualification screen shows | ⬜ Test |
| Press F11 | Disqualification screen shows | ⬜ Test |
| Exit fullscreen via browser | Disqualification screen shows | ⬜ Test |
| Click "Return to Home" | Exits fullscreen, returns to / | ⬜ Test |
| Backend receives violation | JSON file created in data/security_logs | ⬜ Test |
| Test all 3 themes | Blue, purple, green colors correct | ⬜ Test |

---

## Troubleshooting

### Browser Compatibility

The Fullscreen API is supported in:
- ✅ Chrome 71+
- ✅ Edge 79+
- ✅ Firefox 64+
- ✅ Safari 16.4+

**Note:** The system is optimized for Google Chrome.

### Debugging

Add these console logs to SecurityMonitor.jsx:

```jsx
useEffect(() => {
  console.log('Security state:', {
    showWarning,
    fullscreenActive,
    isDisqualified,
    interviewStarted
  });
}, [showWarning, fullscreenActive, isDisqualified, interviewStarted]);
```

Check browser console for:
- "Security violation detected: fullscreen_exit"
- "Violation logged to backend"

---

## Phase 1 Status

**Status:** ✅ Complete - Ready for Testing

**Created Files:**
- ✅ SecurityMonitor.jsx
- ✅ WarningModal.jsx
- ✅ DisqualificationScreen.jsx
- ✅ SecurityTester.jsx
- ✅ index.js
- ✅ README.md

**Next:** Test components, then proceed to Phase 2 (Integration)

---

**Last Updated:** 2025-10-30
**Version:** 1.0.0
