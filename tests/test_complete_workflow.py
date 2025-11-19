#!/usr/bin/env python3
"""
Test script for complete CV upload and interview workflow
"""

import requests
import json
import os

def test_backend_endpoints():
    """Test the backend endpoints to ensure they work"""
    print("Testing backend endpoints...")

    base_url = "http://127.0.0.1:5000"

    try:
        # Test 1: Check if backend is running
        print("1. Testing backend health...")
        response = requests.get(f"{base_url}/")
        print(f"   Backend accessible: {response.status_code == 200}")

        # Test 2: Test job description file exists
        print("2. Checking job description file...")
        job_desc_path = "uploads/job_description.txt"
        job_desc_exists = os.path.exists(job_desc_path)
        print(f"   Job description exists: {job_desc_exists}")

        # Test 3: Test structured CV file exists (from our previous tests)
        print("3. Checking structured CV file...")
        cv_path = "uploads/structured_cv.json"
        cv_exists = os.path.exists(cv_path)
        print(f"   Structured CV exists: {cv_exists}")

        # Test 4: Try to start interview (should work with existing files)
        print("4. Testing interview start...")
        try:
            response = requests.get(f"{base_url}/start_interview")
            if response.status_code == 200:
                data = response.json()
                print(f"   Interview start successful: {bool(data.get('question'))}")
                print(f"   Question generated: {data.get('question', 'No question')[:100]}...")
            else:
                print(f"   Interview start failed: {response.status_code}")
        except Exception as e:
            print(f"   Interview start error: {e}")

        # Test 5: Frontend accessibility
        print("5. Testing frontend accessibility...")
        try:
            frontend_response = requests.get("http://localhost:5173", timeout=5)
            print(f"   Frontend accessible: {frontend_response.status_code == 200}")
        except requests.exceptions.RequestException:
            print("   Frontend not accessible (might not be running)")

        print("\n✅ Backend testing complete!")
        return True

    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def print_workflow_instructions():
    """Print instructions for manual testing"""
    print("\n" + "="*60)
    print("🚀 MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    print()
    print("1. Open your browser and go to: http://localhost:5173")
    print()
    print("2. You should see the new enhanced UI with:")
    print("   ✅ 'AI Interview Assistant' title")
    print("   ✅ 'Step 1: Upload Your CV (PDF)' section")
    print("   ✅ Drag and drop zone for PDF files")
    print()
    print("3. Test the workflow:")
    print("   a) Try dragging a PDF file to the upload zone")
    print("   b) Or click 'Browse Files' to select a PDF")
    print("   c) Click 'Upload and Process CV'")
    print("   d) Wait for processing completion")
    print("   e) Select a voice from the dropdown")
    print("   f) Click 'Start AI Interview'")
    print("   g) Answer the 3 questions")
    print("   h) View the enhanced interview summary")
    print()
    print("4. Expected improvements:")
    print("   ✅ Questions should reference specific CV content")
    print("   ✅ First question: CV verification focus")
    print("   ✅ Second question: Technical competency")
    print("   ✅ Third question: Behavioral assessment")
    print("   ✅ Enhanced interview summary with CV analysis")
    print()
    print("5. If you need a test PDF CV, create one with:")
    print("   - Your work experience at specific companies")
    print("   - Education details with dates")
    print("   - Technical skills and projects")
    print("   - Specific achievements and metrics")
    print()
    print("="*60)

if __name__ == "__main__":
    test_backend_endpoints()
    print_workflow_instructions()