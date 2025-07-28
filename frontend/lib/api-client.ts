const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  user_id: string;
  name: string;
  email: string;
  roles: string[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}


/**
 * Check if we're running in local development mode
 */
function isLocalDevelopment(): boolean {
  return process.env.NODE_ENV === 'development' || 
         API_BASE_URL.includes('localhost') || 
         API_BASE_URL.includes('127.0.0.1');
}

/**
 * API client that handles authentication for both local development and production
 */
class ApiClient {
  private baseUrl: string;
  private tokenCache: { token: string | null; expires: number } = { token: null, expires: 0 };

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Build authentication URL with return URL parameter
   * Made public for testing purposes
   */
  public buildAuthUrl(): string {
    const returnUrl = encodeURIComponent(window.location.href);
    return `/.auth/login/aad?post_login_redirect_uri=${returnUrl}`;
  }

  /**
   * Force refresh the authentication session by redirecting to Easy Auth refresh endpoint
   */
  private async refreshAuthSession(): Promise<void> {
    if (isLocalDevelopment()) {
      return;
    }

    try {
      // Clear token cache first
      this.tokenCache = { token: null, expires: 0 };
      
      // Try to refresh the session using Easy Auth refresh endpoint
      const refreshResponse = await fetch('/.auth/refresh', { 
        method: 'POST',
        credentials: 'include' 
      });
      
      if (!refreshResponse.ok) {
        console.warn('⚠️ Session refresh failed, redirecting to login');
        // If refresh fails, redirect to login with return URL
        window.location.href = this.buildAuthUrl();
        return;
      }
      
      console.log('✅ Authentication session refreshed successfully');
    } catch (error) {
      console.error('❌ Failed to refresh auth session:', error);
      // Fallback: redirect to login with return URL
      window.location.href = this.buildAuthUrl();
    }
  }

  /**
   * Get JWT token from Easy Auth with caching
   */
  private async getAuthToken(): Promise<string | null> {
    if (isLocalDevelopment()) {
      return null;
    }

    // Check if we have a valid cached token
    const now = Date.now();
    if (this.tokenCache.token && now < this.tokenCache.expires) {
      return this.tokenCache.token;
    }
    
    try {
      const response = await fetch('/.auth/me', { credentials: 'include' });
      if (response.ok) {
        const authInfo = await response.json()
        if (authInfo && authInfo.length > 0) {
          const provider = authInfo[0];
          
          // Use id_token instead of access_token - it's a proper JWT!
          if (provider.id_token) {
            console.log('🎫 Using ID token (JWT):', provider.id_token.substring(0, 50) + '...');
            
            // Cache the token for 6 days and 20 hours (tokens refresh for 7 days)
            this.tokenCache = {
              token: provider.id_token,
              expires: now + (164 * 60 * 60 * 1000) // 164 hours = 6 days 20 hours
            };
            
            return provider.id_token;
          }
          
          console.warn('⚠️ No id_token found in auth response');
        }
      }
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
    
    // Clear cache on failure
    this.tokenCache = { token: null, expires: 0 };
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<ApiResponse<T>> {
    const MAX_RETRIES = 1;
    
    try {
      const url = `${this.baseUrl}${endpoint}`;

      
      // Get authentication token in production
      const authToken = await this.getAuthToken();
      
      const requestOptions: RequestInit = {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          // Pass the token to backend
          ...(authToken && { 'Authorization': `Bearer ${authToken}` }),
          ...options.headers,
        },
      };

      // In local development, we need to be explicit about CORS
      if (isLocalDevelopment()) {
        requestOptions.mode = 'cors';
        requestOptions.credentials = 'omit';
      } else {
        // In production, include credentials for Easy Auth
        requestOptions.credentials = 'include';
      }

      console.log(`🔄 Making ${options.method || 'GET'} request to ${url}${retryCount > 0 ? ` (retry ${retryCount})` : ''}`);

      const response = await fetch(url, requestOptions);

      if (!response.ok) {
        if (response.status === 401 && !isLocalDevelopment() && retryCount < MAX_RETRIES) {
          console.warn('🔄 Received 401, attempting to refresh session and retry...');
          
          // Clear token cache and refresh session
          this.tokenCache = { token: null, expires: 0 };
          await this.refreshAuthSession();
          
          // Retry the request
          return this.request(endpoint, options, retryCount + 1);
        }
        
        if (response.status === 401) {
          const errorMessage = isLocalDevelopment() 
            ? 'Authentication failed. Check if backend is running.'
            : 'Authentication failed. Your session may have expired. Please refresh the page to log in again.';
          throw new Error(errorMessage);
        }
        if (response.status === 405) {
          throw new Error(`Method ${options.method || 'GET'} not allowed for ${endpoint}`);
        }
        
        // Try to extract error message from response body
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('Error parsing response body:', parseError);
          // If we can't parse the response body, fall back to generic error (errorMessage already set above)
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('API request failed:', error);
      
      // If this was a retry attempt and it still failed, provide a more helpful error message
      if (retryCount > 0 && error instanceof Error && error.message.includes('Authentication failed')) {
        return { 
          error: 'Session expired and automatic refresh failed. Please refresh the page to log in again.' 
        };
      }
      
      return { 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      };
    }
  }

  // Add a simple test method
  async testCors() {
    return this.request<{ status: string }>('/health');
  }

  // API methods
  async getRoot() {
    return this.request<{
      message: string;
      authenticated_user: {
        name: string;
        email: string;
        user_id: string;
      };
    }>('/');
  }

  async getUserProfile() {
    return this.request<User>('/user/profile');
  }

  async getUsers() {
    return this.request<User>('/users/me');
  }

  async getCurrentUser() {
    return this.request<User>('/users/me');
  }

  async getUserAuthInfo() {
    return this.request<{
      azure_user_id: string;
      name: string;
      email: string;
      roles: string[];
    }>('/users/auth-info');
  }

  async getItems() {
    return this.request<Array<unknown>>('/items/'); 
   }

  async getHealth() {
    return this.request<{ status: string }>('/health');
  }
 }

export const apiClient = new ApiClient(); 