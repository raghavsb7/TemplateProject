import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import backendClient from "@/backendClient";
import { Calendar, Clock, AlertCircle, CheckCircle2 } from "lucide-react";

interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  due_date: string | null;
  start_date: string | null;
  priority: number;
  source_type: string;
}

const Midterms = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = 1; // TODO: Get from auth/store

  useEffect(() => {
    fetchMidterms();
  }, []);

  const fetchMidterms = async () => {
    try {
      setLoading(true);
      const response = await backendClient.get("/tasks", {
        params: { user_id: userId },
      });
      // Filter for midterms - look for tasks with "midterm", "exam", "test" in title
      const allTasks = response.data.tasks || [];
      const midterms = allTasks.filter((task: Task) => {
        const title = task.title.toLowerCase();
        const desc = (task.description || "").toLowerCase();
        return (
          title.includes("midterm") ||
          title.includes("exam") ||
          title.includes("test") ||
          desc.includes("midterm") ||
          desc.includes("exam")
        );
      });
      setTasks(midterms);
    } catch (error: any) {
      console.error("Error fetching midterms:", error);
      if (error.response?.status === 404) {
        setTasks([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No date";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatTime = (dateString: string | null) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
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

  const isUpcoming = (dateString: string | null) => {
    if (!dateString) return false;
    const days = getDaysUntil(dateString);
    return days !== null && days >= 0 && days <= 7;
  };

  const isOverdue = (dateString: string | null) => {
    if (!dateString) return false;
    return new Date(dateString) < new Date();
  };

  // Sort tasks by due date
  const sortedTasks = [...tasks].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading midterms...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Midterms & Exams</h1>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No midterms or exams found.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sortedTasks.map((task) => {
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
                    : ""
                }
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">{task.title}</CardTitle>
                      {task.description && (
                        <p className="text-sm text-muted-foreground">{task.description}</p>
                      )}
                    </div>
                    {task.status === "complete" && (
                      <CheckCircle2 className="h-6 w-6 text-green-600" />
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {task.due_date && (
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold">{formatDate(task.due_date)}</span>
                        {task.start_date && (
                          <>
                            <Clock className="h-4 w-4 text-muted-foreground ml-4" />
                            <span>{formatTime(task.start_date)}</span>
                          </>
                        )}
                      </div>
                    )}
                    {daysUntil !== null && (
                      <div className="flex items-center gap-2">
                        {overdue ? (
                          <>
                            <AlertCircle className="h-4 w-4 text-red-600" />
                            <span className="text-red-600 font-semibold">
                              Overdue by {Math.abs(daysUntil)} day{Math.abs(daysUntil) !== 1 ? "s" : ""}
                            </span>
                          </>
                        ) : upcoming ? (
                          <>
                            <AlertCircle className="h-4 w-4 text-orange-600" />
                            <span className="text-orange-600 font-semibold">
                              {daysUntil} day{daysUntil !== 1 ? "s" : ""} until exam
                            </span>
                          </>
                        ) : (
                          <span className="text-muted-foreground">
                            {daysUntil} day{daysUntil !== 1 ? "s" : ""} until exam
                          </span>
                        )}
                      </div>
                    )}
                    <div className="pt-2">
                      <span className="text-xs text-muted-foreground capitalize">
                        Source: {task.source_type.replace("_", " ")}
                      </span>
                    </div>
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

export default Midterms;

