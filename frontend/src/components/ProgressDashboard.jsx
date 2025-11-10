import { useEffect, useState } from 'react';
import './ProgressDashboard.css';

// Helper function to format stage names
const formatStage = (stage) => {
  const stageMap = {
    'initialization': '🚀 Initializing Campaign',
    'copywriting': '✍️ Optimizing Message',
    'moderation': '🔍 Content Moderation',
    'products': '📦 Processing Products',
    'asset_generation': '🎨 Generating Assets',
    'variations': '📐 Creating Variations',
    'compliance': '🎯 Brand Compliance Check'
  };
  return stageMap[stage] || stage;
};

export default function ProgressDashboard({ campaignId, onComplete }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/campaigns/${campaignId}/status`);
        const data = await response.json();
        setStatus(data);

        if (data.status === 'completed') {
          onComplete(data);
        } else if (data.status === 'failed') {
          setError(data.error);
        } else if (data.status === 'processing' || data.status === 'queued') {
          // Keep polling
          setTimeout(checkStatus, 2000);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    checkStatus();
  }, [campaignId, onComplete]);

  if (loading) {
    return (
      <div className="progress-dashboard">
        <div className="loader"></div>
        <p>Connecting to campaign...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="progress-dashboard error">
        <h2>❌ Campaign Failed</h2>
        <p className="error-message">{error}</p>
        <button onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  return (
    <div className="progress-dashboard">
      <h2>Campaign Processing</h2>

      <div className="status-card">
        <div className="status-header">
          <span className="campaign-id">{campaignId}</span>
          <span className={`status-badge ${status.status}`}>{status.status}</span>
        </div>

        {status.progress && (
          <div className="progress-details">
            <div className="detail-row">
              <span className="label">Region:</span>
              <span className="value">{status.progress.target_region}</span>
            </div>
            <div className="detail-row">
              <span className="label">Audience:</span>
              <span className="value">{status.progress.target_audience}</span>
            </div>
            <div className="detail-row">
              <span className="label">Message:</span>
              <span className="value">{status.progress.campaign_message}</span>
            </div>
            <div className="detail-row">
              <span className="label">Products:</span>
              <span className="value">{status.progress.product_count}</span>
            </div>
          </div>
        )}

        {status.status === 'processing' && (
          <div className="processing-indicator">
            <div className="loader"></div>
            {status.latest_progress ? (
              <div className="progress-update">
                <p className="progress-stage">{formatStage(status.latest_progress.stage)}</p>
                <p className="progress-message">{status.latest_progress.message}</p>
                {status.latest_progress.current_product && (
                  <p className="progress-details">
                    Product {status.latest_progress.current_product} of {status.latest_progress.total_products}
                  </p>
                )}
                {status.latest_progress.variations_created && (
                  <p className="progress-details">
                    {status.latest_progress.variations_created} variations created
                  </p>
                )}
              </div>
            ) : (
              <>
                <p>Generating assets with DALL-E and processing variations...</p>
                <p className="note">This may take 1-2 minutes</p>
              </>
            )}
          </div>
        )}

        {status.status === 'queued' && (
          <div className="processing-indicator">
            <div className="loader"></div>
            <p>Campaign queued for processing...</p>
          </div>
        )}

        {status.status === 'completed' && status.report && (
          <div className="completion-summary">
            <h3>✅ Campaign Complete!</h3>
            <div className="summary-stats">
              <div className="stat">
                <span className="stat-value">{status.report.summary.total_products}</span>
                <span className="stat-label">Products</span>
              </div>
              <div className="stat">
                <span className="stat-value">{status.report.summary.total_variations}</span>
                <span className="stat-label">Variations</span>
              </div>
              <div className="stat">
                <span className="stat-value">{status.report.summary.assets_generated}</span>
                <span className="stat-label">Generated</span>
              </div>
              <div className="stat">
                <span className="stat-value">{status.report.summary.duration_seconds}s</span>
                <span className="stat-label">Duration</span>
              </div>
            </div>

            {status.report.copywriting && (
              <div className="copywriting-results">
                <h4>AI Copywriting Optimization</h4>
                <div className="message-comparison">
                  <div>
                    <strong>Original:</strong> {status.report.copywriting.original_message}
                  </div>
                  <div>
                    <strong>Optimized:</strong> {status.report.copywriting.selected_message}
                  </div>
                  <div>
                    <strong>Confidence:</strong>{' '}
                    {(status.report.copywriting.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
