import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import backendClient from "@/backendClient";
import { CheckCircle2, Circle, AlertCircle, Calendar } from "lucide-react";

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

const TodoList = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const userId = 1; // TODO: Get from auth/store

  useEffect(() => {
    fetchTasks();
  }, [statusFilter]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params: any = { user_id: userId };
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      const response = await backendClient.get("/tasks", { params });
      setTasks(response.data.tasks || []);
    } catch (error: any) {
      console.error("Error fetching tasks:", error);
      // If user doesn't exist, show empty state
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
      fetchTasks();
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
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getPriorityColor = (priority: number) => {
    if (priority >= 3) return "text-red-600";
    if (priority >= 2) return "text-orange-600";
    if (priority >= 1) return "text-yellow-600";
    return "text-gray-600";
  };

  const isOverdue = (dueDate: string | null) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading tasks...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">To-Do List</h1>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tasks</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="complete">Complete</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No tasks found. You're all caught up!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <Card key={task.id} className={task.status === "complete" ? "opacity-60" : ""}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        updateTaskStatus(
                          task.id,
                          task.status === "complete" ? "pending" : "complete"
                        )
                      }
                      className="mt-1"
                    >
                      {task.status === "complete" ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <Circle className="h-5 w-5 text-gray-400" />
                      )}
                    </Button>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{task.title}</CardTitle>
                      {task.description && (
                        <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          <span className={isOverdue(task.due_date) ? "text-red-600 font-semibold" : ""}>
                            {formatDate(task.due_date)}
                          </span>
                        </div>
                        <span className={`font-semibold ${getPriorityColor(task.priority)}`}>
                          Priority: {task.priority}
                        </span>
                        <span className="text-muted-foreground capitalize">
                          {task.source_type.replace("_", " ")}
                        </span>
                        {isOverdue(task.due_date) && task.status !== "complete" && (
                          <div className="flex items-center gap-1 text-red-600">
                            <AlertCircle className="h-4 w-4" />
                            <span className="font-semibold">Overdue</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default TodoList;

