import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';

const execPromise = promisify(exec);

// Mock data for development/testing
const MOCK_DATA = {
  timestamp: Date.now(),
  datetime: new Date().toISOString(),
  strategic_bias: 68.5,
  directional_bias: 1.2,
  green_percentage: 68.5,
  quadrant: "Momentum Long Only",
  data: {
    "-9%": { value: 10, color: "red", is_positive: false },
    "-6%": { value: 15, color: "red", is_positive: false },
    "-3%": { value: 20, color: "red", is_positive: false },
    "<0%": { value: 25, color: "red", is_positive: false },
    ">0%": { value: 120, color: "green", is_positive: true },
    "+3%": { value: 70, color: "green", is_positive: true },
    "+6%": { value: 40, color: "green", is_positive: true },
    "+9%": { value: 30, color: "green", is_positive: true }
  }
};

export async function GET(request: NextRequest) {
  try {
    // In production, we would run the scraper to get real-time data
    // For now, we'll use mock data
    
    // Determine if we should use mock data or try to get real data
    const useMockData = true; // Set to false to attempt real data collection
    
    if (useMockData) {
      return NextResponse.json({
        success: true,
        data: MOCK_DATA,
        message: "Mock data retrieved successfully"
      });
    }
    
    // This part would be used in production to get real data
    // It's commented out for now as it requires the Python environment
    /*
    // Path to the Python script
    const scriptPath = path.join(process.cwd(), 'scripts', 'get_sentiment.py');
    
    // Execute the Python script
    const { stdout, stderr } = await execPromise(`python ${scriptPath}`);
    
    if (stderr) {
      console.error(`Error executing Python script: ${stderr}`);
      throw new Error('Failed to execute Python script');
    }
    
    // Parse the output as JSON
    const data = JSON.parse(stdout);
    
    return NextResponse.json({
      success: true,
      data,
      message: "Data retrieved successfully"
    });
    */
    
    return NextResponse.json({
      success: true,
      data: MOCK_DATA,
      message: "Mock data retrieved successfully"
    });
    
  } catch (error) {
    console.error('Error in sentiment API:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to retrieve sentiment data' },
      { status: 500 }
    );
  }
}
