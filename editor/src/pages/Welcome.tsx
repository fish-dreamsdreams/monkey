import { useEffect, useState } from "react";
import { Alert, Button, Container, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import { getHealth, type Health } from "../services/api";

export default function Welcome() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: Error) => setError(err.message || "后端未启动"));
  }, []);

  return (
    <Container className="text-center mt-5 page-shell">
      <h1>三国内容编辑器</h1>
      <p className="text-muted">创建、编辑、校验、导出内容数据。战斗与 AI 留给游戏客户端。</p>
      {error ? (
        <Alert variant="warning">无法连接后端：{error}。请先启动 FastAPI（默认 8000 端口）。</Alert>
      ) : health ? (
        <Alert variant="success">
          后端正常 · schema {health.schema_version} · API {health.api_version}
        </Alert>
      ) : (
        <Spinner animation="border" size="sm" />
      )}
      <p className="mt-4">
        <Link to="/home">
          <Button variant="dark">打开项目列表</Button>
        </Link>
      </p>
    </Container>
  );
}
