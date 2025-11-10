import { useState, useRef } from 'react';
import './CampaignForm.css';

export default function CampaignForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    products: [
      { name: '', description: '', existing_assets: [] },
      { name: '', description: '', existing_assets: [] },
    ],
    target_region: 'North America',
    target_audience: '',
    campaign_message: '',
    brand_colors: ['#007AFF'],
    enable_copywriting: true,
  });

  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = e.target.result;
        let data;

        if (file.name.endsWith('.json')) {
          data = JSON.parse(content);
        } else if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
          // Simple YAML parser for our specific format
          // For production, use a library like js-yaml
          const lines = content.split('\n');
          data = {};
          let currentKey = null;
          let productsArray = [];
          let currentProduct = null;

          lines.forEach(line => {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith('#')) return;

            if (trimmed.startsWith('products:')) {
              currentKey = 'products';
            } else if (trimmed.startsWith('- name:')) {
              if (currentProduct) productsArray.push(currentProduct);
              currentProduct = { name: trimmed.split(':')[1].trim(), description: '', existing_assets: [] };
            } else if (trimmed.startsWith('description:') && currentProduct) {
              currentProduct.description = trimmed.split(':')[1].trim();
            } else if (!trimmed.startsWith('-') && trimmed.includes(':')) {
              const [key, ...valueParts] = trimmed.split(':');
              let value = valueParts.join(':').trim();

              // Parse value types
              if (key === 'brand_colors') {
                // Parse array, remove brackets and quotes
                data[key] = value ? value.replace(/[\[\]"']/g, '').split(',').map(c => c.trim()).filter(c => c) : [];
              } else if (value === 'true') {
                data[key] = true;
              } else if (value === 'false') {
                data[key] = false;
              } else if (value && !isNaN(value)) {
                data[key] = Number(value);
              } else {
                data[key] = value;
              }
            }
          });

          if (currentProduct) productsArray.push(currentProduct);
          if (productsArray.length) data.products = productsArray;
        }

        // Merge loaded data with form data
        setFormData({
          products: data.products || formData.products,
          target_region: data.target_region || formData.target_region,
          target_audience: data.target_audience || formData.target_audience,
          campaign_message: data.campaign_message || formData.campaign_message,
          brand_colors: data.brand_colors || formData.brand_colors,
          enable_copywriting: data.enable_copywriting !== undefined ? data.enable_copywriting : formData.enable_copywriting,
        });

      } catch (error) {
        alert(`Error parsing file: ${error.message}`);
      }
    };

    reader.readAsText(file);
  };

  const handleProductChange = (index, field, value) => {
    const newProducts = [...formData.products];
    newProducts[index][field] = value;
    setFormData({ ...formData, products: newProducts });
  };

  const addProduct = () => {
    setFormData({
      ...formData,
      products: [...formData.products, { name: '', description: '', existing_assets: [] }],
    });
  };

  const removeProduct = (index) => {
    if (formData.products.length > 2) {
      const newProducts = formData.products.filter((_, i) => i !== index);
      setFormData({ ...formData, products: newProducts });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form className="campaign-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h2>Create Campaign</h2>
        <div className="file-upload-section">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.yaml,.yml"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="upload-btn"
          >
            📁 Load from File
          </button>
          <span className="file-hint">JSON or YAML</span>
        </div>
      </div>

      <div className="form-section">
        <h3>Products (min 2)</h3>
        {formData.products.map((product, index) => (
          <div key={index} className="product-input">
            <div className="product-header">
              <h4>Product {index + 1}</h4>
              {formData.products.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeProduct(index)}
                  className="remove-btn"
                >
                  Remove
                </button>
              )}
            </div>
            <input
              type="text"
              placeholder="Product name"
              value={product.name}
              onChange={(e) => handleProductChange(index, 'name', e.target.value)}
              required
            />
            <textarea
              placeholder="Product description"
              value={product.description}
              onChange={(e) => handleProductChange(index, 'description', e.target.value)}
              required
            />
          </div>
        ))}
        <button type="button" onClick={addProduct} className="add-btn">
          + Add Product
        </button>
      </div>

      <div className="form-section">
        <h3>Campaign Details</h3>

        <label>
          Target Region
          <select
            value={formData.target_region}
            onChange={(e) => setFormData({ ...formData, target_region: e.target.value })}
          >
            <option value="North America">North America</option>
            <option value="Europe">Europe</option>
            <option value="Asia Pacific">Asia Pacific</option>
            <option value="Latin America">Latin America</option>
            <option value="Middle East">Middle East</option>
          </select>
        </label>

        <label>
          Target Audience
          <input
            type="text"
            placeholder="e.g., Tech-savvy professionals aged 25-40"
            value={formData.target_audience}
            onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
            required
          />
        </label>

        <label>
          Campaign Message
          <textarea
            placeholder="Your campaign tagline"
            value={formData.campaign_message}
            onChange={(e) => setFormData({ ...formData, campaign_message: e.target.value })}
            required
          />
        </label>

        <label>
          Brand Colors (comma-separated hex codes)
          <input
            type="text"
            placeholder="#007AFF, #FFFFFF"
            value={formData.brand_colors.join(', ')}
            onChange={(e) =>
              setFormData({
                ...formData,
                brand_colors: e.target.value.split(',').map((c) => c.trim()),
              })
            }
          />
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={formData.enable_copywriting}
            onChange={(e) =>
              setFormData({ ...formData, enable_copywriting: e.target.checked })
            }
          />
          Enable AI Copywriting Optimization
        </label>
      </div>

      <button type="submit" className="submit-btn">
        Generate Campaign
      </button>
    </form>
  );
}
