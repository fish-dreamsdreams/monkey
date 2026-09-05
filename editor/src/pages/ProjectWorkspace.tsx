import { useEffect, useState } from "react";
import { Alert, Container, Nav, Spinner } from "react-bootstrap";
import { useParams } from "react-router-dom";
import CharacterPanel from "../editors/CharacterPanel";
import ExportPanel from "../editors/ExportPanel";
import ValidationPanel from "../editors/ValidationPanel";
import { getProject, type Project } from "../services/api";

type Tab = "characters" | "validation" | "export";

export default function ProjectWorkspace() {
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("characters");

  useEffect(() => {
    if (!projectId) return;
    getProject(projectId)
      .then(setProject)
      .catch((err: Error) => setError(err.message));
  }, [projectId]);

  if (!projectId) return <Alert variant="danger">缺少项目</Alert>;
  if (error) {
    return (
      <Container>
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }
  if (!project) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
      </Container>
    );
  }

  return (
    <Container className="page-shell">
      <h1 className="mb-1">{project.name}</h1>
      <p className="text-muted">
        {project.code} · schema {project.schema_version} · 内容版本 {project.content_version}
      </p>
      <Nav variant="tabs" activeKey={tab} onSelect={(key) => setTab((key as Tab) || "characters")} className="mb-3">
        <Nav.Item>
          <Nav.Link eventKey="characters">人物</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link eventKey="validation">校验</Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link eventKey="export">导出</Nav.Link>
        </Nav.Item>
      </Nav>
      {tab === "characters" ? <CharacterPanel projectId={projectId} /> : null}
      {tab === "validation" ? <ValidationPanel projectId={projectId} /> : null}
      {tab === "export" ? <ExportPanel projectId={projectId} /> : null}
    </Container>
  );
}
