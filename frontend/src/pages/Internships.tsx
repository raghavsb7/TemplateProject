import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import backendClient from "@/backendClient";
import { Briefcase, Calendar, MapPin, Building2, ExternalLink, CheckCircle2 } from "lucide-react";

interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  due_date: string | null;
  priority: number;
  source_type: string;
  task_metadata: string | null;
}

const Internships = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = 1; // TODO: Get from auth/store

  useEffect(() => {
    fetchInternships();
  }, []);

  const fetchInternships = async () => {
    try {
      setLoading(true);
      const response = await backendClient.get("/tasks", {
        params: { user_id: userId },
      });
      // Filter for internships
      const allTasks = response.data.tasks || [];
      const internships = allTasks.filter(
        (task: Task) => task.task_type === "internship"
      );
      setTasks(internships);
    } catch (error: any) {
      console.error("Error fetching internships:", error);
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
      fetchInternships();
    } catch (error) {
      console.error("Error updating task status:", error);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No deadline";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const getDaysUntil = (dateString: string | null) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const parseMetadata = (metadata: string | null) => {
    if (!metadata) return null;
    try {
      return JSON.parse(metadata);
    } catch {
      return null;
    }
  };

  const isUpcoming = (dateString: string | null) => {
    if (!dateString) return false;
    const days = getDaysUntil(dateString);
    return days !== null && days >= 0 && days <= 7;
  };

  const isOverdue = (dateString: string | null) => {
    if (!dateString) return false;
    return new Date(dateString) < new Date();
  };

  // Sort by due date (upcoming first)
  const sortedTasks = [...tasks].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading internships...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Internships</h1>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No internship opportunities found.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedTasks.map((task) => {
            const metadata = parseMetadata(task.task_metadata);
            const daysUntil = getDaysUntil(task.due_date);
            const upcoming = isUpcoming(task.due_date);
            const overdue = isOverdue(task.due_date);

            return (
              <Card
                key={task.id}
                className={
                  overdue
                    ? "border-red-500 border-2"
                    : upcoming
                    ? "border-orange-500 border-2"
                    : task.status === "complete"
                    ? "opacity-60"
                    : ""
                }
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 flex-1">
                      <Briefcase className="h-5 w-5 text-blue-600" />
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

                  <div className="space-y-2">
                    {metadata?.employer && (
                      <div className="flex items-center gap-2 text-sm">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span>{metadata.employer}</span>
                      </div>
                    )}

                    {metadata?.location && (
                      <div className="flex items-center gap-2 text-sm">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <span>{metadata.location}</span>
                      </div>
                    )}

                    {task.due_date && (
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className={overdue ? "text-red-600 font-semibold" : upcoming ? "text-orange-600 font-semibold" : ""}>
                          {formatDate(task.due_date)}
                        </span>
                        {daysUntil !== null && !overdue && (
                          <span className="text-xs text-muted-foreground">
                            ({daysUntil} day{daysUntil !== 1 ? "s" : ""} left)
                          </span>
                        )}
                      </div>
                    )}

                    {metadata?.job_type && (
                      <div className="pt-2">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          {metadata.job_type}
                        </span>
                      </div>
                    )}

                    {overdue && (
                      <div className="pt-2">
                        <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                          Application Deadline Passed
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Internships;

