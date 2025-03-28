import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    // Read data from the public data.json file
    const dataPath = path.join(process.cwd(), 'public', 'data.json');
    const fileData = fs.readFileSync(dataPath, 'utf8');
    const sentimentData = JSON.parse(fileData);
    
    return NextResponse.json({
      success: true,
      data: sentimentData,
      message: "Market sentiment data retrieved successfully"
    });
  } catch (error) {
    console.error('Error in sentiment API:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to retrieve sentiment data' },
      { status: 500 }
    );
  }
}
