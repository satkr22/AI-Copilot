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

type RepositoryBranch = {
  id: string;
  branch_name: string;
  latest_commit_hash: string;
  original_commit_hash: string;
  indexed_at: string | null;
};

type Repository = {
  id: string;
  source_type: string;
  source_url: string | null;
  local_path: string | null;
  branch?: string | null;
  commit_hash?: string | null;
  branches?: RepositoryBranch[];
  created_at: string;
  indexed_at: string | null;
};

type IndexingJob = {
  id: string;
  repository_id: string;
  branch_name: string;
  commit_hash: string | null;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
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
  const [isIndexing, setIsIndexing] = useState(false);


  // Projects removed in this session. The server can keep answering /projects
  // with a just-deleted row, so the UI never renders an id from this list.
  const [deletedProjectIds, setDeletedProjectIds] = useState<string[]>([]);

  const visibleProjects = useMemo(
    () => projects.filter((project) => !deletedProjectIds.includes(project.id)),
    [deletedProjectIds, projects]
  );

  const forgetProject = (projectId: string) => {
    setDeletedProjectIds((prev) =>
      prev.includes(projectId) ? prev : [...prev, projectId]
    );
    setProjects((prev) => prev.filter((project) => project.id !== projectId));
    setSelectedProjectId((prev) => (prev === projectId ? "" : prev));
  };

  const selectedProject = useMemo(
    () => visibleProjects.find((project) => project.id === selectedProjectId) || null,
    [selectedProjectId, visibleProjects]
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
    setProjects(Array.isArray(data) ? data : []);
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
    setDeletedProjectIds([]);
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

  const duplicateExistingRepository = async () => {
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
    setMessage("Duplicate repository attached to project");
  };

  const detachRepository = async () => {
    if (!selectedProject) {
      setMessage("Select a project first");
      return;
    }

    if (!confirm("Detach repository from this project? The repository will be deleted if no other project uses it.")) {
      return;
    }

    const res = await authFetch(`/projects/${selectedProject.id}/repository`, {
      method: "DELETE",
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Failed to detach repository" }));
      setMessage(error.detail || "Failed to detach repository");
      return;
    }

    await refreshDashboard();
    setMessage("Repository detached from project");
  };

  const deleteProject = async () => {
    if (!selectedProject) {
      setMessage("Select a project first");
      return;
    }

    if (!confirm("Delete this project? The attached repository will be deleted if no other project uses it.")) {
      return;
    }

    const res = await authFetch(`/projects/${selectedProject.id}`, {
      method: "DELETE",
    });

    // 404 also means success: the project is no longer on the server.
    if (!res.ok && res.status !== 204 && res.status !== 404) {
      const error = await res.json().catch(() => ({ detail: "Failed to delete project" }));
      setMessage(error.detail || "Failed to delete project");
      return;
    }

    forgetProject(selectedProject.id);
    await refreshDashboard();
    setSelectedRepositoryId("");
    setGithubUrl("");
    setBranch("main");
    setMessage("Project deleted");
  };

  const indexRepository = async () => {
    if (!attachedRepository) {
      setMessage("No repository attached");
      return;
    }

    setIsIndexing(true);

    const res = await authFetch(
      `/repositories/${attachedRepository.id}/index`,
      {
        method: "POST",
      }
    );

    setIsIndexing(false);

    if (!res.ok) {
      const error = await res.json().catch(() => ({
        detail: "Indexing failed",
      }));

      setMessage(error.detail || "Indexing failed");
      return;
    }

    const job: IndexingJob = await res.json();

    await refreshDashboard();

    setMessage(
      `Indexing completed (${job.branch_name} • ${job.status})`
    );
  };



  const uploadZipRepository = async (file: File) => {
    if (!selectedProject) {
      setMessage("Select a project first");
      return;
    }

    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API}/projects/${selectedProject.id}/repository/zip`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Failed to upload zip" }));
      setMessage(error.detail || "Failed to upload zip");
      return;
    }

    await refreshDashboard();
    setMessage("ZIP repository uploaded and attached to project");
  };

  const handleZipUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".zip")) {
      setMessage("Please select a .zip file");
      event.target.value = "";
      return;
    }

    await uploadZipRepository(file);
    event.target.value = "";
  };

  const repositoryLabel = (repository: Repository) => {
    return repository.source_url || repository.local_path || repository.id;
  };

  

  const shortCommit = (commitHash: string) => commitHash.slice(0, 8);

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
              <p>
                Branches:{" "}
                {attachedRepository.branches?.length
                  ? attachedRepository.branches
                      .map(
                        (repoBranch) =>
                          `${repoBranch.branch_name} (${shortCommit(repoBranch.latest_commit_hash)})`
                      )
                      .join(", ")
                  : attachedRepository.branch || "none"}
              </p>
              <p>
                Indexed:{" "}
                {attachedRepository.indexed_at
                  ? new Date(attachedRepository.indexed_at).toLocaleString()
                  : "Not indexed"}
              </p>

              <button
                onClick={indexRepository}
                disabled={isIndexing}
                style={styles.primary}
              >
                {isIndexing ? "Indexing..." : "Index Repository"}
              </button>

              <button
                onClick={detachRepository}
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

              <button onClick={duplicateExistingRepository} style={styles.primary}>
                Duplicate Existing Repository
              </button>

              <div style={styles.uploadSection}>
                <label style={styles.uploadLabel}>
                  <span>Upload ZIP Repository</span>
                  <input
                    type="file"
                    accept=".zip"
                    onChange={handleZipUpload}
                    style={styles.fileInput}
                  />
                </label>
              </div>
            </div>
          )}
        </section>

        <section style={styles.card}>
          <h3>Project Actions</h3>

          <button
            onClick={deleteProject}
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

        {visibleProjects.length === 0 ? (
          <p>No projects yet.</p>
        ) : (
          visibleProjects.map((project) => (
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

  uploadSection: {
    marginTop: 15,
  },

  uploadLabel: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    fontWeight: "bold",
  },

  fileInput: {
    padding: 8,
  },
};
