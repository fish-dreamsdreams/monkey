import { useEffect, useState, type FormEvent } from "react";
import { Alert, Button, Card, Col, Container, Form, Row, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import { createProject, listProjects, type Project } from "../services/api";

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("东汉末年");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = () =>
    listProjects()
      .then(setProjects)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));

  useEffect(() => {
    void refresh();
  }, []);

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await createProject(name.trim());
      setName("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    }
  };

  return (
    <Container className="page-shell">
      <h1 className="mb-3">项目</h1>
      {error ? <Alert variant="danger">{error}</Alert> : null}
      <Card className="mb-4">
        <Card.Body>
          <Form onSubmit={(event) => void onCreate(event)} className="d-flex gap-2">
            <Form.Control
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="项目名称"
              required
            />
            <Button type="submit" variant="dark">
              新建
            </Button>
          </Form>
        </Card.Body>
      </Card>
      {loading ? (
        <Spinner animation="border" />
      ) : (
        <Row xs={1} md={2} className="g-3">
          {projects.map((project) => (
            <Col key={project.id}>
              <Card>
                <Card.Body>
                  <Card.Title>{project.name}</Card.Title>
                  <Card.Text className="text-muted small">
                    {project.code} · schema {project.schema_version} · v{project.content_version}
                  </Card.Text>
                  <Link to={`/projects/${project.id}`}>
                    <Button variant="outline-dark" size="sm">
                      打开
                    </Button>
                  </Link>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </Container>
  );
}
