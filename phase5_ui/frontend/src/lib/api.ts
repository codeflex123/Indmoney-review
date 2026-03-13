const API_BASE_URL = 'http://localhost:8000/api';

export async function fetchReviews(limit = 100) {
    const response = await fetch(`${API_BASE_URL}/reviews?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch reviews');
    return response.json();
}

export async function fetchAnalysis() {
    const response = await fetch(`${API_BASE_URL}/analysis`);
    if (!response.ok) throw new Error('Failed to fetch analysis');
    return response.json();
}

export async function fetchEmailPreview() {
    const response = await fetch(`${API_BASE_URL}/preview`);
    if (!response.ok) throw new Error('Failed to fetch email preview');
    return response.json();
}

export async function triggerPhase(
    phase: 'scrape' | 'analyze' | 'pulsar' | 'email', 
    params?: { email?: string; weeks?: number; limit?: number }
) {
    let url = `${API_BASE_URL}/trigger/${phase}?`;
    
    if (params?.email) url += `email=${encodeURIComponent(params.email)}&`;
    if (params?.weeks) url += `weeks=${params.weeks}&`;
    if (params?.limit) url += `limit=${params.limit}&`;
    
    const response = await fetch(url.slice(0, -1), {
        method: 'POST',
    });
    
    if (!response.ok) throw new Error(`Failed to trigger ${phase}`);
    return response.json();
}
