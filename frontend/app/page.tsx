"use client";

import { Activity, AlertCircle, CheckCircle2, Database, FileText, FolderUp, Upload } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

type Dataset = {
  id: string;
  created_at: string | null;
  name: string;
  pdf_filenames: string[];
  pdf_count: number;
  ground_truth_filename: string;
  csv_text_column: string;
  csv_label_column: string;
  storage_path: string;
  status: string;
  error: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [datasetName, setDatasetName] = useState("");
  const [pdfs, setPdfs] = useState<File[]>([]);
  const [groundTruth, setGroundTruth] = useState<File | null>(null);
  const [latestDataset, setLatestDataset] = useState<Dataset | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      const response = await fetch(`${API_URL}/api/datasets`);
      if (!response.ok) {
        return;
      }

      const items = (await response.json()) as Dataset[];
      setDatasets(items);
      setLatestDataset((current) => current ?? items[0] ?? null);
    } catch {
      // Keep the page usable even if the API is not running yet.
    }
  }

  async function uploadDataset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!pdfs.length || !groundTruth) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    if (datasetName.trim()) {
      formData.append("name", datasetName.trim());
    }
    for (const pdf of pdfs) {
      formData.append("pdfs", pdf);
    }
    formData.append("ground_truth", groundTruth);

    try {
      const response = await fetch(`${API_URL}/api/datasets`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? "Dataset upload failed");
      }

      const dataset = (await response.json()) as Dataset;
      setLatestDataset(dataset);
      setDatasets((current) => [dataset, ...current.filter((item) => item.id !== dataset.id)]);
      setDatasetName("");
      setPdfs([]);
      setGroundTruth(null);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Dataset upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  const canUpload = pdfs.length > 0 && Boolean(groundTruth) && !isUploading;

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local MVP</p>
          <h1>GLiNER-PII Dataset Intake</h1>
        </div>
        <div className="status-pill">
          <Activity size={16} aria-hidden />
          <span>Multi-PDF upload · CSV validation · Local storage</span>
        </div>
      </header>

      <section className="workspace">
        <form className="upload-panel" onSubmit={uploadDataset}>
          <div className="panel-heading">
            <FolderUp size={20} aria-hidden />
            <h2>Upload Dataset</h2>
          </div>

          <label className="text-input">
            <span>Dataset name</span>
            <input
              type="text"
              value={datasetName}
              onChange={(event) => setDatasetName(event.target.value)}
              placeholder="April sample batch"
            />
          </label>

          <label className="file-input tall">
            <FileText size={18} aria-hidden />
            <span>{pdfs.length ? `${pdfs.length} PDF${pdfs.length === 1 ? "" : "s"} selected` : "Select PDFs"}</span>
            <input
              type="file"
              accept="application/pdf"
              multiple
              onChange={(event) => setPdfs(Array.from(event.target.files ?? []))}
            />
          </label>

          {pdfs.length > 0 ? (
            <div className="selection-list">
              {pdfs.map((pdf) => (
                <span key={`${pdf.name}-${pdf.size}`}>{pdf.name}</span>
              ))}
            </div>
          ) : null}

          <label className="file-input">
            <Database size={18} aria-hidden />
            <span>{groundTruth?.name ?? "Select ground_truth_clean.csv"}</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => setGroundTruth(event.target.files?.[0] ?? null)}
            />
          </label>

          <div className="hint-block">
            <strong>CSV validation</strong>
            <p>The backend checks that the uploaded CSV contains a text column and a label column before storing the dataset.</p>
          </div>

          <button className="primary-button" type="submit" disabled={!canUpload}>
            <Upload size={18} aria-hidden />
            <span>{isUploading ? "Uploading" : "Store Dataset"}</span>
          </button>
        </form>

        <section className="results-panel">
          {error ? <Notice message={error} /> : latestDataset ? <DatasetDetails dataset={latestDataset} /> : <EmptyState />}
        </section>
      </section>

      <section className="history-panel">
        <div className="panel-heading">
          <Database size={20} aria-hidden />
          <h2>Stored Datasets</h2>
        </div>
        {datasets.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>PDFs</th>
                  <th>Ground Truth</th>
                  <th>CSV Columns</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>{dataset.name}</td>
                    <td>{dataset.pdf_count}</td>
                    <td>{dataset.ground_truth_filename}</td>
                    <td>{`${dataset.csv_text_column} / ${dataset.csv_label_column}`}</td>
                    <td>{dataset.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-history">No stored datasets yet.</div>
        )}
      </section>
    </main>
  );
}

function DatasetDetails({ dataset }: { dataset: Dataset }) {
  return (
    <div className="results-stack">
      <div className="result-header">
        <div>
          <p className="eyebrow">Latest Upload</p>
          <h2>{dataset.name}</h2>
        </div>
        <span className="status-pill success">{dataset.status}</span>
      </div>

      <div className="metric-grid">
        <Metric label="PDF count" value={String(dataset.pdf_count)} />
        <Metric label="Ground truth" value={dataset.ground_truth_filename} />
        <Metric label="Text column" value={dataset.csv_text_column} />
        <Metric label="Label column" value={dataset.csv_label_column} />
      </div>

      <div className="detail-block">
        <strong>Stored PDFs</strong>
        <ul className="plain-list">
          {dataset.pdf_filenames.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
      </div>

      <div className="detail-block">
        <strong>Local storage path</strong>
        <p>{dataset.storage_path}</p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Notice({ message }: { message: string }) {
  return (
    <div className="notice bad">
      <AlertCircle size={24} aria-hidden />
      <span>{message}</span>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <CheckCircle2 size={28} aria-hidden />
      <span>Upload a dataset to store PDFs and validate the ground truth CSV.</span>
    </div>
  );
}
