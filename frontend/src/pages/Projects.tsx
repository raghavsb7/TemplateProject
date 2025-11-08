import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import backendClient from "@/backendClient";
import { FileText, BookOpen, Edit, Calendar, CheckCircle2 } from "lucide-react";

interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  due_date: string | null;
  priority: number;
  source_type: string;
}

const Projects = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const userId = 1; // TODO: Get from auth/store

  useEffect(() => {
    fetchProjects();
  }, [filter]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await backendClient.get("/tasks", {
        params: { user_id: userId },
      });
      let filtered = response.data.tasks || [];
      
      // Filter for assignments (projects, homework, papers)
      filtered = filtered.filter((task: Task) => 
        task.task_type === "assignment" || task.task_type === "manual"
      );

      if (filter === "homework") {
        filtered = filtered.filter((task: Task) => 
          task.title.toLowerCase().includes("hw") || 
          task.title.toLowerCase().includes("homework") ||
          task.description?.toLowerCase().includes("homework")
        );
      } else if (filter === "papers") {
        filtered = filtered.filter((task: Task) => 
          task.title.toLowerCase().includes("paper") || 
          task.title.toLowerCase().includes("essay") ||
          task.description?.toLowerCase().includes("paper") ||
          task.description?.toLowerCase().includes("essay")
        );
      } else if (filter === "projects") {
        filtered = filtered.filter((task: Task) => 
          task.title.toLowerCase().includes("project") ||
          task.description?.toLowerCase().includes("project")
        );
      }

      setTasks(filtered);
    } catch (error: any) {
      console.error("Error fetching projects:", error);
      if (error.response?.status === 404) {
        setTasks([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: number, newStatus: string) => {
    try {
      await backendClient.put(`/tasks/${taskId}/status`, null, {
        params: { user_id: userId, status: newStatus },
      });
      fetchProjects();
    } catch (error) {
      console.error("Error updating task status:", error);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No due date";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getTaskIcon = (task: Task) => {
    const title = task.title.toLowerCase();
    if (title.includes("paper") || title.includes("essay")) {
      return <Edit className="h-5 w-5" />;
    } else if (title.includes("project")) {
      return <FileText className="h-5 w-5" />;
    }
    return <BookOpen className="h-5 w-5" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Projects, Homework & Papers</h1>
        <div className="flex gap-2">
          <Button
            variant={filter === "all" ? "default" : "outline"}
            onClick={() => setFilter("all")}
            size="sm"
          >
            All
          </Button>
          <Button
            variant={filter === "projects" ? "default" : "outline"}
            onClick={() => setFilter("projects")}
            size="sm"
          >
            Projects
          </Button>
          <Button
            variant={filter === "homework" ? "default" : "outline"}
            onClick={() => setFilter("homework")}
            size="sm"
          >
            Homework
          </Button>
          <Button
            variant={filter === "papers" ? "default" : "outline"}
            onClick={() => setFilter("papers")}
            size="sm"
          >
            Papers
          </Button>
        </div>
      </div>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No projects, homework, or papers found.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map((task) => (
            <Card key={task.id} className={task.status === "complete" ? "opacity-60" : ""}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    {getTaskIcon(task)}
                    <CardTitle className="text-lg">{task.title}</CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      updateTaskStatus(
                        task.id,
                        task.status === "complete" ? "pending" : "complete"
                      )
                    }
                  >
                    <CheckCircle2
                      className={`h-5 w-5 ${
                        task.status === "complete" ? "text-green-600" : "text-gray-400"
                      }`}
                    />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {task.description && (
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
                    {task.description}
                  </p>
                )}
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className={task.status === "overdue" ? "text-red-600 font-semibold" : ""}>
                    {formatDate(task.due_date)}
                  </span>
                </div>
                <div className="mt-2">
                  <span className="text-xs text-muted-foreground capitalize">
                    {task.source_type.replace("_", " ")}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Projects;

