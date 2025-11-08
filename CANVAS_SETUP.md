# Canvas Connection Setup Guide

## Step 1: Get Canvas OAuth Credentials

### For Standard Canvas (canvas.instructure.com):
1. Log in to your Canvas instance
2. Go to **Account** → **Settings**
3. Scroll down and click **+ New Access Token** or **Developer Keys**
4. If you see "Developer Keys", click it, then click **+ Developer Key** → **+ API Key**
5. Fill in:
   - **Key Name**: Student Productivity Platform
   - **Redirect URI**: `http://localhost:8000/api/auth/canvas/callback`
   - **Scopes**: Check all available scopes (or at least read access)
6. Click **Save**
7. Copy the **Client ID** and **Client Secret**

### For School-Specific Canvas:
1. Log in to your school's Canvas instance
2. Go to **Admin** → **Developer Keys** (if you have admin access)
   OR
   Contact your Canvas administrator to create a Developer Key
3. Set the Redirect URI to: `http://localhost:8000/api/auth/canvas/callback`
4. Copy the **Client ID** and **Client Secret**

## Step 2: Configure Backend

1. Open the `.env` file in the `backend` directory
2. Add your Canvas credentials:
   ```
   CANVAS_BASE_URL=https://canvas.instructure.com
   CANVAS_CLIENT_ID=your_client_id_here
   CANVAS_CLIENT_SECRET=your_client_secret_here
   ```
   
   **Note**: If your Canvas is at a different URL (e.g., `https://canvas.yourschool.edu`), update `CANVAS_BASE_URL` accordingly.

3. Save the file
4. Restart the backend server if it's running

## Step 3: Connect Canvas in the App

1. Open the web app at `http://localhost:5173`
2. Navigate to the **Settings** tab
3. Click **Connect Canvas**
4. A new window will open asking you to authorize the app
5. Log in to Canvas and authorize the application
6. The window will close automatically and Canvas will be connected
7. Your assignments will automatically sync!

## Troubleshooting

### "Failed to initiate Canvas connection"
- Make sure `CANVAS_CLIENT_ID` and `CANVAS_CLIENT_SECRET` are set in `.env`
- Restart the backend server after updating `.env`
- Check that the Redirect URI in Canvas matches: `http://localhost:8000/api/auth/canvas/callback`

### "OAuth error" during connection
- Verify your Canvas credentials are correct
- Check that the Redirect URI in Canvas exactly matches: `http://localhost:8000/api/auth/canvas/callback`
- Make sure you're using the correct Canvas base URL

### No assignments showing up
- After connecting, click **Sync Now** in Settings
- Check that you have active courses with assignments in Canvas
- Verify the assignments have due dates set

## Next Steps

After connecting Canvas:
- Your assignments will automatically appear in the **To-Do List**
- They'll be organized in **Projects/HW/Papers** tab
- Midterms and exams will show in the **Midterms** tab
- The **Weekly Schedule** will show upcoming assignments

