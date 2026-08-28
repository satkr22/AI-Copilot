import { useEffect, useState } from "react";

const API = import.meta.env.VITE_BACKEND_API_URL;

type HealthResponse = {
  status: string;
  service: string;
};
export default function App() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch(`${API}/health`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const result: HealthResponse = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <main
      style={{
        fontFamily: "Arial, sans-serif",
        maxWidth: "600px",
        margin: "40px auto",
      }}
    >
      <h1>AI Copilot Frontend</h1>

      {loading && <p>Loading...</p>}

      {error && (
        <p style={{ color: "red" }}>
          Error: {error}
        </p>
      )}

      {data && (
        <div>
          <h2>Backend Response</h2>
          <p>
            <strong>Status:</strong> {data.status}
          </p>
          <p>
            <strong>Service:</strong> {data.service}
          </p>
        </div>
      )}
    </main>
  );
}