import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import { CaseDetailPage } from "./pages/CaseDetail";
import { CaseUploadPage } from "./pages/CaseUpload";
import { ReviewQueuePage } from "./pages/ReviewQueue";
import { ArtifactDetailPage } from "./pages/ArtifactDetail";
import { CaseEventsPage } from "./pages/CaseEvents";
import { AssistantPage } from "./pages/Assistant";
import { AuditLogPage } from "./pages/AuditLog";
import { ClaimsPage } from "./pages/Claims";
import { ReportPage } from "./pages/Report";
import { TimelinePage } from "./pages/Timeline";
import { CasesPage } from "./pages/Cases";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/Login";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="cases" element={<CasesPage />} />
          <Route path="cases/:caseId" element={<CaseDetailPage />} />
          <Route path="cases/:caseId/upload" element={<CaseUploadPage />} />
          <Route path="cases/:caseId/review" element={<ReviewQueuePage />} />
          <Route
            path="cases/:caseId/artifacts/:artifactId"
            element={<ArtifactDetailPage />}
          />
          <Route path="cases/:caseId/timeline" element={<TimelinePage />} />
          <Route path="cases/:caseId/claims" element={<ClaimsPage />} />
          <Route path="cases/:caseId/assistant" element={<AssistantPage />} />
          <Route path="cases/:caseId/report" element={<ReportPage />} />
          <Route path="cases/:caseId/audit" element={<AuditLogPage />} />
          <Route path="cases/:caseId/events" element={<CaseEventsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
