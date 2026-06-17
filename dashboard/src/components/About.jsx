export default function About() {
  return (
    <div className="about">
      <div className="about-section">
        <h2>What is this?</h2>
        <p>
          A data engineering portfolio project built on 9.5 million NYC Yellow Taxi trips
          from January to March 2024. It demonstrates a production-style analytics pipeline
          from raw ingestion through to a live dashboard and ML-powered fare prediction.
        </p>
      </div>

      <div className="about-section">
        <h2>Pipeline Architecture</h2>
        <div className="pipeline">
          <div className="pipeline-step">
            <div className="step-title">Ingest</div>
            <div className="step-body">NYC TLC parquet files streamed record-by-record into Kafka, decoupling ingestion from storage and enabling fault-tolerant replay.</div>
          </div>
          <div className="pipeline-arrow">→</div>
          <div className="pipeline-step">
            <div className="step-title">Store</div>
            <div className="step-body">Kafka consumer batches messages into DuckDB, an embedded analytical database optimised for columnar queries at this scale.</div>
          </div>
          <div className="pipeline-arrow">→</div>
          <div className="pipeline-step">
            <div className="step-title">Transform</div>
            <div className="step-body">dbt models build staging and mart layers (fare summaries, hourly demand) with 9 data quality tests. Orchestrated by Apache Airflow.</div>
          </div>
          <div className="pipeline-arrow">→</div>
          <div className="pipeline-step">
            <div className="step-title">Serve</div>
            <div className="step-body">FastAPI exposes dashboard endpoints and an ML fare predictor (R² = 0.91) trained on trip features.</div>
          </div>
        </div>
      </div>

      <div className="about-section">
        <h2>Design Decisions</h2>
        <div className="decisions">
          <div className="decision">
            <div className="decision-title">Why Kafka?</div>
            <p>In a real taxi platform, trips arrive one by one from dispatch systems as events, not as a file. Kafka sits between the source and the database as a durable buffer. If the consumer crashes mid-ingestion it resumes from where it left off, because Kafka tracks offsets per consumer. The parquet files here are a stand-in for that real event stream, but the architecture reflects how production ingestion actually works.</p>
          </div>
          <div className="decision">
            <div className="decision-title">Why DuckDB and not Snowflake?</div>
            <p>DuckDB was chosen to keep this project self-contained and free to run locally. In production, this data would live in a cloud warehouse like Snowflake where it can scale and be accessed remotely. DuckDB is a deliberate tradeoff for a portfolio context, not a permanent architectural choice.</p>
          </div>
          <div className="decision">
            <div className="decision-title">Why dbt?</div>
            <p>Raw SQL scripts work but become hard to maintain. dbt brings software engineering practices to transformations: version-controlled SQL, a clean layered architecture separating raw, staging, and mart data, and built-in data quality tests that catch bad data before it reaches the dashboard.</p>
          </div>
          <div className="decision">
            <div className="decision-title">Why Airflow?</div>
            <p>A cron job could run dbt on a schedule, but it gives you no visibility. Airflow shows every run, retries on failure, and makes dependencies between tasks explicit. The DAG is essentially live documentation of the pipeline.</p>
          </div>
          <div className="decision">
            <div className="decision-title">Why Random Forest for fare prediction?</div>
            <p>Fare is non-linear. A 5-mile trip at 3am costs differently than the same distance at 6pm rush hour in a different borough. Random Forest handles those interactions naturally without needing manually engineered features for every combination. It achieved R² = 0.91 on the holdout set.</p>
          </div>
        </div>
      </div>

      <div className="about-section">
        <h2>Tech Stack</h2>
        <div className="stack-grid">
          {[
            ['Ingestion',      'Apache Kafka, Python'],
            ['Storage',        'DuckDB'],
            ['Transformation', 'dbt'],
            ['Orchestration',  'Apache Airflow'],
            ['ML',             'scikit-learn (Random Forest)'],
            ['API',            'FastAPI, Python'],
            ['Frontend',       'React, Recharts, Vite'],
            ['Infrastructure', 'Docker Compose'],
          ].map(([layer, tools]) => (
            <div className="stack-row" key={layer}>
              <span className="stack-layer">{layer}</span>
              <span className="stack-tools">{tools}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="about-section">
        <h2>Data</h2>
        <p>
          Source: <a href="https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page" target="_blank" rel="noreferrer">NYC Taxi & Limousine Commission Trip Record Data</a>.
          Jan–Mar 2024 Yellow Taxi trips. 9,554,778 raw records, 9,211,244 after quality filtering.
        </p>
      </div>
    </div>
  )
}
