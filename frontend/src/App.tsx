import { useEffect, useMemo, useState, type CSSProperties } from "react";

const API = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:9000";

type User = {
  id: string;
  name: string;
  email: string;
};

type Project = {
  id: string;
  name: string;
  description: string | null;
  repository_id: string | null;
  status: string;
};

type Repository = {
  id: string;
  source_type: string;
  source_url: string | null;
  local_path: string | null;
  branch: string | null;
  commit_hash: string | null;
  created_at: string;
  indexed_at: string | null;
};

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedRepositoryId, setSelectedRepositoryId] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [message, setMessage] = useState("");

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) || null,
    [projects, selectedProjectId]
  );

  const attachedRepository = useMemo(() => {
    if (!selectedProject?.repository_id) return null;

    return (
      repositories.find(
        (repository) => repository.id === selectedProject.repository_id
      ) || null
    );
  }, [repositories, selectedProject]);

  const availableRepositories = useMemo(() => {
    if (!selectedProject?.repository_id) return repositories;

    return repositories.filter(
      (repository) => repository.id !== selectedProject.repository_id
    );
  }, [repositories, selectedProject]);

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
      await refreshDashboard();
    };

    checkLogin();
  }, []);

  const refreshDashboard = async () => {
    await Promise.all([loadProjects(), loadRepositories()]);
  };

  const loadProjects = async () => {
    const res = await authFetch("/projects");
    if (!res.ok) return;

    const data = await res.json();
    setProjects(data);
  };

  const loadRepositories = async () => {
    const res = await authFetch("/repositories");
    if (!res.ok) return;

    const data = await res.json();
    setRepositories(data);
  };

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

    setMode("login");
    setName("");
    setEmail("");
    setMessage("Registered successfully. Please login.");
  };

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
    setMessage("");
    await refreshDashboard();
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setProjects([]);
    setRepositories([]);
    setSelectedProjectId("");
    setSelectedRepositoryId("");
    setEmail("");
    setName("");
    setProjectName("");
    setDescription("");
    setMessage("");
  };

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
    setMessage("Project created");
  };

  const importGithubRepository = async () => {
    if (!selectedProject) {
      setMessage("Select a project first");
      return;
    }

    const res = await authFetch(
      `/projects/${selectedProject.id}/repository/github`,
      {
        method: "POST",
        body: JSON.stringify({
          source_url: githubUrl,
          branch,
        }),
      }
    );

    if (!res.ok) {
      setMessage("Unable to import GitHub repository");
      return;
    }

    await refreshDashboard();
    setGithubUrl("");
    setBranch("main");
    setMessage("GitHub repository attached to project");
  };

  const attachExistingRepository = async () => {
    if (!selectedProject || !selectedRepositoryId) {
      setMessage("Select a repository first");
      return;
    }

    const res = await authFetch(`/projects/${selectedProject.id}/repository`, {
      method: "PUT",
      body: JSON.stringify({
        repository_id: selectedRepositoryId,
      }),
    });

    if (!res.ok) {
      setMessage("Unable to attach repository");
      return;
    }

    await refreshDashboard();
    setSelectedRepositoryId("");
    setMessage("Existing repository attached to project");
  };

  const showMissingApiMessage = (action: string) => {
    setMessage(`${action} API is not implemented in backend yet.`);
  };

  const repositoryLabel = (repository: Repository) => {
    return repository.source_url || repository.local_path || repository.id;
  };

  if (!user) {
    return (
      <main style={styles.container}>
        <h1>AI Copilot</h1>

        <section style={styles.card}>
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

          {message && <p>{message}</p>}
        </section>
      </main>
    );
  }

  if (selectedProject) {
    return (
      <main style={styles.container}>
        <div style={styles.header}>
          <div>
            <button onClick={() => setSelectedProjectId("")}>Back</button>
            <h2>{selectedProject.name}</h2>
            <p>{selectedProject.description || "No description"}</p>
            <small>Status: {selectedProject.status}</small>
          </div>

          <button onClick={logout}>Logout</button>
        </div>

        <section style={styles.card}>
          <h3>Repository</h3>

          {attachedRepository ? (
            <div>
              <strong>{repositoryLabel(attachedRepository)}</strong>
              <p>Branch: {attachedRepository.branch || "none"}</p>
              <p>Indexed: {attachedRepository.indexed_at || "not indexed"}</p>

              <button
                onClick={() => showMissingApiMessage("Detach repository")}
                style={styles.danger}
              >
                Delete Repository From This Project
              </button>
            </div>
          ) : (
            <div>
              <input
                placeholder="GitHub repository URL"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                style={styles.input}
              />

              <input
                placeholder="Branch"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                style={styles.input}
              />

              <button onClick={importGithubRepository} style={styles.primary}>
                Add Repository From GitHub
              </button>

              <select
                value={selectedRepositoryId}
                onChange={(e) => setSelectedRepositoryId(e.target.value)}
                style={styles.input}
              >
                <option value="">Select existing repository</option>
                {availableRepositories.map((repository) => (
                  <option key={repository.id} value={repository.id}>
                    {repositoryLabel(repository)}
                  </option>
                ))}
              </select>

              <button onClick={attachExistingRepository} style={styles.primary}>
                Attach Existing Repository
              </button>
            </div>
          )}
        </section>

        <section style={styles.card}>
          <h3>Project Actions</h3>

          <button
            onClick={() => showMissingApiMessage("Delete project")}
            style={styles.danger}
          >
            Delete Project
          </button>
        </section>

        {message && <p>{message}</p>}
      </main>
    );
  }

  return (
    <main style={styles.container}>
      <div style={styles.header}>
        <div>
          <h2>Welcome {user.name}</h2>
          <p>{user.email}</p>
        </div>

        <button onClick={logout}>Logout</button>
      </div>

      <section style={styles.card}>
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
      </section>

      <section style={styles.card}>
        <h3>My Projects</h3>

        {projects.length === 0 ? (
          <p>No projects yet.</p>
        ) : (
          projects.map((project) => (
            <button
              key={project.id}
              onClick={() => setSelectedProjectId(project.id)}
              style={styles.projectButton}
            >
              <strong>{project.name}</strong>
              <span>{project.description || "No description"}</span>
              <small>
                {project.status} | repository:{" "}
                {project.repository_id || "not attached"}
              </small>
            </button>
          ))
        )}
      </section>

      {message && <p>{message}</p>}
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  container: {
    maxWidth: 760,
    margin: "40px auto",
    fontFamily: "Arial",
  },

  card: {
    border: "1px solid #ddd",
    padding: 20,
    borderRadius: 8,
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

  danger: {
    marginTop: 15,
    width: "100%",
    padding: 10,
    cursor: "pointer",
    border: "1px solid #b00020",
    color: "#b00020",
    background: "white",
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
    alignItems: "flex-start",
    gap: 20,
  },

  project: {
    borderTop: "1px solid #eee",
    padding: "10px 0",
  },

  projectButton: {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    gap: 6,
    border: 0,
    borderTop: "1px solid #eee",
    background: "#4f4f4f",
    padding: "12px 0",
    cursor: "pointer",
    textAlign: "left",
  },
};
