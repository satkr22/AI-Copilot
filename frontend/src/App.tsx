import { useEffect, useState } from "react";

const API = import.meta.env.VITE_BACKEND_API_URL;

type User = {
  id: string;
  name: string;
  email: string;
};

type Project = {
  id: string;
  name: string;
  description?: string;
  repository_id: string | null;
  status: string;
};

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [mode, setMode] = useState<"login" | "register">("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");

  const [message, setMessage] = useState("");

  // ---------- helper ----------
  const authFetch = async (url: string, options: RequestInit = {}) => {
    const token = localStorage.getItem("token");

    return fetch(`${API}${url}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });
  };

  // ---------- check existing login ----------
  useEffect(() => {
    const checkLogin = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      const res = await authFetch("/auth/me");

      if (!res.ok) {
        localStorage.removeItem("token");
        return;
      }

      const me = await res.json();
      setUser(me);

      loadProjects();
    };

    checkLogin();
  }, []);

  // ---------- load projects ----------
  const loadProjects = async () => {
    const res = await authFetch("/projects");

    if (!res.ok) return;

    const data = await res.json();
    setProjects(data);
  };

  // ---------- register ----------
  const register = async () => {
    const res = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        email,
      }),
    });

    if (!res.ok) {
      setMessage("Registration failed");
      return;
    }

    setMessage("Registered successfully. Please login.");
    setMode("login");
    setName("");
    setEmail("");
    setMessage("Registered successfully. Please login.");
  };

  // ---------- login ----------
  const login = async () => {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      setMessage("Invalid user");
      return;
    }

    const data = await res.json();

    localStorage.setItem("token", data.access_token);

    setUser(data.user);

    await loadProjects();
  };

  // ---------- logout ----------
  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setProjects([]);
    setEmail("");
    setName("");
  };

  // ---------- create project ----------
  const createProject = async () => {
    const res = await authFetch("/projects", {
      method: "POST",
      body: JSON.stringify({
        name: projectName,
        description,
      }),
    });

    if (!res.ok) {
      setMessage("Unable to create project");
      return;
    }

    const newProject: Project = await res.json();

    setProjects((prev) => [...prev, newProject]);

    setProjectName("");
    setDescription("");
  };

  // ==========================================================
  // LOGIN / REGISTER PAGE
  // ==========================================================

  if (!user) {
    return (
      <main style={styles.container}>
        <h1>AI Copilot</h1>

        <div style={styles.card}>
          <div style={styles.tabs}>
            <button
              onClick={() => setMode("login")}
              style={mode === "login" ? styles.active : styles.tab}
            >
              Login
            </button>

            <button
              onClick={() => setMode("register")}
              style={mode === "register" ? styles.active : styles.tab}
            >
              Register
            </button>
          </div>

          {mode === "register" && (
            <input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={styles.input}
            />
          )}

          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
          />

          {mode === "login" ? (
            <button onClick={login} style={styles.primary}>
              Login
            </button>
          ) : (
            <button onClick={register} style={styles.primary}>
              Register
            </button>
          )}

          <p>{message}</p>
        </div>
      </main>
    );
  }

  // ==========================================================
  // DASHBOARD
  // ==========================================================

  return (
    <main style={styles.container}>
      <div style={styles.header}>
        <div>
          <h2>Welcome {user.name}</h2>
          <p>{user.email}</p>
        </div>

        <button onClick={logout}>Logout</button>
      </div>

      <div style={styles.card}>
        <h3>Create Project</h3>

        <input
          placeholder="Project Name"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          style={styles.input}
        />

        <input
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={styles.input}
        />

        <button onClick={createProject} style={styles.primary}>
          Create
        </button>
      </div>

      <div style={styles.card}>
        <h3>My Projects</h3>

        {projects.length === 0 ? (
          <p>No projects yet.</p>
        ) : (
          projects.map((p) => (
            <div key={p.id} style={styles.project}>
              <strong>{p.name}</strong>
              <p>{p.description}</p>
              <small>{p.status}</small>
            </div>
          ))
        )}
      </div>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 700,
    margin: "40px auto",
    fontFamily: "Arial",
  },

  card: {
    border: "1px solid #ddd",
    padding: 20,
    borderRadius: 10,
    marginTop: 20,
  },

  input: {
    width: "100%",
    padding: 10,
    marginTop: 10,
    boxSizing: "border-box",
  },

  primary: {
    marginTop: 15,
    width: "100%",
    padding: 10,
    cursor: "pointer",
  },

  tabs: {
    display: "flex",
    gap: 10,
    marginBottom: 15,
  },

  tab: {
    flex: 1,
    padding: 10,
  },

  active: {
    flex: 1,
    padding: 10,
    background: "#333",
    color: "white",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  project: {
    borderTop: "1px solid #eee",
    padding: "10px 0",
  },
};