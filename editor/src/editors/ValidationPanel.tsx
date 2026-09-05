import { useState } from "react";
import { Alert, Button, Table } from "react-bootstrap";
import { validateProject, type ValidationReport } from "../services/api";

type Props = { projectId: string };

export default function ValidationPanel({ projectId }: Props) {
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setError(null);
    setLoading(true);
    try {
      setReport(await validateProject(projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "校验失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button variant="dark" onClick={() => void run()} disabled={loading} className="mb-3">
        {loading ? "校验中…" : "运行校验"}
      </Button>
      {error ? <Alert variant="danger">{error}</Alert> : null}
      {report ? (
        <>
          <Alert variant={report.valid ? "success" : "danger"}>
            {report.valid ? "可以导出" : "不能导出"} · error {report.error_count} · warning {report.warning_count}
          </Alert>
          <Table size="sm" bordered>
            <thead>
              <tr>
                <th>级别</th>
                <th>规则</th>
                <th>实体</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {report.issues.map((issue, index) => (
                <tr key={`${issue.rule}-${index}`}>
                  <td>{issue.severity}</td>
                  <td>{issue.rule}</td>
                  <td>
                    {issue.entity_type}
                    {issue.entity_id ? `:${issue.entity_id}` : ""}
                  </td>
                  <td>{issue.message}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      ) : null}
    </>
  );
}
