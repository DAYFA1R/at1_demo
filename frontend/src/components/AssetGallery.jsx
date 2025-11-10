import { useEffect, useState } from 'react';
import './AssetGallery.css';

export default function AssetGallery({ campaignId, reportData }) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState('all');

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await fetch(`/api/campaigns/${campaignId}/assets`);
        const data = await response.json();
        setAssets(data.assets);
      } catch (err) {
        console.error('Failed to load assets:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAssets();
  }, [campaignId]);

  const products = [...new Set(assets.map((a) => a.product))];
  const languages = [...new Set(assets.map((a) => a.language))];

  const filteredAssets = assets.filter(
    (asset) =>
      (selectedLanguage === 'all' || asset.language === selectedLanguage) &&
      (selectedProduct === 'all' || asset.product === selectedProduct)
  );

  const assetsByProduct = filteredAssets.reduce((acc, asset) => {
    if (!acc[asset.product]) acc[asset.product] = {};
    if (!acc[asset.product][asset.language]) acc[asset.product][asset.language] = [];
    acc[asset.product][asset.language].push(asset);
    return acc;
  }, {});

  if (loading) {
    return <div className="asset-gallery">Loading assets...</div>;
  }

  return (
    <div className="asset-gallery">
      <div className="gallery-header">
        <h2>Generated Assets</h2>
        <button onClick={() => window.location.reload()} className="new-campaign-btn">
          Create New Campaign
        </button>
      </div>

      <div className="filters">
        <label>
          Filter by Product:
          <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)}>
            <option value="all">All Products</option>
            {products.map((product) => (
              <option key={product} value={product}>
                {product}
              </option>
            ))}
          </select>
        </label>

        <label>
          Filter by Language:
          <select value={selectedLanguage} onChange={(e) => setSelectedLanguage(e.target.value)}>
            <option value="all">All Languages</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="assets-summary">
        <div className="summary-badge">
          {filteredAssets.length} assets | {products.length} products | {languages.length}{' '}
          languages
        </div>
      </div>

      {Object.entries(assetsByProduct).map(([product, languageGroups]) => (
        <div key={product} className="product-group">
          <h3>{product}</h3>

          {Object.entries(languageGroups).map(([language, languageAssets]) => (
            <div key={language} className="language-group">
              <h4>🌍 {language}</h4>
              <div className="asset-grid">
                {languageAssets.map((asset, idx) => (
                  <div key={idx} className="asset-card">
                    <div className="aspect-ratio-label">{asset.aspect_ratio}</div>
                    <img src={asset.url} alt={`${product} - ${asset.aspect_ratio}`} />
                    <div className="asset-info">
                      <span className="filename">{asset.filename}</span>
                      <a href={asset.url} download={asset.filename} className="download-btn">
                        Download
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}

      {filteredAssets.length === 0 && (
        <div className="no-results">No assets match the selected filters</div>
      )}

      {reportData && (
        <div className="report-section">
          <h3>Campaign Report</h3>

          {/* Summary Stats */}
          <div className="report-grid">
            <div className="report-item">
              <strong>Duration:</strong> {reportData.summary.duration_seconds}s
            </div>
            <div className="report-item">
              <strong>Success Rate:</strong> {reportData.summary.success_rate}
            </div>
            <div className="report-item">
              <strong>Assets Generated:</strong> {reportData.summary.assets_generated}
            </div>
            <div className="report-item">
              <strong>Total Variations:</strong> {reportData.summary.total_variations}
            </div>
          </div>

          {/* Copywriting Insights */}
          {reportData.copywriting && (
            <div className="copywriting-section">
              <h4>AI Copywriting Insights</h4>
              <div className="message-evolution">
                <div><strong>Original:</strong> {reportData.copywriting.original_message}</div>
                <div><strong>Optimized:</strong> {reportData.copywriting.selected_message}</div>
                <div><strong>Confidence:</strong> {(reportData.copywriting.confidence_score * 100).toFixed(0)}%</div>
              </div>

              {reportData.copywriting.optimization?.variants && (
                <div className="ab-variants">
                  <h5>Message Variants & Reasoning</h5>
                  {reportData.copywriting.optimization.variants.map((variant, idx) => (
                    <div key={idx} className="variant-card">
                      <div className="variant-text">"{variant.text}"</div>
                      <div className="variant-details">
                        <div><strong>Why:</strong> {variant.reasoning}</div>
                        <div><strong>Hook:</strong> {variant.emotional_hook} • <strong>Confidence:</strong> {(variant.confidence * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {reportData.copywriting.ab_test_variants && (
                <div className="ab-tests">
                  <h5>A/B Test Recommendations</h5>
                  {reportData.copywriting.ab_test_variants.map((test, idx) => (
                    <div key={idx} className="test-card">
                      <div className="test-text">"{test.text}"</div>
                      <div className="test-approach"><strong>Approach:</strong> {test.approach}</div>
                      <div className="test-hypothesis">{test.hypothesis}</div>
                    </div>
                  ))}
                </div>
              )}

              {reportData.copywriting.optimization?.persona_insights && (
                <details className="persona-details">
                  <summary><strong>Audience Persona Insights</strong></summary>
                  <div className="persona-content">
                    <div><strong>Demographics:</strong> {reportData.copywriting.optimization.persona_insights.demographics}</div>
                    <div><strong>Values:</strong> {reportData.copywriting.optimization.persona_insights.values?.join(', ')}</div>
                    <div><strong>Pain Points:</strong> {reportData.copywriting.optimization.persona_insights.pain_points?.join(', ')}</div>
                    <div><strong>Emotional Triggers:</strong> {reportData.copywriting.optimization.persona_insights.emotional_triggers?.join(', ')}</div>
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Warnings */}
          {reportData.warnings && reportData.warnings.length > 0 && (
            <div className="warnings-section">
              <h4>Warnings ({reportData.warnings.length})</h4>
              <ul className="warnings-list">
                {reportData.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Brand Compliance Details */}
          {reportData.compliance_summary?.enabled && (
            <div className="compliance-info">
              <h4>Brand Compliance</h4>
              <div className="compliance-summary">
                <div>Average Score: <strong>{reportData.compliance_summary.average_score}</strong> / 100</div>
                <div>Total Checks: {reportData.compliance_summary.total_checks}</div>
                <div>Status: {reportData.compliance_summary.all_compliant ? '✓ All Compliant' : '⚠ Needs Review'}</div>
              </div>

              {reportData.products_processed && (
                <details className="compliance-details">
                  <summary><strong>Detailed Compliance Breakdown</strong></summary>
                  {reportData.products_processed.map((product, pidx) => (
                    <div key={pidx} className="product-compliance">
                      <h5>{product.name}</h5>
                      {product.compliance && Object.entries(product.compliance).map(([ratio, check]) => (
                        <div key={ratio} className="compliance-check">
                          <div className="check-header">
                            <strong>{ratio}</strong> - Score: {check.overall_score}/100
                            {!check.compliant && <span className="non-compliant"> ⚠</span>}
                          </div>
                          <div className="check-details">
                            <div><strong>Summary:</strong> {check.summary}</div>
                            {check.checks?.colors && (
                              <div>• <strong>Brand Colors:</strong> {check.checks.colors.reason || (check.checks.colors.checked ? '✓' : '✗')}</div>
                            )}
                            {check.checks?.readability && (
                              <div>
                                • <strong>Text Readability:</strong> {check.checks.readability.readable ? '✓ Readable' : '✗ Needs improvement'}
                                (Brightness: {check.checks.readability.text_area_brightness?.toFixed(1)} - Recommend: {check.checks.readability.recommendation})
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </details>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
