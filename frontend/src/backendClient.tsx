import axios from "axios";
import { log } from "./lib/logger"
import { globalStore } from "./store/store";

const apiURL = import.meta.env.VITE_API_ENDPOINT;
log("apiURL : ", apiURL);

const backendClient = axios.create({
    baseURL: apiURL,
    timeout: 10000, // 10 second timeout
});

backendClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const message =
            error.response?.data?.detail || "Something went wrong with the API.";
        const status = error.response?.status;

        log("API error:", { status, message });
        
        globalStore.getState().setError(message);
        // Reject the promise so components can handle errors properly
        return Promise.reject(error);
    }
  );

export default backendClient;