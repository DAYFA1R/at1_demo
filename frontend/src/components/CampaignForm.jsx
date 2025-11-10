import { useState } from 'react';
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
      <h2>Create Campaign</h2>

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
