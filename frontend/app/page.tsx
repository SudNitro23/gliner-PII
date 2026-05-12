"use client";

import { Activity, AlertCircle, CheckCircle2, FileText, Gauge, Upload } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type Evaluation = {
  id: string;
  pdf_filename: string;
  ground_truth_filename: string;
  status: string;
  metrics: Metrics | null;
  predictions: Prediction[];
  matches: Match[];
  model_status: string | null;
  error: string | null;
};

type Metrics = {
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1: number;
  by_label: Record<string, LabelMetrics>;
};

type LabelMetrics = {
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1: number;
};

type Prediction = {
  text: string;
  label: string;
  taxonomy_label: string;
  score: number | null;
};

type Match = {
  status: "true_positive" | "false_positive" | "false_negative";
  prediction: Prediction | null;
  ground_truth: { text: string; label: string } | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [pdf, setPdf] = useState<File | null>(null);
  const [groundTruth, setGroundTruth] = useState<File | null>(null);
  const [threshold, setThreshold] = useState(0.5);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canRun = useMemo(() => Boolean(pdf && groundTruth && !isRunning), [pdf, groundTruth, isRunning]);

  async function runEvaluation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!pdf || !groundTruth) return;

    setIsRunning(true);
    setError(null);
    setEvaluation(null);

    const formData = new FormData();
    formData.append("pdf", pdf);
    formData.append("ground_truth", groundTruth);
    formData.append("threshold", String(threshold));

    try {
      const response = await fetch(`${API_URL}/api/evaluations`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Evaluation failed");
      }

      setEvaluation(await response.json());
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Evaluation failed");
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local MVP</p>
          <h1>GLiNER-PII Evaluation</h1>
        </div>
        <div className="status-pill">
          <Activity size={16} aria-hidden />
          <span>FastAPI · Next.js · SQLite</span>
        </div>
      </header>

      <section className="workspace">
        <form className="upload-panel" onSubmit={runEvaluation}>
          <div className="panel-heading">
            <Gauge size={20} aria-hidden />
            <h2>Run Evaluation</h2>
          </div>

          <label className="file-input">
            <FileText size={18} aria-hidden />
            <span>{pdf?.name ?? "PDF"}</span>
            <input
              type="file"
              accept="application/pdf"
              onChange={(event) => setPdf(event.target.files?.[0] ?? null)}
            />
          </label>

          <label className="file-input">
            <FileText size={18} aria-hidden />
            <span>{groundTruth?.name ?? "Ground truth CSV"}</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setGroundTruth(event.target.files?.[0] ?? null)}
            />
          </label>

          <label className="threshold-row">
            <span>Threshold</span>
            <input
              type="range"
              min="0.1"
              max="0.95"
              step="0.05"
              value={threshold}
              onChange={(event) => setThreshold(Number(event.target.value))}
            />
            <strong>{threshold.toFixed(2)}</strong>
          </label>

          <button className="primary-button" type="submit" disabled={!canRun}>
            <Upload size={18} aria-hidden />
            <span>{isRunning ? "Running" : "Run"}</span>
          </button>
        </form>

        <section className="results-panel">
          {error ? (
            <Notice tone="bad" message={error} />
          ) : evaluation?.status === "failed" ? (
            <Notice tone="bad" message={evaluation.error ?? "Evaluation failed"} />
          ) : evaluation?.metrics ? (
            <Results evaluation={evaluation} />
          ) : (
            <div className="empty-state">
              <CheckCircle2 size={28} aria-hidden />
              <span>Ready</span>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function Results({ evaluation }: { evaluation: Evaluation }) {
  const metrics = evaluation.metrics;
  if (!metrics) return null;

  return (
    <div className="results-stack">
      <div className="result-header">
        <div>
          <p className="eyebrow">Evaluation</p>
          <h2>{evaluation.pdf_filename}</h2>
        </div>
        <span className="status-pill success">{evaluation.model_status ?? evaluation.status}</span>
      </div>

      <div className="metric-grid">
        <Metric label="Precision" value={metrics.precision} />
        <Metric label="Recall" value={metrics.recall} />
        <Metric label="F1" value={metrics.f1} />
        <Metric label="TP" value={metrics.true_positives} />
        <Metric label="FP" value={metrics.false_positives} />
        <Metric label="FN" value={metrics.false_negatives} />
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Text</th>
              <th>Label</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {evaluation.matches.map((match, index) => {
              const entity = match.prediction ?? match.ground_truth;
              return (
                <tr key={`${match.status}-${index}`}>
                  <td>
                    <span className={`match ${match.status}`}>{statusLabel(match.status)}</span>
                  </td>
                  <td>{entity?.text ?? "-"}</td>
                  <td>{match.prediction?.taxonomy_label ?? match.ground_truth?.label ?? "-"}</td>
                  <td>{formatScore(match.prediction?.score)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{typeof value === "number" && value <= 1 ? value.toFixed(2) : value}</strong>
    </div>
  );
}

function Notice({ tone, message }: { tone: "bad"; message: string }) {
  return (
    <div className={`notice ${tone}`}>
      <AlertCircle size={24} aria-hidden />
      <span>{message}</span>
    </div>
  );
}

function statusLabel(status: Match["status"]) {
  if (status === "true_positive") return "TP";
  if (status === "false_positive") return "FP";
  return "FN";
}

function formatScore(score: number | null | undefined) {
  if (score === null || score === undefined) return "-";
  return score.toFixed(2);
}

