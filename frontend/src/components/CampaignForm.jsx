import { useState, useRef, useEffect } from 'react';
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

  const [generatedImages, setGeneratedImages] = useState([]);
  const [showImageBrowser, setShowImageBrowser] = useState(false);
  const [selectedProductIndex, setSelectedProductIndex] = useState(null);

  const fileInputRef = useRef(null);
  const productImageInputRefs = useRef({});

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

  // Fetch generated images on mount
  useEffect(() => {
    const fetchGeneratedImages = async () => {
      try {
        const response = await fetch('/api/generated-images');
        const data = await response.json();
        setGeneratedImages(data.images || []);
      } catch (err) {
        console.error('Failed to load generated images:', err);
      }
    };

    fetchGeneratedImages();
  }, []);

  // Handle product image upload
  const handleProductImageUpload = async (event, productIndex) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();

      // Add uploaded file path to product's existing_assets
      handleProductChange(productIndex, 'existing_assets', [data.absolute_path]);
      handleProductChange(productIndex, 'imagePreview', data.path);
    } catch (err) {
      alert(`Failed to upload image: ${err.message}`);
    }
  };

  // Open image browser for a specific product
  const openImageBrowser = (productIndex) => {
    setSelectedProductIndex(productIndex);
    setShowImageBrowser(true);
  };

  // Select a generated image for a product
  const selectGeneratedImage = (image) => {
    if (selectedProductIndex !== null) {
      handleProductChange(selectedProductIndex, 'existing_assets', [image.absolute_path]);
      handleProductChange(selectedProductIndex, 'imagePreview', image.url);
      setShowImageBrowser(false);
      setSelectedProductIndex(null);
    }
  };

  // Clear selected image for a product
  const clearProductImage = (productIndex) => {
    handleProductChange(productIndex, 'existing_assets', []);
    handleProductChange(productIndex, 'imagePreview', null);
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

            {/* Image Selection Section */}
            <div className="product-image-section">
              <label>Product Image (optional - uses AI generation if not provided)</label>

              {product.imagePreview ? (
                <div className="image-preview-container">
                  <img src={product.imagePreview} alt="Product preview" className="product-preview" />
                  <button
                    type="button"
                    onClick={() => clearProductImage(index)}
                    className="clear-image-btn"
                  >
                    ✕ Clear Image
                  </button>
                </div>
              ) : (
                <div className="image-selection-buttons">
                  <input
                    ref={(el) => (productImageInputRefs.current[index] = el)}
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleProductImageUpload(e, index)}
                    style={{ display: 'none' }}
                  />
                  <button
                    type="button"
                    onClick={() => productImageInputRefs.current[index]?.click()}
                    className="upload-image-btn"
                  >
                    📤 Upload Image
                  </button>
                  <button
                    type="button"
                    onClick={() => openImageBrowser(index)}
                    className="browse-images-btn"
                  >
                    🖼️ Browse Generated Images
                  </button>
                </div>
              )}
            </div>
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

      {/* Image Browser Modal */}
      {showImageBrowser && (
        <div className="modal-overlay" onClick={() => setShowImageBrowser(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select a Generated Image</h3>
              <button
                type="button"
                onClick={() => setShowImageBrowser(false)}
                className="modal-close-btn"
              >
                ✕
              </button>
            </div>

            <div className="generated-images-grid">
              {generatedImages.length === 0 ? (
                <div className="no-images-message">
                  No previously generated images found. Generate a campaign first to see images here.
                </div>
              ) : (
                generatedImages.map((image, idx) => (
                  <div
                    key={idx}
                    className="generated-image-card"
                    onClick={() => selectGeneratedImage(image)}
                  >
                    <img src={image.url} alt={`${image.product} from ${image.campaign_id}`} />
                    <div className="image-card-info">
                      <div className="image-product-name">{image.product}</div>
                      <div className="image-campaign-id">{image.campaign_id.substring(9, 17)}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </form>
  );
}
