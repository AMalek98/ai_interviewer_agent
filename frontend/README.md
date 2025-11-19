# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
  
🚀 How to Run

  Method 1: Using Batch Files

  # Terminal 1 - Backend (port 5001)
  start_coding_backend.bat

  # Terminal 2 - Frontend (port 5174)
  start_coding_frontend.bat

  Method 2: Manual Commands

  Terminal 1 - Backend:
  cd backend
  python coding_agent.py
  Runs on: http://localhost:5001

  Terminal 2 - Frontend:
  cd frontend
  npx vite --port 5174 --open /coding.html
  Runs on: http://localhost:5174/coding.html