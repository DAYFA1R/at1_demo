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
          <div className="report-grid">
            <div className="report-item">
              <strong>Duration:</strong> {reportData.summary.duration_seconds}s
            </div>
            <div className="report-item">
              <strong>Success Rate:</strong> {reportData.summary.success_rate}
            </div>
            {reportData.summary.total_warnings > 0 && (
              <div className="report-item warning">
                <strong>Warnings:</strong> {reportData.summary.total_warnings}
              </div>
            )}
          </div>

          {reportData.compliance_summary?.enabled && (
            <div className="compliance-info">
              <h4>Brand Compliance</h4>
              <p>
                Average Score: <strong>{reportData.compliance_summary.average_score}</strong> / 100
              </p>
              <p>Total Checks: {reportData.compliance_summary.total_checks}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
