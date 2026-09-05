import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Navigation from "./components/Navbar";
import Home from "./pages/Home";
import ProjectWorkspace from "./pages/ProjectWorkspace";
import Welcome from "./pages/Welcome";

function App() {
  return (
    <Router>
      <Navigation />
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/home" element={<Home />} />
        <Route path="/projects/:projectId" element={<ProjectWorkspace />} />
      </Routes>
    </Router>
  );
}

export default App;
