import { useState } from "react";
import { Alert, Button } from "react-bootstrap";
import { exportProject } from "../services/api";

type Props = { projectId: string };

export default function ExportPanel({ projectId }: Props) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const result = await exportProject(projectId);
      setMessage(
        `已导出 schema ${result.package.manifest.schema_version}，内容版本 ${result.package.manifest.content_version}。目录：${result.export_dir}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <p className="text-muted">导出前必须通过校验。失败时后端返回 409 export_blocked。</p>
      <Button variant="dark" onClick={() => void run()} disabled={loading}>
        {loading ? "导出中…" : "导出游戏数据包"}
      </Button>
      {error ? <Alert variant="danger" className="mt-3">{error}</Alert> : null}
      {message ? <Alert variant="success" className="mt-3">{message}</Alert> : null}
    </>
  );
}
