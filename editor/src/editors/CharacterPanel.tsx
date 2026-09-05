import { useEffect, useState, type FormEvent } from "react";
import { Alert, Button, Form, Table } from "react-bootstrap";
import { createCharacter, listCharacters, type CharacterSummary } from "../services/api";

type Props = { projectId: string };

export default function CharacterPanel({ projectId }: Props) {
  const [items, setItems] = useState<CharacterSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [code, setCode] = useState("chr_liu_bei");
  const [name, setName] = useState("刘备");
  const [courtesyName, setCourtesyName] = useState("玄德");
  const [birthYear, setBirthYear] = useState("161");
  const [deathYear, setDeathYear] = useState("223");

  const refresh = () =>
    listCharacters(projectId)
      .then(setItems)
      .catch((err: Error) => setError(err.message));

  useEffect(() => {
    void refresh();
  }, [projectId]);

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await createCharacter(projectId, {
        base: {
          code,
          name,
          courtesy_name: courtesyName || null,
          gender: "male",
          birth_year: birthYear ? Number(birthYear) : null,
          death_year: deathYear ? Number(deathYear) : null,
        },
        historical: { biography: null },
        game: { force: 72, intelligence: 80, charisma: 95 },
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    }
  };

  return (
    <>
      {error ? <Alert variant="danger">{error}</Alert> : null}
      <Form onSubmit={(event) => void onCreate(event)} className="row g-2 mb-3">
        <Form.Group className="col-md-2">
          <Form.Label>code</Form.Label>
          <Form.Control value={code} onChange={(event) => setCode(event.target.value)} required />
        </Form.Group>
        <Form.Group className="col-md-2">
          <Form.Label>姓名</Form.Label>
          <Form.Control value={name} onChange={(event) => setName(event.target.value)} required />
        </Form.Group>
        <Form.Group className="col-md-2">
          <Form.Label>字</Form.Label>
          <Form.Control value={courtesyName} onChange={(event) => setCourtesyName(event.target.value)} />
        </Form.Group>
        <Form.Group className="col-md-2">
          <Form.Label>生年</Form.Label>
          <Form.Control value={birthYear} onChange={(event) => setBirthYear(event.target.value)} />
        </Form.Group>
        <Form.Group className="col-md-2">
          <Form.Label>卒年</Form.Label>
          <Form.Control value={deathYear} onChange={(event) => setDeathYear(event.target.value)} />
        </Form.Group>
        <Form.Group className="col-md-2 d-flex align-items-end">
          <Button type="submit" variant="dark">
            新增人物
          </Button>
        </Form.Group>
      </Form>
      <Table striped bordered hover size="sm">
        <thead>
          <tr>
            <th>姓名</th>
            <th>字</th>
            <th>code</th>
            <th>生卒</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.courtesy_name || "—"}</td>
              <td>{item.code}</td>
              <td>
                {item.birth_year ?? "?"} – {item.death_year ?? "?"}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </>
  );
}
