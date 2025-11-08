import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import backendClient from "@/backendClient";
import { Calendar, Clock } from "lucide-react";

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

const WeeklySchedule = () => {
  const [weeklyTasks, setWeeklyTasks] = useState<{
    this_week: Task[];
    next_week: Task[];
    later: Task[];
  }>({
    this_week: [],
    next_week: [],
    later: [],
  });
  const [loading, setLoading] = useState(true);
  const userId = 1; // TODO: Get from auth/store

  useEffect(() => {
    fetchWeeklyTasks();
  }, []);

  const fetchWeeklyTasks = async () => {
    try {
      setLoading(true);
      const response = await backendClient.get("/tasks/weekly", {
        params: { user_id: userId },
      });
      setWeeklyTasks(response.data);
    } catch (error: any) {
      console.error("Error fetching weekly tasks:", error);
      if (error.response?.status === 404) {
        setWeeklyTasks({ this_week: [], next_week: [], later: [] });
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "No date";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
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

  const TaskCard = ({ task }: { task: Task }) => (
    <Card className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <CardTitle className="text-base">{task.title}</CardTitle>
          <span className="text-xs text-muted-foreground capitalize">
            {task.task_type}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {task.description && (
          <p className="text-sm text-muted-foreground mb-2">{task.description}</p>
        )}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {task.start_date && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{formatTime(task.start_date)}</span>
            </div>
          )}
          {task.due_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(task.due_date)}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p>Loading schedule...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Weekly Schedule</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-4 text-red-600">This Week</h2>
          {weeklyTasks.this_week.length === 0 ? (
            <Card>
              <CardContent className="p-4 text-center text-sm text-muted-foreground">
                No tasks this week
              </CardContent>
            </Card>
          ) : (
            weeklyTasks.this_week.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4 text-orange-600">Next Week</h2>
          {weeklyTasks.next_week.length === 0 ? (
            <Card>
              <CardContent className="p-4 text-center text-sm text-muted-foreground">
                No tasks next week
              </CardContent>
            </Card>
          ) : (
            weeklyTasks.next_week.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4 text-blue-600">Later</h2>
          {weeklyTasks.later.length === 0 ? (
            <Card>
              <CardContent className="p-4 text-center text-sm text-muted-foreground">
                No future tasks
              </CardContent>
            </Card>
          ) : (
            weeklyTasks.later.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default WeeklySchedule;

