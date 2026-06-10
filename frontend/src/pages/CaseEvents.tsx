import { Navigate, useParams } from "react-router-dom";

export function CaseEventsPage() {
  const { caseId } = useParams<{ caseId: string }>();
  if (!caseId) {
    return null;
  }
  return <Navigate to={`/cases/${caseId}/timeline`} replace />;
}
