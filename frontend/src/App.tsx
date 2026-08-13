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
        <Route element={<Layout />}>
          <Route path="/" element={<UploadPage />} />
          <Route path="/redaction/:id" element={<RedactionPage />} />
          <Route path="/release/:id" element={<ReleasePage />} />

          {/* Placeholder routes for nav items */}
          <Route
            path="/archive"
            element={<PlaceholderPage icon="inventory_2" title="ARCHIVE" />}
          />
          <Route
            path="/evidence"
            element={<PlaceholderPage icon="menu_book" title="EVIDENCE LOG" />}
          />
          <Route
            path="/settings"
            element={<PlaceholderPage icon="settings" title="SETTINGS" />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

/** Simple placeholder for nav routes that aren't the core flow */
function PlaceholderPage({ icon, title }: { icon: string; title: string }) {
  return (
    <div className="p-margin flex items-center justify-center min-h-full">
      <div className="border-2 border-dashed border-outline p-12 bg-fresh-paper text-center">
        <span className="material-symbols-outlined text-6xl text-outline mb-4 block">
          {icon}
        </span>
        <h2 className="font-headline text-headline-md uppercase mb-2 text-ink">
          {title}
        </h2>
        <p className="font-code text-code-sm text-outline">
          This section is under development.
        </p>
      </div>
    </div>
  );
}

