import './App.css'
import { Card } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useGlobalStore from './store/store'
import ErrorOverlay from './model-cards/error-overlay'
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { BrowserRouter } from "react-router-dom";
import TodoList from './pages/TodoList'
import WeeklySchedule from './pages/WeeklySchedule'
import Projects from './pages/Projects'
import Midterms from './pages/Midterms'
import Internships from './pages/Internships'
import Settings from './pages/Settings'
import CanvasCallback from './pages/CanvasCallback'

function NavigationTabs() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const getActiveTab = () => {
    if (location.pathname === "/") return "todo";
    if (location.pathname === "/weekly") return "weekly";
    if (location.pathname === "/projects") return "projects";
    if (location.pathname === "/midterms") return "midterms";
    if (location.pathname === "/internships") return "internships";
    if (location.pathname === "/settings") return "settings";
    return "todo";
  };

  const handleTabChange = (value: string) => {
    switch(value) {
      case "todo":
        navigate("/");
        break;
      case "weekly":
        navigate("/weekly");
        break;
      case "projects":
        navigate("/projects");
        break;
      case "midterms":
        navigate("/midterms");
        break;
      case "internships":
        navigate("/internships");
        break;
      case "settings":
        navigate("/settings");
        break;
      default:
        navigate("/");
    }
  };

  return (
    <Tabs value={getActiveTab()} onValueChange={handleTabChange} className="w-full">
      <TabsList className="grid w-full grid-cols-6">
        <TabsTrigger value="todo">To-Do List</TabsTrigger>
        <TabsTrigger value="weekly">Weekly Schedule</TabsTrigger>
        <TabsTrigger value="projects">Projects/HW/Papers</TabsTrigger>
        <TabsTrigger value="midterms">Midterms</TabsTrigger>
        <TabsTrigger value="internships">Internships</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}

function AppContent() {
  const error = useGlobalStore(state => state.error);

  return (
    <>
      <ErrorOverlay />
      
      <Card className="mb-6">
        <div className="p-6">
          <h1 className="text-4xl font-extrabold text-center">Student Productivity Platform</h1>
        </div>
      </Card>

      <div className="mb-6">
        <NavigationTabs />
      </div>

      <div className="min-h-screen">
        <main className="max-w-6xl mx-auto">
          <Routes>
            <Route path="/" element={<TodoList />} />
            <Route path="/weekly" element={<WeeklySchedule />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/midterms" element={<Midterms />} />
            <Route path="/internships" element={<Internships />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/canvas-callback" element={<CanvasCallback />} />
            <Route path="*" element={<h2 className="text-center p-8">404 - Page Not Found</h2>} />
          </Routes>
        </main>
      </div>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen p-8 pb-8 sm:p-8">
        <AppContent />
      </div>
    </BrowserRouter>
  )
}

export default App
