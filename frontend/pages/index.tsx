import Head from "next/head";
import { useEffect, useMemo, useState } from "react";

interface Citation {
  url: string | null;
  title: string | null;
  retrieved_at: string | null;
}

interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const backendUrl = useMemo(
    () => process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
    []
  );

  const askQuestion = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question })
      });

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`);
      }

      const data: ChatResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setResponse(null);
  }, [question]);

  return (
    <>
      <Head>
        <title>Aguirre Assistant</title>
      </Head>
      <main className="container">
        <h1>Aguirre Assistant</h1>
        <p>Pregunta al asistente fiscal.</p>
        <div className="card">
          <label htmlFor="question">Pregunta</label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="¿Cuál es tu consulta?"
            rows={4}
          />
          <button onClick={askQuestion} disabled={!question || loading}>
            {loading ? "Consultando..." : "Enviar"}
          </button>
          {error && <p className="error">{error}</p>}
          {response && (
            <div className="response">
              <h2>Respuesta</h2>
              <p>{response.answer}</p>
              <h3>Citas</h3>
              {response.citations.length === 0 ? (
                <p>No se encontraron citas.</p>
              ) : (
                <ul>
                  {response.citations.map((citation, index) => (
                    <li key={index}>
                      {citation.url ? (
                        <a href={citation.url} target=\"_blank\" rel=\"noreferrer\">
                          {citation.title ?? citation.url}
                        </a>
                      ) : (
                        citation.title ?? \"Cita sin título\"
                      )}
                      {citation.retrieved_at && (
                        <span className=\"meta\"> — {citation.retrieved_at}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </main>
      <style jsx>{`
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem;
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        h1 {
          margin-bottom: 0.5rem;
        }

        .card {
          margin-top: 1rem;
          padding: 1rem;
          border: 1px solid #e5e5e5;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        label {
          display: block;
          font-weight: 600;
          margin-bottom: 0.5rem;
        }

        textarea {
          width: 100%;
          padding: 0.75rem;
          border-radius: 6px;
          border: 1px solid #ccc;
          resize: vertical;
          font-size: 1rem;
        }

        button {
          margin-top: 0.75rem;
          padding: 0.75rem 1.25rem;
          background: #111827;
          color: #fff;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }

        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .response {
          margin-top: 1rem;
        }

        .error {
          color: #dc2626;
          margin-top: 0.5rem;
        }

        .meta {
          color: #6b7280;
          font-size: 0.9rem;
        }
      `}</style>
    </>
  );
}
