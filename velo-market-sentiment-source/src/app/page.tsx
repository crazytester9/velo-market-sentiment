'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface SentimentData {
  timestamp: number;
  datetime: string;
  strategic_bias: number;
  directional_bias: number;
  green_percentage: number;
  quadrant: string;
  data: {
    [key: string]: {
      value: number;
      color: string;
      is_positive: boolean;
    };
  };
}

export default function Home() {
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const router = useRouter();

  const fetchSentimentData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/sentiment');
      
      if (!response.ok) {
        throw new Error('Failed to fetch sentiment data');
      }
      
      const result = await response.json();
      
      if (result.success && result.data) {
        setSentimentData(result.data);
        setLastUpdated(new Date().toLocaleTimeString());
      } else {
        throw new Error(result.message || 'Failed to retrieve valid data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Error fetching sentiment data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentimentData();
    
    // Set up polling every 60 seconds
    const intervalId = setInterval(fetchSentimentData, 60000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Determine directional bias text
  const getDirectionalBiasText = () => {
    if (!sentimentData) return '';
    
    return sentimentData.directional_bias > 0 ? 'LONG' : 'SHORT';
  };
  
  // Determine trading condition text
  const getTradingConditionText = () => {
    if (!sentimentData) return '';
    
    const strategicBias = sentimentData.strategic_bias;
    
    // Strategic bias < 50% indicates mean reversion, >= 50% indicates momentum
    return strategicBias < 50 ? 'MEAN-REVERSION' : 'MOMENTUM';
  };
  
  // Get color for directional bias
  const getDirectionalBiasColor = () => {
    if (!sentimentData) return 'text-gray-500';
    
    return sentimentData.directional_bias > 0 ? 'text-green-600' : 'text-red-600';
  };
  
  // Get color for trading condition
  const getTradingConditionColor = () => {
    if (!sentimentData) return 'text-gray-500';
    
    const strategicBias = sentimentData.strategic_bias;
    
    // Use purple for mean reversion, blue for momentum
    return strategicBias < 50 ? 'text-purple-600' : 'text-blue-600';
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 bg-gray-900 text-white">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">Velo Market Sentiment Analysis</h1>
        
        {loading && !sentimentData && (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
          </div>
        )}
        
        {error && (
          <div className="bg-red-900 text-white p-4 rounded-lg mb-8">
            <p className="font-bold">Error:</p>
            <p>{error}</p>
          </div>
        )}
        
        {sentimentData && (
          <div className="space-y-8">
            {/* Main Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold mb-2">Directional Bias</h2>
                <p className={`text-6xl font-bold ${getDirectionalBiasColor()}`}>
                  {getDirectionalBiasText()}
                </p>
                <p className="mt-2 text-gray-400">
                  Bias: {sentimentData.directional_bias.toFixed(2)}σ
                </p>
              </div>
              
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-semibold mb-2">Trading Condition</h2>
                <p className={`text-6xl font-bold ${getTradingConditionColor()}`}>
                  {getTradingConditionText()}
                </p>
                <p className="mt-2 text-gray-400">
                  Strategic Bias: {sentimentData.strategic_bias.toFixed(2)}%
                </p>
              </div>
            </div>
            
            {/* Market Quadrant */}
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-xl font-semibold mb-4">Current Market Quadrant</h2>
              <div className="flex items-center justify-center">
                <div className="bg-gray-700 p-4 rounded-lg inline-block">
                  <p className="text-3xl font-bold text-yellow-400">{sentimentData.quadrant}</p>
                </div>
              </div>
            </div>
            
            {/* Return Buckets Data */}
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-xl font-semibold mb-4">1d Return Buckets</h2>
              <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
                {Object.entries(sentimentData.data).map(([category, data]) => (
                  <div 
                    key={category} 
                    className={`p-3 rounded-lg text-center ${data.is_positive ? 'bg-green-900' : 'bg-red-900'}`}
                  >
                    <p className="font-bold">{category}</p>
                    <p className="text-2xl">{data.value}</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Last Updated */}
            <div className="text-center text-gray-400">
              <p>Last updated: {lastUpdated}</p>
              <button 
                onClick={fetchSentimentData}
                className="mt-2 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh Data
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
