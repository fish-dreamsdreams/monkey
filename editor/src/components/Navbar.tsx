import { Container, Nav, Navbar } from "react-bootstrap";
import { Link } from "react-router-dom";

export default function Navigation() {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand as={Link} to="/">
          三国内容编辑器
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="editor-nav" />
        <Navbar.Collapse id="editor-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">
              欢迎
            </Nav.Link>
            <Nav.Link as={Link} to="/home">
              项目
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
