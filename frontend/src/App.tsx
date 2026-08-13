import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadPage from './pages/UploadPage';
import RedactionPage from './pages/RedactionPage';
import ReleasePage from './pages/ReleasePage';
import ReportPage from './pages/ReportPage';

/**
 * PII Redaction Tool — Case-File Redaction System
 *
 * Routes:
 * /                  → Case Intake Desk (Upload)
 * /redaction/:id     → Redaction Worksheet
 * /release/:id       → Document Ready (Release)
 * /report/:id        → Evaluation Report
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Report page has its own layout (matching Stitch design) */}
        <Route path="/report/:id" element={<ReportPage />} />

        {/* All other pages share the standard layout */}
