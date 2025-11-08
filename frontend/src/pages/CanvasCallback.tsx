import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import backendClient from "@/backendClient";
import { Card, CardContent } from "@/components/ui/card";

const CanvasCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const error = searchParams.get("error");
      const state = searchParams.get("state");

      if (error) {
        if (window.opener) {
          window.opener.postMessage(
            { type: "canvas-oauth-error", error },
            window.location.origin
          );
          window.close();
        } else {
          alert("Canvas connection error: " + error);
          window.location.href = "/settings";
        }
        return;
      }

      if (!code) {
        if (window.opener) {
          window.opener.postMessage(
            { type: "canvas-oauth-error", error: "No authorization code received" },
            window.location.origin
          );
          window.close();
        } else {
          alert("No authorization code received from Canvas");
          window.location.href = "/settings";
        }
        return;
      }

      try {
        const userId = state ? parseInt(state) : 1;
        const redirectUri = `${window.location.origin}/canvas-callback`;

        await backendClient.post("/auth/canvas/callback", null, {
          params: {
            code,
            redirect_uri: redirectUri,
            user_id: userId,
          },
        });

        // If opened in popup, notify parent and close
        if (window.opener) {
          window.opener.postMessage(
            { type: "canvas-oauth-success" },
            window.location.origin
          );
          window.close();
        } else {
          // If same window redirect, redirect back to settings
          window.location.href = "/settings";
        }
      } catch (err: any) {
        const errorMsg =
          err.response?.data?.detail || "Failed to complete Canvas connection";
        
        // If opened in popup, notify parent and close
        if (window.opener) {
          window.opener.postMessage(
            { type: "canvas-oauth-error", error: errorMsg },
            window.location.origin
          );
          window.close();
        } else {
          // If same window redirect, show error and redirect back
          alert("Failed to connect Canvas: " + errorMsg);
          window.location.href = "/settings";
        }
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen p-8">
      <Card>
        <CardContent className="p-8 text-center">
          <p>Completing Canvas connection...</p>
          <p className="text-sm text-muted-foreground mt-2">
            This window will close automatically.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default CanvasCallback;

