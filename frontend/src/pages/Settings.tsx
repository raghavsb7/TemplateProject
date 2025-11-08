import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import backendClient from "@/backendClient";
import { CheckCircle2, XCircle, Link2, RefreshCw, Key } from "lucide-react";
import BackdropWithSpinner from "@/components/ui/backdropwithspinner";

interface OAuthToken {
  id: number;
  user_id: number;
  source_type: string;
  expires_at: string | null;
  created_at: string;
}

const Settings = () => {
  const [tokens, setTokens] = useState<OAuthToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    // Get or create user
    initializeUser();
    fetchTokens();
  }, []);

  const initializeUser = async () => {
    try {
      // Try to get user with ID 1, or create one
      try {
        const response = await backendClient.get("/users/1");
        setUserId(response.data.id);
        setUserEmail(response.data.email);
      } catch (error: any) {
        // User doesn't exist, create one
        if (error.response?.status === 404) {
          const createResponse = await backendClient.post("/users", {
            email: "student@example.com",
            name: "Student User",
          });
          setUserId(createResponse.data.id);
          setUserEmail(createResponse.data.email);
        }
      }
    } catch (error) {
      console.error("Error initializing user:", error);
    }
  };

  const fetchTokens = async () => {
    if (!userId) return;
    try {
      setLoading(true);
      const response = await backendClient.get("/auth/tokens", {
        params: { user_id: userId },
      });
      setTokens(response.data || []);
    } catch (error) {
      console.error("Error fetching tokens:", error);
    } finally {
      setLoading(false);
    }
  };

  const connectCanvas = async () => {
    if (!userId) {
      alert("Please wait for user initialization...");
      return;
    }

    try {
      setConnecting(true);
      const redirectUri = `${window.location.origin}/canvas-callback`;
      const response = await backendClient.get("/auth/canvas/login", {
        params: {
          redirect_uri: redirectUri,
          state: userId.toString(),
        },
      });

      const authUrl = response.data.auth_url;
      
      // Check if credentials are configured (auth URL should have a non-empty client_id)
      if (!authUrl || authUrl.includes("client_id=&") || (authUrl.includes("client_id=") && authUrl.split("client_id=")[1]?.split("&")[0] === "")) {
        setConnecting(false);
        alert("Canvas credentials not configured!\n\nPlease:\n1. Get Canvas Client ID and Secret from your Canvas instance\n2. Add them to: backend/.env file\n3. Restart the backend server\n\nSee CANVAS_SETUP.md for detailed instructions.");
        return;
      }

      // Redirect directly to Canvas login (same window)
      window.location.href = authUrl;
      
    } catch (error: any) {
      setConnecting(false);
      const errorMsg =
        error.response?.data?.detail ||
        "Failed to initiate Canvas connection. Please check if Canvas credentials are configured in the backend .env file.";
      
      // Check if it's a credentials issue
      if (error.response?.status === 400 || errorMsg.includes("client_id") || errorMsg.includes("Client ID")) {
        alert("Canvas credentials not configured!\n\nPlease:\n1. Get Canvas Client ID and Secret from your Canvas instance\n2. Add them to: backend/.env file\n3. Restart the backend server\n\nSee CANVAS_SETUP.md for detailed instructions.");
      } else {
        alert(errorMsg);
      }
    }
  };

  const syncCanvas = async () => {
    if (!userId) return;
    try {
      setConnecting(true);
      await backendClient.post("/sync", null, {
        params: {
          user_id: userId,
          source: "canvas",
        },
      });
      alert("Canvas tasks synced successfully!");
    } catch (error: any) {
      alert("Error syncing Canvas: " + (error.response?.data?.detail || error.message));
    } finally {
      setConnecting(false);
    }
  };

  const isConnected = (source: string) => {
    return tokens.some((token) => token.source_type === source);
  };

  const getSourceName = (source: string) => {
    const names: { [key: string]: string } = {
      canvas: "Canvas",
      outlook: "Microsoft Outlook",
      google_calendar: "Google Calendar",
      handshake: "Handshake",
    };
    return names[source] || source;
  };

  if (loading && !userId) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings & Integrations</h1>

      {userId && (
        <Card>
          <CardHeader>
            <CardTitle>User Information</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              User ID: {userId}
            </p>
            {userEmail && (
              <p className="text-sm text-muted-foreground">Email: {userEmail}</p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Connected Services</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading connections...</p>
          ) : tokens.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No services connected yet.
            </p>
          ) : (
            <div className="space-y-3">
              {tokens.map((token) => (
                <div
                  key={token.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">
                        {getSourceName(token.source_type)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Connected {new Date(token.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connect Services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isConnected("canvas") ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                ) : (
                  <Link2 className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <p className="font-medium">Canvas LMS</p>
                  <p className="text-sm text-muted-foreground">
                    {isConnected("canvas")
                      ? "Connected - Sync your assignments"
                      : "Connect to sync assignments and due dates"}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                {isConnected("canvas") ? (
                  <Button onClick={syncCanvas} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Sync Now
                  </Button>
                ) : (
                  <Button
                    onClick={connectCanvas}
                    disabled={connecting || !userId}
                    size="sm"
                  >
                    {connecting ? "Connecting..." : "OAuth Login"}
                  </Button>
                )}
              </div>
            </div>
            
            {!isConnected("canvas") && (
              <div className="pt-4 border-t space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Key className="h-4 w-4" />
                  <span className="font-medium">Don't have admin access? Use API Token instead:</span>
                </div>
                <CanvasTokenForm userId={userId} onSuccess={() => { fetchTokens(); }} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {connecting && <BackdropWithSpinner />}
    </div>
  );
};

const CanvasTokenForm = ({ userId, onSuccess }: { userId: number | null; onSuccess: () => void }) => {
  const [token, setToken] = useState("");
  const [canvasUrl, setCanvasUrl] = useState("https://canvas.instructure.com");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId || !token.trim()) {
      setError("Please enter a Canvas API token");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      await backendClient.post("/auth/canvas/token", null, {
        params: {
          user_id: userId,
          access_token: token.trim(),
          canvas_base_url: canvasUrl.trim() || undefined,
        },
      });
      setToken("");
      setError("");
      alert("Canvas connected successfully!");
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to connect Canvas. Please check your token.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <Label htmlFor="canvas-url">Canvas URL (optional)</Label>
        <Input
          id="canvas-url"
          type="text"
          placeholder="https://canvas.instructure.com"
          value={canvasUrl}
          onChange={(e) => setCanvasUrl(e.target.value)}
          className="mt-1"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Leave as default unless your school uses a different Canvas URL
        </p>
      </div>
      <div>
        <Label htmlFor="canvas-token">Canvas API Token</Label>
        <Textarea
          id="canvas-token"
          placeholder="Paste your Canvas API token here"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="mt-1 font-mono text-sm"
          rows={3}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Get your token from: Canvas → Account → Settings → New Access Token
        </p>
      </div>
      {error && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}
      <Button type="submit" disabled={submitting || !userId} size="sm">
        {submitting ? "Connecting..." : "Connect with API Token"}
      </Button>
    </form>
  );
};

export default Settings;

