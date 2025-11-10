import { useState } from 'react';
import CampaignForm from './components/CampaignForm';
import ProgressDashboard from './components/ProgressDashboard';
import AssetGallery from './components/AssetGallery';
import './App.css';

function App() {
  const [view, setView] = useState('form'); // 'form', 'processing', 'gallery'
  const [campaignId, setCampaignId] = useState(null);
  const [reportData, setReportData] = useState(null);

  const handleFormSubmit = async (formData) => {
    try {
      const response = await fetch('/api/campaigns/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      setCampaignId(data.campaign_id);
      setView('processing');
    } catch (error) {
      console.error('Failed to create campaign:', error);
      alert('Failed to create campaign. Please try again.');
    }
  };

  const handleProcessingComplete = (statusData) => {
    setReportData(statusData.report);
    setView('gallery');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎨 Creative Automation Pipeline</h1>
        <p>AI-powered social campaign asset generation</p>
      </header>

      <main className="app-main">
        {view === 'form' && <CampaignForm onSubmit={handleFormSubmit} />}

        {view === 'processing' && (
          <ProgressDashboard campaignId={campaignId} onComplete={handleProcessingComplete} />
        )}

        {view === 'gallery' && (
          <AssetGallery campaignId={campaignId} reportData={reportData} />
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by DALL-E 3 & GPT-4</p>
      </footer>
    </div>
  );
}

export default App;
